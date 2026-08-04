from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.routes import auth, qod, video

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0"
)

# CORS Ayarları - Her yerden gelen isteklere izin veriyoruz
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Mobil app için tüm kaynaklara izin verilir
    allow_credentials=True,
    allow_methods=["*"],  # GET, POST vb. tüm metodlar
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"status": "online", "message": f"{settings.PROJECT_NAME} servisleri çalışıyor."}

# Rotalarımız
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(qod.router, prefix="/api/qod", tags=["QoS"])
app.include_router(video.router, prefix="/api/video", tags=["Video & AI"])