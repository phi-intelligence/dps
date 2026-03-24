import 'dart:convert';

/// Parses `access_token` from `/auth/token` JSON body (OAuth2-style).
/// Extracted for unit testing without HTTP mocks.
String parseAccessTokenFromAuthJson(String body) {
  final decoded = jsonDecode(body);
  if (decoded is! Map<String, dynamic>) {
    throw const FormatException('Invalid token response shape');
  }
  final tokenValue = decoded['access_token'] as String?;
  if (tokenValue == null || tokenValue.isEmpty) {
    throw const FormatException('Missing access_token');
  }
  return tokenValue;
}
