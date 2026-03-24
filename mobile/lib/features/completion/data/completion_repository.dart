import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/errors/api_exception.dart';
import '../../../core/errors/error_mapper.dart';
import '../../../core/network/dio_client.dart';
import 'models/completion_requirements_dto.dart';

final completionRepositoryProvider = Provider<CompletionRepository>((ref) {
  return CompletionRepository(dio: ref.watch(dioProvider));
});

class CompletionRepository {
  CompletionRepository({required this.dio});

  final Dio dio;

  /// `GET /jobs/{job_id}/completion-requirements`
  Future<JobCompletionRequirementsBundleDto> getCompletionRequirements(
    String jobId,
  ) async {
    try {
      final response = await dio.get<Map<String, dynamic>>(
        '/jobs/$jobId/completion-requirements',
      );
      final data = response.data;
      if (data == null) {
        throw ApiException(
          statusCode: response.statusCode,
          message: 'Empty completion requirements response',
          rawDetail: null,
        );
      }
      return JobCompletionRequirementsBundleDto.fromJson(data);
    } on DioException catch (e) {
      if (e.error is ApiException) throw e.error! as ApiException;
      throw ErrorMapper.fromDio(e);
    }
  }
}
