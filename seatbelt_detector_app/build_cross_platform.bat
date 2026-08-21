@echo off
echo 🚗 Seatbelt Detector - Cross-Platform App
echo ========================================
echo.

echo 📱 Available platforms:
echo 1. Android (APK)      - Mobile phones
echo 2. Windows Desktop    - PC/Laptop webcam
echo.

echo 🔧 Build Commands:
echo.
echo For Android:
echo   flutter build apk --debug
echo   APK location: build\app\outputs\flutter-apk\app-debug.apk
echo.
echo For Windows Desktop:
echo   flutter build windows --debug  
echo   EXE location: build\windows\x64\runner\Debug\seatbelt_detector_app.exe
echo.

echo 🚀 Run Commands:
echo.
echo For Android (device connected):
echo   flutter install
echo.
echo For Windows Desktop:
echo   flutter run -d windows
echo   OR double-click: build\windows\x64\runner\Debug\seatbelt_detector_app.exe
echo.

echo ✅ Features by platform:
echo.
echo Android:
echo   - Camera access with permissions
echo   - System sounds + haptic feedback  
echo   - Mobile-optimized layout
echo   - Battery efficient (1 second intervals)
echo.
echo Windows Desktop:
echo   - Webcam access (no permissions needed)
echo   - System alert sounds
echo   - High-resolution camera preview
echo   - Fast detection (0.5 second intervals)
echo.

echo 🎯 Choose your action:
echo [1] Build for Android
echo [2] Build for Windows Desktop  
echo [3] Run on Windows Desktop
echo [4] Exit
echo.

set /p choice="Enter choice (1-4): "

if "%choice%"=="1" (
    echo Building Android APK...
    flutter build apk --debug
    echo.
    echo ✅ Android APK built: build\app\outputs\flutter-apk\app-debug.apk
)

if "%choice%"=="2" (
    echo Building Windows Desktop...
    flutter build windows --debug
    echo.
    echo ✅ Windows EXE built: build\windows\x64\runner\Debug\seatbelt_detector_app.exe
)

if "%choice%"=="3" (
    echo Running on Windows Desktop...
    flutter run -d windows
)

if "%choice%"=="4" (
    echo Goodbye!
    exit /b 0
)

echo.
pause