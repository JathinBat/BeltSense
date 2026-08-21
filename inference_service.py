#!/usr/bin/env python3
"""
Seatbelt Detection Inference Service

A simple HTTP service that receives images and returns seatbelt detection results.
This service loads the trained YOLO model and provides inference via HTTP API.
"""

import os
import sys
import json
import base64
import io
from typing import Dict, Any
import numpy as np
from PIL import Image
import cv2
from flask import Flask, request, jsonify
from flask_cors import CORS

# Add the current directory to Python path for imports
sys.path.append(os.getcwd())

app = Flask(__name__)
CORS(app)  # Enable CORS for Flutter web

# Global variables
model = None
model_loaded = False

def load_model():
    """Load the trained YOLO model."""
    global model, model_loaded
    
    try:
        from ultralytics import YOLO
        
        model_path = "training_results/optimized_run_1759620168/weights/best.pt"
        
        if not os.path.exists(model_path):
            print(f"Error: Model file not found at {model_path}")
            return False
        
        model = YOLO(model_path)
        model_loaded = True
        print(f"✅ Model loaded successfully from: {model_path}")
        return True
        
    except Exception as e:
        print(f"Error loading model: {e}")
        return False

def preprocess_image(image_data: bytes, target_size: int = 224) -> np.ndarray:
    """
    Preprocess image for YOLO inference.
    Converts to grayscale then back to RGB (matching training preprocessing).
    """
    try:
        # Load image from bytes
        image = Image.open(io.BytesIO(image_data))
        
        # Convert to RGB if not already
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Convert to numpy array
        img_array = np.array(image)
        
        # Convert to grayscale (matching training preprocessing)
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        
        # Convert back to 3-channel RGB (grayscale in all channels)
        rgb_gray = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)
        
        # Resize to target size
        resized = cv2.resize(rgb_gray, (target_size, target_size))
        
        return resized
        
    except Exception as e:
        print(f"Error preprocessing image: {e}")
        return None

def run_inference(image_array: np.ndarray) -> Dict[str, Any]:
    """Run inference on the preprocessed image."""
    global model, model_loaded
    
    if not model_loaded or model is None:
        return {
            "error": "Model not loaded",
            "class": "unknown",
            "confidence": 0.0,
            "has_seatbelt": False
        }
    
    try:
        # Run inference
        results = model(image_array, verbose=False)
        
        # Extract results
        if results and len(results) > 0:
            result = results[0]
            
            # Get classification results
            if hasattr(result, 'probs') and result.probs is not None:
                probs = result.probs
                class_id = int(probs.top1)  # Index of highest probability class
                confidence = float(probs.top1conf)  # Highest probability value
                
                # Class names: 0 = no_seatbelt, 1 = seatbelt
                class_names = ["no_seatbelt", "seatbelt"]
                class_name = class_names[class_id] if class_id < len(class_names) else "unknown"
                has_seatbelt = class_id == 1
                
                return {
                    "class": class_name,
                    "confidence": confidence,
                    "has_seatbelt": has_seatbelt,
                    "class_id": class_id,
                    "error": None
                }
            else:
                return {
                    "error": "No classification results available",
                    "class": "unknown",
                    "confidence": 0.0,
                    "has_seatbelt": False
                }
        else:
            return {
                "error": "No results from model",
                "class": "unknown", 
                "confidence": 0.0,
                "has_seatbelt": False
            }
            
    except Exception as e:
        print(f"Error during inference: {e}")
        return {
            "error": str(e),
            "class": "unknown",
            "confidence": 0.0,
            "has_seatbelt": False
        }

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "model_loaded": model_loaded,
        "service": "seatbelt_detection"
    })

@app.route('/detect', methods=['POST'])
def detect_seatbelt():
    """
    Main detection endpoint.
    Expects JSON with base64 encoded image data.
    """
    try:
        # Get JSON data from request
        data = request.get_json()
        
        if not data or 'image' not in data:
            return jsonify({
                "error": "No image data provided",
                "class": "unknown",
                "confidence": 0.0,
                "has_seatbelt": False
            }), 400
        
        # Decode base64 image
        try:
            image_data = base64.b64decode(data['image'])
        except Exception as e:
            return jsonify({
                "error": f"Invalid base64 image data: {e}",
                "class": "unknown", 
                "confidence": 0.0,
                "has_seatbelt": False
            }), 400
        
        # Preprocess image
        processed_image = preprocess_image(image_data)
        if processed_image is None:
            return jsonify({
                "error": "Image preprocessing failed",
                "class": "unknown",
                "confidence": 0.0,
                "has_seatbelt": False
            }), 400
        
        # Run inference
        result = run_inference(processed_image)
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Error in detect endpoint: {e}")
        return jsonify({
            "error": str(e),
            "class": "unknown",
            "confidence": 0.0,
            "has_seatbelt": False
        }), 500

@app.route('/detect_file', methods=['POST'])
def detect_seatbelt_file():
    """
    Alternative detection endpoint that accepts multipart file upload.
    """
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({
                "error": "No file provided",
                "class": "unknown",
                "confidence": 0.0,
                "has_seatbelt": False
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                "error": "No file selected",
                "class": "unknown",
                "confidence": 0.0,
                "has_seatbelt": False
            }), 400
        
        # Read file data
        image_data = file.read()
        
        # Preprocess image
        processed_image = preprocess_image(image_data)
        if processed_image is None:
            return jsonify({
                "error": "Image preprocessing failed",
                "class": "unknown",
                "confidence": 0.0,
                "has_seatbelt": False
            }), 400
        
        # Run inference
        result = run_inference(processed_image)
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Error in detect_file endpoint: {e}")
        return jsonify({
            "error": str(e),
            "class": "unknown",
            "confidence": 0.0,
            "has_seatbelt": False
        }), 500

def main():
    """Main function to start the inference service."""
    print("🚗 Starting Seatbelt Detection Inference Service...")
    
    # Load the model
    if not load_model():
        print("❌ Failed to load model. Exiting.")
        return
    
    print("🌐 Starting HTTP server on http://localhost:8080")
    print("📱 Flutter app can now connect to this service for real inference")
    print("\nEndpoints:")
    print("  GET  /health     - Service health check")
    print("  POST /detect     - Detect seatbelt (JSON with base64 image)")
    print("  POST /detect_file - Detect seatbelt (multipart file upload)")
    print("\nPress Ctrl+C to stop the service")
    
    try:
        app.run(host='0.0.0.0', port=8080, debug=False, threaded=True)
    except KeyboardInterrupt:
        print("\n🛑 Service stopped by user")
    except Exception as e:
        print(f"\n❌ Service error: {e}")

if __name__ == "__main__":
    main()