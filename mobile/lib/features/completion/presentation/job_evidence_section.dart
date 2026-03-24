import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/sync/submission_outcome.dart';
import '../../evidence/presentation/job_form_submit_screen.dart';
import '../../evidence/presentation/job_media_submit_screen.dart';
import '../../evidence/presentation/job_parts_submit_screen.dart';
import '../../evidence/presentation/job_signature_screen.dart';
import '../data/models/completion_requirements_dto.dart';

/// Evidence submission entry points from job detail (Wave 4).
///
/// **Backend-aligned:** `POST` forms, signature, media, parts-usage on `/jobs/{id}/…`.
/// **Not implemented:** certificate upload in engineer app.
///
/// **Media caveat:** `POST /jobs/{id}/media` accepts JSON payloads (e.g. base64), not multipart.
/// Large photos can hit body-size limits — keep compression; offline queue is future work.
///
/// **Parts caveat:** `reconcile_parts_usage_submission` requires SKUs that exist in inventory;
/// unknown SKU → HTTP 400.
///
/// **Refresh:** Callers should pass [onEvidenceSubmitted] to invalidate/refetch job + completion
/// bundle (typically shared `_refreshJob` that invalidates completion provider + fetches job).
class JobEvidenceSection extends StatelessWidget {
  const JobEvidenceSection({
    super.key,
    required this.jobId,
    required this.bundleAsync,
    required this.materialPolicy,
    required this.onEvidenceSubmitted,
  });

  final String jobId;
  final AsyncValue<JobCompletionRequirementsBundleDto> bundleAsync;
  final String materialPolicy;
  final Future<void> Function() onEvidenceSubmitted;

  Future<void> _onSubmissionRouteResult(
    BuildContext context,
    SubmissionOutcome? outcome,
  ) async {
    if (outcome == null) return;
    if (!context.mounted) return;
    if (outcome.isFailed || outcome.isBlocked) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(outcome.detailMessage ?? 'Could not submit')),
      );
      return;
    }
    if (outcome.isSynced) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Evidence submitted')),
      );
      await onEvidenceSubmitted();
    } else if (outcome.isQueued) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Saved offline — will sync when online')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Work evidence & compliance',
          style: Theme.of(context).textTheme.titleMedium,
        ),
        const SizedBox(height: 8),
        bundleAsync.when(
          loading: () => const Card(
            child: Padding(
              padding: EdgeInsets.all(16),
              child: Text('Loading requirement details…'),
            ),
          ),
          error: (e, _) => Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Text(
                'Could not load sections: $e',
                style: TextStyle(color: Theme.of(context).colorScheme.error),
              ),
            ),
          ),
          data: (bundle) => Column(
            children: [
              _NotesCard(),
              const SizedBox(height: 12),
              _FormsSection(
                jobId: jobId,
                bundle: bundle,
                onOpenSubmit: (formKey, keys) async {
                  final outcome = await Navigator.of(context).push<SubmissionOutcome>(
                    MaterialPageRoute<SubmissionOutcome>(
                      builder: (ctx) => JobFormSubmitScreen(
                        jobId: jobId,
                        formKey: formKey,
                        requiredKeys: keys,
                      ),
                    ),
                  );
                  if (!context.mounted) return;
                  await _onSubmissionRouteResult(context, outcome);
                },
              ),
              const SizedBox(height: 12),
              _MediaSection(
                jobId: jobId,
                bundle: bundle,
                onOpenSubmit: (minPhotos) async {
                  final outcome = await Navigator.of(context).push<SubmissionOutcome>(
                    MaterialPageRoute<SubmissionOutcome>(
                      builder: (ctx) => JobMediaSubmitScreen(
                        jobId: jobId,
                        minPhotos: minPhotos,
                      ),
                    ),
                  );
                  if (!context.mounted) return;
                  await _onSubmissionRouteResult(context, outcome);
                },
              ),
              const SizedBox(height: 12),
              _SignatureSection(
                jobId: jobId,
                bundle: bundle,
                onOpenCapture: () async {
                  final outcome = await Navigator.of(context).push<SubmissionOutcome>(
                    MaterialPageRoute<SubmissionOutcome>(
                      builder: (ctx) => JobSignatureScreen(
                        jobId: jobId,
                      ),
                    ),
                  );
                  if (!context.mounted) return;
                  await _onSubmissionRouteResult(context, outcome);
                },
              ),
              const SizedBox(height: 12),
              _PartsSection(
                jobId: jobId,
                bundle: bundle,
                materialPolicy: materialPolicy,
                onOpenSubmit: (minLines) async {
                  final outcome = await Navigator.of(context).push<SubmissionOutcome>(
                    MaterialPageRoute<SubmissionOutcome>(
                      builder: (ctx) => JobPartsSubmitScreen(
                        jobId: jobId,
                        minLineItems: minLines,
                      ),
                    ),
                  );
                  if (!context.mounted) return;
                  await _onSubmissionRouteResult(context, outcome);
                },
              ),
              const SizedBox(height: 12),
              const _CertificateSection(),
            ],
          ),
        ),
      ],
    );
  }
}

class _NotesCard extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.note_alt_outlined, color: Theme.of(context).colorScheme.primary),
                const SizedBox(width: 8),
                Text(
                  'Engineer notes',
                  style: Theme.of(context).textTheme.titleSmall,
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              'Engineer notes are available in the job Activity section. '
              'Use that section to add and review notes.',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: Theme.of(context).colorScheme.onSurfaceVariant,
                  ),
            ),
            const SizedBox(height: 12),
            TextField(
              maxLines: 3,
              enabled: false,
              decoration: InputDecoration(
                border: const OutlineInputBorder(),
                hintText: 'Open Activity on job detail to add notes',
                hintStyle: TextStyle(
                  color: Theme.of(context).colorScheme.outline,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _FormsSection extends StatelessWidget {
  const _FormsSection({
    required this.jobId,
    required this.bundle,
    required this.onOpenSubmit,
  });

  final String jobId;
  final JobCompletionRequirementsBundleDto bundle;
  final Future<void> Function(String formKey, List<String> requiredKeys) onOpenSubmit;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.assignment_outlined, color: Theme.of(context).colorScheme.primary),
                const SizedBox(width: 8),
                Text(
                  'Forms & checklists',
                  style: Theme.of(context).textTheme.titleSmall,
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              'Submit via `POST /jobs/$jobId/forms/{{form_key}}/submit` with a `data` object.',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: Theme.of(context).colorScheme.onSurfaceVariant,
                  ),
            ),
            const SizedBox(height: 8),
            if (bundle.formRequirements.isEmpty)
              Text(
                'No form requirements configured for this job.',
                style: Theme.of(context).textTheme.bodySmall,
              )
            else
              ...bundle.formRequirements.map(
                (f) => Padding(
                  padding: const EdgeInsets.only(bottom: 12),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Icon(
                        f.isSatisfied ? Icons.check_circle : Icons.radio_button_unchecked,
                        color: f.isSatisfied
                            ? Theme.of(context).colorScheme.primary
                            : Theme.of(context).colorScheme.outline,
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Form: ${f.formKey}',
                              style: Theme.of(context).textTheme.titleSmall,
                            ),
                            const SizedBox(height: 4),
                            Text(
                              f.isSatisfied
                                  ? 'Satisfied'
                                  : (f.requiredKeys.isEmpty
                                      ? 'Pending — submit empty data if allowed'
                                      : 'Pending — keys: ${f.requiredKeys.join(', ')}'),
                              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                    color: Theme.of(context).colorScheme.onSurfaceVariant,
                                  ),
                            ),
                            if (!f.isSatisfied) ...[
                              const SizedBox(height: 8),
                              Align(
                                alignment: Alignment.centerLeft,
                                child: FilledButton(
                                  onPressed: () => onOpenSubmit(f.formKey, f.requiredKeys),
                                  child: const Text('Submit'),
                                ),
                              ),
                            ],
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

class _MediaSection extends StatelessWidget {
  const _MediaSection({
    required this.jobId,
    required this.bundle,
    required this.onOpenSubmit,
  });

  final String jobId;
  final JobCompletionRequirementsBundleDto bundle;
  final Future<void> Function(int minPhotos) onOpenSubmit;

  @override
  Widget build(BuildContext context) {
    final pending = bundle.mediaRequirements.where((m) => !m.isSatisfied).toList();
    final minPhotos = pending.isEmpty
        ? 1
        : math.max(
            1,
            pending.map((m) => m.requiredPhotoCount).reduce(math.max),
          );

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.photo_camera_outlined, color: Theme.of(context).colorScheme.primary),
                const SizedBox(width: 8),
                Text(
                  'Photos / media',
                  style: Theme.of(context).textTheme.titleSmall,
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              'Upload via `POST /jobs/$jobId/media` with JSON payloads (base64), not multipart. '
              'The server counts total photo rows to satisfy the requirement.',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: Theme.of(context).colorScheme.onSurfaceVariant,
                  ),
            ),
            const SizedBox(height: 8),
            if (bundle.mediaRequirements.isEmpty)
              Text(
                'No media requirements configured.',
                style: Theme.of(context).textTheme.bodySmall,
              )
            else ...[
              ...bundle.mediaRequirements.map(
                (m) => ListTile(
                  contentPadding: EdgeInsets.zero,
                  dense: true,
                  leading: Icon(
                    m.isSatisfied ? Icons.check_circle : Icons.photo_outlined,
                    color: m.isSatisfied
                        ? Theme.of(context).colorScheme.primary
                        : Theme.of(context).colorScheme.outline,
                  ),
                  title: Text('${m.requiredPhotoCount} photo(s) required (cumulative)'),
                  subtitle: Text(m.isSatisfied ? 'Satisfied' : 'Pending'),
                ),
              ),
              if (pending.isNotEmpty)
                Align(
                  alignment: Alignment.centerLeft,
                  child: FilledButton.icon(
                    onPressed: () => onOpenSubmit(minPhotos),
                    icon: const Icon(Icons.upload_outlined),
                    label: const Text('Add / submit photos'),
                  ),
                ),
            ],
          ],
        ),
      ),
    );
  }
}

class _SignatureSection extends StatelessWidget {
  const _SignatureSection({
    required this.jobId,
    required this.bundle,
    required this.onOpenCapture,
  });

  final String jobId;
  final JobCompletionRequirementsBundleDto bundle;
  final Future<void> Function() onOpenCapture;

  @override
  Widget build(BuildContext context) {
    final pending = bundle.signatureRequirements.where((s) => !s.isSatisfied).toList();

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.draw_outlined, color: Theme.of(context).colorScheme.primary),
                const SizedBox(width: 8),
                Text(
                  'Signature',
                  style: Theme.of(context).textTheme.titleSmall,
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              'Capture via `POST /jobs/$jobId/signature` with a JSON `signature` object (PNG base64 here).',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: Theme.of(context).colorScheme.onSurfaceVariant,
                  ),
            ),
            const SizedBox(height: 8),
            if (bundle.signatureRequirements.isEmpty)
              Text(
                'No signature requirement configured.',
                style: Theme.of(context).textTheme.bodySmall,
              )
            else ...[
              ...bundle.signatureRequirements.map(
                (s) => ListTile(
                  contentPadding: EdgeInsets.zero,
                  dense: true,
                  leading: Icon(
                    s.isSatisfied ? Icons.check_circle : Icons.gesture_outlined,
                    color: s.isSatisfied
                        ? Theme.of(context).colorScheme.primary
                        : Theme.of(context).colorScheme.outline,
                  ),
                  title: const Text('Signature required'),
                  subtitle: Text(s.isSatisfied ? 'Satisfied' : 'Pending'),
                ),
              ),
              if (pending.isNotEmpty)
                Align(
                  alignment: Alignment.centerLeft,
                  child: FilledButton.icon(
                    onPressed: () => onOpenCapture(),
                    icon: const Icon(Icons.draw),
                    label: const Text('Capture signature'),
                  ),
                ),
            ],
          ],
        ),
      ),
    );
  }
}

class _PartsSection extends StatelessWidget {
  const _PartsSection({
    required this.jobId,
    required this.bundle,
    required this.materialPolicy,
    required this.onOpenSubmit,
  });

  final String jobId;
  final JobCompletionRequirementsBundleDto bundle;
  final String materialPolicy;
  final Future<void> Function(int minLineItems) onOpenSubmit;

  @override
  Widget build(BuildContext context) {
    final excludedFromGate =
        materialPolicy == 'no_materials_expected' && bundle.partsRequirements.isNotEmpty;
    final pending = bundle.partsRequirements.where((p) => !p.isSatisfied).toList();
    final minLines = pending.isEmpty
        ? 1
        : math.max(
            1,
            pending.map((p) => p.requiredPartsItemsCount).reduce(math.max),
          );
    final canSubmitParts = pending.isNotEmpty && materialPolicy != 'no_materials_expected';

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.inventory_2_outlined, color: Theme.of(context).colorScheme.primary),
                const SizedBox(width: 8),
                Text(
                  'Parts usage',
                  style: Theme.of(context).textTheme.titleSmall,
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              'Submit via `POST /jobs/$jobId/parts-usage`. SKUs must exist in inventory.',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: Theme.of(context).colorScheme.onSurfaceVariant,
                  ),
            ),
            if (excludedFromGate) ...[
              const SizedBox(height: 8),
              Text(
                'Material policy excludes parts from the completion gate; rows shown for reference only.',
                style: Theme.of(context).textTheme.labelSmall?.copyWith(
                      color: Theme.of(context).colorScheme.tertiary,
                    ),
              ),
            ],
            const SizedBox(height: 8),
            if (bundle.partsRequirements.isEmpty)
              Text(
                'No parts usage requirements configured.',
                style: Theme.of(context).textTheme.bodySmall,
              )
            else ...[
              ...bundle.partsRequirements.map(
                (p) => ListTile(
                  contentPadding: EdgeInsets.zero,
                  dense: true,
                  leading: Icon(
                    p.isSatisfied ? Icons.check_circle : Icons.build_outlined,
                    color: p.isSatisfied
                        ? Theme.of(context).colorScheme.primary
                        : Theme.of(context).colorScheme.outline,
                  ),
                  title: Text('${p.requiredPartsItemsCount} line item(s) required (cumulative)'),
                  subtitle: Text(p.isSatisfied ? 'Satisfied' : 'Pending'),
                ),
              ),
              if (pending.isNotEmpty && canSubmitParts)
                Align(
                  alignment: Alignment.centerLeft,
                  child: FilledButton.icon(
                    onPressed: () => onOpenSubmit(minLines),
                    icon: const Icon(Icons.playlist_add_outlined),
                    label: const Text('Submit parts usage'),
                  ),
                ),
            ],
          ],
        ),
      ),
    );
  }
}

class _CertificateSection extends StatelessWidget {
  const _CertificateSection();

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.verified_outlined, color: Theme.of(context).colorScheme.outline),
                const SizedBox(width: 8),
                Text(
                  'Certificates / compliance',
                  style: Theme.of(context).textTheme.titleSmall,
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              'Certificate list/generate endpoints are Admin/Dispatcher only. '
              'No engineer-safe read/upload in the current API — mobile stays read-only here.',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: Theme.of(context).colorScheme.onSurfaceVariant,
                  ),
            ),
          ],
        ),
      ),
    );
  }
}
