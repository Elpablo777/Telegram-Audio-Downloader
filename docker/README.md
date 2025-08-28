# Docker-Konfiguration für Telegram Audio Downloader

## Überblick

Dieses Projekt bietet mehrere Möglichkeiten, den Telegram Audio Downloader in Docker auszuführen.

## Verfügbare Services

### Haupt-Service: telegram-audio-downloader

Der Haupt-Service zum Herunterladen von Audiodateien.

```yaml
# Einfacher Download
command: telegram-audio-downloader download --group "meine-gruppe" --limit 10

# Download im Lite-Modus (weniger Ressourcen)
command: telegram-audio-downloader download-lite --group "meine-gruppe" --limit 10

# Interaktiver Modus
command: /bin/bash
```

### Überwachungs-Service: telegram-audio-monitor

Ein separater Service zur Überwachung der Anwendung.

## Volumes und Persistenz

Die folgenden Volumes werden für die Persistenz verwendet:

- `./.env:/app/.env` - API-Zugangsdaten
- `./data:/app/data` - Datenbank und Anwendungsdaten
- `./downloads:/app/downloads` - Heruntergeladene Audiodateien
- `./config:/app/config` - Konfigurationsdateien
- `./logs:/app/logs` - Log-Dateien

## Verwendung

### Einfacher Download

```bash
# Erstelle und starte den Container
docker-compose up --build

# Führe den Download-Befehl aus
docker-compose exec telegram-audio-downloader telegram-audio-downloader download --group "meine-gruppe" --limit 10
```

### Lite-Modus

Der Lite-Modus ist für Systeme mit begrenzten Ressourcen gedacht:

```bash
docker-compose exec telegram-audio-downloader telegram-audio-downloader download-lite --group "meine-gruppe" --limit 10
```

### Interaktiver Modus

```bash
# Starte den Container im interaktiven Modus
docker-compose run --rm telegram-audio-downloader /bin/bash

# Innerhalb des Containers kannst du beliebige Befehle ausführen
telegram-audio-downloader --help
```

## Umgebungsvariablen

Stelle sicher, dass deine `.env`-Datei korrekt konfiguriert ist:

```env
API_ID=deine_api_id
API_HASH=dein_api_hash
SESSION_NAME=dein_session_name
```

## Proxy-Konfiguration

Um einen Proxy zu verwenden, konfiguriere ihn in deiner `config.yaml`:

```yaml
proxy:
  type: socks5
  host: proxy.example.com
  port: 1080
  username: dein_benutzername
  password: dein_passwort
```