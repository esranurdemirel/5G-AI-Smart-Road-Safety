import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../providers/app_state.dart';
import '../routes/app_routes.dart';
import '../services/api_service.dart';
import '../services/media_service.dart';
import '../services/ogw_service.dart';
import '../widgets/video_player_widget.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final OgwService _ogwService = OgwService();
  final MediaService _mediaService = MediaService();
  final ApiService _apiService = ApiService();

  // Link artık koddan alınmıyor.
  // Yarışmada verilen HLS linki uygulama ekranından girilecek.
  final TextEditingController _hlsUrlController = TextEditingController();

  bool _isVideoStarted = false;
  String? _selectedStreamUrl;

  @override
  void dispose() {
    _hlsUrlController.dispose();
    super.dispose();
  }

  // Ekrandaki HLS linkini alır ve temel doğrulamasını yapar.
  String? _getEnteredHlsUrl() {
    final String value = _hlsUrlController.text.trim();
    final Uri? uri = Uri.tryParse(value);

    final bool validScheme = uri?.scheme == 'http' || uri?.scheme == 'https';

    if (value.isEmpty || uri == null || !uri.hasScheme || !validScheme) {
      _showError("Geçerli bir HLS linki girin.");
      return null;
    }

    return value;
  }

  // QoD işlemini başlatır.
  // Kullanıcının girdiği HLS linkini değiştirmez.
  Future<void> _toggleQoD() async {
    final AppState appState = Provider.of<AppState>(context, listen: false);

    final String? enteredLink = _getEnteredHlsUrl();

    if (enteredLink == null) {
      return;
    }

    appState.setLoading(true, message: "Ağ hızlandırılıyor (QoD)...");

    final Map<String, dynamic>? result = await _ogwService.startQoS();

    if (!mounted) {
      return;
    }

    appState.setLoading(false);

    final String? qosStatus = result?['data']?['qosStatus'] as String?;

    // Yarışma dokümanına göre REQUESTED başarılıdır.
    final bool qodSuccess =
        result?['status'] == 'success' &&
        (qosStatus == 'REQUESTED' || qosStatus == 'AVAILABLE');

    if (qodSuccess) {
      appState.setQoDStatus(true);

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            "QoD isteği başarılı ($qosStatus). "
            "Girilen HLS linki kullanılacak.",
          ),
          backgroundColor: Colors.green,
        ),
      );
    } else {
      appState.setQoDStatus(false);

      final dynamic errorMessage =
          result?['response'] ?? result?['error'] ?? 'Bilinmeyen hata';

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            "QoD başlatılamadı. "
            "Girilen HLS linki normal bağlantıyla kullanılacak. "
            "$errorMessage",
          ),
          backgroundColor: Colors.red,
        ),
      );
    }

    // Link alanına kesinlikle yeni değer yazılmaz.
    // Kullanıcının girdiği yarışma linki korunur.
  }

  // Girilen HLS videosunun tamamını indirir,
  // galeriye kaydeder ve backend'e gönderir.
  Future<void> _uploadAndAnalyze() async {
    final AppState appState = Provider.of<AppState>(context, listen: false);

    final String? enteredStreamUrl = _getEnteredHlsUrl();

    if (enteredStreamUrl == null) {
      return;
    }

    appState.setLoading(
      true,
      message: "Videonun tamamı indiriliyor ve MP4'e çevriliyor...",
    );

    print("========== VİDEO SEÇİMİ ==========");
    print(
      "QoD durumu: "
      "${appState.isQoDActive ? 'BAŞARILI' : 'BAŞARISIZ'}",
    );
    print("Kullanılan HLS linki: $enteredStreamUrl");
    print("===================================");

    // Kullanıcının ekrandan girdiği link doğrudan MediaService'e gider.
    final String? realFilePath = await _mediaService.downloadVideoForBackend(
      enteredStreamUrl,
      appState.isQoDActive,
    );

    if (!mounted) {
      return;
    }

    if (realFilePath == null) {
      appState.setLoading(false);

      _showError("Video indirilemedi veya MP4 formatına çevrilemedi.");
      return;
    }

    appState.setLoading(true, message: "MP4 dosyası backend'e yükleniyor...");

    final bool uploadSuccess = await _apiService.uploadVideoToBackend(
      realFilePath,
    );

    if (!mounted) {
      return;
    }

    if (!uploadSuccess) {
      appState.setLoading(false);
      _showError("Backend'e yükleme başarısız oldu.");
      return;
    }

    appState.setLoading(true, message: "Yapay Zeka (Inference) bekleniyor...");

    await Future.delayed(const Duration(seconds: 4));

    final Map<String, dynamic> results = await _apiService.fetchAiResults();

    if (!mounted) {
      return;
    }

    appState.setAiResults(results);
    appState.setLoading(false);

    Navigator.pushNamed(context, AppRoutes.result);
  }

  // Kullanıcının girdiği HLS linkini oynatır.
  void _startVideo() {
    final String? enteredStreamUrl = _getEnteredHlsUrl();

    if (enteredStreamUrl == null) {
      return;
    }

    setState(() {
      _selectedStreamUrl = enteredStreamUrl;
      _isVideoStarted = true;
    });

    print("Oynatıcı HLS adresi: $enteredStreamUrl");
  }

  void _showError(String message) {
    if (!mounted) {
      return;
    }

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message), backgroundColor: Colors.red),
    );
  }

  @override
  Widget build(BuildContext context) {
    final AppState appState = Provider.of<AppState>(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text(
          "TEKNOFEST 5G Demo",
          style: TextStyle(fontWeight: FontWeight.bold),
        ),
        automaticallyImplyLeading: false,
      ),
      body: Stack(
        children: [
          SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                // Number Verification özeti
                const Card(
                  elevation: 2,
                  child: ListTile(
                    leading: Icon(Icons.verified_user, color: Colors.green),
                    title: Text("Verified Session"),
                    subtitle: Text("Number Verification başarıyla tamamlandı."),
                  ),
                ),

                const SizedBox(height: 16),

                // QoD kartı ve yarışma HLS linki
                Card(
                  elevation: 2,
                  child: Padding(
                    padding: const EdgeInsets.all(12),
                    child: Column(
                      children: [
                        ListTile(
                          contentPadding: EdgeInsets.zero,
                          leading: Icon(
                            appState.isQoDActive
                                ? Icons.network_wifi_3_bar
                                : Icons.signal_wifi_bad,
                            color: appState.isQoDActive
                                ? Colors.blue
                                : Colors.grey,
                          ),
                          title: const Text("Quality-on-Demand"),
                          subtitle: Text(
                            appState.isQoDActive
                                ? "Status: REQUESTED (Aktif)"
                                : "QoD Pasif",
                          ),
                          trailing: ElevatedButton(
                            onPressed:
                                appState.isQoDActive || appState.isLoading
                                ? null
                                : _toggleQoD,
                            style: ElevatedButton.styleFrom(
                              backgroundColor: Colors.purple,
                            ),
                            child: const Text(
                              "QoD Aç",
                              style: TextStyle(color: Colors.white),
                            ),
                          ),
                        ),

                        const SizedBox(height: 8),

                        TextField(
                          controller: _hlsUrlController,
                          keyboardType: TextInputType.url,
                          autocorrect: false,
                          enableSuggestions: false,
                          decoration: const InputDecoration(
                            labelText: "Yarışma HLS linki",
                            hintText: "https://.../video.m3u8",
                            helperText:
                                "Yarışmada verilen HLS linkini buraya yapıştırın.",
                            prefixIcon: Icon(Icons.link),
                            border: OutlineInputBorder(),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),

                const SizedBox(height: 16),

                // HLS oynatıcı kartı
                Card(
                  elevation: 4,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Padding(
                    padding: const EdgeInsets.all(12),
                    child: Column(
                      children: [
                        const Text(
                          "HLS Video Akışı",
                          style: TextStyle(fontWeight: FontWeight.bold),
                        ),

                        const SizedBox(height: 10),

                        Container(
                          height: 200,
                          width: double.infinity,
                          decoration: BoxDecoration(
                            color: Colors.black,
                            borderRadius: BorderRadius.circular(8),
                          ),
                          clipBehavior: Clip.hardEdge,
                          child: _isVideoStarted && _selectedStreamUrl != null
                              ? VideoPlayerWidget(
                                  key: ValueKey(_selectedStreamUrl),
                                  videoUrl: _selectedStreamUrl!,
                                )
                              : Center(
                                  child: IconButton(
                                    icon: const Icon(
                                      Icons.play_circle_fill,
                                      color: Colors.white,
                                      size: 50,
                                    ),
                                    onPressed: _startVideo,
                                  ),
                                ),
                        ),

                        const SizedBox(height: 12),

                        if (_isVideoStarted)
                          ElevatedButton.icon(
                            onPressed: appState.isLoading
                                ? null
                                : _uploadAndAnalyze,
                            icon: const Icon(
                              Icons.cloud_upload,
                              color: Colors.white,
                            ),
                            label: const Text(
                              "Videonun Tamamını Backend'e Gönder",
                              style: TextStyle(color: Colors.white),
                            ),
                            style: ElevatedButton.styleFrom(
                              backgroundColor: Colors.blueAccent,
                              minimumSize: const Size(double.infinity, 50),
                            ),
                          ),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),

          // İndirme, upload ve AI işlemleri sırasında gösterilir.
          if (appState.isLoading)
            Container(
              color: Colors.black87,
              child: Center(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const CircularProgressIndicator(color: Colors.white),

                    const SizedBox(height: 20),

                    Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 20),
                      child: Text(
                        appState.statusMessage,
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 16,
                        ),
                        textAlign: TextAlign.center,
                      ),
                    ),
                  ],
                ),
              ),
            ),
        ],
      ),
    );
  }
}
