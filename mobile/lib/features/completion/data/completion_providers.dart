import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'completion_repository.dart';
import 'models/completion_requirements_dto.dart';

/// Latest completion bundle from `GET /jobs/{id}/completion-requirements`.
final completionRequirementsProvider =
    FutureProvider.family<JobCompletionRequirementsBundleDto, String>(
  (ref, jobId) async {
    return ref.watch(completionRepositoryProvider).getCompletionRequirements(jobId);
  },
);
