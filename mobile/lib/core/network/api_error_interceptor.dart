import 'package:dio/dio.dart';

import '../errors/api_exception.dart';
import '../errors/error_mapper.dart';

/// Converts API error bodies to [ApiException] on the [DioException.error] field.
class ApiErrorInterceptor extends Interceptor {
  @override
  void onError(DioException err, ErrorInterceptorHandler handler) {
    if (err.type == DioExceptionType.badResponse) {
      final api = ErrorMapper.fromDio(err);
      handler.reject(
        DioException(
          requestOptions: err.requestOptions,
          response: err.response,
          type: err.type,
          error: api,
          message: api.message,
        ),
      );
      return;
    }
    handler.next(err);
  }
}
