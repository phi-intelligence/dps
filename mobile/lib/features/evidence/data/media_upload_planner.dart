import 'dart:convert';

class PlannedMediaBatch {
  const PlannedMediaBatch({
    required this.payloads,
    required this.approxBytes,
  });

  final List<Map<String, Object>> payloads;
  final int approxBytes;
}

class MediaUploadPlan {
  const MediaUploadPlan({
    required this.batches,
    required this.totalBytes,
  });

  final List<PlannedMediaBatch> batches;
  final int totalBytes;
}

MediaUploadPlan planMediaBatches({
  required List<Map<String, Object>> payloads,
  required int hardLimitBytes,
  int targetLimitBytes = 1800000,
}) {
  if (hardLimitBytes <= 0) {
    throw ArgumentError.value(hardLimitBytes, 'hardLimitBytes', 'must be > 0');
  }
  final target = targetLimitBytes > 0 ? targetLimitBytes : hardLimitBytes;
  final batches = <PlannedMediaBatch>[];
  var current = <Map<String, Object>>[];

  int bytesFor(List<Map<String, Object>> rows) {
    return utf8.encode(
      jsonEncode(<String, Object>{
        'media_type': 'photo',
        'payloads': rows,
      }),
    ).length;
  }

  for (final payload in payloads) {
    final singleSize = bytesFor(<Map<String, Object>>[payload]);
    if (singleSize > hardLimitBytes) {
      throw StateError('Single photo payload exceeds server limit ($singleSize > $hardLimitBytes).');
    }

    final trial = [...current, payload];
    final trialSize = bytesFor(trial);
    if (trialSize <= target || current.isEmpty) {
      current = trial;
      continue;
    }

    final currentSize = bytesFor(current);
    batches.add(PlannedMediaBatch(payloads: current, approxBytes: currentSize));
    current = [payload];
  }

  if (current.isNotEmpty) {
    batches.add(PlannedMediaBatch(payloads: current, approxBytes: bytesFor(current)));
  }

  final totalBytes = batches.fold<int>(0, (sum, b) => sum + b.approxBytes);
  return MediaUploadPlan(batches: batches, totalBytes: totalBytes);
}
