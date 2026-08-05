import argparse
from collections import Counter
from pathlib import Path

import cv2
from ultralytics import YOLO

from src.plate import expand_box, read_plate_candidates


def main():
    parser = argparse.ArgumentParser(
        description="Plaka modelini ve OCR sonucunu tek fotoğrafta görsel olarak test eder."
    )
    parser.add_argument("image", help="Test edilecek fotoğrafın yolu")
    parser.add_argument(
        "--weights", default="weights/plaka_tanima.pt", help="Plaka modelinin yolu"
    )
    parser.add_argument(
        "--output", default="plaka_test_sonucu.jpg", help="İşaretli çıktı fotoğrafı"
    )
    args = parser.parse_args()

    image_path = Path(args.image)
    image = cv2.imread(str(image_path))
    if image is None:
        raise SystemExit(f"Fotoğraf açılamadı: {image_path}")

    model = YOLO(args.weights)
    result = model.predict(image, conf=0.15, iou=0.45, verbose=False)[0]
    if result.boxes is None or len(result.boxes) == 0:
        cv2.imwrite(args.output, image)
        raise SystemExit(f"Plaka kutusu bulunamadı. İşaretsiz çıktı: {args.output}")

    best_box = max(result.boxes, key=lambda box: float(box.conf[0]))
    detection_confidence = float(best_box.conf[0])
    x1, y1, x2, y2 = expand_box(best_box.xyxy[0].tolist(), image.shape)
    crop = image[y1:y2, x1:x2]
    cv2.imwrite("plaka_kirpimi.jpg", crop)

    candidates = read_plate_candidates(crop)
    counts = Counter(plate for plate, _ in candidates)
    plate = counts.most_common(1)[0][0] if counts else "TESPITEDILEMEDI"

    cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 3)
    label = f"{plate} | model: {detection_confidence:.2f}"
    text_y = max(30, y1 - 12)
    cv2.putText(
        image, label, (x1, text_y), cv2.FONT_HERSHEY_SIMPLEX,
        0.75, (0, 255, 0), 2, cv2.LINE_AA,
    )
    cv2.imwrite(args.output, image)

    print(f"Plaka kutusu güveni : {detection_confidence:.3f}")
    print(f"OCR adayları        : {dict(counts)}")
    print(f"Seçilen plaka       : {plate}")
    print(f"Plaka kırpımı       : plaka_kirpimi.jpg")
    print(f"İşaretli sonuç      : {args.output}")


if __name__ == "__main__":
    main()
