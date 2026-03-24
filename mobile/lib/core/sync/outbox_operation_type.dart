/// Queued operation kinds stored in [OutboxOps.operationType].
///
/// Policy: see [WAVE5_SYNC_POLICY.md](../../../../docs/WAVE5_SYNC_POLICY.md).
abstract final class OutboxOperationType {
  static const punchIn = 'punch_in';
  static const punchOut = 'punch_out';
  /// Not persisted to outbox — reserved for diagnostics / future compaction.
  static const telemetry = 'telemetry';
  static const formSubmit = 'form_submit';
  static const signatureSubmit = 'signature_submit';
  static const mediaSubmit = 'media_submit';
  static const partsUsage = 'parts_usage';
  static const acceptJob = 'accept_job';
  static const jobNote = 'job_note';
}
