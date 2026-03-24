import 'dart:convert';

import 'package:drift/drift.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/persistence/app_database.dart';
import 'models/job_dto.dart';

const _assignmentSnapshotKey = 'assignment_alert_snapshot_v1';

final assignmentAlertRepositoryProvider = Provider<AssignmentAlertRepository>(
  (ref) => AssignmentAlertRepository(db: ref.watch(appDatabaseProvider)),
);

class AssignmentAlert {
  const AssignmentAlert({
    required this.kind,
    required this.jobId,
    required this.message,
    required this.urgent,
  });

  final String kind;
  final String jobId;
  final String message;
  final bool urgent;
}

class AssignmentAlertRepository {
  AssignmentAlertRepository({required this.db});
  final AppDatabase db;

  Future<List<AssignmentAlert>> detectAndStore(List<JobDto> jobs) async {
    final previous = await _readSnapshot();
    final now = <String, Map<String, dynamic>>{
      for (final job in jobs)
        job.id: {
          'assigned_engineer_id': job.assignedEngineerId,
          'dispatch_priority': job.dispatchPriority,
          'delay_notice': job.delayNotice,
        },
    };

    final alerts = <AssignmentAlert>[];
    for (final job in jobs) {
      final prev = previous[job.id];
      if (prev == null) {
        alerts.add(
          AssignmentAlert(
            kind: 'new_assignment',
            jobId: job.id,
            message: 'New assignment received for ${job.displayTitle}.',
            urgent: (job.dispatchPriority ?? 0) >= 8,
          ),
        );
        continue;
      }
      final prevAssigned = prev['assigned_engineer_id'] as String?;
      if (prevAssigned != null && prevAssigned != job.assignedEngineerId) {
        alerts.add(
          AssignmentAlert(
            kind: 'reassignment',
            jobId: job.id,
            message: 'Assignment updated for job ${job.id}.',
            urgent: false,
          ),
        );
      }
      final prevPriority = (prev['dispatch_priority'] as num?)?.toInt() ?? 0;
      final currentPriority = job.dispatchPriority ?? 0;
      if (currentPriority >= 8 && currentPriority > prevPriority) {
        alerts.add(
          AssignmentAlert(
            kind: 'urgent_update',
            jobId: job.id,
            message: 'Urgent priority update on ${job.displayTitle}.',
            urgent: true,
          ),
        );
      }
      final prevDelay = prev['delay_notice'] as String?;
      if ((job.delayNotice ?? '').trim().isNotEmpty && prevDelay != job.delayNotice) {
        alerts.add(
          AssignmentAlert(
            kind: 'urgent_update',
            jobId: job.id,
            message: 'Dispatch sent an update for ${job.displayTitle}.',
            urgent: true,
          ),
        );
      }
    }

    await _writeSnapshot(now);
    return alerts.take(5).toList(growable: false);
  }

  Future<Map<String, Map<String, dynamic>>> _readSnapshot() async {
    final row = await (db.select(db.syncMetadata)..where((t) => t.key.equals(_assignmentSnapshotKey))).getSingleOrNull();
    final jsonText = row?.valueJson;
    if (jsonText == null || jsonText.trim().isEmpty) return {};
    final decoded = jsonDecode(jsonText);
    if (decoded is! Map<String, dynamic>) return {};
    final out = <String, Map<String, dynamic>>{};
    decoded.forEach((key, value) {
      if (value is Map<String, dynamic>) out[key] = value;
    });
    return out;
  }

  Future<void> _writeSnapshot(Map<String, Map<String, dynamic>> snapshot) async {
    await db.into(db.syncMetadata).insertOnConflictUpdate(
          SyncMetadataCompanion.insert(
            key: _assignmentSnapshotKey,
            valueJson: Value(jsonEncode(snapshot)),
            updatedAt: DateTime.now().toUtc(),
          ),
        );
  }
}
