import 'package:dio/dio.dart';

/// Attaches `Idempotency-Key` when [RequestOptions.extra] contains `idempotency_key`.
///
/// Backend may ignore the header today; keys are still stored on outbox rows for replay.
class IdempotencyInterceptor extends Interceptor {
  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    final key = options.extra['idempotency_key'] as String?;
    if (key != null && key.isNotEmpty) {
      options.headers['Idempotency-Key'] = key;
    }
    handler.next(options);
  }
}
