#!/bin/bash

# GitHub Repository Enhancement Script
# Dieses Script konfiguriert alle wichtigen Repository-Einstellungen

echo "🚀 Konfiguriere GitHub Repository..."

# Repository Beschreibung und Homepage setzen
gh repo edit Elpablo777/Telegram-Audio-Downloader \
  --description "🎵 Ein leistungsstarker, asynchroner Python-Bot zum Herunterladen und Verwalten von Audiodateien aus Telegram-Gruppen mit Performance-Monitoring, Fuzzy-Suche und Docker-Support" \
  --homepage "https://elpablo777.github.io/Telegram-Audio-Downloader"

# Topics hinzufügen für bessere Auffindbarkeit
gh repo edit Elpablo777/Telegram-Audio-Downloader \
  --add-topic telegram-bot \
  --add-topic python \
  --add-topic audio-downloader \
  --add-topic cli \
  --add-topic asyncio \
  --add-topic telegram-api \
  --add-topic music \
  --add-topic downloader \
  --add-topic performance-monitoring \
  --add-topic rich-cli \
  --add-topic docker \
  --add-topic open-source

# Wiki aktivieren
gh repo edit Elpablo777/Telegram-Audio-Downloader --enable-wiki

# Discussions aktivieren  
gh repo edit Elpablo777/Telegram-Audio-Downloader --enable-discussions

# Issues sind bereits aktiviert, aber sicherheitshalber:
gh repo edit Elpablo777/Telegram-Audio-Downloader --enable-issues

# Projects aktivieren
gh repo edit Elpablo777/Telegram-Audio-Downloader --enable-projects

echo "✅ Repository-Konfiguration abgeschlossen!"

# GitHub Pages aktivieren
echo "📄 Aktiviere GitHub Pages..."
gh api repos/Elpablo777/Telegram-Audio-Downloader/pages \
  --method POST \
  --field source='{"branch":"main","path":"/docs"}' \
  --field build_type="legacy" || echo "GitHub Pages bereits konfiguriert oder Fehler aufgetreten"

echo "🎯 Alle GitHub-Features wurden aktiviert!"