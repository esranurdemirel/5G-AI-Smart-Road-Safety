class AuthResponse {
  final bool devicePhoneNumberVerified;
  final String? error;

  AuthResponse({required this.devicePhoneNumberVerified, this.error});

  factory AuthResponse.fromJson(Map<String, dynamic> json) {
    return AuthResponse(
      devicePhoneNumberVerified: json['devicePhoneNumberVerified'] ?? false,
      error: json['error'],
    );
  }
}
