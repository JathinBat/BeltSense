# 🚗 Cross-Platform Seatbelt Detector

A Flutter application that works on **both mobile and desktop** platforms for real-time seatbelt detection using camera integration with audio alerts.

## ✅ **Completed Cross-Platform Features**

### 📱 **Mobile (Android)**
- Camera access with permission handling
- System sounds + haptic feedback (vibration)
- Mobile-optimized layout
- Battery efficient detection (1-second intervals)
- Touch-friendly interface

### 🖥️ **Desktop (Windows/Mac/Linux)**
- Webcam access (no permissions needed)
- System alert sounds
- High-resolution camera preview
- Fast detection updates (0.5-second intervals)  
- Desktop-optimized layout
- Keyboard/mouse friendly

### 🔧 **Platform Detection**
- Automatic platform detection and UI adaptation
- Different alert systems per platform
- Optimized performance for each platform type
- Platform-specific instructions and features

## 🚀 **How to Build & Run**

### For Mobile (Android):
```bash
flutter build apk --debug
# Install: build\app\outputs\flutter-apk\app-debug.apk
```

### For Desktop (Windows):
```bash
flutter build windows --debug  
# Run: build\windows\x64\runner\Debug\seatbelt_detector_app.exe
```

### For Live Development:
```bash
# Mobile (device connected):
flutter run

# Desktop:
flutter run -d windows
```

## 📁 **Quick Launch Scripts**

### `build_cross_platform.bat`
Interactive script to build for any platform:
- [1] Build Android APK
- [2] Build Windows Desktop
- [3] Run on Windows Desktop

### `run_desktop.bat`
Quick launcher for Windows desktop version

## 🎯 **Platform-Specific Features**

| Feature | Mobile | Desktop |
|---------|---------|----------|
| **Camera Access** | Permission required | Direct access |
| **Alert Sounds** | System + Haptic | System sounds |
| **Detection Speed** | 1 second | 0.5 seconds |
| **Resolution** | Medium | High |
| **Layout** | Portrait stack | Side-by-side |
| **Controls** | Touch buttons | Click buttons |

## 🔊 **Audio Alert System**

### Mobile:
- System alert sounds
- Haptic feedback (vibration)
- Continuous alerts when unsafe
- URL-based backup sounds

### Desktop:
- System alert sounds
- URL-based backup sounds
- Visual alert indicators
- No haptic feedback

## 💻 **System Requirements**

### Mobile (Android):
- Android 5.0+ (API 21+)
- Camera permission
- 50MB storage
- Rear-facing camera

### Desktop (Windows):
- Windows 10/11
- Webcam (built-in or USB)
- 100MB storage
- No special permissions needed

## 🛠️ **Development Setup**

1. **Enable desktop platforms:**
   ```bash
   flutter config --enable-windows-desktop
   flutter config --enable-macos-desktop
   flutter config --enable-linux-desktop
   ```

2. **Add platforms to existing project:**
   ```bash
   flutter create --platforms=windows,macos,linux .
   ```

3. **Install dependencies:**
   ```bash
   flutter pub get
   ```

## 📱 **Usage Instructions**

### Mobile:
1. Grant camera permission when prompted
2. Point camera at driver seat area
3. Tap "Start Detection"
4. Receive visual + audio + haptic alerts

### Desktop:
1. Position webcam toward driver area
2. Click "Start Detection"  
3. Receive visual + audio alerts
4. Higher resolution and faster updates

## 🧠 **YOLO Model Integration**

The app is structured for easy YOLO model integration:

```dart
// Replace simulation in _processFrame():
final random = Random();
bool hasSeatbelt = random.nextDouble() > 0.4;

// With actual YOLO inference:
final results = await interpreter.run(processedImage);
bool hasSeatbelt = results['seatbelt'] > 0.7;
```

## 🔄 **Current Status**

✅ **Cross-platform UI** - Adapts to mobile vs desktop  
✅ **Camera integration** - Works on mobile and desktop  
✅ **Audio alerts** - Platform-specific sound systems  
✅ **Platform detection** - Automatic feature adaptation  
✅ **Build scripts** - Easy deployment for both platforms  
🔄 **YOLO integration** - Ready for model implementation  

## 🎮 **Demo Mode**

The app currently runs in **simulation mode** with:
- Random seatbelt detection results
- 60% chance of detecting seatbelt  
- 70-100% confidence simulation
- All alert systems fully functional

## 📈 **Next Steps**

1. **Add your trained YOLO model** to `assets/models/`
2. **Replace simulation code** with actual inference
3. **Test on multiple devices** and platforms
4. **Deploy** to app stores or distribute executables

---

**🌟 The app is now fully cross-platform and ready to use on both mobile and desktop!**