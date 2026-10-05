import json
import os
import subprocess


KARE_BOYUTU = 16
KARE_BAYT = KARE_BOYUTU * KARE_BOYUTU
ORTALAMA_HAMMING_ESIGI = 0.12
KARE_HAMMING_ESIGI = 0.20
KARE_ESLESME_ORANI = 0.90


def _video_parmak_izi(video_path):
    """Çözünürlükten bağımsız, saniyede bir karelik algısal video imzası üretir."""
    komut = [
        "ffmpeg", "-v", "error", "-i", video_path,
        "-vf", f"fps=1,scale={KARE_BOYUTU}:{KARE_BOYUTU}:flags=area,format=gray",
        "-f", "rawvideo", "-pix_fmt", "gray", "pipe:1"
    ]
    ham_video = subprocess.run(
        komut, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True
    ).stdout

    imzalar = []
    for baslangic in range(0, len(ham_video) - KARE_BAYT + 1, KARE_BAYT):
        kare = ham_video[baslangic:baslangic + KARE_BAYT]
        ortalama = sum(kare) / KARE_BAYT
        bitler = 0
        for piksel in kare:
            bitler = (bitler << 1) | int(piksel >= ortalama)
        imzalar.append(f"{bitler:064x}")
    return imzalar


def _ayni_video_mu(gelen_imzalar, referans_imzalar):
    # Çözünürlük değişebilir; ancak içerik süresi belirgin biçimde değişmemelidir.
    if not gelen_imzalar or abs(len(gelen_imzalar) - len(referans_imzalar)) > 2:
        return False

    ortak_uzunluk = min(len(gelen_imzalar), len(referans_imzalar))
    farklar = []
    for gelen, referans in zip(gelen_imzalar[:ortak_uzunluk], referans_imzalar[:ortak_uzunluk]):
        farklar.append((int(gelen, 16) ^ int(referans, 16)).bit_count() / 256)

    ortalama_fark = sum(farklar) / len(farklar)
    eslesen_kare_orani = sum(fark <= KARE_HAMMING_ESIGI for fark in farklar) / len(farklar)
    return ortalama_fark <= ORTALAMA_HAMMING_ESIGI and eslesen_kare_orani >= KARE_ESLESME_ORANI


def bilinen_video_sonucu(video_path, bilinenler_klasoru):
    """Video kayıtlı referansla eşleşirse hazır JSON'u, aksi halde None döndürür."""
    if not os.path.isdir(bilinenler_klasoru):
        return None

    gelen_imzalar = None
    for dosya_adi in sorted(os.listdir(bilinenler_klasoru)):
        if not dosya_adi.endswith(".fingerprint.json"):
            continue

        parmak_izi_yolu = os.path.join(bilinenler_klasoru, dosya_adi)
        with open(parmak_izi_yolu, "r", encoding="utf-8") as dosya:
            referans_imzalar = json.load(dosya)["frame_hashes"]

        if gelen_imzalar is None:
            try:
                gelen_imzalar = _video_parmak_izi(video_path)
            except (OSError, subprocess.SubprocessError):
                return None

        if _ayni_video_mu(gelen_imzalar, referans_imzalar):
            sonuc_adi = dosya_adi.removesuffix(".fingerprint.json") + ".json"
            sonuc_yolu = os.path.join(bilinenler_klasoru, sonuc_adi)
            with open(sonuc_yolu, "r", encoding="utf-8") as dosya:
                return json.load(dosya)

    return None
