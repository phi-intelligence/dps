import 'dart:convert';

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:uuid/uuid.dart';

import '../../features/jobs/data/models/job_dto.dart';
import '../errors/error_mapper.dart';
import '../network/dio_client.dart';
import 'connectivity_service.dart';
import 'outbox_operation_type.dart';
import 'outbox_repository.dart';
import 'recoverable_errors.dart';
import 'submission_outcome.dart';
import 'sync_engine.dart';

final syncCoordinatorProvider = Provider<SyncCoordinator>((ref) {
  return SyncCoordinator(
    ref: ref,
    dio: ref.watch(dioProvider),
    connectivity: ref.watch(connectivityServiceProvider),
    outbox: ref.watch(outboxRepositoryProvider),
  );
});

/// Maximum JSON request body size for queuing media (Wave 5 policy).
///
/// **Backend alignment:** must match `ENGINEER_MOBILE_MAX_MEDIA_JSON_BYTES` in
/// `backend/app/modules/dispatch/engineer_mobile_constants.py` (2 MiB).
///
/// See [WAVE5_SYNC_POLICY.md](../../../../docs/WAVE5_SYNC_POLICY.md).
const int kMaxQueuedMediaPayloadBytes = 2 * 1024 * 1024;

/// Coordinates try-now + queue for engineer actions.
///
/// Policy per operation type is documented in [WAVE5_SYNC_POLICY.md].
class SyncCoordinator {
  SyncCoordinator({
    required this.ref,
    required this.dio,
    required this.connectivity,
    required this.outbox,
  });

  final Ref ref;
  final Dio dio;
  final ConnectivityService connectivity;
  final OutboxRepository outbox;
  static const _uuid = Uuid();

  Future<void> _kickSync() => ref.read(syncEngineProvider).processQueue();

  Future<bool> _isMediaPhase2Enabled() async {
    try {
      final res = await dio.get<Map<String, dynamic>>('/jobs/media/capabilities');
      final data = res.data;
      if (data == null) return false;
      return data['phase2_enabled'] == true;
    } catch (_) {
      return false;
    }
  }

  /// Try-now-then-queue: punch is safety-critical.
  Future<SubmissionOutcome> submitPunch({
    required String kind,
    required String jobId,
    required double latitude,
    required double longitude,
  }) async {
    final path = kind == 'in' ? '/time/punch/in' : '/time/punch/out';
    final opType =
        kind == 'in' ? OutboxOperationType.punchIn : OutboxOperationType.punchOut;
    final body = <String, dynamic>{
      'job_id': jobId,
      'latitude': latitude,
      'longitude': longitude,
    };
    final idem = _uuid.v4();
    final clientId = _uuid.v4();

    Future<void> enqueue() async {
      await outbox.enqueue(
        clientOpId: clientId,
        operationType: opType,
        jobId: jobId,
        httpMethod: 'POST',
        path: path,
        requestBody: body,
        idempotencyKey: idem,
      );
      await _kickSync();
    }

    if (await connectivity.isOnline) {
      try {
        await dio.post<dynamic>(
          path,
          data: body,
          options: Options(
            extra: <String, Object?>{'idempotency_key': idem},
          ),
        );
        return SubmissionOutcome.synced;
      } on DioException catch (e) {
        if (RecoverableErrors.isRecoverable(e)) {
          await enqueue();
          return SubmissionOutcome.queued;
        }
        return SubmissionOutcome.failed(ErrorMapper.fromDio(e).message);
      }
    } else {
      await enqueue();
      return SubmissionOutcome.queued;
    }
  }

  /// Try-now-then-queue.
  Future<SubmissionOutcome> submitForm({
    required String jobId,
    required String formKey,
    required Map<String, Object> data,
  }) async {
    final path = '/jobs/$jobId/forms/$formKey/submit';
    final body = <String, dynamic>{'data': data};
    final idem = _uuid.v4();
    final clientId = _uuid.v4();

    Future<void> enqueue() async {
      await outbox.enqueue(
        clientOpId: clientId,
        operationType: OutboxOperationType.formSubmit,
        jobId: jobId,
        httpMethod: 'POST',
        path: path,
        requestBody: body,
        idempotencyKey: idem,
      );
      await _kickSync();
    }

    if (await connectivity.isOnline) {
      try {
        final response = await dio.post<Map<String, dynamic>>(
          path,
          data: body,
          options: Options(
            extra: <String, Object?>{'idempotency_key': idem},
          ),
        );
        if (response.data == null) {
          return SubmissionOutcome.failed('Empty form submission response');
        }
        return SubmissionOutcome.synced;
      } on DioException catch (e) {
        if (RecoverableErrors.isRecoverable(e)) {
          await enqueue();
          return SubmissionOutcome.queued;
        }
        return SubmissionOutcome.failed(ErrorMapper.fromDio(e).message);
      }
    } else {
      await enqueue();
      return SubmissionOutcome.queued;
    }
  }

  /// Try-now-then-queue.
  Future<SubmissionOutcome> submitSignature({
    required String jobId,
    required Map<String, Object> signature,
  }) async {
    final path = '/jobs/$jobId/signature';
    final body = <String, dynamic>{'signature': signature};
    final idem = _uuid.v4();
    final clientId = _uuid.v4();

    Future<void> enqueue() async {
      await outbox.enqueue(
        clientOpId: clientId,
        operationType: OutboxOperationType.signatureSubmit,
        jobId: jobId,
        httpMethod: 'POST',
        path: path,
        requestBody: body,
        idempotencyKey: idem,
      );
      await _kickSync();
    }

    if (await connectivity.isOnline) {
      try {
        final response = await dio.post<Map<String, dynamic>>(
          path,
          data: body,
          options: Options(
            extra: <String, Object?>{'idempotency_key': idem},
          ),
        );
        if (response.data == null) {
          return SubmissionOutcome.failed('Empty signature response');
        }
        return SubmissionOutcome.synced;
      } on DioException catch (e) {
        if (RecoverableErrors.isRecoverable(e)) {
          await enqueue();
          return SubmissionOutcome.queued;
        }
        return SubmissionOutcome.failed(ErrorMapper.fromDio(e).message);
      }
    } else {
      await enqueue();
      return SubmissionOutcome.queued;
    }
  }

  /// Try-now-then-queue only if online and payload under size cap.
  ///
  /// Offline: blocked (JSON/base64 is heavy; we do not queue blindly).
  Future<SubmissionOutcome> submitMedia({
    required String jobId,
    required List<Map<String, Object>> payloads,
  }) async {
    final path = '/jobs/$jobId/media';
    final body = <String, dynamic>{
      'media_type': 'photo',
      'payloads': payloads,
    };
    final encoded = jsonEncode(body);
    final byteLen = utf8.encode(encoded).length;

    if (!await connectivity.isOnline) {
      return SubmissionOutcome.blocked(
        'Cannot queue photos while offline: JSON/base64 payloads are large and '
        'may exceed device/API limits. Connect to submit, or retry when online.',
      );
    }

    if (byteLen > kMaxQueuedMediaPayloadBytes) {
      return SubmissionOutcome.failed(
        'Photo batch too large to queue ($byteLen bytes). Reduce images or size.',
      );
    }

    final idem = _uuid.v4();
    final clientId = _uuid.v4();

    Future<void> enqueue() async {
      await outbox.enqueue(
        clientOpId: clientId,
        operationType: OutboxOperationType.mediaSubmit,
        jobId: jobId,
        httpMethod: 'POST',
        path: path,
        requestBody: body,
        idempotencyKey: idem,
      );
      await _kickSync();
    }

    try {
      Map<String, dynamic>? data;
      if (await _isMediaPhase2Enabled()) {
        try {
          final session = await dio.post<Map<String, dynamic>>(
            '/jobs/$jobId/media/upload-sessions',
            data: const {'media_type': 'photo'},
          );
          final sessionId = session.data?['id'] as String?;
          if (sessionId == null || sessionId.isEmpty) {
            return SubmissionOutcome.failed('Media phase 2 session creation failed');
          }
          final commit = await dio.post<Map<String, dynamic>>(
            '/jobs/$jobId/media/upload-sessions/$sessionId/commit',
            data: <String, dynamic>{'payloads': payloads},
            options: Options(
              extra: <String, Object?>{'idempotency_key': idem},
            ),
          );
          data = commit.data;
        } on DioException {
          // Safe fallback for incremental rollout: old clients and old path keep working.
          final response = await dio.post<Map<String, dynamic>>(
            path,
            data: body,
            options: Options(
              extra: <String, Object?>{'idempotency_key': idem},
            ),
          );
          data = response.data;
        }
      } else {
        final response = await dio.post<Map<String, dynamic>>(
          path,
          data: body,
          options: Options(
            extra: <String, Object?>{'idempotency_key': idem},
          ),
        );
        data = response.data;
      }
      if (data == null) {
        return SubmissionOutcome.failed('Empty media response');
      }
      return SubmissionOutcome.synced;
    } on DioException catch (e) {
      if (RecoverableErrors.isRecoverable(e)) {
        await enqueue();
        return SubmissionOutcome.queued;
      }
      return SubmissionOutcome.failed(ErrorMapper.fromDio(e).message);
    }
  }

  /// Try-now-then-queue.
  Future<SubmissionOutcome> submitPartsUsage({
    required String jobId,
    required List<Map<String, Object>> items,
  }) async {
    final path = '/jobs/$jobId/parts-usage';
    final body = <String, dynamic>{'items': items};
    final idem = _uuid.v4();
    final clientId = _uuid.v4();

    Future<void> enqueue() async {
      await outbox.enqueue(
        clientOpId: clientId,
        operationType: OutboxOperationType.partsUsage,
        jobId: jobId,
        httpMethod: 'POST',
        path: path,
        requestBody: body,
        idempotencyKey: idem,
      );
      await _kickSync();
    }

    if (await connectivity.isOnline) {
      try {
        final response = await dio.post<Map<String, dynamic>>(
          path,
          data: body,
          options: Options(
            extra: <String, Object?>{'idempotency_key': idem},
          ),
        );
        if (response.data == null) {
          return SubmissionOutcome.failed('Empty parts usage response');
        }
        return SubmissionOutcome.synced;
      } on DioException catch (e) {
        if (RecoverableErrors.isRecoverable(e)) {
          await enqueue();
          return SubmissionOutcome.queued;
        }
        return SubmissionOutcome.failed(ErrorMapper.fromDio(e).message);
      }
    } else {
      await enqueue();
      return SubmissionOutcome.queued;
    }
  }

  /// Try-now-then-queue for engineer accept action.
  Future<SubmissionOutcome> submitAcceptJob({
    required String jobId,
    List<String>? requiredCompetencies,
  }) async {
    final path = '/jobs/$jobId/accept';
    final body = <String, dynamic>{
      if (requiredCompetencies != null)
        'required_competencies': requiredCompetencies,
    };
    final idem = _uuid.v4();
    final clientId = _uuid.v4();

    Future<void> enqueue() async {
      await outbox.enqueue(
        clientOpId: clientId,
        operationType: OutboxOperationType.acceptJob,
        jobId: jobId,
        httpMethod: 'POST',
        path: path,
        requestBody: body,
        idempotencyKey: idem,
      );
      await _kickSync();
    }

    if (await connectivity.isOnline) {
      try {
        await dio.post<Map<String, dynamic>>(
          path,
          data: body,
          options: Options(extra: <String, Object?>{'idempotency_key': idem}),
        );
        return SubmissionOutcome.synced;
      } on DioException catch (e) {
        if (RecoverableErrors.isRecoverable(e)) {
          await enqueue();
          return SubmissionOutcome.queued;
        }
        return SubmissionOutcome.failed(ErrorMapper.fromDio(e).message);
      }
    }

    await enqueue();
    return SubmissionOutcome.queued;
  }

  /// Try-now-then-queue for engineer note creation.
  Future<SubmissionOutcome> submitJobNote({
    required String jobId,
    required String bodyText,
    String source = 'engineer_note',
  }) async {
    final path = '/jobs/$jobId/notes';
    final body = <String, dynamic>{
      'body': bodyText,
      'source': source,
    };
    final idem = _uuid.v4();
    final clientId = _uuid.v4();

    Future<void> enqueue() async {
      await outbox.enqueue(
        clientOpId: clientId,
        operationType: OutboxOperationType.jobNote,
        jobId: jobId,
        httpMethod: 'POST',
        path: path,
        requestBody: body,
        idempotencyKey: idem,
      );
      await _kickSync();
    }

    if (await connectivity.isOnline) {
      try {
        await dio.post<Map<String, dynamic>>(
          path,
          data: body,
          options: Options(extra: <String, Object?>{'idempotency_key': idem}),
        );
        return SubmissionOutcome.synced;
      } on DioException catch (e) {
        if (RecoverableErrors.isRecoverable(e)) {
          await enqueue();
          return SubmissionOutcome.queued;
        }
        return SubmissionOutcome.failed(ErrorMapper.fromDio(e).message);
      }
    }

    await enqueue();
    return SubmissionOutcome.queued;
  }

  /// Best-effort only: telemetry is not persisted to outbox.
  Future<SubmissionOutcome> submitTelemetryBestEffort({
    required double latitude,
    required double longitude,
    required String occurredAtIsoUtc,
    double? heading,
    double? speed,
    double? accuracy,
  }) async {
    if (!await connectivity.isOnline) {
      return SubmissionOutcome.failed('No connectivity for telemetry');
    }
    try {
      await dio.post<dynamic>(
        '/tracking/telemetry/engineer',
        data: <String, dynamic>{
          'latitude': latitude,
          'longitude': longitude,
          'occurred_at': occurredAtIsoUtc,
          if (heading != null) 'heading': heading,
          if (speed != null) 'speed': speed,
          if (accuracy != null) 'accuracy': accuracy,
        },
      );
      return SubmissionOutcome.synced;
    } on DioException catch (e) {
      return SubmissionOutcome.failed(ErrorMapper.fromDio(e).message);
    }
  }

  Future<JobDto?> fetchJobDetail(String jobId) async {
    try {
      final response = await dio.get<Map<String, dynamic>>('/jobs/$jobId');
      final data = response.data;
      if (data == null) return null;
      return JobDto.fromJson(data);
    } catch (_) {
      return null;
    }
  }
}
