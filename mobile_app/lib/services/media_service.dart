import 'dart:io';

import 'package:path_provider/path_provider.dart';
import 'package:ffmpeg_kit_flutter/ffmpeg_kit.dart';
import 'package:ffmpeg_kit_flutter/return_code.dart';
import 'package:gal/gal.dart';

class MediaService {
  Future<String?> downloadVideoForBackend(
    String streamUrl,
    bool isQoDActive,
  ) async {
    try {
      final directory = await getTemporaryDirectory();

      final String timestamp = DateTime.now().millisecondsSinceEpoch.toString();

      final String filePath =
          '${directory.path}/teknofest_record_$timestamp.mp4';

      // -t kullanılmadığı için seçilen HLS videosunun tamamını indirir.
      // QoD başarılıysa yüksek, başarısızsa düşük kaliteli HLS adresi
      // HomeScreen tarafından gönderilir.
      final String command =
          '-y '
          '-i "$streamUrl" '
          '-c copy '
          '-bsf:a aac_adtstoasc '
          '"$filePath"';

      print("========== VİDEO İNDİRME ==========");
      print(
        "Seçilen kalite: "
        "${isQoDActive ? 'YÜKSEK' : 'DÜŞÜK'}",
      );
      print("Yayın adresi: $streamUrl");
      print("Videonun tamamı indiriliyor...");

      final session = await FFmpegKit.execute(command);
      final returnCode = await session.getReturnCode();

      if (ReturnCode.isSuccess(returnCode)) {
        final File videoFile = File(filePath);
        final int fileSize = await videoFile.length();
        final double fileSizeMb = fileSize / (1024 * 1024);

        print("Video başarıyla oluşturuldu: $filePath");
        print("Video boyutu: ${fileSizeMb.toStringAsFixed(2)} MB");

        try {
          bool hasAccess = await Gal.hasAccess();

          if (!hasAccess) {
            await Gal.requestAccess();
          }

          await Gal.putVideo(filePath);
          print("Video galeriye kaydedildi.");
        } catch (galError) {
          // Galeriye kaydetme başarısız olsa bile backend upload devam eder.
          print("Galeri hatası: $galError");
        }

        print("====================================");

        return filePath;
      }

      final output = await session.getOutput();
      final failStackTrace = await session.getFailStackTrace();

      print("FFmpeg çıkışı: $output");
      print("FFmpeg kayıt hatası: $failStackTrace");
      print("====================================");

      return null;
    } catch (error, stackTrace) {
      print("MediaService istisnası: $error");
      print("Stack trace: $stackTrace");

      return null;
    }
  }
}
