# 🤝 Mitwirken

Vielen Dank, dass Sie sich dafür entschieden haben, zum Telegram Audio Downloader beizutragen! Wir freuen uns über alle Arten von Beiträgen.

## 📋 Verhaltenskodex

Bitte lesen Sie unseren [Verhaltenskodex](CODE_OF_CONDUCT.md), bevor Sie mit der Mitarbeit beginnen.

## 🚀 Erste Schritte

1. Forken Sie das Repository
2. Klonen Sie Ihren Fork
3. Erstellen Sie einen Feature-Branch (`git checkout -b feature/AmazingFeature`)
4. Committen Sie Ihre Änderungen (`git commit -m 'Add some AmazingFeature'`)
5. Pushen Sie zum Branch (`git push origin feature/AmazingFeature`)
6. Öffnen Sie einen Pull Request

## 📊 Entwicklungsumgebung einrichten

```bash
# Repository klonen
git clone https://github.com/Elpablo777/telegram-audio-downloader.git
cd telegram-audio-downloader

# Virtuelle Umgebung erstellen
python -m venv venv

# Virtuelle Umgebung aktivieren
# Windows: venv\Scripts\activate
# Linux/macOS: source venv/bin/activate

# Entwicklungsabhängigkeiten installieren
pip install -e ".[dev]"

# Tests ausführen, um sicherzustellen, dass alles funktioniert
python -m pytest
```

## 🧪 Tests

Wir haben eine umfassende Testsuite, die folgende Arten von Tests umfasst:

- **Unit-Tests**: Testen einzelne Funktionen und Klassen
- **Integrationstests**: Testen die Interaktion zwischen Komponenten
- **End-to-End-Tests**: Testen den kompletten Download-Workflow

### Tests ausführen

```bash
# Alle Tests ausführen
python -m pytest

# Tests mit Coverage
python -m pytest --cov=src

# Spezifische Testdatei ausführen
python -m pytest tests/test_downloader.py

# Tests parallel ausführen (schneller)
python -m pytest -n auto
```

## 📝 Code-Qualität

Wir halten uns an hohe Standards für Code-Qualität:

### Python-Stil
- PEP 8 Konformität
- Type Hints für alle Funktionen und Klassen
- Docstrings für alle öffentlichen Funktionen und Klassen

### Tools
```bash
# Code formatieren
black src/ tests/

# Importe sortieren
isort src/ tests/

# Linting
flake8 src/ tests/

# Type-Checking
mypy src/
```

## 📚 Dokumentation

- Alle neuen Funktionen müssen dokumentiert werden
- Aktualisieren Sie die README.md, wenn sich die CLI ändert
- Fügen Sie Docstrings zu neuen Funktionen hinzu

## 🐛 Fehlerberichte und Feature-Anfragen

### Fehlerberichte
Wenn Sie einen Fehler finden:
1. Überprüfen Sie, ob der Fehler bereits gemeldet wurde
2. Erstellen Sie ein neues Issue mit:
   - Eine klare und beschreibende Titel
   - Eine detaillierte Beschreibung des Problems
   - Schritte zur Reproduktion
   - Erwartetes vs. tatsächliches Verhalten
   - Informationen über Ihre Umgebung (Betriebssystem, Python-Version, etc.)

### Feature-Anfragen
Für neue Funktionen:
1. Erstellen Sie ein Issue, das die neue Funktion beschreibt
2. Erklären Sie, warum diese Funktion nützlich wäre
3. Beschreiben Sie die geplante Implementierung (wenn möglich)

## 📦 Pull Requests

### Richtlinien
- Halten Sie PRs klein und fokussiert
- Schreiben Sie aussagekräftige Commit-Nachrichten
- Fügen Sie Tests für neue Funktionen hinzu
- Aktualisieren Sie die Dokumentation bei Bedarf
- Stellen Sie sicher, dass alle Tests bestanden werden

### Prozess
1. Erstellen Sie einen Fork des Repositories
2. Erstellen Sie einen Feature-Branch
3. Implementieren Sie Ihre Änderungen
4. Fügen Sie Tests hinzu
5. Aktualisieren Sie die Dokumentation
6. Führen Sie alle Tests aus
7. Committen und pushen Sie Ihre Änderungen
8. Erstellen Sie einen Pull Request

## 📈 Code-Review

Alle Pull Requests werden von einem Maintainer überprüft. Während des Reviews achten wir auf:

- Code-Qualität und -Stil
- Korrekte Fehlerbehandlung
- Effizienz und Performance
- Sicherheit
- Testabdeckung
- Dokumentation

## 🤖 Automatische Issue-Zusammenfassung

Unser Repository verwendet GitHub Actions, um neue Issues automatisch zusammenzufassen. Diese Funktion:

- Erstellt automatisch eine Zusammenfassung für neue Issues
- Verwendet OpenAI GPT für intelligente Zusammenfassungen (wenn konfiguriert)
- Fügt die Zusammenfassung als Kommentar zum Issue hinzu

Dies hilft Maintainern, schnell den Inhalt neuer Issues zu verstehen. Für weitere Informationen siehe [.github/workflows/ISSUE_SUMMARY.md](.github/workflows/ISSUE_SUMMARY.md).

## 📄 Lizenz

Durch das Einreichen eines Pull Requests erklären Sie sich damit einverstanden, dass Ihre Beiträge unter der MIT-Lizenz lizenziert sind.

## 🙏 Danksagung

Vielen Dank für Ihren Beitrag zum Telegram Audio Downloader! Ihre Arbeit hilft dabei, dieses Projekt für alle besser zu machen.