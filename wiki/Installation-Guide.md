# 📦 Installation Guide

Eine detaillierte Anleitung zur Installation des Telegram Audio Downloaders auf verschiedenen Betriebssystemen.

## 🎯 **Voraussetzungen**

### **System-Anforderungen**
- **Python**: 3.11 oder höher
- **Betriebssystem**: Windows 10+, Ubuntu 20.04+, macOS 12.0+
- **RAM**: Mindestens 2GB (4GB empfohlen)
- **Festplatte**: 1GB freier Speicherplatz

### **Telegram API**
Sie benötigen Ihre eigenen Telegram API-Credentials:
1. Besuchen Sie [my.telegram.org](https://my.telegram.org/)
2. Loggen Sie sich mit Ihrer Telefonnummer ein
3. Gehen Sie zu "API development tools"
4. Erstellen Sie eine neue App und notieren Sie:
   - `api_id` (Zahlenfolge)
   - `api_hash` (Hexadezimaler String)

---

## 🪟 **Windows Installation**

### **Methode 1: Automatische Installation (Empfohlen)**

```batch
# 1. Repository klonen
git clone https://github.com/Elpablo777/Telegram-Audio-Downloader.git
cd Telegram-Audio-Downloader

# 2. Installationsskript ausführen
powershell -ExecutionPolicy Bypass -File scripts/install_windows.ps1
```

### **Methode 2: Manuelle Installation**

```batch
# 1. Python Virtual Environment erstellen
python -m venv venv
venv\Scripts\activate

# 2. Abhängigkeiten installieren
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .

# 3. Konfiguration
copy .env.example .env
# Bearbeiten Sie .env mit Ihren API-Daten
```

### **Windows-spezifische Hinweise**
- **FFmpeg**: Wird für erweiterte Audio-Verarbeitung benötigt
  ```batch
  # Via Chocolatey
  choco install ffmpeg
  
  # Oder manuell von https://ffmpeg.org/download.html
  ```
- **Git**: Installieren Sie Git für Windows von [git-scm.com](https://git-scm.com/)

---

## 🐧 **Linux Installation (Ubuntu/Debian)**

### **Automatische Installation**

```bash
# 1. System-Updates
sudo apt update && sudo apt upgrade -y

# 2. Repository klonen
git clone https://github.com/Elpablo777/Telegram-Audio-Downloader.git
cd Telegram-Audio-Downloader

# 3. Installationsskript ausführen
chmod +x scripts/install_linux.sh
./scripts/install_linux.sh
```

### **Manuelle Installation**

```bash
# 1. Python und Abhängigkeiten installieren
sudo apt install -y python3.11 python3.11-venv python3-pip git ffmpeg

# 2. Virtual Environment erstellen
python3.11 -m venv venv
source venv/bin/activate

# 3. Python-Abhängigkeiten installieren
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .

# 4. Konfiguration
cp .env.example .env
nano .env  # Ihre API-Daten eintragen
```

### **Alternative Linux-Distributionen**

**CentOS/RHEL/Fedora:**
```bash
# Pakete installieren
sudo dnf install -y python3.11 python3-pip git ffmpeg

# Rest wie oben...
```

**Arch Linux:**
```bash
# Pakete installieren
sudo pacman -S python python-pip git ffmpeg

# Rest wie oben...
```

---

## 🍎 **macOS Installation**

### **Mit Homebrew (Empfohlen)**

```bash
# 1. Homebrew installieren (falls nicht vorhanden)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2. Abhängigkeiten installieren
brew install python@3.11 git ffmpeg

# 3. Repository klonen
git clone https://github.com/Elpablo777/Telegram-Audio-Downloader.git
cd Telegram-Audio-Downloader

# 4. Virtual Environment erstellen
python3.11 -m venv venv
source venv/bin/activate

# 5. Python-Abhängigkeiten installieren
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .

# 6. Konfiguration
cp .env.example .env
nano .env  # Ihre API-Daten eintragen
```

### **macOS-spezifische Hinweise**
- Stellen Sie sicher, dass Xcode Command Line Tools installiert sind:
  ```bash
  xcode-select --install
  ```

---

## 🐳 **Docker Installation**

### **Schnellstart mit Docker Compose**

```bash
# 1. Repository klonen
git clone https://github.com/Elpablo777/Telegram-Audio-Downloader.git
cd Telegram-Audio-Downloader

# 2. Umgebungsvariablen konfigurieren
cp .env.example .env
# .env mit Ihren API-Daten bearbeiten

# 3. Container starten
docker-compose up -d

# 4. Tool verwenden
docker-compose exec telegram-audio-downloader telegram-audio-downloader --help
```

### **Docker ohne Compose**

```bash
# 1. Image erstellen
docker build -t telegram-audio-downloader .

# 2. Container ausführen
docker run -it --rm \
  -v $(pwd)/downloads:/app/downloads \
  -v $(pwd)/.env:/app/.env \
  telegram-audio-downloader telegram-audio-downloader --help
```

---

## ⚙️ **Konfiguration**

### **.env-Datei erstellen**

```ini
# Telegram API Credentials (ERFORDERLICH)
API_ID=12345678
API_HASH=1234567890abcdef1234567890abcdef
SESSION_NAME=telegram_session

# Download-Einstellungen (OPTIONAL)
DOWNLOAD_DIR=downloads
MAX_CONCURRENT_DOWNLOADS=3
MAX_FILE_SIZE_MB=100

# Audio-Einstellungen (OPTIONAL)
PREFERRED_FORMAT=mp3
AUDIO_QUALITY=high

# Performance-Einstellungen (OPTIONAL)
MAX_MEMORY_MB=1024
ENABLE_PERFORMANCE_MONITORING=true

# Logging (OPTIONAL)
LOG_LEVEL=INFO
LOG_FILE=data/telegram_audio_downloader.log
```

### **Erste Einrichtung**

```bash
# 1. Virtual Environment aktivieren
source venv/bin/activate  # Linux/macOS
# ODER
venv\Scripts\activate     # Windows

# 2. Tool initialisieren
telegram-audio-downloader --setup

# 3. Telegram-Authentifizierung (nur beim ersten Mal)
telegram-audio-downloader auth

# 4. Test-Download
telegram-audio-downloader download @testgroup --limit=1
```

---

## 🧪 **Installation Verifizieren**

### **System-Check ausführen**

```bash
# Systemcheck
telegram-audio-downloader --system-check

# Version anzeigen
telegram-audio-downloader --version

# Verfügbare Befehle
telegram-audio-downloader --help
```

### **Test-Downloads**

```bash
# Kleiner Test (1 Datei)
telegram-audio-downloader download @musikgruppe --limit=1

# Performance-Test
telegram-audio-downloader performance --test

# Konfiguration prüfen
telegram-audio-downloader config --show
```

---

## 🔧 **Entwickler-Installation**

Für Entwickler, die am Projekt mitwirken möchten:

```bash
# 1. Fork des Repositories erstellen (GitHub Web UI)

# 2. Entwickler-Repository klonen
git clone https://github.com/IHR-USERNAME/Telegram-Audio-Downloader.git
cd Telegram-Audio-Downloader

# 3. Entwicklungs-Environment einrichten
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# 4. Entwicklungs-Abhängigkeiten installieren
pip install -e ".[dev]"

# 5. Pre-commit Hooks installieren
pre-commit install

# 6. Tests ausführen
pytest

# 7. Code-Quality prüfen
flake8 src/
black src/
mypy src/
```

---

## 🆘 **Problemlösung**

### **Häufige Installationsprobleme**

**Python-Version zu alt:**
```bash
# Prüfen Sie Ihre Python-Version
python --version

# Installieren Sie Python 3.11+ von https://python.org
```

**Pip-Fehler:**
```bash
# Pip aktualisieren
pip install --upgrade pip

# Bei SSL-Problemen
pip install --trusted-host pypi.org --trusted-host pypi.python.org --upgrade pip
```

**Virtual Environment Probleme:**
```bash
# Virtual Environment neu erstellen
rm -rf venv  # Linux/macOS
rmdir /s venv  # Windows

python -m venv venv
```

**Telegram API-Fehler:**
- Überprüfen Sie Ihre API-Credentials in der .env-Datei
- Stellen Sie sicher, dass keine Leerzeichen oder Anführungszeichen in den Werten sind
- API_ID muss eine Zahl sein, API_HASH ein String

**Berechtigungsfehler (Linux/macOS):**
```bash
# Download-Verzeichnis erstellen
mkdir -p downloads
chmod 755 downloads

# Log-Verzeichnis erstellen
mkdir -p data
chmod 755 data
```

### **Logs überprüfen**

```bash
# Aktuelle Logs anzeigen
tail -f data/telegram_audio_downloader.log

# Debug-Modus aktivieren
telegram-audio-downloader --debug download @gruppe
```

---

## 🚀 **Nächste Schritte**

Nach erfolgreicher Installation:

1. **[Quick Start Guide](Quick-Start)** - Erste Schritte in 5 Minuten
2. **[CLI Commands](CLI-Commands)** - Alle verfügbaren Befehle
3. **[Configuration](Configuration)** - Erweiterte Konfiguration
4. **[FAQ](FAQ)** - Häufig gestellte Fragen

---

## 💬 **Hilfe & Support**

- **GitHub Issues**: [Bug Reports & Feature Requests](https://github.com/Elpablo777/Telegram-Audio-Downloader/issues)
- **Discussions**: [Community-Forum](https://github.com/Elpablo777/Telegram-Audio-Downloader/discussions)
- **Email**: hannover84@msn.com

**Happy Installing!** 🎉