// @ai perplexity flutter-api-service  
// API service for communicating with AmiFi backend
// Human decisions: Error handling, endpoint configuration

import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/transaction.dart';

class ApiService {
  static const String baseUrl = 'http://localhost:8000';
  
  // Human decision: API endpoints mapping
  static const String transactionsEndpoint = '/api/v1/transactions';
  static const String healthEndpoint = '/health';
  static const String processBulkEndpoint = '/api/v1/process-bulk';

  Future<List<Transaction>> getTransactions({
    int limit = 50,
    String userId = 'demo-user',
  }) async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl$transactionsEndpoint?limit=$limit&user_id=$userId'),
        headers: {'Content-Type': 'application/json'},
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        final transactions = (data['transactions'] as List)
            .map((json) => Transaction.fromJson(json))
            .toList();
        return transactions;
      } else {
        throw Exception('Failed to load transactions: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Network error: $e');
    }
  }

  Future<Map<String, dynamic>> getHealthStatus() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl$healthEndpoint'),
        headers: {'Content-Type': 'application/json'},
      );

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Health check failed: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Health check error: $e');
    }
  }

  Future<Map<String, dynamic>> processBulkData({
    required String fileType,
    String userId = 'demo-user',
  }) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl$processBulkEndpoint'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({
          'file_type': fileType,
          'user_id': userId,
        }),
      );

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Bulk processing failed: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Bulk processing error: $e');
    }
  }
}
