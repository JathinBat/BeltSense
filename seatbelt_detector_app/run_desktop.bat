@echo off
echo 🖥️ Starting Seatbelt Detector on Windows Desktop...
echo.

if exist "build\windows\x64\runner\Debug\seatbelt_detector_app.exe" (
    echo ✅ Found Windows executable, launching...
    start "" "build\windows\x64\runner\Debug\seatbelt_detector_app.exe"
    echo.
    echo 🚗 Seatbelt Detector is now running on your desktop!
    echo.
    echo Features:
    echo - Webcam access for seatbelt detection
    echo - High-resolution camera preview  
    echo - System alert sounds
    echo - Fast detection updates
    echo.
) else (
    echo ❌ Windows executable not found!
    echo.
    echo Building Windows version first...
    flutter build windows --debug
    
    if exist "build\windows\x64\runner\Debug\seatbelt_detector_app.exe" (
        echo.
        echo ✅ Build successful! Launching...
        start "" "build\windows\x64\runner\Debug\seatbelt_detector_app.exe"
    ) else (
        echo.
        echo ❌ Build failed. Please check for errors above.
        echo.
        echo Try running manually:
        echo   flutter build windows --debug
        echo   flutter run -d windows
    )
)

echo.
pause