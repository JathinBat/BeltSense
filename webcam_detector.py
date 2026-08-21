"""
Real-time Seatbelt Detection using Webcam
This script captures webcam footage and classifies seatbelt usage in real-time
"""

import cv2
import torch
import numpy as np
from ultralytics import YOLO
from pathlib import Path
import time

class WebcamSeatbeltDetector:
    def __init__(self, model_path=None):
        """Initialize the webcam detector"""
        if model_path is None:
            model_path = "seatbelt_model/final/weights/best.pt"
        
        self.model_path = model_path
        self.model = None
        self.cap = None
        self.is_running = False
        
        # Display settings
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.font_scale = 0.7
        self.thickness = 2
        
        # Colors (BGR format for OpenCV)
        self.colors = {
            'seatbelt': (0, 255, 0),      # Green
            'no_seatbelt': (0, 0, 255),   # Red
            'background': (0, 0, 0),       # Black
            'text_bg': (255, 255, 255)    # White
        }
        
    def fix_torch_loading(self):
        """Fix PyTorch loading issue for compatibility"""
        original_load = torch.load
        def patched_load(*args, **kwargs):
            kwargs['weights_only'] = False
            return original_load(*args, **kwargs)
        torch.load = patched_load
        return original_load
        
    def load_model(self):
        """Load the trained seatbelt detection model"""
        try:
            print(f"🔧 Loading model from: {self.model_path}")
            
            # Apply PyTorch fix
            original_load = self.fix_torch_loading()
            
            # Load model
            self.model = YOLO(self.model_path)
            
            # Restore original torch.load
            torch.load = original_load
            
            print("✅ Model loaded successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            return False
    
    def initialize_camera(self, camera_index=0):
        """Initialize webcam capture"""
        try:
            print(f"📷 Initializing camera {camera_index}...")
            self.cap = cv2.VideoCapture(camera_index)
            
            if not self.cap.isOpened():
                raise Exception(f"Could not open camera {camera_index}")
            
            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            
            print("✅ Camera initialized successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Error initializing camera: {e}")
            return False
    
    def classify_frame(self, frame):
        """Classify a single frame"""
        try:
            # Resize frame to model input size (224x224)
            resized_frame = cv2.resize(frame, (224, 224))
            
            # Run inference
            results = self.model(resized_frame, verbose=False)
            
            # Extract results
            result = results[0]
            predicted_class = result.names[result.probs.top1]
            confidence = result.probs.top1conf.item()
            
            return predicted_class, confidence
            
        except Exception as e:
            print(f"❌ Classification error: {e}")
            return None, 0.0
    
    def draw_results(self, frame, prediction, confidence):
        """Draw classification results on frame"""
        height, width = frame.shape[:2]
        
        # Determine result text and color
        if prediction == "seatbelt":
            result_text = "✅ SEATBELT DETECTED"
            color = self.colors['seatbelt']
            status_text = "SAFE"
        else:
            result_text = "⚠️ NO SEATBELT"
            color = self.colors['no_seatbelt']
            status_text = "UNSAFE"
        
        # Draw background rectangles for text
        cv2.rectangle(frame, (10, 10), (width-10, 100), self.colors['background'], -1)
        cv2.rectangle(frame, (10, 10), (width-10, 100), color, 3)
        
        # Draw main result text
        cv2.putText(frame, result_text, (20, 40), self.font, 0.8, color, self.thickness)
        
        # Draw confidence
        confidence_text = f"Confidence: {confidence:.1%}"
        cv2.putText(frame, confidence_text, (20, 70), self.font, 0.6, (255, 255, 255), self.thickness-1)
        
        # Draw status indicator (top right)
        status_bg_color = color if prediction == "seatbelt" else self.colors['no_seatbelt']
        cv2.rectangle(frame, (width-150, 10), (width-10, 60), status_bg_color, -1)
        cv2.putText(frame, status_text, (width-140, 40), self.font, 0.7, (255, 255, 255), self.thickness)
        
        return frame
    
    def draw_instructions(self, frame):
        """Draw usage instructions"""
        height, width = frame.shape[:2]
        
        # Instructions at bottom
        instructions = [
            "Press 'q' to quit",
            "Press 's' to save screenshot",
            "Position yourself in frame"
        ]
        
        y_start = height - 80
        for i, instruction in enumerate(instructions):
            cv2.putText(frame, instruction, (10, y_start + i*20), 
                       self.font, 0.5, (200, 200, 200), 1)
        
        return frame
    
    def save_screenshot(self, frame, prediction, confidence):
        """Save screenshot with timestamp"""
        timestamp = int(time.time())
        filename = f"seatbelt_detection_{prediction}_{timestamp}.jpg"
        
        # Add timestamp to frame
        time_text = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        cv2.putText(frame, time_text, (10, frame.shape[0]-10), 
                   self.font, 0.5, (255, 255, 255), 1)
        
        cv2.imwrite(filename, frame)
        print(f"📸 Screenshot saved: {filename}")
    
    def run(self, camera_index=0):
        """Run real-time seatbelt detection"""
        print("🚗 REAL-TIME SEATBELT DETECTION")
        print("=" * 50)
        
        # Load model
        if not self.load_model():
            return False
        
        # Initialize camera
        if not self.initialize_camera(camera_index):
            return False
        
        print("🎬 Starting real-time detection...")
        print("📋 Controls: 'q' to quit, 's' to save screenshot")
        print("=" * 50)
        
        self.is_running = True
        frame_count = 0
        
        try:
            while self.is_running:
                # Capture frame
                ret, frame = self.cap.read()
                if not ret:
                    print("❌ Failed to capture frame")
                    break
                
                # Flip frame horizontally for mirror effect
                frame = cv2.flip(frame, 1)
                
                # Classify every few frames to improve performance
                if frame_count % 5 == 0:  # Classify every 5th frame
                    prediction, confidence = self.classify_frame(frame)
                
                # Draw results
                if 'prediction' in locals() and prediction:
                    frame = self.draw_results(frame, prediction, confidence)
                else:
                    # Show loading message
                    cv2.putText(frame, "🔄 Loading...", (20, 40), 
                               self.font, 0.8, (255, 255, 0), self.thickness)
                
                # Draw instructions
                frame = self.draw_instructions(frame)
                
                # Display frame
                cv2.imshow('Seatbelt Detection', frame)
                
                # Handle key presses
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    print("👋 Quitting...")
                    break
                elif key == ord('s') and 'prediction' in locals():
                    self.save_screenshot(frame, prediction, confidence)
                
                frame_count += 1
                
        except KeyboardInterrupt:
            print("\n👋 Interrupted by user")
        
        finally:
            self.cleanup()
        
        return True
    
    def cleanup(self):
        """Clean up resources"""
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()
        print("✅ Cleanup completed")

def main():
    """Main function to run webcam detection"""
    detector = WebcamSeatbeltDetector()
    
    print("🎯 Seatbelt Detection - Webcam Mode")
    print("Make sure you have a webcam connected!")
    
    try:
        # Try default camera first
        success = detector.run(camera_index=0)
        
        if not success:
            print("\n🔄 Trying alternative camera...")
            detector.run(camera_index=1)
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("🏁 Session ended")

if __name__ == "__main__":
    main()
