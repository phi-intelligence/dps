import 'package:flutter/foundation.dart';

/// Debug logging — never log JWTs or passwords.
void appDebug(String message, {String? tag}) {
  if (kDebugMode) {
    debugPrint(tag != null ? '[$tag] $message' : message);
  }
}
