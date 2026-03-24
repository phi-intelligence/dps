import 'package:drift/drift.dart';

/// Key/value sync metadata (last success, counters).
class SyncMetadata extends Table {
  TextColumn get key => text()();
  TextColumn get valueJson => text().nullable()();
  DateTimeColumn get updatedAt => dateTime()();

  @override
  Set<Column> get primaryKey => {key};
}
