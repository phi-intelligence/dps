import 'package:flutter_test/flutter_test.dart';
import 'package:phi_dps_mobile/features/evidence/data/media_upload_planner.dart';

void main() {
  Map<String, Object> payloadOfSize(String name, int b64Len) => <String, Object>{
        'filename': '$name.jpg',
        'content_base64': 'x' * b64Len,
        'mime_type': 'image/jpeg',
      };

  test('planMediaBatches splits payloads into safe chunks', () {
    final payloads = [
      payloadOfSize('a', 700000),
      payloadOfSize('b', 700000),
      payloadOfSize('c', 700000),
    ];
    final plan = planMediaBatches(
      payloads: payloads,
      hardLimitBytes: 2 * 1024 * 1024,
      targetLimitBytes: 1500000,
    );
    expect(plan.batches.length, greaterThan(1));
    expect(plan.batches.every((b) => b.approxBytes <= 2 * 1024 * 1024), isTrue);
  });

  test('planMediaBatches throws when single payload exceeds hard limit', () {
    expect(
      () => planMediaBatches(
        payloads: [payloadOfSize('huge', 3 * 1024 * 1024)],
        hardLimitBytes: 2 * 1024 * 1024,
      ),
      throwsA(isA<StateError>()),
    );
  });
}
