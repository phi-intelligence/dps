import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../config/app_config.dart';
import '../auth/token_storage.dart' show tokenStorageProvider;
import 'api_error_interceptor.dart';
import 'auth_interceptor.dart';
import 'client_version_interceptor.dart';
import 'idempotency_interceptor.dart';
import 'logging_interceptor.dart';

final appConfigProvider = Provider<AppConfig>((ref) => const AppConfig());

final dioProvider = Provider<Dio>((ref) {
  final config = ref.watch(appConfigProvider);
  final tokenStorage = ref.watch(tokenStorageProvider);

  final dio = Dio(
    BaseOptions(
      baseUrl: config.apiBase,
      connectTimeout: const Duration(seconds: 30),
      receiveTimeout: const Duration(seconds: 30),
      headers: const {'Content-Type': 'application/json'},
    ),
  );

  dio.interceptors.addAll([
    LoggingInterceptor(),
    ClientVersionInterceptor(),
    IdempotencyInterceptor(),
    AuthInterceptor(tokenStorage),
    ApiErrorInterceptor(),
  ]);

  return dio;
});
