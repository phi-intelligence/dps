import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:signature/signature.dart';

import '../../../core/errors/action_failure_guidance.dart';
import '../../../core/sync/submission_outcome.dart';
import '../../../core/sync/sync_coordinator.dart';

/// `POST /jobs/{id}/signature` with PNG bytes as base64 in JSON payload.
class JobSignatureScreen extends ConsumerStatefulWidget {
  const JobSignatureScreen({
    super.key,
    required this.jobId,
  });

  final String jobId;

  @override
  ConsumerState<JobSignatureScreen> createState() => _JobSignatureScreenState();
}

class _JobSignatureScreenState extends ConsumerState<JobSignatureScreen> {
  late final SignatureController _controller;
  bool _busy = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _controller = SignatureController(
      penStrokeWidth: 2,
      penColor: Colors.black,
      exportBackgroundColor: Colors.white,
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (_controller.isEmpty) {
      setState(() => _error = 'Draw a signature first');
      return;
    }
    setState(() {
      _busy = true;
      _error = null;
    });
    final bytes = await _controller.toPngBytes();
    if (bytes == null || bytes.isEmpty) {
      if (mounted) {
        setState(() {
          _busy = false;
          _error = 'Could not export signature';
        });
      }
      return;
    }
    final payload = <String, Object>{
      'encoding': 'png_base64',
      'data': base64Encode(bytes),
      'captured_at': DateTime.now().toUtc().toIso8601String(),
    };
    final outcome = await ref.read(syncCoordinatorProvider).submitSignature(
          jobId: widget.jobId,
          signature: payload,
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
      appBar: AppBar(title: const Text('Signature')),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(16),
            child: Text(
              'Sign in the box. Data is sent as JSON (base64 PNG), not multipart.',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: Theme.of(context).colorScheme.onSurfaceVariant,
                  ),
            ),
          ),
          Expanded(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: DecoratedBox(
                decoration: BoxDecoration(
                  border: Border.all(color: Theme.of(context).colorScheme.outline),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Signature(
                  controller: _controller,
                  backgroundColor: Colors.white,
                ),
              ),
            ),
          ),
          if (_error != null)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: Text(
                _error!,
                style: TextStyle(color: Theme.of(context).colorScheme.error),
              ),
            ),
          Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                OutlinedButton(
                  onPressed: _busy
                      ? null
                      : () {
                          _controller.clear();
                          setState(() => _error = null);
                        },
                  child: const Text('Clear'),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: FilledButton(
                    onPressed: _busy ? null : _submit,
                    child: Text(_busy ? 'Submitting…' : 'Submit signature'),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
