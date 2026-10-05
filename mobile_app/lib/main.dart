import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'providers/app_state.dart';
import 'routes/app_routes.dart';

void main() {
  runApp(
    // MultiProvider: Uygulama genelinde kullanılacak servisleri ve durumları burada tanımlıyoruz.
    MultiProvider(
      providers: [ChangeNotifierProvider(create: (_) => AppState())],
      child: const TeknofestApp(),
    ),
  );
}

class TeknofestApp extends StatelessWidget {
  const TeknofestApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Teknofest AI Video Analiz',
      debugShowCheckedModeBanner:
          false, // Sağ üstteki çirkin "Debug" yazısını kaldırır
      theme: ThemeData(
        primarySwatch: Colors.blue,
        scaffoldBackgroundColor:
            Colors.grey[50], // Uygulamanın genel arka plan rengi
        appBarTheme: const AppBarTheme(
          elevation: 0,
          centerTitle: true,
          backgroundColor: Colors.white,
          foregroundColor: Colors.black, // Başlık metni rengi
        ),
      ),
      // Uygulamanın hangi sayfa ile başlayacağını ve diğer rotaları belirtiyoruz
      initialRoute: AppRoutes.splash,
      routes: AppRoutes.getRoutes(),
    );
  }
}
