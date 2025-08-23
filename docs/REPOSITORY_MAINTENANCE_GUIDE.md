# 📖 Repository Maintenance Guide

## Übersicht

Diese Anleitung beschreibt die Schritte zur Pflege und Wartung des Telegram Audio Downloader Repositorys, einschließlich Changelog-Management, Versionsführung und Synchronisation.

## 1. Changelog-Management

### 1.1 Neue Änderungen hinzufügen

Fügen Sie neue Änderungen zum `[Unreleased]` Abschnitt der [CHANGELOG.md](file://c:\Users\Pablo\Desktop\Telegram%20Musik%20Tool\CHANGELOG.md) hinzu:

```bash
# Wechseln Sie ins Projektverzeichnis
cd c:\Users\Pablo\Desktop\Telegram Musik Tool

# Fügen Sie eine neue Änderung hinzu
python scripts/update_changelog.py add "Behoben" "Fehler bei der Dateinamenbereinigung behoben"
python scripts/update_changelog.py add "Hinzugefügt" "Neue Suchfunktion für Audio-Dateien"
```

Verfügbare Änderungstypen:
- Hinzugefügt
- Geändert
- Veraltet
- Entfernt
- Behoben
- Sicherheit

### 1.2 Changelog für ein Release aktualisieren

Wenn Sie ein neues Release erstellen, aktualisieren Sie das Changelog:

```bash
# Aktualisieren Sie das Changelog für Version 1.1.0
python scripts/update_changelog.py release 1.1.0
```

## 2. Versionsverwaltung

### 2.1 Aktuelle Version anzeigen

```bash
# Zeigen Sie die aktuelle Version an
python scripts/version_manager.py get
```

### 2.2 Version aktualisieren

```bash
# Setzen Sie eine neue Version (Semantic Versioning)
python scripts/version_manager.py set 1.1.0

# Validieren Sie ein Versionsformat
python scripts/version_manager.py validate 1.1.0-beta.1
```

### 2.3 Versionsinformationen anzeigen

```bash
# Zeigen Sie Versionsinformationen aus allen Dateien an
python scripts/version_manager.py info
```

## 3. Repository-Synchronisation

### 3.1 Mit Remote-Repository synchronisieren

```bash
# Synchronisieren Sie das lokale Repository mit dem Remote-Repository
python scripts/maintain_repository.py sync
```

### 3.2 Release erstellen

```bash
# Erstellen Sie ein neues Release
python scripts/maintain_repository.py release 1.1.0 "Neue Suchfunktion und Performance-Verbesserungen"
```

## 4. Wartungsbericht generieren

### 4.1 Vollständigen Wartungsbericht erstellen

```bash
# Generieren Sie einen Wartungsbericht
python scripts/maintain_repository.py report
```

Der Bericht enthält:
- Git-Status (geänderte/ungetrackte Dateien)
- Aktuellen Branch
- Letzten Tag
- Versionskonsistenz
- Teststatus
- Code-Qualitätschecks

## 5. Automatisierte Workflows

### 5.1 GitHub Actions

Die folgenden GitHub Actions sind konfiguriert:

1. **CI Workflow** (`.github/workflows/ci.yml`):
   - Läuft bei jedem Push und PR
   - Führt Tests und Code-Qualitätschecks aus

2. **Release Workflow** (`.github/workflows/release.yml`):
   - Läuft bei neuen Tags
   - Erstellt GitHub Releases
   - Baut und veröffentlicht Artefakte

### 5.2 Dependabot

Dependabot ist konfiguriert in `.github/dependabot.yml`:
- Überprüft Abhängigkeiten wöchentlich
- Erstellt automatisch PRs für Updates

## 6. Best Practices

### 6.1 Commits

Verwenden Sie Conventional Commits:
```
feat: Neue Suchfunktion hinzugefügt
fix: Fehler bei der Dateinamenbereinigung behoben
docs: README aktualisiert
refactor: Code-Struktur verbessert
```

### 6.2 Branching-Strategie

- `main`: Produktionsreife Version
- `develop`: Entwicklungsbranch
- Feature-Branches: `feature/issue-{nummer}-{beschreibung}`
- Hotfix-Branches: `hotfix/{version}-{beschreibung}`

### 6.3 Pull Requests

- Erstellen Sie für jede Änderung einen PR
- Weisen Sie Reviewer zu
- Führen Sie alle Checks durch
- Merge nur nach erfolgreicher CI

## 7. Notfallverfahren

### 7.1 Repository-Kompromittierung

1. Sofortigen Zugriff sperren
2. Kontaktaufnahme mit GitHub-Support
3. Wiederherstellen aus Backups
4. Untersuchen der Ursache

### 7.2 Verlust von Maintainer-Zugriff

1. Kontaktaufnahme mit anderen Maintainern
2. Anfrage bei GitHub für Zugriffswiederherstellung
3. Dokumentation des Vorfalls

## 8. Häufige Aufgaben

### 8.1 Abhängigkeiten aktualisieren

```bash
# Überprüfen Sie veraltete Abhängigkeiten
pip list --outdated

# Aktualisieren Sie requirements.txt
pip freeze > requirements.txt
```

### 8.2 Sicherheitsüberprüfungen

```bash
# Führen Sie Sicherheitsüberprüfungen durch
python -m safety check
python -m bandit -r src/
```

### 8.3 Code-Qualität prüfen

```bash
# Führen Sie Linting durch
flake8 src/

# Formatieren Sie den Code
black src/

# Sortieren Sie Importe
isort src/

# Typüberprüfung
mypy src/
```

## 9. Dokumentation pflegen

### 9.1 README aktualisieren

- Halten Sie Badges aktuell
- Aktualisieren Sie Installationsanweisungen
- Fügen Sie neue Funktionen hinzu

### 9.2 Wiki pflegen

- Erstellen Sie neue Seiten für neue Funktionen
- Aktualisieren Sie bestehende Seiten
- Überprüfen Sie die Navigation

## 10. Community-Management

### 10.1 Issues

- Antworten Sie innerhalb von 24 Stunden
- Verwenden Sie Templates
- Labeln Sie korrekt
- Schließen Sie gelöste Issues

### 10.2 Pull Requests

- Überprüfen Sie innerhalb von 48 Stunden
- Geben Sie konstruktives Feedback
- Helfen Sie bei notwendigen Änderungen
- Danken Sie Beitragenden

---

*Diese Anleitung wird regelmäßig aktualisiert. Bei Fragen wenden Sie sich an die Projekt-Maintainer.*