import numpy as np
import cv2
from collections import Counter
import re
import pytesseract

def teknofest_renk_tespiti(arac_kare):
    """
    Araç BBox'ı içindeki pikselleri K-Means ile kümeleyerek
    EN ÇOK BULUNAN (dominant) rengi çıkarır ve TEKNOFEST paletine yuvarlar.
    """
    h, w = arac_kare.shape[:2]
    
    if h < 10 or w < 10:
        return "beyaz"

    # Asfaltın dominant olmasını engellemek için dış kenarlardan %10 tıraşlama
    sy, ey = int(h * 0.1), int(h * 0.9)
    sx, ex = int(w * 0.1), int(w * 0.9)
    islem_karesi = arac_kare[sy:ey, sx:ex]

    img_rgb = cv2.cvtColor(islem_karesi, cv2.COLOR_BGR2RGB)
    pixels = img_rgb.reshape((-1, 3))
    pixels = np.float32(pixels)

    # K-Means ile 3 ana renk kümesine ayırıyoruz
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    K = 3
    _, labels, centers = cv2.kmeans(pixels, K, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)

    # En çok tekrar eden renk kümesini bul
    label_counts = Counter(labels.flatten())
    dominant_label = label_counts.most_common(1)[0][0]
    dominant_rgb = centers[dominant_label]

    # TEKNOFEST Sözlüğündeki Standart Renk Havuzu
    renk_paleti = {
        "beyaz": np.array([240, 240, 240]),
        "siyah": np.array([30, 30, 30]),
        "gri": np.array([128, 128, 128]),
        "kirmizi": np.array([200, 40, 40]),
        "mavi": np.array([40, 60, 200]),
        "sari": np.array([220, 200, 40]),
        "yesil": np.array([40, 150, 40]),
        "turuncu": np.array([220, 120, 30]),
        "kahverengi": np.array([120, 70, 40])
    }

    en_yakin_renk = "beyaz"
    min_mesafe = float('inf')

    for isim, rgb_deger in renk_paleti.items():
        mesafe = np.linalg.norm(dominant_rgb - rgb_deger)
        if mesafe < min_mesafe:
            min_mesafe = mesafe
            en_yakin_renk = isim

    return en_yakin_renk


def kural_motorunu_calistir(ham_kutular, zaman_saniye):
    """
    Kabin İçi Kural Motoru (Sürücü Sağda, Yolcu Solda Açısına Göre)
    Sürücü eylemlerini SADECE sürücü kutusunun içindeyse onaylar.
    """
    anlik_tespitler = []
    
    insanlar = []
    emniyet_kemerleri = []
    diger_aksiyonlar = []
    
    # Sınıfları rollerine göre ayır
    for kutu in ham_kutular:
        lbl = kutu["label"]
        conf = kutu["conf"]
        
        if lbl == "insan":
            if conf >= 0.60: # Güven eşiği
                insanlar.append(kutu)
        elif lbl == "emniyet_kemeri_var":
            emniyet_kemerleri.append(kutu)
        elif lbl in ["arkaya_bakma", "esneme", "etrafa_bakinma", "sigara_icme", "su_icme", "telefonla_konusma"]:
            diger_aksiyonlar.append(kutu)
        elif lbl in ["teknocan", "bilgisayar"]:
            anlik_tespitler.append({
                "zaman_saniye": zaman_saniye,
                "kategori": "nesneler",
                "etiket": lbl,
                "confidence_score": round(conf, 2)
            })

    if not insanlar:
        return anlik_tespitler

    # Merkez koordinatları hesapla
    for i in insanlar:
        x1, y1, x2, y2 = i["bbox"]
        i["cx"] = (x1 + x2) / 2
        i["cy"] = (y1 + y2) / 2
        i["w"] = x2 - x1

    # SÜRÜCÜ SAĞDA: X ekseninde en büyük 'cx' değerine sahip olan sürücüdür.
    sirali_insanlar = sorted(insanlar, key=lambda x: x["cx"], reverse=True)
    surucu = sirali_insanlar[0] 
    
    on_koltuk_yolcusu = None
    arka_koltuk_yolculari = []
    
    kalan_insanlar = sirali_insanlar[1:]
    y_tolerans = 80 

    for insan in kalan_insanlar:
        # Sürücü ile y ekseninde benzer hizada mı?
        if abs(insan["cy"] - surucu["cy"]) <= y_tolerans:
            # Ön koltuk yolcusu onun SOLUNDA (daha küçük cx) olmalıdır
            if insan["cx"] < surucu["cx"]:
                # Sürücünün kendi gövdesini/omzunu çift görmesini engelleme filtresi
                if abs(surucu["cx"] - insan["cx"]) > (surucu["w"] * 0.5):
                    on_koltuk_yolcusu = insan
        else:
            # Hizası uymayanlar arkadadır
            arka_koltuk_yolculari.append(insan)

    # Yolcu tespitlerini yarışma formatına ekle
    if on_koltuk_yolcusu:
        anlik_tespitler.append({
            "zaman_saniye": zaman_saniye,
            "kategori": "yolcular",
            "etiket": "on_koltuk",
            "confidence_score": round(on_koltuk_yolcusu["conf"], 2)
        })
        
    for idx, arka_yolcu in enumerate(arka_koltuk_yolculari):
        etiket_adi = f"arka_koltuk_{idx + 1}" if idx < 2 else "arka_koltuk_2"
        anlik_tespitler.append({
            "zaman_saniye": zaman_saniye,
            "kategori": "yolcular",
            "etiket": etiket_adi,
            "confidence_score": round(arka_yolcu["conf"], 2)
        })

    # --- KUTU İÇERME KONTROLÜ FONKSİYONU ---
    def kutu_icinde_mi(kucuk_box, buyuk_box):
        ix1 = max(kucuk_box[0], buyuk_box[0])
        iy1 = max(kucuk_box[1], buyuk_box[1])
        ix2 = min(kucuk_box[2], buyuk_box[2])
        iy2 = min(kucuk_box[3], buyuk_box[3])
        
        if ix1 < ix2 and iy1 < iy2:
            kesisim_alan = (ix2 - ix1) * (iy2 - iy1)
            kucuk_alan = (kucuk_box[2] - kucuk_box[0]) * (kucuk_box[3] - kucuk_box[1])
            # Küçük kutunun (kemer veya eylem) en az %40'ı büyük kutunun (insan) içindeyse
            if (kesisim_alan / kucuk_alan) > 0.4:
                return True
        return False

    # Emniyet kemeri ihlali sadece SÜRÜCÜ koltuğu için sorgulanır
    surucu_kemer_bulundu = False
    for kemer in emniyet_kemerleri:
        if kutu_icinde_mi(kemer["bbox"], surucu["bbox"]):
            surucu_kemer_bulundu = True
            break
    
    if not surucu_kemer_bulundu:
        anlik_tespitler.append({
            "zaman_saniye": zaman_saniye,
            "kategori": "sofor_eylemi",
            "etiket": "emniyet_kemeri_ihlali",
            "confidence_score": round(surucu["conf"], 2)
        })

    # --- DİĞER SÜRÜCÜ AKSİYONLARI (MEKANSAL FİLTRELEME) ---
    for aksiyon in diger_aksiyonlar:
        # Eğer aksiyon kutusu, SÜRÜCÜ kutusunun içindeyse kaydet
        if kutu_icinde_mi(aksiyon["bbox"], surucu["bbox"]):
            anlik_tespitler.append({
                "zaman_saniye": zaman_saniye,
                "kategori": "sofor_eylemi",
                "etiket": aksiyon["label"],
                "confidence_score": round(aksiyon["conf"], 2)
            })

    return anlik_tespitler


def teknofest_plaka_okuyucu(plaka_resmi):
    import pytesseract
    import re
    import cv2
    import numpy as np

    if plaka_resmi is None or plaka_resmi.size == 0:
        return "TESPITEDILEMEDI"

    try:
        # 1. Ön İşleme
        gray = cv2.cvtColor(plaka_resmi, cv2.COLOR_BGR2GRAY)
        
        # 2. Kontur Analizi
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edged = cv2.Canny(blurred, 30, 200)
        contours, _ = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            largest = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(largest)
            if w > 10 and h > 10:
                gray = gray[y:y+h, x:x+w]

        # 3. İyileştirme
        gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        _, net_resim = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # 4. Tesseract Okuma
        config = '--psm 7 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        text = pytesseract.image_to_string(net_resim, config=config).upper()
        
        # 5. Temizleme ve Yaygın OCR Hatalarını Düzeltme
        clean = re.sub(r'[^A-Z0-9]', '', text)
        clean = clean.replace('O', '0').replace('I', '1').replace('Z', '2').replace('S', '5').replace('B', '8')
        
        # 6. Desen Eşleştirme (Türkiye Plaka Formatı)
        if re.match(r'^\d{2}[A-Z]{1,3}\d{3,4}$', clean):
            return clean
        
        return "TESPITEDILEMEDI"
        
    except:
        return "TESPITEDILEMEDI"
   

def slalom_kontrolu(arac_gecmisi, zaman_saniye, pencere_saniyesi=3.0):
    """
    Doğrusal Regresyon (Linear Regression) tabanlı kusursuz slalom tespiti.
    Aracın gidişatına sanal bir "İdeal Rota" çizer ve sadece bu rotadan belirgin 
    şekilde sağa-sola taşan (zikzak yapan) hareketleri slalom olarak yakalar.
    """
    aktif = [n for n in arac_gecmisi if (zaman_saniye - n[0]) <= pencere_saniyesi]
    
    # Sağlıklı bir rota çizebilmek için en az 1 saniyelik veri (30 kare) birikmeli
    if len(aktif) < 30: 
        return False
        
    import numpy as np
    
    t_degerleri = np.array([n[0] for n in aktif])
    cx_degerleri = np.array([n[1] for n in aktif])
    w_degerleri = np.array([n[3] for n in aktif])
    
    # 1. İDEAL ROTAYI ÇİZ (Line of Best Fit)
    # np.polyfit ile zaman ve x konumu arasındaki en iyi 1. dereceden (düz) çizgiyi buluruz
    egim, kesisim = np.polyfit(t_degerleri, cx_degerleri, 1)
    
    # Bu düz çizgiye göre arabanın normalde olması GEREKEN kusursuz x koordinatları
    ideal_cx = egim * t_degerleri + kesisim
    
    # 2. SAPMALARI HESAPLA (Gerçek konum - İdeal konum)
    # Eğer araç düz gidiyorsa sapmalar 0'a çok yakın (sadece YOLO titremesi) olur
    sapmalar = cx_degerleri - ideal_cx
    
    # YOLO titremelerini yumuşatmak için 5 karelik (hareketli ortalama) filtre uygula
    kernel = np.ones(5) / 5
    yumusak_sapmalar = np.convolve(sapmalar, kernel, mode='valid')
    
    # 3. ZİKZAK SAYIMI
    # Dinamik Eşik: Aracın ortalama genişliğinin %15'i kadar rotadan taşması gerekir
    esik = np.mean(w_degerleri) * 0.15 
    
    durumlar = [] # 1: Rotanın sağına taştı, -1: Rotanın soluna taştı
    
    for sapma in yumusak_sapmalar:
        if sapma > esik:
            # Sadece yeni bir yöne taşıldığında listeye ekle
            if not durumlar or durumlar[-1] != 1:
                durumlar.append(1)
        elif sapma < -esik:
            if not durumlar or durumlar[-1] != -1:
                durumlar.append(-1)
                
    # Eğer rotadan [Sağ, Sol, Sağ] veya [Sol, Sağ, Sol] şeklinde 
    # en az 3 farklı belirgin sapma (2 kırılma) yaşandıysa bu net bir slalomdur!
    if len(durumlar) >= 3:
        arac_gecmisi.clear()
        return True
        
    return False