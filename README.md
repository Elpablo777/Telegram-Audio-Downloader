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
- [🛡️ Sicherheit](#-sicherheit)
- [🛠️ Wartung](#-wartung)
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

### **🔍 Intelligente Suche & Filter**
- 🔍 **Fuzzy-Suche** nach Titel, Künstler, Album
- 🎵 **Metadaten-basierte Filterung** (Genre, Jahr, Dauer)
- 📁 **Automatische Kategorisierung** nach Künstler/Album
- 🏷️ **Tag-basierte Organisation** mit benutzerdefinierten Tags

### **🛠️ Entwicklerfreundlich**
- 🐍 **Asynchrone API** mit modernem Python
- 📖 **Umfangreiche Dokumentation** mit Beispielen
- 🧪 **Über 50 Unit-Tests** für maximale Stabilität
- 🐳 **Docker-Unterstützung** für einfache Bereitstellung
- 📦 **Modulare Architektur** für einfache Erweiterung

---

## 📦 **Installation**

### **🐍 Voraussetzungen**
- Python 3.11 oder neuer
- Telegram API-Zugangsdaten (https://my.telegram.org)
- FFmpeg für Audio-Konvertierung (optional aber empfohlen)

### **📥 Schnellinstallation**

```bash
# Repository klonen
git clone https://github.com/Elpablo777/Telegram-Audio-Downloader.git
cd Telegram-Audio-Downloader

# Virtuelle Umgebung erstellen und aktivieren
python -m venv venv
source venv/bin/activate  # Linux/macOS
# oder
venv\Scripts\activate  # Windows

# Abhängigkeiten installieren
pip install -r requirements.txt
```

### **🐳 Docker Installation (Empfohlen)**

```bash
# Docker-Image bauen
docker-compose build

# Umgebung konfigurieren
cp .env.example .env
# Bearbeiten Sie .env mit Ihren Telegram-Zugangsdaten
```

---

## ⚡ **Quick Start**

### **1. Konfiguration**
Erstellen Sie eine `.env` Datei mit Ihren Telegram-Zugangsdaten:

```env
TELEGRAM_API_ID=ihre_api_id
TELEGRAM_API_HASH=ihre_api_hash
TELEGRAM_PHONE_NUMBER=+491234567890
```

### **2. Erster Download**
```bash
# Einfacher Download
python telegram_audio_downloader.py download --group "meine-musik-gruppe"

# Fortgeschrittene Optionen
python telegram_audio_downloader.py download --group "meine-musik-gruppe" --limit 50 --quality high
```

### **3. Docker Quick Start**
```bash
# Dienst starten
docker-compose up -d

# CLI-Befehl ausführen
docker-compose exec telegram-audio-downloader python telegram_audio_downloader.py download --group "meine-musik-gruppe"
```

---

## 🔧 **Konfiguration**

### **⚙️ Grundlegende Konfiguration**
Die Konfiguration erfolgt über mehrere Ebenen:

1. **.env Datei** (Empfohlen)
```env
# Telegram-Zugangsdaten
TELEGRAM_API_ID=123456
TELEGRAM_API_HASH=abc123def456
TELEGRAM_PHONE_NUMBER=+491234567890

# Download-Einstellungen
DOWNLOAD_PATH=./downloads
MAX_CONCURRENT_DOWNLOADS=3
DEFAULT_QUALITY=high
```

2. **YAML/JSON/INI Konfigurationsdateien**
```yaml
# config/default.yaml
telegram:
  api_id: 123456
  api_hash: abc123def456
  phone_number: "+491234567890"

download:
  path: "./downloads"
  max_concurrent: 3
  quality: "high"
  resume: true
```

### **🌐 Proxy-Konfiguration**
```yaml
# config/proxy.yaml
proxy:
  type: "socks5"
  host: "proxy.example.com"
  port: 1080
  username: "proxy_user"
  password: "proxy_pass"
```

---

## 💻 **CLI-Befehle**

### **📥 Hauptbefehle**
```bash
# Download-Befehle
python telegram_audio_downloader.py download --group GRUPPENNAME
python telegram_audio_downloader.py download --group GRUPPENNAME --limit 100
python telegram_audio_downloader.py download-lite --group GRUPPENNAME  # Reduzierter Ressourcenverbrauch

# Suchbefehle
python telegram_audio_downloader.py search "Suchbegriff"
python telegram_audio_downloader.py search --group GRUPPENNAME "Suchbegriff"

# Verwaltungsbefehle
python telegram_audio_downloader.py list-groups
python telegram_audio_downloader.py status
python telegram_audio_downloader.py history
```

### **🔧 Wartungsbefehle**
```bash
# Datenbank-Operationen
python telegram_audio_downloader.py db optimize
python telegram_audio_downloader.py db cleanup
python telegram_audio_downloader.py db backup

# Cache-Verwaltung
python telegram_audio_downloader.py cache clear
python telegram_audio_downloader.py cache stats

# Konfigurationsprüfung
python telegram_audio_downloader.py config validate
python telegram_audio_downloader.py config show
```

---

## 🎯 **Erweiterte Funktionen**

### **🧠 Intelligente Warteschlange**
- Priorisierte Downloads basierend auf Dateigröße und Audioqualität
- Adaptive Bandbreitenanpassung
- Automatische Fehlerbehandlung und Wiederholung

### **📊 Echtzeit-Monitoring**
- Live-Download-Fortschritt
- Systemressourcenüberwachung
- Performance-Metriken und Statistiken

### **📂 Automatische Organisation**
- Künstler-/Album-basierte Ordnerstruktur
- Metadaten-basierte Dateibenennung
- Duplikaterkennung und -vermeidung

---

## 📊 **Performance-Monitoring**

### **📈 Echtzeit-Metriken**
- Download-Geschwindigkeit
- Speicherverbrauch
- CPU-Auslastung
- Netzwerk-Throughput

### **🗄️ Historische Daten**
- Download-Historie
- Erfolgs-/Fehlerraten
- Performance-Trends

---

## 🐳 **Docker Support**

### **🏗️ Build-Prozess**
```dockerfile
# Multi-stage Build für optimale Image-Größe
FROM python:3.11-slim as builder
# ... Build-Optimierungen ...

FROM python:3.11-slim
# ... Runtime-Konfiguration ...
```

### **🎛️ docker-compose.yml**
```yaml
version: '3.8'
services:
  telegram-audio-downloader:
    build: .
    volumes:
      - ./.env:/app/.env
      - ./downloads:/app/downloads
      - ./data:/app/data
    # ... Weitere Konfiguration ...
```

---

## 🧪 **Tests**

### **✅ Ausführen der Tests**
```bash
# Alle Tests ausführen
pytest

# Spezifische Testgruppe
pytest tests/test_basic_download.py

# Testabdeckung
pytest --cov=src

# Integrationstests
pytest tests/test_integration.py
```

### **🛠️ Testinfrastruktur**
- Unit-Tests für alle Kernfunktionen
- Integrationstests für Telegram-API
- Performance-Tests
- Sicherheitstests

---

## 📚 **API Referenz**

### **📦 Hauptklassen**

#### **AudioDownloader**
```python
from telegram_audio_downloader import AudioDownloader

downloader = AudioDownloader(config_path="config.yaml")
await downloader.download_group("meine-gruppe", limit=50)
```

#### **Configuration**
```python
from telegram_audio_downloader.config import Config

config = Config("config.yaml")
api_id = config.get("telegram.api_id")
```

### **🔧 Hilfsfunktionen**
- `get_client()` - Telegram-Client erstellen
- `download_file()` - Einzelne Datei herunterladen
- `extract_metadata()` - Audio-Metadaten extrahieren

---

## 🤝 **Contributing**

### **📋 Voraussetzungen**
1. Python 3.11+
2. Telegram API-Zugangsdaten für Tests
3. FFmpeg installiert

### **🏗️ Entwicklungsumgebung**
```bash
# Virtuelle Umgebung erstellen
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate  # Windows

# Entwicklungsabhängigkeiten installieren
pip install -r requirements_dev.txt

# Pre-Commit-Hooks installieren
pre-commit install
```

### **🧪 Tests ausführen**
```bash
# Stilprüfung
flake8 src tests

# Typüberprüfung
mypy src

# Sicherheitsprüfung
bandit -r src

# Alle Tests
pytest
```

### **📦 Pull Request Richtlinien**
1. Erstellen Sie einen Feature-Branch
2. Fügen Sie Tests für neue Funktionen hinzu
3. Aktualisieren Sie die Dokumentation
4. Führen Sie alle Tests erfolgreich aus
5. Verwenden Sie aussagekräftige Commit-Nachrichten

---

## 🛡️ **Sicherheit**

### **🔐 Sicherheitspraktiken**
- Keine hartkodierten Geheimnisse
- Sichere Dateiberechtigungen
- Regelmäßige Abhängigkeitsaktualisierungen
- Automatisierte Sicherheitsprüfungen

### **🛠️ Sicherheitswerkzeuge**
```bash
# Sicherheitsprüfung ausführen
python scripts/security_fix.py
python check_security.py

# Abhängigkeiten scannen
safety check -r requirements.txt
```

### **🛡️ Sicherheitsfeatures**
- API-Schlüssel-Verschlüsselung
- Rate-Limiting für API-Anfragen
- Automatische Session-Invalidierung
- Sichere Fehlerbehandlung

---

## 🛠️ **Wartung**

### **🧹 Automatisierte Wartung**
Das Projekt enthält professionelle Wartungsskripte im `scripts/` Verzeichnis:

1. **PR Cleanup** - Überprüfung und Bewertung von Pull Requests
2. **Security Fix** - Automatische Behebung von Sicherheitsproblemen
3. **Changelog Update** - Automatische Aktualisierung des Änderungsprotokolls

```bash
# PR-Überprüfung durchführen
python scripts/pr_cleanup.py

# Sicherheitsprobleme beheben
python scripts/security_fix.py

# Changelog aktualisieren
python scripts/update_changelog.py 1.2.0
```

### **🔄 Regelmäßige Wartungsaufgaben**
- Abhängigkeitsaktualisierungen
- Sicherheitsprüfungen
- Performance-Optimierungen
- Dokumentationsaktualisierungen

---

## 📄 **Lizenz**

Dieses Projekt ist unter der MIT-Lizenz lizenziert - siehe die [LICENSE](LICENSE) Datei für Details.

---

<div align="center">

**🎉 Danke, dass Sie den Telegram Audio Downloader verwenden!**

 Wenn Sie Probleme finden oder Verbesserungen vorschlagen möchten, [erstellen Sie ein Issue](https://github.com/Elpablo777/Telegram-Audio-Downloader/issues) oder senden Sie einen [Pull Request](https://github.com/Elpablo777/Telegram-Audio-Downloader/pulls).

</div>