import 'dart:convert';

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:phi_dps_mobile/auth_token.dart';
import '../../../core/auth/token_storage.dart';
import '../../../core/errors/api_exception.dart';
import '../../../core/errors/error_mapper.dart';
import '../../../core/network/dio_client.dart';

final authRepositoryProvider = Provider<AuthRepository>((ref) {
  return AuthRepository(
    dio: ref.watch(dioProvider),
    tokenStorage: ref.watch(tokenStorageProvider),
  );
});

class AuthRepository {
  AuthRepository({
    required this.dio,
    required this.tokenStorage,
  });

  final Dio dio;
  final TokenStorage tokenStorage;

  /// OAuth2 password grant — `POST /auth/token` (form-urlencoded).
  Future<void> login({
    required String username,
    required String password,
  }) async {
    try {
      final response = await dio.post<dynamic>(
        '/auth/token',
        data: {
          'username': username,
          'password': password,
        },
        options: Options(
          contentType: Headers.formUrlEncodedContentType,
        ),
      );
      final data = response.data;
      if (data is! Map<String, dynamic>) {
        throw ApiException(
          statusCode: response.statusCode,
          message: 'Invalid token response shape',
          rawDetail: data,
        );
      }
      final token = parseAccessTokenFromAuthJson(jsonEncode(data));
      await tokenStorage.writeAccessToken(token);
    } on DioException catch (e) {
      if (e.error is ApiException) throw e.error! as ApiException;
      throw ErrorMapper.fromDio(e);
    }
  }
}
