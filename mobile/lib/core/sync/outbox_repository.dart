import 'dart:convert';

import 'package:drift/drift.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../persistence/app_database.dart';
import 'outbox_status.dart';

final outboxRepositoryProvider = Provider<OutboxRepository>((ref) {
  return OutboxRepository(db: ref.watch(appDatabaseProvider));
});

class OutboxRepository {
  OutboxRepository({required this.db});

  final AppDatabase db;

  /// Insert a new pending row. [clientOpId] and [idempotencyKey] are typically unique UUIDs.
  Future<int> enqueue({
    required String clientOpId,
    required String operationType,
    String? jobId,
    required String httpMethod,
    required String path,
    required Object requestBody,
    required String idempotencyKey,
  }) async {
    final now = DateTime.now().toUtc();
    final bodyJson = jsonEncode(requestBody);
    return db.into(db.outboxOps).insert(
          OutboxOpsCompanion.insert(
            clientOpId: clientOpId,
            operationType: operationType,
            jobId: Value(jobId),
            httpMethod: httpMethod,
            path: path,
            requestBodyJson: bodyJson,
            idempotencyKey: idempotencyKey,
            createdAt: now,
            updatedAt: Value(now),
            status: OutboxStatus.pending,
          ),
        );
  }

  Future<void> updateRow(
    int id,
    OutboxOpsCompanion companion,
  ) async {
    await (db.update(db.outboxOps)..where((t) => t.id.equals(id))).write(companion);
  }

  Future<void> deleteRow(int id) async {
    await (db.delete(db.outboxOps)..where((t) => t.id.equals(id))).go();
  }

  /// If the app crashed mid-request, rows can be left in [OutboxStatus.syncing].
  Future<void> resetStuckSyncing() async {
    final now = DateTime.now().toUtc();
    await (db.update(db.outboxOps)
          ..where((t) => t.status.equals(OutboxStatus.syncing)))
        .write(
      OutboxOpsCompanion(
        status: const Value(OutboxStatus.pending),
        updatedAt: Value(now),
      ),
    );
  }

  /// Rows eligible for sync worker (pending, or failed with retries left handled by engine).
  Future<List<OutboxOp>> listProcessablePending() {
    return (db.select(db.outboxOps)
          ..where((t) => t.status.equals(OutboxStatus.pending))
          ..orderBy([(t) => OrderingTerm.asc(t.createdAt)]))
        .get();
  }

  Stream<List<OutboxOp>> watchAll() => db.select(db.outboxOps).watch();

  Future<void> retryRow(int id) async {
    final now = DateTime.now().toUtc();
    await (db.update(db.outboxOps)..where((t) => t.id.equals(id))).write(
      OutboxOpsCompanion(
        status: const Value(OutboxStatus.pending),
        updatedAt: Value(now),
      ),
    );
  }

  Future<void> retryAllRetryable() async {
    final now = DateTime.now().toUtc();
    await (db.update(db.outboxOps)
          ..where((t) =>
              t.status.equals(OutboxStatus.failed) |
              t.status.equals(OutboxStatus.conflict)))
        .write(
      OutboxOpsCompanion(
        status: const Value(OutboxStatus.pending),
        updatedAt: Value(now),
      ),
    );
  }

  Future<void> setLastEngineSyncUtc(DateTime t) async {
    final iso = t.toUtc().toIso8601String();
    await db.into(db.syncMetadata).insertOnConflictUpdate(
          SyncMetadataCompanion.insert(
            key: 'last_engine_sync_utc',
            valueJson: Value(jsonEncode(iso)),
            updatedAt: DateTime.now().toUtc(),
          ),
        );
  }

  Future<DateTime?> getLastEngineSyncUtc() async {
    final row = await (db.select(db.syncMetadata)
          ..where((t) => t.key.equals('last_engine_sync_utc')))
        .getSingleOrNull();
    if (row?.valueJson == null) return null;
    final decoded = jsonDecode(row!.valueJson!);
    if (decoded is String) return DateTime.tryParse(decoded);
    return null;
  }
}
