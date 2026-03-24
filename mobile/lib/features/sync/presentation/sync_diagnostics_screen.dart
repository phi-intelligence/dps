import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/errors/action_failure_guidance.dart';
import '../../../core/persistence/app_database.dart';
import '../../../core/sync/outbox_repository.dart';
import '../../../core/sync/outbox_status.dart';
import '../../../core/sync/outbox_sync_providers.dart';
import '../../../core/sync/sync_engine.dart';

/// Lists outbox rows + manual sync retry.
class SyncDiagnosticsScreen extends ConsumerStatefulWidget {
  const SyncDiagnosticsScreen({super.key});

  @override
  ConsumerState<SyncDiagnosticsScreen> createState() =>
      _SyncDiagnosticsScreenState();
}

class _SyncDiagnosticsScreenState extends ConsumerState<SyncDiagnosticsScreen> {
  String _statusFilter = 'all';

  @override
  Widget build(BuildContext context) {
    final ref = this.ref;
    final rowsAsync = ref.watch(_outboxRowsProvider);
    final lastSync = ref.watch(lastEngineSyncProvider);
    final syncing = ref.watch(syncRunningProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Sync & outbox'),
        leading: IconButton(
          icon: const Icon(Icons.close),
          onPressed: () => context.pop(),
        ),
        actions: [
          IconButton(
            tooltip: 'Retry all failed/conflict',
            onPressed: syncing
                ? null
                : () async {
                    await ref.read(outboxRepositoryProvider).retryAllRetryable();
                    await ref.read(syncEngineProvider).processQueue();
                  },
            icon: const Icon(Icons.replay_circle_filled_outlined),
          ),
          IconButton(
            tooltip: 'Sync now',
            onPressed: syncing
                ? null
                : () async {
                    await ref.read(syncEngineProvider).processQueue();
                  },
            icon: syncing
                ? const SizedBox(
                    width: 22,
                    height: 22,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.sync),
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          lastSync.when(
            data: (t) => Text(
              t != null
                  ? 'Last successful engine sync: ${t.toLocal()}'
                  : 'No successful engine sync yet',
              style: Theme.of(context).textTheme.bodySmall,
            ),
            loading: () => const Text('…'),
            error: (e, _) => Text('Meta: $e'),
          ),
          const SizedBox(height: 16),
          Text(
            'Queued operations',
            style: Theme.of(context).textTheme.titleMedium,
          ),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8,
            children: [
              _filterChip('all', 'All'),
              _filterChip(OutboxStatus.pending, 'Pending'),
              _filterChip(OutboxStatus.syncing, 'Syncing'),
              _filterChip(OutboxStatus.failed, 'Failed'),
              _filterChip(OutboxStatus.conflict, 'Conflict'),
            ],
          ),
          const SizedBox(height: 8),
          rowsAsync.when(
            loading: () => const Center(child: CircularProgressIndicator()),
            error: (e, _) => Text('$e'),
            data: (rows) {
              final filtered = _statusFilter == 'all'
                  ? rows
                  : rows.where((r) => r.status == _statusFilter).toList();
              if (filtered.isEmpty) {
                return const Text('Outbox is empty.');
              }
              return Column(
                children: filtered
                    .map(
                      (r) => Card(
                        child: ListTile(
                          title: Text(r.operationType),
                          subtitle: Text(
                            '${_statusLabel(r.status)} · ${r.path}\n'
                            'job: ${r.jobId ?? "—"} · retries: ${r.attemptCount}\n'
                            '${r.lastError?.trim().isNotEmpty == true ? r.lastError : "No error details"}'
                            '${_inlineGuidance(r.lastError).isEmpty ? '' : '\nHint: ${_inlineGuidance(r.lastError)}'}',
                            style: Theme.of(context).textTheme.bodySmall,
                          ),
                          isThreeLine: true,
                          trailing: (r.status == OutboxStatus.failed ||
                                  r.status == OutboxStatus.conflict)
                              ? Wrap(
                                  spacing: 4,
                                  children: [
                                    IconButton(
                                      tooltip: 'Retry this item',
                                      onPressed: syncing
                                          ? null
                                          : () async {
                                              await ref.read(outboxRepositoryProvider).retryRow(r.id);
                                              await ref.read(syncEngineProvider).processQueue();
                                            },
                                      icon: const Icon(Icons.replay_outlined),
                                    ),
                                    IconButton(
                                      tooltip: 'Discard this item',
                                      onPressed: syncing
                                          ? null
                                          : () async {
                                              await ref.read(outboxRepositoryProvider).deleteRow(r.id);
                                            },
                                      icon: const Icon(Icons.delete_outline),
                                    ),
                                  ],
                                )
                              : null,
                        ),
                      ),
                    )
                    .toList(),
              );
            },
          ),
          const SizedBox(height: 24),
          Text(
            'Statuses: ${OutboxStatus.pending}, ${OutboxStatus.syncing}, '
            '${OutboxStatus.failed}, ${OutboxStatus.conflict}. '
            'Successful rows are removed from the outbox. '
            'Tip: retry for network/server transient errors; discard for duplicate/conflict rows you do not want replayed.',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: Theme.of(context).colorScheme.onSurfaceVariant,
                ),
          ),
        ],
      ),
    );
  }

  Widget _filterChip(String value, String label) {
    return ChoiceChip(
      label: Text(label),
      selected: _statusFilter == value,
      onSelected: (_) => setState(() => _statusFilter = value),
    );
  }

  String _statusLabel(String raw) {
    switch (raw) {
      case OutboxStatus.pending:
        return 'Pending (waiting to sync)';
      case OutboxStatus.syncing:
        return 'Syncing now';
      case OutboxStatus.failed:
        return 'Failed (needs retry)';
      case OutboxStatus.conflict:
        return 'Conflict (server rejected as conflicting)';
      default:
        return raw;
    }
  }

  String _inlineGuidance(String? err) => actionFailureGuidance(err);
}

final _outboxRowsProvider = StreamProvider<List<OutboxOp>>((ref) {
  final db = ref.watch(appDatabaseProvider);
  return db.select(db.outboxOps).watch().map(
        (rows) => [...rows]..sort((a, b) => b.createdAt.compareTo(a.createdAt)),
      );
});
