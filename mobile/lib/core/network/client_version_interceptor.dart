import 'package:dio/dio.dart';
import 'package:package_info_plus/package_info_plus.dart';

/// Adds [X-Client-Version] once per process (app package version).
class ClientVersionInterceptor extends Interceptor {
  static String? _version;

  @override
  Future<void> onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    _version ??= (await PackageInfo.fromPlatform()).version;
    options.headers['X-Client-Version'] = _version!;
    handler.next(options);
  }
}
