import 'package:flutter/foundation.dart' show defaultTargetPlatform, kIsWeb, TargetPlatform;

/// API base URL. Override at build/run time:
/// `flutter run --dart-define=PHI_DPS_API_BASE=http://YOUR_LAN_IP:8000`
///
/// - **Android emulator:** `127.0.0.1` points at the emulator itself, not your Mac.
///   Default for Android is `http://10.0.2.2:8000` (host loopback from the emulator).
/// - **Android physical device:** use your computer's LAN IP via dart-define.
/// - **iOS Simulator / macOS / desktop:** `http://127.0.0.1:8000` works for local backend.
class AppConfig {
  const AppConfig();

  String get apiBase {
    const fromEnv = String.fromEnvironment("PHI_DPS_API_BASE");
    if (fromEnv.isNotEmpty) return fromEnv;
    if (kIsWeb) return "http://127.0.0.1:8000";
    if (defaultTargetPlatform == TargetPlatform.android) {
      return "http://10.0.2.2:8000";
    }
    return "http://127.0.0.1:8000";
  }
}
