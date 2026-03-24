import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/errors/api_exception.dart';
import '../../../core/errors/error_mapper.dart';
import '../../../core/network/dio_client.dart';

final currentUserRepositoryProvider = Provider<CurrentUserRepository>(
  (ref) => CurrentUserRepository(dio: ref.watch(dioProvider)),
);

class CurrentUserDto {
  const CurrentUserDto({
    required this.id,
    required this.email,
    required this.assignedVehicleId,
    required this.roles,
  });

  final String id;
  final String email;
  final String? assignedVehicleId;
  final List<String> roles;

  factory CurrentUserDto.fromJson(Map<String, dynamic> json) {
    final roleRows = (json['roles'] as List<dynamic>? ?? const <dynamic>[])
        .whereType<Map<String, dynamic>>();
    return CurrentUserDto(
      id: '${json['id']}',
      email: json['email'] as String? ?? '',
      assignedVehicleId: json['assigned_vehicle_id'] as String?,
      roles: roleRows.map((r) => (r['name'] as String? ?? '').trim()).where((r) => r.isNotEmpty).toList(),
    );
  }
}

class CurrentUserRepository {
  CurrentUserRepository({required this.dio});
  final Dio dio;

  Future<CurrentUserDto> getCurrentUser() async {
    try {
      final response = await dio.get<Map<String, dynamic>>('/auth/me');
      final data = response.data;
      if (data == null) {
        throw ApiException(
          statusCode: response.statusCode,
          message: 'Empty current user response',
          rawDetail: null,
        );
      }
      return CurrentUserDto.fromJson(data);
    } on DioException catch (e) {
      if (e.error is ApiException) throw e.error! as ApiException;
      throw ErrorMapper.fromDio(e);
    }
  }
}
