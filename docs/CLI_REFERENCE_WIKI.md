# 💻 CLI Reference

Vollständige Referenz aller CLI-Befehle und Optionen des Telegram Audio Downloaders.

---

## 📋 **Befehlsübersicht**

```bash
telegram-audio-downloader [GLOBALE_OPTIONEN] BEFEHL [OPTIONEN] [ARGUMENTE]
```

### **Verfügbare Befehle**
- `download` - Audiodateien herunterladen
- `search` - Downloads durchsuchen und filtern  
- `performance` - System-Performance überwachen
- `metadata` - Metadaten analysieren und aktualisieren
- `stats` - Download-Statistiken anzeigen
- `groups` - Bekannte Gruppen verwalten

---

## 🌍 **Globale Optionen**

```bash
--debug              Aktiviert detaillierte Debug-Ausgaben
--help               Zeigt Hilfe an und beendet
--version            Zeigt Versionsinformation
```

### **Beispiele**
```bash
# Debug-Modus aktivieren
telegram-audio-downloader --debug download @gruppe

# Version anzeigen
telegram-audio-downloader --version
```

---

## 📥 **download - Audiodateien herunterladen**

```bash
telegram-audio-downloader download GRUPPE [OPTIONEN]
```

### **Argumente**
- `GRUPPE` (erforderlich) - Telegram-Gruppe (Name, @username oder ID)

### **Optionen**
```bash
--limit, -l INTEGER           Maximale Anzahl zu verarbeitender Nachrichten
--output, -o PATH            Ausgabeverzeichnis (Standard: downloads)
--parallel, -p INTEGER       Parallele Downloads (Standard: 3, Max: 10)
```

### **Beispiele**
```bash
# Einfacher Download
telegram-audio-downloader download @musikgruppe

# Mit Limit und parallelen Downloads
telegram-audio-downloader download @klassikgruppe --limit=100 --parallel=5

# In spezifisches Verzeichnis
telegram-audio-downloader download "Musik Gruppe" --output=./my_music

# Gruppe per ID
telegram-audio-downloader download -1001234567890 --limit=50
```

### **Tipps**
- Verwenden Sie `--parallel=1` bei langsamer Internetverbindung
- `--limit` ist nützlich zum Testen oder für neue Gruppen
- Setzen Sie Gruppennamen mit Leerzeichen in Anführungszeichen

---

## 🔍 **search - Downloads durchsuchen**

```bash
telegram-audio-downloader search [SUCHBEGRIFF] [OPTIONEN]
```

### **Argumente**
- `SUCHBEGRIFF` (optional) - Text zum Suchen in Titel, Künstler, Dateiname

### **Grundlegende Optionen**
```bash
--limit INTEGER              Anzahl anzuzeigender Ergebnisse (Standard: 10)
--all                        Alle Ergebnisse anzeigen (ignoriert --limit)
--metadata, -m               Erweiterte Metadaten in der Ausgabe
```

### **Filter-Optionen**
```bash
--group, -g TEXT             Nach Gruppe filtern
--status TEXT                Nach Download-Status filtern
                            (pending, downloading, completed, failed, skipped)
--format TEXT                Nach Audioformat filtern (mp3, flac, ogg, etc.)
--min-size TEXT              Minimale Dateigröße (z.B. "5MB", "100KB")
--max-size TEXT              Maximale Dateigröße (z.B. "50MB", "1GB")
--duration-min INTEGER       Minimale Dauer in Sekunden
--duration-max INTEGER       Maximale Dauer in Sekunden
```

### **Erweiterte Optionen**
```bash
--fuzzy, -f                  Fuzzy-Suche aktivieren (toleriert Schreibfehler)
```

### **Beispiele**

#### **Grundlegende Suche**
```bash
# Alle Downloads anzeigen
telegram-audio-downloader search

# Nach Künstler suchen
telegram-audio-downloader search "Beatles"

# Alle Ergebnisse mit Metadaten
telegram-audio-downloader search --all --metadata
```

#### **Filter-Beispiele**
```bash
# Nur FLAC-Dateien
telegram-audio-downloader search --format=flac

# Große Dateien finden
telegram-audio-downloader search --min-size=50MB

# Lange Tracks
telegram-audio-downloader search --duration-min=600  # > 10 Minuten

# Aus bestimmter Gruppe
telegram-audio-downloader search --group="Klassik"

# Fehlgeschlagene Downloads
telegram-audio-downloader search --status=failed
```

#### **Kombinierte Filter**
```bash
# FLAC-Dateien über 20MB aus Klassik-Gruppe
telegram-audio-downloader search \
  --format=flac \
  --min-size=20MB \
  --group="Klassik" \
  --metadata

# Fuzzy-Suche nach "Bethoven" (findet "Beethoven")
telegram-audio-downloader search "bethoven" --fuzzy
```

#### **Größen-Format**
```bash
# Unterstützte Größen-Einheiten
--min-size=500KB             # Kilobytes
--max-size=100MB             # Megabytes  
--min-size=1GB               # Gigabytes
--max-size=1024              # Bytes (ohne Einheit)
```

---

## 📊 **performance - System-Performance überwachen**

```bash
telegram-audio-downloader performance [OPTIONEN]
```

### **Optionen**
```bash
--watch, -w                  Echtzeit-Überwachung (Strg+C zum Beenden)
--cleanup, -c                System-Bereinigung durchführen
--output, -o PATH            Download-Verzeichnis für Analyse (Standard: downloads)
```

### **Beispiele**

#### **Einmalige Statistiken**
```bash
# Aktuelle Performance anzeigen
telegram-audio-downloader performance

# Mit anderem Download-Verzeichnis
telegram-audio-downloader performance --output=./music
```

#### **Echtzeit-Monitoring**
```bash
# Live-Dashboard starten
telegram-audio-downloader performance --watch

# Ausgabe (aktualisiert alle 5 Sekunden):
# 🔥 PERFORMANCE MONITOR
# Laufzeit: 3600s | 14:30:25
# 
# ┏━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┓
# ┃ Downloads     ┃           Wert ┃
# ┡━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━┩
# │ Erfolgreich   │            142 │
# │ Fehlgeschlagen│              3 │
# │ Erfolgsrate   │          97.9% │
# └───────────────┴────────────────┘
```

#### **System-Bereinigung**
```bash
# Garbage Collection und Temp-Files bereinigen
telegram-audio-downloader performance --cleanup

# Ausgabe:
# 🧹 Bereinige System...
# ✓ Garbage Collection: 1247 Objekte bereinigt
# ✓ Temp-Dateien bereinigt: 23 Dateien
```

---

## 🏷️ **metadata - Metadaten analysieren**

```bash
telegram-audio-downloader metadata [OPTIONEN]
```

### **Optionen**
```bash
--update, -u                 Metadaten aus bereits heruntergeladenen Dateien aktualisieren
--verify, -v                 Checksums verifizieren
--file-id TEXT               Nur bestimmte Datei analysieren (File-ID)
```

### **Beispiele**

#### **Metadaten aktualisieren**
```bash
# Alle Metadaten aktualisieren
telegram-audio-downloader metadata --update

# Mit Checksum-Verifikation
telegram-audio-downloader metadata --update --verify
```

#### **Einzelne Datei analysieren**
```bash
# Bestimmte Datei (File-ID aus Suche bekannt)
telegram-audio-downloader metadata --file-id=12345 --verify
```

#### **Nur Checksums prüfen**
```bash
# Alle Checksums verifizieren
telegram-audio-downloader metadata --verify
```

---

## 📈 **stats - Download-Statistiken**

```bash
telegram-audio-downloader stats
```

### **Keine Optionen** - Zeigt umfassende Statistiken

### **Beispiel-Ausgabe**
```bash
📊 Statistik

Gesamtanzahl Dateien: 2,847
Erfolgreich heruntergeladen: 2,791
Fehlgeschlagen: 56
Gesamtgröße: 47.3 GB

📂 Nach Gruppe
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┓
┃ Gruppe                                          ┃    Dateien ┃          Größe ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━┩
│ Klassische Musik                               │      1,234 │        18.7 GB │
│ Electronic Music                               │        892 │        15.2 GB │
│ Jazz Collection                                │        665 │        13.4 GB │
└─────────────────────────────────────────────────┴───────────┴─────────────────┘
```

---

## 👥 **groups - Gruppen-Verwaltung**

```bash
telegram-audio-downloader groups
```

### **Keine Optionen** - Zeigt alle bekannten Gruppen

### **Beispiel-Ausgabe**
```bash
┏━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┓
┃ ID           ┃ Titel                                                  ┃ Benutzername                                           ┃ Letzte Überprüfung                                    ┃ Dateien ┃
┡━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━┩
│ -1001234567  │ Klassische Musik                                      │ @klassikmusik                                          │ 23.08.2024 14:30                                      │    1234 │
│ -1009876543  │ Electronic Music                                       │ @electrobeats                                          │ 23.08.2024 12:15                                      │     892 │
│ -1005555444  │ Jazz Collection                                        │ -                                                      │ 22.08.2024 18:45                                      │     665 │
└──────────────┴────────────────────────────────────────────────────────┴────────────────────────────────────────────────────────┴────────────────────────────────────────────────────────┴─────────┘
```

---

## 🎛️ **Erweiterte Nutzung**

### **Pipe und Kombinationen**
```bash
# Ergebnisse in Datei speichern
telegram-audio-downloader search --all > my_music_list.txt

# Anzahl FLAC-Dateien zählen
telegram-audio-downloader search --format=flac --all | wc -l

# Nur erfolgreich heruntergeladene Dateien
telegram-audio-downloader search --status=completed --all
```

### **Konfiguration über Umgebungsvariablen**
```bash
# Temporäre Konfiguration
export DEFAULT_DOWNLOAD_DIR="/path/to/music"
export MAX_CONCURRENT_DOWNLOADS=5
telegram-audio-downloader download @gruppe

# Debug-Level setzen
export LOG_LEVEL=DEBUG
telegram-audio-downloader --debug download @gruppe
```

### **Scripting-Beispiele**

#### **Batch-Download mehrerer Gruppen**
```bash
#!/bin/bash
groups=("@gruppe1" "@gruppe2" "@gruppe3")
for group in "${groups[@]}"; do
    echo "Lade $group herunter..."
    telegram-audio-downloader download "$group" --limit=50
done
```

#### **Performance-Monitoring mit Logfile**
```bash
# Performance-Log erstellen
telegram-audio-downloader performance >> performance.log

# Stündlicher Performance-Check (Cron)
0 * * * * /path/to/telegram-audio-downloader performance >> /var/log/audio-downloader.log
```

---

## 🚨 **Fehlerbehandlung**

### **Exit-Codes**
- `0` - Erfolg
- `1` - Allgemeiner Fehler
- `2` - Konfigurationsfehler
- `3` - Netzwerkfehler
- `4` - Telegram-API-Fehler

### **Häufige Fehlermeldungen**

#### **"API_ID und API_HASH müssen gesetzt sein"**
```bash
# Lösung: .env-Datei konfigurieren
cp .env.example .env
# API_ID und API_HASH eintragen
```

#### **"FloodWaitError: Warte X Sekunden"**
```bash
# Automatisch behandelt - System wartet automatisch
# Reduzieren Sie --parallel bei häufigen FloodWait-Fehlern
telegram-audio-downloader download @gruppe --parallel=1
```

#### **"Gruppe nicht gefunden"**
```bash
# Prüfen Sie Gruppennamen/ID
telegram-audio-downloader groups  # Zeigt bekannte Gruppen

# Verschiedene Formate versuchen
telegram-audio-downloader download @gruppenname
telegram-audio-downloader download "Gruppen Name"
telegram-audio-downloader download -1001234567890
```

---

## 💡 **Tipps & Tricks**

### **Performance-Optimierung**
```bash
# Parallele Downloads anpassen je nach Internetgeschwindigkeit
telegram-audio-downloader download @gruppe --parallel=1   # Langsam
telegram-audio-downloader download @gruppe --parallel=3   # Standard
telegram-audio-downloader download @gruppe --parallel=5   # Schnell

# System-Ressourcen überwachen
telegram-audio-downloader performance --watch
```

### **Effizienter Workflow**
```bash
# 1. Neue Gruppe testen
telegram-audio-downloader download @neue_gruppe --limit=10

# 2. Performance prüfen
telegram-audio-downloader performance

# 3. Vollständiger Download
telegram-audio-downloader download @neue_gruppe --parallel=3

# 4. Ergebnisse durchsuchen
telegram-audio-downloader search --group="neue_gruppe" --metadata
```

### **Automation**
```bash
# Täglicher Cron-Job für Updates
0 2 * * * /path/to/telegram-audio-downloader download @hauptgruppe --limit=100

# Wöchentliche Performance-Bereinigung
0 3 * * 0 /path/to/telegram-audio-downloader performance --cleanup
```

---

## 📞 **Hilfe und Support**

Bei Fragen zu spezifischen CLI-Befehlen:

```bash
# Hilfe zu einem bestimmten Befehl
telegram-audio-downloader download --help
telegram-audio-downloader search --help
telegram-audio-downloader performance --help
```

Weitere Hilfe:
- **[Installation Guide](Installation-Guide)** - Setup und Konfiguration
- **[GitHub Issues](https://github.com/Elpablo777/Telegram-Audio-Downloader/issues)** - Bug-Reports
- **[Discussions](https://github.com/Elpablo777/Telegram-Audio-Downloader/discussions)** - Community-Hilfe

---

**Happy Downloading! 🎵**