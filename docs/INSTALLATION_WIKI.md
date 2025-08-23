# 📦 Installation Guide

Willkommen zum ausführlichen Installationsguide für den Telegram Audio Downloader!

## 🎯 **Überblick**

Es gibt mehrere Wege, den Telegram Audio Downloader zu installieren:
- **Entwicklungsinstallation** (für Entwickler)
- **Benutzerinstallation** (für Endanwender)
- **Docker-Installation** (empfohlen für Production)

---

## 🔧 **Voraussetzungen**

### **System-Anforderungen**
- **Betriebssystem**: Windows 10+, Linux (Ubuntu 20.04+), macOS 10.15+
- **Python**: 3.11 oder höher
- **Speicher**: Mindestens 512 MB RAM, empfohlen 2 GB
- **Festplatte**: 1 GB für das System + Platz für Downloads

### **Erforderliche Software**
```bash
# Python-Version prüfen
python --version  # Sollte >= 3.11 sein

# Git installieren (falls nicht vorhanden)
# Windows: https://git-scm.com/download/win
# Linux: sudo apt install git
# macOS: xcode-select --install
```

---

## 📥 **Methode 1: Schnellinstallation für Benutzer**

### **Schritt 1: Repository klonen**
```bash
git clone https://github.com/Elpablo777/Telegram-Audio-Downloader.git
cd Telegram-Audio-Downloader
```

### **Schritt 2: Virtuelle Umgebung erstellen**
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python -m venv venv
source venv/bin/activate
```

### **Schritt 3: Abhängigkeiten installieren**
```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
```

### **Schritt 4: Konfiguration**
```bash
# .env-Datei erstellen
cp .env.example .env

# .env-Datei bearbeiten (wichtig!)
# API_ID=Ihre_Telegram_API_ID
# API_HASH=Ihre_Telegram_API_Hash
```

**Telegram API Credentials erhalten:**
1. Gehen Sie zu https://my.telegram.org/apps
2. Loggen Sie sich mit Ihrer Telefonnummer ein
3. Erstellen Sie eine neue App
4. Notieren Sie API_ID und API_HASH

### **Schritt 5: Installation testen**
```bash
telegram-audio-downloader --help
```

---

## 🐳 **Methode 2: Docker-Installation (Empfohlen)**

### **Voraussetzungen**
- Docker und Docker Compose installiert
- Git installiert

### **Schnelle Docker-Installation**
```bash
# Repository klonen
git clone https://github.com/Elpablo777/Telegram-Audio-Downloader.git
cd Telegram-Audio-Downloader

# .env-Datei konfigurieren
cp .env.example .env
# API_ID und API_HASH eintragen

# Container starten
docker-compose up -d

# Tool verwenden
docker-compose exec telegram-audio-downloader telegram-audio-downloader --help
```

### **Direkter Docker-Build**
```bash
# Image builden
docker build -t telegram-audio-downloader .

# Container starten
docker run -it --rm \
  -v $(pwd)/downloads:/app/downloads \
  -v $(pwd)/.env:/app/.env \
  telegram-audio-downloader \
  telegram-audio-downloader --help
```

---

## 🛠️ **Methode 3: Entwicklungsinstallation**

### **Für Contributors und Entwickler**
```bash
# Repository forken und klonen
git clone https://github.com/IHR-USERNAME/Telegram-Audio-Downloader.git
cd Telegram-Audio-Downloader

# Development-Environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Development-Abhängigkeiten
pip install -e ".[dev]"

# Pre-commit hooks (optional)
pre-commit install

# Tests ausführen
pytest
```

---

## ⚡ **Schnellstart**

Nach der Installation können Sie sofort loslegen:

```bash
# Erste Gruppe durchsuchen
telegram-audio-downloader download @musikgruppe

# Mit erweiterten Optionen
telegram-audio-downloader download @gruppe \
  --limit=50 \
  --parallel=5 \
  --output=./music

# Downloads durchsuchen
telegram-audio-downloader search "beatles" --fuzzy

# Performance überwachen
telegram-audio-downloader performance --watch
```

---

## 🔧 **Konfiguration**

### **.env-Datei Beispiel**
```env
# Telegram API (Pflicht)
API_ID=1234567
API_HASH=abcdef1234567890abcdef1234567890
SESSION_NAME=my_telegram_session

# Optional
DB_PATH=data/downloader.db
MAX_CONCURRENT_DOWNLOADS=3
DEFAULT_DOWNLOAD_DIR=downloads
LOG_LEVEL=INFO
```

### **config/default.ini**
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

## 🧪 **Installation verifizieren**

### **Grundlegende Tests**
```bash
# Version prüfen
telegram-audio-downloader --version

# Hilfe anzeigen
telegram-audio-downloader --help

# Konfiguration testen
telegram-audio-downloader groups

# Performance-Check
telegram-audio-downloader performance
```

### **Unit-Tests ausführen**
```bash
# Alle Tests
pytest

# Mit Coverage
pytest --cov=src/telegram_audio_downloader

# Nur bestimmte Tests
pytest tests/test_utils.py -v
```

---

## 🐛 **Troubleshooting**

### **Häufige Probleme**

#### **1. Python-Version zu alt**
```bash
# Problem: "Python 3.11+ required"
# Lösung: Python aktualisieren
python --version  # Prüfen
# Neuinstallation von python.org
```

#### **2. API-Credentials fehlen**
```bash
# Problem: "API_ID und API_HASH müssen gesetzt sein"
# Lösung: .env-Datei korrekt konfigurieren
cat .env  # Prüfen
```

#### **3. Abhängigkeits-Konflikte**
```bash
# Problem: "Dependency conflict"
# Lösung: Frische virtuelle Umgebung
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### **4. Permissions-Probleme**
```bash
# Problem: "Permission denied"
# Linux/macOS:
sudo chown -R $USER:$USER .
chmod +x telegram_audio_downloader.py

# Windows: Als Administrator ausführen
```

#### **5. Docker-Probleme**
```bash
# Problem: "Docker daemon not running"
# Lösung: Docker Desktop starten

# Problem: "Permission denied (Docker)"
# Linux: User zur docker-Gruppe hinzufügen
sudo usermod -aG docker $USER
# Neuanmeldung erforderlich
```

---

## 📚 **Weiterführende Dokumentation**

- **[CLI-Referenz](CLI-Reference)** - Alle Befehle und Optionen
- **[API-Dokumentation](API-Documentation)** - Programmatische Nutzung
- **[Performance-Guide](Performance-Guide)** - Optimierung und Monitoring
- **[Docker-Guide](Docker-Guide)** - Erweiterte Container-Konfiguration
- **[Contributing-Guide](../CONTRIBUTING.md)** - Entwicklung und Beiträge

---

## 🆘 **Hilfe erhalten**

Falls Sie Probleme haben:

1. **Dokumentation prüfen**: Wiki durchsuchen
2. **Issues durchsuchen**: [GitHub Issues](https://github.com/Elpablo777/Telegram-Audio-Downloader/issues)
3. **Issue erstellen**: Detaillierte Problembeschreibung
4. **Discussions**: [GitHub Discussions](https://github.com/Elpablo777/Telegram-Audio-Downloader/discussions)

**Beim Issue erstellen bitte angeben:**
- Betriebssystem und Version
- Python-Version
- Installationsmethode
- Vollständige Fehlermeldung
- Relevante Konfiguration (ohne API-Keys!)

---

**Happy Downloading! 🎵**