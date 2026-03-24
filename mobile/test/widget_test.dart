import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:phi_dps_mobile/app/app.dart';
import 'package:phi_dps_mobile/core/auth/token_storage.dart';

import 'support/fake_token_storage.dart';

void main() {
  setUpAll(() {
    TestWidgetsFlutterBinding.ensureInitialized();
  });

  testWidgets('Engineer login screen loads', (WidgetTester tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          tokenStorageProvider.overrideWithValue(FakeTokenStorage()),
        ],
        child: const PhiDpsApp(),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('PHI-DPS Engineer Login'), findsOneWidget);
    expect(find.text('Login'), findsOneWidget);
    expect(find.byType(ElevatedButton), findsWidgets);
  });
}
