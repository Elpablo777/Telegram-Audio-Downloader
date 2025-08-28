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

## Sicherheitswerkzeuge

### Abhängigkeitsüberprüfungen
- **pip-audit**: Überprüfung auf bekannte Sicherheitslücken in Abhängigkeiten
- **safety**: Überprüfung auf Sicherheitslücken basierend auf PyUp.io-Datenbank

### Suche nach sensiblen Daten
- **gitleaks**: Sucht nach versehentlich committeten sensiblen Daten

### Statische Code-Analyse
- **bandit**: Sucht nach bekannten Sicherheitsproblemen im Python-Code

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

### Umgang mit Secrets
- Alle sensiblen Daten werden als Umgebungsvariablen gespeichert
- Keine hartcodierten Secrets im Code
- Verwendung von `.env`-Dateien für die lokale Entwicklung (ausgeschlossen von Git)
- Restriktive Dateiberechtigungen für sensible Dateien

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

### Ausführen von Sicherheitsprüfungen
```bash
# Schnelle Sicherheitsprüfung
make security

# Umfassende Sicherheitsprüfung
make security-comprehensive

# Simuliere CI/CD Pipeline lokal
make ci-local
```

Detaillierte Informationen zu den Sicherheitswerkzeugen finden Sie in [docs/security-tools.md](docs/security-tools.md).