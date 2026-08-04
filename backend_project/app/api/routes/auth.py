from fastapi import APIRouter, Query
from fastapi.responses import RedirectResponse
import httpx
from app.core.config import settings
from app.services.ogw_service import get_access_token

router = APIRouter()

@router.post("/verify")
async def start_verification(phone_number: str):
    """
    Adım 2 & 3: Flutter numarayı gönderir, Backend OGW yetkilendirme sayfasına yönlendirir[cite: 4].
    """
    # 302 Redirect için OGW authorize URL'sini hazırlıyoruz[cite: 4]
    authorize_url = (
        f"{settings.OGW_BASE_URL}/authorize"
        f"?response_type=code"
        f"&client_id={settings.OGW_CLIENT_ID}"
        f"&scope={settings.OGW_SCOPES}"
        f"&redirect_uri={settings.OGW_REDIRECT_URI}"
    )
    return RedirectResponse(url=authorize_url, status_code=302)

@router.get("/callback")
async def auth_callback(code: str = Query(..., alias="operator_auth_code")):
    """
    Adım 5 & 6: OGW kullanıcıyı onaylayıp bu adrese operator_auth_code ile yönlendirir[cite: 4].
    """
    # Adım 7 & 8: Code'u kullanarak access_token al[cite: 4]
    access_token = await get_access_token(auth_code=code)

    # Adım 9: Token ile numara doğrulama isteği at[cite: 4]
    verify_headers = {
        "Authorization": f"Bearer {access_token}"
    }

    # Not: Gerçek senaryoda telefon numarası session/cache'ten alınmalıdır.
    async with httpx.AsyncClient() as client:
        verify_response = await client.post(
            f"{settings.OGW_BASE_URL}/number-verification/v1/verify",
            headers=verify_headers,
            json={"phoneNumber": "+905390000020"} # Örnek numara
        )

        # Adım 10: Doğrulama sonucunu dön[cite: 4]
        return verify_response.json()