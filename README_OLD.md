# Telegram Audio Downloader

Ein leistungsstarkes Tool zum Herunterladen und Verwalten von Audiodateien aus Telegram-Gruppen.

## 📋 Funktionen

- Automatisches Herunterladen von Audiodateien aus Telegram-Gruppen
- Unterstützung für verschiedene Audioformate (MP3, M4A, OGG, FLAC, WAV)
- Metadaten-Extraktion und -Verwaltung
- Fortschrittsanzeige
- Fortsetzbarer Download
- Parallele Downloads
- Datenbankgestützte Verwaltung heruntergeladener Dateien
- Kommandozeilenoberfläche

## 🚀 Installation

1. Stelle sicher, dass Python 3.8+ installiert ist
2. Klone das Repository:
   ```bash
   git clone https://github.com/dein-benutzer/telegram-audio-downloader.git
   cd telegram-audio-downloader
   ```
3. Installiere die Abhängigkeiten:
   ```bash
   pip install -r requirements.txt
   ```
4. Erstelle eine `.env`-Datei im Hauptverzeichnis mit deinen Telegram-API-Daten:
   ```
   API_ID=deine_api_id
   API_HASH=dein_api_hash
   SESSION_NAME=session_name
   ```

## 🛠 Verwendung

```bash
# Herunterladen aller Audiodateien aus einer Gruppe
python -m telegram_audio_downloader.cli download --group "Gruppenname"

# Nach bestimmten Audiodateien suchen
python -m telegram_audio_downloader.cli search "Suchbegriff"

# Hilfe anzeigen
python -m telegram_audio_downloader.cli --help
```

## 📂 Projektstruktur

```
.
├── config/               # Konfigurationsdateien
├── data/                 # Datenbank und heruntergeladene Dateien
├── docker/               # Docker-Konfiguration
├── docs/                 # Detaillierte Dokumentation
├── src/                  # Quellcode
│   └── telegram_audio_downloader/
│       ├── __init__.py
│       ├── cli.py        # Hauptskript
│       ├── database.py   # Datenbankmodelle
│       ├── downloader.py # Download-Logik
│       ├── models.py     # Datenmodelle
│       └── utils.py      # Hilfsfunktionen
├── tests/                # Tests
├── .env.example         # Beispiel-Umgebungsvariablen
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
└── README.md
```

## 📝 Dokumentation

Detaillierte Dokumentation findest du im [docs/](docs/) Verzeichnis.

## 📄 Lizenz

Dieses Projekt steht unter der MIT-Lizenz - siehe die [LICENSE](LICENSE) Datei für Details.

## 🙏 Danksagung

- [Telethon](https://docs.telethon.dev/) für die leistungsstarke Telegram-Client-Bibliothek
- Allen Mitwirkenden und Unterstützern
