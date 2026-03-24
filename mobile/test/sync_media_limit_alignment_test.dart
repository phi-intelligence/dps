import 'package:flutter_test/flutter_test.dart';
import 'package:phi_dps_mobile/core/sync/sync_coordinator.dart';

/// Backend: `ENGINEER_MOBILE_MAX_MEDIA_JSON_BYTES` in
/// `backend/app/modules/dispatch/engineer_mobile_constants.py` (2 MiB).
void main() {
  test('queued media JSON cap matches backend 2 MiB policy', () {
    expect(kMaxQueuedMediaPayloadBytes, 2 * 1024 * 1024);
  });
}
