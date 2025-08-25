---
trigger: always_on
alwaysApply: true
---

# Telegram Audio Downloader - Qoder Quest Konfiguration

## Projektbeschreibung
Der Telegram Audio Downloader ist ein leistungsstarker, asynchroner Python-Bot zum Herunterladen und Verwalten von Audiodateien aus Telegram-Gruppen mit Performance-Monitoring, Fuzzy-Suche und Docker-Support.

## Ziel der Quest
Diese Quest-Konfiguration soll die KI von Qoder dabei unterstützen, effektive Verbesserungen und Erweiterungen für den Telegram Audio Downloader zu entwickeln. Die KI soll in der Lage sein, neue Funktionen zu implementieren, bestehenden Code zu verbessern und bei der Fehlerbehebung zu helfen.

## Verfügbare Module und Komponenten
- Hauptanwendung: [telegram_audio_downloader.py](file:///c:/Users/Pablo/Desktop/Telegram%20Musik%20Tool/src/telegram_audio_downloader/__init__.py)
- Konfiguration: [config/](file:///c:/Users/Pablo/Desktop/Telegram%20Musik%20Tool/config) Verzeichnis
- Tests: [tests/](file:///c:/Users/Pablo/Desktop/Telegram%20Musik%20Tool/tests) Verzeichnis
- Dokumentation: [docs/](file:///c:/Users/Pablo/Desktop/Telegram%20Musik%20Tool/docs) Verzeichnis
- Skripte: [scripts/](file:///c:/Users/Pablo/Desktop/Telegram%20Musik%20Tool/scripts) Verzeichnis

## Wichtige Abhängigkeiten
- Python 3.11+
- Telethon
- aiofiles
- aiohttp
- pydub (für Audioverarbeitung)

## Projektstruktur
```
Telegram-Audio-Downloader/
├── src/
│   └── telegram_audio_downloader/
├── tests/
├── config/
├── docs/
├── scripts/
├── data/
└── docker/
```

## Entwicklungshinweise
1. Achte auf asynchrone Programmierung mit asyncio
2. Verwende Typ-Hints für alle Funktionen und Variablen
3. Implementiere umfassende Fehlerbehandlung
4. Schreibe Unit-Tests für neue Funktionen
5. Halte dich an die bestehenden Codierungsstandards

## Typische Quest-Aufgaben
1. Neue Download-Filter implementieren
2. Verbesserung der Metadaten-Extraktion
3. Erweiterung der Konfigurationsmöglichkeiten
4. Optimierung der Performance
5. Implementierung neuer Benachrichtigungssysteme
6. Verbesserung der Fehlerbehandlung
7. Erweiterung der Dokumentation
8. Docker-Image-Optimierung
