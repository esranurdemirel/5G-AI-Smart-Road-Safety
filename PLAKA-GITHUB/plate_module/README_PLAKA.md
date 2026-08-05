# Plaka modülü

Bu klasör ana backend dosyalarını değiştirmeden plaka sistemini ayrı tutar.

## İçerik

- `src/plate.py`: OCR, Türk plaka doğrulaması ve video konsensüsü.
- `weights/plaka_tanima.pt`: Plaka kutusunu bulan YOLO ağırlığı.
- `test_plaka_video.py`: Video testi.
- `test_plaka_gorsel.py`: Görsel testi.
- `requirements_plate.txt`: Bu modülün Python bağımlılıkları.

## Bağımsız test

Repo kökünden:

```bash
python3 -m pip install -r plate_module/requirements_plate.txt
python3 plate_module/test_plaka_video.py "/tam/yol/video.mp4" \
  --weights plate_module/weights/plaka_tanima.pt \
  --output plate_module/sonuc.mp4 \
  --json plate_module/sonuc.json \
  --sample-fps 5
```

## Ana sisteme bağlama

Ana inference kodunda:

```python
from plate_module.src.plate import PlateConsensus
```

Her video/araç örneği için bir konsensüs oluşturulur:

```python
plaka_konsensus = PlateConsensus(minimum_frames=2)
```

YOLO plaka kutusu bulunduğunda `observe(...)`, video sonunda `best()` çağrılır.
Ana backend ile birleştirme ve doğrulama tamamlanmadan mevcut plaka kodu silinmemelidir.

