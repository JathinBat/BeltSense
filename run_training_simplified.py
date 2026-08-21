"""
Simplified Seatbelt Detection Training Script
Uses ONLY seatbelt_ACTUALLY_FILTERED dataset with cross-validation support
"""

import os
import shutil
import time
import json
import warnings
import yaml
from pathlib import Path
from typing import Dict, List, Optional
import psutil
import torch
from ultralytics import YOLO

warnings.filterwarnings("ignore")

class SeatbeltTrainer:
    def __init__(self):
        self.base_path = Path(__file__).parent
        self.dataset_path = self.base_path / "seatbelt_ACTUALLY_FILTERED" / "seatbelt_dataset" / "seatbelt_dataset"
        self.results_path = self.base_path / "training_results"
        self.results_path.mkdir(exist_ok=True)
        
        # Training config
        self.config = {
            'img_size': 224,
            'epochs': 40,
            'patience': 8,
            'lr': 0.001,
            'batch_size': self._get_optimal_batch_size()
        }
        
        # Device detection
        if torch.cuda.is_available():
            self.device = 'cuda'
            print(f"Using GPU: {torch.cuda.get_device_name(0)}")
        else:
            self.device = 'cpu'
            print("Using CPU")

    def _get_optimal_batch_size(self) -> int:
        """Calculate optimal batch size based on available memory"""
        memory_gb = psutil.virtual_memory().available / (1024**3)
        if torch.cuda.is_available():
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            return 64 if gpu_memory >= 8 else 32 if gpu_memory >= 4 else 16
        return 32 if memory_gb >= 16 else 16 if memory_gb >= 8 else 8

    def _convert_to_grayscale(self):
        """Convert images to grayscale as requested"""
        import cv2
        converted = 0
        
        for split in ['train', 'val']:
            for class_name in ['seatbelt', 'no_seatbelt']:
                class_dir = self.dataset_path / split / class_name
                if class_dir.exists():
                    for img_path in class_dir.glob("*.jpg"):
                        try:
                            img = cv2.imread(str(img_path))
                            if img is not None:
                                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                                gray_3ch = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
                                cv2.imwrite(str(img_path), gray_3ch)
                                converted += 1
                        except Exception:
                            pass
        print(f"Converted {converted} images to grayscale")

    def setup_dataset(self) -> tuple[Path, Dict]:
        """Setup dataset and create config, return dataset stats"""
        if not self.dataset_path.exists():
            raise FileNotFoundError(f"Dataset not found: {self.dataset_path}")
        
        # Count images and check validation set
        dataset_stats = {}
        total_images = 0
        min_val_images = float('inf')
        
        for split in ['train', 'val']:
            for class_name in ['seatbelt', 'no_seatbelt']:
                class_dir = self.dataset_path / split / class_name
                if class_dir.exists():
                    images = list(class_dir.glob("*.jpg"))
                    count = len(images)
                    total_images += count
                    dataset_stats[f"{split}_{class_name}"] = count
                    print(f"{split}/{class_name}: {count} images")
                    
                    if split == 'val':
                        min_val_images = min(min_val_images, count)
        
        if total_images == 0:
            raise ValueError("No images found!")
        
        # Check if validation set is adequate (at least 10 images per class)
        val_adequate = min_val_images >= 10
        dataset_stats['validation_adequate'] = val_adequate
        
        if not val_adequate:
            print(f"⚠️  Validation set inadequate (min {min_val_images} images per class)")
            print("Will use cross-validation instead of standard training")
        
        # Convert to grayscale
        self._convert_to_grayscale()
        
        # Create dataset.yaml
        config = {
            'path': str(self.dataset_path).replace('\\', '/'),
            'train': 'train',
            'val': 'val',
            'nc': 2,
            'names': ['no_seatbelt', 'seatbelt']
        }
        
        with open(self.dataset_path / 'dataset.yaml', 'w') as f:
            yaml.dump(config, f)
        
        return self.dataset_path, dataset_stats

    def _load_model(self) -> YOLO:
        """Load YOLOv8 model"""
        try:
            return YOLO('yolov8n-cls.pt')
        except Exception:
            return YOLO('yolov8n-cls.yaml')

    def train_standard(self) -> Dict:
        """Standard training with train/val split"""
        print("Starting standard training...")
        
        dataset_path, stats = self.setup_dataset()
        
        # Check if validation is adequate, auto-switch to k-fold if not
        if not stats['validation_adequate']:
            print("🔄 Auto-switching to 5-fold cross-validation due to inadequate validation set")
            return self.train_cross_validation(5)
        
        model = self._load_model()
        
        start_time = time.time()
        
        results = model.train(
            data=str(dataset_path).replace('\\', '/'),
            epochs=self.config['epochs'],
            imgsz=self.config['img_size'],
            batch=self.config['batch_size'],
            device=self.device,
            project=str(self.results_path),
            name=f'run_{int(time.time())}',
            patience=self.config['patience'],
            lr0=self.config['lr'],
            optimizer='AdamW',
            cache=True
        )
        
        training_time = time.time() - start_time
        
        return {
            'success': True,
            'model_path': str(results.save_dir / 'weights' / 'best.pt'),
            'training_time': training_time,
            'method': 'Standard Training'
        }

    def train_cross_validation(self, k_folds: int = 5) -> Dict:
        """K-Fold cross-validation training"""
        print(f"Starting {k_folds}-fold cross-validation...")
        
        # Setup base dataset
        dataset_path, stats = self.setup_dataset()
        
        # Collect ALL images (train + val) for cross-validation
        all_images = {'seatbelt': [], 'no_seatbelt': []}
        for split in ['train', 'val']:
            for class_name in ['seatbelt', 'no_seatbelt']:
                class_dir = self.dataset_path / split / class_name
                if class_dir.exists():
                    all_images[class_name].extend(list(class_dir.glob("*.jpg")))
        
        fold_results = []
        
        for fold in range(k_folds):
            print(f"Training fold {fold + 1}/{k_folds}")
            
            # Create fold dataset
            fold_path = self._create_fold_dataset(all_images, fold, k_folds)
            
            # Train model for this fold
            model = self._load_model()
            
            results = model.train(
                data=str(fold_path).replace('\\', '/'),
                epochs=self.config['epochs'],
                imgsz=self.config['img_size'],
                batch=self.config['batch_size'],
                device=self.device,
                project=str(self.results_path),
                name=f'fold_{fold + 1}_{int(time.time())}',
                patience=self.config['patience'],
                lr0=self.config['lr'],
                optimizer='AdamW',
                cache=True,
                verbose=False
            )
            
            # Validate
            val_results = model.val(data=str(fold_path).replace('\\', '/'))
            
            fold_results.append({
                'fold': fold + 1,
                'accuracy': float(val_results.top1),
                'model_path': str(results.save_dir / 'weights' / 'best.pt')
            })
            
            print(f"Fold {fold + 1} accuracy: {float(val_results.top1):.1%}")
        
        # Calculate statistics
        accuracies = [r['accuracy'] for r in fold_results]
        mean_acc = sum(accuracies) / len(accuracies)
        std_acc = (sum((acc - mean_acc) ** 2 for acc in accuracies) / len(accuracies)) ** 0.5
        
        best_fold = max(fold_results, key=lambda x: x['accuracy'])
        
        return {
            'success': True,
            'mean_accuracy': mean_acc,
            'std_accuracy': std_acc,
            'fold_results': fold_results,
            'best_model_path': best_fold['model_path'],
            'method': f'{k_folds}-Fold Cross-Validation'
        }

    def _create_fold_dataset(self, train_images: Dict, fold: int, k_folds: int) -> Path:
        """Create dataset for specific fold"""
        import random
        
        fold_path = self.results_path / f'fold_{fold + 1}_dataset'
        
        # Create directories
        for split in ['train', 'val']:
            for class_name in ['seatbelt', 'no_seatbelt']:
                (fold_path / split / class_name).mkdir(parents=True, exist_ok=True)
        
        # Split images for each class
        for class_name, images in train_images.items():
            shuffled = images.copy()
            random.shuffle(shuffled)
            
            # Calculate fold boundaries
            fold_size = len(shuffled) // k_folds
            start_idx = fold * fold_size
            end_idx = start_idx + fold_size if fold < k_folds - 1 else len(shuffled)
            
            # Split: current fold for validation, others for training
            val_images = shuffled[start_idx:end_idx]
            train_images_fold = shuffled[:start_idx] + shuffled[end_idx:]
            
            # Copy files
            for img in train_images_fold:
                shutil.copy2(img, fold_path / 'train' / class_name / img.name)
            
            for img in val_images:
                shutil.copy2(img, fold_path / 'val' / class_name / img.name)
        
        # Create config
        config = {
            'path': str(fold_path).replace('\\', '/'),
            'train': 'train',
            'val': 'val',
            'nc': 2,
            'names': ['no_seatbelt', 'seatbelt']
        }
        
        with open(fold_path / 'dataset.yaml', 'w') as f:
            yaml.dump(config, f)
        
        return fold_path

def create_classifier_script(model_path: str):
    """Create optimized classifier script"""
    script = f'''from ultralytics import YOLO

class SeatbeltClassifier:
    def __init__(self):
        self.model = YOLO(r"{model_path}")
    
    def classify(self, image_path: str) -> dict:
        results = self.model(image_path)
        result = results[0]
        
        class_id = result.probs.top1
        class_name = result.names[class_id]
        confidence = float(result.probs.top1conf)
        wearing_seatbelt = class_id == 1
        
        return {{
            'class': class_name,
            'confidence': confidence,
            'wearing_seatbelt': wearing_seatbelt
        }}

# Usage: classifier = SeatbeltClassifier()
#        result = classifier.classify("image.jpg")
'''
    
    with open('seatbelt_classifier.py', 'w') as f:
        f.write(script)

def main():
    print("Seatbelt Detection Training")
    print("=" * 40)
    
    trainer = SeatbeltTrainer()
    
    # Check dataset first to recommend training method
    try:
        _, stats = trainer.setup_dataset()
        
        print("Training methods:")
        if stats['validation_adequate']:
            print("1. Standard (recommended - adequate validation set)")
            print("2. 5-Fold Cross-Validation")
            print("3. 10-Fold Cross-Validation")
            default_choice = "1"
        else:
            print("1. Standard (will auto-switch to k-fold)")
            print("2. 5-Fold Cross-Validation (recommended - small validation set)")
            print("3. 10-Fold Cross-Validation")
            default_choice = "2"
        
        choice = input(f"Choice [{default_choice}]: ").strip() or default_choice
        
        if choice == "2":
            results = trainer.train_cross_validation(5)
        elif choice == "3":
            results = trainer.train_cross_validation(10)
        else:
            results = trainer.train_standard()
        
        if results['success']:
            print(f"\nTraining completed successfully!")
            
            if 'Cross-Validation' in results['method']:
                print(f"Mean accuracy: {results['mean_accuracy']:.1%} ± {results['std_accuracy']:.1%}")
                model_path = results['best_model_path']
            else:
                print(f"Training time: {results['training_time']/60:.1f} minutes")
                model_path = results['model_path']
            
            print(f"Best model: {model_path}")
            
            # Create classifier script
            create_classifier_script(model_path)
            print("Created: seatbelt_classifier.py")
            
        else:
            print("Training failed!")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()