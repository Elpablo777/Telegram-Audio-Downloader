# Fortschrittliche Download-Wiederaufnahme

Die fortgeschrittene Download-Wiederaufnahme ist eine robuste Funktion des Telegram Audio Downloaders, die sicherstellt, dass Downloads auch bei Unterbrechungen zuverlässig fortgesetzt werden können.

## Funktionen

### Prüfsummenprüfung
- **Integritätsverifikation**: Jeder Download wird mit einer SHA-256 Prüfsumme versehen
- **Automatische Validierung**: Vor der Wiederaufnahme wird die Dateiintegrität überprüft
- **Fehlererkennung**: Beschädigte Downloads werden automatisch neu gestartet

### Teilweiser Download
- **Effiziente Fortsetzung**: Downloads werden genau an der Stelle fortgesetzt, an der sie unterbrochen wurden
- **Byte-genauer Fortschritt**: Der exakte Download-Offset wird in der Datenbank gespeichert
- **Platzsparend**: Kein erneuter Download bereits heruntergeladener Daten

### Automatische Wiederholung
- **Intelligente Retry-Logik**: Bei Fehlern werden Downloads automatisch erneut versucht
- **Exponentielles Backoff**: Wartezeiten zwischen Wiederholungen erhöhen sich progressiv
- **Maximale Versuche**: Konfigurierbare Obergrenze für Wiederholungsversuche

### Detaillierte Protokollierung
- **Fortschrittsverfolgung**: Echtzeit-Protokollierung des Download-Fortschritts
- **Audit-Trail**: Vollständige Ereignisprotokollierung für jeden Download
- **Performance-Metriken**: Erfassung von Download-Geschwindigkeiten und -Statistiken

## Technische Implementierung

### Resume-Manager
Der `AdvancedResumeManager` ist die zentrale Komponente für die Download-Wiederaufnahme:

```python
from src.telegram_audio_downloader.advanced_resume import get_resume_manager

# Initialisierung
resume_manager = get_resume_manager(download_dir)

# Laden des Resume-Zustands
resume_info = resume_manager.load_resume_state(file_id, file_path, total_bytes)

# Prüfen, ob Wiederaufnahme möglich ist
if resume_manager.can_resume(file_id):
    print(f"Download kann bei {resume_info.downloaded_bytes} Bytes fortgesetzt werden")
```

### Datenbank-Integration
Resume-Informationen werden in der `audio_files` Tabelle gespeichert:

- `resume_offset`: Anzahl bereits heruntergeladener Bytes
- `resume_checksum`: SHA-256 Prüfsumme der heruntergeladenen Daten

### Fehlerbehandlung
Das System implementiert eine robuste Fehlerbehandlung:

1. **Prüfsummenfehler**: Bei Prüfsummenfehlern wird der Download neu gestartet
2. **Netzwerkfehler**: Automatische Wiederholung mit exponentiellem Backoff
3. **Dateisystemfehler**: Validierung der Dateiintegrität vor Wiederaufnahme

## Konfiguration

Die Resume-Funktionalität kann über die Konfigurationsdatei angepasst werden:

```ini
[download]
# Maximale Wiederholungsversuche
max_retries = 3

# Wartezeit zwischen Wiederholungen (in Sekunden)
retry_delay = 5

# Prüfsummenalgorithmus
checksum_algorithm = sha256
```

## Nutzung

Die Wiederaufnahme-Funktionalität ist vollständig automatisch und erfordert keine manuelle Interaktion. Bei Unterbrechungen wird der Download beim nächsten Start automatisch fortgesetzt.

### Monitoring
Der Fortschritt kann über die API oder CLI überwacht werden:

```bash
# CLI-Befehl zur Anzeige des Download-Fortschritts
python -m telegram_audio_downloader --progress

# API-Endpunkt für Fortschrittsinformationen
GET /api/v1/downloads/progress
```

## Best Practices

1. **Regelmäßige Backups**: Sicherung der Datenbank zur Wiederherstellung von Resume-Informationen
2. **Stabile Netzwerkverbindung**: Verwendung stabiler Netzwerkverbindungen für unterbrechungsfreie Downloads
3. **Ausreichend Speicherplatz**: Überwachung des verfügbaren Speicherplatzes

## Fehlerbehebung

### Häufige Probleme

**Problem**: Download startet immer von vorne
**Lösung**: Prüfen Sie die Dateiberechtigungen und die Datenbankverbindung

**Problem**: Prüfsummenfehler
**Lösung**: Löschen Sie die teilweise heruntergeladene Datei und starten Sie den Download neu

### Logs
Überprüfen Sie die Log-Dateien für detaillierte Fehlerinformationen:

```bash
# Anzeige der letzten 100 Log-Einträge
tail -n 100 logs/telegram_audio_downloader.log
```