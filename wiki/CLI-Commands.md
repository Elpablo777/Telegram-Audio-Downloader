# 🛠️ CLI Commands Reference

Vollständige Referenz aller verfügbaren Kommandozeilen-Befehle des Telegram Audio Downloaders.

## 📋 **Inhaltsverzeichnis**

- [Grundlegende Befehle](#grundlegende-befehle)
- [Download-Befehle](#download-befehle)
- [Such- und Filter-Befehle](#such--und-filter-befehle)
- [Performance & Monitoring](#performance--monitoring)
- [Konfiguration & Management](#konfiguration--management)
- [Entwickler-Tools](#entwickler-tools)

---

## 🎯 **Grundlegende Befehle**

### **Hilfe & Information**
```bash
# Allgemeine Hilfe anzeigen
telegram-audio-downloader --help
telegram-audio-downloader -h

# Version anzeigen
telegram-audio-downloader --version
telegram-audio-downloader -v

# System-Check durchführen
telegram-audio-downloader --system-check

# Debug-Modus aktivieren
telegram-audio-downloader --debug [COMMAND]
telegram-audio-downloader -d [COMMAND]
```

### **Authentifizierung**
```bash
# Telegram-Authentifizierung starten
telegram-audio-downloader auth

# Authentifizierungsstatus prüfen
telegram-audio-downloader auth --status

# Session löschen (Neu-Authentifizierung erforderlich)
telegram-audio-downloader auth --reset
```

---

## 📥 **Download-Befehle**

### **Grundlegendes Download**
```bash
# Aus Gruppe/Kanal herunterladen
telegram-audio-downloader download GRUPPE [OPTIONS]
telegram-audio-downloader dl GRUPPE [OPTIONS]  # Kurz-Alias

# Beispiele
telegram-audio-downloader download @musikgruppe
telegram-audio-downloader download "Musik & Sounds"
telegram-audio-downloader download -1001234567890
```

### **Download-Optionen**
```bash
# Maximale Anzahl Dateien
--limit N, -l N
telegram-audio-downloader download @gruppe --limit=50

# Parallele Downloads
--parallel N, -p N
telegram-audio-downloader download @gruppe --parallel=5

# Output-Verzeichnis
--output DIR, -o DIR
telegram-audio-downloader download @gruppe --output=./downloads/musik

# Audio-Format filtern
--format FORMAT, -f FORMAT
telegram-audio-downloader download @gruppe --format=mp3
telegram-audio-downloader download @gruppe --format=mp3,flac,wav

# Dateigröße-Filter
--min-size SIZE
--max-size SIZE
telegram-audio-downloader download @gruppe --min-size=1MB --max-size=50MB

# Datum-Filter (ISO-Format)
--after DATE
--before DATE
telegram-audio-downloader download @gruppe --after=2024-01-01

# Nur neue Dateien (skip bereits heruntergeladene)
--skip-existing
telegram-audio-downloader download @gruppe --skip-existing

# Fortschritt überschreiben (bei unterbrochenen Downloads)
--resume
telegram-audio-downloader download @gruppe --resume
```

### **Erweiterte Download-Optionen**
```bash
# Metadaten-Extraktion aktivieren
--metadata, -m
telegram-audio-downloader download @gruppe --metadata

# Checksum-Verifikation
--verify-checksum
telegram-audio-downloader download @gruppe --verify-checksum

# Retry-Verhalten
--max-retries N
telegram-audio-downloader download @gruppe --max-retries=5

# Download-Timeout
--timeout SECONDS
telegram-audio-downloader download @gruppe --timeout=300

# Quiet-Modus (weniger Ausgaben)
--quiet, -q
telegram-audio-downloader download @gruppe --quiet

# Verbose-Modus (detaillierte Ausgaben)
--verbose, -v
telegram-audio-downloader download @gruppe --verbose
```

---

## 🔍 **Such- und Filter-Befehle**

### **Basis-Suche**
```bash
# In heruntergeladenen Dateien suchen
telegram-audio-downloader search [QUERY] [OPTIONS]
telegram-audio-downloader find [QUERY] [OPTIONS]  # Alias

# Beispiele
telegram-audio-downloader search "beethoven"
telegram-audio-downloader search "classical music"
```

### **Such-Optionen**
```bash
# Fuzzy-Suche (mit Schreibfehler-Toleranz)
--fuzzy, -f
telegram-audio-downloader search "bethovn" --fuzzy

# Nach Audio-Format filtern
--format FORMAT
telegram-audio-downloader search "symphony" --format=flac

# Nach Dateigröße filtern
--min-size SIZE
--max-size SIZE
telegram-audio-downloader search "piano" --min-size=5MB --max-size=100MB

# Nach Audiodauer filtern
--duration-min SECONDS
--duration-max SECONDS
telegram-audio-downloader search "song" --duration-min=180 --duration-max=300

# Nach Künstler suchen
--artist ARTIST
telegram-audio-downloader search --artist="John Williams"

# Nach Album suchen
--album ALBUM
telegram-audio-downloader search --album="Soundtrack"

# Reguläre Ausdrücke verwenden
--regex, -r
telegram-audio-downloader search "Mozart.*Symphony" --regex

# Erweiterte Metadaten anzeigen
--metadata, -m
telegram-audio-downloader search "concerto" --metadata

# Ergebnisse sortieren
--sort-by {name,size,date,duration}
--reverse
telegram-audio-downloader search "piano" --sort-by=size --reverse

# Maximale Anzahl Ergebnisse
--limit N
telegram-audio-downloader search "music" --limit=20
```

### **Gespeicherte Suchen**
```bash
# Suche speichern
telegram-audio-downloader search "classical" --save="classical_music"

# Gespeicherte Suche ausführen
telegram-audio-downloader search --load="classical_music"

# Alle gespeicherten Suchen anzeigen
telegram-audio-downloader search --list-saved
```

---

## 📊 **Performance & Monitoring**

### **Performance-Dashboard**
```bash
# Real-time Performance-Überwachung
telegram-audio-downloader performance [OPTIONS]
telegram-audio-downloader perf [OPTIONS]  # Alias

# Live-Überwachung starten
--watch, -w
telegram-audio-downloader performance --watch

# Memory-Usage überwachen
--memory, -m
telegram-audio-downloader performance --memory

# Disk-Usage anzeigen
--disk, -d
telegram-audio-downloader performance --disk

# Network-Statistics
--network, -n
telegram-audio-downloader performance --network

# Performance-Test durchführen
--test, -t
telegram-audio-downloader performance --test

# System bereinigen
--cleanup, -c
telegram-audio-downloader performance --cleanup
```

### **Performance-Berichte**
```bash
# Performance-Report generieren
--report, -r
telegram-audio-downloader performance --report

# Report in Datei speichern
--output FILE
telegram-audio-downloader performance --report --output=performance_report.json

# Historical Performance anzeigen
--history DAYS
telegram-audio-downloader performance --history=30
```

---

## ⚙️ **Konfiguration & Management**

### **Konfiguration**
```bash
# Aktuelle Konfiguration anzeigen
telegram-audio-downloader config [OPTIONS]

# Alle Einstellungen anzeigen
--show, -s
telegram-audio-downloader config --show

# Spezifische Einstellung anzeigen
--get KEY
telegram-audio-downloader config --get=max_concurrent_downloads

# Einstellung ändern
--set KEY=VALUE
telegram-audio-downloader config --set=max_concurrent_downloads=5

# Konfiguration zurücksetzen
--reset
telegram-audio-downloader config --reset

# Konfiguration validieren
--validate
telegram-audio-downloader config --validate

# Konfiguration exportieren
--export FILE
telegram-audio-downloader config --export=my_config.json

# Konfiguration importieren
--import FILE
telegram-audio-downloader config --import=my_config.json
```

### **Gruppen-Management**
```bash
# Alle verfügbaren Gruppen/Kanäle anzeigen
telegram-audio-downloader groups [OPTIONS]

# Mit Statistiken
--stats, -s
telegram-audio-downloader groups --stats

# Nur Gruppen (keine Kanäle)
--groups-only
telegram-audio-downloader groups --groups-only

# Nur Kanäle (keine Gruppen)
--channels-only
telegram-audio-downloader groups --channels-only

# Nach Größe sortieren
--sort-by {name,members,messages}
telegram-audio-downloader groups --sort-by=members

# Detaillierte Informationen
--details, -d
telegram-audio-downloader groups --details
```

### **Statistiken**
```bash
# Download-Statistiken anzeigen
telegram-audio-downloader stats [OPTIONS]

# Detaillierte Statistiken
--detailed, -d
telegram-audio-downloader stats --detailed

# Zeitraum-Filter
--period {today,week,month,year,all}
telegram-audio-downloader stats --period=month

# Nach Gruppe filtern
--group GROUP
telegram-audio-downloader stats --group=@musikgruppe

# Export als JSON
--export FILE
telegram-audio-downloader stats --export=stats.json

# Top-Downloads anzeigen
--top N
telegram-audio-downloader stats --top=10
```

---

## 🛠️ **Datenbank-Management**

### **Datenbank-Operationen**
```bash
# Datenbank-Status anzeigen
telegram-audio-downloader db [OPTIONS]

# Datenbank-Statistiken
--stats, -s
telegram-audio-downloader db --stats

# Datenbank bereinigen (entfernt verwaiste Einträge)
--cleanup, -c
telegram-audio-downloader db --cleanup

# Datenbank optimieren
--optimize, -o
telegram-audio-downloader db --optimize

# Datenbank-Backup erstellen
--backup FILE
telegram-audio-downloader db --backup=backup.db

# Datenbank wiederherstellen
--restore FILE
telegram-audio-downloader db --restore=backup.db

# Datenbank-Integrität prüfen
--check
telegram-audio-downloader db --check
```

### **Metadaten-Management**
```bash
# Metadaten extrahieren/aktualisieren
telegram-audio-downloader metadata [OPTIONS]

# Für alle Dateien
--all, -a
telegram-audio-downloader metadata --all

# Für spezifisches Verzeichnis
--directory DIR
telegram-audio-downloader metadata --directory=./downloads

# Nur fehlende Metadaten
--missing-only
telegram-audio-downloader metadata --missing-only

# Cover-Art extrahieren
--extract-covers
telegram-audio-downloader metadata --extract-covers

# Metadaten reparieren
--repair
telegram-audio-downloader metadata --repair
```

---

## 🔧 **Entwickler-Tools**

### **Debug & Testing**
```bash
# Debug-Informationen ausgeben
telegram-audio-downloader --debug [COMMAND]

# Trace-Modus (sehr detailliert)
--trace
telegram-audio-downloader --trace download @gruppe --limit=1

# Profiling aktivieren
--profile
telegram-audio-downloader --profile download @gruppe

# Memory-Profiling
--memory-profile
telegram-audio-downloader --memory-profile download @gruppe

# Log-Level setzen
--log-level {DEBUG,INFO,WARNING,ERROR}
telegram-audio-downloader --log-level=DEBUG [COMMAND]
```

### **API-Testing**
```bash
# API-Verbindung testen
telegram-audio-downloader test [OPTIONS]

# Authentifizierung testen
--auth
telegram-audio-downloader test --auth

# Gruppe/Kanal-Zugriff testen
--group GROUP
telegram-audio-downloader test --group=@musikgruppe

# Download-Test (ohne echten Download)
--download-test
telegram-audio-downloader test --download-test --group=@musikgruppe

# Performance-Test
--performance
telegram-audio-downloader test --performance
```

---

## 📝 **Batch-Operations**

### **Batch-Downloads**
```bash
# Aus Datei mit Gruppen-Liste
--batch-file FILE
telegram-audio-downloader download --batch-file=groups.txt

# groups.txt Format:
# @musikgruppe1
# @musikgruppe2
# "Gruppe mit Leerzeichen"

# Batch mit verschiedenen Einstellungen
telegram-audio-downloader download --batch-file=groups.txt --limit=10 --parallel=3
```

### **Scheduled Operations**
```bash
# Cron-Job Syntax generieren
--cron
telegram-audio-downloader download @gruppe --cron

# Daemon-Modus (kontinuierlich laufen)
--daemon
telegram-audio-downloader download @gruppe --daemon --interval=3600

# One-Shot (einmalig ausführen und beenden)
--once
telegram-audio-downloader download @gruppe --once
```

---

## 🎨 **Output-Formatierung**

### **Output-Optionen**
```bash
# JSON-Output
--json
telegram-audio-downloader stats --json

# CSV-Output
--csv
telegram-audio-downloader stats --csv

# Farben deaktivieren
--no-color
telegram-audio-downloader download @gruppe --no-color

# Minimaler Output
--minimal
telegram-audio-downloader download @gruppe --minimal

# Progress-Bar deaktivieren
--no-progress
telegram-audio-downloader download @gruppe --no-progress

# Timestamps in Logs
--timestamps
telegram-audio-downloader download @gruppe --timestamps
```

---

## 🔗 **Nützliche Kombinationen**

### **Power-User Kombinationen**
```bash
# Maximaler Performance-Download
telegram-audio-downloader download @gruppe \
  --parallel=10 \
  --format=flac \
  --min-size=10MB \
  --skip-existing \
  --metadata \
  --verify-checksum

# Intelligente Suche & Download
telegram-audio-downloader search "mozart" --fuzzy --save="mozart_search"
telegram-audio-downloader download @classical --limit=100 --format=flac

# Performance-Monitoring während Download
telegram-audio-downloader performance --watch &
telegram-audio-downloader download @gruppe --parallel=5

# Batch-Download mit Reporting
telegram-audio-downloader download --batch-file=groups.txt \
  --parallel=3 \
  --limit=50 \
  --json > download_report.json
```

---

## 💡 **Tipps & Tricks**

### **Effizienz-Tipps**
```bash
# Aliases für häufige Befehle definieren
alias tad="telegram-audio-downloader"
alias tad-dl="telegram-audio-downloader download"
alias tad-search="telegram-audio-downloader search --fuzzy"

# Konfiguration für wiederkehrende Downloads
echo "max_concurrent_downloads=5" >> ~/.telegram_audio_downloader.conf
echo "default_format=flac" >> ~/.telegram_audio_downloader.conf
```

### **Automatisierung**
```bash
# Täglicher Download-Cron (Linux/macOS)
0 2 * * * cd /path/to/project && ./venv/bin/telegram-audio-downloader download @daily_music --limit=20

# Windows Task Scheduler Batch-Datei
@echo off
cd /d "C:\path\to\project"
venv\Scripts\activate
telegram-audio-downloader download @music --limit=10
```

---

## 🆘 **Hilfe bei Problemen**

### **Debug-Befehle**
```bash
# Vollständiger Debug-Download
telegram-audio-downloader --debug --trace download @gruppe --limit=1

# Log-Analyse
tail -f data/telegram_audio_downloader.log | grep ERROR

# System-Diagnose
telegram-audio-downloader --system-check --verbose
```

### **Recovery-Befehle**
```bash
# Unterbrochene Downloads fortsetzen
telegram-audio-downloader download @gruppe --resume

# Korrupte Dateien neu herunterladen
telegram-audio-downloader download @gruppe --force-redownload

# Datenbank reparieren
telegram-audio-downloader db --check --repair
```

---

## 🔗 **Weiterführende Dokumentation**

- **[Configuration Guide](Configuration)** - Detaillierte Konfiguration
- **[Performance Tuning](Performance-Tuning)** - Optimierung für Speed
- **[Batch Operations](Batch-Operations)** - Automatisierte Workflows
- **[Troubleshooting](Troubleshooting)** - Problemlösungen
- **[API Reference](API-Integration)** - Programmatische Nutzung

---

**Happy CLI-ing!** 🛠️✨