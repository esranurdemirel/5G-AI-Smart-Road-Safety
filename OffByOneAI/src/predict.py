import cv2
import os
from ultralytics import YOLO 
from src.utils import kural_motorunu_calistir, teknofest_renk_tespiti, teknofest_plaka_okuyucu, slalom_kontrolu

def run_inference(video_path, weights_dict):
    """
    3 farklı YOLO modelini koşturarak kararları birleştiren ana fonksiyon.
    İki aşamalı kabin analizi ve dinamik araç/slalom takibi içerir.
    """
    print("[Yükleme] Modeller hafızaya alınıyor...")
    model_arac = YOLO(weights_dict["arac_tipi"])
    model_plaka = YOLO(weights_dict["plaka"])
    model_kabin = YOLO(weights_dict["kabin"])
    
    video_id = os.path.basename(video_path)
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise Exception(f"Video dosyası açılamadı: {video_path}")
        
    fps = cap.get(cv2.DataFrame if hasattr(cv2, 'DataFrame') else cv2.CAP_PROP_FPS)
    if fps == 0:
        fps = 30.0
        
    frame_count = 0
    
    global_arac_bilgisi = {
        "tip": "sedan",
        "plaka": "TESPITEDILEMEDI",
        "renk": "beyaz",
        "confidence_score": 0.50
    }
    
    plaka_gercekten_okundu = False 
    konsolide_tespitler = []
    
    # Slalom tespiti için aracın yatay koordinat geçmişini tutan liste
    arac_gecmisi = []

    print("[Analiz] Video kareleri işleniyor...")
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        frame_count += 1
        zaman_saniye = round(frame_count / fps, 2)
        
        # --- 1. MODEL: ARAÇ Genel Bilgisi ve Slalom Takibi ---
        if frame_count % 5 == 0:
            sonuc_arac = model_arac(frame, verbose=False)[0]
            
            if len(sonuc_arac.boxes) > 0:
                en_iyi_arac = sonuc_arac.boxes[0]
                x1, y1, x2, y2 = en_iyi_arac.xyxy[0].tolist()
                arac_conf = float(en_iyi_arac.conf[0])
               # Slalom analizi için merkez ve genişlik hesapla
                cx = (x1 + x2) / 2
                cy = (y1 + y2) / 2
                w = x2 - x1
                # Dinamik ölçekleme ve detrending için tüm konum/boyut bilgisini sakla
                arac_gecmisi.append((zaman_saniye, cx, cy, w))
                
                # Bağımsız slalom fonksiyonunu çalıştır
                if slalom_kontrolu(arac_gecmisi, zaman_saniye):
                    konsolide_tespitler.append({
                        "zaman_saniye": zaman_saniye,
                        "kategori": "sofor_eylemi",
                        "etiket": "slalom",
                        "confidence_score": round(arac_conf, 2)
                    })
                
                cls_id = int(en_iyi_arac.cls[0])
                arac_tipi = model_arac.names[cls_id]
                
                if arac_conf > global_arac_bilgisi["confidence_score"] or global_arac_bilgisi["plaka"] == "TESPITEDILEMEDI":
                    global_arac_bilgisi["tip"] = arac_tipi
                    global_arac_bilgisi["confidence_score"] = round(arac_conf, 2)
                    
                    arac_resmi = frame[int(y1):int(y2), int(x1):int(x2)]
                    global_arac_bilgisi["renk"] = teknofest_renk_tespiti(arac_resmi)

                if not plaka_gercekten_okundu:
                    sonuc_plaka = model_plaka(frame, verbose=False)[0]
                    if len(sonuc_plaka.boxes) > 0:
                        en_iyi_plaka = sonuc_plaka.boxes[0]
                        px1, py1, px2, py2 = en_iyi_plaka.xyxy[0].tolist()
                        
                        plaka_kesiti = frame[int(py1):int(py2), int(px1):int(px2)]
                        okunan_plaka = teknofest_plaka_okuyucu(plaka_kesiti)
                        if okunan_plaka != "TESPITEDILEMEDI":
                            global_arac_bilgisi["plaka"] = okunan_plaka
                            plaka_gercekten_okundu = True

        # --- 2. MODEL: KABİN İÇİ ("KES VE ARA" MANTIĞI) ---
        ham_kutular = []
        sonuc_kabin_genel = model_kabin(frame, verbose=False)[0]
        insan_kutu_listesi = []
        
        if sonuc_kabin_genel.boxes is not None:
            for box in sonuc_kabin_genel.boxes:
                cls_id = int(box.cls[0])
                label = model_kabin.names[cls_id]
                conf = float(box.conf[0])
                xyxy = box.xyxy[0].tolist()
                
                if label == "insan":
                    insan_kutu_listesi.append(xyxy)
                    ham_kutular.append({"bbox": xyxy, "label": label, "conf": conf})
                elif label in ["teknocan", "bilgisayar"]:
                    ham_kutular.append({"bbox": xyxy, "label": label, "conf": conf})

        for insan_bbox in insan_kutu_listesi:
            ix1, iy1, ix2, iy2 = map(int, insan_bbox)
            ix1, iy1 = max(0, ix1), max(0, iy1)
            ix2, iy2 = min(frame.shape[1], ix2), min(frame.shape[0], iy2)
            
            insan_kesiti = frame[iy1:iy2, ix1:ix2]
            
            if insan_kesiti.size > 0:
                sonuc_aksiyon = model_kabin(insan_kesiti, verbose=False, conf=0.15)[0]
                if sonuc_aksiyon.boxes is not None:
                    for a_box in sonuc_aksiyon.boxes:
                        a_cls = int(a_box.cls[0])
                        a_label = model_kabin.names[a_cls]
                        a_conf = float(a_box.conf[0])
                        a_xyxy = a_box.xyxy[0].tolist()
                        
                        if a_label != "insan" and a_label not in ["teknocan", "bilgisayar"]:
                            gercek_bbox = [
                                a_xyxy[0] + ix1,
                                a_xyxy[1] + iy1,
                                a_xyxy[2] + ix1,
                                a_xyxy[3] + iy1
                            ]
                            ham_kutular.append({
                                "bbox": gercek_bbox,
                                "label": a_label,
                                "conf": a_conf
                            })
        
        anlik_tespitler = kural_motorunu_calistir(ham_kutular, zaman_saniye)
        konsolide_tespitler.extend(anlik_tespitler)

    cap.release()
    
    # Zaman bazlı tespitleri süzme (Event Debouncing)
    zipper_tespitler = []
    son_gorulme = {}
    
    for t in konsolide_tespitler:
        anahtar = (t["kategori"], t["etiket"])
        suanki_zaman = t["zaman_saniye"]
        
        if anahtar not in son_gorulme or (suanki_zaman - son_gorulme[anahtar]) >= 1.0:
            son_gorulme[anahtar] = suanki_zaman
            zipper_tespitler.append(t)

    output_json = {
        "video_id": video_id,
        "arac_bilgisi": global_arac_bilgisi,
        "tespitler": zipper_tespitler
    }
    
    return output_json