import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/errors/api_exception.dart';
import '../../../core/errors/error_mapper.dart';
import '../../../core/network/dio_client.dart';

final inventoryLookupRepositoryProvider = Provider<InventoryLookupRepository>(
  (ref) => InventoryLookupRepository(dio: ref.watch(dioProvider)),
);

class InventoryLookupItem {
  InventoryLookupItem({
    required this.id,
    required this.sku,
    required this.name,
    required this.onHandQuantity,
    required this.unitOfMeasure,
  });

  final String id;
  final String sku;
  final String name;
  final double onHandQuantity;
  final String unitOfMeasure;

  factory InventoryLookupItem.fromJson(Map<String, dynamic> json) {
    return InventoryLookupItem(
      id: json['id'] as String,
      sku: json['sku'] as String,
      name: json['name'] as String? ?? '',
      onHandQuantity: (json['on_hand_quantity'] as num?)?.toDouble() ?? 0,
      unitOfMeasure: json['unit_of_measure'] as String? ?? 'ea',
    );
  }
}

class InventoryLookupRepository {
  InventoryLookupRepository({required this.dio});

  final Dio dio;

  Future<List<InventoryLookupItem>> searchItems({
    required String query,
    int limit = 20,
  }) async {
    try {
      final response = await dio.get<List<dynamic>>(
        '/inventory/engineer/items/search',
        queryParameters: <String, dynamic>{
          'q': query,
          'limit': limit,
        },
      );
      final data = response.data ?? const <dynamic>[];
      return data
          .whereType<Map<String, dynamic>>()
          .map(InventoryLookupItem.fromJson)
          .toList();
    } on DioException catch (e) {
      if (e.error is ApiException) throw e.error! as ApiException;
      throw ErrorMapper.fromDio(e);
    }
  }
}
