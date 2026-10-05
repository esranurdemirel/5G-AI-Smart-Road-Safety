import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:share_plus/share_plus.dart';
import 'dart:convert';
import 'dart:typed_data';
import '../providers/app_state.dart';
import '../services/api_service.dart';

class ResultScreen extends StatefulWidget {
  const ResultScreen({super.key});

  @override
  State<ResultScreen> createState() => _ResultScreenState();
}

class _ResultScreenState extends State<ResultScreen> {
  final ApiService _apiService = ApiService();
  bool _isRefreshing = false;

  // Sağ üstteki yenile butonunun fonksiyonu
  Future<void> _refreshResults() async {
    setState(() {
      _isRefreshing = true;
    });

    final appState = Provider.of<AppState>(context, listen: false);
    final newResults = await _apiService.fetchAiResults();
    appState.setAiResults(newResults);

    setState(() {
      _isRefreshing = false;
    });
  }

  Future<void> _saveJson(Map<String, dynamic> rawJson) async {
    final String jsonText = const JsonEncoder.withIndent('  ').convert(rawJson);
    final Uint8List bytes = Uint8List.fromList(utf8.encode(jsonText));

    await SharePlus.instance.share(
      ShareParams(
        files: [XFile.fromData(bytes, mimeType: 'application/json')],
        fileNameOverrides: const ['results.json'],
        title: 'JSON sonucunu kaydet',
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final appState = Provider.of<AppState>(context);
    final results = appState.aiResults;

    // Hata durumu kontrolü (FAILED)
    final bool hasError = results == null || results.containsKey('error');

    // Başarılı durum (DONE) değişkenleri
    final Map<String, dynamic>? aracBilgisi = hasError
        ? null
        : results['arac_bilgisi'];
    final List<dynamic>? tespitler = hasError ? null : results['tespitler'];

    return Scaffold(
      appBar: AppBar(
        title: const Text(
          "Yapay Zeka Analiz Sonucu",
          style: TextStyle(fontWeight: FontWeight.bold),
        ),
        actions: [
          IconButton(
            icon: _isRefreshing
                ? const SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(
                      color: Colors.white,
                      strokeWidth: 2,
                    ),
                  )
                : const Icon(Icons.refresh),
            onPressed: _isRefreshing ? null : _refreshResults,
            tooltip: 'Sonuçları Yenile',
          ),
        ],
      ),
      body: hasError
          ? _buildErrorView(results?['error'] ?? "Sonuçlar alınamadı.")
          : _buildSuccessView(aracBilgisi, tespitler, results),
    );
  }

  // --- HATA GÖRÜNÜMÜ (FAILED) ---
  Widget _buildErrorView(String errorMessage) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.error_outline, color: Colors.red, size: 60),
          const SizedBox(height: 16),
          const Text(
            "FAILED",
            style: TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.bold,
              color: Colors.red,
            ),
          ),
          const SizedBox(height: 8),
          Text(errorMessage, style: const TextStyle(color: Colors.grey)),
        ],
      ),
    );
  }

  // --- BAŞARILI GÖRÜNÜM (DONE) ---
  Widget _buildSuccessView(
    Map<String, dynamic>? aracBilgisi,
    List<dynamic>? tespitler,
    Map<String, dynamic> rawJson,
  ) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // 1. Araç Kartı (Araç Bilgisi)
          if (aracBilgisi != null) ...[
            const Text(
              "Araç Bilgisi",
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
                color: Colors.blueAccent,
              ),
            ),
            const SizedBox(height: 8),
            Card(
              elevation: 3,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
              ),
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  children: [
                    _buildInfoRow(
                      "Tip",
                      aracBilgisi['tip']?.toString().toUpperCase() ??
                          "BİLİNMİYOR",
                    ),
                    const Divider(),
                    _buildInfoRow(
                      "Plaka",
                      aracBilgisi['plaka']?.toString() ?? "BİLİNMİYOR",
                    ),
                    const Divider(),
                    _buildInfoRow(
                      "Renk",
                      aracBilgisi['renk']?.toString().toUpperCase() ??
                          "BİLİNMİYOR",
                    ),
                    const Divider(),
                    _buildInfoRow(
                      "Güven Skoru",
                      "%${((aracBilgisi['confidence_score'] ?? 0) * 100).toStringAsFixed(1)}",
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 24),
          ],

          // 2. Tespit Listesi (İhlaller vb.)
          if (tespitler != null && tespitler.isNotEmpty) ...[
            const Text(
              "Tespitler (Olaylar)",
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
                color: Colors.redAccent,
              ),
            ),
            const SizedBox(height: 8),
            ListView.builder(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              itemCount: tespitler.length,
              itemBuilder: (context, index) {
                final tespit = tespitler[index];
                return Card(
                  margin: const EdgeInsets.only(bottom: 10),
                  child: ListTile(
                    leading: const CircleAvatar(
                      backgroundColor: Colors.redAccent,
                      child: Icon(Icons.warning, color: Colors.white),
                    ),
                    title: Text(
                      tespit['etiket']
                              ?.toString()
                              .replaceAll('_', ' ')
                              .toUpperCase() ??
                          "BİLİNMEYEN OLAY",
                    ),
                    subtitle: Text(
                      "Kategori: ${tespit['kategori']}\nZaman: ${tespit['zaman_saniye']} sn",
                    ),
                    trailing: Text(
                      "%${((tespit['confidence_score'] ?? 0) * 100).toStringAsFixed(0)}",
                      style: const TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 16,
                      ),
                    ),
                    isThreeLine: true,
                  ),
                );
              },
            ),
            const SizedBox(height: 24),
          ],

          // 3. Ham JSON Görünümü (Raw JSON)
          const Text(
            "Geliştirici Görüntüsü",
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
              color: Colors.grey,
            ),
          ),
          const SizedBox(height: 8),
          ElevatedButton.icon(
            onPressed: () => _saveJson(rawJson),
            icon: const Icon(Icons.download),
            label: const Text("JSON'u Telefona Kaydet"),
          ),
          const SizedBox(height: 8),
          ExpansionTile(
            title: const Text("Ham JSON (results.json)"),
            collapsedBackgroundColor: Colors.grey.shade200,
            children: [
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(12),
                color: Colors.black87,
                child: SelectableText(
                  const JsonEncoder.withIndent('  ').convert(rawJson),
                  style: const TextStyle(
                    fontFamily: 'monospace',
                    color: Colors.greenAccent,
                    fontSize: 12,
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  // Yardımcı widget: Araç kartı içindeki satırlar için
  Widget _buildInfoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4.0),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            label,
            style: const TextStyle(
              fontWeight: FontWeight.w600,
              color: Colors.grey,
            ),
          ),
          Text(
            value,
            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
          ),
        ],
      ),
    );
  }
}
