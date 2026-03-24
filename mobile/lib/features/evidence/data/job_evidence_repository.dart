import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/errors/api_exception.dart';
import '../../../core/errors/error_mapper.dart';
import '../../../core/network/dio_client.dart';
import '../../completion/data/models/completion_requirements_dto.dart';
import 'models/evidence_submission_dto.dart';

final jobEvidenceRepositoryProvider = Provider<JobEvidenceRepository>((ref) {
  return JobEvidenceRepository(dio: ref.watch(dioProvider));
});

/// Engineer evidence: forms, signature, media, parts (`dispatch/routes.py`).
class JobEvidenceRepository {
  JobEvidenceRepository({required this.dio});

  final Dio dio;

  /// `POST /jobs/{job_id}/forms/{form_key}/submit` — body `{ "data": { ... } }`.
  /// Server validates `required_keys_json` against `data` when a requirement exists.
  Future<JobFormSubmissionDto> submitForm({
    required String jobId,
    required String formKey,
    required Map<String, Object> data,
  }) async {
    try {
      final response = await dio.post<Map<String, dynamic>>(
        '/jobs/$jobId/forms/$formKey/submit',
        data: <String, dynamic>{'data': data},
      );
      final m = response.data;
      if (m == null) {
        throw ApiException(
          statusCode: response.statusCode,
          message: 'Empty form submission response',
          rawDetail: null,
        );
      }
      return JobFormSubmissionDto.fromJson(m);
    } on DioException catch (e) {
      if (e.error is ApiException) throw e.error! as ApiException;
      throw ErrorMapper.fromDio(e);
    }
  }

  /// `POST /jobs/{job_id}/signature` — body `{ "signature": { ... } }`.
  Future<JobSignatureRequirementDto> submitSignature({
    required String jobId,
    required Map<String, Object> signature,
  }) async {
    try {
      final response = await dio.post<Map<String, dynamic>>(
        '/jobs/$jobId/signature',
        data: <String, dynamic>{'signature': signature},
      );
      final m = response.data;
      if (m == null) {
        throw ApiException(
          statusCode: response.statusCode,
          message: 'Empty signature response',
          rawDetail: null,
        );
      }
      return JobSignatureRequirementDto.fromJson(m);
    } on DioException catch (e) {
      if (e.error is ApiException) throw e.error! as ApiException;
      throw ErrorMapper.fromDio(e);
    }
  }

  /// `POST /jobs/{job_id}/media` — body `{ "media_type": "photo", "payloads": [ {...}, ... ] }`.
  /// Each payload is stored as JSON (e.g. base64 image + metadata). Not multipart.
  Future<JobMediaRequirementDto> submitMedia({
    required String jobId,
    String mediaType = 'photo',
    required List<Map<String, Object>> payloads,
  }) async {
    try {
      final response = await dio.post<Map<String, dynamic>>(
        '/jobs/$jobId/media',
        data: <String, dynamic>{
          'media_type': mediaType,
          'payloads': payloads,
        },
      );
      final m = response.data;
      if (m == null) {
        throw ApiException(
          statusCode: response.statusCode,
          message: 'Empty media response',
          rawDetail: null,
        );
      }
      return JobMediaRequirementDto.fromJson(m);
    } on DioException catch (e) {
      if (e.error is ApiException) throw e.error! as ApiException;
      throw ErrorMapper.fromDio(e);
    }
  }

  /// `POST /jobs/{job_id}/parts-usage` — body `{ "items": [ { "sku", "quantity", ... } ] }`.
  /// `reconcile_parts_usage_submission` requires known SKUs in inventory.
  Future<JobPartsUsageRequirementDto> submitPartsUsage({
    required String jobId,
    required List<Map<String, Object>> items,
  }) async {
    try {
      final response = await dio.post<Map<String, dynamic>>(
        '/jobs/$jobId/parts-usage',
        data: <String, dynamic>{'items': items},
      );
      final m = response.data;
      if (m == null) {
        throw ApiException(
          statusCode: response.statusCode,
          message: 'Empty parts usage response',
          rawDetail: null,
        );
      }
      return JobPartsUsageRequirementDto.fromJson(m);
    } on DioException catch (e) {
      if (e.error is ApiException) throw e.error! as ApiException;
      throw ErrorMapper.fromDio(e);
    }
  }
}
