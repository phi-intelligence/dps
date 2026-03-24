String actionFailureGuidance(String? message) {
  final m = (message ?? '').toLowerCase();
  if (m.isEmpty) return '';
  if (m.contains('idempotency-key') || m.contains('conflict')) {
    return 'This looks like a replay/conflict. Avoid duplicate edits, then retry once or discard from Sync diagnostics.';
  }
  if (m.contains('missing required keys') || m.contains('missing_required_keys')) {
    return 'Complete the missing required fields before retrying.';
  }
  if (m.contains('assigned to another engineer')) {
    return 'This job is no longer assigned to your account. Refresh jobs and contact dispatch.';
  }
  if (m.contains('geofence')) {
    return 'Move inside the site geofence, refresh GPS, then retry.';
  }
  if (m.contains('already punched in')) {
    return 'You are already clocked in for this job. Use punch out or check active job state.';
  }
  if (m.contains('no previous punch-in')) {
    return 'Punch in first, then punch out.';
  }
  if (m.contains('too large') || m.contains('413') || m.contains('2 mib')) {
    return 'Reduce photo count/quality and submit in smaller sets. Use the Small data preset if needed.';
  }
  if (m.contains('unknown sku')) {
    return 'Use SKU search to pick a valid stock item before resubmitting.';
  }
  if (m.contains('forbidden') || m.contains('403')) {
    return 'Your current role cannot perform this action. Contact dispatch/admin.';
  }
  if (m.contains('401') || m.contains('expired token')) {
    return 'Session may be expired. Re-login and retry.';
  }
  if (m.contains('cannot queue photos while offline')) {
    return 'Media uploads require connectivity in this release. Reconnect and retry in smaller batches.';
  }
  return 'If this persists, open Sync diagnostics to retry or discard the failed action.';
}
