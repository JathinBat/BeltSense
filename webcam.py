"""
Simple Webcam Seatbelt Detection
One file to rule them all - just run this and it works!
"""

import cv2
import torch
import numpy as np
from ultralytics import YOLO
import time

def fix_torch_loading():
    """Fix PyTorch loading issue"""
    original_load = torch.load
    def patched_load(*args, **kwargs):
        kwargs['weights_only'] = False
        return original_load(*args, **kwargs)
    torch.load = patched_load
    return original_load

def run_webcam_detection():
    """Main function - does everything in one place"""
    print("🚗 WEBCAM SEATBELT DETECTION")
    print("=" * 40)
    
    # 1. Load the model
    print("🔧 Loading AI model...")
    try:
        original_load = fix_torch_loading()
        model = YOLO("seatbelt_model/final/weights/best.pt")
        torch.load = original_load
        print("✅ Model loaded!")
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        print("Make sure you have run the training first!")
        return
    
    # 2. Start webcam
    print("📷 Starting webcam...")
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("❌ Could not open webcam!")
        print("Make sure your webcam is connected and not used by another app")
        return
    
    print("✅ Webcam started!")
    print("\n📋 CONTROLS:")
    print("   Press 'q' to quit")
    print("   Press 's' to save screenshot")
    print("=" * 40)
    
    # 3. Main loop
    frame_count = 0
    prediction = "loading"
    confidence = 0.0
    last_high_confidence_prediction = "loading"
    last_high_confidence = 0.0
    
    try:
        while True:
            # Get frame from webcam
            ret, frame = cap.read()
            if not ret:
                break
            
            # Flip for mirror effect
            frame = cv2.flip(frame, 1)
            
            # Classify every 2 frames (for faster updates)
            if frame_count % 2 == 0:
                try:
                    # Resize and predict
                    small_frame = cv2.resize(frame, (224, 224))
                    results = model(small_frame, verbose=False)
                    
                    # Get results
                    result = results[0]
                    prediction = result.names[result.probs.top1]
                    confidence = result.probs.top1conf.item()
                    
                    # Only update display if confidence is above 70%
                    if confidence > 0.70:
                        last_high_confidence_prediction = prediction
                        last_high_confidence = confidence
                    
                except Exception as e:
                    prediction = "error"
                    confidence = 0.0
            
            # 4. Draw results on frame (using last high-confidence prediction)
            height, width = frame.shape[:2]
            
            # Use the last high-confidence prediction for display
            display_prediction = last_high_confidence_prediction
            display_confidence = last_high_confidence
            
            # Choose colors and text
            if display_prediction == "seatbelt":
                color = (0, 255, 0)  # Green
                status = "✅ SEATBELT ON - SAFE"
                bg_color = (0, 100, 0)
            elif display_prediction == "no_seatbelt":
                color = (0, 0, 255)  # Red  
                status = "⚠️ NO SEATBELT - UNSAFE"
                bg_color = (0, 0, 100)
            else:
                color = (255, 255, 0)  # Yellow
                status = "🔄 LOADING..."
                bg_color = (100, 100, 0)
            
            # Draw background box
            cv2.rectangle(frame, (10, 10), (width-10, 120), (0, 0, 0), -1)
            cv2.rectangle(frame, (10, 10), (width-10, 120), color, 3)
            
            # Draw main text
            cv2.putText(frame, status, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
            
            # Draw confidence
            if display_confidence > 0:
                conf_text = f"Confidence: {display_confidence:.1%}"
                cv2.putText(frame, conf_text, (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Draw instructions at bottom
            cv2.putText(frame, "Press 'q' to quit, 's' for screenshot", 
                       (10, height-20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
            
            # 5. Show the frame
            cv2.imshow('Seatbelt Detection', frame)
            
            # 6. Handle key presses
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                print("👋 Goodbye!")
                break
            elif key == ord('s'):
                # Save screenshot
                filename = f"seatbelt_{display_prediction}_{int(time.time())}.jpg"
                cv2.imwrite(filename, frame)
                print(f"📸 Saved: {filename}")
            
            frame_count += 1
    
    except KeyboardInterrupt:
        print("\n👋 Stopped by user")
    
    finally:
        # 7. Cleanup
        cap.release()
        cv2.destroyAllWindows()
        print("✅ Done!")

if __name__ == "__main__":
    # Just run it!
    run_webcam_detection()
