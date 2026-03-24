import 'dart:convert';

/// Mirrors [JobCompletionRequirementsBundleOut] (`dispatch/schemas.py`).
///
/// **Gap vs full completion story:** This bundle lists requirement **rows** and
/// `satisfied_at` only. It does **not** include:
/// - live job `status` (use [JobDto.status] alongside this)
/// - inventory/parts reconciliation approval state (may still block with
///   `completion_blocked_inventory` after requirements are satisfied)
/// - certificate presence (invoice/compliance is separate modules)
class JobCompletionRequirementsBundleDto {
  const JobCompletionRequirementsBundleDto({
    required this.jobId,
    required this.materialPolicy,
    required this.formRequirements,
    required this.signatureRequirements,
    required this.mediaRequirements,
    required this.partsRequirements,
  });

  final String jobId;
  final String materialPolicy;
  final List<JobFormRequirementDto> formRequirements;
  final List<JobSignatureRequirementDto> signatureRequirements;
  final List<JobMediaRequirementDto> mediaRequirements;
  final List<JobPartsUsageRequirementDto> partsRequirements;

  factory JobCompletionRequirementsBundleDto.fromJson(Map<String, dynamic> json) {
    return JobCompletionRequirementsBundleDto(
      jobId: '${json['job_id']}',
      materialPolicy: json['material_policy'] as String? ?? 'materials_optional',
      formRequirements: (json['form_requirements'] as List<dynamic>? ?? [])
          .map((e) => JobFormRequirementDto.fromJson(e as Map<String, dynamic>))
          .toList(),
      signatureRequirements:
          (json['signature_requirements'] as List<dynamic>? ?? [])
              .map((e) =>
                  JobSignatureRequirementDto.fromJson(e as Map<String, dynamic>))
              .toList(),
      mediaRequirements: (json['media_requirements'] as List<dynamic>? ?? [])
          .map((e) => JobMediaRequirementDto.fromJson(e as Map<String, dynamic>))
          .toList(),
      partsRequirements:
          (json['parts_requirements'] as List<dynamic>? ?? [])
              .map((e) =>
                  JobPartsUsageRequirementDto.fromJson(e as Map<String, dynamic>))
              .toList(),
    );
  }
}

class JobFormRequirementDto {
  const JobFormRequirementDto({
    required this.id,
    required this.jobId,
    required this.formKey,
    required this.requiredKeysJson,
    this.satisfiedAt,
    this.createdAt,
  });

  final String id;
  final String jobId;
  final String formKey;
  final String requiredKeysJson;
  final DateTime? satisfiedAt;
  final DateTime? createdAt;

  List<String> get requiredKeys {
    try {
      final decoded = jsonDecode(requiredKeysJson);
      if (decoded is List) {
        return decoded.map((e) => e.toString()).toList();
      }
    } catch (_) {}
    return [];
  }

  bool get isSatisfied => satisfiedAt != null;

  factory JobFormRequirementDto.fromJson(Map<String, dynamic> json) {
    return JobFormRequirementDto(
      id: '${json['id']}',
      jobId: '${json['job_id']}',
      formKey: json['form_key'] as String? ?? '',
      requiredKeysJson: json['required_keys_json'] as String? ?? '[]',
      satisfiedAt: _parseDate(json['satisfied_at']),
      createdAt: _parseDate(json['created_at']),
    );
  }
}

class JobSignatureRequirementDto {
  const JobSignatureRequirementDto({
    required this.id,
    required this.jobId,
    this.satisfiedAt,
    this.createdAt,
  });

  final String id;
  final String jobId;
  final DateTime? satisfiedAt;
  final DateTime? createdAt;

  bool get isSatisfied => satisfiedAt != null;

  factory JobSignatureRequirementDto.fromJson(Map<String, dynamic> json) {
    return JobSignatureRequirementDto(
      id: '${json['id']}',
      jobId: '${json['job_id']}',
      satisfiedAt: _parseDate(json['satisfied_at']),
      createdAt: _parseDate(json['created_at']),
    );
  }
}

class JobMediaRequirementDto {
  const JobMediaRequirementDto({
    required this.id,
    required this.jobId,
    required this.requiredPhotoCount,
    this.satisfiedAt,
    this.createdAt,
  });

  final String id;
  final String jobId;
  final int requiredPhotoCount;
  final DateTime? satisfiedAt;
  final DateTime? createdAt;

  bool get isSatisfied => satisfiedAt != null;

  factory JobMediaRequirementDto.fromJson(Map<String, dynamic> json) {
    return JobMediaRequirementDto(
      id: '${json['id']}',
      jobId: '${json['job_id']}',
      requiredPhotoCount: (json['required_photo_count'] as num?)?.toInt() ?? 0,
      satisfiedAt: _parseDate(json['satisfied_at']),
      createdAt: _parseDate(json['created_at']),
    );
  }
}

class JobPartsUsageRequirementDto {
  const JobPartsUsageRequirementDto({
    required this.id,
    required this.jobId,
    required this.requiredPartsItemsCount,
    this.satisfiedAt,
    this.createdAt,
  });

  final String id;
  final String jobId;
  final int requiredPartsItemsCount;
  final DateTime? satisfiedAt;
  final DateTime? createdAt;

  bool get isSatisfied => satisfiedAt != null;

  factory JobPartsUsageRequirementDto.fromJson(Map<String, dynamic> json) {
    return JobPartsUsageRequirementDto(
      id: '${json['id']}',
      jobId: '${json['job_id']}',
      requiredPartsItemsCount:
          (json['required_parts_items_count'] as num?)?.toInt() ?? 0,
      satisfiedAt: _parseDate(json['satisfied_at']),
      createdAt: _parseDate(json['created_at']),
    );
  }
}

DateTime? _parseDate(Object? value) {
  if (value == null) return null;
  if (value is String) return DateTime.tryParse(value);
  return null;
}
