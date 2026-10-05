import subprocess
import os
from app.core.config import settings

def process_video_with_ai():
    """
    Video yüklendikten sonra arka planda Docker konteynerini tetikler.
    """
    print("[YAPAY ZEKA] İşlem başlatılıyor...")

    # VM üzerindeki gerçek dosya yolunu alıyoruz (Backend'in data klasörü)
    # Bu yol, Docker'ın içindeki /app/data klasörüne bağlanacak (mount)
    host_data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data"))

    # Docker çalıştırma komutu (GPU desteği ile)
    docker_command = [
        "docker", "run", "--rm",
        "--gpus", "all",  # GPU varsa kullanması için
        "-v", f"{host_data_dir}:/app/data", # Klasörleri eşleştiriyoruz
        "teknofest-2026/old-version-test:latest" # Az önce derlediğimiz imaj
    ]

    try:
        # Komutu çalıştır ve bitmesini bekle
        result = subprocess.run(docker_command, capture_output=True, text=True, check=True)
        print("[YAPAY ZEKA] Analiz tamamlandı. Çıktı:")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"[YAPAY ZEKA HATA] Konteyner çalışırken hata oluştu: {e.stderr}")