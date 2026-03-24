import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/errors/api_exception.dart';
import '../../../core/errors/error_mapper.dart';
import '../../../core/network/dio_client.dart';

final jobActivityRepositoryProvider = Provider<JobActivityRepository>(
  (ref) => JobActivityRepository(dio: ref.watch(dioProvider)),
);

class JobActivityItemDto {
  JobActivityItemDto({
    required this.id,
    required this.jobId,
    required this.authorUserId,
    required this.activityType,
    required this.source,
    required this.body,
    required this.createdAt,
  });

  final String id;
  final String jobId;
  final String authorUserId;
  final String activityType;
  final String source;
  final String body;
  final DateTime createdAt;

  factory JobActivityItemDto.fromJson(Map<String, dynamic> json) {
    return JobActivityItemDto(
      id: json['id'] as String,
      jobId: json['job_id'] as String,
      authorUserId: json['author_user_id'] as String,
      activityType: json['activity_type'] as String? ?? 'note',
      source: json['source'] as String? ?? 'engineer_note',
      body: json['body'] as String? ?? '',
      createdAt: DateTime.parse(json['created_at'] as String),
    );
  }
}

class JobActivityRepository {
  JobActivityRepository({required this.dio});

  final Dio dio;

  Future<List<JobActivityItemDto>> listJobActivity(String jobId) async {
    try {
      final response = await dio.get<List<dynamic>>('/jobs/$jobId/activity');
      final list = response.data ?? const <dynamic>[];
      return list
          .whereType<Map<String, dynamic>>()
          .map(JobActivityItemDto.fromJson)
          .toList();
    } on DioException catch (e) {
      if (e.error is ApiException) throw e.error! as ApiException;
      throw ErrorMapper.fromDio(e);
    }
  }
}
