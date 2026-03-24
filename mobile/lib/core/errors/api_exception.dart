/// Typed failure for PHI-DPS API responses (FastAPI `detail` payloads).
class ApiException implements Exception {
  ApiException({
    required this.statusCode,
    required this.message,
    this.rawDetail,
  });

  final int? statusCode;
  final String message;

  /// Original `detail` from JSON: string, map, or list.
  final Object? rawDetail;

  @override
  String toString() => 'ApiException($statusCode): $message';
}
