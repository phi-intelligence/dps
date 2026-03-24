import 'package:drift/drift.dart';

/// Queued engineer writes for offline replay (Wave 5 outbox).
///
/// Status: [OutboxStatus] — pending, syncing, synced, failed, conflict.
/// [attemptCount] doubles as retry counter (incremented on each failed attempt).
class OutboxOps extends Table {
  IntColumn get id => integer().autoIncrement()();
  TextColumn get clientOpId => text().unique()();
  TextColumn get operationType => text()();
  /// Optional job scope for UI filtering (telemetry may be null).
  TextColumn get jobId => text().nullable()();
  TextColumn get httpMethod => text()();
  TextColumn get path => text()();
  TextColumn get requestBodyJson => text()();
  TextColumn get idempotencyKey => text()();
  DateTimeColumn get createdAt => dateTime()();
  DateTimeColumn get updatedAt => dateTime().nullable()();
  IntColumn get attemptCount => integer().withDefault(const Constant(0))();
  DateTimeColumn get lastAttemptAt => dateTime().nullable()();
  TextColumn get lastError => text().nullable()();
  TextColumn get status => text()();
}
