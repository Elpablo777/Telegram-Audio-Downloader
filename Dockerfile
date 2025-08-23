# Multi-stage Build für kleinere Images
FROM python:3.11-slim as builder

# Arbeitsverzeichnis setzen
WORKDIR /app

# Build-Abhängigkeiten installieren
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Python-Abhängigkeiten installieren
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Runtime-Stage
FROM python:3.11-slim

# Arbeitsverzeichnis setzen
WORKDIR /app

# Runtime-Abhängigkeiten installieren
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Python-Packages aus Builder kopieren
COPY --from=builder /root/.local /root/.local

# Umgebungsvariablen setzen
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/root/.local/bin:$PATH \
    PYTHONPATH=/app

# Anwendung kopieren
COPY . .

# Paket im Entwicklungsmodus installieren
RUN pip install --no-cache-dir -e .

# Verzeichnisse erstellen
RUN mkdir -p /app/data /app/downloads /app/config

# Gesunder Benutzer (security best practice)
RUN useradd -m -u 1000 telegramuser && \
    chown -R telegramuser:telegramuser /app
USER telegramuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import telegram_audio_downloader; print('OK')" || exit 1

# Standardbefehl
CMD ["telegram-audio-downloader", "--help"]
