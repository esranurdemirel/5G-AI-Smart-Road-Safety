import os
import shutil
import json
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, status
from app.core.config import settings
from app.services.ai_service import process_video_with_ai

router = APIRouter()

@router.post("/upload-video", status_code=status.HTTP_202_ACCEPTED)
async def upload_video_for_analysis(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Adım 05: Flutter uygulamasından videoyu alır ve AI analizini başlatır.
    """
    os.makedirs(os.path.dirname(settings.INPUT_VIDEO_PATH), exist_ok=True)

    with open(settings.INPUT_VIDEO_PATH, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    background_tasks.add_task(process_video_with_ai)

    return {
        "status": "accepted",
        "message": "Video başarıyla alındı, yapay zeka analizi arka planda başladı."
    }

@router.get("/results")
async def get_ai_results():
    """
    Adım 06: Flutter uygulaması AI sonuçlarını çekmek için bu adresi sorgular.
    Durumlar: PROCESSING, DONE, FAILED[cite: 3].
    """
    result_file = settings.OUTPUT_JSON_PATH
    video_file = settings.INPUT_VIDEO_PATH

    # DURUM 1: DONE - Eğer results.json varsa, işlem başarıyla bitmiştir
    if os.path.exists(result_file):
        try:
            with open(result_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {
                "status": "DONE",
                "data": data
            }
        except Exception as e:
            return {
                "status": "FAILED",
                "message": f"Sonuç dosyası okunamadı veya format hatalı: {str(e)}"
            }

    # DURUM 2: PROCESSING - Eğer sonuç yok ama yüklenen video duruyorsa, model çalışıyordur
    elif os.path.exists(video_file):
        return {
            "status": "PROCESSING",
            "message": "Al videoyu işliyor..."
        }

    # DURUM 3: FAILED - Hiçbiri yoksa ortada bir video veya analiz süreci yoktur
    else:
        return {
            "status": "FAILED",
            "message": "Sistemde analiz edilecek bir video bulunmuyor."
        }