import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/errors/action_failure_guidance.dart';
import '../../auth/data/current_user_repository.dart';
import '../data/vehicle_checks_repository.dart';

class VehicleChecksScreen extends ConsumerStatefulWidget {
  const VehicleChecksScreen({super.key});

  @override
  ConsumerState<VehicleChecksScreen> createState() => _VehicleChecksScreenState();
}

class _VehicleChecksScreenState extends ConsumerState<VehicleChecksScreen> {
  bool _loading = true;
  bool _submitting = false;
  String? _error;
  String? _state;

  String? _vehicleId;
  CurrentUserDto? _me;
  VehicleInspectionOutDto? _latest;
  List<VehicleDefectOutDto> _openDefects = const [];

  final List<_CheckItemState> _checks = [
    _CheckItemState(code: 'lights', label: 'Lights', pass: true, criticalOnFail: true),
    _CheckItemState(code: 'brakes', label: 'Brakes', pass: true, criticalOnFail: true),
    _CheckItemState(code: 'tyres', label: 'Tyres', pass: true, criticalOnFail: true),
    _CheckItemState(code: 'fluids', label: 'Fluids', pass: true, criticalOnFail: false),
    _CheckItemState(code: 'load', label: 'Tools / load secure', pass: true, criticalOnFail: true),
  ];
  final _issueTitle = TextEditingController();
  final _issueDescription = TextEditingController();
  String _issueSeverity = 'minor';

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    for (final c in _checks) {
      c.notesController.dispose();
    }
    _issueTitle.dispose();
    _issueDescription.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
      _state = null;
    });
    try {
      final repo = ref.read(vehicleChecksRepositoryProvider);
      final me = await ref.read(currentUserRepositoryProvider).getCurrentUser();
      final vehicleId = me.assignedVehicleId?.trim();
      if (vehicleId == null || vehicleId.isEmpty) {
        setState(() {
          _loading = false;
          _me = me;
          _error = 'No assigned vehicle. Ask dispatch/admin to set assigned_vehicle_id.';
        });
        return;
      }
      final latest = await repo.latestInspection(vehicleId);
      final defects = await repo.listOpenDefects(vehicleId);
      if (!mounted) return;
      setState(() {
        _me = me;
        _vehicleId = vehicleId;
        _latest = latest;
        _openDefects = defects;
        _loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _loading = false;
        _error = e.toString();
      });
    }
  }

  Future<void> _submit() async {
    final me = _me;
    final vehicleId = _vehicleId;
    if (me == null || vehicleId == null) return;
    setState(() {
      _submitting = true;
      _error = null;
      _state = null;
    });
    try {
      final hasCriticalFail = _checks.any((c) => !c.pass && c.criticalOnFail);
      final hasAnyFail = _checks.any((c) => !c.pass);
      final overall = hasCriticalFail
          ? 'failed_critical'
          : hasAnyFail
              ? 'failed_minor'
              : 'passed';

      final items = _checks
          .map(
            (c) => VehicleInspectionItemInput(
              itemCode: c.code,
              itemLabel: c.label,
              result: c.pass ? 'pass' : 'fail',
              notes: c.notesController.text.trim().isEmpty ? null : c.notesController.text.trim(),
              failCriticality: c.criticalOnFail ? 'critical' : 'minor',
            ),
          )
          .toList();

      await ref.read(vehicleChecksRepositoryProvider).submitInspection(
            vehicleId: vehicleId,
            engineerId: me.id,
            items: items,
            overallStatus: overall,
            notes: null,
          );

      final issueTitle = _issueTitle.text.trim();
      if (issueTitle.isNotEmpty) {
        await ref.read(vehicleChecksRepositoryProvider).createDefect(
              vehicleId: vehicleId,
              title: issueTitle,
              severity: _issueSeverity,
              description: _issueDescription.text.trim().isEmpty ? null : _issueDescription.text.trim(),
            );
      }
      if (!mounted) return;
      setState(() {
        _submitting = false;
        _state = 'Vehicle check submitted.';
      });
      await _load();
    } catch (e) {
      if (!mounted) return;
      final msg = e.toString();
      final hint = actionFailureGuidance(msg);
      setState(() {
        _submitting = false;
        _error = hint.isEmpty ? msg : '$msg\n$hint';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Vehicle check')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _load,
              child: ListView(
                padding: const EdgeInsets.all(12),
                children: [
                  Card(
                    child: ListTile(
                      title: Text(_vehicleId == null ? 'Vehicle not assigned' : 'Vehicle $_vehicleId'),
                      subtitle: Text(
                        _latest == null
                            ? 'No previous inspection'
                            : 'Last: ${_latest!.overallStatus} on ${_latest!.inspectionDate.toLocal().toString().split(' ').first}',
                      ),
                    ),
                  ),
                  Card(
                    child: ListTile(
                      leading: const Icon(Icons.warning_amber_outlined),
                      title: Text('Open defects: ${_openDefects.length}'),
                      subtitle: _openDefects.isEmpty
                          ? const Text('No open defects')
                          : Text(_openDefects.take(2).map((d) => '${d.severity}: ${d.title}').join(' | ')),
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text('Daily inspection', style: Theme.of(context).textTheme.titleMedium),
                  const SizedBox(height: 8),
                  ..._checks.map(
                    (c) => Card(
                      child: Padding(
                        padding: const EdgeInsets.all(12),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: [
                                Expanded(child: Text(c.label)),
                                SegmentedButton<bool>(
                                  segments: const [
                                    ButtonSegment(value: true, label: Text('Pass')),
                                    ButtonSegment(value: false, label: Text('Fail')),
                                  ],
                                  selected: {c.pass},
                                  onSelectionChanged: _submitting
                                      ? null
                                      : (v) => setState(() {
                                            c.pass = v.first;
                                          }),
                                ),
                              ],
                            ),
                            if (!c.pass) ...[
                              const SizedBox(height: 8),
                              TextField(
                                controller: c.notesController,
                                decoration: const InputDecoration(
                                  labelText: 'Issue details',
                                  border: OutlineInputBorder(),
                                ),
                              ),
                            ],
                          ],
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text('Issue capture (optional)', style: Theme.of(context).textTheme.titleMedium),
                  const SizedBox(height: 8),
                  TextField(
                    controller: _issueTitle,
                    decoration: const InputDecoration(
                      labelText: 'Issue title',
                      border: OutlineInputBorder(),
                    ),
                  ),
                  const SizedBox(height: 8),
                  TextField(
                    controller: _issueDescription,
                    maxLines: 2,
                    decoration: const InputDecoration(
                      labelText: 'Issue description',
                      border: OutlineInputBorder(),
                    ),
                  ),
                  const SizedBox(height: 8),
                  DropdownButtonFormField<String>(
                    initialValue: _issueSeverity,
                    items: const [
                      DropdownMenuItem(value: 'minor', child: Text('Minor')),
                      DropdownMenuItem(value: 'major', child: Text('Major')),
                      DropdownMenuItem(value: 'critical', child: Text('Critical')),
                    ],
                    decoration: const InputDecoration(
                      labelText: 'Issue severity',
                      border: OutlineInputBorder(),
                    ),
                    onChanged: _submitting ? null : (v) => setState(() => _issueSeverity = v ?? 'minor'),
                  ),
                  const SizedBox(height: 12),
                  FilledButton.icon(
                    onPressed: _submitting || _vehicleId == null ? null : _submit,
                    icon: const Icon(Icons.check_circle_outline),
                    label: Text(_submitting ? 'Submitting...' : 'Submit daily vehicle check'),
                  ),
                  if (_state != null) ...[
                    const SizedBox(height: 8),
                    Text(_state!, style: TextStyle(color: Theme.of(context).colorScheme.primary)),
                  ],
                  if (_error != null) ...[
                    const SizedBox(height: 8),
                    Text(_error!, style: TextStyle(color: Theme.of(context).colorScheme.error)),
                  ],
                ],
              ),
            ),
    );
  }
}

class _CheckItemState {
  _CheckItemState({
    required this.code,
    required this.label,
    required this.pass,
    required this.criticalOnFail,
  });

  final String code;
  final String label;
  bool pass;
  final bool criticalOnFail;
  final TextEditingController notesController = TextEditingController();
}
