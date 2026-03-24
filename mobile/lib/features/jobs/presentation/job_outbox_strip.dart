import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/sync/outbox_sync_providers.dart';

/// Shows when this job has pending/failed/conflicting outbox rows.
class JobOutboxStrip extends ConsumerWidget {
  const JobOutboxStrip({super.key, required this.jobId});

  final String jobId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final summary = ref.watch(jobOutboxSummaryProvider(jobId));
    return summary.when(
      loading: () => const SizedBox.shrink(),
      error: (_, __) => const SizedBox.shrink(),
      data: (s) {
        if (!s.hasAny) return const SizedBox.shrink();
        return Padding(
          padding: const EdgeInsets.only(bottom: 12),
          child: Material(
            color: Theme.of(context).colorScheme.tertiaryContainer,
            borderRadius: BorderRadius.circular(8),
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Row(
                children: [
                  Icon(
                    Icons.cloud_upload_outlined,
                    color: Theme.of(context).colorScheme.onTertiaryContainer,
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      'Unsynced job actions: ${s.pending} waiting to send'
                      '${s.failed > 0 ? ', ${s.failed} failed and need retry' : ''}'
                      '${s.conflict > 0 ? ', ${s.conflict} conflict (review details)' : ''}. '
                      'Use Sync diagnostics to retry or inspect errors.',
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                  ),
                ],
              ),
            ),
          ),
        );
      },
    );
  }
}
