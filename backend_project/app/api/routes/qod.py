from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx
from app.core.config import settings

router = APIRouter()

# Flutter'dan gelecek isteğin formatını tanımlıyoruz
class QoDRequest(BaseModel):
    duration: int  # Saniye cinsinden hızlandırma süresi[cite: 4]
    access_token: str # Numara doğrulamada aldığımız giriş anahtarı

@router.post("/")
async def start_quality_on_demand(request: QoDRequest):
    """
    Adım 12-16: Flutter'dan gelen süre bilgisiyle Turkcell ağını hızlandırır[cite: 4].
    """
    headers = {
        "Authorization": f"Bearer {request.access_token}",
        "Content-Type": "application/json"
    }

    # Turkcell'in bizden beklediği veri yapısı (YAML'da ve PDF'te anlatılan kısım)[cite: 4]
    payload = {
        "duration": request.duration,
        "applicationServer": {
            "ipv4Address": "0.0.0.0/0"
        },
        "qosProfile": "teknofest2026"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.OGW_BASE_URL}/quality-on-demand/v1/sessions",
            headers=headers,
            json=payload
        )

        # Turkcell 201 Created dönerse işlem başarılı demektir[cite: 4]
        if response.status_code == 201:
            return {
                "status": "success",
                "message": "İnternet hızlandırma (QoD) başarıyla başlatıldı.",
                "data": response.json()
            }
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Hızlandırma başarısız: {response.text}"
            )