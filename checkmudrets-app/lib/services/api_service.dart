import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;

import '../models/receipt.dart';
import '../models/stats.dart';
import '../models/user.dart';
import '../utils/constants.dart';

/// HTTP-клиент для взаимодействия с FastAPI бэкендом.
class ApiService {
  final String baseUrl;

  ApiService({String? baseUrl}) : baseUrl = baseUrl ?? ApiConstants.baseUrl;

  // ─── Auth ──────────────────────────────────────────────────────────────────

  /// Регистрация или вход по device_id.
  Future<User> register(String deviceId, String? name) async {
    final response = await http
        .post(
          Uri.parse('$baseUrl/auth/register'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({'device_id': deviceId, 'name': name}),
        )
        .timeout(ApiConstants.timeout);

    _checkStatus(response);
    return User.fromJson(jsonDecode(response.body) as Map<String, dynamic>);
  }

  // ─── Receipts ──────────────────────────────────────────────────────────────

  /// Загрузить фото чека (multipart/form-data).
  Future<Map<String, dynamic>> uploadReceipt(
    String deviceId,
    File imageFile,
  ) async {
    final request = http.MultipartRequest(
      'POST',
      Uri.parse('$baseUrl/receipts'),
    );
    request.fields['device_id'] = deviceId;
    request.files.add(
      await http.MultipartFile.fromPath('file', imageFile.path),
    );

    final streamed = await request.send().timeout(ApiConstants.uploadTimeout);
    final response = await http.Response.fromStream(streamed);

    _checkStatus(response);
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  /// Получить историю чеков.
  Future<List<Receipt>> getReceipts(String deviceId, {int limit = 10}) async {
    final uri = Uri.parse('$baseUrl/receipts').replace(
      queryParameters: {'device_id': deviceId, 'limit': limit.toString()},
    );
    final response = await http.get(uri).timeout(ApiConstants.timeout);

    _checkStatus(response);
    final data = jsonDecode(response.body) as Map<String, dynamic>;
    final list = data['receipts'] as List<dynamic>;
    return list.map((e) => Receipt.fromJson(e as Map<String, dynamic>)).toList();
  }

  // ─── Stats ─────────────────────────────────────────────────────────────────

  /// Получить статистику за месяц.
  Future<Stats> getStats(String deviceId, {String? month}) async {
    final params = <String, String>{'device_id': deviceId};
    if (month != null) params['month'] = month;

    final uri = Uri.parse('$baseUrl/stats').replace(queryParameters: params);
    final response = await http.get(uri).timeout(ApiConstants.timeout);

    _checkStatus(response);
    return Stats.fromJson(jsonDecode(response.body) as Map<String, dynamic>);
  }

  // ─── Advice ────────────────────────────────────────────────────────────────

  /// Получить персональные советы по экономии.
  Future<String> getAdvice(String deviceId) async {
    final uri = Uri.parse('$baseUrl/advice').replace(
      queryParameters: {'device_id': deviceId},
    );
    final response = await http.get(uri).timeout(ApiConstants.timeout);

    _checkStatus(response);
    final data = jsonDecode(response.body) as Map<String, dynamic>;
    return data['advice'] as String;
  }

  // ─── Report ────────────────────────────────────────────────────────────────

  /// Получить недельный отчёт.
  Future<Map<String, dynamic>> getReport(String deviceId) async {
    final uri = Uri.parse('$baseUrl/report').replace(
      queryParameters: {'device_id': deviceId},
    );
    final response = await http.get(uri).timeout(ApiConstants.timeout);

    _checkStatus(response);
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  // ─── Helpers ───────────────────────────────────────────────────────────────

  void _checkStatus(http.Response response) {
    if (response.statusCode < 200 || response.statusCode >= 300) {
      String message = 'Ошибка сервера: ${response.statusCode}';
      try {
        final body = jsonDecode(response.body) as Map<String, dynamic>;
        message = body['detail'] as String? ?? message;
      } catch (_) {}
      throw ApiException(message, response.statusCode);
    }
  }
}

/// Исключение при ошибке API.
class ApiException implements Exception {
  final String message;
  final int statusCode;

  const ApiException(this.message, this.statusCode);

  @override
  String toString() => 'ApiException($statusCode): $message';
}
