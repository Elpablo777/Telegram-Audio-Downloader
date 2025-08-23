# Mitwirken am Projekt

Vielen Dank für Ihr Interesse am Telegram Audio Downloader! Hier finden Sie Informationen, wie Sie zum Projekt beitragen können.

## 🛠 Entwicklungsumgebung einrichten

1. Das Repository forken und klonen:
   ```bash
   git clone https://github.com/dein-benutzer/telegram-audio-downloader.git
   cd telegram-radio-bot
   ```

2. Virtuelle Umgebung erstellen und aktivieren:
   ```bash
   # Linux/macOS
   python -m venv venv
   source venv/bin/activate
   
   # Windows
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. Abhängigkeiten installieren:
   ```bash
   pip install -e ".[dev]"
   ```

4. `.env`-Datei erstellen:
   ```bash
   cp .env.example .env
   ```
   Tragen Sie Ihre Telegram-API-Daten in der `.env`-Datei ein.

## 🧪 Tests ausführen

```bash
# Alle Tests ausführen
pytest

# Tests mit Coverage-Report
pytest --cov=telegram_audio_downloader tests/

# Bestimmten Test ausführen
pytest tests/test_downloader.py::TestDownloader::test_download_audio
```

## 📝 Code-Stil

- **Black** für Code-Formatierung
- **isort** für Import-Sortierung
- **flake8** für Linting
- **mypy** für statische Typüberprüfung

```bash
# Code formatieren
black src/

# Importe sortieren
isort src/

# Linting durchführen
flake8 src/

# Typüberprüfung
mypy src/
```

## 🔄 Pull Request einreichen

1. Einen neuen Branch erstellen:
   ```bash
   git checkout -b feature/mein-feature
   ```

2. Änderungen committen:
   ```bash
   git add .
   git commit -m "Beschreibung der Änderungen"
   ```

3. Branch pushen:
   ```bash
   git push origin feature/mein-feature
   ```

4. Pull Request auf GitHub erstellen

## 📋 Pull Request Richtlinien

- Beschreiben Sie Ihre Änderungen klar und präzise
- Fügen Sie Tests für neue Funktionen hinzu
- Dokumentieren Sie neue Funktionen mit Docstrings
- Halten Sie den Code sauber und gut strukturiert
- Achten Sie auf die Codequalität

## 📜 Verhaltenskodex

Bitte lesen Sie unseren [Verhaltenskodex](CODE_OF_CONDUCT.md), bevor Sie mitwirken.

## 📬 Fragen?

Bei Fragen öffnen Sie bitte ein Issue oder kontaktieren Sie den Projektbetreuer.
