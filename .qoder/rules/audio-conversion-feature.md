---
trigger: manual
---

# Audio-Dateien nach dem Download in MP3 konvertieren

## Beschreibung
Implementiere eine neue Funktion im Telegram Audio Downloader, die Audiodateien nach dem Download automatisch in das MP3-Format konvertiert, falls sie nicht bereits in diesem Format vorliegen.

## Anforderungen
1. Nach dem erfolgreichen Download einer Audiodatei überprüfen, ob sie bereits im MP3-Format ist
2. Wenn die Datei nicht im MP3-Format ist (z.B. .ogg oder .m4a), konvertiere sie automatisch in eine MP3-Datei
3. Verwende die pydub-Bibliothek für die Konvertierung
4. Füge pydub zu den requirements.txt hinzu, falls es noch nicht im Projekt verwendet wird
5. Lösche die Originaldatei nach der erfolgreichen Konvertierung
6. Implementiere eine Konfigurationsoption, um die Konvertierung ein-/ausschalten zu können

## Technische Details
- Verwende asynchrone Programmierung, wo immer möglich
- Implementiere umfassende Fehlerbehandlung für den Konvertierungsprozess
- Füge Unit-Tests für die neue Funktionalität hinzu
- Dokumentiere die neue Funktion in der README.md

## Dateien zum Ändern
- [src/telegram_audio_downloader/__init__.py](file:///c:/Users/Pablo/Desktop/Telegram%20Musik%20Tool/src/telegram_audio_downloader/__init__.py)
- [requirements.txt](file:///c:/Users/Pablo/Desktop/Telegram%20Musik%20Tool/requirements.txt)
- [config/default_config.json](file:///c:/Users/Pablo/Desktop/Telegram%20Musik%20Tool/config/default_config.json) (falls vorhanden)
- [README.md](file:///c:/Users/Pablo/Desktop/Telegram%20Musik%20Tool/README.md)

## Testfälle
- Teste die Konvertierung von verschiedenen Audioformaten (.ogg, .m4a) in MP3
- Teste das Verhalten, wenn eine Datei bereits im MP3-Format vorliegt
- Teste die Fehlerbehandlung bei ungültigen Dateien
- Teste die Konfigurationsoption zum Ein-/Ausschalten der Konvertierung