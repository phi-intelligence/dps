import 'package:flutter_test/flutter_test.dart';
import 'package:phi_dps_mobile/auth_token.dart';

void main() {
  group('parseAccessTokenFromAuthJson', () {
    test('parses standard OAuth2 JSON', () {
      expect(
        parseAccessTokenFromAuthJson('{"access_token":"abc.xyz","token_type":"bearer"}'),
        'abc.xyz',
      );
    });

    test('throws on missing access_token', () {
      expect(
        () => parseAccessTokenFromAuthJson('{"token_type":"bearer"}'),
        throwsA(isA<FormatException>()),
      );
    });

    test('throws on non-object JSON', () {
      expect(
        () => parseAccessTokenFromAuthJson('"string"'),
        throwsA(isA<FormatException>()),
      );
    });
  });
}
