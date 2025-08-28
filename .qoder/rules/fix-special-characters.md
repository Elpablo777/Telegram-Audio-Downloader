---
trigger: manual
---

# Absturz bei Dateinamen mit Sonderzeichen beheben

## Beschreibung
Behebe das Problem, dass das Skript manchmal abstürzt, wenn der Name einer Audiodatei auf Telegram Sonderzeichen oder Emojis enthält.

## Anforderungen
1. Analysiere den Code, der für die Benennung der heruntergeladenen Dateien zuständig ist
2. Passe den Code so an, dass alle ungültigen Zeichen (wie \ / : * ? " < > |) automatisch aus dem Dateinamen entfernt oder durch einen Unterstrich _ ersetzt werden
3. Stelle sicher, dass das Skript danach stabil läuft
4. Behandle Emojis und andere Unicode-Zeichen korrekt
5. Implementiere eine Funktion zur Bereinigung von Dateinamen

## Technische Details
- Verwende reguläre Ausdrücke zur Identifizierung ungültiger Zeichen
- Implementiere eine robuste Bereinigungsfunktion für Dateinamen
- Verwende asynchrone Programmierung, wo immer möglich
- Implementiere umfassende Fehlerbehandlung

## Dateien zum Ändern
- [src/telegram_audio_downloader/__init__.py](file:///c:/Users/Pablo/Desktop/Telegram%20Musik%20Tool/src/telegram_audio_downloader/__init__.py)
- [src/telegram_audio_downloader/file_operations.py](file:///c:/Users/Pablo/Desktop/Telegram%20Musik%20Tool/src/telegram_audio_downloader/file_operations.py) (falls vorhanden)

## Testfälle
- Teste Dateinamen mit verschiedenen Sonderzeichen
- Teste Dateinamen mit Emojis
- Teste Dateinamen mit nicht-ASCII-Zeichen
- Teste, dass die bereinigten Dateinamen gültig sind