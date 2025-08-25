---
title: "Häufig gestellte Fragen (FAQ) 🙋‍♀️"
labels: "documentation, Q&A"
---

# Häufig gestellte Fragen (FAQ)

Willkommen in unserem FAQ-Bereich! Hier finden Sie Antworten auf die häufigsten Fragen zur Verwendung des Telegram Audio Downloaders.

## 🚀 Erste Schritte

### Wie installiere ich den Telegram Audio Downloader?

Sie können den Telegram Audio Downloader auf verschiedene Arten installieren:

1. **Mit pip:**
   ```bash
   pip install telegram-audio-downloader
   ```

2. **Aus dem Quellcode:**
   ```bash
   git clone https://github.com/Elpablo777/Telegram-Audio-Downloader.git
   cd Telegram-Audio-Downloader
   pip install -r requirements.txt
   ```

3. **Mit Docker:**
   ```bash
   docker pull elpablo777/telegram-audio-downloader
   ```

### Welche Voraussetzungen muss mein System erfüllen?

- Python 3.11 oder höher
- Ein Telegram-Konto
- API-ID und API-Hash von Telegram (über https://my.telegram.org erhalten)

## ⚙️ Konfiguration

### Wie konfiguriere ich den Telegram Audio Downloader?

Die Konfiguration erfolgt über eine JSON-Datei. Standardmäßig sucht das Tool nach einer Datei namens `config.json` im Arbeitsverzeichnis. Sie können auch eine andere Konfigurationsdatei mit dem `-c` oder `--config` Parameter angeben.

Beispiel für eine grundlegende Konfiguration:
```json
{
  "api_id": 123456,
  "api_hash": "your_api_hash_here",
  "phone_number": "+1234567890",
  "download_path": "./downloads",
  "session_name": "telegram_audio_downloader"
}
```

### Wo finde ich meine API-ID und API-Hash?

1. Besuchen Sie https://my.telegram.org
2. Melden Sie sich mit Ihrer Telefonnummer an
3. Klicken Sie auf "API development tools"
4. Erstellen Sie eine neue Anwendung (oder verwenden Sie eine vorhandene)
5. Ihre API-ID und API-Hash werden angezeigt

## 📥 Download-Prozess

### Wie starte ich einen Download?

Nach der Konfiguration können Sie den Download mit folgendem Befehl starten:
```bash
python telegram_audio_downloader.py --chat "https://t.me/your_chat_link"
```

### Kann ich mehrere Chats gleichzeitig herunterladen?

Ja, Sie können mehrere Chats gleichzeitig herunterladen, indem Sie mehrere `--chat` Parameter angeben:
```bash
python telegram_audio_downloader.py --chat "https://t.me/chat1" --chat "https://t.me/chat2"
```

### Wie funktioniert die Fortschrittsanzeige?

Das Tool zeigt den Download-Fortschritt in Echtzeit an, einschließlich:
- Anzahl der verarbeiteten Nachrichten
- Anzahl der heruntergeladenen Dateien
- Geschätzte verbleibende Zeit
- Aktuelle Download-Geschwindigkeit

## 🔧 Problemlösung

### Ich erhalte einen "FloodWaitError". Was soll ich tun?

Dieser Fehler tritt auf, wenn Sie die Telegram-API zu häufig aufrufen. Das Tool implementiert bereits automatische Wartezeiten, aber Sie können auch:

1. Die Anzahl der gleichzeitigen Downloads reduzieren
2. Die Abrufhäufigkeit verringern
3. Das Tool für einige Stunden pausieren lassen

### Warum werden einige Audiodateien nicht heruntergeladen?

Mögliche Gründe:
1. Die Dateien sind durch Rechtebeschränkungen geschützt
2. Die Dateien sind größer als das von Telegram erlaubte Maximum
3. Netzwerkprobleme
4. Das Tool hat Schwierigkeiten, bestimmte Dateiformate zu erkennen

### Wie kann ich Logs aktivieren?

Sie können detaillierte Logs aktivieren, indem Sie die Log-Ebene in der Konfiguration ändern:
```json
{
  "log_level": "DEBUG"
}
```

## 🛡️ Sicherheit

### Ist es sicher, meine API-Zugangsdaten im Klartext zu speichern?

Für die Entwicklung ist dies akzeptabel, aber für Produktivumgebungen empfehlen wir:
1. Umgebungsvariablen zu verwenden
2. Ein sicheres Schlüsselverwaltungssystem zu implementieren
3. Die Zugriffsrechte der Konfigurationsdatei einzuschränken

### Wie schützt das Tool meine Daten?

Das Tool:
1. Speichert keine sensiblen Daten außerhalb des lokalen Systems
2. Verschlüsselt lokale Datenbanken
3. Implementiert Rate-Limiting zur Vermeidung von API-Missbrauch
4. Verwendet sichere Dateioperationen

## 🐳 Docker

### Wie verwende ich das Tool mit Docker?

1. Ziehen Sie das Image:
   ```bash
   docker pull elpablo777/telegram-audio-downloader
   ```

2. Führen Sie den Container aus:
   ```bash
   docker run -v /local/download/path:/downloads -v /local/config/path:/config elpablo777/telegram-audio-downloader
   ```

### Kann ich meine eigene Docker-Compose-Datei verwenden?

Ja, hier ist eine Beispiel-Docker-Compose-Datei:
```yaml
version: '3.8'
services:
  telegram-audio-downloader:
    image: elpablo777/telegram-audio-downloader
    volumes:
      - ./downloads:/downloads
      - ./config:/config
    environment:
      - TZ=Europe/Berlin
```

## 📚 Entwicklung

### Wie kann ich zur Entwicklung beitragen?

1. Forken Sie das Repository
2. Erstellen Sie einen Feature-Branch
3. Implementieren Sie Ihre Änderungen
4. Schreiben Sie Tests
5. Erstellen Sie einen Pull Request

### Wie führe ich die Tests aus?

```bash
pytest tests/
```

### Welche Codierungsstandards gelten?

- PEP 8 für Python-Code
- Typ-Hints für alle Funktionen
- Docstrings für alle öffentlichen Funktionen und Klassen
- Unit-Tests für neue Funktionen

## 🆘 Weitere Hilfe

Wenn Ihre Frage hier nicht beantwortet wurde, zögern Sie nicht, eine neue Discussion in der [Q&A-Kategorie](/discussions?discussions_q=category:Q&A) zu erstellen oder ein [Issue](https://github.com/Elpablo777/Telegram-Audio-Downloader/issues) zu öffnen.

Wir aktualisieren diesen FAQ-Bereich regelmäßig basierend auf den Fragen unserer Community!