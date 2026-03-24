import 'package:flutter_test/flutter_test.dart';
import 'package:phi_dps_mobile/features/completion/data/models/completion_requirements_dto.dart';
import 'package:phi_dps_mobile/features/completion/domain/completion_readiness.dart';

void main() {
  group('computeCompletionReadiness', () {
    test('empty bundle + no pending → satisfied', () {
      const bundle = JobCompletionRequirementsBundleDto(
        jobId: 'j1',
        materialPolicy: 'materials_optional',
        formRequirements: [],
        signatureRequirements: [],
        mediaRequirements: [],
        partsRequirements: [],
      );
      final r = computeCompletionReadiness(
        bundle: bundle,
        jobStatus: 'accepted',
        materialPolicy: 'materials_optional',
      );
      expect(r.requirementsAllSatisfied, isTrue);
      expect(r.pendingItems, isEmpty);
    });

    test('parts excluded when policy is no_materials_expected', () {
      final bundle = JobCompletionRequirementsBundleDto(
        jobId: 'j1',
        materialPolicy: 'no_materials_expected',
        formRequirements: [
          JobFormRequirementDto(
            id: '1',
            jobId: 'j1',
            formKey: 'gas',
            requiredKeysJson: '[]',
            satisfiedAt: DateTime.utc(2025, 1, 1),
          ),
        ],
        signatureRequirements: const [],
        mediaRequirements: const [],
        partsRequirements: [
          const JobPartsUsageRequirementDto(
            id: 'p1',
            jobId: 'j1',
            requiredPartsItemsCount: 2,
            satisfiedAt: null,
          ),
        ],
      );
      final r = computeCompletionReadiness(
        bundle: bundle,
        jobStatus: 'accepted',
        materialPolicy: 'no_materials_expected',
      );
      expect(r.requirementsAllSatisfied, isTrue);
      expect(r.pendingItems, isEmpty);
    });

    test('pending form blocks satisfied', () {
      const bundle = JobCompletionRequirementsBundleDto(
        jobId: 'j1',
        materialPolicy: 'materials_optional',
        formRequirements: [
          JobFormRequirementDto(
            id: '1',
            jobId: 'j1',
            formKey: 'risk',
            requiredKeysJson: '["a"]',
            satisfiedAt: null,
          ),
        ],
        signatureRequirements: [],
        mediaRequirements: [],
        partsRequirements: [],
      );
      final r = computeCompletionReadiness(
        bundle: bundle,
        jobStatus: 'completion_blocked_forms',
        materialPolicy: 'materials_optional',
      );
      expect(r.requirementsAllSatisfied, isFalse);
      expect(r.pendingItems, isNotEmpty);
      expect(r.statusBlockers, isNotEmpty);
    });
  });
}
