import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'outbox_sync_providers.dart';

/// @nodoc — prefer [outboxStatsProvider] and [syncRunningProvider].
@Deprecated('Use outboxStatsProvider / syncRunningProvider')
final legacySyncStateProvider = Provider<LegacySyncState>((ref) {
  final stats = ref.watch(outboxStatsProvider).valueOrNull;
  return LegacySyncState(pendingOutboxCount: stats?.needsAttention ?? 0);
});

@Deprecated('Use OutboxStats')
class LegacySyncState {
  const LegacySyncState({this.pendingOutboxCount = 0});
  final int pendingOutboxCount;
}
