import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../jobs/data/models/job_dto.dart';
import '../data/models/completion_requirements_dto.dart';
import '../domain/completion_readiness.dart';

/// Completion gate summary + satisfied / pending lists from the bundle + job status.
class JobCompletionReadinessSection extends StatelessWidget {
  const JobCompletionReadinessSection({
    super.key,
    required this.job,
    required this.bundleAsync,
    required this.onRetry,
  });

  final JobDto job;
  final AsyncValue<JobCompletionRequirementsBundleDto> bundleAsync;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return bundleAsync.when(
      loading: () => const Card(
        child: Padding(
          padding: EdgeInsets.all(16),
          child: Center(child: LinearProgressIndicator()),
        ),
      ),
      error: (e, _) => Card(
        color: Theme.of(context).colorScheme.errorContainer,
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Completion requirements unavailable',
                style: Theme.of(context).textTheme.titleSmall,
              ),
              const SizedBox(height: 8),
              Text('$e', style: Theme.of(context).textTheme.bodySmall),
              TextButton.icon(
                onPressed: onRetry,
                icon: const Icon(Icons.refresh, size: 18),
                label: const Text('Retry'),
              ),
            ],
          ),
        ),
      ),
      data: (bundle) {
        final policy = job.materialPolicy ?? bundle.materialPolicy;
        final result = computeCompletionReadiness(
          bundle: bundle,
          jobStatus: job.status,
          materialPolicy: policy,
        );

        return Card(
          clipBehavior: Clip.antiAlias,
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Icon(
                      Icons.fact_check_outlined,
                      color: Theme.of(context).colorScheme.primary,
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        'Completion readiness',
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                    ),
                    _ReadinessChip(
                      jobStatus: job.status,
                      requirementsAllSatisfied: result.requirementsAllSatisfied,
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Text(
                  result.summaryHeadline,
                  style: Theme.of(context).textTheme.titleSmall?.copyWith(
                        fontWeight: FontWeight.w600,
                      ),
                ),
                const SizedBox(height: 6),
                Text(
                  result.summaryDetail,
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: Theme.of(context).colorScheme.onSurfaceVariant,
                      ),
                ),
                if (result.statusBlockers.isNotEmpty) ...[
                  const SizedBox(height: 12),
                  ...result.statusBlockers.map(
                    (b) => Padding(
                      padding: const EdgeInsets.only(bottom: 6),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Icon(
                            Icons.block,
                            size: 18,
                            color: Theme.of(context).colorScheme.error,
                          ),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              b,
                              style: Theme.of(context).textTheme.bodySmall,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
                const SizedBox(height: 12),
                Text(
                  'Material policy: $policy'
                  '${policy == 'no_materials_expected' ? ' — parts rows are not part of the server completion gate.' : ''}',
                  style: Theme.of(context).textTheme.labelSmall?.copyWith(
                        color: Theme.of(context).colorScheme.onSurfaceVariant,
                      ),
                ),
                if (policy == 'no_materials_expected' &&
                    bundle.partsRequirements.isNotEmpty) ...[
                  const SizedBox(height: 8),
                  Text(
                    'Note: ${bundle.partsRequirements.length} parts requirement row(s) exist in data but are excluded from the gate for this policy (matches server logic).',
                    style: Theme.of(context).textTheme.labelSmall?.copyWith(
                          color: Theme.of(context).colorScheme.tertiary,
                        ),
                  ),
                ],
                const Divider(height: 24),
                _ItemList(
                  title: 'Satisfied (${result.satisfiedItems.length})',
                  items: result.satisfiedItems,
                  emptyLabel: 'None yet',
                  icon: Icons.check_circle_outline,
                ),
                const SizedBox(height: 12),
                _ItemList(
                  title: 'Remaining (${result.pendingItems.length})',
                  items: result.pendingItems,
                  emptyLabel: 'None — all configured rows satisfied',
                  icon: Icons.pending_outlined,
                  highlight: true,
                ),
                if (result.requirementsAllSatisfied &&
                    !const {'completed', 'closed', 'cancelled'}
                        .contains(job.status.toLowerCase())) ...[
                  const SizedBox(height: 8),
                  Text(
                    'No “Mark complete” control is shown — completion is finalized by server rules after punch and inventory checks.',
                    style: Theme.of(context).textTheme.labelSmall?.copyWith(
                          fontStyle: FontStyle.italic,
                          color: Theme.of(context).colorScheme.onSurfaceVariant,
                        ),
                  ),
                ],
              ],
            ),
          ),
        );
      },
    );
  }
}

class _ReadinessChip extends StatelessWidget {
  const _ReadinessChip({
    required this.jobStatus,
    required this.requirementsAllSatisfied,
  });

  final String jobStatus;
  final bool requirementsAllSatisfied;

  @override
  Widget build(BuildContext context) {
    final st = jobStatus.toLowerCase();
    if (st == 'completed' || st == 'closed' || st == 'cancelled') {
      return const Chip(
        label: Text('Finished'),
        avatar: Icon(Icons.flag, size: 18),
        visualDensity: VisualDensity.compact,
        materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
      );
    }
    if (requirementsAllSatisfied) {
      return const Chip(
        label: Text('Checklist OK'),
        avatar: Icon(Icons.check, size: 18),
        visualDensity: VisualDensity.compact,
        materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
      );
    }
    return const Chip(
      label: Text('Not ready'),
      avatar: Icon(Icons.hourglass_top, size: 18),
      visualDensity: VisualDensity.compact,
      materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
    );
  }
}

class _ItemList extends StatelessWidget {
  const _ItemList({
    required this.title,
    required this.items,
    required this.emptyLabel,
    required this.icon,
    this.highlight = false,
  });

  final String title;
  final List<CompletionLineItem> items;
  final String emptyLabel;
  final IconData icon;
  final bool highlight;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: Theme.of(context).textTheme.labelLarge,
        ),
        const SizedBox(height: 4),
        if (items.isEmpty)
          Text(
            emptyLabel,
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: Theme.of(context).colorScheme.onSurfaceVariant,
                ),
          )
        else
          ...items.map(
            (it) => ListTile(
              dense: true,
              contentPadding: EdgeInsets.zero,
              leading: Icon(
                icon,
                size: 20,
                color: highlight && !it.isSatisfied
                    ? Theme.of(context).colorScheme.error
                    : Theme.of(context).colorScheme.outline,
              ),
              title: Text('${it.category}: ${it.label}'),
              subtitle: Text(it.detail),
            ),
          ),
      ],
    );
  }
}
