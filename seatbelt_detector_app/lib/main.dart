import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter/foundation.dart';
import 'package:camera/camera.dart';
import 'package:audioplayers/audioplayers.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:geolocator/geolocator.dart';
import 'dart:async';
import 'dart:math' as math;
import 'dart:io' show Platform;
import 'dart:typed_data';
// On-device ONNX inference
import 'package:onnxruntime/onnxruntime.dart';
import 'package:image/image.dart' as img;

late List<CameraDescription> cameras;

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  try {
    cameras = await availableCameras();
  } on CameraException catch (e) {
    print('Error initializing cameras: $e');
    cameras = [];
  } catch (e) {
    print('Camera not available on this platform: $e');
    cameras = []; // Set empty list for platforms without camera support
  }
  
  runApp(const SeatbeltDetectorApp());
}

class SeatbeltDetectorApp extends StatelessWidget {
  const SeatbeltDetectorApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Seatbelt Detector',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.blue),
        useMaterial3: true,
      ),
      home: const SeatbeltDetectorHome(),
      debugShowCheckedModeBanner: false,
    );
  }
}

class SeatbeltDetectorHome extends StatefulWidget {
  const SeatbeltDetectorHome({super.key});

  @override
  State<SeatbeltDetectorHome> createState() => _SeatbeltDetectorHomeState();
}

class _SeatbeltDetectorHomeState extends State<SeatbeltDetectorHome> {
  CameraController? _controller;
  bool _isDetecting = false;
  bool _isInitialized = false;
  String _detectionResult = 'Initializing...';
  double _confidence = 0.0;
  Color _statusColor = Colors.orange;
  bool _isAlertPlaying = false;
  String _platformInfo = '';
  int _selectedCameraIndex = 0;
  
  // On-device ONNX model.
  //
  // Contract verified directly against assets/models/seatbelt_model.onnx:
  //   input  "images"  [1, 3, 224, 224]  float32, NCHW, RGB, scaled to 0-1
  //   output "output0" [1, 2]            softmax already applied by the model
  //   classes {0: no_seatbelt, 1: seatbelt}
  // Feeding NHWC is rejected by the runtime, and the model expects colour —
  // do not reintroduce the old grayscale/NHWC preprocessing.
  static const String _modelAsset = 'assets/models/seatbelt_model.onnx';
  static const String _inputName = 'images';
  static const int _inputSize = 224;
  static const List<String> _classNames = ['no_seatbelt', 'seatbelt'];
  static const int _kNoSeatbelt = 0;
  static const int _kSeatbelt = 1;

  bool _modelLoaded = false;
  OrtSession? _session;
  
  // GPS and driving detection variables
  bool _isDriving = false;
  bool _gpsInitialized = false;
  double _currentSpeed = 0.0;
  Position? _lastPosition;
  String _gpsStatus = 'GPS Initializing...';
  Color _gpsStatusColor = Colors.orange;
  
  final AudioPlayer _audioPlayer = AudioPlayer();
  Timer? _detectionTimer;
  Timer? _alertTimer;
  Timer? _gpsTimer;
  
  @override
  void initState() {
    super.initState();
    _initializePlatform();
    _initializeModel();
    _initializeAudio();
    _initializeGPS();
    _initializeCamera();
  }

  void _initializePlatform() {
    if (kIsWeb) {
      _platformInfo = 'Web Platform';
    } else if (!kIsWeb && Platform.isAndroid) {
      _platformInfo = 'Android';
    } else if (!kIsWeb && Platform.isIOS) {
      _platformInfo = 'iOS';
    } else if (!kIsWeb && Platform.isWindows) {
      _platformInfo = 'Windows Desktop';
    } else if (!kIsWeb && Platform.isMacOS) {
      _platformInfo = 'macOS Desktop';
    } else if (!kIsWeb && Platform.isLinux) {
      _platformInfo = 'Linux Desktop';
    } else {
      _platformInfo = 'Unknown Platform';
    }
  }

  Future<void> _initializeModel() async {
    try {
      print('Loading ONNX model from $_modelAsset ...');

      OrtEnv.instance.init();

      final ByteData raw = await rootBundle.load(_modelAsset);
      final Uint8List modelBytes = raw.buffer.asUint8List(
        raw.offsetInBytes,
        raw.lengthInBytes,
      );

      _session = OrtSession.fromBuffer(modelBytes, OrtSessionOptions());

      print('Model loaded. input "$_inputName" '
          '[1, 3, $_inputSize, $_inputSize] NCHW, float 0-1, RGB; '
          'output [1, 2] softmax over $_classNames');

      setState(() {
        _modelLoaded = true;
        if (_detectionResult == 'Initializing...') {
          _detectionResult = 'Model ready';
          _statusColor = Colors.blue;
        }
      });
    } catch (e) {
      // A safety feature must never pretend to work. If the model cannot be
      // loaded we say so and leave _modelLoaded false, which disables
      // detection entirely rather than falling back to a guess.
      print('Error loading ONNX model: $e');
      setState(() {
        _modelLoaded = false;
        _detectionResult = 'Model failed to load - detection disabled';
        _statusColor = Colors.red;
        _confidence = 0.0;
      });
    }
  }

  Future<void> _initializeAudio() async {
    try {
      // Audio player should be ready to use without complex configuration for this use case
      print('Audio player initialized for $_platformInfo');
    } catch (e) {
      print('Audio initialization warning: $e');
    }
  }

  Future<void> _initializeGPS() async {
    try {
      // Check if location services are enabled
      bool serviceEnabled = await Geolocator.isLocationServiceEnabled();
      if (!serviceEnabled) {
        setState(() {
          _gpsStatus = 'Location services disabled - Enable in device settings';
          _gpsStatusColor = Colors.red;
        });
        
        // Show dialog to guide user to enable location services
        _showLocationServiceDialog();
        return;
      }

      // Check location permission
      LocationPermission permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        // Show explanation before requesting permission
        _showPermissionExplanationDialog();
        
        permission = await Geolocator.requestPermission();
        if (permission == LocationPermission.denied) {
          setState(() {
            _gpsStatus = 'Location permission denied - Tap to retry';
            _gpsStatusColor = Colors.red;
          });
          return;
        }
      }

      if (permission == LocationPermission.deniedForever) {
        setState(() {
          _gpsStatus = 'Location permission permanently denied - Check app settings';
          _gpsStatusColor = Colors.red;
        });
        _showPermissionSettingsDialog();
        return;
      }

      // Start GPS tracking
      setState(() {
        _gpsInitialized = true;
        _gpsStatus = 'GPS Ready - Monitoring movement';
        _gpsStatusColor = Colors.blue;
      });

      _startGPSTracking();
      print('GPS initialized for $_platformInfo');
    } catch (e) {
      setState(() {
        _gpsStatus = 'GPS initialization failed: $e';
        _gpsStatusColor = Colors.red;
      });
      print('GPS initialization error: $e');
    }
  }

  void _showLocationServiceDialog() {
    if (!mounted) return;
    showDialog(
      context: context,
      builder: (BuildContext context) {
        return AlertDialog(
          title: const Text('📍 Location Services Disabled'),
          content: const Text(
            'This app needs location services to detect when you\'re driving and automatically start seatbelt detection.\n\n'
            'Please enable Location Services in your device settings.',
          ),
          actions: [
            TextButton(
              child: const Text('Settings'),
              onPressed: () {
                Navigator.of(context).pop();
                Geolocator.openLocationSettings();
              },
            ),
            TextButton(
              child: const Text('Skip GPS'),
              onPressed: () {
                Navigator.of(context).pop();
                setState(() {
                  _gpsStatus = 'GPS disabled - Manual detection only';
                  _gpsStatusColor = Colors.orange;
                });
              },
            ),
          ],
        );
      },
    );
  }

  void _showPermissionExplanationDialog() {
    if (!mounted) return;
    showDialog(
      context: context,
      builder: (BuildContext context) {
        return AlertDialog(
          title: const Text('🚗 GPS Permission Needed'),
          content: const Text(
            'Seatbelt Detector uses GPS to:\n\n'
            '• Automatically detect when you\'re driving\n'
            '• Start seatbelt monitoring while in motion\n'
            '• Save battery when parked\n\n'
            'Your location data stays private and is never shared.',
          ),
          actions: [
            TextButton(
              child: const Text('Allow GPS'),
              onPressed: () {
                Navigator.of(context).pop();
              },
            ),
            TextButton(
              child: const Text('Skip GPS'),
              onPressed: () {
                Navigator.of(context).pop();
                setState(() {
                  _gpsStatus = 'GPS skipped - Manual detection only';
                  _gpsStatusColor = Colors.orange;
                });
              },
            ),
          ],
        );
      },
    );
  }

  void _showPermissionSettingsDialog() {
    if (!mounted) return;
    showDialog(
      context: context,
      builder: (BuildContext context) {
        return AlertDialog(
          title: const Text('⚙️ Permission Required'),
          content: const Text(
            'GPS permission was permanently denied. To enable automatic driving detection:\n\n'
            '1. Go to App Settings\n'
            '2. Find "Permissions"\n'
            '3. Enable "Location" permission\n'
            '4. Restart the app',
          ),
          actions: [
            TextButton(
              child: const Text('App Settings'),
              onPressed: () {
                Navigator.of(context).pop();
                Geolocator.openAppSettings();
              },
            ),
            TextButton(
              child: const Text('Continue Without GPS'),
              onPressed: () {
                Navigator.of(context).pop();
              },
            ),
          ],
        );
      },
    );
  }

  void _startGPSTracking() {
    _gpsTimer = Timer.periodic(const Duration(seconds: 3), (timer) {
      _updateLocation();
    });
  }

  Future<void> _updateLocation() async {
    try {
      Position position = await Geolocator.getCurrentPosition(
        desiredAccuracy: LocationAccuracy.medium,
      );

      // Calculate speed if we have a previous position
      if (_lastPosition != null) {
        double distanceInMeters = Geolocator.distanceBetween(
          _lastPosition!.latitude,
          _lastPosition!.longitude,
          position.latitude,
          position.longitude,
        );

        // Calculate time difference in seconds
        double timeDifferenceInSeconds = 
            position.timestamp.difference(_lastPosition!.timestamp).inSeconds.toDouble();

        if (timeDifferenceInSeconds > 0) {
          // Calculate speed in m/s and convert to km/h
          double speedMPS = distanceInMeters / timeDifferenceInSeconds;
          _currentSpeed = speedMPS * 3.6; // Convert to km/h
        }
      } else {
        // Use the speed from the GPS if available (more accurate)
        _currentSpeed = position.speed * 3.6; // Convert from m/s to km/h
      }

      _lastPosition = position;

      // Determine if user is driving (speed threshold: 10 km/h)
      bool wasDriving = _isDriving;
      _isDriving = _currentSpeed > 10.0;

      setState(() {
        if (_isDriving) {
          _gpsStatus = 'DRIVING DETECTED - Speed: ${_currentSpeed.toStringAsFixed(1)} km/h';
          _gpsStatusColor = Colors.green;
        } else {
          _gpsStatus = 'STATIONARY - Speed: ${_currentSpeed.toStringAsFixed(1)} km/h';
          _gpsStatusColor = Colors.blue;
        }
      });

      // If just started driving, automatically start detection
      if (_isDriving && !wasDriving && _isInitialized && !_isDetecting) {
        print('Driving detected - auto-starting seatbelt detection');
        _startDetection();
      }

      // If stopped driving, stop detection
      if (!_isDriving && wasDriving && _isDetecting) {
        print('Stopped driving - auto-stopping seatbelt detection');
        _stopDetection();
      }

    } catch (e) {
      print('Error updating location: $e');
      setState(() {
        _gpsStatus = 'GPS tracking error: $e';
        _gpsStatusColor = Colors.red;
      });
    }
  }

  bool _isDesktop() {
    return !kIsWeb && (Platform.isWindows || Platform.isMacOS || Platform.isLinux);
  }

  bool _isMobile() {
    return !kIsWeb && (Platform.isAndroid || Platform.isIOS);
  }

  Future<void> _initializeCamera([int? cameraIndex]) async {
    if (cameras.isEmpty) {
      setState(() {
        if (_isDesktop()) {
          _detectionResult = 'Desktop Mode - Camera plugin not supported\nSimulation mode active on $_platformInfo';
          _isInitialized = true; // Allow app to work without camera
        } else {
          _detectionResult = 'No cameras available on $_platformInfo';
        }
        _statusColor = _isDesktop() ? Colors.blue : Colors.red;
      });
      return;
    }

    // Dispose of existing controller if reinitializing
    if (_controller != null) {
      await _controller!.dispose();
      _controller = null;
      setState(() {
        _isInitialized = false;
      });
    }

    // Request camera permission (mobile platforms only)
    if (_isMobile()) {
      final status = await Permission.camera.request();
      if (status != PermissionStatus.granted) {
        setState(() {
          _detectionResult = 'Camera permission denied';
          _statusColor = Colors.red;
        });
        return;
      }
    }

    // Use provided index or current selected index
    int targetIndex = cameraIndex ?? _selectedCameraIndex;
    if (targetIndex >= cameras.length) {
      targetIndex = 0; // Fallback to first camera
    }
    _selectedCameraIndex = targetIndex;

    CameraDescription selectedCamera = cameras[_selectedCameraIndex];

    _controller = CameraController(
      selectedCamera,
      // Use different resolution based on platform
      _isDesktop() ? ResolutionPreset.high : ResolutionPreset.medium,
      enableAudio: false,
    );

    try {
      await _controller!.initialize();
      if (mounted) {
        setState(() {
          _isInitialized = true;
          _detectionResult = 'Camera ready on $_platformInfo (${_getCameraName(selectedCamera)}) - Click to start detection';
          _statusColor = Colors.blue;
        });
      }
    } catch (e) {
      setState(() {
        _detectionResult = 'Camera initialization failed: $e';
        _statusColor = Colors.red;
      });
    }
  }

  String _getCameraName(CameraDescription camera) {
    switch (camera.lensDirection) {
      case CameraLensDirection.front:
        return 'Front Camera';
      case CameraLensDirection.back:
        return 'Back Camera';
      case CameraLensDirection.external:
        return 'External Camera';
    }
  }

  Future<void> _switchCamera() async {
    if (cameras.length <= 1) return;
    
    // Stop detection if running
    if (_isDetecting) {
      _stopDetection();
    }
    
    // Switch to next camera
    int nextIndex = (_selectedCameraIndex + 1) % cameras.length;
    await _initializeCamera(nextIndex);
  }

  Future<void> _startDetection() async {
    if (!_isInitialized || _controller == null) return;
    
    setState(() {
      _isDetecting = true;
      _detectionResult = 'Starting detection...';
      _statusColor = Colors.orange;
    });

    _detectionTimer = Timer.periodic(
      _isDesktop() 
          ? const Duration(milliseconds: 500)  // Faster on desktop
          : const Duration(seconds: 1),        // Slower on mobile
      (timer) {
        _processFrame();
      }
    );
  }

  void _stopDetection() {
    _detectionTimer?.cancel();
    _alertTimer?.cancel();
    setState(() {
      _isDetecting = false;
      _isAlertPlaying = false;
      _detectionResult = 'Detection stopped';
      _statusColor = Colors.grey;
    });
  }

  Future<void> _processFrame() async {
    // Skip camera check for desktop simulation mode
    if (_controller != null && (!_controller!.value.isInitialized || _controller!.value.isTakingPicture)) {
      return;
    }

    try {
      if (_modelLoaded && _controller != null && _controller!.value.isInitialized) {
        await _runRealInference();
      } else if (_controller == null) {
        // No camera hardware at all (desktop preview). This is an explicitly
        // labelled demo, never presented as a real reading.
        await _runSimulationMode();
      } else {
        await _reportDetectionUnavailable(
            _modelLoaded ? 'Camera not ready' : 'Model not loaded');
      }
    } catch (e) {
      // Never fall back to a fabricated result on a safety feature: a random
      // "seatbelt detected" would silence a real alert, and a random
      // "no seatbelt" would cry wolf. Surface the failure instead.
      print('Error processing frame: $e');
      await _reportDetectionUnavailable('Detection error');
    }
  }

  /// Puts the UI into an explicit "we do not know" state and silences any
  /// alert, so nothing is asserted about the occupant without a real reading.
  Future<void> _reportDetectionUnavailable(String reason) async {
    if (_isAlertPlaying) {
      _stopAlert();
    }
    if (!mounted) return;
    setState(() {
      _detectionResult = '⚠️ Detection unavailable - $reason';
      _statusColor = Colors.orange;
      _confidence = 0.0;
    });
  }

  /// Runs the ONNX session and returns the class probabilities.
  ///
  /// [input] must be NCHW float data of length 3 * 224 * 224.
  List<double> _runModel(OrtSession session, Float32List input) {
    final inputTensor = OrtValueTensor.createTensorWithDataList(
      input,
      [1, 3, _inputSize, _inputSize],
    );
    final runOptions = OrtRunOptions();
    List<OrtValue?>? outputs;
    try {
      final List<OrtValue?>? result =
          session.run(runOptions, {_inputName: inputTensor});
      outputs = result;
      final dynamic value =
          (result != null && result.isNotEmpty) ? result.first?.value : null;
      // output0 has shape [1, 2], so the runtime hands back a nested list.
      if (value is List && value.isNotEmpty && value.first is List) {
        return (value.first as List)
            .map((e) => (e as num).toDouble())
            .toList(growable: false);
      }
      return const <double>[];
    } finally {
      inputTensor.release();
      runOptions.release();
      outputs?.forEach((o) => o?.release());
    }
  }

  Future<void> _runRealInference() async {
    try {
      // Capture image from camera
      final XFile imageFile = await _controller!.takePicture();
      final Uint8List imageBytes = await imageFile.readAsBytes();
      
      // Preprocess the image for the model
      final Float32List inputData = await _preprocessImage(imageBytes);
      
      if (inputData.isEmpty) {
        print('Image preprocessing failed');
        await _reportDetectionUnavailable('Could not read frame');
        return;
      }
      
      // Run the trained YOLOv8n-cls model on this frame.
      final OrtSession? session = _session;
      if (session == null) {
        await _reportDetectionUnavailable('Model not loaded');
        return;
      }

      final List<double> probabilities = _runModel(session, inputData);
      if (probabilities.length != 2) {
        await _reportDetectionUnavailable('Unexpected model output');
        return;
      }

      // output0 is already a softmax distribution, so these sum to 1.0.
      final double noSeatbeltConf = probabilities[_kNoSeatbelt];
      final double seatbeltConf = probabilities[_kSeatbelt];

      // Determine prediction (higher confidence wins)
      final bool hasSeatbelt = seatbeltConf > noSeatbeltConf;
      final double confidence = math.max(noSeatbeltConf, seatbeltConf);
      
      setState(() {
        if (hasSeatbelt) {
          _detectionResult = _isDriving 
              ? '✅ SEATBELT DETECTED - SAFE DRIVING'
              : '✅ SEATBELT DETECTED - SAFE';
          _statusColor = Colors.green;
          _confidence = confidence;
          // Stop alert if it was playing
          if (_isAlertPlaying) {
            _stopAlert();
          }
        } else {
          _detectionResult = _isDriving 
              ? '⚠️ NO SEATBELT - DANGEROUS DRIVING!'
              : '⚠️ NO SEATBELT - UNSAFE!';
          _statusColor = Colors.red;
          _confidence = confidence;
          _startAlert();
        }
      });
      
      print('Real inference - Seatbelt: ${seatbeltConf.toStringAsFixed(3)}, No Seatbelt: ${noSeatbeltConf.toStringAsFixed(3)}');
      
    } catch (e) {
      print('Error in real inference: $e');
      await _reportDetectionUnavailable('Inference error');
    }
  }

  /// Demo animation for desktop builds with no camera hardware. Every string
  /// it produces is tagged (SIMULATION); it is never used as a fallback when a
  /// real camera is present, because a fabricated reading on a safety feature
  /// is worse than no reading.
  Future<void> _runSimulationMode() async {
    await Future.delayed(const Duration(milliseconds: 500));
    
    // Simulate detection results using Random
    final random = math.Random();
    
    // Make detection more urgent if driving at higher speeds
    double alertProbability = _isDriving 
        ? 0.2 + (_currentSpeed / 100.0) * 0.3  // Higher speed = more likely to detect unsafe
        : 0.3; // Normal probability when not driving
    
    bool hasSeatbelt = random.nextDouble() > alertProbability;
    double confidence = 0.7 + (random.nextDouble() * 0.3); // 70-100% confidence
    
    setState(() {
      if (hasSeatbelt) {
        _detectionResult = _isDriving 
            ? '✅ SEATBELT DETECTED - SAFE DRIVING (SIMULATION)'
            : '✅ SEATBELT DETECTED - SAFE (SIMULATION)';
        _statusColor = Colors.green;
        _confidence = confidence;
        // Stop alert if it was playing
        if (_isAlertPlaying) {
          _stopAlert();
        }
      } else {
        _detectionResult = _isDriving 
            ? '⚠️ NO SEATBELT - DANGEROUS DRIVING! (SIMULATION)'
            : '⚠️ NO SEATBELT - UNSAFE! (SIMULATION)';
        _statusColor = Colors.red;
        _confidence = confidence;
        _startAlert();
      }
    });
  }

  Future<Float32List> _preprocessImage(Uint8List imageBytes) async {
    try {
      // Decode the image
      img.Image? image = img.decodeImage(imageBytes);
      if (image == null) {
        print('Failed to decode image');
        return Float32List(0);
      }
      
      // Match the transform ultralytics uses for YOLOv8 classification:
      // scale the shorter side to 224 preserving aspect ratio, then take the
      // centre 224x224 crop. On the labelled hold-out set this measured better
      // than a plain squash-resize to 224x224, because squashing distorts the
      // diagonal belt strap the model keys on.
      final int shorterSide =
          image.width < image.height ? image.width : image.height;
      final double scale = _inputSize / shorterSide;
      // .clamp() is declared on num and returns num, so toInt() is required
      // before these can be passed as int arguments.
      final int scaledWidth =
          (image.width * scale).round().clamp(_inputSize, 1 << 20).toInt();
      final int scaledHeight =
          (image.height * scale).round().clamp(_inputSize, 1 << 20).toInt();
      final img.Image scaled = img.copyResize(
        image,
        width: scaledWidth,
        height: scaledHeight,
        interpolation: img.Interpolation.linear,
      );
      final img.Image cropped = img.copyCrop(
        scaled,
        x: (scaled.width - _inputSize) ~/ 2,
        y: (scaled.height - _inputSize) ~/ 2,
        width: _inputSize,
        height: _inputSize,
      );

      // Pack as NCHW (all red, then all green, then all blue) scaled to 0-1.
      // The model rejects NHWC, and colour is kept because the model was
      // trained on RGB - converting to grayscale measurably loses accuracy.
      const int plane = _inputSize * _inputSize;
      final Float32List inputData = Float32List(3 * plane);
      for (int y = 0; y < _inputSize; y++) {
        for (int x = 0; x < _inputSize; x++) {
          final img.Pixel pixel = cropped.getPixel(x, y);
          final int i = y * _inputSize + x;
          inputData[i] = pixel.r.toDouble() / 255.0;
          inputData[plane + i] = pixel.g.toDouble() / 255.0;
          inputData[2 * plane + i] = pixel.b.toDouble() / 255.0;
        }
      }

      return inputData;

    } catch (e) {
      print('Error preprocessing image: $e');
      return Float32List(0);
    }
  }

  Future<void> _startAlert() async {
    if (_isAlertPlaying) return;
    
    setState(() {
      _isAlertPlaying = true;
    });

    // Start continuous alert system
    _alertTimer = Timer.periodic(const Duration(milliseconds: 1000), (timer) {
      _playAlertSound();
    });
    
    // Play initial alert
    _playAlertSound();
  }

  void _stopAlert() {
    _alertTimer?.cancel();
    setState(() {
      _isAlertPlaying = false;
    });
  }

  Future<void> _playAlertSound() async {
    try {
      // Primary approach: Always use system sound first (this should work on all platforms)
      await SystemSound.play(SystemSoundType.alert);
      
      if (_isMobile()) {
        // Add haptic feedback for mobile
        await HapticFeedback.vibrate();
      }

      // Every fallback below is on-device. The alert deliberately has no
      // network path: fetching a sound would send a request to a third party
      // at the exact moment a violation is detected, revealing the user's IP
      // and the timing of the alert, and contradicting the privacy policy's
      // guarantee that nothing leaves the device.
      try {
        await _audioPlayer.play(AssetSource('audio/alert.mp3'));
        print('Played bundled alert.mp3');
      } catch (e) {
        print('Bundled alert.mp3 failed: $e');
        try {
          await SystemSound.play(SystemSoundType.click);
        } catch (e2) {
          print('Backup system sound failed: $e2');
        }
      }

    } catch (e) {
      print('Critical error in audio playback: $e');
      
      // Final emergency fallback
      if (_isMobile()) {
        try {
          await HapticFeedback.heavyImpact();
          print('Emergency: Used strong haptic feedback only');
        } catch (hapticError) {
          print('Complete audio failure - no feedback possible: $hapticError');
        }
      }
    }
  }

  @override
  void dispose() {
    _detectionTimer?.cancel();
    _alertTimer?.cancel();
    _gpsTimer?.cancel();
    _controller?.dispose();
    _session?.release();
    _session = null;
    OrtEnv.instance.release();
    _audioPlayer.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
        title: Text('🚗 Seatbelt Detector ($_platformInfo)'),
        centerTitle: true,
        actions: [
          if (cameras.length > 1)
            IconButton(
              icon: const Icon(Icons.switch_camera),
              tooltip: 'Switch Camera',
              onPressed: _isDetecting ? null : _switchCamera,
            ),
          if (cameras.length > 1)
            Padding(
              padding: const EdgeInsets.only(right: 8.0),
              child: Center(
                child: Text(
                  '${_selectedCameraIndex + 1}/${cameras.length}',
                  style: const TextStyle(fontSize: 12),
                ),
              ),
            ),
        ],
      ),
      body: Column(
        children: [
          // Camera Preview
          Expanded(
            flex: 3,
            child: Container(
              width: double.infinity,
              margin: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: _statusColor, width: 3),
              ),
              child: ClipRRect(
                borderRadius: BorderRadius.circular(10),
                child: (_isInitialized && _controller != null)
                    ? AspectRatio(
                        aspectRatio: _controller!.value.aspectRatio,
                        child: CameraPreview(_controller!),
                      )
                    : Container(
                        color: Colors.black,
                        child: Center(
                          child: Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Icon(
                                _isDesktop() ? Icons.desktop_windows : Icons.camera_alt,
                                color: Colors.white,
                                size: 64,
                              ),
                              const SizedBox(height: 16),
                              Text(
                                _isDesktop() 
                                    ? '🖥️ Desktop Simulation Mode\n\nCamera preview not available\nbut detection simulation works!'
                                    : '📷 Camera Initializing...',
                                style: const TextStyle(
                                  color: Colors.white,
                                  fontSize: 16,
                                ),
                                textAlign: TextAlign.center,
                              ),
                            ],
                          ),
                        ),
                      ),
              ),
            ),
          ),
          
          // Status Panel
          Expanded(
            flex: 1,
            child: Container(
              width: double.infinity,
              margin: const EdgeInsets.symmetric(horizontal: 16),
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: _statusColor.withOpacity(0.1),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: _statusColor, width: 2),
              ),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(
                    _detectionResult,
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                      color: _statusColor,
                    ),
                    textAlign: TextAlign.center,
                  ),
                  if (_confidence > 0) ...[
                    const SizedBox(height: 8),
                    Text(
                      'Confidence: ${(_confidence * 100).toStringAsFixed(1)}%',
                      style: TextStyle(
                        fontSize: 14,
                        color: Colors.grey[600],
                      ),
                    ),
                  ],
                  if (_isAlertPlaying) ...[
                    const SizedBox(height: 8),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                      decoration: BoxDecoration(
                        color: Colors.red,
                        borderRadius: BorderRadius.circular(20),
                      ),
                      child: const Text(
                        '🔊 ALERT ACTIVE!',
                        style: TextStyle(
                          color: Colors.white,
                          fontWeight: FontWeight.bold,
                          fontSize: 12,
                        ),
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ),
          
          // GPS Status Panel
          Container(
            width: double.infinity,
            margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: _gpsStatusColor.withOpacity(0.1),
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: _gpsStatusColor, width: 2),
            ),
            child: Row(
              children: [
                Icon(
                  _isDriving ? Icons.directions_car : Icons.gps_fixed,
                  color: _gpsStatusColor,
                  size: 20,
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      GestureDetector(
                        onTap: !_gpsInitialized ? _initializeGPS : null,
                        child: Text(
                          _gpsStatus,
                          style: TextStyle(
                            fontSize: 14,
                            fontWeight: FontWeight.bold,
                            color: _gpsStatusColor,
                            decoration: !_gpsInitialized 
                                ? TextDecoration.underline 
                                : TextDecoration.none,
                          ),
                        ),
                      ),
                      if (_gpsInitialized) ...[
                        const SizedBox(height: 4),
                        Text(
                          _isDriving 
                              ? '🚗 Auto-detection enabled while driving'
                              : '🏠 Manual detection only when stationary',
                          style: TextStyle(
                            fontSize: 12,
                            color: Colors.grey[600],
                          ),
                        ),
                      ] else ...[
                        const SizedBox(height: 4),
                        Text(
                          'Tap above to retry GPS setup',
                          style: TextStyle(
                            fontSize: 12,
                            color: Colors.grey[600],
                            fontStyle: FontStyle.italic,
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
                if (_isDriving)
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: Colors.green,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: const Text(
                      'DRIVING',
                      style: TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.bold,
                        fontSize: 10,
                      ),
                    ),
                  ),
                if (!_gpsInitialized)
                  IconButton(
                    icon: const Icon(Icons.refresh),
                    onPressed: _initializeGPS,
                    color: _gpsStatusColor,
                    tooltip: 'Retry GPS Setup',
                  ),
              ],
            ),
          ),
          
          // Camera Selection (if multiple cameras available)
          if (cameras.length > 1)
            Container(
              width: double.infinity,
              margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.grey[100],
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Colors.grey[300]!),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    '📹 Camera Selection',
                    style: TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.bold,
                      color: Colors.black87,
                    ),
                  ),
                  const SizedBox(height: 8),
                  SingleChildScrollView(
                    scrollDirection: Axis.horizontal,
                    child: Row(
                      children: cameras.asMap().entries.map((entry) {
                        int index = entry.key;
                        CameraDescription camera = entry.value;
                        bool isSelected = index == _selectedCameraIndex;
                        
                        return Padding(
                          padding: const EdgeInsets.only(right: 8.0),
                          child: ElevatedButton.icon(
                            onPressed: (_isDetecting || index == _selectedCameraIndex) 
                                ? null 
                                : () => _initializeCamera(index),
                            style: ElevatedButton.styleFrom(
                              backgroundColor: isSelected ? Colors.blue : Colors.white,
                              foregroundColor: isSelected ? Colors.white : Colors.blue,
                              side: BorderSide(
                                color: isSelected ? Colors.blue : Colors.grey[300]!,
                              ),
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(6),
                              ),
                            ),
                            icon: Icon(
                              camera.lensDirection == CameraLensDirection.front
                                  ? Icons.camera_front
                                  : camera.lensDirection == CameraLensDirection.back
                                      ? Icons.camera_rear
                                      : Icons.camera_alt,
                              size: 18,
                            ),
                            label: Text(
                              _getCameraName(camera),
                              style: const TextStyle(fontSize: 12),
                            ),
                          ),
                        );
                      }).toList(),
                    ),
                  ),
                ],
              ),
            ),
          
          // Control Buttons
          Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                Expanded(
                  child: ElevatedButton(
                    onPressed: _isInitialized && !_isDetecting ? _startDetection : null,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.green,
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(vertical: 16),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(8),
                      ),
                    ),
                    child: const Text(
                      'Start Detection',
                      style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: ElevatedButton(
                    onPressed: _isDetecting ? _stopDetection : null,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.red,
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(vertical: 16),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(8),
                      ),
                    ),
                    child: const Text(
                      'Stop Detection',
                      style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                    ),
                  ),
                ),
              ],
            ),
          ),
          
          // Model Status Info
          Container(
            width: double.infinity,
            margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: _modelLoaded ? Colors.green.withOpacity(0.1) : Colors.orange.withOpacity(0.1),
              borderRadius: BorderRadius.circular(8),
              border: Border.all(
                color: _modelLoaded ? Colors.green : Colors.orange,
                width: 1,
              ),
            ),
            child: Row(
              children: [
                Icon(
                  _modelLoaded ? Icons.smart_toy : Icons.warning,
                  color: _modelLoaded ? Colors.green : Colors.orange,
                  size: 16,
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    _modelLoaded
                        ? '🧠 On-device model active - assistive only, always check your belt yourself'
                        : '⚠️ Model not loaded - detection is disabled',
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                      color: _modelLoaded ? Colors.green[700] : Colors.orange[700],
                    ),
                  ),
                ),
              ],
            ),
          ),
          
          // Instructions
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: Text(
              _isDesktop() 
                  ? 'GPS-enabled seatbelt detection system with embedded AI model. The app automatically monitors your driving status and activates seatbelt detection when moving above 10 km/h.\n\nDesktop features: Real AI inference, high resolution detection, system sounds, and optimized performance.'
                  : 'GPS-enabled seatbelt detection for safe driving with embedded AI model. The app automatically detects when you\'re driving and monitors seatbelt usage with audio alerts and haptic feedback.\n\nMobile features: Real AI inference while driving, haptic feedback, system sounds, and battery optimization.',
              style: TextStyle(
                fontSize: 12,
                color: Colors.grey[600],
              ),
              textAlign: TextAlign.center,
            ),
          ),
        ],
      ),
    );
  }
}
