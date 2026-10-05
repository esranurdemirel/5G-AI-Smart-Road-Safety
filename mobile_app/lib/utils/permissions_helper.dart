import 'package:permission_handler/permission_handler.dart';
import 'dart:io';

class PermissionsHelper {
  static Future<bool> requestGalleryPermission() async {
    if (Platform.isAndroid) {
      // Android 13 ve üzeri için photos, daha eskiler için storage izni
      var status = await Permission.photos.request();
      if (status.isGranted) return true;
      var storageStatus = await Permission.storage.request();
      return storageStatus.isGranted;
    } else if (Platform.isIOS) {
      var status = await Permission.photos.request();
      return status.isGranted;
    }
    return false;
  }
}
