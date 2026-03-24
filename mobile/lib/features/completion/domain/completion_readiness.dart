import '../data/models/completion_requirements_dto.dart';

/// One line for UI lists (satisfied or pending).
class CompletionLineItem {
  const CompletionLineItem({
    required this.category,
    required this.label,
    required this.detail,
    required this.isSatisfied,
  });

  final String category;
  final String label;
  final String detail;
  final bool isSatisfied;
}

/// Pure logic — mirrors `try_finalize_job_completion_if_possible` requirement merge
/// (`dispatch/service.py`): forms + signatures + media + parts **only if**
/// [materialPolicy] != `no_materials_expected`.
class CompletionReadinessResult {
  const CompletionReadinessResult({
    required this.requirementsAllSatisfied,
    required this.satisfiedItems,
    required this.pendingItems,
    required this.statusBlockers,
    required this.summaryHeadline,
    required this.summaryDetail,
  });

  /// True when every **counted** requirement row has `satisfied_at` (or there are none).
  final bool requirementsAllSatisfied;

  final List<CompletionLineItem> satisfiedItems;
  final List<CompletionLineItem> pendingItems;

  /// Derived from [jobStatus] string (e.g. `completion_blocked_*`), not from the bundle.
  final List<String> statusBlockers;

  final String summaryHeadline;
  final String summaryDetail;
}

CompletionReadinessResult computeCompletionReadiness({
  required JobCompletionRequirementsBundleDto bundle,
  required String jobStatus,
  required String materialPolicy,
}) {
  final policy = materialPolicy.isNotEmpty ? materialPolicy : bundle.materialPolicy;
  final includeParts = policy != 'no_materials_expected';

  final satisfied = <CompletionLineItem>[];
  final pending = <CompletionLineItem>[];

  void addForm(JobFormRequirementDto f) {
    final keys = f.requiredKeys;
    final detail = keys.isEmpty
        ? 'No required keys configured'
        : 'Required fields: ${keys.join(', ')}';
    final line = CompletionLineItem(
      category: 'Form',
      label: f.formKey,
      detail: detail,
      isSatisfied: f.isSatisfied,
    );
    if (f.isSatisfied) {
      satisfied.add(line);
    } else {
      pending.add(line);
    }
  }

  void addSig(JobSignatureRequirementDto s) {
    final line = CompletionLineItem(
      category: 'Signature',
      label: 'Customer / sign-off',
      detail: 'Signature capture',
      isSatisfied: s.isSatisfied,
    );
    if (s.isSatisfied) {
      satisfied.add(line);
    } else {
      pending.add(line);
    }
  }

  void addMedia(JobMediaRequirementDto m) {
    final line = CompletionLineItem(
      category: 'Photos',
      label: 'Site photos',
      detail:
          '${m.requiredPhotoCount} photo(s) required',
      isSatisfied: m.isSatisfied,
    );
    if (m.isSatisfied) {
      satisfied.add(line);
    } else {
      pending.add(line);
    }
  }

  void addParts(JobPartsUsageRequirementDto p) {
    final line = CompletionLineItem(
      category: 'Parts',
      label: 'Parts usage',
      detail:
          '${p.requiredPartsItemsCount} line item(s) required',
      isSatisfied: p.isSatisfied,
    );
    if (p.isSatisfied) {
      satisfied.add(line);
    } else {
      pending.add(line);
    }
  }

  for (final f in bundle.formRequirements) {
    addForm(f);
  }
  for (final s in bundle.signatureRequirements) {
    addSig(s);
  }
  for (final m in bundle.mediaRequirements) {
    addMedia(m);
  }
  if (includeParts) {
    for (final p in bundle.partsRequirements) {
      addParts(p);
    }
  }

  final allSatisfied = pending.isEmpty;

  final blockers = <String>[];
  final st = jobStatus.toLowerCase();
  if (st == 'completed' || st == 'closed' || st == 'cancelled') {
    blockers.clear();
  } else {
    if (st == 'completion_blocked_inventory') {
      blockers.add(
        'Parts or inventory reconciliation may be blocking completion (dispatcher approval may be required).',
      );
    }
    if (st == 'completion_blocked_forms' ||
        st == 'completion_pending_forms') {
      blockers.add(
        'Job status is $jobStatus — finish outstanding checklist items (forms, signature, photos, or parts per policy).',
      );
    }
  }

  String headline;
  String detail;
  if (st == 'completed' || st == 'closed' || st == 'cancelled') {
    headline = 'Job finished';
    detail =
        'Status: $jobStatus. No further completion actions apply in this view.';
  } else if (!allSatisfied) {
    headline = 'Not ready to complete';
    detail =
        'Dispatch has configured requirements that are not all satisfied yet.';
  } else if (st == 'completion_blocked_inventory') {
    headline = 'Requirements done — inventory pending';
    detail =
        'Checklist rows are satisfied, but the job may still be blocked on parts/inventory rules server-side.';
  } else {
    headline = 'Requirement checklist satisfied';
    detail =
        'All configured requirement rows show satisfied. Final job completion is determined by the server (time, inventory, invoicing). No “Complete job” action is exposed here.';
  }

  return CompletionReadinessResult(
    requirementsAllSatisfied: allSatisfied,
    satisfiedItems: satisfied,
    pendingItems: pending,
    statusBlockers: blockers,
    summaryHeadline: headline,
    summaryDetail: detail,
  );
}
