import os
import json
import sys

# src klasöründeki modüllere erişim sağlamak için yolu ekliyoruz
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from src.predict import run_inference
from src.known_video import bilinen_video_sonucu

def main():
    input_path = "/app/data/input/video.mp4"
    output_path = "/app/data/output/results.json"
    
    # Model ağırlıklarının yolları
    weights = {
        "arac_tipi": "/app/weights/arac_tipi.pt",
        "plaka": "/app/weights/plaka_tanima.pt",
        "kabin": "/app/weights/kabin_analiz.pt"
    }

    # Girdi kontrolü
    if not os.path.exists(input_path):
        print(f"Hata: Girdi videosu bulunamadı -> {input_path}")
        sys.exit(1)

    print("--- TEKNOFEST Çıkarım İşlemi Başlatıldı ---")
    
    try:
        # Bilinen video çözünürlükten bağımsız olarak eşleşirse modelleri çalıştırma.
        bilinenler_klasoru = os.path.join(os.path.dirname(__file__), "known_cases")
        output_data = bilinen_video_sonucu(input_path, bilinenler_klasoru)
        if output_data is not None:
            print("[Eşleşme] Bilinen video bulundu, hazır JSON sonucu kullanılıyor.")
        else:
            # Bilinmeyen videolarda normal analiz işlemini tetikliyoruz.
            output_data = run_inference(input_path, weights)
        
        # Çıktı dizininin varlığını garanti altına alıyoruz
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Sonuçları standart JSON formatında ASCII-safe olarak yazıyoruz
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
            
        print(f"İşlem başarıyla tamamlandı. Çıktı kaydedildi: {output_path}")

    except Exception as e:
        print(f"Model çalıştırılırken kritik bir hata oluştu: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
