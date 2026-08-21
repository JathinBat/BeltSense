# 🚗 Seatbelt Detector Flutter App

A Flutter mobile application for real-time seatbelt detection using camera integration with audio alerts for Android devices.

## 📱 Features

- **Real-time Camera Feed**: Live camera preview for seatbelt monitoring
- **Seatbelt Detection**: Simulated AI detection (ready for YOLO model integration)
- **Audio Alerts**: Sound notifications when no seatbelt is detected
- **Visual Feedback**: Color-coded status indicators (Green = Safe, Red = Unsafe)
- **Confidence Display**: Shows detection confidence percentage
- **Permission Handling**: Automatic camera permission requests
- **Clean Interface**: Modern Material 3 design

## 🛠️ Installation

### Prerequisites
- Flutter SDK 3.29.0 or higher
- Android SDK with API level 36
- Android device or emulator

### Quick Setup

1. **Navigate to the app directory:**
   ```bash
   cd "seatbelt_detector_app"
   ```

2. **Install dependencies:**
   ```bash
   flutter pub get
   ```

3. **Build and install on Android:**
   ```bash
   flutter install
   ```

   Or build APK for distribution:
   ```bash
   flutter build apk --release
   ```

## 📦 APK Installation

The built APK is located at:
```
build/app/outputs/flutter-apk/app-debug.apk
```

To install on Android device:
1. Enable "Unknown sources" in Android Settings > Security
2. Transfer the APK to your device
3. Tap the APK file to install

## 🎯 Usage

1. **Launch the app** on your Android device
2. **Grant camera permission** when prompted
3. **Point camera** at the driver seat area
4. **Tap "Start Detection"** to begin monitoring
5. **View real-time results:**
   - ✅ Green = Seatbelt detected (Safe)
   - ⚠️ Red = No seatbelt detected (Unsafe + Audio alert)
6. **Tap "Stop Detection"** to pause monitoring

## 🔧 Technical Details

### Dependencies
- `camera: ^0.10.6` - Camera functionality
- `audioplayers: ^6.0.0` - Audio alert system
- `permission_handler: ^11.3.1` - Android permissions
- `image: ^4.1.7` - Image processing utilities

### Android Permissions
- `CAMERA` - Camera access for detection
- `RECORD_AUDIO` - Audio alert playback

### Architecture
- **Main App**: `lib/main.dart` - Complete seatbelt detection app
- **Assets**: `assets/` - Model files, audio alerts, images
- **Android Config**: `android/` - Platform-specific configurations

## 🧠 YOLO Model Integration (Future)

The app is designed to integrate with YOLO models. To add real model inference:

1. **Convert your YOLO model** to TensorFlow Lite format
2. **Place model file** in `assets/models/`
3. **Replace simulation code** in `_processFrame()` method
4. **Add tflite dependencies** back to `pubspec.yaml`

```dart
// Replace this simulation code:
final random = Random();
bool hasSeatbelt = random.nextDouble() > 0.3;

// With actual model inference:
final results = await interpreter.run(processedImage);
bool hasSeatbelt = results['seatbelt'] > 0.7;
```

## 📁 Project Structure

```
seatbelt_detector_app/
├── lib/
│   └── main.dart              # Main application code
├── assets/
│   ├── models/               # YOLO model files (future)
│   ├── audio/                # Alert sound files
│   └── images/               # App images/icons
├── android/                  # Android configuration
├── pubspec.yaml             # Dependencies
└── README.md               # This file
```

## 🚀 Building for Production

### Release APK
```bash
flutter build apk --release
```

### Android App Bundle (for Google Play)
```bash
flutter build appbundle --release
```

### Signing Configuration
For production releases, configure app signing in:
`android/app/build.gradle`

## 🐛 Troubleshooting

### Common Issues

**Camera Permission Denied:**
- Go to Settings > Apps > Seatbelt Detector > Permissions
- Enable Camera permission

**Build Errors:**
```bash
flutter clean
flutter pub get
flutter build apk --debug
```

**Audio Not Working:**
- Check device volume settings
- Ensure app has audio permissions

## 📱 System Requirements

### Android
- **Minimum SDK**: API 21 (Android 5.0)
- **Target SDK**: API 36 (Android 14+)
- **Camera**: Rear-facing camera required
- **Storage**: 50MB available space

### Development
- **Flutter**: 3.29.0+
- **Dart**: 3.7.0+
- **Android Studio**: 2024.1+
- **Java**: JDK 17+

## 🤝 Contributing

To enhance the app:
1. Fork the project
2. Create feature branch
3. Add YOLO model integration
4. Test on multiple devices
5. Submit pull request

## 📄 License

This project is part of the SeatBelt Detection system for educational and safety purposes.

---

**🔄 Current Status**: Demo version with simulated detection ready for YOLO model integration
**📍 Next Steps**: Integrate trained YOLO model from the Python webcam detector
