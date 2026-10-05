class AiResult {
  final Map<String, dynamic>? aracBilgisi;
  final List<dynamic>? tespitler;
  final String? error;

  AiResult({this.aracBilgisi, this.tespitler, this.error});

  factory AiResult.fromJson(Map<String, dynamic> json) {
    if (json.containsKey('error')) {
      return AiResult(error: json['error']);
    }
    return AiResult(
      aracBilgisi: json['arac_bilgisi'],
      tespitler: json['tespitler'],
    );
  }
}
