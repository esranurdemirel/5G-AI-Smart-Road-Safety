import time


_access_token: str | None = None
_expires_at: float = 0.0


def save_access_token(access_token: str, expires_in: int = 300) -> None:
    """Open Gateway token'ını yalnızca backend belleğinde saklar."""
    global _access_token, _expires_at
    _access_token = access_token
    # Ağ gecikmesi için token süresinden 10 saniye güvenlik payı bırak.
    _expires_at = time.time() + max(0, expires_in - 10)


def get_access_token() -> str | None:
    """Geçerli token'ı döndürür; süresi bittiyse temizler."""
    global _access_token, _expires_at
    if not _access_token or time.time() >= _expires_at:
        _access_token = None
        _expires_at = 0.0
        return None
    return _access_token
