import 'dart:convert';

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/errors/api_exception.dart';
import '../../../core/errors/error_mapper.dart';
import '../../../core/network/dio_client.dart';

final timeRepositoryProvider = Provider<TimeRepository>((ref) {
  return TimeRepository(dio: ref.watch(dioProvider));
});

class TimeRepository {
  TimeRepository({required this.dio});

  final Dio dio;

  /// `POST /time/punch/in` | `POST /time/punch/out`
  Future<String> punch({
    required String kind,
    required String jobId,
    required double latitude,
    required double longitude,
  }) async {
    final path = kind == 'in' ? '/time/punch/in' : '/time/punch/out';
    try {
      final response = await dio.post<dynamic>(
        path,
        data: <String, dynamic>{
          'job_id': jobId,
          'latitude': latitude,
          'longitude': longitude,
        },
      );
      final data = response.data;
      if (data is String) return data;
      return jsonEncode(data);
    } on DioException catch (e) {
      if (e.error is ApiException) throw e.error! as ApiException;
      throw ErrorMapper.fromDio(e);
    }
  }
}
