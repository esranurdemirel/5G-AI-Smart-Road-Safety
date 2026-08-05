import re
from collections import defaultdict

import cv2
import numpy as np
import pytesseract
from pytesseract import Output

try:
    from fast_plate_ocr import LicensePlateRecognizer
except ImportError:  # Eski/Tesseract kurulumu yine çalışmaya devam etsin.
    LicensePlateRecognizer = None


PLATE_RE = re.compile(
    r"^(0[1-9]|[1-7][0-9]|8[01])([A-Z]{1,3})([0-9]{2,4})$"
)

NUMBER_MAP = str.maketrans({
    "O": "0", "Q": "0", "D": "0", "I": "1", "L": "1",
    "Z": "2", "S": "5", "G": "6", "B": "8",
})
LETTER_MAP = str.maketrans({
    "0": "O", "1": "I", "2": "Z", "5": "S", "6": "G", "8": "B",
})


_FAST_OCR = None
_FAST_OCR_INITIALIZED = False


def _get_fast_plate_ocr():
    """Plakaya özel OCR modelini yalnızca ilk ihtiyaçta bir kez yükler."""
    global _FAST_OCR, _FAST_OCR_INITIALIZED
    if _FAST_OCR_INITIALIZED:
        return _FAST_OCR
    _FAST_OCR_INITIALIZED = True
    if LicensePlateRecognizer is None:
        return None
    try:
        _FAST_OCR = LicensePlateRecognizer("cct-s-v2-global-model")
    except Exception as exc:
        # Model indirilemez/kurulamazsa bütün inference'ı düşürme.
        print(f"[Plaka OCR] Özel OCR yüklenemedi, Tesseract kullanılacak: {exc}")
        _FAST_OCR = None
    return _FAST_OCR


def _clean(text):
    text = text.upper().replace("İ", "I")
    return re.sub(r"[^A-Z0-9]", "", text)


def normalize_turkish_plate(text):
    """OCR metnini 01-81 + 1-3 harf + 2-4 rakam biçiminde doğrular."""
    text = _clean(text)
    if not 5 <= len(text) <= 9:
        return None

    raw_city = text[:2]
    city = raw_city.translate(NUMBER_MAP)
    rest = text[2:]
    candidates = []
    for letter_count in range(1, 4):
        if not 2 <= len(rest) - letter_count <= 4:
            continue
        raw_letters = rest[:letter_count]
        raw_digits = rest[letter_count:]
        letters = raw_letters.translate(LETTER_MAP)
        digits = raw_digits.translate(NUMBER_MAP)
        candidate = city + letters + digits
        if PLATE_RE.fullmatch(candidate):
            # OCR metninin doğal harf/rakam yapısını mümkün olduğunca koru.
            # Örnek: 68FB678 için 68+FB+678 (0 dönüşüm),
            # 68+F+B678 (B->8 dönüşümü) seçeneğinden daha doğrudur.
            substitutions = sum(a != b for a, b in zip(raw_city, city))
            substitutions += sum(a != b for a, b in zip(raw_letters, letters))
            substitutions += sum(a != b for a, b in zip(raw_digits, digits))
            candidates.append((substitutions, candidate))

    if not candidates:
        return None
    candidates.sort(key=lambda item: (item[0], item[1]))
    return candidates[0][1]


def expand_box(xyxy, shape, ratio=0.12):
    h, w = shape[:2]
    x1, y1, x2, y2 = map(float, xyxy)
    pad_x = (x2 - x1) * ratio
    pad_y = (y2 - y1) * ratio
    return (
        max(0, int(x1 - pad_x)),
        max(0, int(y1 - pad_y)),
        min(w, int(x2 + pad_x)),
        min(h, int(y2 + pad_y)),
    )


def _order_points(points):
    points = np.asarray(points, dtype=np.float32)
    ordered = np.zeros((4, 2), dtype=np.float32)
    sums = points.sum(axis=1)
    diffs = np.diff(points, axis=1).reshape(-1)
    ordered[0] = points[np.argmin(sums)]      # sol ust
    ordered[2] = points[np.argmax(sums)]      # sag alt
    ordered[1] = points[np.argmin(diffs)]     # sag ust
    ordered[3] = points[np.argmax(diffs)]     # sol alt
    return ordered


def rectify_plate(crop):
    """Kırpım içindeki en uygun dörtgeni bulursa perspektifi düzeltir."""
    if crop is None or crop.size == 0:
        return crop
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(cv2.GaussianBlur(gray, (3, 3), 0), 50, 180)
    contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    image_area = crop.shape[0] * crop.shape[1]

    for contour in sorted(contours, key=cv2.contourArea, reverse=True)[:15]:
        area = cv2.contourArea(contour)
        if area < image_area * 0.15:
            continue
        perimeter = cv2.arcLength(contour, True)
        polygon = cv2.approxPolyDP(contour, 0.03 * perimeter, True)
        if len(polygon) != 4:
            continue
        points = _order_points(polygon.reshape(4, 2))
        tl, tr, br, bl = points
        width = int(max(np.linalg.norm(br - bl), np.linalg.norm(tr - tl)))
        height = int(max(np.linalg.norm(tr - br), np.linalg.norm(tl - bl)))
        if height < 5 or width / height < 2.0:
            continue
        destination = np.array(
            [[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]],
            dtype=np.float32,
        )
        matrix = cv2.getPerspectiveTransform(points, destination)
        return cv2.warpPerspective(crop, matrix, (width, height))
    return crop


def preprocessing_variants(crop):
    rectified = rectify_plate(crop)
    gray = cv2.cvtColor(rectified, cv2.COLOR_BGR2GRAY)
    target_height = 96
    scale = max(1.0, target_height / max(gray.shape[0], 1))
    gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8)).apply(gray)
    denoised = cv2.bilateralFilter(clahe, 7, 45, 45)
    sharpened = cv2.filter2D(
        denoised, -1, np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    )
    _, otsu = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    adaptive = cv2.adaptiveThreshold(
        denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 31, 7,
    )
    return [gray, clahe, sharpened, otsu, adaptive, cv2.bitwise_not(adaptive)]


def read_plate_candidates(crop):
    """Bir plaka kırpımından (plaka, OCR güveni) adayları döndürür."""
    found = []

    # Genel metin OCR'ından önce plakalar için özel eğitilmiş modeli dene.
    # OpenCV BGR üretir; FastPlateOCR RGB uint8 bekler.
    recognizer = _get_fast_plate_ocr()
    if recognizer is not None:
        try:
            rectified = rectify_plate(crop)
            rgb = cv2.cvtColor(rectified, cv2.COLOR_BGR2RGB)
            prediction = recognizer.run(rgb, return_confidence=True)[0]
            plate = normalize_turkish_plate(prediction.plate)
            if plate:
                probabilities = np.asarray(prediction.char_probs, dtype=np.float32)
                probabilities = probabilities[np.isfinite(probabilities)]
                score = float(probabilities.mean()) if probabilities.size else 0.70
                # Özel modelin oyu güçlüdür; fakat video konsensüsü yine en az
                # iki ayrı kare şartını uygulayacaktır.
                found.extend([(plate, score)] * 4)
        except Exception as exc:
            # Tek bozuk kırpım yüzünden video analizini durdurma.
            print(f"[Plaka OCR] Özel OCR kareyi okuyamadı: {exc}")

    config_base = "-c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    for image in preprocessing_variants(crop):
        for psm in (7, 8, 13):
            data = pytesseract.image_to_data(
                image, config=f"--psm {psm} {config_base}", output_type=Output.DICT
            )
            tokens, confidences = [], []
            for text, confidence in zip(data["text"], data["conf"]):
                token = _clean(text)
                try:
                    confidence = float(confidence)
                except (TypeError, ValueError):
                    confidence = -1.0
                if token:
                    tokens.append(token)
                    if confidence >= 0:
                        confidences.append(confidence / 100.0)
            raw = "".join(tokens)
            plate = normalize_turkish_plate(raw)
            if plate:
                score = float(np.mean(confidences)) if confidences else 0.30
                found.append((plate, score))
    return found


class PlateConsensus:
    """Tek kareye kilitlenmeden video boyunca plaka adaylarını biriktirir."""

    def __init__(self, minimum_frames=2):
        self.minimum_frames = minimum_frames
        self.frames = defaultdict(set)
        self.scores = defaultdict(list)

    def observe(self, frame, frame_index, plate_box, detection_confidence):
        x1, y1, x2, y2 = expand_box(plate_box, frame.shape)
        crop = frame[y1:y2, x1:x2]
        if crop.size == 0:
            return
        for plate, ocr_confidence in read_plate_candidates(crop):
            self.frames[plate].add(int(frame_index))
            self.scores[plate].append(
                0.55 * float(ocr_confidence) + 0.45 * float(detection_confidence)
            )

    def best(self):
        eligible = [
            plate for plate, frames in self.frames.items()
            if len(frames) >= self.minimum_frames
        ]
        if not eligible:
            return "TESPITEDILEMEDI", 0.0
        plate = max(
            eligible,
            # Önce ayrı kare sayısı, sonra farklı ön işlemelerin desteği,
            # en son ortalama güven. Böylece tek bir aşırı güvenli OCR hatası,
            # çoğunluğun okuduğu plakayı ezemez.
            key=lambda value: (
                len(self.frames[value]),
                len(self.scores[value]),
                np.mean(self.scores[value]),
            ),
        )
        repeat_score = min(1.0, len(self.frames[plate]) / 3.0)
        mean_score = float(np.mean(self.scores[plate]))
        confidence = min(1.0, 0.70 * mean_score + 0.30 * repeat_score)
        return plate, round(confidence, 2)
