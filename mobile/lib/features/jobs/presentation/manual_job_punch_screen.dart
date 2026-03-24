import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:geolocator/geolocator.dart';
import 'package:go_router/go_router.dart';

import '../../../core/errors/api_exception.dart';
import '../../../core/sync/submission_outcome.dart';
import '../../../core/sync/sync_coordinator.dart';

/// Fallback when you cannot open a job from the list (e.g. support / edge case).
class ManualJobPunchScreen extends ConsumerStatefulWidget {
  const ManualJobPunchScreen({super.key});

  @override
  ConsumerState<ManualJobPunchScreen> createState() =>
      _ManualJobPunchScreenState();
}

class _ManualJobPunchScreenState extends ConsumerState<ManualJobPunchScreen> {
  final _jobId = TextEditingController();
  final _lat = TextEditingController(text: '51.5074');
  final _lon = TextEditingController(text: '-0.1278');

  bool _busy = false;
  bool _locationBusy = false;
  String? _status;

  @override
  void initState() {
    super.initState();
    _jobId.addListener(() => setState(() {}));
  }

  @override
  void dispose() {
    _jobId.dispose();
    _lat.dispose();
    _lon.dispose();
    super.dispose();
  }

  Future<void> _useCurrentLocation() async {
    setState(() {
      _locationBusy = true;
      _status = null;
    });
    try {
      var permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
      }
      if (permission == LocationPermission.deniedForever ||
          permission == LocationPermission.denied) {
        setState(() => _status = 'Location permission denied');
        return;
      }
      final pos = await Geolocator.getCurrentPosition(
        locationSettings:
            const LocationSettings(accuracy: LocationAccuracy.high),
      );
      _lat.text = pos.latitude.toString();
      _lon.text = pos.longitude.toString();
      setState(() => _status = 'Location updated');
    } catch (e) {
      setState(() => _status = e.toString());
    } finally {
      setState(() => _locationBusy = false);
    }
  }

  Future<void> _punch(String kind) async {
    setState(() {
      _busy = true;
      _status = null;
    });
    try {
      unawaited(
        ref.read(syncCoordinatorProvider).submitTelemetryBestEffort(
              latitude: double.tryParse(_lat.text.trim()) ?? 0.0,
              longitude: double.tryParse(_lon.text.trim()) ?? 0.0,
              occurredAtIsoUtc: DateTime.now().toUtc().toIso8601String(),
            ),
      );
      final outcome = await ref.read(syncCoordinatorProvider).submitPunch(
            kind: kind,
            jobId: _jobId.text.trim(),
            latitude: double.tryParse(_lat.text.trim()) ?? 0.0,
            longitude: double.tryParse(_lon.text.trim()) ?? 0.0,
          );
      if (outcome.isSynced) {
        setState(() => _status = '$kind OK (synced)');
      } else if (outcome.isQueued) {
        setState(() => _status = '$kind queued — will sync when online');
      } else {
        setState(() => _status = outcome.detailMessage ?? 'Failed');
      }
    } on ApiException catch (e) {
      setState(() => _status = e.message);
    } catch (e) {
      setState(() => _status = e.toString());
    } finally {
      setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Manual job ID punch'),
        leading: IconButton(
          icon: const Icon(Icons.close),
          onPressed: () => context.pop(),
        ),
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Card(
            color: Theme.of(context).colorScheme.surfaceContainerHighest,
            child: const Padding(
              padding: EdgeInsets.all(12),
              child: Text(
                'Use this only when you cannot select a job from My jobs. '
                'Prefer opening the job and punching from the job screen.',
              ),
            ),
          ),
          const SizedBox(height: 16),
          TextField(
            controller: _jobId,
            decoration: const InputDecoration(
              labelText: 'Job ID',
              border: OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _lat,
                  decoration: const InputDecoration(
                    labelText: 'Latitude',
                    border: OutlineInputBorder(),
                  ),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: TextField(
                  controller: _lon,
                  decoration: const InputDecoration(
                    labelText: 'Longitude',
                    border: OutlineInputBorder(),
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          OutlinedButton.icon(
            onPressed: _locationBusy ? null : _useCurrentLocation,
            icon: _locationBusy
                ? const SizedBox(
                    width: 16,
                    height: 16,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.my_location, size: 18),
            label: Text(_locationBusy ? 'Getting location…' : 'Use current location'),
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(
                child: FilledButton(
                  onPressed: (_busy || _jobId.text.trim().isEmpty)
                      ? null
                      : () => _punch('in'),
                  child: const Text('Punch in'),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: FilledButton.tonal(
                  onPressed: (_busy || _jobId.text.trim().isEmpty)
                      ? null
                      : () => _punch('out'),
                  child: const Text('Punch out'),
                ),
              ),
            ],
          ),
          if (_status != null)
            Padding(
              padding: const EdgeInsets.only(top: 16),
              child: Text(_status!),
            ),
        ],
      ),
    );
  }
}
