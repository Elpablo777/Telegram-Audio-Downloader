# Konfiguration

Der Telegram Audio Downloader unterstützt mehrere Methoden zur Konfiguration:

## Konfigurationsquellen

Die Konfiguration wird in folgender Prioritätsreihenfolge geladen:

1. **Befehlszeilenargumente** - Höchste Priorität
2. **Umgebungsvariablen** 
3. **Konfigurationsdatei**
4. **Standardwerte** - Niedrigste Priorität

## Umgebungsvariablen

Folgende Umgebungsvariablen werden unterstützt:

| Variable | Beschreibung | Standardwert |
|----------|-------------|--------------|
| `API_ID` | Telegram API ID | Erforderlich |
| `API_HASH` | Telegram API Hash | Erforderlich |
| `SESSION_NAME` | Name der Session-Datei | `telegram_audio_downloader` |
| `DOWNLOAD_DIR` | Download-Verzeichnis | `downloads` |
| `MAX_CONCURRENT_DOWNLOADS` | Maximale parallele Downloads | `3` |
| `RATE_LIMIT_DELAY` | Verzögerung zwischen Anfragen (Sekunden) | `0.1` |
| `DB_PATH` | Pfad zur Datenbankdatei | `data/downloads.db` |
| `LOG_DIR` | Verzeichnis für Log-Dateien | `logs` |
| `LOG_LEVEL` | Log-Level (DEBUG, INFO, WARNING, ERROR) | `INFO` |
| `MAX_MEMORY_MB` | Maximale Speichernutzung (MB) | `1024` |
| `CACHE_SIZE` | Größe des Datei-Caches | `50000` |
| `ENCRYPTION_KEY` | Schlüssel für sensible Daten | `null` |

## Konfigurationsdateien

Der Downloader unterstützt verschiedene Konfigurationsformate:

### JSON

```json
{
  "api_id": "YOUR_API_ID",
  "api_hash": "YOUR_API_HASH",
  "session_name": "telegram_audio_downloader",
  "download_dir": "downloads",
  "max_concurrent_downloads": 3,
  "rate_limit_delay": 0.1,
  "db_path": "data/downloads.db",
  "log_dir": "logs",
  "log_level": "INFO",
  "max_memory_mb": 1024,
  "cache_size": 50000,
  "encryption_key": null
}
```

### YAML

```yaml
api_id: "YOUR_API_ID"
api_hash: "YOUR_API_HASH"
session_name: "telegram_audio_downloader"
download_dir: "downloads"
max_concurrent_downloads: 3
rate_limit_delay: 0.1
db_path: "data/downloads.db"
log_dir: "logs"
log_level: "INFO"
max_memory_mb: 1024
cache_size: 50000
encryption_key: null
```

### INI

```ini
[DEFAULT]
api_id = YOUR_API_ID
api_hash = YOUR_API_HASH
session_name = telegram_audio_downloader
download_dir = downloads
max_concurrent_downloads = 3
rate_limit_delay = 0.1
db_path = data/downloads.db
log_dir = logs
log_level = INFO
max_memory_mb = 1024
cache_size = 50000
encryption_key = None
```

## Verwendung

### Mit Konfigurationsdatei

```bash
python -m telegram_audio_downloader --config /path/to/config.json download @music_group
```

### Mit Umgebungsvariablen

```bash
export API_ID=your_api_id
export API_HASH=your_api_hash
python -m telegram_audio_downloader download @music_group
```

### Mit Befehlszeilenargumenten

```bash
python -m telegram_audio_downloader --max-concurrent-downloads 5 download @music_group
```

## Sicherheit

Für sensible Daten wie API-Schlüssel wird die Verwendung von Umgebungsvariablen oder sicheren Konfigurationsmethoden empfohlen.

## Validierung

Die Konfiguration wird automatisch validiert. Bei ungültigen Werten wird eine Fehlermeldung angezeigt.