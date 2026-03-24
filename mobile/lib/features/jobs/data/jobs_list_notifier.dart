import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'jobs_repository.dart';
import 'models/job_dto.dart';

final jobListProvider =
    AsyncNotifierProvider<JobListNotifier, List<JobDto>>(JobListNotifier.new);

class JobListNotifier extends AsyncNotifier<List<JobDto>> {
  @override
  Future<List<JobDto>> build() async {
    return _load();
  }

  Future<List<JobDto>> _load() async {
    return ref.read(jobsRepositoryProvider).listJobs();
  }

  Future<void> refresh() async {
    state = await AsyncValue.guard(_load);
  }
}

/// `GET /jobs/{id}` with pull-to-refresh support.
final jobDetailProvider =
    FutureProvider.family<JobDto, String>((ref, jobId) async {
  return ref.watch(jobsRepositoryProvider).getJob(jobId);
});

final jobGeofenceProvider =
    FutureProvider.family<JobGeofenceDto?, String>((ref, jobId) async {
  return ref.watch(jobsRepositoryProvider).getGeofence(jobId);
});
