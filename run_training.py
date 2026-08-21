"""
Optimized Seatbelt Detection Training Script
High-performance training with advanced optimization techniques
"""

import os
import shutil
import time
import json
import torch
import psutil
from pathlib import Path
from ultralytics import YOLO
import matplotlib.pyplot as plt
from sklearn.model_selection import KFold
import numpy as np

def setup_dataset():
    """Organize images into YOLOv8 format"""
    print("📁 Setting up seatbelt dataset...")
    
    base_path = Path(__file__).parent
    
    # Source folders
    seatbelt_source = base_path / "archive (2)" / "images.cv_6zo3bssqvgd8yvuq188n3s" / "data" / "train" / "seat_belt"
    no_seatbelt_source = base_path / "no seatbelt.v3i.yolov8" / "train" / "images"
    
    # Destination
    dataset_path = base_path / "seatbelt_dataset"
    train_seatbelt_dest = dataset_path / "train" / "seatbelt"
    train_no_seatbelt_dest = dataset_path / "train" / "no_seatbelt"
    val_seatbelt_dest = dataset_path / "val" / "seatbelt"
    val_no_seatbelt_dest = dataset_path / "val" / "no_seatbelt"
    
    # Create directories
    for dest_dir in [train_seatbelt_dest, train_no_seatbelt_dest, val_seatbelt_dest, val_no_seatbelt_dest]:
        dest_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy images (only if not already done)
    if not any(train_seatbelt_dest.glob("*.jpg")):
        copy_images(seatbelt_source, train_seatbelt_dest)
        print(f"✅ Copied seatbelt images")
    
    if not any(train_no_seatbelt_dest.glob("*.jpg")):
        copy_images(no_seatbelt_source, train_no_seatbelt_dest)
        print(f"✅ Copied no-seatbelt images")
    
    # Split some training images to validation (20%)
    if not any(val_seatbelt_dest.glob("*.jpg")):
        split_for_validation(train_seatbelt_dest, val_seatbelt_dest, 0.2)
        split_for_validation(train_no_seatbelt_dest, val_no_seatbelt_dest, 0.2)
        print(f"✅ Created validation split")
    
    return dataset_path

def copy_images(source_dir, dest_dir):
    """Copy all images from source to destination"""
    if not source_dir.exists():
        return
    
    for img in source_dir.glob("*.jpg"):
        shutil.copy2(img, dest_dir / img.name)

def split_for_validation(train_dir, val_dir, val_ratio=0.2):
    """Move some training images to validation"""
    images = list(train_dir.glob("*.jpg"))
    val_count = int(len(images) * val_ratio)
    
    for img in images[:val_count]:
        shutil.move(str(img), str(val_dir / img.name))

def count_images(directory):
    """Count images in directory"""
    return len(list(directory.glob("*.jpg"))) if directory.exists() else 0

def detect_optimal_device():
    """🎯 Automatically detect the best available device"""
    try:
        import torch
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            print(f"🚀 GPU Detected: {gpu_name} ({gpu_memory:.1f} GB VRAM)")
            return 'cuda'
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            print(f"🍎 Apple M1/M2 GPU detected")
            return 'mps'
    except ImportError:
        pass
    
    cpu_count = os.cpu_count()
    print(f"💻 Using CPU: {cpu_count} cores")
    return 'cpu'

def calculate_optimal_batch_size(device):
    """📊 Calculate optimal batch size based on available hardware"""
    try:
        import torch
        import psutil
        
        if device == 'cuda':
            gpu_memory_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            if gpu_memory_gb >= 8:
                return 64  # High-end GPU
            elif gpu_memory_gb >= 4:
                return 32  # Mid-range GPU
            else:
                return 16  # Budget GPU
        else:
            available_memory_gb = psutil.virtual_memory().available / (1024**3)
            if available_memory_gb >= 16:
                return 32
            elif available_memory_gb >= 8:
                return 16
            else:
                return 8
    except ImportError:
        return 16  # Safe default

def train_model():
    """Train the seatbelt detection model with optimizations"""
    print("🚗 EFFICIENT SEATBELT DETECTION TRAINING")
    print("=" * 50)
    
    # Detect optimal hardware configuration
    device = detect_optimal_device()
    batch_size = calculate_optimal_batch_size(device)
    
    print(f"🔧 Optimization Settings:")
    print(f"   Device: {device}")
    print(f"   Optimal batch size: {batch_size}")
    
    # Setup dataset
    dataset_path = setup_dataset()
    
    # Count images
    train_seatbelt_count = count_images(dataset_path / "train" / "seatbelt")
    train_no_seatbelt_count = count_images(dataset_path / "train" / "no_seatbelt")
    val_seatbelt_count = count_images(dataset_path / "val" / "seatbelt")
    val_no_seatbelt_count = count_images(dataset_path / "val" / "no_seatbelt")
    
    print(f"\n📊 Dataset Summary:")
    print(f"✅ Training Seatbelt: {train_seatbelt_count}")
    print(f"⚠️  Training No Seatbelt: {train_no_seatbelt_count}")
    print(f"✅ Validation Seatbelt: {val_seatbelt_count}")
    print(f"⚠️  Validation No Seatbelt: {val_no_seatbelt_count}")
    print(f"📈 Total: {sum([train_seatbelt_count, train_no_seatbelt_count, val_seatbelt_count, val_no_seatbelt_count])}")
    
    total_images = sum([train_seatbelt_count, train_no_seatbelt_count, val_seatbelt_count, val_no_seatbelt_count])
    if total_images < 20:
        print("❌ Not enough images for training (need at least 20)")
        return
    
    print(f"\n🚀 Starting optimized training...")
    
    # Import required modules
    try:
        import torch
        from ultralytics import YOLO
        import time
        
        # Apply PyTorch compatibility fix
        original_load = torch.load
        def patched_load(*args, **kwargs):
            kwargs.pop('weights_only', None)  # Remove problematic parameter
            return original_load(*args, **kwargs)
        torch.load = patched_load
        
        print("🔧 Applied PyTorch compatibility fix")
        
        # Load model with fallback
        try:
            model = YOLO('yolov8n-cls.pt')
            print("✅ Loaded pretrained YOLOv8n-cls model")
            epochs = 50  # Fewer epochs with pretrained weights
        except Exception as e:
            print(f"⚠️  Pretrained model failed, using architecture only...")
            model = YOLO('yolov8n-cls.yaml') 
            print("✅ Created model from architecture")
            epochs = 100  # More epochs when training from scratch
        
        # Restore original torch.load
        torch.load = original_load
        
        # Check for mixed precision support
        use_mixed_precision = False
        if device == 'cuda':
            try:
                major, minor = torch.cuda.get_device_capability(0)
                use_mixed_precision = major >= 7 or (major == 6 and minor >= 1)
                if use_mixed_precision:
                    print("⚡ Mixed precision training enabled - expect ~2x speed boost!")
            except:
                pass
        
        # Optimized training configuration
        training_config = {
            'data': str(dataset_path),
            'epochs': epochs,
            'imgsz': 224,
            'batch': batch_size,
            'device': device,
            'project': 'seatbelt_model',
            'name': f'efficient_run_{int(time.time())}',
            'patience': 15,  # Early stopping
            'cache': True,  # Cache images for faster loading
            'workers': min(8, os.cpu_count()),  # Optimal workers
            'optimizer': 'AdamW',  # Better optimizer
            'lr0': 0.001,  # Learning rate
            'cos_lr': True,  # Cosine LR scheduler
            'augment': True,  # Data augmentation
        }
        
        # Add mixed precision if supported
        if use_mixed_precision:
            training_config['amp'] = True
        
        print(f"\n📋 Training with configuration:")
        for key, value in training_config.items():
            print(f"   {key}: {value}")
        
        # Start training with timing
        start_time = time.time()
        results = model.train(**training_config)
        training_time = time.time() - start_time
        
        print(f"\n🎉 SUCCESS! Model trained in {training_time/60:.1f} minutes!")
        print(f"📁 Saved at: {results.save_dir}")
        print(f"🎯 Best weights: {results.save_dir}/weights/best.pt")
        
        # Evaluate model performance
        try:
            print(f"\n🎯 Evaluating model performance...")
            val_results = model.val()
            if hasattr(val_results, 'top1'):
                print(f"✅ Validation Accuracy: {val_results.top1:.1%}")
        except Exception as e:
            print(f"⚠️  Evaluation failed: {e}")
        
        # Create optimized usage script
        create_classifier_script(f"{results.save_dir}/weights/best.pt")
        
        return True
        
    except Exception as e:
        print(f"❌ Optimized training failed: {e}")
        import traceback
        traceback.print_exc()
        
        # Fallback to simple command
        print(f"\n💡 Try this PowerShell command for manual training:")
        print(f"$env:TORCH_WEIGHTS_ONLY='0'; yolo classify train data='{dataset_path.name}' model=yolov8n-cls.pt epochs=50 imgsz=224 batch={batch_size} device={device} cache=True")
        
        return False

def create_classifier_script(model_path):
    """Create a simple classifier script"""
    script = f'''"""
Seatbelt Detection Classifier
Use this script to classify your images
"""

from ultralytics import YOLO
from pathlib import Path

def classify_image(image_path):
    """Classify a single image"""
    model = YOLO(r"{model_path}")
    results = model(image_path)
    
    result = results[0]
    class_name = result.names[result.probs.top1]
    confidence = result.probs.top1conf.item()
    
    print(f"Image: {{Path(image_path).name}}")
    print(f"Result: {{class_name}} ({{confidence:.1%}})")
    
    if "seatbelt" in class_name.lower():
        print("✅ Seatbelt detected!")
    else:
        print("⚠️  No seatbelt detected!")
    
    return class_name, confidence

if __name__ == "__main__":
    # Example usage:
    # classify_image("path/to/your/image.jpg")
    print("Ready to classify! Edit this script with your image path.")
'''
    
    with open('seatbelt_classifier.py', 'w') as f:
        f.write(script)
    
    print("💾 Created: seatbelt_classifier.py")

if __name__ == "__main__":
    train_model()
