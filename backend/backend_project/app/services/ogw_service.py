import base64
import httpx
from fastapi import HTTPException
from app.core.config import settings

async def get_access_token(auth_code: str) -> str:
    """
    OGW'den authorization_code kullanarak token alır.
    """
    # 1. client_id ve client_secret birleştirilip Base64 ile kodlanır[cite: 4]
    credentials = f"{settings.OGW_CLIENT_ID}:{settings.OGW_CLIENT_SECRET}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()

    headers = {
        "Authorization": f"Basic {encoded_credentials}",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    # 2. Token alma isteği[cite: 4]
    data = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": settings.OGW_REDIRECT_URI
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.OGW_BASE_URL}/oauth2/token",
            headers=headers,
            data=data
        )

        if response.status_code == 200:
            return response.json().get("access_token")
        else:
            raise HTTPException(status_code=response.status_code, detail="Token alınamadı")
