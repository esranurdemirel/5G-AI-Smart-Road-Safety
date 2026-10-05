import 'package:flutter/material.dart';
import '../routes/app_routes.dart';

class DevBypassButton extends StatelessWidget {
  const DevBypassButton({super.key});

  @override
  Widget build(BuildContext context) {
    // Sadece geliştirme aşamasında görünmesi için şık, ufak bir buton
    return TextButton(
      onPressed: () {
        // Girişi başarılı farz edip direkt Ana Ekrana atlar
        Navigator.pushReplacementNamed(context, AppRoutes.home);
      },
      style: TextButton.styleFrom(
        foregroundColor: Colors.orange,
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      ),
      child: const Text(
        "⚡ [DEV] Girişi Atla ve Devam Et",
        style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
      ),
    );
  }
}
