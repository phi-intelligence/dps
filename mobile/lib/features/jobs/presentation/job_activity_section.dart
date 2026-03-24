import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/errors/action_failure_guidance.dart';
import '../../../core/sync/submission_outcome.dart';
import '../../../core/sync/sync_coordinator.dart';
import '../data/job_activity_repository.dart';

final jobActivityProvider = FutureProvider.family<List<JobActivityItemDto>, String>((ref, jobId) {
  return ref.watch(jobActivityRepositoryProvider).listJobActivity(jobId);
});

class JobActivitySection extends ConsumerStatefulWidget {
  const JobActivitySection({
    super.key,
    required this.jobId,
    this.onSubmitted,
  });

  final String jobId;
  final VoidCallback? onSubmitted;

  @override
  ConsumerState<JobActivitySection> createState() => _JobActivitySectionState();
}

class _JobActivitySectionState extends ConsumerState<JobActivitySection> {
  final _controller = TextEditingController();
  bool _submitting = false;
  String? _submitError;
  String? _submitState;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _submitNote() async {
    final text = _controller.text.trim();
    if (text.isEmpty) {
      setState(() => _submitError = 'Note cannot be empty');
      return;
    }
    setState(() {
      _submitting = true;
      _submitError = null;
      _submitState = null;
    });
    final outcome = await ref.read(syncCoordinatorProvider).submitJobNote(
          jobId: widget.jobId,
          bodyText: text,
        );
    if (!mounted) return;
    setState(() => _submitting = false);
    if (outcome.isFailed || outcome.isBlocked) {
      final msg = outcome.detailMessage ?? 'Failed to submit note';
      final hint = actionFailureGuidance(msg);
      setState(() => _submitError = hint.isEmpty ? msg : '$msg\n$hint');
      return;
    }
    _controller.clear();
    if (outcome.isQueued) {
      setState(() => _submitState = 'Note queued and will sync when online');
    } else {
      setState(() => _submitState = 'Note added');
      ref.invalidate(jobActivityProvider(widget.jobId));
      widget.onSubmitted?.call();
    }
  }

  @override
  Widget build(BuildContext context) {
    final activityAsync = ref.watch(jobActivityProvider(widget.jobId));

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Activity', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            TextField(
              controller: _controller,
              maxLines: 3,
              maxLength: 4000,
              decoration: const InputDecoration(
                labelText: 'Add engineer note',
                alignLabelWithHint: true,
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                FilledButton.icon(
                  onPressed: _submitting ? null : _submitNote,
                  icon: const Icon(Icons.note_add_outlined),
                  label: Text(_submitting ? 'Submitting…' : 'Add note'),
                ),
                const SizedBox(width: 12),
                if (_submitState != null)
                  Expanded(
                    child: Text(
                      _submitState!,
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                            color: Theme.of(context).colorScheme.primary,
                          ),
                    ),
                  ),
              ],
            ),
            if (_submitError != null) ...[
              const SizedBox(height: 8),
              Text(
                _submitError!,
                style: TextStyle(color: Theme.of(context).colorScheme.error),
              ),
            ],
            const SizedBox(height: 12),
            activityAsync.when(
              loading: () => const LinearProgressIndicator(),
              error: (e, _) => Text(
                'Failed to load activity: $e',
                style: TextStyle(color: Theme.of(context).colorScheme.error),
              ),
              data: (rows) {
                if (rows.isEmpty) {
                  return Text(
                    'No activity yet.',
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: Theme.of(context).colorScheme.onSurfaceVariant,
                        ),
                  );
                }
                return Column(
                  children: rows
                      .map(
                        (r) => ListTile(
                          contentPadding: EdgeInsets.zero,
                          leading: Icon(_activityIcon(r.activityType)),
                          title: Text(r.body),
                          subtitle: Text(
                            '${r.activityType} · ${r.source} · ${r.createdAt.toLocal()}',
                            style: Theme.of(context).textTheme.bodySmall,
                          ),
                        ),
                      )
                      .toList(),
                );
              },
            ),
          ],
        ),
      ),
    );
  }
}

IconData _activityIcon(String activityType) {
  switch (activityType) {
    case 'punch':
      return Icons.punch_clock_outlined;
    case 'form_submission':
      return Icons.fact_check_outlined;
    case 'signature_submission':
      return Icons.draw_outlined;
    case 'media_submission':
      return Icons.photo_camera_outlined;
    case 'parts_submission':
      return Icons.inventory_2_outlined;
    default:
      return Icons.notes_outlined;
  }
}
