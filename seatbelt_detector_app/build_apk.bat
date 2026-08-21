@echo off
echo 🚗 Seatbelt Detector - Flutter App Builder
echo ==========================================
echo.

echo 📱 Available commands:
echo 1. flutter install      - Install directly to connected device
echo 2. flutter build apk    - Build debug APK
echo 3. flutter build apk --release  - Build release APK
echo.

echo 📦 Current APK location:
echo build\app\outputs\flutter-apk\app-debug.apk
echo.

echo 🔧 Quick setup:
echo 1. Connect Android device with USB debugging enabled
echo 2. Run: flutter install
echo.

echo ⚡ Building APK now...
flutter build apk --debug

echo.
echo ✅ Build complete!
echo APK saved to: build\app\outputs\flutter-apk\app-debug.apk
echo.

echo 📲 To install on device:
echo 1. Enable "Unknown sources" in Android Settings
echo 2. Transfer APK to device  
echo 3. Tap APK file to install
echo.

pause
