# API Dokumentation - Telegram Audio Downloader

## Überblick

Das Telegram Audio Downloader Tool bietet sowohl eine Kommandozeilen-Schnittstelle (CLI) als auch programmierbare APIs für den systematischen Download und die Verwaltung von Audiodateien aus Telegram-Gruppen.

## CLI-Befehle

### Download-Befehl

```bash
telegram-audio-downloader download [OPTIONEN] GRUPPE
```

**Parameter:**
- `GRUPPE` (erforderlich): Name oder ID der Telegram-Gruppe

**Optionen:**
- `--limit INTEGER`: Maximale Anzahl der zu verarbeitenden Nachrichten
- `--output, -o PATH`: Ausgabeverzeichnis (Standard: downloads)
- `--parallel, -p INTEGER`: Anzahl paralleler Downloads (Standard: 3)

**Beispiele:**
```bash
# Einfacher Download
telegram-audio-downloader download "Musik Gruppe"

# Mit benutzerdefinierten Optionen
telegram-audio-downloader download "Musik Gruppe" --output /mein/pfad --parallel 5 --limit 100
```

### Such-Befehl

```bash
telegram-audio-downloader search [OPTIONEN] [SUCHBEGRIFF]
```

**Optionen:**
- `--group, -g TEXT`: Filtere nach Gruppe
- `--status TEXT`: Filtere nach Status (pending, downloading, completed, failed, skipped)
- `--metadata, -m`: Zeige erweiterte Metadaten
- `--fuzzy, -f`: Aktiviere Fuzzy-Suche
- `--min-size TEXT`: Minimale Dateigröße (z.B. "5MB")
- `--max-size TEXT`: Maximale Dateigröße (z.B. "100MB")
- `--format TEXT`: Audioformat (mp3, flac, etc.)
- `--duration-min INTEGER`: Minimale Dauer in Sekunden
- `--duration-max INTEGER`: Maximale Dauer in Sekunden
- `--limit INTEGER`: Maximale Anzahl Ergebnisse (Standard: 10)
- `--all`: Zeige alle Ergebnisse

**Beispiele:**
```bash
# Basis-Suche
telegram-audio-downloader search "Mozart"

# Erweiterte Suche
telegram-audio-downloader search "Beethoven" --fuzzy --min-size 5MB --format flac --metadata

# Nach Gruppe filtern
telegram-audio-downloader search --group "Klassik" --status completed
```

### Metadaten-Befehl

```bash
telegram-audio-downloader metadata [OPTIONEN]
```

**Optionen:**
- `--update, -u`: Aktualisiere Metadaten aus Dateien
- `--verify, -v`: Verifiziere Checksums
- `--file-id TEXT`: Analysiere nur bestimmte Datei

**Beispiele:**
```bash
# Metadaten aktualisieren
telegram-audio-downloader metadata --update

# Checksums verifizieren
telegram-audio-downloader metadata --verify

# Beides für alle Dateien
telegram-audio-downloader metadata --update --verify
```

### Weitere Befehle

- `telegram-audio-downloader groups`: Zeigt alle bekannten Gruppen
- `telegram-audio-downloader stats`: Zeigt Download-Statistiken

## Python API

### AudioDownloader Klasse

```python
from telegram_audio_downloader import AudioDownloader

# Initialisierung
downloader = AudioDownloader(
    download_dir="downloads",
    max_concurrent_downloads=3
)

# Client initialisieren
await downloader.initialize_client()

# Downloads starten
await downloader.download_audio_files("Gruppe Name", limit=100)

# Ressourcen freigeben
await downloader.close()
```

#### Methoden

##### `initialize_client()`
Initialisiert den Telegram-Client mit API-Credentials aus Umgebungsvariablen.

**Umgebungsvariablen:**
- `API_ID`: Telegram API ID
- `API_HASH`: Telegram API Hash
- `SESSION_NAME`: Session-Name (optional, Standard: "session")

##### `download_audio_files(group_name, limit=None)`
Lädt alle Audiodateien aus der angegebenen Gruppe herunter.

**Parameter:**
- `group_name` (str): Name oder ID der Telegram-Gruppe
- `limit` (int, optional): Maximale Anzahl der Nachrichten

##### `close()`
Schließt die Verbindung zum Telegram-Client.

### Datenbank-Modelle

#### AudioFile

Repräsentiert eine heruntergeladene Audiodatei.

**Wichtige Felder:**
- `file_id`: Eindeutige Telegram-Datei-ID
- `file_name`: Lokaler Dateiname
- `title`: Titel des Tracks
- `performer`: Künstler/Interpret
- `duration`: Dauer in Sekunden
- `file_size`: Dateigröße in Bytes
- `status`: Download-Status
- `local_path`: Pfad zur lokalen Datei
- `checksum_md5`: MD5-Checksum
- `downloaded_at`: Download-Zeitstempel

**Methoden:**
- `is_downloaded`: Prüft, ob erfolgreich heruntergeladen
- `is_partially_downloaded`: Prüft auf teilweisen Download
- `download_progress`: Fortschritt in Prozent
- `can_resume_download()`: Prüft Resume-Möglichkeit

#### TelegramGroup

Repräsentiert eine Telegram-Gruppe.

**Felder:**
- `group_id`: Telegram-Gruppen-ID
- `title`: Gruppentitel
- `username`: Gruppen-Benutzername
- `last_checked`: Letzte Überprüfung

### Utility-Funktionen

```python
from telegram_audio_downloader import utils

# Dateinamen bereinigen
safe_name = utils.sanitize_filename("Problematic/Name<>.mp3")

# Metadaten extrahieren
metadata = utils.extract_audio_metadata("/path/to/file.mp3")

# Dateigröße formatieren
size_str = utils.format_file_size(1048576)  # "1.0 MB"

# Dauer formatieren
duration_str = utils.format_duration(185)  # "03:05"

# Hash berechnen
file_hash = utils.calculate_file_hash("/path/to/file.mp3", "md5")
```

## Konfiguration

### Umgebungsvariablen

Erstelle eine `.env`-Datei im Projektverzeichnis:

```env
# Telegram API credentials (erforderlich)
# Erhältlich von https://my.telegram.org/apps
API_ID=12345678
API_HASH=abcd1234efgh5678ijkl90mnop

# Session-Name (optional)
SESSION_NAME=my_session

# Datenbankpfad (optional)
DB_PATH=data/audio_downloader.db
```

### Konfigurationsdatei

Optional: `config/default.ini` für erweiterte Einstellungen:

```ini
[settings]
default_download_dir = downloads
max_concurrent_downloads = 3
max_file_size_mb = 500
download_delay = 1.0
extract_metadata = true
resumable_downloads = true

[database]
path = data/audio_downloader.db
backup_interval_days = 7

[logging]
level = INFO
file = data/telegram_audio_downloader.log
max_file_size_mb = 10
backup_count = 3
```

## Fehlerbehandlung

### Häufige Fehler

1. **FloodWaitError**: Zu viele Anfragen an Telegram
   - Das Tool wartet automatisch die vorgeschriebene Zeit
   - Reduziere `max_concurrent_downloads`

2. **Authentifizierungsfehler**: Ungültige API-Credentials
   - Überprüfe API_ID und API_HASH in `.env`
   - Lösche alte Session-Dateien

3. **Speicherplatz**: Nicht genug Festplattenspeicher
   - Das Tool prüft automatisch verfügbaren Speicher
   - Bereinige alte Downloads oder ändere `download_dir`

4. **Netzwerkfehler**: Verbindungsprobleme
   - Das Tool versucht automatisch Wiederholung
   - Prüfe Internetverbindung

### Logging

Logs werden standardmäßig in `data/telegram_audio_downloader.log` gespeichert.

**Log-Level:**
- `DEBUG`: Detaillierte Debug-Informationen
- `INFO`: Allgemeine Informationen
- `WARNING`: Warnungen (FloodWait, etc.)
- `ERROR`: Fehler die behandelt werden können
- `CRITICAL`: Schwere Fehler

## Performance-Optimierung

### Download-Geschwindigkeit

1. **Parallele Downloads**: 3-5 gleichzeitige Downloads sind optimal
2. **Netzwerkbandbreite**: Bessere Verbindung = schnellere Downloads
3. **Rate-Limiting**: Telegram begrenzt die Download-Geschwindigkeit

### Speicher-Nutzung

1. **Batch-Verarbeitung**: Große Gruppen werden in Batches verarbeitet
2. **Streaming**: Große Dateien werden gestreamt, nicht komplett in den Speicher geladen
3. **Garbage Collection**: Automatische Speicherbereinigung

### Datenbank-Performance

1. **Indizierung**: Wichtige Felder sind indiziert für schnelle Suchen
2. **WAL-Modus**: SQLite nutzt Write-Ahead-Logging für bessere Performance
3. **Vacuuming**: Periodische Datenbankoptimierung empfohlen

## Docker-Nutzung

### Build und Run

```bash
# Image bauen
docker build -t telegram-audio-downloader .

# Container starten
docker run --rm -it \
    -v $(pwd)/.env:/app/.env \
    -v $(pwd)/downloads:/app/downloads \
    -v $(pwd)/data:/app/data \
    telegram-audio-downloader

# Mit docker-compose
docker-compose up --build
```

### Environment für Docker

```
version: '3.8'
services:
  downloader:
    build: .
    volumes:
      - ./.env:/app/.env
      - ./downloads:/app/downloads
      - ./data:/app/data
    environment:
      - PYTHONPATH=/app
```

## Erweiterte Nutzung

### Custom Scripts

```python
import asyncio
from telegram_audio_downloader import AudioDownloader
from telegram_audio_downloader.models import AudioFile, DownloadStatus

async def custom_download():
    downloader = AudioDownloader(max_concurrent_downloads=5)
    
    try:
        await downloader.initialize_client()
        await downloader.download_audio_files("Meine Gruppe")
        
        # Statistiken anzeigen
        completed = AudioFile.select().where(
            AudioFile.status == DownloadStatus.COMPLETED.value
        ).count()
        print(f"Downloads abgeschlossen: {completed}")
        
    finally:
        await downloader.close()

# Ausführen
asyncio.run(custom_download())
```

### Webhook-Integration

Das Tool kann in Webhook-Systeme integriert werden für automatische Downloads:

```python
from telegram_audio_downloader import AudioDownloader
from flask import Flask, request

app = Flask(__name__)

@app.route('/download', methods=['POST'])
async def trigger_download():
    data = request.get_json()
    group_name = data.get('group')
    
    downloader = AudioDownloader()
    await downloader.initialize_client()
    await downloader.download_audio_files(group_name)
    await downloader.close()
    
    return {"status": "success"}
```

## Support

Bei Problemen oder Fragen:

1. Prüfe die Logs in `data/telegram_audio_downloader.log`
2. Aktiviere Debug-Modus: `--debug`
3. Prüfe die GitHub Issues
4. Erstelle ein neues Issue mit:
   - Fehlermeldung
   - Verwendete Befehle
   - System-Informationen
   - Log-Auszüge (ohne sensible Daten)
