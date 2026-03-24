import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:phi_dps_mobile/core/errors/api_exception.dart';
import 'package:phi_dps_mobile/core/errors/error_mapper.dart';

void main() {
  group('ErrorMapper.fromDio', () {
    test('maps FastAPI string detail', () {
      final d = DioException(
        requestOptions: RequestOptions(path: '/x'),
        response: Response(
          requestOptions: RequestOptions(path: '/x'),
          statusCode: 400,
          data: {'detail': 'Geofence required'},
        ),
        type: DioExceptionType.badResponse,
      );
      final e = ErrorMapper.fromDio(d);
      expect(e, isA<ApiException>());
      expect(e.statusCode, 400);
      expect(e.message, 'Geofence required');
    });

    test('maps missing_required_keys object detail', () {
      final d = DioException(
        requestOptions: RequestOptions(path: '/x'),
        response: Response(
          requestOptions: RequestOptions(path: '/x'),
          statusCode: 422,
          data: {
            'detail': {
              'missing_required_keys': ['a', 'b'],
            },
          },
        ),
        type: DioExceptionType.badResponse,
      );
      final e = ErrorMapper.fromDio(d);
      expect(e.message, contains('a'));
      expect(e.message, contains('b'));
    });

    test('returns nested ApiException unchanged', () {
      final inner = ApiException(statusCode: 400, message: 'x');
      final d = DioException(
        requestOptions: RequestOptions(path: '/x'),
        error: inner,
        type: DioExceptionType.badResponse,
      );
      expect(ErrorMapper.fromDio(d), same(inner));
    });

    test('maps 409 idempotency conflict string detail (pilot replay)', () {
      final d = DioException(
        requestOptions: RequestOptions(path: '/time/punch/in'),
        response: Response(
          requestOptions: RequestOptions(path: '/time/punch/in'),
          statusCode: 409,
          data: {
            'detail': 'Idempotency-Key reused with a different request payload',
          },
        ),
        type: DioExceptionType.badResponse,
      );
      final e = ErrorMapper.fromDio(d);
      expect(e.statusCode, 409);
      expect(e.message, contains('Idempotency-Key'));
    });

    test('maps 413 media payload too large string detail', () {
      final d = DioException(
        requestOptions: RequestOptions(path: '/jobs/j1/media'),
        response: Response(
          requestOptions: RequestOptions(path: '/jobs/j1/media'),
          statusCode: 413,
          data: {
            'detail': 'Media JSON payload exceeds 2097152 bytes',
          },
        ),
        type: DioExceptionType.badResponse,
      );
      final e = ErrorMapper.fromDio(d);
      expect(e.statusCode, 413);
      expect(e.message, isNotEmpty);
    });
  });
}
