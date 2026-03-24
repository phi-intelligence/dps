import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/errors/api_exception.dart';
import '../../../core/errors/error_mapper.dart';
import '../../../core/network/dio_client.dart';
import 'models/job_dto.dart';

final jobsRepositoryProvider = Provider<JobsRepository>((ref) {
  return JobsRepository(dio: ref.watch(dioProvider));
});

class JobsRepository {
  JobsRepository({required this.dio});

  final Dio dio;

  /// `GET /jobs` — Engineer receives assigned jobs only.
  Future<List<JobDto>> listJobs({int limit = 50, int offset = 0}) async {
    try {
      final response = await dio.get<List<dynamic>>(
        '/jobs',
        queryParameters: {
          'limit': limit,
          'offset': offset,
        },
      );
      final list = response.data;
      if (list == null) return [];
      return list
          .map((e) => JobDto.fromJson(e as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      if (e.error is ApiException) throw e.error! as ApiException;
      throw ErrorMapper.fromDio(e);
    }
  }

  /// `GET /jobs/{job_id}`
  Future<JobDto> getJob(String jobId) async {
    try {
      final response = await dio.get<Map<String, dynamic>>('/jobs/$jobId');
      final data = response.data;
      if (data == null) {
        throw ApiException(
          statusCode: response.statusCode,
          message: 'Empty job response',
          rawDetail: null,
        );
      }
      return JobDto.fromJson(data);
    } on DioException catch (e) {
      if (e.error is ApiException) throw e.error! as ApiException;
      throw ErrorMapper.fromDio(e);
    }
  }

  /// `POST /jobs/{job_id}/accept` — engineer workflow start (`status` → `accepted`).
  Future<JobDto> acceptJob(String jobId, {List<String>? requiredCompetencies}) async {
    try {
      final response = await dio.post<Map<String, dynamic>>(
        '/jobs/$jobId/accept',
        data: <String, dynamic>{
          if (requiredCompetencies != null)
            'required_competencies': requiredCompetencies,
        },
      );
      final data = response.data;
      if (data == null) {
        throw ApiException(
          statusCode: response.statusCode,
          message: 'Empty accept response',
          rawDetail: null,
        );
      }
      return JobDto.fromJson(data);
    } on DioException catch (e) {
      if (e.error is ApiException) throw e.error! as ApiException;
      throw ErrorMapper.fromDio(e);
    }
  }

  /// `GET /tracking/geofences/{job_id}` — **404** if not configured.
  Future<JobGeofenceDto?> getGeofence(String jobId) async {
    try {
      final response = await dio.get<Map<String, dynamic>>(
        '/tracking/geofences/$jobId',
      );
      final data = response.data;
      if (data == null) return null;
      return JobGeofenceDto.fromJson(data);
    } on DioException catch (e) {
      final code = e.response?.statusCode;
      if (code == 404) return null;
      if (e.error is ApiException) {
        final ae = e.error! as ApiException;
        if (ae.statusCode == 404) return null;
        throw ae;
      }
      throw ErrorMapper.fromDio(e);
    }
  }
}
