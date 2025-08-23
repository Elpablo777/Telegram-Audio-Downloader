# 🔧 Troubleshooting Guide

Umfassende Problemlösungen für häufige Issues beim Telegram Audio Downloader.

## 🚨 **Notfall-Schnellhilfe**

### **Tool startet nicht**
```bash
# 1. Virtual Environment prüfen
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# 2. Installation prüfen
pip show telegram-audio-downloader

# 3. Abhängigkeiten neu installieren
pip install --upgrade -r requirements.txt
```

### **"Command not found" Fehler**
```bash
# Tool direkt ausführen
python -m telegram_audio_downloader --help

# Oder vollständiger Pfad
./venv/bin/telegram-audio-downloader  # Linux/macOS
venv\Scripts\telegram-audio-downloader.exe  # Windows
```

### **Authentifizierung schlägt fehl**
```bash
# Session zurücksetzen
telegram-audio-downloader auth --reset

# .env-Datei prüfen
cat .env  # Linux/macOS
type .env # Windows
```

---

## 📋 **Kategorien**

- [Installation Problems](#installation-problems)
- [Authentication Issues](#authentication-issues)  
- [Download Errors](#download-errors)
- [Performance Problems](#performance-problems)
- [Network Issues](#network-issues)
- [Storage & File Problems](#storage--file-problems)
- [Database Issues](#database-issues)
- [Platform-Specific Issues](#platform-specific-issues)

---

## 🛠️ **Installation Problems**

### **Python Version Conflicts**

**Problem**: `python: command not found` oder falsche Version

**Lösung**:
```bash
# Python-Version prüfen
python --version
python3 --version

# Python 3.11+ installieren
# Ubuntu/Debian
sudo apt update && sudo apt install python3.11 python3.11-venv

# macOS (via Homebrew)
brew install python@3.11

# Windows: Von python.org herunterladen
```

### **Pip Installation Failures**

**Problem**: `ERROR: Could not install packages due to an EnvironmentError`

**Lösungen**:
```bash
# 1. Pip aktualisieren
python -m pip install --upgrade pip

# 2. User-Installation verwenden
pip install --user -r requirements.txt

# 3. Bei SSL-Problemen
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt

# 4. Cache löschen
pip cache purge
```

### **Virtual Environment Problems**

**Problem**: Virtual Environment kann nicht erstellt werden

**Lösung**:
```bash
# Alte venv löschen
rm -rf venv  # Linux/macOS
rmdir /s venv  # Windows

# Neu erstellen
python3.11 -m venv venv

# Aktivieren und testen
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

pip --version
```

### **Dependency Conflicts**

**Problem**: `ERROR: pip's dependency resolver does not currently have a necessary feature needed for this project`

**Lösung**:
```bash
# 1. Clean Installation
pip uninstall telegram-audio-downloader telethon -y
pip install --no-deps -r requirements.txt
pip install -e .

# 2. Spezifische Versionen erzwingen
pip install telethon==1.40.0 --force-reinstall

# 3. Compatibility-Check
pip check
```

---

## 🔐 **Authentication Issues**

### **API Credentials Invalid**

**Problem**: `Invalid API_ID or API_HASH`

**Diagnose**:
```bash
# .env-Datei prüfen
cat .env
```

**Lösung**:
```bash
# 1. Korrekte Formate prüfen
# API_ID muss eine Zahl sein (ohne Anführungszeichen)
API_ID=12345678
# API_HASH muss ein String sein (ohne Anführungszeichen)
API_HASH=1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p

# 2. Neue Credentials erstellen
# Gehen Sie zu https://my.telegram.org/apps
# Erstellen Sie eine neue App

# 3. Whitespace/BOM-Probleme
# .env-Datei in plaintext-Editor neu erstellen
```

### **Phone Number Issues**

**Problem**: `Phone number already registered` oder `Invalid phone number`

**Lösung**:
```bash
# 1. Vollständige Nummer mit Ländercode verwenden
# Richtig: +49123456789
# Falsch: 0123456789

# 2. Bei "already registered": Das ist normal!
# Einfach Bestätigungscode eingeben

# 3. Verschiedene Formate testen
+49 123 456789
+49123456789
0049123456789
```

### **2FA/Two-Factor Authentication**

**Problem**: `Two-step verification is enabled`

**Lösung**:
```bash
# 1. Cloud-Passwort eingeben (nicht SMS-Code!)
# Das ist Ihr Telegram-Cloud-Passwort

# 2. Wenn Passwort vergessen
# In Telegram-App: Settings > Privacy and Security > Two-Step Verification > Forgot Password

# 3. 2FA temporär deaktivieren (optional)
# In Telegram-App: Settings > Privacy and Security > Two-Step Verification > Turn Off
```

### **Session File Corruption**

**Problem**: `sqlite3.DatabaseError: database disk image is malformed`

**Lösung**:
```bash
# 1. Session-Dateien löschen
rm *.session  # Linux/macOS
del *.session # Windows

# 2. Neu authentifizieren
telegram-audio-downloader auth

# 3. Session-Backup erstellen (zukünftig)
cp my_session.session my_session.session.backup
```

---

## 📥 **Download Errors**

### **Group Not Found**

**Problem**: `No such peer` oder `Group/Channel not found`

**Diagnose**:
```bash
# Verfügbare Gruppen anzeigen
telegram-audio-downloader groups
```

**Lösung**:
```bash
# 1. Verschiedene Formate testen
telegram-audio-downloader download @musikgruppe
telegram-audio-downloader download musikgruppe
telegram-audio-downloader download "Musik & Sounds"
telegram-audio-downloader download -1001234567890

# 2. Gruppe beitreten zuerst
# Über Telegram-App der Gruppe beitreten

# 3. Public vs Private Groups
# Private Gruppen benötigen Einladung
```

### **FloodWaitError (Rate Limiting)**

**Problem**: `A wait of X seconds is required`

**Lösung**:
```bash
# 1. Das Tool wartet automatisch - nichts tun!

# 2. Parallele Downloads reduzieren
telegram-audio-downloader download @gruppe --parallel=1

# 3. Bei häufigen FloodWaits
telegram-audio-downloader download @gruppe --parallel=2 --limit=10

# 4. Zu andere Tageszeit downloaden
# Nachts/früh morgens ist oft weniger Traffic
```

### **Download Aborts/Interruptions**

**Problem**: Downloads brechen ab oder hängen

**Lösung**:
```bash
# 1. Resume verwenden
telegram-audio-downloader download @gruppe --resume

# 2. Timeout erhöhen
telegram-audio-downloader download @gruppe --timeout=600

# 3. Retry-Verhalten anpassen
telegram-audio-downloader download @gruppe --max-retries=10

# 4. Debug-Modus aktivieren
telegram-audio-downloader --debug download @gruppe --limit=1
```

### **Permission Denied Errors**

**Problem**: `PermissionError: [Errno 13] Permission denied`

**Lösung**:

**Linux/macOS**:
```bash
# Download-Verzeichnis erstellen mit Berechtigungen
mkdir -p downloads
chmod 755 downloads

# Ownership prüfen
ls -la downloads/

# Falls nötig, Ownership ändern
sudo chown -R $USER:$USER downloads/
```

**Windows**:
```powershell
# Als Administrator ausführen
# Oder Berechtigungen ändern
icacls "C:\path\to\downloads" /grant %USERNAME%:F

# Windows Defender Ausnahme
Add-MpPreference -ExclusionPath "C:\path\to\downloads"
```

---

## ⚡ **Performance Problems**

### **Slow Download Speeds**

**Diagnose**:
```bash
# 1. Internet-Speed testen
speedtest-cli

# 2. System-Performance überwachen
telegram-audio-downloader performance --watch

# 3. Disk I/O testen
dd if=/dev/zero of=testfile bs=1M count=1000  # Linux/macOS
```

**Optimierung**:
```bash
# 1. Parallele Downloads erhöhen
telegram-audio-downloader download @gruppe --parallel=8

# 2. SSD verwenden
telegram-audio-downloader download @gruppe --output=/path/to/ssd

# 3. Memory erhöhen
export MAX_MEMORY_MB=2048
telegram-audio-downloader download @gruppe

# 4. Network-Optimierung
# siehe Performance Tuning Guide
```

### **High Memory Usage**

**Problem**: Tool verbraucht zu viel RAM

**Lösung**:
```bash
# 1. Memory-Limit setzen
export MAX_MEMORY_MB=512
telegram-audio-downloader download @gruppe

# 2. Parallele Downloads reduzieren
telegram-audio-downloader download @gruppe --parallel=2

# 3. Garbage Collection aktivieren
export PYTHONGC=1

# 4. Memory-Monitoring
telegram-audio-downloader performance --memory --watch
```

### **CPU Bottlenecks**

**Problem**: Hohe CPU-Last

**Lösung**:
```bash
# 1. Process-Priority reduzieren
nice -n 10 telegram-audio-downloader download @gruppe

# 2. CPU-intensive Features deaktivieren
telegram-audio-downloader download @gruppe --no-verify-checksum --no-metadata

# 3. CPU-Affinity setzen (Linux)
taskset -c 0-1 telegram-audio-downloader download @gruppe
```

---

## 🌐 **Network Issues**

### **Connection Timeouts**

**Problem**: `Connection timed out` oder `Network unreachable`

**Lösung**:
```bash
# 1. Timeout erhöhen
telegram-audio-downloader download @gruppe --timeout=300

# 2. DNS-Server wechseln
# In .env-Datei:
DNS_SERVERS=1.1.1.1,8.8.8.8

# 3. Network-Diagnostics
ping google.com
nslookup api.telegram.org

# 4. Proxy/VPN prüfen
# Falls VPN aktiv, testen ohne VPN
```

### **Proxy/VPN Issues**

**Problem**: Downloads funktionieren nicht über Proxy/VPN

**Lösung**:
```bash
# 1. Proxy in .env konfigurieren
PROXY_TYPE=socks5
PROXY_HOST=127.0.0.1
PROXY_PORT=9050
PROXY_USERNAME=user
PROXY_PASSWORD=pass

# 2. System-Proxy prüfen
echo $HTTP_PROXY
echo $HTTPS_PROXY

# 3. Direct Connection testen
unset HTTP_PROXY HTTPS_PROXY
telegram-audio-downloader download @gruppe --limit=1
```

### **Firewall Blocking**

**Problem**: Verbindung wird von Firewall blockiert

**Lösung**:

**Linux (iptables)**:
```bash
# Telegram-IP-Ranges erlauben
sudo iptables -A OUTPUT -d 149.154.160.0/20 -j ACCEPT
sudo iptables -A OUTPUT -d 91.108.4.0/22 -j ACCEPT
```

**Windows Firewall**:
```powershell
# Python in Firewall-Ausnahmen
New-NetFirewallRule -DisplayName "Python Telegram" -Direction Outbound -Program "C:\path\to\python.exe" -Action Allow
```

**macOS**:
```bash
# Firewall-Status prüfen
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate
```

---

## 💾 **Storage & File Problems**

### **Disk Space Issues**

**Problem**: `No space left on device`

**Diagnose**:
```bash
# Speicherplatz prüfen
df -h .  # Linux/macOS
dir /-s  # Windows

# Große Dateien finden
du -sh downloads/*  # Linux/macOS
```

**Lösung**:
```bash
# 1. Cleanup durchführen
telegram-audio-downloader performance --cleanup

# 2. Alte Downloads löschen
find downloads/ -mtime +30 -delete  # Ältere als 30 Tage

# 3. Temp-Dateien bereinigen
rm -rf /tmp/telegram_*  # Linux/macOS
del /q %TEMP%\telegram_*  # Windows

# 4. Anderes Verzeichnis verwenden
telegram-audio-downloader download @gruppe --output=/other/disk/downloads
```

### **File Corruption**

**Problem**: Heruntergeladene Dateien sind beschädigt

**Diagnose**:
```bash
# Checksum-Verifikation aktivieren
telegram-audio-downloader download @gruppe --verify-checksum

# Datei-Integrität prüfen
file downloads/audio.mp3
ffprobe downloads/audio.mp3
```

**Lösung**:
```bash
# 1. Erneuter Download mit Verifikation
telegram-audio-downloader download @gruppe --force-redownload --verify-checksum

# 2. Disk-Check durchführen (Linux)
sudo fsck /dev/sda1

# 3. Bad Blocks prüfen
sudo badblocks -v /dev/sda1

# 4. SMART-Status prüfen
sudo smartctl -a /dev/sda1
```

### **Filename Issues**

**Problem**: Ungültige Zeichen in Dateinamen

**Lösung**:
```bash
# 1. Automatische Bereinigung ist aktiv
# Sollte automatisch funktionieren

# 2. Manuelle Bereinigung testen
telegram-audio-downloader metadata --repair

# 3. Custom Filename-Pattern
# In .env:
FILENAME_PATTERN="{artist} - {title}.{ext}"
SANITIZE_FILENAMES=true
```

---

## 🗃️ **Database Issues**

### **Database Locked**

**Problem**: `sqlite3.OperationalError: database is locked`

**Lösung**:
```bash
# 1. Alle Instanzen beenden
pkill -f telegram-audio-downloader  # Linux/macOS
taskkill /f /im python.exe  # Windows (vorsichtig!)

# 2. Lock-Files löschen
rm *.db-wal *.db-shm  # Linux/macOS
del *.db-wal *.db-shm  # Windows

# 3. Database-Integrität prüfen
telegram-audio-downloader db --check

# 4. Falls nötig, reparieren
telegram-audio-downloader db --repair
```

### **Database Corruption**

**Problem**: `sqlite3.DatabaseError: database disk image is malformed`

**Lösung**:
```bash
# 1. Backup erstellen (falls möglich)
cp audio_downloader.db audio_downloader.db.corrupt

# 2. Database-Recovery versuchen
sqlite3 audio_downloader.db ".dump" | sqlite3 audio_downloader_recovered.db

# 3. Neuer Start mit leerer Database
mv audio_downloader.db audio_downloader.db.old
telegram-audio-downloader --init-db

# 4. Daten aus Backup wiederherstellen (falls vorhanden)
telegram-audio-downloader db --restore=backup.db
```

### **Slow Database Operations**

**Problem**: Database-Abfragen sind langsam

**Lösung**:
```bash
# 1. Database optimieren
telegram-audio-downloader db --optimize

# 2. Vacuum durchführen
sqlite3 audio_downloader.db "VACUUM;"

# 3. Index-Rebuild
sqlite3 audio_downloader.db "REINDEX;"

# 4. Statistics aktualisieren
sqlite3 audio_downloader.db "ANALYZE;"
```

---

## 🖥️ **Platform-Specific Issues**

### **Windows-spezifische Probleme**

**Problem**: Various Windows-related issues

**Lösungen**:

```powershell
# 1. Execution Policy (PowerShell)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 2. Long Path Support aktivieren
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force

# 3. Windows Defender Ausnahmen
Add-MpPreference -ExclusionPath "C:\path\to\project"
Add-MpPreference -ExclusionProcess "python.exe"

# 4. Antivirus temporär deaktivieren
# Bei Download-Problemen Antivirus testen

# 5. Encoding-Probleme
chcp 65001  # UTF-8 Encoding
```

### **macOS-spezifische Probleme**

**Problem**: macOS security restrictions

**Lösungen**:
```bash
# 1. Gatekeeper für Terminal erlauben
sudo spctl --master-disable

# 2. Python von Homebrew verwenden
brew install python@3.11
/opt/homebrew/bin/python3.11 -m venv venv

# 3. Xcode Command Line Tools
xcode-select --install

# 4. Rosetta 2 für M1/M2 Macs (falls nötig)
softwareupdate --install-rosetta

# 5. Firewall-Ausnahme
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /opt/homebrew/bin/python3.11
```

### **Linux-spezifische Probleme**

**Problem**: Various Linux distribution issues

**Lösungen**:

**Ubuntu/Debian**:
```bash
# 1. System-Updates
sudo apt update && sudo apt upgrade

# 2. Fehlende Abhängigkeiten
sudo apt install python3.11-dev python3.11-venv build-essential

# 3. FFmpeg für Audio-Processing
sudo apt install ffmpeg

# 4. SSL/TLS Libraries
sudo apt install libssl-dev libffi-dev
```

**CentOS/RHEL/Fedora**:
```bash
# 1. Python 3.11 installieren
sudo dnf install python3.11 python3.11-devel

# 2. Development Tools
sudo dnf groupinstall "Development Tools"

# 3. FFmpeg (EPEL Repository)
sudo dnf install epel-release
sudo dnf install ffmpeg
```

**Arch Linux**:
```bash
# 1. System-Update
sudo pacman -Syu

# 2. Abhängigkeiten
sudo pacman -S python python-pip git ffmpeg base-devel

# 3. AUR-Packages (falls nötig)
yay -S python311  # Falls spezifische Version benötigt
```

---

## 🐳 **Docker Issues**

### **Docker Build Failures**

**Problem**: `docker build` schlägt fehl

**Lösung**:
```bash
# 1. Cache löschen
docker system prune -a

# 2. Multi-stage Build debuggen
docker build --target development .

# 3. Build-Logs analysieren
docker build --progress=plain .

# 4. Base-Image aktualisieren
docker pull python:3.11-slim
```

### **Container Runtime Issues**

**Problem**: Container startet nicht oder crashes

**Lösung**:
```bash
# 1. Logs überprüfen
docker-compose logs telegram-audio-downloader

# 2. Interactive Mode für Debugging
docker run -it --rm telegram-audio-downloader /bin/bash

# 3. Volume-Mounts prüfen
docker run -it --rm -v $(pwd)/.env:/app/.env telegram-audio-downloader env

# 4. Memory-Limits prüfen
docker stats telegram-audio-downloader
```

---

## 🔍 **Advanced Debugging**

### **Logging aktivieren**

```bash
# 1. Debug-Level aktivieren
telegram-audio-downloader --debug download @gruppe --limit=1

# 2. Trace-Modus (sehr detailliert)
telegram-audio-downloader --trace download @gruppe --limit=1

# 3. Log-Datei analysieren
tail -f data/telegram_audio_downloader.log

# 4. Spezifische Log-Level
export LOG_LEVEL=DEBUG
telegram-audio-downloader download @gruppe
```

### **Network-Debugging**

```bash
# 1. Telethon-Debug aktivieren
export TELETHON_DEBUG=1
telegram-audio-downloader download @gruppe --limit=1

# 2. Network-Traffic überwachen
sudo tcpdump -i any host api.telegram.org

# 3. HTTP-Proxy für Debugging
export HTTP_PROXY=http://localhost:8080
# Dann mit Burp Suite oder ähnlichem analysieren
```

### **Performance-Profiling**

```bash
# 1. CPU-Profiling
telegram-audio-downloader --profile download @gruppe --limit=5

# 2. Memory-Profiling
telegram-audio-downloader --memory-profile download @gruppe --limit=5

# 3. System-Call-Tracing (Linux)
strace -e trace=file telegram-audio-downloader download @gruppe --limit=1

# 4. Performance-Report generieren
telegram-audio-downloader performance --report --output=perf_report.json
```

---

## 📊 **Diagnostic Commands**

### **System-Check**
```bash
# Vollständiger System-Check
telegram-audio-downloader --system-check

# Mit Details
telegram-audio-downloader --system-check --verbose

# JSON-Output für Automatisierung
telegram-audio-downloader --system-check --json
```

### **Health-Check Script**

Erstellen Sie ein `health_check.sh` Script:

```bash
#!/bin/bash
# Umfassender Health-Check

echo "=== Telegram Audio Downloader Health Check ==="

echo "1. Python Version:"
python --version

echo "2. Virtual Environment:"
which python
which pip

echo "3. Package Installation:"
pip show telegram-audio-downloader

echo "4. Dependencies:"
pip check

echo "5. Configuration:"
if [ -f .env ]; then
    echo ".env exists"
else
    echo "ERROR: .env missing"
fi

echo "6. Database:"
if [ -f audio_downloader.db ]; then
    echo "Database exists"
else
    echo "Database missing (OK for first run)"
fi

echo "7. Network Test:"
ping -c 1 api.telegram.org >/dev/null 2>&1 && echo "Network OK" || echo "Network ERROR"

echo "8. Disk Space:"
df -h .

echo "9. System Resources:"
free -h  # Linux only

echo "10. Tool Test:"
timeout 30 telegram-audio-downloader --help >/dev/null 2>&1 && echo "Tool OK" || echo "Tool ERROR"

echo "=== Health Check Complete ==="
```

Ausführen mit:
```bash
chmod +x health_check.sh
./health_check.sh
```

---

## 📞 **Getting Help**

### **Before Reporting Issues**

1. **Run Health Check**: `./health_check.sh`
2. **Check Logs**: `cat data/telegram_audio_downloader.log | tail -50`
3. **Try Debug Mode**: `telegram-audio-downloader --debug [command]`
4. **Search Existing Issues**: [GitHub Issues](https://github.com/Elpablo777/Telegram-Audio-Downloader/issues)

### **Reporting Bugs**

**Include this Information:**
```bash
# System Info
uname -a  # Linux/macOS
systeminfo  # Windows

# Python Info
python --version
pip --version

# Package Info
pip show telegram-audio-downloader

# Error Logs (last 20 lines)
tail -20 data/telegram_audio_downloader.log

# Debug Output
telegram-audio-downloader --debug [failing-command] 2>&1
```

### **Support Channels**

1. **GitHub Issues**: [Bug Reports & Feature Requests](https://github.com/Elpablo777/Telegram-Audio-Downloader/issues)
2. **GitHub Discussions**: [Questions & Help](https://github.com/Elpablo777/Telegram-Audio-Downloader/discussions)
3. **Wiki**: [Documentation](https://github.com/Elpablo777/Telegram-Audio-Downloader/wiki)
4. **Email**: hannover84@msn.com (for complex issues)

### **Community Help**

- **Stack Overflow**: Tag mit `telegram-audio-downloader`
- **Reddit**: r/learnpython, r/telegram
- **Discord**: Python-Community-Server

---

## 🎯 **Quick Reference**

### **Emergency Commands**
```bash
# Reset everything
rm -rf venv .env *.session *.db
git pull
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt && pip install -e .
cp .env.example .env
# Edit .env with your credentials

# Safe mode start
telegram-audio-downloader --debug --safe-mode download @gruppe --limit=1

# Emergency stop
pkill -f telegram-audio-downloader

# Logs location
less data/telegram_audio_downloader.log
```

### **Recovery Procedures**
```bash
# Database recovery
telegram-audio-downloader db --backup=emergency_backup.db
telegram-audio-downloader db --check --repair

# Session recovery
rm *.session
telegram-audio-downloader auth

# Config recovery
cp .env.example .env
# Re-enter your API credentials
```

---

**Hope this helps! Happy Troubleshooting!** 🔧✨

*This troubleshooting guide is continuously updated based on community feedback and common support requests.*