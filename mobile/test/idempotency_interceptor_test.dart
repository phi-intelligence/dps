import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:phi_dps_mobile/core/network/idempotency_interceptor.dart';

void main() {
  group('IdempotencyInterceptor', () {
    test('sets Idempotency-Key header when extra contains idempotency_key', () {
      const key = '550e8400-e29b-41d4-a716-446655440000';
      final options = RequestOptions(
        path: '/time/punch/in',
        extra: <String, Object?>{'idempotency_key': key},
      );
      IdempotencyInterceptor().onRequest(options, RequestInterceptorHandler());
      expect(options.headers['Idempotency-Key'], key);
    });

    test('does not set header when idempotency_key is absent', () {
      final options = RequestOptions(path: '/jobs/1');
      IdempotencyInterceptor().onRequest(options, RequestInterceptorHandler());
      expect(options.headers['Idempotency-Key'], isNull);
    });

    test('does not set header when idempotency_key is empty', () {
      final options = RequestOptions(
        path: '/x',
        extra: <String, Object?>{'idempotency_key': ''},
      );
      IdempotencyInterceptor().onRequest(options, RequestInterceptorHandler());
      expect(options.headers['Idempotency-Key'], isNull);
    });
  });
}
