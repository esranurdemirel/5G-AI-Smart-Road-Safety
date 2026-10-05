import 'package:flutter/foundation.dart';

class LoggerUtils {
  static void info(String message) {
    if (kDebugMode) {
      print(
        '📘 [BİLGİ] ${DateTime.now().toLocal().toString().split('.')[0]}: $message',
      );
    }
  }

  static void error(String message, [dynamic error]) {
    if (kDebugMode) {
      print(
        '📕 [HATA] ${DateTime.now().toLocal().toString().split('.')[0]}: $message',
      );
      if (error != null) print(error);
    }
  }

  static void success(String message) {
    if (kDebugMode) {
      print(
        '📗 [BAŞARILI] ${DateTime.now().toLocal().toString().split('.')[0]}: $message',
      );
    }
  }
}
