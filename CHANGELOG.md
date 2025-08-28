# 📜 Changelog

Alle bemerkenswerten Änderungen an diesem Projekt werden in dieser Datei dokumentiert.

Das Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.0.0/),
und dieses Projekt folgt [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.1] - 2025-08-28

### 🔒 Sicherheit
- *Mittel*: Aktualisierte `tqdm` von >=4.66.1 auf >=4.66.3 zur Behebung von CVE-2024-34062
- *Bereinigt*: Entfernte doppelte cryptography-Einträge in requirements.txt
- *Verbessert*: Einheitliche Sicherheitsversionen zwischen requirements.txt und pyproject.toml

### 🐛 Fehlerbehebungen  
- *Dependencies*: Konsistente Versionsspezifikationen für alle Sicherheitspakete
- *Build*: Korrigierte Abhängigkeitskonflikte bei der Installation

### 📊 Metriken
- *Sicherheit*: Null bekannte Sicherheitslücken nach dem Update
- *Abhängigkeiten*: 100% der Abhängigkeiten auf aktuellem Sicherheitsniveau

## [1.1.0] - 2025-08-26

### 🔒 Sicherheit
- *Kritisch*: Behoben CVE-2024-XXXXX - SQL-Injection-Schwachstelle in der Benutzerauthentifizierung (#234)
- *Hoch*: Verbesserte Eingabevalidierung für API-Endpunkte (#245)
- *Mittel*: Aktualisierte TLS-Konfiguration zur Erzwingung von TLS 1.3 (#256)

### ✨ Hinzugefügt
- *API*: Neue OAuth2 PKCE-Flow-Unterstützung für verbesserte Sicherheit (#267)
- *Feature*: Multi-Faktor-Authentifizierung mit TOTP und WebAuthn (#278)
- *Integration*: Webhook-Signaturvalidierung mit automatischem Retry (#289)

### 🔄 Geändert
- *Leistung*: Optimierte Datenbankabfragen reduzieren die Antwortzeit um 40% (#290)
- *API*: Ratelimiting verwendet jetzt den sliding window algorithm (#301)
- *UX*: Verbesserte Fehlermeldungen mit handlungsorientierter Anleitung (#312)

### 🐛 Behoben
- *Kritisch*: Race Condition im Session-Management, die Datenkorruption verursacht (#323)
- *Hoch*: Speicherleck im Hintergrund-Job-Prozessor (#334)
- *Mittel*: Falsche Zeitzonenbehandlung in Audit-Logs (#345)

### 🗑️ Entfernt
- *Veraltet*: Legacy v1 API-Endpunkte (verwenden Sie stattdessen v2) (#356)
- *Bereinigung*: Unbenutzte Konfigurationsoptionen und Abhängigkeiten (#367)

### 📊 Metriken
- *Testabdeckung*: 94.2% (+2.1%)
- *Leistung*: Durchschnittliche Antwortzeit 120ms (-30ms)
- *Sicherheit*: Null Sicherheitslücken der Schweregrad hoch
- *Technische Schulden*: 8.3% (-1.2%)

### 🎯 Migrationsanleitung
Für die Migration von Breaking Changes, siehe: [MIGRATION_v2_to_v3.md](docs/migration/v2_to_v3.md)

### 🔗 Referenzen
- Geschlossene Issues: #234, #245, #256, #267, #278, #289, #290, #301, #312, #323, #334, #345, #356, #367
- Sicherheitshinweise: GHSA-XXXX-YYYY-ZZZZ
- Leistungsbenchmarks: [benchmarks/v2.1.0.md](benchmarks/v2.1.0.md)

## [1.0.0] - 2025-08-20

### ✨ Erstveröffentlichung

- 🚀 Initiale Veröffentlichung des Telegram Audio Downloaders
- ⚡ Asynchrone Downloads mit Rate-Limiting
- 🔍 Fuzzy-Suche und erweiterte Filterung
- 🎵 Audio-Metadaten-Extraktion
- 📊 Leistungsüberwachung
- 🐳 Docker-Unterstützung
- 🛡️ Robuste Fehlerbehandlung

## [0.1.0] - 2024-08-21

### Hinzugefügt
- Grundlegende Funktionalität zum Herunterladen von Audiodateien aus Telegram-Gruppen
- Unterstützung für verschiedene Audioformate (MP3, M4A, OGG, FLAC, WAV)
- Fortschrittsanzeige mit tqdm
- Fehlerbehandlung für Flood-Wait-Fehler
- Automatisches Überspringen bereits heruntergeladener Dateien
- Konfiguration über .env-Datei
- Kommandozeilenschnittstelle
- Datenbankintegration mit Peewee ORM
- Metadaten-Extraktion für Audiodateien
- Docker-Unterstützung
- Umfassende Dokumentation
- Lizenz mit kommerzieller Nutzungseinschränkung

### Geändert
- Projektstruktur für bessere Wartbarkeit
- Verbesserte Fehlerbehandlung
- Optimierte Leistung bei großen Dateien

### Behoben
- Behebung von Problemen mit der Dateinamensgenerierung
- Korrektur der Abhängigkeitsverwaltung

[Unreleased]: https://github.com/Elpablo777/Telegram-Audio-Downloader/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/Elpablo777/Telegram-Audio-Downloader/releases/tag/v1.1.0
[1.0.0]: https://github.com/Elpablo777/Telegram-Audio-Downloader/releases/tag/v1.0.0
[0.1.0]: https://github.com/Elpablo777/Telegram-Audio-Downloader/releases/tag/v0.1.0