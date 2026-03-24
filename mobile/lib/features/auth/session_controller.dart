import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../app/router_refresh.dart';
import '../../core/auth/token_storage.dart';
import 'data/auth_repository.dart';

enum AuthState {
  loading,
  authenticated,
  unauthenticated,
}

final sessionControllerProvider =
    NotifierProvider<SessionController, AuthState>(() => SessionController());

class SessionController extends Notifier<AuthState> {
  @override
  AuthState build() {
    Future.microtask(_hydrate);
    return AuthState.loading;
  }

  Future<void> _hydrate() async {
    final token = await ref.read(tokenStorageProvider).readAccessToken();
    state = token != null && token.isNotEmpty
        ? AuthState.authenticated
        : AuthState.unauthenticated;
    ref.read(routerRefreshProvider).refresh();
  }

  Future<void> login(String email, String password) async {
    await ref.read(authRepositoryProvider).login(
          username: email.trim(),
          password: password,
        );
    state = AuthState.authenticated;
    ref.read(routerRefreshProvider).refresh();
  }

  Future<void> logout() async {
    await ref.read(tokenStorageProvider).clear();
    state = AuthState.unauthenticated;
    ref.read(routerRefreshProvider).refresh();
  }
}
