# ❓ Frequently Asked Questions (FAQ)

Die häufigsten Fragen und Antworten zum Telegram Audio Downloader.

## 📋 **Inhaltsverzeichnis**

- [Installation & Setup](#installation--setup)
- [Telegram API & Authentifizierung](#telegram-api--authentifizierung)
- [Downloads & Performance](#downloads--performance)
- [Audio-Formate & Qualität](#audio-formate--qualität)
- [Fehlerbehandlung](#fehlerbehandlung)
- [Sicherheit & Datenschutz](#sicherheit--datenschutz)

---

## 🛠️ **Installation & Setup**

### **Q: Welche Python-Version wird benötigt?**
**A:** Python 3.11 oder höher ist erforderlich. Der Code nutzt moderne Python-Features wie erweiterte Type Hints und async/await-Syntax.

```bash
# Python-Version prüfen
python --version
python3 --version  # Linux/macOS
```

### **Q: Kann ich das Tool ohne Git installieren?**
**A:** Ja! Sie können das Repository als ZIP herunterladen:
1. Gehen Sie zu [GitHub Repository](https://github.com/Elpablo777/Telegram-Audio-Downloader)
2. Klicken Sie "Code" > "Download ZIP"
3. Entpacken Sie das ZIP
4. Folgen Sie der normalen Installation

### **Q: Funktioniert das Tool auf Raspberry Pi?**
**A:** Ja! Das Tool läuft auf Raspberry Pi (ARM-Architektur):

```bash
# Spezielle Installation für Raspberry Pi
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip git ffmpeg

# Normale Installation fortsetzen
git clone https://github.com/Elpablo777/Telegram-Audio-Downloader.git
cd Telegram-Audio-Downloader
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

---

## 🔑 **Telegram API & Authentifizierung**

### **Q: Wo bekomme ich API_ID und API_HASH?**
**A:** 
1. Gehen Sie zu [my.telegram.org](https://my.telegram.org/)
2. Loggen Sie sich mit Ihrer Telefonnummer ein
3. Klicken Sie "API development tools"
4. Füllen Sie das Formular aus (App title: "Audio Downloader", Short name: "audio_dl")
5. Notieren Sie sich API_ID (Zahl) und API_HASH (String)

### **Q: Ist es sicher, meine Telegram-Credentials zu verwenden?**
**A:** Ja, absolut sicher:
- Ihre Credentials werden nur lokal gespeichert
- Keine Datenübertragung an Dritte
- Open-Source-Code ist vollständig einsehbar
- Telethon ist eine etablierte, vertrauenswürdige Bibliothek

### **Q: "Phone number already registered" - was tun?**
**A:** Das ist normal! Es bedeutet, dass Ihre Nummer bereits bei Telegram registriert ist:
1. Geben Sie Ihre Telefonnummer mit Ländercode ein (z.B. +49123456789)
2. Sie erhalten einen Bestätigungscode in Telegram
3. Geben Sie diesen Code ein
4. Falls 2FA aktiviert ist, geben Sie Ihr Cloud-Passwort ein

---

## 📥 **Downloads & Performance**

### **Q: Wie schnell kann ich herunterladen?**
**A:** Das hängt von mehreren Faktoren ab:
- **Telegram-Limits**: ~10-20 MB/s pro Session
- **Parallele Downloads**: 3-5 gleichzeitig empfohlen
- **Ihre Internetverbindung**
- **Server-Load der Gruppen**

```bash
# Performance optimieren
telegram-audio-downloader download @gruppe --parallel=5 --limit=50
```

### **Q: Werden bereits heruntergeladene Dateien übersprungen?**
**A:** Ja, automatisch:
- Das Tool führt eine Datenbank aller Downloads
- Bereits vorhandene Dateien werden übersprungen
- Erzwingen mit `--force-redownload`
- Prüfung mit `--skip-existing`

### **Q: Kann ich unterbrochene Downloads fortsetzen?**
**A:** Teilweise:
- Telethon unterstützt kein echtes Resume
- Das Tool versucht intelligente Neuversuche
- Verwenden Sie `--resume` für bessere Handling
- Checksum-Verifikation mit `--verify-checksum`

---

## 🎵 **Audio-Formate & Qualität**

### **Q: Welche Audio-Formate werden unterstützt?**
**A:** Alle gängigen Formate:
- **Verlustlos**: FLAC, WAV
- **Komprimiert**: MP3, AAC, M4A, OGG, OPUS
- **Automatische Erkennung** basierend auf MIME-Type und Dateiendung

### **Q: Kann ich die Audio-Qualität beeinflussen?**
**A:** Nur indirekt:
- Das Tool lädt Dateien in Original-Qualität herunter
- Keine Konvertierung oder Qualitätsverlust
- Filtern nach Format möglich: `--format=flac`
- Größenfilter als Qualitäts-Proxy: `--min-size=10MB`

### **Q: Werden Metadaten (ID3-Tags) extrahiert?**
**A:** Ja, umfassend:
- **Standard-Tags**: Titel, Künstler, Album, Jahr, Genre
- **Erweiterte Tags**: Cover-Art, Dauer, Bitrate
- **Automatische Extraktion** bei aktivierter `--metadata` Option
- **Reparatur** möglich mit `telegram-audio-downloader metadata --repair`

---

## 🐛 **Fehlerbehandlung**

### **Q: "ImportError: cannot import name 'NetworkError'" - was tun?**
**A:** Das ist ein Telethon-Versionskonflikt:
```bash
# Telethon aktualisieren
pip install --upgrade telethon

# Oder spezifische Version installieren
pip install telethon==1.40.0
```

### **Q: Download bricht mit "Connection lost" ab - was tun?**
**A:** Netzwerk-Probleme handhaben:
```bash
# Mehr Retry-Versuche
telegram-audio-downloader download @gruppe --max-retries=10

# Längerer Timeout
telegram-audio-downloader download @gruppe --timeout=600

# Debug-Modus für Details
telegram-audio-downloader --debug download @gruppe --limit=1
```

### **Q: "Cannot install cryptography==X.Y.Z and cryptography>=A.B.C" - wie lösen?**
**A:** Doppelte/konfliktäre Dependency-Spezifikationen:
```bash
# 1. Cache leeren und neu installieren
pip cache purge
pip uninstall telegram-audio-downloader telethon cryptography -y

# 2. Aktuelle requirements.txt verwenden
pip install -r requirements.txt

# 3. Bei anhaltenden Problemen: manuelle Installation
pip install telethon>=1.40.0 cryptography>=45.0.6
pip install -e .
```

**Ursache:** Ältere telethon-Versionen (< 1.40.0) sind nicht kompatibel mit neueren cryptography-Versionen.

### **Q: "Database is locked" Fehler - Lösung?**
**A:** SQLite-Datenbank-Konflikt:
```bash
# 1. Alle Instanzen beenden
pkill -f telegram-audio-downloader

# 2. Datenbank-Integrität prüfen
telegram-audio-downloader db --check

# 3. Falls nötig, reparieren
telegram-audio-downloader db --repair
```

---

## 🔒 **Sicherheit & Datenschutz**

### **Q: Kann Telegram sehen, was ich herunterlade?**
**A:** Ja, aber:
- Telegram sieht alle API-Aktivitäten (normal)
- Keine Datensammlung durch das Tool selbst
- Logs bleiben lokal
- Kein Tracking oder Telemetrie

### **Q: Sind meine API-Credentials sicher gespeichert?**
**A:** Ja:
- Lokal in `.env`-Datei gespeichert
- Niemals an Dritte übertragen
- Session-Dateien sind verschlüsselt
- Regelmäßige Rotation empfohlen

### **Q: Kann ich das Tool über VPN/Proxy nutzen?**
**A:** Ja:
```bash
# System-Proxy wird automatisch verwendet
# Oder explizit in .env konfigurieren
PROXY_TYPE=socks5
PROXY_HOST=127.0.0.1  
PROXY_PORT=9050
PROXY_USERNAME=user
PROXY_PASSWORD=pass
```

---

## 🤖 **Automatisierung & Scripting**

### **Q: Kann ich das Tool als Cron-Job laufen lassen?**
**A:** Ja, perfekt dafür geeignet:

```bash
# Crontab-Eintrag (Linux/macOS)
# Jeden Tag um 2 Uhr, max 20 neue Dateien
0 2 * * * cd /path/to/project && ./venv/bin/telegram-audio-downloader download @musikgruppe --limit=20 --quiet

# Windows Task Scheduler (.bat-Datei)
@echo off
cd /d "C:\path\to\project"
venv\Scripts\activate
telegram-audio-downloader download @musikgruppe --limit=20 --quiet
```

### **Q: Kann ich das Tool in eigene Python-Scripts einbinden?**
**A:** Ja, vollständig:

```python
from telegram_audio_downloader import AudioDownloader
import asyncio

async def my_download():
    downloader = AudioDownloader(download_dir="./music")
    await downloader.initialize_client()
    await downloader.download_audio_files("@musikgruppe", limit=10)
    await downloader.close()

asyncio.run(my_download())
```

---

## 📊 **Monitoring & Statistiken**

### **Q: Kann ich Download-Statistiken exportieren?**
**A:** Ja, in verschiedenen Formaten:

```bash
# JSON-Export
telegram-audio-downloader stats --export=stats.json --period=month

# CSV für Excel
telegram-audio-downloader stats --csv > downloads.csv

# Detailed Report
telegram-audio-downloader stats --detailed --period=all
```

### **Q: Gibt es ein Web-Interface?**
**A:** Nicht offiziell, aber möglich:
- CLI-Tool ist primärer Interface
- JSON-APIs ermöglichen Web-Frontend-Entwicklung
- Community-Contributions willkommen

---

## 🔄 **Updates & Wartung**

### **Q: Wie aktualisiere ich das Tool?**
**A:**
```bash
# Git-Update
git pull origin main
pip install --upgrade -r requirements.txt

# Oder komplette Neuinstallation
pip install --upgrade telegram-audio-downloader
```

### **Q: Wie sichere ich meine Daten?**
**A:**
```bash
# Wichtige Dateien sichern
cp .env .env.backup
telegram-audio-downloader db --backup=database_backup.db
tar -czf telegram_audio_backup.tar.gz .env data/ downloads/
```

---

## 🤝 **Community & Support**

### **Q: Wo kann ich Bugs melden?**
**A:** 
- **GitHub Issues**: [Bug Reports](https://github.com/Elpablo777/Telegram-Audio-Downloader/issues)
- **Template verwenden** für bessere Hilfe
- **Logs beifügen** bei Fehlern
- **System-Info angeben**

### **Q: Kann ich neue Features vorschlagen?**
**A:** Absolut!
- **GitHub Discussions**: [Feature Requests](https://github.com/Elpablo777/Telegram-Audio-Downloader/discussions)
- **Feature Request Template** verwenden
- **Use Case beschreiben**
- **Community-Voting** berücksichtigen

### **Q: Wie kann ich zum Projekt beitragen?**
**A:** Viele Möglichkeiten:
- **Code**: Pull Requests mit neuen Features/Fixes
- **Dokumentation**: Wiki-Verbesserungen
- **Tests**: Unit-Tests schreiben
- **Übersetzungen**: Multi-Language Support
- **Bug Reports**: Qualitäts-Feedback

---

## 📞 **Weitere Hilfe**

**Wenn Sie hier keine Antwort finden:**

1. **[Troubleshooting Guide](Troubleshooting)** - Detaillierte Problemlösungen
2. **[GitHub Issues](https://github.com/Elpablo777/Telegram-Audio-Downloader/issues)** - Neue Issues melden
3. **[Discussions](https://github.com/Elpablo777/Telegram-Audio-Downloader/discussions)** - Community-Fragen
4. **Email**: hannover84@msn.com - Direkte Unterstützung

---

**Happy Downloading!** 🎵✨