# ⚡ Quick Start Guide

Kommen Sie in 5 Minuten zum ersten Download! Diese Anleitung führt Sie durch die wichtigsten Schritte.

## 🎯 **Überblick**

1. **Installation** (2 Minuten)
2. **API-Konfiguration** (1 Minute)
3. **Erste Authentifizierung** (1 Minute)
4. **Erster Download** (1 Minute)

---

## 📦 **1. Schnell-Installation**

### **Windows (PowerShell als Administrator)**
```powershell
# Python 3.11+ installieren (von python.org)
# Git installieren (von git-scm.com)

git clone https://github.com/Elpablo777/Telegram-Audio-Downloader.git
cd Telegram-Audio-Downloader
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
```

### **Linux/macOS (Terminal)**
```bash
git clone https://github.com/Elpablo777/Telegram-Audio-Downloader.git
cd Telegram-Audio-Downloader
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

### **Docker (Noch schneller!)**
```bash
git clone https://github.com/Elpablo777/Telegram-Audio-Downloader.git
cd Telegram-Audio-Downloader
docker-compose up -d
```

---

## 🔑 **2. API-Konfiguration (1 Minute)**

### **Telegram API-Daten holen**
1. Gehen Sie zu [my.telegram.org](https://my.telegram.org/)
2. Loggen Sie sich mit Ihrer Telefonnummer ein
3. Klicken Sie auf "API development tools"
4. Erstellen Sie eine neue App
5. Notieren Sie sich `api_id` und `api_hash`

### **.env-Datei erstellen**
```bash
# Kopiere das Template
cp .env.example .env

# Bearbeite mit Ihren Daten
nano .env    # Linux/macOS
notepad .env # Windows
```

```ini
# Ihre echten Daten hier eintragen:
API_ID=12345678
API_HASH=1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p
SESSION_NAME=my_session
```

> **⚠️ Wichtig**: Keine Anführungszeichen verwenden!

---

## 🔐 **3. Telegram-Authentifizierung**

```bash
# Virtuelle Umgebung aktivieren (falls nicht aktiv)
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Authentifizierung starten
telegram-audio-downloader auth
```

Sie werden aufgefordert:
1. **Telefonnummer** eingeben (mit Ländercode, z.B. +49123456789)
2. **Bestätigungscode** aus Telegram eingeben
3. **2FA-Passwort** (falls aktiviert)

✅ **Erfolgreich**: "Telegram-Client erfolgreich authentifiziert"

---

## 🎵 **4. Erster Download**

### **Gruppe finden**
```bash
# Alle verfügbaren Gruppen anzeigen
telegram-audio-downloader groups
```

### **Ersten Download starten**
```bash
# Download aus einer Gruppe (nur 5 Dateien zum Testen)
telegram-audio-downloader download @musikgruppe --limit=5
```

**Alternativen:**
```bash
# Wenn Sie den Gruppennamen kennen
telegram-audio-downloader download "Musik & Sounds" --limit=5

# Wenn Sie die Gruppen-ID kennen
telegram-audio-downloader download -1001234567890 --limit=5

# Aus einem Kanal
telegram-audio-downloader download @musicchannel --limit=5
```

### **Download-Progress verfolgen**
Der Download zeigt eine schöne Fortschrittsanzeige:
```
📥 Sammle Audiodateien...
🎵 5 neue Audiodateien gefunden

Lade herunter: Artist - Song.mp3 ████████████████ 100% 3.2MB/s
✅ Download erfolgreich: downloads/Artist - Song.mp3 (2.1s)
```

---

## 🎯 **5. Wichtige Erste Befehle**

### **System-Check**
```bash
# Prüfen, ob alles richtig installiert ist
telegram-audio-downloader --system-check
```

### **Hilfe anzeigen**
```bash
# Alle verfügbaren Befehle
telegram-audio-downloader --help

# Hilfe zu einem spezifischen Befehl
telegram-audio-downloader download --help
```

### **Download-Statistiken**
```bash
# Zeigt Ihre Download-Historie
telegram-audio-downloader stats
```

---

## ⚡ **Erweiterte Quick-Tipps**

### **Parallele Downloads (Schneller!)**
```bash
# 5 parallele Downloads (Standard: 3)
telegram-audio-downloader download @gruppe --parallel=5 --limit=20
```

### **Spezifisches Audio-Format**
```bash
# Nur FLAC-Dateien herunterladen
telegram-audio-downloader download @gruppe --format=flac

# Mehrere Formate
telegram-audio-downloader download @gruppe --format=mp3,flac
```

### **Custom Download-Verzeichnis**
```bash
# In spezifisches Verzeichnis herunterladen
telegram-audio-downloader download @gruppe --output=./meine_musik
```

### **Fuzzy-Suche verwenden**
```bash
# Nach bestimmter Musik suchen (mit Schreibfehler-Toleranz)
telegram-audio-downloader search "bethovn" --fuzzy
telegram-audio-downloader search "klassik" --fuzzy
```

---

## 🔍 **Quick-Troubleshooting**

### **Häufige Probleme & Sofort-Lösungen**

**"Command not found" Fehler:**
```bash
# Virtual Environment aktivieren
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Oder vollständiger Pfad
./venv/bin/telegram-audio-downloader  # Linux/macOS
venv\Scripts\telegram-audio-downloader.exe  # Windows
```

**"API_ID or API_HASH missing" Fehler:**
```bash
# .env-Datei prüfen
cat .env  # Linux/macOS
type .env # Windows

# Sicherstellen, dass keine Leerzeichen oder Anführungszeichen
```

**"Group not found" Fehler:**
```bash
# Gruppen-Liste anzeigen
telegram-audio-downloader groups

# Gruppe mit @ oder ohne versuchen
telegram-audio-downloader download musikgruppe  # ohne @
telegram-audio-downloader download @musikgruppe # mit @
```

**Download bricht ab:**
```bash
# Mit Debug-Informationen erneut versuchen
telegram-audio-downloader --debug download @gruppe --limit=1
```

---

## 🚀 **Nächste Schritte**

Nach Ihrem ersten erfolgreichen Download:

### **Sofort weitermachen:**
1. **[CLI Commands](CLI-Commands)** - Lernen Sie alle Befehle kennen
2. **[Configuration](Configuration)** - Optimieren Sie Ihre Einstellungen
3. **[Audio Formats](Audio-Formats)** - Verstehen Sie die Format-Optionen

### **Für Fortgeschrittene:**
4. **[Performance Tuning](Performance-Tuning)** - Maximale Download-Geschwindigkeit
5. **[Batch Operations](Batch-Operations)** - Automatisierte Massendownloads
6. **[Custom Scripts](Custom-Scripts)** - Eigene Automatisierungen

### **Bei Problemen:**
- **[FAQ](FAQ)** - Häufig gestellte Fragen
- **[Troubleshooting](Troubleshooting)** - Detaillierte Problemlösungen

---

## 💡 **Pro-Tipps für den Start**

### **Performance optimieren:**
```bash
# Performance-Dashboard aktivieren
telegram-audio-downloader performance --watch

# Memory-Usage überwachen
telegram-audio-downloader performance --memory
```

### **Automatisierung vorbereiten:**
```bash
# Cron-Job für regelmäßige Downloads (Linux/macOS)
echo "0 */6 * * * cd /path/to/project && ./venv/bin/telegram-audio-downloader download @gruppe --limit=50" | crontab -

# Windows Task Scheduler
# Erstellen Sie eine .bat-Datei mit Ihren Download-Befehlen
```

### **Backup Ihrer Konfiguration:**
```bash
# Wichtige Dateien sichern
cp .env .env.backup
cp -r data/ data_backup/
```

---

## 🎉 **Herzlichen Glückwunsch!**

Sie haben erfolgreich:
✅ Den Telegram Audio Downloader installiert  
✅ Ihre API konfiguriert  
✅ Die Authentifizierung abgeschlossen  
✅ Ihren ersten Download durchgeführt  

**Das Tool ist bereit für den produktiven Einsatz!** 🎵

---

## 📞 **Schnelle Hilfe**

- **Problem?** → [Troubleshooting](Troubleshooting)
- **Feature fehlt?** → [GitHub Issues](https://github.com/Elpablo777/Telegram-Audio-Downloader/issues)
- **Frage?** → [Discussions](https://github.com/Elpablo777/Telegram-Audio-Downloader/discussions)

**Happy Downloading!** 🎵✨