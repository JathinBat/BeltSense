"""
Run Seatbelt Detection Model with Random Images
This script demonstrates the trained model by classifying random images
from the seatbelt and no-seatbelt datasets.
"""

import random
import torch
from pathlib import Path
from ultralytics import YOLO

def fix_torch_loading():
    """Fix PyTorch loading issue for compatibility"""
    original_load = torch.load
    def patched_load(*args, **kwargs):
        kwargs['weights_only'] = False
        return original_load(*args, **kwargs)
    torch.load = patched_load
    return original_load

def get_random_image(category="random"):
    """
    Get a random image from the dataset
    Args:
        category: "seatbelt", "no_seatbelt", or "random" (default)
    Returns:
        Path to random image file
    """
    base_path = Path(__file__).parent
    
    if category == "seatbelt":
        image_dirs = [base_path / "seatbelt_dataset" / "val" / "seatbelt"]
    elif category == "no_seatbelt":
        image_dirs = [base_path / "seatbelt_dataset" / "val" / "no_seatbelt"]
    else:  # random from both
        image_dirs = [
            base_path / "seatbelt_dataset" / "val" / "seatbelt",
            base_path / "seatbelt_dataset" / "val" / "no_seatbelt"
        ]
    
    # Collect all image files
    all_images = []
    for img_dir in image_dirs:
        if img_dir.exists():
            all_images.extend(list(img_dir.glob("*.jpg")))
    
    if not all_images:
        raise FileNotFoundError("No images found in the dataset directories")
    
    return random.choice(all_images)

def classify_random_image(category="random", model_path=None):
    """
    Classify a random image and display results
    Args:
        category: "seatbelt", "no_seatbelt", or "random"
        model_path: Path to model weights (optional)
    """
    if model_path is None:
        model_path = "seatbelt_model/final/weights/best.pt"
    
    # Get random image
    try:
        image_path = get_random_image(category)
        parent_name = image_path.parent.name
        actual_category = "seatbelt" if parent_name == "seatbelt" else "no_seatbelt"
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        return
    
    print("🎲 RANDOM SEATBELT DETECTION TEST")
    print("=" * 50)
    print(f"🖼️  Selected Image: {image_path.name}")
    print(f"📁 Actual Category: {actual_category}")
    print(f"🤖 Model Path: {model_path}")
    
    # Apply PyTorch fix
    original_load = fix_torch_loading()
    
    try:
        # Load model and predict
        print(f"\n🔧 Loading model...")
        model = YOLO(model_path)
        
        print(f"🔍 Classifying image...")
        results = model(str(image_path))
        
        # Extract results
        result = results[0]
        predicted_class = result.names[result.probs.top1]
        confidence = result.probs.top1conf.item()
        
        # Display results
        print(f"\n📊 CLASSIFICATION RESULTS")
        print(f"🎯 Predicted: {predicted_class}")
        print(f"📈 Confidence: {confidence:.1%}")
        print(f"✅ Actual: {actual_category}")
        
        # Check accuracy
        correct = (predicted_class == actual_category)
        if correct:
            print(f"🎉 CORRECT PREDICTION!")
        else:
            print(f"❌ INCORRECT PREDICTION")
        
        # Visual indicator
        if predicted_class.lower() == "seatbelt":
            print("✅ SEATBELT DETECTED!")
        else:
            print("⚠️  NO SEATBELT DETECTED!")
            
        return {
            'image_path': str(image_path),
            'predicted': predicted_class,
            'confidence': confidence,
            'actual': actual_category,
            'correct': correct
        }
        
    except Exception as e:
        print(f"❌ Error during classification: {e}")
        return None
    finally:
        # Restore original torch.load
        torch.load = original_load

def run_multiple_tests(num_tests=5):
    """Run multiple random tests and show accuracy"""
    print("🔄 RUNNING MULTIPLE RANDOM TESTS")
    print("=" * 50)
    
    results = []
    for i in range(num_tests):
        print(f"\n--- Test {i+1}/{num_tests} ---")
        result = classify_random_image()
        if result:
            results.append(result)
        print()
    
    # Calculate accuracy
    if results:
        correct_count = sum(1 for r in results if r['correct'])
        accuracy = correct_count / len(results)
        
        print("📊 SUMMARY")
        print("=" * 30)
        print(f"✅ Correct Predictions: {correct_count}/{len(results)}")
        print(f"📈 Accuracy: {accuracy:.1%}")
        
        # Show individual results
        print(f"\n📋 Individual Results:")
        for i, result in enumerate(results, 1):
            status = "✅" if result['correct'] else "❌"
            print(f"{status} Test {i}: {result['predicted']} ({result['confidence']:.1%}) - Actual: {result['actual']}")
    
    return results

if __name__ == "__main__":
    print("🚗 SEATBELT DETECTION MODEL TESTER")
    print("=" * 50)
    print("Choose an option:")
    print("1. Test random image (any category)")
    print("2. Test random seatbelt image")  
    print("3. Test random no-seatbelt image")
    print("4. Run multiple random tests")
    print("5. Quick single test")
    
    try:
        choice = input("\nEnter your choice (1-5) or press Enter for quick test: ").strip()
        
        if choice == "1" or choice == "":
            classify_random_image("random")
        elif choice == "2":
            classify_random_image("seatbelt")
        elif choice == "3":
            classify_random_image("no_seatbelt")
        elif choice == "4":
            run_multiple_tests(int(input("Enter number of tests: ")))
        elif choice == "5":
            classify_random_image("random")
        else:
            print("Invalid choice, running quick test...")
            classify_random_image("random")
            
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")