import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../features/auth/presentation/login_screen.dart';
import '../features/auth/session_controller.dart';
import '../features/jobs/presentation/job_detail_screen.dart';
import '../features/jobs/presentation/job_list_screen.dart';
import '../features/jobs/presentation/manual_job_punch_screen.dart';
import '../features/sync/presentation/app_diagnostics_screen.dart';
import '../features/sync/presentation/sync_diagnostics_screen.dart';
import '../features/vehicles/presentation/vehicle_checks_screen.dart';
import 'router_refresh.dart';

final goRouterProvider = Provider<GoRouter>((ref) {
  final refresh = ref.watch(routerRefreshProvider);
  final router = GoRouter(
    initialLocation: '/login',
    refreshListenable: refresh,
    redirect: (context, state) {
      final auth = ref.read(sessionControllerProvider);
      if (auth == AuthState.loading) return null;
      final loc = state.uri.path;
      final loggingIn = loc == '/login';
      if (auth == AuthState.unauthenticated && !loggingIn) return '/login';
      if (auth == AuthState.authenticated && loggingIn) return '/jobs';
      return null;
    },
    routes: [
      GoRoute(
        path: '/login',
        builder: (context, state) => const LoginScreen(),
      ),
      GoRoute(
        path: '/jobs',
        builder: (context, state) => const JobListScreen(),
        routes: [
          GoRoute(
            path: 'sync',
            builder: (context, state) => const SyncDiagnosticsScreen(),
          ),
          GoRoute(
            path: 'settings',
            builder: (context, state) => const AppDiagnosticsScreen(),
          ),
          GoRoute(
            path: 'manual-punch',
            builder: (context, state) => const ManualJobPunchScreen(),
          ),
          GoRoute(
            path: 'vehicle-check',
            builder: (context, state) => const VehicleChecksScreen(),
          ),
          GoRoute(
            path: ':jobId',
            builder: (context, state) => JobDetailScreen(
              jobId: state.pathParameters['jobId']!,
            ),
          ),
        ],
      ),
    ],
  );
  ref.onDispose(router.dispose);
  return router;
});
