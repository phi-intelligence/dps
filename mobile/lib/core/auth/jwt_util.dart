import 'dart:convert';

/// Returns JWT `sub` claim (subject — for PHI-DPS this is the **user id**, not vehicle id).
String? extractSubFromJwt(String jwt) {
  try {
    final parts = jwt.split('.');
    if (parts.length < 2) return null;
    final payloadBase64 = base64Url.normalize(parts[1]);
    final payloadJson = utf8.decode(base64Url.decode(payloadBase64));
    final payload = jsonDecode(payloadJson) as Map<String, dynamic>;
    final sub = payload['sub'];
    return sub?.toString();
  } catch (_) {
    return null;
  }
}
