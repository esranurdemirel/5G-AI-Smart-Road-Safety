import argparse
import json
from pathlib import Path

import cv2
from ultralytics import YOLO

from src.plate import PlateConsensus, expand_box


def main():
    parser = argparse.ArgumentParser(
        description="Videoda otomatik plaka tespiti/OCR yapar ve işaretli video üretir."
    )
    parser.add_argument("video", help="Test videosunun yolu")
    parser.add_argument(
        "--weights", default="weights/plaka_tanima.pt", help="Plaka modelinin yolu"
    )
    parser.add_argument(
        "--output", default="plaka_video_sonucu.mp4", help="İşaretli çıktı videosu"
    )
    parser.add_argument(
        "--json", default="plaka_video_sonucu.json", help="Özet JSON çıktısı"
    )
    parser.add_argument(
        "--sample-fps", type=float, default=3.0,
        help="Saniyede OCR uygulanacak kare sayısı (varsayılan: 3)",
    )
    args = parser.parse_args()

    video_path = Path(args.video)
    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        raise SystemExit(f"Video açılamadı: {video_path}")

    fps = float(capture.get(cv2.CAP_PROP_FPS))
    if fps <= 0:
        fps = 30.0
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    sample_interval = max(1, round(fps / max(args.sample_fps, 0.1)))

    writer = cv2.VideoWriter(
        args.output,
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (width, height),
    )
    if not writer.isOpened():
        capture.release()
        raise SystemExit(f"Çıktı videosu oluşturulamadı: {args.output}")

    model = YOLO(args.weights)
    consensus = PlateConsensus(minimum_frames=2)
    frame_index = 0
    detection_count = 0
    last_box = None
    last_detection_confidence = 0.0

    print(f"Video: {video_path}")
    print(f"FPS: {fps:.2f}, kare: {total_frames}, OCR örnekleme: {args.sample_fps:.1f} FPS")

    while True:
        ok, frame = capture.read()
        if not ok:
            break

        if frame_index % sample_interval == 0:
            result = model.predict(frame, conf=0.15, iou=0.45, verbose=False)[0]
            if result.boxes is not None and len(result.boxes) > 0:
                best_box = max(result.boxes, key=lambda box: float(box.conf[0]))
                last_detection_confidence = float(best_box.conf[0])
                last_box = expand_box(best_box.xyxy[0].tolist(), frame.shape)
                consensus.observe(
                    frame=frame,
                    frame_index=frame_index,
                    plate_box=best_box.xyxy[0].tolist(),
                    detection_confidence=last_detection_confidence,
                )
                detection_count += 1
            else:
                last_box = None

        plate, consensus_confidence = consensus.best()
        if last_box is not None:
            x1, y1, x2, y2 = last_box
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 3)
            cv2.putText(
                frame,
                f"{plate} | det:{last_detection_confidence:.2f} oy:{consensus_confidence:.2f}",
                (x1, max(28, y1 - 10)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (0, 255, 0),
                2,
                cv2.LINE_AA,
            )

        writer.write(frame)
        frame_index += 1
        if frame_index % max(1, round(fps * 5)) == 0:
            print(f"İşlenen: {frame_index}/{total_frames or '?'} | güncel plaka: {plate}")

    capture.release()
    writer.release()

    plate, confidence = consensus.best()
    summary = {
        "video_id": video_path.name,
        "plaka": plate,
        "confidence_score": confidence,
        "plaka_kutusu_bulunan_ornek_kare": detection_count,
        "destekleyen_kare_sayisi": len(consensus.frames.get(plate, set())),
        "adaylar": {
            candidate: {
                "kare_sayisi": len(consensus.frames[candidate]),
                "ocr_on_isleme_destegi": len(consensus.scores[candidate]),
            }
            for candidate in consensus.frames
        },
    }
    with open(args.json, "w", encoding="utf-8") as file:
        json.dump(summary, file, ensure_ascii=False, indent=2)

    print("\nBitti.")
    print(f"Okunan plaka   : {plate}")
    print(f"Güven          : {confidence:.2f}")
    print(f"İşaretli video : {args.output}")
    print(f"Özet JSON      : {args.json}")


if __name__ == "__main__":
    main()
