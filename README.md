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
- 📚 **Persistente Download-Historie** (keine doppelten Downloads)

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
- 🔒 **Proxy-Support** für eingeschränkte Regionen

### **🖥️ Benutzerfreundlichkeit**
- 🌈 **Rich CLI-Interface** mit Farben und Tabellen
- 📊 **Fortschritts-Anzeigen** mit Spinner und Progress-Bars
- 📈 **Performance-Dashboard** mit Echtzeit-Überwachung
- 📋 **Detaillierte Statistiken** und Berichte
- 🐣 **Lite-Modus** für Systeme mit begrenzten Ressourcen

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

# Lite-Modus (weniger Ressourcen)
telegram-audio-downloader download-lite @musikgruppe --limit=10
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

### **YAML-Konfiguration**
Exportieren Sie die aktuelle Konfiguration in eine YAML-Datei:
```bash
telegram-audio-downloader config-export --output config/my_config.yaml
```

### **Proxy-Konfiguration**
Konfigurieren Sie einen Proxy in Ihrer `config.yaml`:
```yaml
proxy:
  type: socks5  # oder http
  host: proxy.example.com
  port: 1080
  username: your_username
  password: your_password
```

---

## 💻 **CLI-Befehle**

### **Download-Befehle**
```bash
# Basis-Download
telegram-audio-downloader download <GRUPPE>

# Download mit Optionen
telegram-audio-downloader download <GRUPPE> --limit=50 --parallel=3 --output=./downloads

# Lite-Modus (weniger Ressourcen, keine Datenbank)
telegram-audio-downloader download-lite <GRUPPE> --limit=10 --no-db --no-metadata

# Konfiguration exportieren
telegram-audio-downloader config-export --output config.yaml
```

### **Suchbefehle**
```bash
# Alle Dateien durchsuchen
telegram-audio-downloader search

# Fuzzy-Suche
telegram-audio-downloader search "beethoven" --fuzzy

# Suche mit Filtern
telegram-audio-downloader search "rock" --format=mp3 --min-size=5MB
```

### **Performance-Befehle**
```bash
# Aktuelle Performance-Statistiken
telegram-audio-downloader performance

# Echtzeit-Monitoring
telegram-audio-downloader performance --watch
```

---

## 🐳 **Docker Support**

### **Docker Compose**
```bash
# Container bauen und starten
docker-compose up --build

# Download-Befehl ausführen
docker-compose exec telegram-audio-downloader telegram-audio-downloader download @musikgruppe

# Lite-Modus
docker-compose exec telegram-audio-downloader telegram-audio-downloader download-lite @musikgruppe
```

### **Volumes und Persistenz**
- `./.env:/app/.env` - API-Zugangsdaten
- `./data:/app/data` - Datenbank und Anwendungsdaten
- `./downloads:/app/downloads` - Heruntergeladene Audiodateien
- `./config:/app/config` - Konfigurationsdateien
- `./logs:/app/logs` - Log-Dateien

Weitere Details finden Sie in [docker/README.md](docker/README.md).

---

## 🐣 **Lite-Modus**

Der Lite-Modus ist für Systeme mit begrenzten Ressourcen gedacht:

```bash
# Lite-Modus mit allen Optionen
telegram-audio-downloader download-lite @musikgruppe --limit=10 --no-db --no-metadata

# Lite-Modus in Docker
docker-compose exec telegram-audio-downloader telegram-audio-downloader download-lite @musikgruppe
```

Vorteile des Lite-Modus:
- Weniger Speicherbedarf
- Keine Datenbank (optional)
- Keine Metadaten-Extraktion (optional)
- Maximal 1 paralleler Download
- Schnellerer Start

---

## 🔒 **Proxy-Support**

Für Benutzer in eingeschränkten Regionen:

1. Konfigurieren Sie den Proxy in Ihrer `config.yaml`:
```yaml
proxy:
  type: socks5
  host: proxy.example.com
  port: 1080
  username: your_username
  password: your_password
```

2. Verwenden Sie den Download-Befehl wie gewohnt:
```bash
telegram-audio-downloader download @musikgruppe
```

---

## 📚 **Persistente Download-Historie**

Das Tool speichert automatisch den Fortschritt pro Gruppe, um doppelte Downloads zu vermeiden:

- Letzte verarbeitete Nachrichten-ID pro Gruppe
- Cache für bereits heruntergeladene Dateien
- Automatische Fortsetzung bei erneutem Start

---

## 🧪 **Tests**

Das Projekt verfügt über umfassende Tests:

```bash
# Unit-Tests ausführen
python -m pytest tests/unit/

# Integrationstests ausführen
python -m pytest tests/integration/

# Alle Tests ausführen
python -m pytest
```

---

## 🤝 **Contributing**

Beiträge sind willkommen! Bitte lesen Sie [CONTRIBUTING.md](CONTRIBUTING.md) für Details.

### **Entwicklungsumgebung einrichten**
```bash
# Abhängigkeiten für Entwicklung installieren
pip install -e ".[dev,test,docs]"

# Pre-commit Hooks installieren
pre-commit install

# Tests ausführen
pytest
```

---

## 📄 **Lizenz**

Dieses Projekt ist unter der MIT-Lizenz lizenziert - siehe [LICENSE](LICENSE) für Details.

---

<div align="center">

**Made with ❤️ für Musikliebhaber weltweit**

[Issues](https://github.com/Elpablo777/telegram-audio-downloader/issues) •
[Pull Requests](https://github.com/Elpablo777/telegram-audio-downloader/pulls) •
[Wiki](https://github.com/Elpablo777/telegram-audio-downloader/wiki)

</div>