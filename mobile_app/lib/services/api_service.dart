import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;

class ApiService {
  static const String backendUrl = "http://34.122.6.67:8080";

  /// Oluşturulan MP4 videosunu multipart/form-data olarak backend'e gönderir.
  Future<bool> uploadVideoToBackend(String filePath) async {
    try {
      final File videoFile = File(filePath);

      if (!await videoFile.exists()) {
        print("Backend upload hatası: Video dosyası bulunamadı.");
        print("Aranan dosya: $filePath");
        return false;
      }

      final int fileSizeBytes = await videoFile.length();
      final double fileSizeMb = fileSizeBytes / (1024 * 1024);

      print("========== VİDEO UPLOAD ==========");
      print("Backend adresi: $backendUrl");
      print("Dosya yolu: $filePath");
      print("Dosya boyutu: ${fileSizeMb.toStringAsFixed(2)} MB");

      final Uri uri = Uri.parse('$backendUrl/api/video/upload-video');

      final http.MultipartRequest request = http.MultipartRequest('POST', uri);

      // Backend UploadFile parametresinin adı "file" olduğu için
      // multipart alanının adı da "file" olmalıdır.
      request.files.add(
        await http.MultipartFile.fromPath(
          'file',
          filePath,
          filename: 'teknofest_video.mp4',
        ),
      );

      print("Video backend'e gönderiliyor...");

      final http.StreamedResponse streamedResponse = await request
          .send()
          .timeout(const Duration(minutes: 5));

      final String responseBody = await streamedResponse.stream.bytesToString();

      print("Backend HTTP kodu: ${streamedResponse.statusCode}");
      print("Backend cevabı: $responseBody");
      print("==================================");

      if (streamedResponse.statusCode == 200 ||
          streamedResponse.statusCode == 201 ||
          streamedResponse.statusCode == 202) {
        print("Video backend'e başarıyla gönderildi.");
        return true;
      }

      print(
        "Backend video yüklemeyi reddetti: "
        "${streamedResponse.statusCode}",
      );
      return false;
    } catch (error, stackTrace) {
      print("Backend yükleme hatası: $error");
      print("Stack trace: $stackTrace");
      return false;
    }
  }

  /// Backend'in ürettiği AI sonuçlarını alır.
  Future<Map<String, dynamic>> fetchAiResults() async {
    try {
      final Uri uri = Uri.parse('$backendUrl/api/video/results');

      print("AI sonuçları isteniyor: $uri");

      final http.Response response = await http
          .get(uri)
          .timeout(const Duration(seconds: 30));

      print("AI sonuç HTTP kodu: ${response.statusCode}");
      print("AI sonuç cevabı: ${response.body}");

      if (response.statusCode == 200) {
        final dynamic decodedBody = jsonDecode(response.body);

        if (decodedBody is Map<String, dynamic>) {
          return decodedBody;
        }

        return {
          "status": "FAILED",
          "message": "Backend beklenmeyen JSON biçimi döndürdü.",
        };
      }

      return {
        "status": "FAILED",
        "message": "Sunucu hatası: ${response.statusCode}",
        "response": response.body,
      };
    } catch (error, stackTrace) {
      print("JSON çekme hatası: $error");
      print("Stack trace: $stackTrace");

      return {"status": "FAILED", "message": "Sonuçlar alınamadı: $error"};
    }
  }
}
