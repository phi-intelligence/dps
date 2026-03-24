import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../persistence/app_database.dart';
import 'outbox_repository.dart';
import 'outbox_status.dart';

/// Aggregate counts for global sync UI.
class OutboxStats {
  const OutboxStats({
    required this.pending,
    required this.syncing,
    required this.failed,
    required this.conflict,
  });

  final int pending;
  final int syncing;
  final int failed;
  final int conflict;

  int get needsAttention => pending + syncing;
  int get problems => failed + conflict;

  static OutboxStats fromRows(List<OutboxOp> rows) {
    var p = 0, s = 0, f = 0, c = 0;
    for (final r in rows) {
      switch (r.status) {
        case OutboxStatus.pending:
          p++;
          break;
        case OutboxStatus.syncing:
          s++;
          break;
        case OutboxStatus.failed:
          f++;
          break;
        case OutboxStatus.conflict:
          c++;
          break;
        case OutboxStatus.synced:
          break;
        default:
          p++;
      }
    }
    return OutboxStats(
      pending: p,
      syncing: s,
      failed: f,
      conflict: c,
    );
  }
}

final outboxStatsProvider = StreamProvider<OutboxStats>((ref) {
  final db = ref.watch(appDatabaseProvider);
  return db.select(db.outboxOps).watch().map(OutboxStats.fromRows);
});

final lastEngineSyncProvider = FutureProvider<DateTime?>((ref) async {
  return ref.watch(outboxRepositoryProvider).getLastEngineSyncUtc();
});

/// Pending / failed / conflict rows for a single job (for job detail strip).
class JobOutboxSummary {
  const JobOutboxSummary({
    required this.pending,
    required this.failed,
    required this.conflict,
  });

  final int pending;
  final int failed;
  final int conflict;

  bool get hasAny => pending + failed + conflict > 0;

  static JobOutboxSummary empty() =>
      const JobOutboxSummary(pending: 0, failed: 0, conflict: 0);

  static JobOutboxSummary forJob(String jobId, List<OutboxOp> rows) {
    var p = 0, f = 0, c = 0;
    for (final r in rows) {
      if (r.jobId != jobId) continue;
      switch (r.status) {
        case OutboxStatus.pending:
        case OutboxStatus.syncing:
          p++;
          break;
        case OutboxStatus.failed:
          f++;
          break;
        case OutboxStatus.conflict:
          c++;
          break;
        default:
          break;
      }
    }
    return JobOutboxSummary(pending: p, failed: f, conflict: c);
  }
}

final jobOutboxSummaryProvider =
    StreamProvider.family<JobOutboxSummary, String>((ref, jobId) {
  final db = ref.watch(appDatabaseProvider);
  return db.select(db.outboxOps).watch().map(
        (rows) => JobOutboxSummary.forJob(jobId, rows),
      );
});
