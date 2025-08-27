# Sicherheitsrichtlinie

## Unterstützte Versionen

Wir veröffentlichen Sicherheitsupdates für die neueste Version des Telegram Audio Downloaders.

| Version | Unterstützt          |
| ------- | -------------------- |
| 1.1.x   | :white_check_mark:   |
| < 1.0   | :x:                  |

## Sicherheitslücke melden

Wenn Sie eine Sicherheitslücke in diesem Projekt entdecken, melden Sie diese bitte per E-Mail an hannover84@msn.com.

Bitte fügen Sie folgende Informationen in Ihren Bericht ein:
- Beschreibung der Sicherheitslücke
- Schritte zum Reproduzieren der Sicherheitslücke
- Mögliche Auswirkungen der Sicherheitslücke
- Eventuell identifizierte Gegenmaßnahmen

Wir bestätigen den Eingang Ihres Berichts innerhalb von 48 Stunden und bemühen uns, innerhalb von 7 Tagen einen Fix bereitzustellen.

## Automatisierte Sicherheitsmaßnahmen

### CodeQL Statische Analyse
- Tägliche statische Codeanalyse auf Sicherheitsprobleme
- Erweiterte Analyse für Python-spezifische Schwachstellen
- Automatische Berichterstattung an GitHub Security Advisories

### Abhängigkeitsmanagement
- **Dependabot** für automatische Sicherheitsupdates
- Tägliche Überprüfung auf Sicherheitslücken
- Automatische Erstellung von Pull-Requests für Sicherheitsupdates

### Überwachte Sicherheitspakete
- `cryptography`
- `aiohttp`
- `telethon`
- `python-dotenv`
- `pydub`
- `peewee`

## Offenlegungsrichtlinie für Sicherheitslücken

Wir befolgen eine koordinierte Offenlegungsrichtlinie:
1. Bestätigung und Validierung der Sicherheitslücke
2. Entwicklung und Test von Patches
3. Veröffentlichung einer neuen Version mit dem Fix
4. Öffentliche Bekanntgabe der Sicherheitslücke nach Verfügbarkeit des Fixes

## Sicherheitspraktiken

### Entwicklungsprozess
- Automatisierte Sicherheitstests in der CI/CD-Pipeline
- Regelmäßige Sicherheitsaudits
- Code-Review mit Fokus auf Sicherheitsaspekte

### Infrastruktur
- Minimale Berechtigungen für Workflows
- Sichere Geheimnisverwaltung mit GitHub Secrets
- Regelmäßige Sicherheitsupdates der Build-Umgebung

### Datenschutz
- Sichere Verarbeitung von Benutzerdaten
- Verschlüsselung sensibler Informationen
- Regelmäßige Überprüfung der Datenschutzmaßnahmen

## Sicherheitshinweise für Entwickler

### Empfohlene Entwicklungsumgebung
- Aktuelle Python-Version (mindestens 3.11)
- Verwendung von virtuellen Umgebungen
- Regelmäßige Aktualisierung der Entwicklungstools

### Sicherheitsrelevante Einstellungen
- Aktivierte Sicherheitsfeatures in der Konfiguration
- Regelmäßige Überprüfung der Sicherheitseinstellungen
- Dokumentation aller sicherheitsrelevanten Konfigurationen