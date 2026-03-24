import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'connectivity_service.dart';
import 'sync_engine.dart';

/// App-start + periodic + connectivity reconnect sync triggers.
class SyncLifecycle extends ConsumerStatefulWidget {
  const SyncLifecycle({super.key, required this.child});

  final Widget child;

  @override
  ConsumerState<SyncLifecycle> createState() => _SyncLifecycleState();
}

class _SyncLifecycleState extends ConsumerState<SyncLifecycle> {
  Timer? _timer;
  StreamSubscription<List<dynamic>>? _connectivitySub;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      unawaited(ref.read(syncEngineProvider).processQueue());
    });
    _timer = Timer.periodic(const Duration(seconds: 45), (_) {
      unawaited(ref.read(syncEngineProvider).processQueue());
    });
    _connectivitySub =
        ref.read(connectivityServiceProvider).onConnectivityChanged.listen((_) {
      unawaited(ref.read(syncEngineProvider).processQueue());
    });
  }

  @override
  void dispose() {
    _timer?.cancel();
    unawaited(_connectivitySub?.cancel());
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => widget.child;
}
