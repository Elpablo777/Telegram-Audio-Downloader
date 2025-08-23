# 🛠️ Repository Maintenance Guidelines

## Übersicht

Dieses Dokument definiert die Richtlinien und Verfahren für die Pflege dieses GitHub-Repositorys, um sicherzustellen, dass es professionell, konsistent und wartbar bleibt.

## Versionsverwaltung

### Semantic Versioning

Das Projekt folgt [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html):

- **MAJOR** version bei inkompatiblen API-Änderungen
- **MINOR** version bei funktioneller Erweiterung rückwärtskompatibel
- **PATCH** version bei rückwärtskompatiblen Bugfixes

### Versionsformat

```
v{MAJOR}.{MINOR}.{PATCH}[-{PRERELEASE}][+{BUILD}]
```

Beispiele:
- v1.0.0
- v1.2.3
- v2.0.0-alpha.1

## Changelog-Pflege

### Format

Das Changelog folgt den [Keep a Changelog](https://keepachangelog.com/de/1.0.0/) Richtlinien:

```markdown
## [Unreleased]

### Hinzugefügt
### Geändert
### Veraltet
### Entfernt
### Behoben
### Sicherheit
```

### Aktualisierung

1. **Bei jeder Änderung**: Füge Einträge im `[Unreleased]` Abschnitt hinzu
2. **Bei Release**: Verschiebe Einträge von `[Unreleased]` zur neuen Version
3. **Links aktualisieren**: Füge Links zu Vergleichen zwischen Versionen hinzu

## Release-Prozess

### 1. Vorbereitung

1. Überprüfe alle offenen Issues und PRs
2. Stelle sicher, dass alle Tests bestanden werden
3. Aktualisiere die Versionsnummer in:
   - `src/telegram_audio_downloader/__init__.py`
   - `setup.py`
   - `pyproject.toml`
4. Aktualisiere das Changelog
5. Erstelle einen Release-Kandidaten-Branch

### 2. Testen

1. Führe alle Tests lokal aus
2. Teste die Installation aus dem Quellverzeichnis
3. Teste die Installation aus dem gebauten Paket
4. Überprüfe die Dokumentation

### 3. Release erstellen

1. Merge den Release-Kandidaten-Branch in `main`
2. Erstelle einen Git-Tag: `git tag -a v1.0.0 -m "Release v1.0.0"`
3. Push den Tag: `git push origin v1.0.0`
4. GitHub Actions erstellt automatisch das Release

### 4. Nach dem Release

1. Überprüfe das erstellte GitHub Release
2. Überprüfe die Paketveröffentlichung (PyPI)
3. Aktualisiere die Dokumentation wenn nötig
4. Melde das Release in relevanten Kanälen

## Branching-Strategie

### Hauptbranches

- **main**: Produktionsreife Version
- **develop**: Entwicklungsbranch für die nächste Version

### Feature-Branches

- Erstelle für jedes Feature/Issue einen separaten Branch
- Benenne nach dem Schema: `feature/issue-{nummer}-{kurzbeschreibung}`
- Beispiel: `feature/issue-123-add-fuzzy-search`

### Release-Branches

- Erstelle für jeden Release-Kandidaten einen Branch
- Benenne nach dem Schema: `release/v{version}`
- Beispiel: `release/v1.2.0`

## Commit-Richtlinien

### Format

Verwende den [Conventional Commits](https://www.conventionalcommits.org/de/v1.0.0/) Standard:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Typen

- **feat**: Neue Funktion
- **fix**: Fehlerbehebung
- **docs**: Dokumentationsänderungen
- **style**: Formatierung, fehlende Semikolons, etc.
- **refactor**: Code-Änderungen ohne neue Funktionen oder Fehlerbehebungen
- **perf**: Leistungsverbesserungen
- **test**: Hinzufügen oder Ändern von Tests
- **build**: Änderungen am Build-System oder externen Abhängigkeiten
- **ci**: Änderungen an CI-Konfigurationsdateien und Skripten
- **chore**: Andere Änderungen, die keine der obigen Kategorien betreffen

### Beispiele

```
feat: add fuzzy search functionality
fix: resolve memory leak in downloader
docs: update installation instructions
refactor: improve error handling in cli module
```

## Code-Qualität

### Stil

- Folge dem [PEP 8](https://pep8.org/) Style Guide
- Verwende Type Hints wo immer möglich
- Halte Funktionen kurz und fokussiert
- Verwende aussagekräftige Namen

### Tests

- Schreibe Unit-Tests für neue Funktionen
- Strebe eine Testabdeckung von >90% an
- Verwende pytest für Tests
- Führe Tests regelmäßig aus

### Überprüfung

- Verwende linters (flake8, pylint)
- Verwende Formatierer (black, isort)
- Führe Sicherheitsprüfungen durch (bandit, safety)
- Überprüfe Typen (mypy)

## Dokumentation

### README

Halte die README aktuell mit:

- Projektbeschreibung
- Installationsanweisungen
- Schnellstart-Guide
- CLI-Befehle
- Beispiele
- Links zu weiteren Ressourcen

### Wiki

- Halte die Wiki-Seiten aktuell
- Dokumentiere neue Funktionen
- Erstelle Tutorials für komplexe Funktionen
- Pflege die FAQ

### Code-Dokumentation

- Verwende docstrings für alle öffentlichen Funktionen und Klassen
- Verwende Google-Style docstrings
- Dokumentiere komplexe Algorithmen
- Halte die API-Referenz aktuell

## CI/CD

### Workflows

- **CI**: Läuft bei jedem Push und PR
- **Release**: Läuft bei Tags
- **Code Quality**: Läuft täglich
- **Monitoring**: Läuft täglich

### Überwachung

- Überwache Build-Status
- Überwache Testabdeckung
- Überwache Sicherheitswarnungen
- Überwache Abhängigkeitsaktualisierungen

## Abhängigkeiten

### Aktualisierung

- Verwende Dependabot für automatische PRs
- Überprüfe regelmäßig Sicherheitswarnungen
- Teste sorgfältig vor dem Aktualisieren von Hauptversionen
- Halte requirements.txt aktuell

### Pinning

- Pin alle Abhängigkeiten in requirements.txt
- Verwende Versionsbereiche für nicht-kritische Abhängigkeiten
- Pin kritische Abhängigkeiten auf exakte Versionen

## Sicherheit

### Best Practices

- Halte alle Abhängigkeiten aktuell
- Verwende Sicherheitsprüfungen in CI
- Überprüfe regelmäßig auf bekannte Sicherheitslücken
- Verwende sichere Codierungspraktiken

### Melden

- Melde Sicherheitsprobleme verantwortungsvoll
- Folge dem SECURITY.md Prozess
- Arbeite schnell an Patches für kritische Probleme

## Community

### Issues

- Beantworte Issues zeitnah
- Verwende Templates für Bug-Reports und Feature-Requests
- Markiere Issues mit passenden Labels
- Schließe gelöste Issues

### Pull Requests

- Überprüfe PRs innerhalb von 48 Stunden
- Verwende Checklisten für Reviews
- Fordere Änderungen wenn nötig
- Danke Beitragenden

### Kommunikation

- Sei freundlich und respektvoll
- Halte Diskussionen sachlich
- Fördere eine einladende Gemeinschaft
- Halte die Code of Conduct ein

## Automatisierung

### Tools

- Verwende GitHub Actions für CI/CD
- Automatisiere Changelog-Generierung
- Automatisiere Release-Erstellung
- Automatisiere Abhängigkeitsaktualisierungen

### Skripte

- Halte Entwickler-Skripte aktuell
- Dokumentiere alle Skripte
- Verwende Makefiles oder Nox für komplexe Aufgaben
- Automatisiere wiederholende Aufgaben

## Überwachung

### Metriken

- Überwache Build-Zeiten
- Überwache Testabdeckung
- Überwache Code-Qualität
- Überwache Community-Aktivität

### Berichte

- Erstelle regelmäßige Statusberichte
- Melde wichtige Metriken
- Analysiere Trends
- Identifiziere Verbesserungsmöglichkeiten