import 'dart:convert';
import 'dart:math';

import 'package:dio/dio.dart';
import 'package:drift/drift.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../errors/error_mapper.dart';
import '../network/dio_client.dart';
import '../persistence/app_database.dart';
import 'connectivity_service.dart';
import 'outbox_repository.dart';
import 'outbox_status.dart';
import 'recoverable_errors.dart';

final syncEngineProvider = Provider<SyncEngine>((ref) {
  return SyncEngine(
    ref: ref,
    outbox: ref.watch(outboxRepositoryProvider),
    dio: ref.watch(dioProvider),
    connectivity: ref.watch(connectivityServiceProvider),
  );
});

/// True while [SyncEngine.processQueue] holds the mutex (sequential sync).
final syncRunningProvider = StateProvider<bool>((ref) => false);

/// Drains the local outbox with sequential POST/GET replay and backoff.
class SyncEngine {
  SyncEngine({
    required this.ref,
    required this.outbox,
    required this.dio,
    required this.connectivity,
  });

  final Ref ref;
  final OutboxRepository outbox;
  final Dio dio;
  final ConnectivityService connectivity;

  bool _mutex = false;

  static const maxAttempts = 12;

  /// Safe entry: skips if another run is active or device is offline.
  Future<void> processQueue() async {
    if (_mutex) return;
    if (!await connectivity.isOnline) return;
    _mutex = true;
    ref.read(syncRunningProvider.notifier).state = true;
    try {
      await outbox.resetStuckSyncing();
      while (await connectivity.isOnline) {
        final rows = await outbox.listProcessablePending();
        OutboxOp? next;
        for (final r in rows) {
          if (_canProcessNow(r)) {
            next = r;
            break;
          }
        }
        if (next == null) break;
        await _processOne(next);
      }
    } finally {
      _mutex = false;
      ref.read(syncRunningProvider.notifier).state = false;
    }
  }

  bool _canProcessNow(OutboxOp r) {
    if (r.attemptCount == 0 || r.lastAttemptAt == null) return true;
    final wait = _backoff(r.attemptCount);
    return DateTime.now().toUtc().isAfter(r.lastAttemptAt!.toUtc().add(wait));
  }

  Duration _backoff(int attemptCount) {
    final sec = min(300, pow(2, min(attemptCount, 8)).toInt());
    return Duration(seconds: sec);
  }

  Future<void> _processOne(OutboxOp row) async {
    final now = DateTime.now().toUtc();
    await outbox.updateRow(
      row.id,
      OutboxOpsCompanion(
        status: const Value(OutboxStatus.syncing),
        updatedAt: Value(now),
      ),
    );

    try {
      final data = jsonDecode(row.requestBodyJson);
      final method = row.httpMethod.toUpperCase();
      await dio.request<dynamic>(
        row.path,
        data: data,
        options: Options(
          method: method,
          extra: <String, Object?>{
            'idempotency_key': row.idempotencyKey,
          },
        ),
      );
      await outbox.deleteRow(row.id);
      await outbox.setLastEngineSyncUtc(DateTime.now().toUtc());
    } on DioException catch (e) {
      await _handleFailure(row, e);
    } catch (e, st) {
      await _handleFailure(
        row,
        DioException(
          requestOptions: RequestOptions(path: row.path),
          error: e,
          stackTrace: st,
        ),
      );
    }
  }

  Future<void> _handleFailure(OutboxOp row, DioException e) async {
    final now = DateTime.now().toUtc();
    final msg = ErrorMapper.fromDio(e).message;

    if (RecoverableErrors.isConflict(e)) {
      await outbox.updateRow(
        row.id,
        OutboxOpsCompanion(
          status: const Value(OutboxStatus.conflict),
          lastError: Value(msg),
          lastAttemptAt: Value(now),
          updatedAt: Value(now),
          attemptCount: Value(row.attemptCount + 1),
        ),
      );
      return;
    }

    if (RecoverableErrors.shouldMarkFailedImmediately(e)) {
      await outbox.updateRow(
        row.id,
        OutboxOpsCompanion(
          status: const Value(OutboxStatus.failed),
          lastError: Value(msg),
          lastAttemptAt: Value(now),
          updatedAt: Value(now),
          attemptCount: Value(row.attemptCount + 1),
        ),
      );
      return;
    }

    if (RecoverableErrors.isRecoverable(e)) {
      final nextCount = row.attemptCount + 1;
      if (nextCount >= maxAttempts) {
        await outbox.updateRow(
          row.id,
          OutboxOpsCompanion(
            status: const Value(OutboxStatus.failed),
            lastError: Value('$msg (max retries)'),
            lastAttemptAt: Value(now),
            updatedAt: Value(now),
            attemptCount: Value(nextCount),
          ),
        );
      } else {
        await outbox.updateRow(
          row.id,
          OutboxOpsCompanion(
            status: const Value(OutboxStatus.pending),
            lastError: Value(msg),
            lastAttemptAt: Value(now),
            updatedAt: Value(now),
            attemptCount: Value(nextCount),
          ),
        );
      }
      return;
    }

    await outbox.updateRow(
      row.id,
      OutboxOpsCompanion(
        status: const Value(OutboxStatus.failed),
        lastError: Value(msg),
        lastAttemptAt: Value(now),
        updatedAt: Value(now),
        attemptCount: Value(row.attemptCount + 1),
      ),
    );
  }
}
