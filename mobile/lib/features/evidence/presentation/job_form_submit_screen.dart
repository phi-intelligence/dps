import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/errors/action_failure_guidance.dart';
import '../../../core/sync/submission_outcome.dart';
import '../../../core/sync/sync_coordinator.dart';

/// Submit `POST /jobs/{id}/forms/{form_key}/submit` with dynamic `data` map.
///
/// Keys come from `required_keys_json` on the requirement; values are sent as strings.
class JobFormSubmitScreen extends ConsumerStatefulWidget {
  const JobFormSubmitScreen({
    super.key,
    required this.jobId,
    required this.formKey,
    required this.requiredKeys,
  });

  final String jobId;
  final String formKey;
  final List<String> requiredKeys;

  @override
  ConsumerState<JobFormSubmitScreen> createState() =>
      _JobFormSubmitScreenState();
}

class _JobFormSubmitScreenState extends ConsumerState<JobFormSubmitScreen> {
  final _controllers = <String, TextEditingController>{};
  bool _busy = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    for (final k in widget.requiredKeys) {
      _controllers[k] = TextEditingController();
    }
  }

  @override
  void dispose() {
    for (final c in _controllers.values) {
      c.dispose();
    }
    super.dispose();
  }

  Future<void> _submit() async {
    setState(() {
      _busy = true;
      _error = null;
    });
    final data = <String, Object>{};
    for (final e in _controllers.entries) {
      data[e.key] = e.value.text.trim();
    }
    final outcome = await ref.read(syncCoordinatorProvider).submitForm(
          jobId: widget.jobId,
          formKey: widget.formKey,
          data: data,
        );
    if (!mounted) return;
    setState(() => _busy = false);
    if (outcome.isFailed || outcome.isBlocked) {
      final msg = outcome.detailMessage ?? 'Failed';
      final hint = actionFailureGuidance(msg);
      setState(() => _error = hint.isEmpty ? msg : '$msg\n$hint');
      return;
    }
    Navigator.of(context).pop(outcome);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Form: ${widget.formKey}'),
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text(
            'Submit all required fields. The server validates keys against dispatch configuration.',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: Theme.of(context).colorScheme.onSurfaceVariant,
                ),
          ),
          const SizedBox(height: 16),
          if (_controllers.isEmpty)
            Text(
              'No required keys — submit sends an empty `data` object.',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: Theme.of(context).colorScheme.onSurfaceVariant,
                  ),
            )
          else
            ..._controllers.entries.map(
              (e) => Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: TextField(
                  controller: e.value,
                  decoration: InputDecoration(
                    labelText: e.key,
                    border: const OutlineInputBorder(),
                  ),
                  maxLines: e.key.toLowerCase().contains('note') ? 4 : 1,
                ),
              ),
            ),
          if (_error != null)
            Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: Text(
                _error!,
                style: TextStyle(color: Theme.of(context).colorScheme.error),
              ),
            ),
          FilledButton(
            onPressed: _busy ? null : _submit,
            child: Text(_busy ? 'Submitting…' : 'Submit'),
          ),
        ],
      ),
    );
  }
}
