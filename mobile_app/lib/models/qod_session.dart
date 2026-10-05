class ModSession {
  final String? sessionId;
  final String? status;
  final int? duration;

  ModSession({this.sessionId, this.status, this.duration});

  factory ModSession.fromJson(Map<String, dynamic> json) {
    return ModSession(
      sessionId: json['sessionId'],
      status: json['status'],
      duration: json['duration'],
    );
  }
}
