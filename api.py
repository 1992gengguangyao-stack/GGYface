from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import base64
import requests
import os

app = Flask(__name__, static_folder='.')
CORS(app)

GOOGLE_API_KEY = "AIzaSyCaLFY_FM7iwdhAC2Vi8I-_9yGXBh3CYVc"

def detect_face_and_search(image_base64):
    try:
        url = "https://vision.googleapis.com/v1/images:annotate"
        payload = {
            "requests": [{
                "image": {"content": image_base64},
                "features": [
                    {"type": "FACE_DETECTION", "maxResults": 5},
                    {"type": "WEB_DETECTION", "maxResults": 15}
                ]
            }]
        }
        
        response = requests.post(url + "?key=" + GOOGLE_API_KEY, json=payload, headers={"Content-Type": "application/json"}, timeout=30)
        result = response.json()
        
        if "error" in result:
            return {"error": result["error"]["message"]}
        
        resp = result.get("responses", [{}])[0]
        faces = resp.get("faceAnnotations", [])
        web = resp.get("webDetection", {})
        
        return {
            "faces_detected": len(faces),
            "similar_images": web.get("visuallySimilarImages", [])[:10],
            "matching_pages": web.get("pagesWithMatchingImages", [])[:15]
        }
    except Exception as e:
        return {"error": str(e)}

def extract_social_media(results):
    social_platforms = {"instagram.com": "Instagram", "twitter.com": "Twitter", "x.com": "Twitter", "tiktok.com": "TikTok", "facebook.com": "Facebook", "youtube.com": "YouTube", "linkedin.com": "LinkedIn"}
    social_results = []
    
    for page in results.get("matching_pages", []):
        url = page.get("url", "")
        for domain, platform in social_platforms.items():
            if domain in url:
                social_results.append({"platform": platform, "url": url, "title": page.get("pageTitle", "")[:60]})
                break
    
    for img in results.get("similar_images", []):
        url = img.get("url", "")
        for domain, platform in social_platforms.items():
            if domain in url:
                social_results.append({"platform": platform, "url": url})
                break
    
    return social_results

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('.', path)

@app.route('/api/search', methods=['POST'])
def search():
    data = request.json or {}
    if 'image' not in data:
        return jsonify({"error": "No image provided"}), 400
    
    image_data = data['image']
    if ',' in image_data:
        image_data = image_data.split(',')[1]
    
    result = detect_face_and_search(image_data)
    
    if result.get("error"):
        return jsonify({"status": "error", "message": result.get("error"), "results": []})
    
    social = extract_social_media(result)
    
    return jsonify({
        "status": "ok",
        "faces_detected": result.get("faces_detected", 0),
        "results": social if social else []
    })

@app.route('/api/health')
def health():
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
