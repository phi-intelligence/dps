import 'dart:convert';

import 'package:dio/dio.dart';

import 'api_exception.dart';

/// Maps [DioException] to [ApiException] using FastAPI error body shapes.
class ErrorMapper {
  const ErrorMapper._();

  static ApiException fromDio(DioException e) {
    final existing = e.error;
    if (existing is ApiException) return existing;
    final response = e.response;
    final code = response?.statusCode;
    if (response != null) {
      final parsed = _parseBody(response.data, statusCode: code);
      if (parsed != null) return parsed;
    }
    return ApiException(
      statusCode: code,
      message: e.message ?? e.toString(),
      rawDetail: response?.data,
    );
  }

  static ApiException? _parseBody(dynamic data, {int? statusCode}) {
    if (data == null) return null;
    if (data is String) {
      try {
        final decoded = jsonDecode(data);
        return _fromDecoded(decoded, statusCode: statusCode);
      } catch (_) {
        return ApiException(statusCode: statusCode, message: data, rawDetail: data);
      }
    }
    if (data is Map<String, dynamic>) {
      return _fromDecoded(data, statusCode: statusCode);
    }
    return null;
  }

  static ApiException? _fromDecoded(Object? decoded, {int? statusCode}) {
    if (decoded is! Map<String, dynamic>) return null;
    final detail = decoded['detail'];
    if (detail == null) {
      return ApiException(
        statusCode: statusCode,
        message: decoded.toString(),
        rawDetail: decoded,
      );
    }
    if (detail is String) {
      return ApiException(statusCode: statusCode, message: detail, rawDetail: detail);
    }
    if (detail is List) {
      final msg = detail.map((e) => e.toString()).join('; ');
      return ApiException(statusCode: statusCode, message: msg, rawDetail: detail);
    }
    if (detail is Map<String, dynamic>) {
      final missing = detail['missing_required_keys'];
      if (missing is List) {
        return ApiException(
          statusCode: statusCode,
          message: 'Missing required keys: ${missing.join(", ")}',
          rawDetail: detail,
        );
      }
      return ApiException(
        statusCode: statusCode,
        message: detail.toString(),
        rawDetail: detail,
      );
    }
    return ApiException(statusCode: statusCode, message: detail.toString(), rawDetail: detail);
  }
}
