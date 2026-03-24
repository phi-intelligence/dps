import 'package:dio/dio.dart';

import '../errors/api_exception.dart';

/// Classifies transport / transient failures suitable for offline queue + retry.
///
/// Non-recoverable: client errors (4xx except 408/409/429), validation — do not spin forever.
abstract final class RecoverableErrors {
  static bool isRecoverable(DioException e) {
    final type = e.type;
    if (type == DioExceptionType.connectionTimeout ||
        type == DioExceptionType.sendTimeout ||
        type == DioExceptionType.receiveTimeout ||
        type == DioExceptionType.connectionError ||
        type == DioExceptionType.unknown) {
      return true;
    }
    final code = e.response?.statusCode;
    if (code == null) return true;
    if (code == 408 || code == 429) return true;
    if (code >= 500 && code <= 599) return true;
    return false;
  }

  /// After max attempts or non-retryable HTTP failure.
  static bool shouldMarkFailedImmediately(DioException e) {
    final code = e.response?.statusCode;
    if (code == 409) return false; // conflict — special status
    if (code == null) return false;
    if (code >= 400 && code < 500 && code != 408 && code != 429) {
      return true;
    }
    if (e.error is ApiException) {
      return true;
    }
    return false;
  }

  static bool isConflict(DioException e) => e.response?.statusCode == 409;
}
