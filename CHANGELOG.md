# 📝 Changelog

Alle bemerkenswerten Änderungen an diesem Projekt werden in dieser Datei dokumentiert.

Das Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.0.0/),
und dieses Projekt hält sich an [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Sicherheit
- Behebung mehrerer Sicherheitsanfälligkeiten in kryptografischen Abhängigkeiten (cryptography)
- Behebung von HTTP-Sicherheitsanfälligkeiten in aiohttp (Request Smuggling, Directory Traversal, XSS)
- Behebung von Sicherheitsanfälligkeiten in tqdm CLI-Argumenten

### Hinzugefügt
- Professionelle PR-Cleanup- und Review-Automatisierung
- Automatisierte Sicherheitsbehebungsskripte
- Changelog-Update-Automatisierung
- Umfassende Wartungsskripte-Dokumentation
- Sicherheitsrichtliniendatei (SECURITY.md)

### Geändert
- Verbesserte Sicherheitsüberprüfungen in der CI/CD-Pipeline
- Aktualisierte Abhängigkeitsverwaltung
- Verfeinerte Docker-Sicherheitskonfiguration
- Aktualisierte Abhängigkeiten auf sichere Versionen:
  - cryptography >=44.0.1
  - aiohttp >=3.10.11
  - tqdm >=4.66.3

### Veraltet
- Veraltete `safety check` Kommandos durch neue `safety scan` Kommandos ersetzt

### Entfernt
- Veraltete Sicherheitsprüfungsdateien

### Behoben
- Korrekte Handhabung von API-Schlüsseln in der Konfiguration
- Dateiberechtigungsprobleme in der Entwicklungsumgebung
- Merge-Konflikterkennung in Pull Requests

### Sicherheit
- Implementierung automatischer Sicherheitsbehebungen
- Härtung der Docker-Konfiguration für nicht-root Ausführung
- Verbesserte Geheimnisverwaltung

## [1.1.0] - 2024-08-23

### Hinzugefügt
- Neue Skripte für Repository-Pflege und Versionsverwaltung
- Detaillierte Anleitung für Repository-Wartung
- Sichere Serialisierungsfunktionen zur Vermeidung von pickle-Sicherheitslücken
- Sichere Subprocess-Funktionen zur Vermeidung von Sicherheitslücken
- Konfigurationsdateien für GitHub Discussions
- Aktualisierte Testinfrastruktur mit manuellen Testskripten
- Umfassende Testdokumentation

[1.1.0]: https://github.com/Elpablo777/Telegram-Audio-Downloader/releases/tag/v1.1.0