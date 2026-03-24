/// Values for [OutboxOps.status].
abstract final class OutboxStatus {
  static const pending = 'pending';
  static const syncing = 'syncing';
  static const synced = 'synced';
  static const failed = 'failed';
  static const conflict = 'conflict';
}
