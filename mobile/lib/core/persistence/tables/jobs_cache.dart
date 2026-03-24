import 'package:drift/drift.dart';

/// Cached `GET /jobs/{id}` payloads (Wave 2+ refresh).
class JobsCache extends Table {
  TextColumn get jobId => text()();
  TextColumn get payloadJson => text()();
  DateTimeColumn get fetchedAt => dateTime()();

  @override
  Set<Column> get primaryKey => {jobId};
}
