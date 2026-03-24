import 'package:phi_dps_mobile/core/auth/token_storage.dart';

/// In-memory token storage for widget tests (no platform channels).
class FakeTokenStorage implements TokenStorage {
  String? _token;

  @override
  Future<String?> readAccessToken() async => _token;

  @override
  Future<void> writeAccessToken(String token) async {
    _token = token;
  }

  @override
  Future<void> clear() async {
    _token = null;
  }
}
