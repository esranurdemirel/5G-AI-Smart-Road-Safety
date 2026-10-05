class AppConstants {
  // Ana Sunucu Adresimiz
  static const String baseUrl = "http://34.122.6.67:8080";

  // Turkcell OGW (Open Gateway) Uç Noktaları
  static const String verifyEndpoint = "/api/auth/verify";
  static const String qodEndpoint = "/api/qod/";

  // Video ve Yapay Zeka Uç Noktaları
  static const String uploadVideoEndpoint = "/api/video/upload-video";
  static const String aiResultsEndpoint = "/api/video/results";

  // QoD için yarışma profili
  static const String qodProfile = "teknofest2026";
}
