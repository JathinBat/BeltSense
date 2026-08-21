# 🚗 Seatbelt Detection Project

A YOLOv8-based image classifier for detecting whether people in car images are wearing seatbelts.

## 📊 Model Performance
- **Training-time validation accuracy**: 95.7% (epoch 17)
- **Training Images**: 1,710 (767 seatbelt, 943 no-seatbelt)
- **Validation Images**: 370 (133 seatbelt, 237 no-seatbelt)
- **Total Dataset**: 2,080 images

> **Note on the dataset:** the training images are third-party photos of
> identifiable people collected from image search. They are deliberately not
> tracked in this repository — see `.gitignore`.

> **Note on model files:** the only model tracked here is
> `seatbelt_detector_app/assets/models/seatbelt_model.onnx`, which the app runs
> on-device. Training checkpoints (`best.pt`) are not tracked — PyTorch
> checkpoints are pickles that embed the absolute path of the machine that
> produced them. Keep them locally and regenerate the app model with
> `python convert_model_for_flutter.py <path/to/best.pt>`.

## 🎯 Usage

### Train the Model
```bash
python run_training.py
```

### Real-time Webcam Detection 📹
```bash
python webcam_detector.py
```

### Test Random Images
```bash
python runModel.py
```

### Classify Static Images
```python
from seatbelt_classifier import classify_image, classify_folder

# Classify a single image
classify_image("path/to/your/image.jpg")

# Classify all images in a folder
classify_folder("path/to/your/folder")
```

## 📁 Project Structure
```
├── run_training.py          # Main training script
├── seatbelt_classifier.py   # Image classification functions
├── runModel.py              # Random image testing
├── webcam_detector.py       # 📹 Real-time webcam detection
├── test_webcam.py           # Webcam functionality test
├── seatbelt_dataset/        # Organized training data
├── seatbelt_model/          # Trained model outputs
│   └── final/weights/best.pt # Best trained model
└── requirements.txt         # Dependencies
```

## 🔧 Requirements
- Python 3.8+
- ultralytics (YOLOv8)
- opencv-python (for webcam)

Install dependencies:
```bash
pip install -r requirements.txt
```

## 🚀 Quick Start
1. **Train the model**: `python run_training.py`
2. **Test webcam**: `python test_webcam.py` (optional)
3. **Real-time detection**: `python webcam_detector.py`
4. **Test with random images**: `python runModel.py`

## 📹 Webcam Features
- Real-time seatbelt detection
- Live confidence scoring
- Mirror mode display
- Screenshot capture (press 's')
- Visual safety indicators
- Quit with 'q' key

The model will automatically detect seatbelts with high accuracy and provide confidence scores for each classification.
