import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/models/completion_requirements_dto.dart';

/// Structured areas for evidence/compliance work — mostly informational until Wave 4+.
///
/// **Wired today:** requirement rows mirror `GET .../completion-requirements`.
/// **Not wired:** form submit, media upload, signature capture, certificates (role/API).
class JobEvidencePlaceholders extends StatelessWidget {
  const JobEvidencePlaceholders({
    super.key,
    required this.bundleAsync,
    required this.materialPolicy,
  });

  final AsyncValue<JobCompletionRequirementsBundleDto> bundleAsync;
  final String materialPolicy;

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
              _FormsSection(bundle: bundle),
              const SizedBox(height: 12),
              _MediaSection(bundle: bundle),
              const SizedBox(height: 12),
              _SignatureSection(bundle: bundle),
              const SizedBox(height: 12),
              _PartsSection(bundle: bundle, materialPolicy: materialPolicy),
              const SizedBox(height: 12),
              _CertificateSection(),
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
              'There is no engineer-safe `POST /jobs/{id}/notes` (or similar) in the current '
              'API. Saving notes from mobile requires a backend change.',
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
                hintText: 'Notes will be available after backend support',
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
  const _FormsSection({required this.bundle});

  final JobCompletionRequirementsBundleDto bundle;

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
              'Submitting forms uses `POST /jobs/{id}/forms/{form_key}/submit` — not yet implemented in this app.',
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
                (f) => ListTile(
                  contentPadding: EdgeInsets.zero,
                  dense: true,
                  leading: Icon(
                    f.isSatisfied ? Icons.check_circle : Icons.radio_button_unchecked,
                    color: f.isSatisfied
                        ? Theme.of(context).colorScheme.primary
                        : Theme.of(context).colorScheme.outline,
                  ),
                  title: Text('Form: ${f.formKey}'),
                  subtitle: Text(
                    f.isSatisfied
                        ? 'Satisfied'
                        : 'Pending — ${f.requiredKeys.isEmpty ? 'no keys required' : 'keys: ${f.requiredKeys.join(', ')}'}',
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
  const _MediaSection({required this.bundle});

  final JobCompletionRequirementsBundleDto bundle;

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
              'Upload uses `POST /jobs/{id}/media` — mobile pipeline not implemented yet.',
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
            else
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
                  title: Text('${m.requiredPhotoCount} photo(s) required'),
                  subtitle: Text(m.isSatisfied ? 'Satisfied' : 'Pending'),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

class _SignatureSection extends StatelessWidget {
  const _SignatureSection({required this.bundle});

  final JobCompletionRequirementsBundleDto bundle;

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
              'Capture uses `POST /jobs/{id}/signature` — mobile UI not implemented yet.',
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
            else
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
          ],
        ),
      ),
    );
  }
}

class _PartsSection extends StatelessWidget {
  const _PartsSection({
    required this.bundle,
    required this.materialPolicy,
  });

  final JobCompletionRequirementsBundleDto bundle;
  final String materialPolicy;

  @override
  Widget build(BuildContext context) {
    final excludedFromGate =
        materialPolicy == 'no_materials_expected' && bundle.partsRequirements.isNotEmpty;

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
              'Submission uses `POST /jobs/{id}/parts-usage` — mobile entry not implemented yet.',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: Theme.of(context).colorScheme.onSurfaceVariant,
                  ),
            ),
            if (excludedFromGate) ...[
              const SizedBox(height: 8),
              Text(
                'Material policy excludes parts from the completion gate; parts rows may still exist for reference.',
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
            else
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
                  title: Text('${p.requiredPartsItemsCount} line item(s) required'),
                  subtitle: Text(p.isSatisfied ? 'Satisfied' : 'Pending'),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

class _CertificateSection extends StatelessWidget {
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
              'Certificate list/generate endpoints are `Admin`/`Dispatcher` only in the current API. '
              'Engineers cannot load certificates from mobile until the backend exposes an engineer-safe read.',
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
