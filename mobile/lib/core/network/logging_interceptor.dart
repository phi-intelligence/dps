import 'package:dio/dio.dart';

import '../logging/app_logger.dart';

class LoggingInterceptor extends Interceptor {
  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    final safeHeaders = Map<String, dynamic>.from(options.headers);
    safeHeaders.removeWhere((k, _) => k.toLowerCase() == 'authorization');
    appDebug('${options.method} ${options.uri}', tag: 'HTTP');
    handler.next(options);
  }

  @override
  void onResponse(Response<dynamic> response, ResponseInterceptorHandler handler) {
    appDebug('${response.statusCode} ${response.requestOptions.uri}', tag: 'HTTP');
    handler.next(response);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) {
    appDebug('ERR ${err.response?.statusCode} ${err.requestOptions.uri} ${err.message}', tag: 'HTTP');
    handler.next(err);
  }
}
