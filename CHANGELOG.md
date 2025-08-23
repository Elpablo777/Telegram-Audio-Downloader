# 📝 Changelog

Alle bemerkenswerten Änderungen an diesem Projekt werden in dieser Datei dokumentiert.

Das Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.0.0/),
und dieses Projekt hält sich an [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-08-23

### 🎉 Production Release - Vollständig überarbeitetes System

#### ✨ Hinzugefügt
- **Performance-Optimierungen**
  - Parallele Downloads mit konfigurierbarer Anzahl (Standard: 3)
  - Intelligente Rate-Limiting mit Token-Bucket-Algorithmus
  - Memory-Management mit automatischer Garbage Collection
  - Performance-Dashboard mit Echtzeit-Überwachung (`performance --watch`)
  - Disk-Space-Monitoring und automatische Temp-File-Bereinigung
  
- **Erweiterte Audio-Features**
  - Fortsetzbare Downloads bei Unterbrechungen
  - Checksum-Verifikation (MD5) für Datenintegrität
  - Erweiterte Metadaten-Extraktion mit Mutagen
  - Automatische ID3-Tag-Aktualisierung
  - Multi-Format-Support erweitert (OPUS hinzugefügt)
  
- **Such- und Filter-System**
  - Fuzzy-Suche mit Schreibfehler-Toleranz
  - Filter nach Dateigröße (min-size, max-size)
  - Filter nach Audiodauer (duration-min, duration-max)
  - Filter nach Audio-Format
  - Volltext-Suche in Titel, Künstler, Dateinamen
  
- **Neue CLI-Befehle**
  - `performance` - System-Monitoring und Performance-Statistiken
  - `metadata` - Metadaten-Analyse und -Aktualisierung
  - `stats` - Umfassende Download-Statistiken
  - `groups` - Verwaltung bekannter Telegram-Gruppen
  
- **Robustes Error-Handling**
  - FloodWait-Error-Handling mit adaptiver Rate-Anpassung
  - Exponential Backoff bei Netzwerk-Fehlern
  - Detailliertes Error-Tracking und Kategorisierung
  - Retry-Mechanismus für temporäre Fehler
  
- **Professional Logging**
  - Rich-Handler für schöne Console-Ausgaben
  - Strukturiertes Logging mit Kategorien
  - Error-Tracking mit Kontext-Informationen
  - Debug-Modus für detaillierte Diagnose
  
- **Testing & Quality Assurance**
  - Umfassende Unit-Test-Suite (30+ Tests)
  - Test-Coverage für alle wichtigen Komponenten
  - Type-Hints für bessere Code-Qualität
  - Automatisierte Testing-Pipeline

#### 🔄 Geändert
- **CLI-Interface komplett überarbeitet**
  - Rich-basierte Ausgaben mit Farben und Tabellen
  - Erweiterte Such-Optionen mit vielen Filtern
  - Performance-Monitoring integriert
  - Verbesserte Hilfe-Texte und Beispiele
  
- **Datenbank-Schema erweitert**
  - Neue Felder für fortsetzbare Downloads
  - Checksum-Speicherung und Verifizierung
  - Download-Attempt-Tracking
  - Erweiterte Metadaten-Felder
  
- **Architektur-Verbesserungen**
  - Modulare Komponentenstruktur
  - Separation of Concerns
  - Performance-Monitor als zentrale Komponente
  - Verbesserte Konfigurationsverwaltung

#### 🐛 Behoben
- Kritische Syntax-Fehler in cli.py behoben
- Fehlende Import-Statements ergänzt
- Memory-Leaks bei großen Downloads behoben
- Race-Conditions bei parallelen Downloads eliminiert
- Dateinamen-Kollisionen durch bessere Bereinigung verhindert
- pydub Kompatibilitätsprobleme mit Python 3.13 gelöst

#### 🔒 Security
- Verbesserte Input-Validation
- Sichere Dateinamen-Bereinigung
- Rate-Limiting zum Schutz vor API-Missbrauch

## [0.1.0] - 2025-08-21

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
