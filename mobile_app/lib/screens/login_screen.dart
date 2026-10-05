import 'dart:async';

import 'package:app_links/app_links.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:url_launcher/url_launcher.dart'; // 🟢 LİNK AÇMAK İÇİN EKLENDİ
import '../providers/app_state.dart';
import '../services/ogw_service.dart';
import '../routes/app_routes.dart';
import '../widgets/dev_bypass_button.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final AppLinks _appLinks = AppLinks();
  StreamSubscription<Uri>? _linkSubscription;

  // Yarışma için verilen SIM numarası.
  final TextEditingController _phoneController = TextEditingController(
    text: "+905360302810",
  );
  final OgwService _ogwService = OgwService();

  String? _errorMessage;
  String? _connectionLogs;

  @override
  void initState() {
    super.initState();
    _listenForAuthCallback();
  }

  void _listenForAuthCallback() {
    _linkSubscription = _appLinks.uriLinkStream.listen(
      (Uri uri) {
        if (uri.scheme != 'smartroad' ||
            uri.host != 'auth' ||
            uri.path != '/callback') {
          return;
        }

        final bool verified = uri.queryParameters['verified'] == 'true';

        if (!mounted) return;

        if (verified) {
          Navigator.pushReplacementNamed(context, AppRoutes.home);
        } else {
          setState(() {
            _errorMessage = 'Sign-in failed';
            _connectionLogs =
                'Number Verification sonucu doğrulanamadı.';
          });
        }
      },
      onError: (Object error) {
        if (!mounted) return;
        setState(() {
          _errorMessage = 'Uygulamaya dönüş başarısız';
          _connectionLogs = error.toString();
        });
      },
    );
  }

  @override
  void dispose() {
    _linkSubscription?.cancel();
    _phoneController.dispose();
    super.dispose();
  }

  Future<void> _handleLogin() async {
    final appState = Provider.of<AppState>(context, listen: false);
    appState.setLoading(true, message: "Numara doğrulanıyor...");

    setState(() {
      _errorMessage = null;
      _connectionLogs = null;
    });

    // Arka planda şebeke doğrulaması (Number Verify)
    final response = await _ogwService.verifyNumber(_phoneController.text);

    appState.setLoading(false);

    // 🟢 1. DURUM: 302 YÖNLENDİRMESİ GELDİ (Turkcell Onay Sayfası)
    if (response != null && response["status"] == 302) {
      final String? turkcellLink = response["url"];

      if (turkcellLink == null || turkcellLink.isEmpty) {
        setState(() {
          _errorMessage = "Link bulunamadı!";
          _connectionLogs = "Sunucu yönlendirme linki göndermedi.";
        });
        return;
      }

      final Uri url = Uri.parse(turkcellLink);

      try {
        // Android 11 güvenlik engeline takılmamak için 'canLaunchUrl' sormadan DİREKT AÇIYORUZ:
        await launchUrl(url, mode: LaunchMode.externalApplication);
      } catch (e) {
        setState(() {
          _errorMessage = "Tarayıcı açılamadı!";
          _connectionLogs = "Geçersiz Link: $turkcellLink \nHata Detayı: $e";
        });
      }
    }
    // 🟢 2. DURUM: DOĞRUDAN BAŞARILI DÖNDÜ (200 OK)
    else if (response != null &&
        response['devicePhoneNumberVerified'] == true) {
      if (mounted) {
        Navigator.pushReplacementNamed(context, AppRoutes.home);
      }
    }
    // 🟢 3. DURUM: HATA VEYA DOĞRULAMA BAŞARISIZ
    else {
      setState(() {
        _errorMessage = "Sign-in failed";
        _connectionLogs =
            "POST /api/auth/verify\nStatus: Failed\nResponse: $response\nTime: ${DateTime.now()}";
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final isLoading = Provider.of<AppState>(context).isLoading;

    return Scaffold(
      body: SafeArea(
        // 🟢 TASARIM HATASINI ÇÖZEN KISIM: Ekranı kaydırılabilir yaptık (Klavye taşmasını engeller)
        child: SingleChildScrollView(
          child: Padding(
            padding: const EdgeInsets.all(24.0),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const SizedBox(height: 40), // Yukarıdan biraz boşluk bırakalım
                // --- DEV BYPASS BUTONU EN ÜSTTE ---
                const DevBypassButton(),
                const SizedBox(height: 20),
                // -------------------------
                const Text(
                  "VERIFY YOUR NUMBER",
                  style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 10),
                const Text(
                  "Mobil ağ üzerinden şifresiz giriş yapın.",
                  textAlign: TextAlign.center,
                  style: TextStyle(color: Colors.grey),
                ),
                const SizedBox(height: 40),
                TextField(
                  controller: _phoneController,
                  decoration: const InputDecoration(
                    labelText: "Telefon Numarası (MSISDN)",
                    border: OutlineInputBorder(),
                    prefixIcon: Icon(Icons.phone),
                  ),
                  keyboardType: TextInputType.phone,
                ),
                const SizedBox(height: 24),
                ElevatedButton(
                  onPressed: isLoading ? null : _handleLogin,
                  style: ElevatedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    backgroundColor: Colors.blueAccent,
                  ),
                  child: isLoading
                      ? const SizedBox(
                          height: 20,
                          width: 20,
                          child: CircularProgressIndicator(
                            color: Colors.white,
                            strokeWidth: 2,
                          ),
                        )
                      : const Text(
                          "Sign In",
                          style: TextStyle(fontSize: 18, color: Colors.white),
                        ),
                ),
                // Hata durumu için Connection Logs Kartı
                if (_errorMessage != null) ...[
                  const SizedBox(height: 20),
                  Text(
                    _errorMessage!,
                    style: const TextStyle(
                      color: Colors.red,
                      fontWeight: FontWeight.bold,
                    ),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 10),
                  ExpansionTile(
                    title: const Text(
                      "Connection Logs",
                      style: TextStyle(color: Colors.red),
                    ),
                    iconColor: Colors.red,
                    collapsedIconColor: Colors.red,
                    children: [
                      Container(
                        padding: const EdgeInsets.all(12.0),
                        color: Colors.grey[200],
                        width: double.infinity,
                        child: Text(
                          _connectionLogs ?? "Bilinmeyen Hata",
                          style: const TextStyle(
                            fontFamily: 'monospace',
                            fontSize: 12,
                          ),
                        ),
                      ),
                    ],
                  ),
                ],
              ],
            ),
          ),
        ),
      ),
    );
  }
}
