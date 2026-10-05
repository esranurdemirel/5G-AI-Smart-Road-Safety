import 'package:flutter/material.dart';

class AppState extends ChangeNotifier {
  bool _isLoading = false;
  String _statusMessage = "";
  bool _isQoDActive = false;
  Map<String, dynamic>? _aiResults;

  bool get isLoading => _isLoading;
  String get statusMessage => _statusMessage;
  bool get isQoDActive => _isQoDActive;
  Map<String, dynamic>? get aiResults => _aiResults;

  void setLoading(bool loading, {String message = ""}) {
    _isLoading = loading;
    _statusMessage = message;
    notifyListeners();
  }

  void setQoDStatus(bool status) {
    _isQoDActive = status;
    notifyListeners();
  }

  void setAiResults(Map<String, dynamic>? results) {
    _aiResults = results;
    notifyListeners();
  }
}
