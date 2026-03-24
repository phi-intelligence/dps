import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';

import '../../../core/errors/action_failure_guidance.dart';
import '../../../core/sync/submission_outcome.dart';
import '../../../core/sync/sync_coordinator.dart';
import '../data/media_upload_planner.dart';

/// Submit photos via `POST /jobs/{id}/media` with JSON payloads (base64), not multipart.
///
/// Wave 5: offline submission is blocked (see [SyncCoordinator.submitMedia]).
class JobMediaSubmitScreen extends ConsumerStatefulWidget {
  const JobMediaSubmitScreen({
    super.key,
    required this.jobId,
    required this.minPhotos,
  });

  final String jobId;
  final int minPhotos;

  @override
  ConsumerState<JobMediaSubmitScreen> createState() =>
      _JobMediaSubmitScreenState();
}

class _JobMediaSubmitScreenState extends ConsumerState<JobMediaSubmitScreen> {
  final _picker = ImagePicker();
  final List<_PendingPhoto> _pending = [];
  bool _busy = false;
  String? _error;
  String? _state;
  int _batchProgress = 0;
  int _batchTotal = 0;
  static const int _maxMediaJsonBytes = 2 * 1024 * 1024;
  static const int _targetBatchJsonBytes = 1800000;
  int _imageQuality = 75;
  int _maxDimension = 1600;

  Future<void> _pick() async {
    setState(() => _error = null);
    try {
      final files = await _picker.pickMultiImage(
        maxWidth: _maxDimension.toDouble(),
        maxHeight: _maxDimension.toDouble(),
        imageQuality: _imageQuality,
      );
      if (files.isEmpty) return;
      for (final x in files) {
        final bytes = await x.readAsBytes();
        _pending.add(
          _PendingPhoto(
            name: x.name,
            base64: base64Encode(bytes),
          ),
        );
      }
      setState(() {});
    } catch (e) {
      setState(() => _error = e.toString());
    }
  }

  void _remove(int i) {
    setState(() {
      _pending.removeAt(i);
    });
  }

  Future<void> _submit() async {
    if (_pending.isEmpty) {
      setState(() => _error = 'Add at least one photo');
      return;
    }
    setState(() {
      _busy = true;
      _error = null;
        _state = null;
        _batchProgress = 0;
        _batchTotal = 0;
    });
    final payloads = _pending
        .map(
          (p) => <String, Object>{
            'filename': p.name,
            'content_base64': p.base64,
            'mime_type': 'image/jpeg',
          },
        )
        .toList();
    try {
      final plan = planMediaBatches(
        payloads: payloads,
        hardLimitBytes: _maxMediaJsonBytes,
        targetLimitBytes: _targetBatchJsonBytes,
      );
      setState(() => _batchTotal = plan.batches.length);

      for (var i = 0; i < plan.batches.length; i++) {
        final batch = plan.batches[i];
        if (!mounted) return;
        setState(() {
          _batchProgress = i + 1;
          _state = 'Uploading batch ${i + 1}/${plan.batches.length} '
              '(${batch.payloads.length} photo${batch.payloads.length == 1 ? '' : 's'})...';
        });
        final outcome = await ref.read(syncCoordinatorProvider).submitMedia(
              jobId: widget.jobId,
              payloads: batch.payloads,
            );
        if (!mounted) return;
        if (outcome.isFailed || outcome.isBlocked) {
          final msg = outcome.detailMessage ?? 'Failed';
          final hint = actionFailureGuidance(msg);
          setState(() {
            _busy = false;
            _error = hint.isEmpty ? msg : '$msg\n$hint';
          });
          return;
        }
      }
    } on StateError catch (e) {
      if (!mounted) return;
      setState(() {
        _busy = false;
        _error = '${e.message} Reduce quality or retake closer shots.';
      });
      return;
    }
    if (!mounted) return;
    setState(() => _busy = false);
    Navigator.of(context).pop(SubmissionOutcome.synced);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Site photos')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text(
            'Requirement: at least ${widget.minPhotos} photo(s). '
            'Images are sent as JSON base64 (server stores `payload_json` per row). '
            'Offline photo queue is disabled (see sync policy). '
            'For reliability, photos are auto-submitted in smaller batches.',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: Theme.of(context).colorScheme.onSurfaceVariant,
                ),
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              FilledButton.icon(
                onPressed: _busy ? null : _pick,
                icon: const Icon(Icons.add_photo_alternate_outlined),
                label: const Text('Add photos'),
              ),
              const SizedBox(width: 12),
              if (_pending.isNotEmpty)
                Text('${_pending.length} selected', style: Theme.of(context).textTheme.titleSmall),
            ],
          ),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8,
            children: [
              ChoiceChip(
                label: const Text('High'),
                selected: _imageQuality == 85,
                onSelected: _busy
                    ? null
                    : (_) => setState(() {
                          _imageQuality = 85;
                          _maxDimension = 1920;
                        }),
              ),
              ChoiceChip(
                label: const Text('Balanced'),
                selected: _imageQuality == 75,
                onSelected: _busy
                    ? null
                    : (_) => setState(() {
                          _imageQuality = 75;
                          _maxDimension = 1600;
                        }),
              ),
              ChoiceChip(
                label: const Text('Small data'),
                selected: _imageQuality == 60,
                onSelected: _busy
                    ? null
                    : (_) => setState(() {
                          _imageQuality = 60;
                          _maxDimension = 1280;
                        }),
              ),
            ],
          ),
          if (_pending.isNotEmpty) ...[
            const SizedBox(height: 8),
            Builder(
              builder: (context) {
                final payloads = _pending
                    .map(
                      (p) => <String, Object>{
                        'filename': p.name,
                        'content_base64': p.base64,
                        'mime_type': 'image/jpeg',
                      },
                    )
                    .toList();
                final approxJsonBytes = utf8.encode(
                  jsonEncode(<String, Object>{'media_type': 'photo', 'payloads': payloads}),
                ).length;
                final over = approxJsonBytes > _maxMediaJsonBytes;
                final plan = over
                    ? null
                    : planMediaBatches(
                        payloads: payloads,
                        hardLimitBytes: _maxMediaJsonBytes,
                        targetLimitBytes: _targetBatchJsonBytes,
                      );
                return Text(
                  'Approx request size: $approxJsonBytes bytes (hard limit $_maxMediaJsonBytes)'
                  '${plan == null ? '' : ' · planned batches: ${plan.batches.length}'}',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: over
                            ? Theme.of(context).colorScheme.error
                            : Theme.of(context).colorScheme.onSurfaceVariant,
                      ),
                );
              },
            ),
          ],
          const SizedBox(height: 12),
          ...List.generate(
            _pending.length,
            (i) => ListTile(
              leading: const Icon(Icons.image_outlined),
              title: Text(_pending[i].name),
              subtitle: Text(
                '~${(_pending[i].base64.length * 3 / 4).round()} bytes decoded (approx)',
              ),
              trailing: IconButton(
                icon: const Icon(Icons.delete_outline),
                onPressed: _busy ? null : () => _remove(i),
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
          if (_state != null)
            Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: Text(
                _state!,
                style: TextStyle(color: Theme.of(context).colorScheme.primary),
              ),
            ),
          if (_busy && _batchTotal > 0)
            Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: LinearProgressIndicator(value: _batchProgress / _batchTotal),
            ),
          FilledButton(
            onPressed: _busy ? null : _submit,
            child: Text(_busy ? 'Uploading in batches…' : 'Submit photos'),
          ),
        ],
      ),
    );
  }
}

class _PendingPhoto {
  _PendingPhoto({required this.name, required this.base64});

  final String name;
  final String base64;
}
