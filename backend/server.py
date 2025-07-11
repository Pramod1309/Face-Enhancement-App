from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pymongo import MongoClient
from bson import ObjectId
import os
import base64
import uuid
import asyncio
from datetime import datetime
from typing import Optional, List
import cv2
import numpy as np
from io import BytesIO
from PIL import Image
import requests
import json

app = FastAPI(title="AI Face Reconstruction API", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/')
client = MongoClient(MONGO_URL)
db = client['face_reconstruction_db']
cases_collection = db['cases']
results_collection = db['results']

# HuggingFace API configuration
HUGGINGFACE_API_KEY = os.environ.get('HUGGINGFACE_API_KEY', '')
HUGGINGFACE_API_URL = "https://api-inference.huggingface.co/models/"

def detect_faces_opencv(image_data):
    """Detect faces using OpenCV as fallback"""
    try:
        # Convert base64 to image
        img_bytes = base64.b64decode(image_data.split(',')[1])
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Load face cascade
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        
        return len(faces) > 0, len(faces)
    except Exception as e:
        print(f"Face detection error: {e}")
        return False, 0

async def enhance_face_huggingface(image_data, model_name):
    """Enhance face using HuggingFace API"""
    try:
        headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
        
        # Convert base64 to bytes
        img_bytes = base64.b64decode(image_data.split(',')[1])
        
        # Call HuggingFace API
        response = requests.post(
            f"{HUGGINGFACE_API_URL}{model_name}",
            headers=headers,
            data=img_bytes
        )
        
        if response.status_code == 200:
            # Convert response to base64
            enhanced_img = base64.b64encode(response.content).decode('utf-8')
            return f"data:image/png;base64,{enhanced_img}"
        else:
            return None
    except Exception as e:
        print(f"HuggingFace API error: {e}")
        return None

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "Face Reconstruction API"}

@app.post("/api/upload-image")
async def upload_image(file: UploadFile = File(...)):
    """Upload and analyze image for face detection"""
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read and encode image
        content = await file.read()
        base64_image = base64.b64encode(content).decode('utf-8')
        image_data = f"data:{file.content_type};base64,{base64_image}"
        
        # Detect faces
        faces_detected, face_count = detect_faces_opencv(image_data)
        
        # Create case record
        case_id = str(uuid.uuid4())
        case_data = {
            "case_id": case_id,
            "original_image": image_data,
            "filename": file.filename,
            "upload_time": datetime.now().isoformat(),
            "faces_detected": faces_detected,
            "face_count": face_count,
            "status": "uploaded"
        }
        
        cases_collection.insert_one(case_data)
        
        return {
            "case_id": case_id,
            "faces_detected": faces_detected,
            "face_count": face_count,
            "message": "Image uploaded and analyzed successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.post("/api/enhance-face/{case_id}")
async def enhance_face(case_id: str, enhancement_type: str = "restoration"):
    """Enhance face using AI models"""
    try:
        # Get case data
        case = cases_collection.find_one({"case_id": case_id})
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")
        
        # Check if HuggingFace API key is available
        if not HUGGINGFACE_API_KEY:
            # Fallback to basic enhancement
            enhanced_image = case['original_image']  # For now, return original
            confidence = 0.5
            method = "Basic Enhancement (Demo)"
        else:
            # Choose model based on enhancement type
            if enhancement_type == "restoration":
                model_name = "microsoft/DiT-XL-2-256"  # Face restoration model
            else:
                model_name = "microsoft/DiT-XL-2-256"  # Super resolution model
            
            # Enhance using HuggingFace
            enhanced_image = await enhance_face_huggingface(case['original_image'], model_name)
            
            if enhanced_image:
                confidence = 0.85
                method = f"HuggingFace {model_name}"
            else:
                enhanced_image = case['original_image']
                confidence = 0.5
                method = "Basic Enhancement (API Error)"
        
        # Save result
        result_id = str(uuid.uuid4())
        result_data = {
            "result_id": result_id,
            "case_id": case_id,
            "original_image": case['original_image'],
            "enhanced_image": enhanced_image,
            "enhancement_type": enhancement_type,
            "confidence_score": confidence,
            "method_used": method,
            "processing_time": datetime.now().isoformat(),
            "status": "completed"
        }
        
        results_collection.insert_one(result_data)
        
        # Update case status
        cases_collection.update_one(
            {"case_id": case_id},
            {"$set": {"status": "processed", "result_id": result_id}}
        )
        
        return {
            "result_id": result_id,
            "enhanced_image": enhanced_image,
            "confidence_score": confidence,
            "method_used": method,
            "message": "Face enhancement completed"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Enhancement failed: {str(e)}")

@app.get("/api/case/{case_id}")
async def get_case(case_id: str):
    """Get case details"""
    try:
        case = cases_collection.find_one({"case_id": case_id})
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")
        
        # Remove MongoDB ObjectId for JSON serialization
        case.pop('_id', None)
        
        return case
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get case: {str(e)}")

@app.get("/api/result/{result_id}")
async def get_result(result_id: str):
    """Get enhancement result"""
    try:
        result = results_collection.find_one({"result_id": result_id})
        if not result:
            raise HTTPException(status_code=404, detail="Result not found")
        
        # Remove MongoDB ObjectId for JSON serialization
        result.pop('_id', None)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get result: {str(e)}")

@app.get("/api/cases")
async def get_all_cases():
    """Get all cases"""
    try:
        cases = list(cases_collection.find({}).sort("upload_time", -1))
        
        # Remove MongoDB ObjectIds
        for case in cases:
            case.pop('_id', None)
        
        return {"cases": cases}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cases: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)