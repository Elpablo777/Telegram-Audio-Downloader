# Telegram Audio Downloader

[![Build Status](https://github.com/yourusername/telegram-audio-downloader/workflows/CI/badge.svg)](https://github.com/yourusername/telegram-audio-downloader/actions)
[![Coverage Status](https://codecov.io/gh/yourusername/telegram-audio-downloader/branch/main/graph/badge.svg)](https://codecov.io/gh/yourusername/telegram-audio-downloader)
[![License](https://img.shields.io/github/license/yourusername/telegram-audio-downloader)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![Code Style](https://img.shields.io/badge/code%20style-black-black)](https://github.com/psf/black)
[![Security](https://img.shields.io/badge/security-bandit-brightgreen)](https://github.com/PyCQA/bandit)

Ein leistungsstarkes Tool zum Herunterladen und Verwalten von Audiodateien aus Telegram-Gruppen.

## Funktionen

- 🔒 **Sichere Authentifizierung** mit Telegram API
- ⚡ **Parallele Downloads** mit anpassbarer Anzahl gleichzeitiger Verbindungen
- 🔄 **Fortsetzbare Downloads** mit Prüfsummenprüfung
- 🎵 **Erweiterte Metadaten-Extraktion** aus ID3-Tags, Vorbis-Kommentaren und Telegram-Metadaten
- 📁 **Intelligentes Caching** mit mehrstufigem Caching (Speicher, Festplatte, CDN)
- 📝 **Erweiterte Dateinamen-Generierung** mit anpassbaren Vorlagen, dynamischen Platzhaltern und automatischer Nummerierung
- 📦 **Batch-Verarbeitung** mit priorisierter Warteschlange
- 📊 **Erweiterte Protokollierung** mit detaillierten Fehlerberichten und Performance-Metriken
- 🔁 **Automatische Formatkonvertierung** zwischen MP3, M4A, FLAC, OPUS
- 🖥️ **Erweiterte Benutzerinteraktion** mit Fortschrittsbalken und Benachrichtigungen
- 🔐 **Erweiterte Sicherheitsfunktionen** mit Dateiüberprüfung und Zugriffskontrolle
- 📋 **Intelligente Warteschlange** mit dynamischer Priorisierung
- 🔔 **Erweiterte Benachrichtigungen** über Desktop-Benachrichtigungen und E-Mail
- 📂 **Automatische Kategorisierung** durch Metadatenanalyse
- 💬 **Interaktiver Modus** mit Befehlsvervollständigung
- 🎨 **Farbkodierung** für verschiedene Nachrichtentypen
- ⌨️ **Tastaturkürzel** für häufige Aktionen
- ❓ **Kontextbezogene Hilfe** mit Beispielen
- 🌍 **Mehrsprachige Unterstützung** (Englisch, Deutsch, Spanisch, Französisch)
- ♿ **Barrierefreiheit** mit Tastaturnavigation und Screenreader-Unterstützung
- 👥 **Benutzerprofilierung** mit Profilverwaltung
- 🔍 **Erweiterte Suche** mit Filtern nach Metadaten
- 🎛️ **Benutzerdefinierte Tastenkombinationen**
- 🔤 **Automatische Vervollständigung**
- 🎯 **Visuelles Feedback** mit Animationen
- ✅ **Eingabevalidierung** mit hilfreichen Fehlermeldungen
- 📚 **Benutzerführung** mit Tutorial und Assistenten
- 🎨 **Anpassbare Oberfläche** mit Themes

## Kompatibilitätshinweis

**Wichtig:** Die automatische Formatkonvertierung (MP3, M4A, FLAC, OPUS) erfordert die `pydub`-Bibliothek, die derzeit nicht mit Python 3.13 kompatibel ist. Wenn Sie die Formatkonvertierungsfunktionen nutzen möchten, verwenden Sie bitte Python 3.12 oder älter.

Für alle anderen Funktionen ist Python 3.8 oder höher erforderlich.

## Installation

### Voraussetzungen

- Python 3.8 oder höher
- Telegram API-Zugangsdaten (API-ID und API-Hash)

### Installation mit pip

```bash
pip install telegram-audio-downloader
```

### Installation aus dem Quellcode

```bash
git clone https://github.com/yourusername/telegram-audio-downloader.git
cd telegram-audio-downloader
pip install -r requirements.txt
```

## Konfiguration

Erstellen Sie eine `.env`-Datei im Projektverzeichnis mit Ihren Telegram-API-Zugangsdaten:

```env
API_ID=your_api_id
API_HASH=your_api_hash
SESSION_NAME=your_session_name
```

## Verwendung

### Grundlegende Verwendung

```bash
# Einfacher Download aus einer Gruppe
telegram-audio-downloader download "Gruppenname"

# Download mit Limit
telegram-audio-downloader download "Gruppenname" --limit 10

# Download in ein bestimmtes Verzeichnis
telegram-audio-downloader download "Gruppenname" --output /pfad/zum/verzeichnis

# Download mit benutzerdefinierter Dateinamen-Vorlage
telegram-audio-downloader download "Gruppenname" --filename-template "$artist - $title ($year)"
```

### Batch-Verarbeitung

Die Batch-Verarbeitung ermöglicht es, mehrere Download-Aufträge zu planen und automatisch zu verarbeiten:

```bash
# Füge einen Download-Auftrag zur Batch-Warteschlange hinzu
telegram-audio-downloader batch-add --group "Gruppe1" --limit 5 --priority HIGH

# Füge einen weiteren Download-Auftrag hinzu
telegram-audio-downloader batch-add --group "Gruppe2" --output "/pfad/zu/gruppe2" --parallel 2 --priority NORMAL

# Liste alle Batch-Aufträge in der Warteschlange auf
telegram-audio-downloader batch-list

# Verarbeite alle Batch-Aufträge
telegram-audio-downloader batch-process --max-concurrent 2
```

Verfügbare Prioritätsstufen:
- `LOW`: Niedrige Priorität
- `NORMAL`: Normale Priorität (Standard)
- `HIGH`: Hohe Priorität
- `CRITICAL`: Kritische Priorität

### Fortgeschrittene Verwendung

```bash
# Parallele Downloads mit benutzerdefinierter Anzahl
telegram-audio-downloader download "Gruppenname" --parallel 5

# Suche in heruntergeladenen Dateien
telegram-audio-downloader search "Suchbegriff"

# Anzeige der Download-Historie
telegram-audio-downloader history

# Konfiguration anzeigen
telegram-audio-downloader config show

# Konfiguration aktualisieren
telegram-audio-downloader config set max_concurrent_downloads 5
```

### Dateinamen-Vorlagen

Der Telegram Audio Downloader unterstützt anpassbare Dateinamen-Vorlagen mit verschiedenen Platzhaltern:

- `$title` - Titel des Tracks
- `$artist` - Künstler/Interpret
- `$album` - Albumname
- `$year` - Erscheinungsjahr
- `$genre` - Genre
- `$track_number` - Track-Nummer
- `$disc_number` - Disc-Nummer
- `$date` - Datum
- `$composer` - Komponist
- `$performer` - Interpret
- `$duration` - Dauer
- `$bitrate` - Bitrate
- `$sample_rate` - Sample-Rate
- `$channels` - Anzahl der Kanäle
- `$file_size` - Dateigröße
- `$file_extension` - Dateiendung
- `$message_id` - Telegram-Nachrichten-ID
- `$group_name` - Gruppenname
- `$group_id` - Gruppen-ID
- `$download_date` - Download-Datum
- `$counter` - Automatischer Zähler

Beispiele für Vorlagen:

```bash
# Einfache Vorlage
telegram-audio-downloader download "Gruppe" --filename-template "$artist - $title"

# Detaillierte Vorlage
telegram-audio-downloader download "Gruppe" --filename-template "$artist - $album ($year) - $track_number. $title"

# Mit Zähler
telegram-audio-downloader download "Gruppe" --filename-template "$counter. $artist - $title"
```

## Entwicklung

### Abhängigkeiten installieren

```bash
pip install -r requirements-dev.txt
```

### Tests ausführen

```bash
# Alle Tests ausführen
python -m pytest

# Tests mit Coverage
python -m pytest --cov=src

# Spezifische Testdatei ausführen
python -m pytest tests/test_downloader.py
```

### Code-Qualität prüfen

```bash
# Linting
flake8 src

# Formatierung prüfen
black --check src

# Typ-Prüfung
mypy src
```

## Lizenz

Dieses Projekt ist unter der MIT-Lizenz lizenziert - siehe die [LICENSE](LICENSE) Datei für Details.

## Mitwirken

Beiträge sind willkommen! Bitte lesen Sie [CONTRIBUTING.md](CONTRIBUTING.md) für Details zu unserem Code of Conduct und dem Prozess für das Einreichen von Pull Requests.

## Autoren

- **Ihr Name** - *Erster Maintainer* - [yourusername](https://github.com/yourusername)

Siehe auch die Liste der [Mitwirkenden](https://github.com/yourusername/telegram-audio-downloader/contributors) die an diesem Projekt teilgenommen haben.

## Danksagung

- [Telethon](https://github.com/LonamiWebs/Telethon) für die Telegram-API-Implementierung
- [Mutagen](https://github.com/quodlibet/mutagen) für die Metadaten-Extraktion
- [Click](https://github.com/pallets/click) für die CLI-Implementierung
- [Rich](https://github.com/Textualize/rich) für die Terminal-Benutzeroberfläche