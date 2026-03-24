import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/sync/outbox_sync_providers.dart';
import '../../../core/sync/sync_engine.dart';

/// Global sync status: pending count, failures, manual navigation to diagnostics.
class SyncBanner extends ConsumerWidget {
  const SyncBanner({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final statsAsync = ref.watch(outboxStatsProvider);
    final syncing = ref.watch(syncRunningProvider);

    return Material(
      color: Theme.of(context).colorScheme.surfaceContainerHighest,
      child: InkWell(
        onTap: () => context.push('/jobs/sync'),
        child: Padding(
          padding: EdgeInsets.only(
            left: 12,
            right: 12,
            top: MediaQuery.of(context).padding.top > 0 ? 4 : 8,
            bottom: 8,
          ),
          child: Row(
            children: [
              if (syncing)
                const SizedBox(
                  width: 18,
                  height: 18,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              else
                Icon(
                  Icons.cloud_sync_outlined,
                  size: 20,
                  color: Theme.of(context).colorScheme.primary,
                ),
              const SizedBox(width: 8),
              Expanded(
                child: statsAsync.when(
                  loading: () => Text(
                    'Checking sync…',
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                  error: (e, _) => Text(
                    'Sync: $e',
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: Theme.of(context).colorScheme.error,
                        ),
                  ),
                  data: (stats) {
                    final parts = <String>[];
                    if (stats.needsAttention > 0) {
                      parts.add('${stats.pending} pending');
                      if (stats.syncing > 0) {
                        parts.add('${stats.syncing} syncing');
                      }
                    }
                    if (stats.failed > 0) {
                      parts.add('${stats.failed} failed');
                    }
                    if (stats.conflict > 0) {
                      parts.add('${stats.conflict} conflict');
                    }
                    final msg = parts.isEmpty ? 'All changes synced' : parts.join(' · ');
                    return Text(
                      msg,
                      style: Theme.of(context).textTheme.bodySmall,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    );
                  },
                ),
              ),
              Icon(
                Icons.chevron_right,
                size: 20,
                color: Theme.of(context).colorScheme.outline,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
