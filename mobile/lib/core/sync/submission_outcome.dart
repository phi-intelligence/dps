/// Result of a sync-aware engineer action (Wave 5).
enum SubmissionKind { synced, queued, blocked, failed }

class SubmissionOutcome {
  const SubmissionOutcome._(this.kind, [this.message]);

  final SubmissionKind kind;
  final String? message;

  static const SubmissionOutcome synced =
      SubmissionOutcome._(SubmissionKind.synced);
  static const SubmissionOutcome queued =
      SubmissionOutcome._(SubmissionKind.queued);

  static SubmissionOutcome blocked(String message) =>
      SubmissionOutcome._(SubmissionKind.blocked, message);

  static SubmissionOutcome failed(String message) =>
      SubmissionOutcome._(SubmissionKind.failed, message);
}

extension SubmissionOutcomeX on SubmissionOutcome {
  bool get isSynced => kind == SubmissionKind.synced;
  bool get isQueued => kind == SubmissionKind.queued;
  bool get isBlocked => kind == SubmissionKind.blocked;
  bool get isFailed => kind == SubmissionKind.failed;

  /// User-visible detail for blocked/failed outcomes.
  String? get detailMessage =>
      (kind == SubmissionKind.blocked || kind == SubmissionKind.failed)
          ? message
          : null;
}
