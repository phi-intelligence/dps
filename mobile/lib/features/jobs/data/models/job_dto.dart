/// Mirrors backend [JobOut] (`dispatch/schemas.py`).
///
/// **Not included in API response:** customer name, phone, email — use CRM/portal
/// if needed; engineer `GET /jobs` and `GET /jobs/{id}` do not embed contact fields.
class JobDto {
  const JobDto({
    required this.id,
    required this.address,
    required this.status,
    this.customerId,
    this.quoteId,
    this.contractId,
    this.siteId,
    this.assetId,
    this.ppmScheduleId,
    this.workType,
    this.slaPolicyId,
    this.slaPriority,
    this.assetCriticality,
    this.coveredUnderContract,
    this.complianceRequired,
    this.scheduledAt,
    this.assignedEngineerId,
    this.siteLatitude,
    this.siteLongitude,
    this.addressGeocodedLatitude,
    this.addressGeocodedLongitude,
    this.materialPolicy,
    this.dispatchPriority,
    this.etaMinutes,
    this.delayNotice,
    this.delayNoticeAt,
    this.slaRiskState,
    this.slaTargetCompletionAt,
    this.createdAt,
  });

  final String id;
  final String address;
  final String status;
  final String? customerId;
  final String? quoteId;
  final String? contractId;
  final String? siteId;
  final String? assetId;
  final String? ppmScheduleId;
  final String? workType;
  final String? slaPolicyId;
  final String? slaPriority;
  final String? assetCriticality;
  final bool? coveredUnderContract;
  final bool? complianceRequired;
  final DateTime? scheduledAt;
  final String? assignedEngineerId;
  final double? siteLatitude;
  final double? siteLongitude;
  final double? addressGeocodedLatitude;
  final double? addressGeocodedLongitude;
  final String? materialPolicy;
  final int? dispatchPriority;
  final double? etaMinutes;
  final String? delayNotice;
  final DateTime? delayNoticeAt;
  final String? slaRiskState;
  final DateTime? slaTargetCompletionAt;
  final DateTime? createdAt;

  /// Display title: no separate title field on backend — use address or id.
  String get displayTitle =>
      address.trim().isNotEmpty ? address : 'Job $id';

  factory JobDto.fromJson(Map<String, dynamic> json) {
    return JobDto(
      id: '${json['id']}',
      address: json['address'] as String? ?? '',
      status: json['status'] as String? ?? '',
      customerId: json['customer_id'] as String?,
      quoteId: json['quote_id'] as String?,
      contractId: json['contract_id'] as String?,
      siteId: json['site_id'] as String?,
      assetId: json['asset_id'] as String?,
      ppmScheduleId: json['ppm_schedule_id'] as String?,
      workType: json['work_type'] as String?,
      slaPolicyId: json['sla_policy_id'] as String?,
      slaPriority: json['sla_priority'] as String?,
      assetCriticality: json['asset_criticality'] as String?,
      coveredUnderContract: json['covered_under_contract'] as bool?,
      complianceRequired: json['compliance_required'] as bool?,
      scheduledAt: _parseDate(json['scheduled_at']),
      assignedEngineerId: json['assigned_engineer_id'] as String?,
      siteLatitude: (json['site_latitude'] as num?)?.toDouble(),
      siteLongitude: (json['site_longitude'] as num?)?.toDouble(),
      addressGeocodedLatitude:
          (json['address_geocoded_latitude'] as num?)?.toDouble(),
      addressGeocodedLongitude:
          (json['address_geocoded_longitude'] as num?)?.toDouble(),
      materialPolicy: json['material_policy'] as String?,
      dispatchPriority: (json['dispatch_priority'] as num?)?.toInt(),
      etaMinutes: (json['eta_minutes'] as num?)?.toDouble(),
      delayNotice: json['delay_notice'] as String?,
      delayNoticeAt: _parseDate(json['delay_notice_at']),
      slaRiskState: json['sla_risk_state'] as String?,
      slaTargetCompletionAt: _parseDate(json['sla_target_completion_at']),
      createdAt: _parseDate(json['created_at']),
    );
  }

  static DateTime? _parseDate(Object? value) {
    if (value == null) return null;
    if (value is String) return DateTime.tryParse(value);
    return null;
  }
}

extension JobDtoActiveX on JobDto {
  bool get isOnSite => status == 'on_site';
  bool get isEnRoute => status == 'en_route';
  bool get isAccepted => status == 'accepted';
  bool get isCompletionPending => status == 'completion_pending_forms';
  bool get isCompleted => status == 'completed';
  bool get isCancelled => status == 'cancelled';

  /// Practical active/in-progress heuristic using existing backend status only.
  bool get isInProgressLike => isOnSite || isEnRoute || isAccepted || isCompletionPending;

  /// Closest available signal for "punched in" without a dedicated session endpoint.
  bool get isLikelyPunchedIn => isOnSite;
}

/// `GET /tracking/geofences/{job_id}` → [JobGeofenceOut]
class JobGeofenceDto {
  const JobGeofenceDto({
    required this.id,
    required this.jobId,
    required this.latitude,
    required this.longitude,
    required this.radiusM,
  });

  final String id;
  final String jobId;
  final double latitude;
  final double longitude;
  final double radiusM;

  factory JobGeofenceDto.fromJson(Map<String, dynamic> json) {
    return JobGeofenceDto(
      id: '${json['id']}',
      jobId: '${json['job_id']}',
      latitude: (json['latitude'] as num).toDouble(),
      longitude: (json['longitude'] as num).toDouble(),
      radiusM: (json['radius_m'] as num).toDouble(),
    );
  }
}
