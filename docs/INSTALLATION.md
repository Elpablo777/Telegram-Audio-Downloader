# Installation & Setup - Telegram Audio Downloader

## Systemanforderungen

### Minimal
- **Python**: 3.8 oder höher
- **Betriebssystem**: Windows 10+, macOS 10.14+, Linux (Ubuntu 18.04+)
- **RAM**: 512MB verfügbar
- **Speicher**: 1GB frei für Downloads und Datenbank

### Empfohlen
- **Python**: 3.11
- **RAM**: 2GB oder mehr
- **SSD**: Für bessere Performance
- **Netzwerk**: Stabile Internetverbindung (10 Mbps+)

### Externe Abhängigkeiten
- **FFmpeg**: Für Audioverarbeitung (automatisch mit Requirements installiert)

## 1. Python-Installation

### Windows
1. Download von [python.org](https://www.python.org/downloads/)
2. Installiere mit "Add Python to PATH" aktiviert
3. Verifiziere: `python --version`

### macOS
```bash
# Mit Homebrew (empfohlen)
brew install python@3.11

# Oder von python.org herunterladen
```

### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install python3.11 python3.11-pip python3.11-venv
```

## 2. Projekt herunterladen

### Option A: Git Clone (empfohlen)
```bash
git clone https://github.com/dein-benutzer/telegram-audio-downloader.git
cd telegram-audio-downloader
```

### Option B: ZIP-Download
1. Lade ZIP von GitHub herunter
2. Entpacke in gewünschtes Verzeichnis
3. Öffne Terminal/Kommandozeile im Verzeichnis

## 3. Virtual Environment (empfohlen)

```bash
# Virtual Environment erstellen
python -m venv venv

# Aktivieren
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Später deaktivieren mit:
deactivate
```

## 4. Dependencies installieren

```bash
# Alle Dependencies installieren
pip install -r requirements.txt

# Entwicklungspaket installieren
pip install -e .
```

### FFmpeg Installation (falls nicht automatisch installiert)

#### Windows
```bash
# Mit Chocolatey
choco install ffmpeg

# Oder manuell von https://ffmpeg.org/ herunterladen
```

#### macOS
```bash
brew install ffmpeg
```

#### Linux
```bash
sudo apt install ffmpeg
```

## 5. Telegram API Setup

### API-Credentials erstellen
1. Gehe zu [my.telegram.org](https://my.telegram.org/)
2. Logge dich mit deiner Telefonnummer ein
3. Wähle "API development tools"
4. Erstelle eine neue Anwendung:
   - **App title**: "Audio Downloader" (oder beliebig)
   - **Short name**: "audiodownloader"
   - **Platform**: Desktop
   - **Description**: "Tool zum Herunterladen von Audiodateien"

### .env-Datei erstellen

Kopiere `.env.example` zu `.env` und fülle aus:

```bash
cp .env.example .env
```

Bearbeite `.env`:
```env
# Deine API-Credentials von my.telegram.org
API_ID=12345678
API_HASH=abcd1234efgh5678ijkl90mnop

# Session-Name (beliebig wählbar)
SESSION_NAME=my_audio_session
```

## 6. Erste Ausführung

### Authentifizierung
Beim ersten Start wirst du aufgefordert, dich zu authentifizieren:

```bash
telegram-audio-downloader --help
```

Falls eine Authentifizierung nötig ist:
1. Gib deine Telefonnummer ein (mit Ländercode, z.B. +49...)
2. Gib den per SMS/Telegram erhaltenen Code ein
3. Falls 2FA aktiviert: Gib dein Cloud-Password ein

### Test-Download
```bash
# Teste mit einer kleinen Gruppe
telegram-audio-downloader download "Test Gruppe" --limit 5
```

## 7. Konfiguration anpassen

### Basis-Konfiguration
Bearbeite `config/default.ini`:

```ini
[settings]
# Standardverzeichnis für Downloads
default_download_dir = downloads

# Maximale parallele Downloads
max_concurrent_downloads = 3

# Maximale Dateigröße in MB (0 = unbegrenzt)
max_file_size_mb = 500

# Wartezeit zwischen Downloads in Sekunden
download_delay = 1.0

[database]
# Datenbankpfad
path = data/audio_downloader.db

[logging]
# Log-Level: DEBUG, INFO, WARNING, ERROR
level = INFO
file = data/telegram_audio_downloader.log
```

### Verzeichnisstruktur
```
telegram-audio-downloader/
├── config/          # Konfigurationsdateien
├── data/           # Datenbank und Logs
├── downloads/      # Heruntergeladene Dateien
├── src/           # Quellcode
├── tests/         # Unit-Tests
├── docs/          # Dokumentation
├── .env           # API-Credentials (privat!)
└── requirements.txt
```

## 8. Docker-Installation (Alternative)

### Voraussetzungen
- Docker Desktop oder Docker Engine
- docker-compose (optional, aber empfohlen)

### Setup
```bash
# Image bauen
docker build -t telegram-audio-downloader .

# Mit docker-compose (empfohlen)
docker-compose up --build

# Oder direkt mit Docker
docker run --rm -it \
    -v $(pwd)/.env:/app/.env \
    -v $(pwd)/downloads:/app/downloads \
    -v $(pwd)/data:/app/data \
    telegram-audio-downloader
```

## 9. Troubleshooting

### Häufige Probleme

#### "Modul nicht gefunden"
```bash
# Stelle sicher, dass du im richtigen Verzeichnis bist
cd telegram-audio-downloader

# Virtual Environment aktiviert?
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Paket installiert?
pip install -e .
```

#### "API-Fehler" oder "Unauthorized"
```bash
# Überprüfe .env-Datei
cat .env

# Lösche alte Session-Dateien
rm *.session

# Starte neu und authentifiziere dich erneut
telegram-audio-downloader --help
```

#### "FFmpeg nicht gefunden"
```bash
# Teste FFmpeg-Installation
ffmpeg -version

# Falls nicht installiert, siehe FFmpeg-Abschnitt oben
```

#### Speicherplatz-Probleme
```bash
# Überprüfe verfügbaren Speicher
df -h  # Linux/macOS
dir    # Windows

# Ändere Download-Verzeichnis
telegram-audio-downloader download "Gruppe" --output /pfad/mit/viel/speicher
```

#### Performance-Probleme
```bash
# Reduziere parallele Downloads
telegram-audio-downloader download "Gruppe" --parallel 1

# Oder in config/default.ini:
max_concurrent_downloads = 1
```

### Debug-Modus aktivieren
```bash
telegram-audio-downloader --debug download "Gruppe"
```

### Logs überprüfen
```bash
# Log-Datei anzeigen
tail -f data/telegram_audio_downloader.log

# Nur Fehler anzeigen
grep ERROR data/telegram_audio_downloader.log
```

## 10. Updates

### Git-basierte Installation
```bash
# Updates herunterladen
git pull origin main

# Dependencies aktualisieren
pip install -r requirements.txt --upgrade

# Paket neu installieren
pip install -e . --force-reinstall
```

### Datenbank-Migration
Bei größeren Updates könnte eine Datenbank-Migration nötig sein:

```bash
# Backup erstellen
cp data/audio_downloader.db data/audio_downloader.db.backup

# Migration automatisch durchführen
telegram-audio-downloader --help
```

## 11. Deinstallation

### Virtual Environment
```bash
# Environment deaktivieren
deactivate

# Verzeichnis löschen
rm -rf telegram-audio-downloader/
```

### System-weite Installation
```bash
pip uninstall telegram-audio-downloader

# Konfigurationsdateien löschen (optional)
rm -rf ~/.telegram-audio-downloader/
```

### Docker
```bash
# Container und Images löschen
docker-compose down --rmi all --volumes
docker rmi telegram-audio-downloader
```

## 12. Sicherheitshinweise

### .env-Datei
- **Niemals** die `.env`-Datei öffentlich teilen oder committen
- API-Credentials sind persönlich und sollten geheim bleiben
- Verwende verschiedene Session-Namen für verschiedene Zwecke

### Berechtigungen
- Das Tool benötigt nur Leserechte für Telegram-Gruppen
- Niemals Admin-Rechte oder Bot-Token verwenden
- Prüfe regelmäßig aktive Sessions in Telegram-Einstellungen

### Datenschutz
- Heruntergeladene Dateien können urheberrechtlich geschützt sein
- Respektiere die Regeln der Telegram-Gruppen
- Verwende das Tool nur für legale Zwecke

## Support

Bei Problemen oder Fragen:

1. **Dokumentation**: Lies zuerst diese Dokumentation und die API-Docs
2. **Issues**: Suche in den GitHub Issues nach ähnlichen Problemen
3. **Debug**: Aktiviere Debug-Modus und prüfe Logs
4. **Community**: Frage in relevanten Telegram-Gruppen oder Foren

### Issue-Vorlage
Wenn du ein Issue erstellst, füge hinzu:
- **System**: OS, Python-Version
- **Installation**: pip, docker, git clone?
- **Fehlermeldung**: Vollständige Fehlermeldung
- **Befehle**: Welche Befehle hast du ausgeführt?
- **Logs**: Relevante Log-Einträge (ohne sensible Daten!)
- **Konfiguration**: Relevante Config-Einstellungen

# 🛠️ Installationsanleitung

Diese Anleitung zeigt Ihnen, wie Sie den Telegram Audio Downloader auf verschiedenen Betriebssystemen installieren.

## 🖥️ Windows

### Voraussetzungen
1. Python 3.11 oder höher
2. Git (optional, aber empfohlen)
3. FFmpeg

### 1. Python installieren
1. Laden Sie Python von [python.org](https://www.python.org/downloads/) herunter
2. Führen Sie den Installer aus
3. Aktivieren Sie "Add Python to PATH"

### 2. Git installieren (optional)
1. Laden Sie Git von [git-scm.com](https://git-scm.com/download/win) herunter
2. Führen Sie den Installer aus

### 3. FFmpeg installieren
1. Laden Sie FFmpeg von [ffmpeg.org](https://ffmpeg.org/download.html) herunter
2. Entpacken Sie die Dateien in einen Ordner (z.B. `C:\ffmpeg`)
3. Fügen Sie den `bin`-Ordner zum System-PATH hinzu:
   - Rechtsklick auf "Dieser PC" → "Eigenschaften"
   - "Erweiterte Systemeinstellungen"
   - "Umgebungsvariablen"
   - Wählen Sie "Path" → "Bearbeiten"
   - Fügen Sie `C:\ffmpeg\bin` hinzu

### 4. Telegram Audio Downloader installieren
```cmd
# Repository klonen (wenn Git installiert ist)
git clone https://github.com/Elpablo777/telegram-audio-downloader.git
cd telegram-audio-downloader

# Oder laden Sie die neueste Version herunter und entpacken Sie sie

# Virtuelle Umgebung erstellen
python -m venv venv

# Virtuelle Umgebung aktivieren
venv\Scripts\activate

# Abhängigkeiten installieren
pip install -r requirements.txt

# Paket installieren
pip install -e .
```

## 🐧 Linux (Ubuntu/Debian)

### Voraussetzungen
1. Python 3.11 oder höher
2. Git
3. FFmpeg

### 1. System aktualisieren
```bash
sudo apt update
sudo apt upgrade
```

### 2. Python und Git installieren
```bash
sudo apt install python3 python3-pip git
```

### 3. FFmpeg installieren
```bash
sudo apt install ffmpeg
```

### 4. Telegram Audio Downloader installieren
```bash
# Repository klonen
git clone https://github.com/Elpablo777/telegram-audio-downloader.git
cd telegram-audio-downloader

# Virtuelle Umgebung erstellen
python3 -m venv venv

# Virtuelle Umgebung aktivieren
source venv/bin/activate

# Abhängigkeiten installieren
pip install -r requirements.txt

# Paket installieren
pip install -e .
```

## 🍏 macOS

### Voraussetzungen
1. Python 3.11 oder höher
2. Git
3. FFmpeg

### 1. Homebrew installieren (falls nicht vorhanden)
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 2. Python, Git und FFmpeg installieren
```bash
brew install python git ffmpeg
```

### 3. Telegram Audio Downloader installieren
```bash
# Repository klonen
git clone https://github.com/Elpablo777/telegram-audio-downloader.git
cd telegram-audio-downloader

# Virtuelle Umgebung erstellen
python3 -m venv venv

# Virtuelle Umgebung aktivieren
source venv/bin/activate

# Abhängigkeiten installieren
pip install -r requirements.txt

# Paket installieren
pip install -e .
```

## 🐳 Docker (plattformunabhängig)

### Voraussetzungen
1. Docker installiert

### Installation
```bash
# Repository klonen
git clone https://github.com/Elpablo777/telegram-audio-downloader.git
cd telegram-audio-downloader

# Docker-Image bauen
docker build -t telegram-audio-downloader .

# Oder verwenden Sie docker-compose
docker-compose up --build
```

## 🔧 Erste Einrichtung

### 1. Telegram API-Zugangsdaten erhalten
1. Gehen Sie zu [https://my.telegram.org/apps](https://my.telegram.org/apps)
2. Melden Sie sich mit Ihrem Telegram-Konto an
3. Erstellen Sie eine neue Anwendung
4. Notieren Sie sich die `API_ID` und `API_HASH`

### 2. Konfigurationsdatei erstellen
```bash
# .env-Datei erstellen
cp .env.example .env
```

Bearbeiten Sie die `.env`-Datei mit Ihren Zugangsdaten:
```env
API_ID=1234567
API_HASH=your_api_hash_here
SESSION_NAME=my_telegram_session
```

### 3. Ersten Download testen
```bash
# Virtuelle Umgebung aktivieren (wenn nicht bereits geschehen)
# Windows: venv\Scripts\activate
# Linux/macOS: source venv/bin/activate

# Ersten Download starten
telegram-audio-downloader download @your_music_group
```

## ✅ Verifizierung

Überprüfen Sie, ob die Installation erfolgreich war:
```bash
# Hilfe anzeigen
telegram-audio-downloader --help

# Version anzeigen
telegram-audio-downloader --version
```

## 📝 Problemlösung

### Häufige Probleme

1. **"Command not found" Fehler**
   - Stellen Sie sicher, dass die virtuelle Umgebung aktiviert ist
   - Überprüfen Sie, ob das Paket korrekt installiert wurde

2. **FFmpeg nicht gefunden**
   - Stellen Sie sicher, dass FFmpeg installiert und im PATH ist
   - Führen Sie `ffmpeg -version` aus, um die Installation zu überprüfen

3. **ImportError: No module named 'telethon'**
   - Stellen Sie sicher, dass alle Abhängigkeiten installiert sind
   - Führen Sie `pip install -r requirements.txt` erneut aus

4. **Permission denied Fehler**
   - Verwenden Sie eine virtuelle Umgebung
   - Führen Sie den Befehl mit `sudo` aus (nur bei Bedarf auf Linux/macOS)

### Support

Wenn Sie Probleme haben, die nicht durch diese Anleitung gelöst werden:
1. Überprüfen Sie die [Issues](https://github.com/Elpablo777/telegram-audio-downloader/issues) auf GitHub
2. Erstellen Sie ein neues Issue mit detaillierten Informationen
3. Kontaktieren Sie den Entwickler über die bereitgestellten Kontaktdaten
