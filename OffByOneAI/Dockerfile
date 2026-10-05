# 1. Adım: Resmi CUDA temel imajını kullanıyoruz
FROM nvidia/cuda:12.1.0-base-ubuntu22.04

# Sistem bağımlılıklarını kuruyoruz (OpenCV ve FFmpeg için gerekli)
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    ffmpeg \
    libsm6 \
    libxext6 \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Python kütüphanelerini buraya ekliyoruz


# Çalışma dizinini belirliyoruz
WORKDIR /app

# Gerekli klasör yapılarını oluşturuyoruz
RUN mkdir -p /app/data/input /app/data/output /app/weights /app/src

# Gereksinimler dosyasını kopyalayıp bağımlılıkları kuruyoruz
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Model ağırlıklarını ve kaynak kodları seçici olarak kopyalıyoruz
COPY weights/ /app/weights/
COPY known_cases/ /app/known_cases/
COPY src/ /app/src/
COPY main.py .
COPY README.md .

# Konteyner ayağa kalktığında çalışacak komut
CMD ["python3", "main.py"]
