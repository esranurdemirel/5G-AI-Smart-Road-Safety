import 'dart:convert';

import 'package:http/http.dart' as http;

class OgwService {
  static const String backendUrl = 'http://34.122.6.67:8080';

  /// Number Verification akışını başlatır ve backend'in 302 Location
  /// adresini mobil ekrana iletir. Open Gateway sayfasını LoginScreen açar.
  Future<Map<String, dynamic>?> verifyNumber(String phoneNumber) async {
    try {
      final Uri uri = Uri.parse(
        '$backendUrl/api/auth/verify',
      ).replace(queryParameters: {'phone_number': phoneNumber.trim()});

      final http.Request request = http.Request('POST', uri)
        ..headers['Content-Type'] = 'application/json'
        ..followRedirects = false;

      final http.StreamedResponse streamedResponse = await request.send();
      final http.Response response = await http.Response.fromStream(
        streamedResponse,
      );

      if (response.statusCode == 302 ||
          response.statusCode == 303 ||
          response.statusCode == 307) {
        return {'status': 302, 'url': response.headers['location']};
      }

      if (response.statusCode == 200 || response.statusCode == 202) {
        return jsonDecode(response.body) as Map<String, dynamic>;
      }

      return {
        'status': response.statusCode,
        'error': 'Doğrulama başlatılamadı',
        'response': response.body,
      };
    } catch (error) {
      return {'status': 0, 'error': error.toString()};
    }
  }

  /// Token ve client secret mobil uygulamaya konulmaz. Backend, Number
  /// Verification sırasında aldığı token ile QoD isteğini yapmalıdır.
  Future<Map<String, dynamic>?> startQoS() async {
    try {
      final Uri uri = Uri.parse('$backendUrl/api/qod/');
      final http.Response response = await http.post(
        uri,
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'duration': 300}),
      );
      print("QoD HTTP status: ${response.statusCode}");
      print("QoD response: ${response.body}");

      if (response.statusCode == 200 || response.statusCode == 201) {
        return jsonDecode(response.body) as Map<String, dynamic>;
      }

      return {
        'status': response.statusCode,
        'error': 'QoD başlatılamadı',
        'response': response.body,
      };
    } catch (error) {
      return {'status': 0, 'error': error.toString()};
    }
  }
}
