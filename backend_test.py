#!/usr/bin/env python3
"""
Backend API Testing for AI Face Reconstruction System
Tests all backend endpoints with real data
"""

import requests
import json
import base64
import os
import time
from io import BytesIO
from PIL import Image, ImageDraw
import numpy as np

# Get backend URL from frontend .env
BACKEND_URL = "https://7f7014d7-9366-4289-81de-2d8b04e5f7f9.preview.emergentagent.com/api"

def create_test_image_with_face():
    """Create a simple test image with a face-like pattern for testing"""
    # Create a 200x200 image with a simple face pattern
    img = Image.new('RGB', (200, 200), color='white')
    draw = ImageDraw.Draw(img)
    
    # Draw a simple face pattern that OpenCV might detect
    # Face outline (circle)
    draw.ellipse([50, 50, 150, 150], outline='black', width=3)
    # Eyes
    draw.ellipse([70, 80, 85, 95], fill='black')
    draw.ellipse([115, 80, 130, 95], fill='black')
    # Nose
    draw.line([100, 95, 100, 115], fill='black', width=2)
    # Mouth
    draw.arc([80, 115, 120, 135], start=0, end=180, fill='black', width=2)
    
    # Convert to bytes
    buffer = BytesIO()
    img.save(buffer, format='JPEG')
    return buffer.getvalue()

def test_health_check():
    """Test API Health Check - GET /api/health"""
    print("\n=== Testing API Health Check ===")
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "healthy":
                print("✅ Health check PASSED")
                return True
            else:
                print("❌ Health check FAILED - Invalid response format")
                return False
        else:
            print(f"❌ Health check FAILED - Status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Health check FAILED - Error: {str(e)}")
        return False

def test_image_upload():
    """Test Image Upload and Face Detection - POST /api/upload-image"""
    print("\n=== Testing Image Upload and Face Detection ===")
    try:
        # Create test image
        image_data = create_test_image_with_face()
        
        # Prepare file upload
        files = {
            'file': ('test_face.jpg', image_data, 'image/jpeg')
        }
        
        response = requests.post(f"{BACKEND_URL}/upload-image", files=files, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            data = response.json()
            required_fields = ['case_id', 'faces_detected', 'face_count', 'message']
            
            if all(field in data for field in required_fields):
                print("✅ Image upload PASSED")
                return True, data.get('case_id')
            else:
                print("❌ Image upload FAILED - Missing required fields")
                return False, None
        else:
            print(f"❌ Image upload FAILED - Status code: {response.status_code}")
            return False, None
            
    except Exception as e:
        print(f"❌ Image upload FAILED - Error: {str(e)}")
        return False, None

def test_face_enhancement(case_id):
    """Test Face Enhancement API - POST /api/enhance-face/{case_id}"""
    print(f"\n=== Testing Face Enhancement for case_id: {case_id} ===")
    try:
        response = requests.post(f"{BACKEND_URL}/enhance-face/{case_id}", timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            data = response.json()
            required_fields = ['result_id', 'enhanced_image', 'confidence_score', 'method_used', 'message']
            
            if all(field in data for field in required_fields):
                print("✅ Face enhancement PASSED")
                return True, data.get('result_id')
            else:
                print("❌ Face enhancement FAILED - Missing required fields")
                return False, None
        else:
            print(f"❌ Face enhancement FAILED - Status code: {response.status_code}")
            return False, None
            
    except Exception as e:
        print(f"❌ Face enhancement FAILED - Error: {str(e)}")
        return False, None

def test_get_case(case_id):
    """Test Get Case - GET /api/case/{case_id}"""
    print(f"\n=== Testing Get Case for case_id: {case_id} ===")
    try:
        response = requests.get(f"{BACKEND_URL}/case/{case_id}", timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            required_fields = ['case_id', 'original_image', 'filename', 'upload_time', 'faces_detected', 'face_count', 'status']
            
            if all(field in data for field in required_fields):
                print("✅ Get case PASSED")
                print(f"Case status: {data.get('status')}")
                print(f"Faces detected: {data.get('faces_detected')}")
                print(f"Face count: {data.get('face_count')}")
                return True
            else:
                print("❌ Get case FAILED - Missing required fields")
                return False
        else:
            print(f"❌ Get case FAILED - Status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Get case FAILED - Error: {str(e)}")
        return False

def test_get_all_cases():
    """Test Get All Cases - GET /api/cases"""
    print("\n=== Testing Get All Cases ===")
    try:
        response = requests.get(f"{BACKEND_URL}/cases", timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if 'cases' in data and isinstance(data['cases'], list):
                print(f"✅ Get all cases PASSED - Found {len(data['cases'])} cases")
                return True
            else:
                print("❌ Get all cases FAILED - Invalid response format")
                return False
        else:
            print(f"❌ Get all cases FAILED - Status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Get all cases FAILED - Error: {str(e)}")
        return False

def test_invalid_case_id():
    """Test error handling with invalid case ID"""
    print("\n=== Testing Error Handling with Invalid Case ID ===")
    try:
        invalid_case_id = "invalid-case-id-12345"
        response = requests.get(f"{BACKEND_URL}/case/{invalid_case_id}", timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 404:
            print("✅ Error handling PASSED - Correctly returned 404 for invalid case ID")
            return True
        else:
            print(f"❌ Error handling FAILED - Expected 404, got {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error handling test FAILED - Error: {str(e)}")
        return False

def main():
    """Run all backend API tests"""
    print("🚀 Starting AI Face Reconstruction Backend API Tests")
    print(f"Testing against: {BACKEND_URL}")
    
    results = {
        'health_check': False,
        'image_upload': False,
        'face_enhancement': False,
        'get_case': False,
        'get_all_cases': False,
        'error_handling': False
    }
    
    case_id = None
    result_id = None
    
    # Test 1: Health Check
    results['health_check'] = test_health_check()
    
    # Test 2: Image Upload
    results['image_upload'], case_id = test_image_upload()
    
    # Test 3: Face Enhancement (only if upload succeeded)
    if case_id:
        results['face_enhancement'], result_id = test_face_enhancement(case_id)
        
        # Test 4: Get Case (only if we have a case_id)
        results['get_case'] = test_get_case(case_id)
    
    # Test 5: Get All Cases
    results['get_all_cases'] = test_get_all_cases()
    
    # Test 6: Error Handling
    results['error_handling'] = test_invalid_case_id()
    
    # Summary
    print("\n" + "="*50)
    print("🏁 TEST SUMMARY")
    print("="*50)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✅ PASSED" if passed_test else "❌ FAILED"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All backend API tests PASSED!")
        return True
    else:
        print("⚠️  Some backend API tests FAILED!")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)