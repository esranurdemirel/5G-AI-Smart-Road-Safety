import uuid

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services.token_store import get_access_token


router = APIRouter()


class QoDRequest(BaseModel):
    duration: int = Field(default=60, ge=1, le=300)


@router.post("/")
async def start_quality_on_demand(request: QoDRequest):
    """Number Verification token'ıyla QoD oturumu oluşturur."""
    access_token = get_access_token()

    if not access_token:
        raise HTTPException(
            status_code=401,
            detail=(
                "Geçerli Number Verification oturumu bulunamadı veya token "
                "süresi doldu. Numara doğrulamayı yeniden tamamlayın."
            ),
        )

    correlation_id = str(uuid.uuid4())

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "x-correlator": correlation_id,
    }

    payload = {
        "duration": request.duration,
        "applicationServer": {
            "ipv4Address": "0.0.0.0/0"
        },
        "qosProfile": "teknofest2026",
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{settings.OGW_BASE_URL}/quality-on-demand/v1/sessions",
                headers=headers,
                json=payload,
            )
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"QoD servisine bağlanılamadı: {exc}",
        ) from exc

    if response.status_code != 201:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"QoD isteği reddedildi: {response.text}",
        )

    data = response.json()

    return {
        "status": "success",
        "correlationId": correlation_id,
        "data": data,
    }
