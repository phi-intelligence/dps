import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/errors/api_exception.dart';
import '../../../core/errors/error_mapper.dart';
import '../../../core/network/dio_client.dart';
import '../../auth/data/current_user_repository.dart';

final vehicleChecksRepositoryProvider = Provider<VehicleChecksRepository>(
  (ref) => VehicleChecksRepository(
    dio: ref.watch(dioProvider),
    currentUserRepository: ref.watch(currentUserRepositoryProvider),
  ),
);

class VehicleInspectionItemInput {
  const VehicleInspectionItemInput({
    required this.itemCode,
    required this.itemLabel,
    required this.result,
    this.notes,
    this.failCriticality = 'minor',
  });

  final String itemCode;
  final String itemLabel;
  final String result;
  final String? notes;
  final String failCriticality;
}

class VehicleInspectionOutDto {
  const VehicleInspectionOutDto({
    required this.id,
    required this.vehicleId,
    required this.overallStatus,
    required this.inspectionDate,
  });

  final String id;
  final String vehicleId;
  final String overallStatus;
  final DateTime inspectionDate;

  factory VehicleInspectionOutDto.fromJson(Map<String, dynamic> json) {
    return VehicleInspectionOutDto(
      id: '${json['id']}',
      vehicleId: '${json['vehicle_id']}',
      overallStatus: json['overall_status'] as String? ?? '',
      inspectionDate: DateTime.parse(json['inspection_date'] as String),
    );
  }
}

class VehicleDefectOutDto {
  const VehicleDefectOutDto({
    required this.id,
    required this.title,
    required this.severity,
    required this.status,
  });

  final String id;
  final String title;
  final String severity;
  final String status;

  factory VehicleDefectOutDto.fromJson(Map<String, dynamic> json) {
    return VehicleDefectOutDto(
      id: '${json['id']}',
      title: json['title'] as String? ?? '',
      severity: json['severity'] as String? ?? '',
      status: json['status'] as String? ?? '',
    );
  }
}

class VehicleChecksRepository {
  VehicleChecksRepository({
    required this.dio,
    required this.currentUserRepository,
  });

  final Dio dio;
  final CurrentUserRepository currentUserRepository;

  Future<String> requireAssignedVehicleId() async {
    final me = await currentUserRepository.getCurrentUser();
    final vehicleId = me.assignedVehicleId?.trim();
    if (vehicleId == null || vehicleId.isEmpty) {
      throw ApiException(
        statusCode: null,
        message: 'No assigned vehicle found for this account.',
      );
    }
    return vehicleId;
  }

  Future<VehicleInspectionOutDto?> latestInspection(String vehicleId) async {
    try {
      final response = await dio.get<Map<String, dynamic>>('/vehicles/$vehicleId/inspections/latest');
      final data = response.data;
      if (data == null) return null;
      return VehicleInspectionOutDto.fromJson(data);
    } on DioException catch (e) {
      if (e.response?.statusCode == 404) return null;
      if (e.error is ApiException) {
        final ae = e.error! as ApiException;
        if (ae.statusCode == 404) return null;
        throw ae;
      }
      throw ErrorMapper.fromDio(e);
    }
  }

  Future<List<VehicleDefectOutDto>> listOpenDefects(String vehicleId) async {
    try {
      final response = await dio.get<List<dynamic>>(
        '/vehicles/$vehicleId/defects',
        queryParameters: const {'status': 'open'},
      );
      final data = response.data ?? const <dynamic>[];
      return data.whereType<Map<String, dynamic>>().map(VehicleDefectOutDto.fromJson).toList();
    } on DioException catch (e) {
      if (e.error is ApiException) throw e.error! as ApiException;
      throw ErrorMapper.fromDio(e);
    }
  }

  Future<VehicleInspectionOutDto> submitInspection({
    required String vehicleId,
    required String engineerId,
    required List<VehicleInspectionItemInput> items,
    required String overallStatus,
    String? notes,
  }) async {
    try {
      final response = await dio.post<Map<String, dynamic>>(
        '/vehicles/$vehicleId/inspections',
        data: {
          'engineer_id': engineerId,
          'overall_status': overallStatus,
          'notes': notes,
          'items': items
              .map(
                (i) => {
                  'item_code': i.itemCode,
                  'item_label': i.itemLabel,
                  'result': i.result,
                  'notes': i.notes,
                  'fail_criticality': i.failCriticality,
                },
              )
              .toList(),
        },
      );
      final data = response.data;
      if (data == null) {
        throw ApiException(
          statusCode: response.statusCode,
          message: 'Empty inspection response',
          rawDetail: null,
        );
      }
      return VehicleInspectionOutDto.fromJson(data);
    } on DioException catch (e) {
      if (e.error is ApiException) throw e.error! as ApiException;
      throw ErrorMapper.fromDio(e);
    }
  }

  Future<void> createDefect({
    required String vehicleId,
    required String title,
    required String severity,
    String? description,
    String defectType = 'daily_check',
  }) async {
    try {
      await dio.post<Map<String, dynamic>>(
        '/vehicles/$vehicleId/defects',
        data: {
          'defect_type': defectType,
          'severity': severity,
          'title': title,
          'description': description,
        },
      );
    } on DioException catch (e) {
      if (e.error is ApiException) throw e.error! as ApiException;
      throw ErrorMapper.fromDio(e);
    }
  }
}
