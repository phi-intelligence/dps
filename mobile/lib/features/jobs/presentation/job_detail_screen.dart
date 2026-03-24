import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:geolocator/geolocator.dart';
import 'package:go_router/go_router.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../../core/errors/api_exception.dart';
import '../../../core/errors/action_failure_guidance.dart';
import '../../../core/sync/outbox_sync_providers.dart';
import '../../../core/sync/submission_outcome.dart';
import '../../../core/sync/sync_coordinator.dart';
import '../../completion/data/completion_providers.dart';
import '../../completion/presentation/job_completion_readiness_section.dart';
import '../../completion/presentation/job_evidence_section.dart';
import '../data/jobs_list_notifier.dart';
import '../data/active_job_context_repository.dart';
import '../data/jobs_repository.dart';
import '../data/models/job_dto.dart';
import 'job_activity_section.dart';
import 'job_outbox_strip.dart';

/// Engineer workflow for a single job: summary, location, punch, telemetry, maps.
class JobDetailScreen extends ConsumerWidget {
  const JobDetailScreen({super.key, required this.jobId});

  final String jobId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final jobAsync = ref.watch(jobDetailProvider(jobId));

    return jobAsync.when(
      loading: () => Scaffold(
        appBar: AppBar(title: const Text('Job')),
        body: const Center(child: CircularProgressIndicator()),
      ),
      error: (err, _) => Scaffold(
        appBar: AppBar(title: const Text('Job')),
        body: _JobDetailError(
          message: err.toString(),
          onRetry: () {
            ref.invalidate(jobDetailProvider(jobId));
            ref.invalidate(jobGeofenceProvider(jobId));
            ref.invalidate(completionRequirementsProvider(jobId));
          },
        ),
      ),
      data: (job) => _JobDetailScaffold(jobId: jobId, initialJob: job),
    );
  }
}

class _JobDetailError extends StatelessWidget {
  const _JobDetailError({required this.message, required this.onRetry});

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
            Text(message, textAlign: TextAlign.center),
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

class _JobDetailScaffold extends ConsumerStatefulWidget {
  const _JobDetailScaffold({
    required this.jobId,
    required this.initialJob,
  });

  final String jobId;
  final JobDto initialJob;

  @override
  ConsumerState<_JobDetailScaffold> createState() => _JobDetailScaffoldState();
}

class _JobDetailScaffoldState extends ConsumerState<_JobDetailScaffold> {
  late JobDto _job;
  final _scrollController = ScrollController();
  final _completionKey = GlobalKey();
  final _activityKey = GlobalKey();
  final _evidenceKey = GlobalKey();
  Timer? _telemetryTimer;
  StreamSubscription<Position>? _positionSub;
  bool _telemetryBusy = false;
  bool _gpsStreamStarted = false;
  double? _lastSentLat;
  double? _lastSentLon;
  DateTime? _lastSentAt;
  String? _telemetryStatus;
  Position? _lastPosition;
  bool _punchBusy = false;
  bool _acceptBusy = false;
  String? _actionMessage;

  static const _minSendInterval = Duration(seconds: 10);
  static const _minMoveMeters = 25.0;

  @override
  void initState() {
    super.initState();
    _job = widget.initialJob;
    unawaited(ref.read(activeJobContextRepositoryProvider).setActiveJobId(widget.jobId));
    unawaited(_startGpsStream());
    _telemetryTimer = Timer.periodic(const Duration(seconds: 10), (_) {
      unawaited(_sendTelemetryBestEffort(reason: 'interval'));
    });
  }

  @override
  void dispose() {
    _scrollController.dispose();
    _telemetryTimer?.cancel();
    unawaited(_positionSub?.cancel());
    super.dispose();
  }

  Future<void> _scrollTo(GlobalKey key) async {
    final ctx = key.currentContext;
    if (ctx == null) return;
    await Scrollable.ensureVisible(
      ctx,
      duration: const Duration(milliseconds: 250),
      curve: Curves.easeInOut,
      alignment: 0.05,
    );
  }

  Future<void> _refreshJob() async {
    try {
      ref.invalidate(jobGeofenceProvider(widget.jobId));
      ref.invalidate(completionRequirementsProvider(widget.jobId));
      final fresh = await ref.read(jobsRepositoryProvider).getJob(widget.jobId);
      if (mounted) {
        setState(() => _job = fresh);
        final terminal = fresh.isCompleted || fresh.isCancelled;
        unawaited(ref.read(activeJobContextRepositoryProvider).setActiveJobId(terminal ? null : fresh.id));
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Refresh failed: $e')),
        );
      }
    }
  }

  Future<void> _startGpsStream() async {
    if (_gpsStreamStarted) return;
    try {
      var permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
      }
      if (permission == LocationPermission.deniedForever ||
          permission == LocationPermission.denied) {
        if (mounted) {
          setState(() => _telemetryStatus =
              'GPS: enable location permission for punch & tracking');
        }
        return;
      }
      _gpsStreamStarted = true;
      const settings = LocationSettings(
        accuracy: LocationAccuracy.high,
        distanceFilter: 8,
      );
      _positionSub = Geolocator.getPositionStream(locationSettings: settings)
          .listen(
        (pos) {
          _lastPosition = pos;
          if (mounted) setState(() {});
          unawaited(_sendTelemetryBestEffort(reason: 'move', position: pos));
        },
        onError: (Object e) {
          if (mounted) {
            setState(() => _telemetryStatus = 'GPS stream error: $e');
          }
        },
      );
      final current = await Geolocator.getCurrentPosition(
        locationSettings:
            const LocationSettings(accuracy: LocationAccuracy.high),
      );
      _lastPosition = current;
      if (mounted) setState(() {});
    } catch (e) {
      if (mounted) {
        setState(() => _telemetryStatus = 'GPS failed: $e');
      }
    }
  }

  Future<void> _sendTelemetryBestEffort({
    required String reason,
    Position? position,
  }) async {
    if (_telemetryBusy) return;
    final pos = position ?? _lastPosition;
    if (pos == null) return;

    final lat = pos.latitude;
    final lon = pos.longitude;

    final now = DateTime.now();
    if (_lastSentAt != null) {
      final since = now.difference(_lastSentAt!);
      if (since < _minSendInterval) {
        if (reason != 'move') return;
        if (_lastSentLat != null && _lastSentLon != null) {
          final moved = Geolocator.distanceBetween(
            _lastSentLat!,
            _lastSentLon!,
            lat,
            lon,
          );
          if (moved < _minMoveMeters) return;
        }
      }
    }

    _telemetryBusy = true;
    try {
      final outcome = await ref.read(syncCoordinatorProvider).submitTelemetryBestEffort(
            latitude: lat,
            longitude: lon,
            occurredAtIsoUtc: DateTime.now().toUtc().toIso8601String(),
            heading: pos.heading,
            speed: pos.speed,
            accuracy: pos.accuracy,
          );
      if (!outcome.isSynced) {
        if (mounted) {
          setState(
            () => _telemetryStatus = 'Telemetry failed: ${outcome.detailMessage ?? "unknown"}',
          );
        }
        return;
      }
      _lastSentAt = now;
      _lastSentLat = lat;
      _lastSentLon = lon;
      if (mounted) {
        setState(() => _telemetryStatus =
            'Telemetry OK ($reason) @ ${now.toLocal().toIso8601String()}');
      }
    } catch (e) {
      if (mounted) {
        setState(() => _telemetryStatus = 'Telemetry failed: $e');
      }
    } finally {
      _telemetryBusy = false;
    }
  }

  Future<void> _sendTelemetryNow() async {
    if (_lastPosition == null) {
      setState(() => _telemetryStatus = 'Waiting for GPS fix…');
      try {
        final p = await Geolocator.getCurrentPosition(
          locationSettings:
              const LocationSettings(accuracy: LocationAccuracy.high),
        );
        _lastPosition = p;
      } catch (e) {
        setState(() => _telemetryStatus = 'Could not get location: $e');
        return;
      }
    }
    await _sendTelemetryBestEffort(reason: 'manual', position: _lastPosition);
  }

  Future<void> _openMaps() async {
    final lat = _job.siteLatitude ?? _job.addressGeocodedLatitude;
    final lon = _job.siteLongitude ?? _job.addressGeocodedLongitude;
    final Uri uri;
    if (lat != null && lon != null) {
      uri = Uri.parse(
        'https://www.google.com/maps/search/?api=1&query=$lat,$lon',
      );
    } else {
      uri = Uri.parse(
        'https://www.google.com/maps/search/?api=1&query=${Uri.encodeComponent(_job.address)}',
      );
    }
    if (!await launchUrl(uri, mode: LaunchMode.externalApplication)) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Could not open maps')),
        );
      }
    }
  }

  Future<void> _acceptJob() async {
    setState(() {
      _acceptBusy = true;
      _actionMessage = null;
    });
    try {
      final outcome = await ref.read(syncCoordinatorProvider).submitAcceptJob(
            jobId: widget.jobId,
          );
      if (!mounted) return;
      if (outcome.isSynced) {
        final fresh = await ref.read(syncCoordinatorProvider).fetchJobDetail(widget.jobId);
        if (fresh != null && mounted) {
          setState(() => _job = fresh);
        }
        ref.invalidate(jobGeofenceProvider(widget.jobId));
        ref.invalidate(completionRequirementsProvider(widget.jobId));
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Job accepted')),
          );
        }
      } else if (outcome.isQueued) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Accept queued — will sync when online')),
          );
        }
      } else {
        final msg = outcome.detailMessage ?? 'Accept failed';
        final hint = actionFailureGuidance(msg);
        setState(() => _actionMessage = hint.isEmpty ? msg : '$msg\n$hint');
      }
    } on ApiException catch (e) {
      final hint = actionFailureGuidance(e.message);
      setState(() => _actionMessage = hint.isEmpty ? e.message : '${e.message}\n$hint');
    } catch (e) {
      setState(() => _actionMessage = e.toString());
    } finally {
      setState(() => _acceptBusy = false);
    }
  }

  Future<void> _punch(String kind) async {
    final pos = _lastPosition;
    if (pos == null) {
      setState(() => _actionMessage = 'Wait for GPS or grant location permission.');
      return;
    }
    setState(() {
      _punchBusy = true;
      _actionMessage = null;
    });
    try {
      unawaited(_sendTelemetryBestEffort(reason: 'punch', position: pos));
      final outcome = await ref.read(syncCoordinatorProvider).submitPunch(
            kind: kind,
            jobId: widget.jobId,
            latitude: pos.latitude,
            longitude: pos.longitude,
          );
      if (!mounted) return;
      if (outcome.isSynced) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              kind == 'in' ? 'Punched in' : 'Punched out',
            ),
          ),
        );
        await _refreshJob();
      } else if (outcome.isQueued) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Punch queued — will sync when online'),
          ),
        );
      } else if (outcome.isFailed || outcome.isBlocked) {
        final msg = outcome.detailMessage ?? 'Punch failed';
        final hint = actionFailureGuidance(msg);
        setState(() => _actionMessage = hint.isEmpty ? msg : '$msg\n$hint');
      }
    } on ApiException catch (e) {
      final hint = actionFailureGuidance(e.message);
      setState(() => _actionMessage = hint.isEmpty ? e.message : '${e.message}\n$hint');
    } catch (e) {
      setState(() => _actionMessage = e.toString());
    } finally {
      setState(() => _punchBusy = false);
    }
  }

  bool get _canShowAccept => _job.status == 'created';

  @override
  Widget build(BuildContext context) {
    final geofenceAsync = ref.watch(jobGeofenceProvider(widget.jobId));
    final completionAsync =
        ref.watch(completionRequirementsProvider(widget.jobId));

    return Scaffold(
      appBar: AppBar(
        title: Text(
          _job.displayTitle,
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: 'Refresh job',
            onPressed: () async {
              await _refreshJob();
              if (context.mounted) {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Job refreshed')),
                );
              }
            },
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _refreshJob,
        child: ListView(
          controller: _scrollController,
          padding: const EdgeInsets.all(16),
          children: [
            _SummaryCard(job: _job),
            const SizedBox(height: 12),
            _ComplianceVisibilityCard(job: _job),
            const SizedBox(height: 12),
            _ActiveSessionCard(
              job: _job,
              onPunchOut: _lastPosition == null || _punchBusy ? null : () => _punch('out'),
              onOpenCompletion: () => _scrollTo(_completionKey),
              onOpenActivity: () => _scrollTo(_activityKey),
              onOpenEvidence: () => _scrollTo(_evidenceKey),
              onOpenSync: () => context.push('/jobs/sync'),
            ),
            const SizedBox(height: 12),
            JobOutboxStrip(jobId: widget.jobId),
            Container(
              key: _completionKey,
              child: JobCompletionReadinessSection(
                job: _job,
                bundleAsync: completionAsync,
                onRetry: () => ref.invalidate(
                  completionRequirementsProvider(widget.jobId),
                ),
              ),
            ),
            const SizedBox(height: 12),
            geofenceAsync.when(
              loading: () => const LinearProgressIndicator(),
              error: (_, __) => const SizedBox.shrink(),
              data: (gf) {
                if (gf == null) {
                  return Card(
                    color: Theme.of(context).colorScheme.errorContainer,
                    child: const ListTile(
                      leading: Icon(Icons.warning_amber_rounded),
                      title: Text('No site geofence configured'),
                      subtitle: Text(
                        'Dispatch must set a geofence for this job, or punch may fail server-side.',
                      ),
                    ),
                  );
                }
                return Card(
                  color: Theme.of(context).colorScheme.primaryContainer,
                  child: ListTile(
                    leading: const Icon(Icons.location_on_outlined),
                    title: const Text('Site geofence active'),
                    subtitle: Text(
                      'Radius ${gf.radiusM.toStringAsFixed(0)} m · centred on lat/lon',
                    ),
                  ),
                );
              },
            ),
            const SizedBox(height: 16),
            Text(
              'Location for punch',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 4),
            Text(
              _lastPosition != null
                  ? 'Using GPS · ${ _lastPosition!.latitude.toStringAsFixed(5) }, ${ _lastPosition!.longitude.toStringAsFixed(5) }'
                  : 'Waiting for GPS…',
              style: Theme.of(context).textTheme.bodySmall,
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: FilledButton.icon(
                    onPressed: _punchBusy || _lastPosition == null
                        ? null
                        : () => _punch('in'),
                    icon: const Icon(Icons.login),
                    label: const Text('Punch in'),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: FilledButton.tonalIcon(
                    onPressed: _punchBusy || _lastPosition == null
                        ? null
                        : () => _punch('out'),
                    icon: const Icon(Icons.logout),
                    label: const Text('Punch out'),
                  ),
                ),
              ],
            ),
            if (_actionMessage != null) ...[
              const SizedBox(height: 8),
              Text(
                _actionMessage!,
                style: TextStyle(color: Theme.of(context).colorScheme.error),
              ),
            ],
            const SizedBox(height: 16),
            Container(
              key: _activityKey,
              child: JobActivitySection(
              jobId: widget.jobId,
              onSubmitted: _refreshJob,
            ),
            ),
            const SizedBox(height: 16),
            Text('Actions', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            if (_canShowAccept)
              ListTile(
                leading: const Icon(Icons.check_circle_outline),
                title: const Text('Accept job'),
                subtitle: const Text('Assigns you and sets status to accepted'),
                trailing: _acceptBusy
                    ? const SizedBox(
                        width: 24,
                        height: 24,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : null,
                onTap: _acceptBusy ? null : _acceptJob,
              ),
            ListTile(
              leading: const Icon(Icons.map_outlined),
              title: const Text('Open in maps'),
              subtitle: const Text('Navigate to site address or coordinates'),
              onTap: _openMaps,
            ),
            ListTile(
              leading: const Icon(Icons.radar),
              title: const Text('Send location now'),
              subtitle: const Text('Posts telemetry immediately (throttled)'),
              onTap: _telemetryBusy ? null : _sendTelemetryNow,
            ),
            if (_telemetryStatus != null)
              Padding(
                padding: const EdgeInsets.only(top: 8),
                child: Text(
                  _telemetryStatus!,
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: Theme.of(context).colorScheme.onSurfaceVariant,
                      ),
                ),
              ),
            const SizedBox(height: 24),
            Container(
              key: _evidenceKey,
              child: JobEvidenceSection(
              jobId: widget.jobId,
              bundleAsync: completionAsync,
              materialPolicy: _job.materialPolicy ?? 'materials_optional',
              onEvidenceSubmitted: _refreshJob,
            ),
            ),
          ],
        ),
      ),
    );
  }
}

class _ActiveSessionCard extends ConsumerWidget {
  const _ActiveSessionCard({
    required this.job,
    required this.onPunchOut,
    required this.onOpenCompletion,
    required this.onOpenActivity,
    required this.onOpenEvidence,
    required this.onOpenSync,
  });

  final JobDto job;
  final VoidCallback? onPunchOut;
  final VoidCallback onOpenCompletion;
  final VoidCallback onOpenActivity;
  final VoidCallback onOpenEvidence;
  final VoidCallback onOpenSync;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final summary = ref.watch(jobOutboxSummaryProvider(job.id));
    final s = summary.value;
    final isActive = job.isInProgressLike;
    final punched = job.isLikelyPunchedIn;
    final syncText = s == null
        ? ''
        : s.hasAny
            ? ' · sync: ${s.pending} pending, ${s.failed} failed, ${s.conflict} conflict'
            : ' · sync: clear';
    return Card(
      color: isActive ? Theme.of(context).colorScheme.secondaryContainer : null,
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(isActive ? Icons.play_circle_fill : Icons.work_outline),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    isActive ? 'Active in-progress session' : 'Not currently active',
                    style: Theme.of(context).textTheme.titleSmall,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 6),
            Text(
              'Status: ${job.status}${punched ? ' · likely punched in' : ''}$syncText',
              style: Theme.of(context).textTheme.bodySmall,
            ),
            const SizedBox(height: 10),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                FilledButton.tonalIcon(
                  onPressed: onPunchOut,
                  icon: const Icon(Icons.logout),
                  label: const Text('Punch out'),
                ),
                OutlinedButton.icon(
                  onPressed: onOpenCompletion,
                  icon: const Icon(Icons.checklist),
                  label: const Text('Completion'),
                ),
                OutlinedButton.icon(
                  onPressed: onOpenActivity,
                  icon: const Icon(Icons.notes),
                  label: const Text('Notes'),
                ),
                OutlinedButton.icon(
                  onPressed: onOpenEvidence,
                  icon: const Icon(Icons.assignment_turned_in_outlined),
                  label: const Text('Evidence'),
                ),
                if (s != null && s.hasAny)
                  OutlinedButton.icon(
                    onPressed: onOpenSync,
                    icon: const Icon(Icons.sync_problem),
                    label: const Text('Resolve sync'),
                  ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _SummaryCard extends StatelessWidget {
  const _SummaryCard({required this.job});

  final JobDto job;

  @override
  Widget build(BuildContext context) {
    final t = Theme.of(context).textTheme;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(job.displayTitle, style: t.titleLarge),
            const SizedBox(height: 8),
            _InfoRow(label: 'Job ID', value: job.id),
            _InfoRow(label: 'Status', value: job.status),
            if (job.scheduledAt != null)
              _InfoRow(
                label: 'Scheduled',
                value: job.scheduledAt!.toLocal().toString(),
              ),
            if (job.quoteId != null)
              _InfoRow(label: 'Quote', value: job.quoteId!),
            if (job.contractId != null)
              _InfoRow(label: 'Contract', value: job.contractId!),
            if (job.customerId != null)
              _InfoRow(label: 'Customer ID', value: job.customerId!),
            if (job.siteId != null)
              _InfoRow(label: 'Site ID', value: job.siteId!),
            if (job.workType != null)
              _InfoRow(label: 'Work type', value: job.workType!),
            if (job.materialPolicy != null)
              _InfoRow(label: 'Material policy', value: job.materialPolicy!),
            if (job.etaMinutes != null)
              _InfoRow(
                label: 'ETA (minutes)',
                value: job.etaMinutes!.toStringAsFixed(0),
              ),
            if (job.slaRiskState != null)
              _InfoRow(label: 'SLA risk', value: job.slaRiskState!),
            const Divider(height: 24),
            Text(
              'Site / address',
              style: t.titleSmall,
            ),
            const SizedBox(height: 4),
            Text(job.address, style: t.bodyMedium),
            const SizedBox(height: 12),
            const Divider(height: 24),
            Text('Customer/site context', style: t.titleSmall),
            const SizedBox(height: 4),
            Text(
              [
                if (job.customerId != null) 'Customer ref: ${job.customerId}',
                if (job.siteId != null) 'Site ref: ${job.siteId}',
                if (job.assetId != null) 'Asset ref: ${job.assetId}',
                if (job.contractId != null) 'Contract ref: ${job.contractId}',
              ].isEmpty
                  ? 'No extra customer/site references available on this job payload.'
                  : [
                      if (job.customerId != null) 'Customer ref: ${job.customerId}',
                      if (job.siteId != null) 'Site ref: ${job.siteId}',
                      if (job.assetId != null) 'Asset ref: ${job.assetId}',
                      if (job.contractId != null) 'Contract ref: ${job.contractId}',
                    ].join('\n'),
              style: t.bodySmall?.copyWith(
                color: Theme.of(context).colorScheme.onSurfaceVariant,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              'Contact details and rich customer history are not included in current engineer /jobs payloads.',
              style: t.bodySmall?.copyWith(
                color: Theme.of(context).colorScheme.onSurfaceVariant,
                fontStyle: FontStyle.italic,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _ComplianceVisibilityCard extends StatelessWidget {
  const _ComplianceVisibilityCard({required this.job});
  final JobDto job;

  @override
  Widget build(BuildContext context) {
    final required = job.complianceRequired == true;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Compliance visibility', style: Theme.of(context).textTheme.titleSmall),
            const SizedBox(height: 6),
            Text(
              required ? 'Compliance is marked required for this job.' : 'No explicit compliance requirement flag.',
              style: Theme.of(context).textTheme.bodySmall,
            ),
            const SizedBox(height: 6),
            Text(
              'Certificate artifacts are not yet exposed on engineer-safe APIs in this app version.',
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

class _InfoRow extends StatelessWidget {
  const _InfoRow({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 120,
            child: Text(
              label,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: Theme.of(context).colorScheme.onSurfaceVariant,
                  ),
            ),
          ),
          Expanded(child: Text(value, style: Theme.of(context).textTheme.bodyMedium)),
        ],
      ),
    );
  }
}
