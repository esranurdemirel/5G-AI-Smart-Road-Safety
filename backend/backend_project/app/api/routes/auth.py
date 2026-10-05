from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse

from app.core.config import settings
from app.services.ogw_service import get_access_token
from app.services.token_store import save_access_token


router = APIRouter()

# Yarışma demosu tek cihaz ve tek worker ile çalışır. Girilen numarayı callback
# aşamasına taşır; mobil uygulamaya client secret veya access token gönderilmez.
pending_phone_number: str | None = None


def normalize_phone_number(phone_number: str) -> str:
    normalized = (
        phone_number.strip()
        .replace(" ", "")
        .replace("-", "")
        .replace("(", "")
        .replace(")", "")
    )
    if normalized.startswith("05") and len(normalized) == 11:
        normalized = "+90" + normalized[1:]
    elif normalized.startswith("5") and len(normalized) == 10:
        normalized = "+90" + normalized

    if (
        not normalized.startswith("+905")
        or len(normalized) != 13
        or not normalized[1:].isdigit()
    ):
        raise HTTPException(
            status_code=400,
            detail="Telefon numarası 05360302810 veya +905360302810 formatında olmalıdır.",
        )
    return normalized


@router.post("/verify")
async def start_verification(phone_number: str = Query(...)):
    global pending_phone_number
    pending_phone_number = normalize_phone_number(phone_number)

    params = {
        "response_type": "code",
        "client_id": settings.OGW_CLIENT_ID,
        "scope": settings.OGW_SCOPES,
        "redirect_uri": settings.OGW_REDIRECT_URI,
    }
    authorize_url = (
        f"{settings.OGW_BASE_URL}/oauth2/authorize?{urlencode(params)}"
    )
    return RedirectResponse(url=authorize_url, status_code=302)


@router.get("/callback")
async def auth_callback(code: str = Query(...)):
    global pending_phone_number
    phone_number = pending_phone_number
    pending_phone_number = None

    if not phone_number:
        raise HTTPException(
            status_code=400,
            detail="Doğrulanacak telefon numarası bulunamadı. Girişi yeniden başlatın.",
        )

    access_token = await get_access_token(auth_code=code)
    if not access_token:
        raise HTTPException(status_code=502, detail="Access token alınamadı.")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            verify_response = await client.post(
                f"{settings.OGW_BASE_URL}/number-verification/v1/verify",
                headers={"Authorization": f"Bearer {access_token}"},
                json={"phoneNumber": phone_number},
            )
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Number Verification servisine bağlanılamadı: {exc}",
        ) from exc

    if verify_response.status_code != 200:
        raise HTTPException(
            status_code=verify_response.status_code,
            detail=verify_response.text,
        )

    result = verify_response.json()
    verified = result.get("devicePhoneNumberVerified") is True

    if verified:
        save_access_token(access_token, expires_in=300)

    return RedirectResponse(
        url=f"smartroad://auth/callback?verified={'true' if verified else 'false'}",
        status_code=302,
    )
