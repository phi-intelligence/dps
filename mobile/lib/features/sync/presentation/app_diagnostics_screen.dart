import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:package_info_plus/package_info_plus.dart';

import '../../../core/persistence/app_database.dart';
import '../../../core/auth/token_storage.dart';
import '../../../core/network/dio_client.dart';
import '../../../core/sync/outbox_sync_providers.dart';
import '../../auth/session_controller.dart';

class AppDiagnosticsScreen extends ConsumerWidget {
  const AppDiagnosticsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final pkgAsync = ref.watch(_packageInfoProvider);
    final tokenAsync = ref.watch(_tokenExistsProvider);
    final auth = ref.watch(sessionControllerProvider);
    final statsAsync = ref.watch(outboxStatsProvider);
    final lastSyncAsync = ref.watch(lastEngineSyncProvider);
    final recentFailuresAsync = ref.watch(_recentFailureSummaryProvider);
    final apiBase = ref.watch(appConfigProvider).apiBase;

    return Scaffold(
      appBar: AppBar(
        title: const Text('App diagnostics'),
        leading: IconButton(
          icon: const Icon(Icons.close),
          onPressed: () => context.pop(),
        ),
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text('Build & environment', style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 8),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  pkgAsync.when(
                    data: (p) => Text('App version: ${p.version} (${p.buildNumber})'),
                    loading: () => const Text('App version: loading…'),
                    error: (e, _) => Text('App version error: $e'),
                  ),
                  Text('API base: $apiBase'),
                  const Text('Flutter mode: ${kReleaseMode ? "release" : "debug/profile"}'),
                  Text('Platform: ${kIsWeb ? "web" : defaultTargetPlatform.name}'),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          Text('Session', style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 8),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Auth state: $auth'),
                  tokenAsync.when(
                    data: (hasToken) => Text('Stored access token: ${hasToken ? "present" : "missing"}'),
                    loading: () => const Text('Stored access token: loading…'),
                    error: (e, _) => Text('Stored access token error: $e'),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          Text('Sync', style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 8),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  statsAsync.when(
                    data: (s) => Text(
                      'Pending: ${s.pending} · Syncing: ${s.syncing} · Failed: ${s.failed} · Conflict: ${s.conflict}',
                    ),
                    loading: () => const Text('Sync stats: loading…'),
                    error: (e, _) => Text('Sync stats error: $e'),
                  ),
                  const SizedBox(height: 6),
                  lastSyncAsync.when(
                    data: (t) => Text(
                      t == null ? 'Last sync: never' : 'Last sync: ${t.toLocal()}',
                    ),
                    loading: () => const Text('Last sync: loading…'),
                    error: (e, _) => Text('Last sync error: $e'),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 12),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Support snapshot', style: Theme.of(context).textTheme.titleSmall),
                  const SizedBox(height: 6),
                  recentFailuresAsync.when(
                    data: (s) => Text(
                      s.isEmpty ? 'No failed/conflict outbox rows.' : s,
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                    loading: () => const Text('Loading support snapshot...'),
                    error: (e, _) => Text('Support snapshot error: $e'),
                  ),
                  const SizedBox(height: 8),
                  FilledButton.icon(
                    onPressed: () async {
                      final pkg = await ref.read(_packageInfoProvider.future);
                      final hasToken = await ref.read(_tokenExistsProvider.future);
                      final stats = await ref.read(outboxStatsProvider.future);
                      final lastSync = await ref.read(lastEngineSyncProvider.future);
                      final recent = await ref.read(_recentFailureSummaryProvider.future);
                      final text = [
                        'PHI-DPS support snapshot',
                        'Version: ${pkg.version} (${pkg.buildNumber})',
                        'API base: $apiBase',
                        'Auth state: $auth',
                        'Token present: $hasToken',
                        'Sync stats: pending=${stats.pending}, syncing=${stats.syncing}, failed=${stats.failed}, conflict=${stats.conflict}',
                        'Last sync: ${lastSync?.toIso8601String() ?? "never"}',
                        'Failures: ${recent.isEmpty ? "none" : recent}',
                      ].join('\n');
                      await Clipboard.setData(ClipboardData(text: text));
                      if (context.mounted) {
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(content: Text('Support snapshot copied to clipboard')),
                        );
                      }
                    },
                    icon: const Icon(Icons.copy_all_outlined),
                    label: const Text('Copy support snapshot'),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'Escalate immediately for repeated 409 loops, repeated 413 media failures, or job assignment mismatches.',
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: Theme.of(context).colorScheme.onSurfaceVariant,
                        ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

final _packageInfoProvider = FutureProvider<PackageInfo>((ref) async {
  return PackageInfo.fromPlatform();
});

final _tokenExistsProvider = FutureProvider<bool>((ref) async {
  final token = await ref.read(tokenStorageProvider).readAccessToken();
  return token != null && token.isNotEmpty;
});

final _recentFailureSummaryProvider = FutureProvider<String>((ref) async {
  final db = ref.read(appDatabaseProvider);
  final rows = await db.select(db.outboxOps).get();
  final filtered = rows
      .where((r) => r.status == 'failed' || r.status == 'conflict')
      .toList()
    ..sort((a, b) => (b.updatedAt ?? b.createdAt).compareTo(a.updatedAt ?? a.createdAt));
  final top = filtered.take(5).toList(growable: false);
  if (top.isEmpty) return '';
  return top
      .map(
        (r) => '${r.operationType} (${r.status})'
            '${r.lastError == null || r.lastError!.trim().isEmpty ? '' : ': ${r.lastError}'}',
      )
      .join('\n');
});
