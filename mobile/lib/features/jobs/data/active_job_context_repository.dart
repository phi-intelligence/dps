import 'dart:convert';

import 'package:drift/drift.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/persistence/app_database.dart';

const _activeJobKey = 'active_job_id';

final activeJobContextRepositoryProvider = Provider<ActiveJobContextRepository>(
  (ref) => ActiveJobContextRepository(db: ref.watch(appDatabaseProvider)),
);

class ActiveJobContextRepository {
  ActiveJobContextRepository({required this.db});
  final AppDatabase db;

  Future<void> setActiveJobId(String? jobId) async {
    await db.into(db.syncMetadata).insertOnConflictUpdate(
          SyncMetadataCompanion.insert(
            key: _activeJobKey,
            valueJson: Value(jobId == null ? null : jsonEncode(jobId)),
            updatedAt: DateTime.now().toUtc(),
          ),
        );
  }

  Future<String?> getActiveJobId() async {
    final row = await (db.select(db.syncMetadata)..where((t) => t.key.equals(_activeJobKey))).getSingleOrNull();
    if (row?.valueJson == null) return null;
    final decoded = jsonDecode(row!.valueJson!);
    return decoded is String ? decoded : null;
  }
}

final activeJobIdProvider = FutureProvider<String?>((ref) {
  return ref.watch(activeJobContextRepositoryProvider).getActiveJobId();
});
