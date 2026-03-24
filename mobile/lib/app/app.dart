import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/sync/sync_lifecycle.dart';
import '../features/sync/presentation/sync_banner.dart';
import 'router.dart';
import 'theme.dart';

class PhiDpsApp extends ConsumerWidget {
  const PhiDpsApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(goRouterProvider);
    return SyncLifecycle(
      child: MaterialApp.router(
        title: 'PHI-DPS Mobile',
        theme: buildPhiDpsTheme(),
        routerConfig: router,
        builder: (context, child) {
          return Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const SyncBanner(),
              Expanded(child: child ?? const SizedBox.shrink()),
            ],
          );
        },
      ),
    );
  }
}
