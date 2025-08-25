# 🎵 Telegram Audio Downloader

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)
![Platform](https://img.shields.io/badge/Platform-Windows%20|%20Linux%20|%20macOS-lightgrey.svg)

**Ein leistungsstarker, asynchroner Python-Bot zum Herunterladen und Verwalten von Audiodateien aus Telegram-Gruppen**

> 🎵 Sammeln Sie mühelos Ihre Lieblingsmusik aus Telegram-Gruppen mit diesem professionellen Download-Tool!

[Features](#-features) •
[Installation](#-installation) •
[Quick Start](#-quick-start) •
[Dokumentation](#-dokumentation) •
[API](#-api-referenz) •
[Contributing](#-contributing)

</div>

---

## 📋 **Inhaltsverzeichnis**

- [🚀 Features](#-features)
- [📦 Installation](#-installation)
- [⚡ Quick Start](#-quick-start)
- [🔧 Konfiguration](#-konfiguration)
- [💻 CLI-Befehle](#-cli-befehle)
- [🎯 Erweiterte Funktionen](#-erweiterte-funktionen)
- [📊 Performance-Monitoring](#-performance-monitoring)
- [🐳 Docker Support](#-docker-support)
- [🧪 Tests](#-tests)
- [📚 API Referenz](#-api-referenz)
- [🤝 Contributing](#-contributing)
- [📄 Lizenz](#-lizenz)

---

## 🚀 **Features**

### **⚡ Performance & Effizienz**
- 🚀 **Parallele Downloads** mit konfigurierbarer Anzahl (Standard: 3)
- 🎯 **Intelligente Rate-Limiting** mit adaptivem Token-Bucket-Algorithmus
- 🧠 **Memory-Management** mit automatischer Garbage Collection
- 🔄 **Fortsetzbare Downloads** bei Unterbrechungen
- 📈 **Performance-Monitoring** in Echtzeit

### **🎵 Audio-Funktionalitäten**
- 🎼 **Erweiterte Metadaten-Extraktion** (Titel, Künstler, Album, etc.)
- 🔧 **Automatische Dateinamen-Bereinigung**
- 🎶 **Multi-Format-Support**: MP3, FLAC, OGG, M4A, WAV, OPUS
- ✅ **Checksum-Verifikation** für Datenintegrität
- 📝 **ID3-Tags** Extraktion und Verwaltung

### **🔍 Such- & Filter-System**
- 🔎 **Fuzzy-Suche** (toleriert Schreibfehler)
- 🎛️ **Erweiterte Filter**: Größe, Format, Dauer, Gruppe, Status
- 📊 **Volltext-Suche** in Titel, Künstler, Dateinamen
- 📋 **Metadaten-Anzeige** mit Rich-Tables

### **🛡️ Robustheit & Sicherheit**
- 🚧 **FloodWait-Handling** mit adaptiver Rate-Anpassung
- 🔄 **Exponential Backoff** bei Netzwerk-Fehlern
- 📊 **Error-Tracking** mit detaillierter Protokollierung
- 🎯 **Graceful Degradation** bei API-Limits

### **🖥️ Benutzerfreundlichkeit**
- 🌈 **Rich CLI-Interface** mit Farben und Tabellen
- 📊 **Fortschritts-Anzeigen** mit Spinner und Progress-Bars
- 📈 **Performance-Dashboard** mit Echtzeit-Überwachung
- 📋 **Detaillierte Statistiken** und Berichte

---

## 📦 **Installation**

### **Voraussetzungen**
- Python 3.11 oder höher
- Telegram API Credentials (API_ID, API_HASH)
- Git (für Installation aus dem Repository)

### **1. Repository klonen**
```bash
git clone https://github.com/Elpablo777/telegram-audio-downloader.git
cd telegram-audio-downloader
```

### **2. Abhängigkeiten installieren**
```bash
# Virtuelle Umgebung erstellen (empfohlen)
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/macOS

# Abhängigkeiten installieren
pip install -r requirements.txt
```

### **3. Als Paket installieren**
```bash
# Entwicklungsinstallation
pip install -e .

# Oder direkte Installation
pip install .
```

---

## ⚡ **Quick Start**

### **1. Konfiguration**
```bash
# .env-Datei erstellen
cp .env.example .env
```

Bearbeiten Sie die `.env`-Datei:
```env
# Telegram API credentials (von https://my.telegram.org/apps)
API_ID=1234567
API_HASH=your_api_hash_here
SESSION_NAME=my_telegram_session
```

### **2. Ersten Download starten**
```bash
# Audiodateien aus einer Gruppe herunterladen
telegram-audio-downloader download @musikgruppe

# Mit Optionen
telegram-audio-downloader download @musikgruppe --limit=50 --parallel=5 --output=./music
```

### **3. Downloads durchsuchen**
```bash
# Alle heruntergeladenen Dateien anzeigen
telegram-audio-downloader search

# Suche mit Filtern
telegram-audio-downloader search "beethoven" --fuzzy --format=flac --min-size=10MB
```

### **4. Performance überwachen**
```bash
# Einmalige Statistiken
telegram-audio-downloader performance

# Echtzeit-Monitoring
telegram-audio-downloader performance --watch
```

---

## 🔧 **Konfiguration**

### **Umgebungsvariablen (.env)**
```env
# Telegram API (Pflicht)
API_ID=1234567                    # Ihre Telegram API ID
API_HASH=abcdef1234567890         # Ihr Telegram API Hash
SESSION_NAME=telegram_session     # Session-Dateiname

# Optional
DB_PATH=data/downloader.db        # Datenbank-Pfad
MAX_CONCURRENT_DOWNLOADS=3        # Parallele Downloads
DEFAULT_DOWNLOAD_DIR=downloads    # Standard Download-Ordner
LOG_LEVEL=INFO                    # Logging-Level (DEBUG, INFO, WARNING, ERROR)
```

### **Konfigurationsdatei (config/default.ini)**
```ini
[downloads]
max_concurrent = 3
chunk_size = 1048576
retry_attempts = 3
retry_delay = 5

[performance]
max_memory_mb = 1024
rate_limit_requests_per_second = 1.0
rate_limit_burst_size = 5

[metadata]
extract_extended = true
verify_checksums = true
update_id3_tags = true
```

---

## 💻 **CLI-Befehle**

### **Download-Befehle**
```bash
# Basis-Download
telegram-audio-downloader download <GRUPPE>

# Download mit Limit
telegram-audio-downloader download <GRUPPE> --limit <ANZAHL>

# Download in bestimmtes Verzeichnis
telegram-audio-downloader download <GRUPPE> --output <PFAD>

# Parallele Downloads
telegram-audio-downloader download <GRUPPE> --parallel <ANZAHL>
```

### **Such-Befehle**
```bash
# Alle Dateien durchsuchen
telegram-audio-downloader search <SUCHBEGRIFF>

# Suche mit Fuzzy-Matching
telegram-audio-downloader search <SUCHBEGRIFF> --fuzzy

# Suche mit Filtern
telegram-audio-downloader search <SUCHBEGRIFF> --format=mp3 --min-size=5MB
```

### **Batch-Verarbeitung**
```bash
# Download-Auftrag zur Warteschlange hinzufügen
telegram-audio-downloader batch-add --group <GRUPPE> --priority HIGH

# Alle Batch-Aufträge verarbeiten
telegram-audio-downloader batch-process

# Batch-Aufträge auflisten
telegram-audio-downloader batch-list
```

### **Konfigurations-Befehle**
```bash
# Aktuelle Konfiguration anzeigen
telegram-audio-downloader config show

# Konfigurationswert setzen
telegram-audio-downloader config set <SCHLÜSSEL> <WERT>
```

---

## 🎯 **Erweiterte Funktionen**

### **Dateinamen-Vorlagen**
Unterstützt anpassbare Dateinamen-Vorlagen mit Platzhaltern:
- `$title` - Titel des Tracks
- `$artist` - Künstler/Interpret
- `$album` - Albumname
- `$year` - Erscheinungsjahr
- `$genre` - Genre
- `$track_number` - Track-Nummer

Beispiel:
```bash
telegram-audio-downloader download "Gruppe" --filename-template "$artist - $title ($year)"
```

### **Automatische Kategorisierung**
Dateien werden automatisch anhand von Metadaten in Ordner organisiert:
- Nach Künstler
- Nach Album
- Nach Jahr
- Nach Genre

### **Intelligente Warteschlange**
- Priorisierung von Downloads
- Dynamische Ressourcenverteilung
- Fehlerbehandlung und Wiederholung

---

## 📊 **Performance-Monitoring**

Das Tool bietet detaillierte Performance-Metriken:
- Download-Geschwindigkeit in Echtzeit
- Speicherverbrauch
- API-Nutzung
- Fehlerstatistiken

```bash
# Performance-Dashboard starten
telegram-audio-downloader performance --watch
```

---

## 🐳 **Docker Support**

### **Mit Docker bauen**
```bash
docker build -t telegram-audio-downloader .
```

### **Mit Docker ausführen**
```bash
docker run --env-file .env -v ./downloads:/app/downloads telegram-audio-downloader download @musikgruppe
```

### **Mit docker-compose**
```bash
docker-compose up --build
```

---

## 🧪 **Tests**

### **Unit-Tests ausführen**
```bash
python -m pytest tests/
```

### **Tests mit Coverage**
```bash
python -m pytest --cov=src tests/
```

### **Integrationstests**
```bash
python -m pytest tests/test_integration.py
```

---

## 📚 **API Referenz**

### **Hauptklassen**

#### **AudioDownloader**
Die Hauptklasse für das Herunterladen von Audiodateien.

```python
from telegram_audio_downloader import AudioDownloader

downloader = AudioDownloader(
    download_dir="./downloads",
    max_concurrent_downloads=3
)

# Dateien herunterladen
await downloader.download_audio_files("gruppenname")
```

#### **Config**
Zentrale Konfigurationsklasse.

```python
from telegram_audio_downloader import Config

config = Config()
config.set("max_concurrent_downloads", 5)
config.save()
```

---

## 🤝 **Contributing**

Beiträge sind willkommen! Bitte lesen Sie [CONTRIBUTING.md](CONTRIBUTING.md) für Details.

### **Entwicklungsumgebung einrichten**
```bash
# Entwicklungspakete installieren
pip install -e ".[dev]"

# Tests ausführen
python -m pytest

# Code-Qualität prüfen
black --check src/
isort --check-only src/
flake8 src/
mypy src/
```

---

## 📄 **Lizenz**

Dieses Projekt ist unter der MIT-Lizenz lizenziert - siehe die [LICENSE](LICENSE) Datei für Details.

---

## 🙏 **Danksagung**

- [Telethon](https://docs.telethon.dev/) für die leistungsstarke Telegram-Client-Bibliothek
- Allen Mitwirkenden und Unterstützern