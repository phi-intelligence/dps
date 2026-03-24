import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../auth/session_controller.dart';
import '../../../core/sync/outbox_sync_providers.dart';
import '../data/active_job_context_repository.dart';
import '../data/assignment_alert_repository.dart';
import '../data/jobs_list_notifier.dart';
import '../data/models/job_dto.dart';

/// Assigned jobs — tap a row to open [JobDetailScreen].
class JobListScreen extends ConsumerStatefulWidget {
  const JobListScreen({super.key});

  @override
  ConsumerState<JobListScreen> createState() => _JobListScreenState();
}

class _JobListScreenState extends ConsumerState<JobListScreen> {
  List<AssignmentAlert> _alerts = const [];
  String? _lastSnapshotKey;

  @override
  Widget build(BuildContext context) {
    final jobsAsync = ref.watch(jobListProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('My jobs'),
        actions: [
          IconButton(
            icon: const Icon(Icons.cloud_sync_outlined),
            tooltip: 'Sync & outbox',
            onPressed: () => context.push('/jobs/sync'),
          ),
          IconButton(
            icon: const Icon(Icons.settings_suggest_outlined),
            tooltip: 'App diagnostics',
            onPressed: () => context.push('/jobs/settings'),
          ),
          IconButton(
            icon: const Icon(Icons.edit_note_outlined),
            tooltip: 'Punch using job ID (fallback)',
            onPressed: () => context.push('/jobs/manual-punch'),
          ),
          IconButton(
            icon: const Icon(Icons.directions_car_outlined),
            tooltip: 'Daily vehicle check',
            onPressed: () => context.push('/jobs/vehicle-check'),
          ),
          IconButton(
            icon: const Icon(Icons.logout),
            tooltip: 'Logout',
            onPressed: () => ref.read(sessionControllerProvider.notifier).logout(),
          ),
        ],
      ),
      body: jobsAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, _) => _JobListError(
          message: err.toString(),
          onRetry: () => ref.invalidate(jobListProvider),
        ),
        data: (jobs) {
          _handleAssignmentAlerts(jobs);
          if (jobs.isEmpty) {
            return _EmptyJobs(
              onRefresh: () async {
                await ref.read(jobListProvider.notifier).refresh();
              },
            );
          }
          final persistedActiveId = ref.watch(activeJobIdProvider).value;
          final activeJob = _pickActiveJob(jobs, persistedActiveId: persistedActiveId);
          return RefreshIndicator(
            onRefresh: () async {
              await ref.read(jobListProvider.notifier).refresh();
            },
            child: ListView(
              padding: const EdgeInsets.symmetric(vertical: 8),
              children: [
                if (_alerts.isNotEmpty)
                  _AssignmentAlertsCard(
                    alerts: _alerts,
                    onOpenJob: (jobId) => context.push('/jobs/$jobId'),
                  ),
                if (activeJob != null)
                  _ActiveJobHeader(
                    job: activeJob,
                    onOpen: () => context.push('/jobs/${activeJob.id}'),
                    onOpenSync: () => context.push('/jobs/sync'),
                  ),
                ...List.generate(jobs.length, (index) {
                  final job = jobs[index];
                  return Column(
                    children: [
                      _JobRow(
                        job: job,
                        isActive: activeJob?.id == job.id,
                        onTap: () => context.push('/jobs/${job.id}'),
                      ),
                      const Divider(height: 1),
                    ],
                  );
                }),
              ],
            ),
          );
        },
      ),
    );
  }

  void _handleAssignmentAlerts(List<JobDto> jobs) {
    final snapshotKey = jobs
        .map((j) => '${j.id}:${j.assignedEngineerId ?? ''}:${j.dispatchPriority ?? -1}:${j.delayNotice ?? ''}')
        .join('|');
    if (snapshotKey == _lastSnapshotKey) return;
    _lastSnapshotKey = snapshotKey;
    Future.microtask(() async {
      final alerts = await ref.read(assignmentAlertRepositoryProvider).detectAndStore(jobs);
      if (!mounted) return;
      if (alerts.isEmpty) return;
      setState(() => _alerts = alerts);
    });
  }
}

class _AssignmentAlertsCard extends StatelessWidget {
  const _AssignmentAlertsCard({
    required this.alerts,
    required this.onOpenJob,
  });

  final List<AssignmentAlert> alerts;
  final void Function(String jobId) onOpenJob;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(8, 8, 8, 4),
      child: Card(
        color: Theme.of(context).colorScheme.tertiaryContainer,
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Assignment alerts', style: Theme.of(context).textTheme.titleSmall),
              const SizedBox(height: 8),
              ...alerts.map(
                (a) => ListTile(
                  dense: true,
                  contentPadding: EdgeInsets.zero,
                  leading: Icon(
                    a.urgent ? Icons.priority_high : Icons.notifications_active_outlined,
                    color: a.urgent ? Theme.of(context).colorScheme.error : null,
                  ),
                  title: Text(a.message),
                  subtitle: Text(a.kind),
                  trailing: TextButton(
                    onPressed: () => onOpenJob(a.jobId),
                    child: const Text('Open'),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _JobRow extends StatelessWidget {
  const _JobRow({
    required this.job,
    required this.onTap,
    required this.isActive,
  });

  final JobDto job;
  final VoidCallback onTap;
  final bool isActive;

  @override
  Widget build(BuildContext context) {
    return Consumer(
      builder: (context, ref, _) {
        final summary = ref.watch(jobOutboxSummaryProvider(job.id));
        final outbox = summary.value;
        final hasOutboxAttention = outbox != null && outbox.hasAny;
        return Container(
          color: isActive ? Theme.of(context).colorScheme.primaryContainer.withValues(alpha: 0.3) : null,
          child: ListTile(
            leading: CircleAvatar(
              child: Text(
                job.status.isNotEmpty ? job.status[0].toUpperCase() : '?',
              ),
            ),
            title: Row(
              children: [
                Expanded(
                  child: Text(
                    job.displayTitle,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
                if (isActive)
                  const Padding(
                    padding: EdgeInsets.only(left: 8),
                    child: Chip(
                      visualDensity: VisualDensity.compact,
                      label: Text('ACTIVE'),
                    ),
                  ),
              ],
            ),
            subtitle: Text(
              '${job.status} · ID ${job.id}'
              '${job.isLikelyPunchedIn ? ' · punched in' : ''}'
              '${hasOutboxAttention ? ' · sync pending' : ''}',
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
            trailing: const Icon(Icons.chevron_right),
            onTap: onTap,
          ),
        );
      },
    );
  }
}

class _ActiveJobHeader extends ConsumerWidget {
  const _ActiveJobHeader({
    required this.job,
    required this.onOpen,
    required this.onOpenSync,
  });

  final JobDto job;
  final VoidCallback onOpen;
  final VoidCallback onOpenSync;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final summary = ref.watch(jobOutboxSummaryProvider(job.id));
    final s = summary.value;
    return Padding(
      padding: const EdgeInsets.fromLTRB(8, 8, 8, 12),
      child: Card(
        color: Theme.of(context).colorScheme.secondaryContainer,
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Current active job',
                style: Theme.of(context).textTheme.titleSmall,
              ),
              const SizedBox(height: 4),
              Text(
                job.displayTitle,
                style: Theme.of(context).textTheme.bodyMedium,
              ),
              const SizedBox(height: 4),
              Text(
                '${job.status}${job.isLikelyPunchedIn ? ' · likely punched in' : ''}'
                '${s != null && s.hasAny ? ' · unsynced actions' : ''}',
                style: Theme.of(context).textTheme.bodySmall,
              ),
              const SizedBox(height: 8),
              Wrap(
                spacing: 8,
                children: [
                  FilledButton.icon(
                    onPressed: onOpen,
                    icon: const Icon(Icons.play_arrow),
                    label: const Text('Resume job'),
                  ),
                  OutlinedButton.icon(
                    onPressed: onOpenSync,
                    icon: const Icon(Icons.sync),
                    label: const Text('Sync'),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}

JobDto? _pickActiveJob(List<JobDto> jobs, {String? persistedActiveId}) {
  if (jobs.isEmpty) return null;
  JobDto? pickBy(bool Function(JobDto) predicate) {
    for (final j in jobs) {
      if (predicate(j)) return j;
    }
    return null;
  }

  return pickBy((j) => j.isOnSite) ??
      pickBy((j) => j.isEnRoute) ??
      pickBy((j) => j.isAccepted) ??
      pickBy((j) => j.isCompletionPending) ??
      pickBy((j) => persistedActiveId != null && j.id == persistedActiveId) ??
      pickBy((j) => j.isInProgressLike);
}

class _JobListError extends StatelessWidget {
  const _JobListError({
    required this.message,
    required this.onRetry,
  });

  final String message;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.error_outline, size: 48, color: Theme.of(context).colorScheme.error),
            const SizedBox(height: 16),
            Text(
              'Could not load jobs',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 8),
            Text(
              message,
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.bodySmall,
            ),
            const SizedBox(height: 24),
            FilledButton.icon(
              onPressed: onRetry,
              icon: const Icon(Icons.refresh),
              label: const Text('Retry'),
            ),
          ],
        ),
      ),
    );
  }
}

class _EmptyJobs extends StatelessWidget {
  const _EmptyJobs({required this.onRefresh});

  final Future<void> Function() onRefresh;

  @override
  Widget build(BuildContext context) {
    return RefreshIndicator(
      onRefresh: onRefresh,
      child: ListView(
        physics: const AlwaysScrollableScrollPhysics(),
        children: [
          SizedBox(
            height: MediaQuery.sizeOf(context).height * 0.5,
            child: Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(
                    Icons.work_outline,
                    size: 64,
                    color: Theme.of(context).colorScheme.outline,
                  ),
                  const SizedBox(height: 16),
                  Text(
                    'No jobs assigned',
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'Pull to refresh or check back later.',
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                          color: Theme.of(context).colorScheme.onSurfaceVariant,
                        ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
