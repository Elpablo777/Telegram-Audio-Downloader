"""
Erweiterte Metadaten-Extraktion für den Telegram Audio Downloader.
"""

import asyncio
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from urllib.parse import quote

import aiohttp
import mutagen
from mutagen.id3 import ID3NoHeaderError
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from mutagen.oggvorbis import OggVorbis
from mutagen.mp4 import MP4

from .error_handling import handle_error
from .file_error_handler import handle_file_error, with_file_error_handling
from .utils import sanitize_filename

logger = logging.getLogger(__name__)

# Unterstützte externe APIs
EXTERNAL_APIS = {
    "musicbrainz": "https://musicbrainz.org/ws/2/recording",
    "lastfm": "http://ws.audioscrobbler.com/2.0/",
    "spotify": "https://api.spotify.com/v1/search",
}

# API-Schlüssel (sollten aus der Konfiguration geladen werden)
API_KEYS = {
    "lastfm": "YOUR_LASTFM_API_KEY",  # Platzhalter, sollte aus Konfiguration kommen
    "spotify": "YOUR_SPOTIFY_CLIENT_ID:YOUR_SPOTIFY_CLIENT_SECRET",  # Platzhalter
}

class AdvancedMetadataExtractor:
    """Erweiterte Metadaten-Extraktion mit Unterstützung für verschiedene Quellen."""
    
    def __init__(self, download_dir: Path):
        """
        Initialisiert den erweiterten Metadaten-Extraktor.
        
        Args:
            download_dir: Verzeichnis für Downloads
        """
        self.download_dir = download_dir
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        """Async-Kontextmanager-Eintritt."""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async-Kontextmanager-Austritt."""
        if self.session:
            await self.session.close()
            
    @with_file_error_handling()
    def extract_local_metadata(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Extrahiert erweiterte Metadaten aus einer lokalen Audiodatei.
        
        Args:
            file_path: Pfad zur Audiodatei
            
        Returns:
            Dictionary mit allen verfügbaren Metadaten
        """
        file_path = Path(file_path)
        metadata: Dict[str, Any] = {
            "title": None,
            "artist": None,
            "album": None,
            "date": None,
            "genre": None,
            "composer": None,
            "performer": None,
            "duration": None,
            "bitrate": None,
            "sample_rate": None,
            "channels": None,
            "format": None,
            "has_cover": False,
            "track_number": None,
            "total_tracks": None,
            "disc_number": None,
            "total_discs": None,
            "copyright": None,
            "isrc": None,
            "upc": None,
            "lyrics": None,
            "comments": None,
            "rating": None,
            "bpm": None,
            "key": None,
            "mood": None,
            "style": None,
        }
        
        try:
            # Verwende mutagen für die Metadaten-Extraktion
            audio_file = mutagen.File(file_path)
            if audio_file is None:
                logger.warning(f"Konnte Metadaten nicht aus {file_path} extrahieren")
                return metadata
                
            # Grundlegende Informationen
            info = audio_file.info
            metadata["duration"] = getattr(info, "length", None)
            metadata["bitrate"] = getattr(info, "bitrate", None)
            metadata["sample_rate"] = getattr(info, "sample_rate", None)
            metadata["channels"] = getattr(info, "channels", None)
            metadata["format"] = file_path.suffix.lower()[1:]  # ohne Punkt
            
            # Tags extrahieren (verschiedene Formate haben verschiedene Tag-Namen)
            tags = audio_file.tags if audio_file.tags else {}
            
            # Titel
            for key in ["TIT2", "TITLE", "\\xa9nam", "©nam"]:
                if key in tags:
                    metadata["title"] = (
                        str(tags[key][0]) if isinstance(tags[key], list) else str(tags[key])
                    )
                    break
                    
            # Künstler
            for key in ["TPE1", "ARTIST", "\\xa9ART", "©ART"]:
                if key in tags:
                    metadata["artist"] = (
                        str(tags[key][0]) if isinstance(tags[key], list) else str(tags[key])
                    )
                    break
                    
            # Album
            for key in ["TALB", "ALBUM", "\\xa9alb", "©alb"]:
                if key in tags:
                    metadata["album"] = (
                        str(tags[key][0]) if isinstance(tags[key], list) else str(tags[key])
                    )
                    break
                    
            # Jahr/Datum
            for key in ["TDRC", "TDRL", "DATE", "\\xa9day", "©day"]:
                if key in tags:
                    metadata["date"] = (
                        str(tags[key][0]) if isinstance(tags[key], list) else str(tags[key])
                    )
                    break
                    
            # Genre
            for key in ["TCON", "GENRE", "\\xa9gen", "©gen"]:
                if key in tags:
                    metadata["genre"] = (
                        str(tags[key][0]) if isinstance(tags[key], list) else str(tags[key])
                    )
                    break
                    
            # Komponist
            for key in ["TCOM", "COMPOSER", "\\xa9wrt", "©wrt"]:
                if key in tags:
                    metadata["composer"] = (
                        str(tags[key][0]) if isinstance(tags[key], list) else str(tags[key])
                    )
                    break
                    
            # Interpret (bei Compilations)
            for key in ["TPE2", "ALBUMARTIST", "aART"]:
                if key in tags:
                    metadata["performer"] = (
                        str(tags[key][0]) if isinstance(tags[key], list) else str(tags[key])
                    )
                    break
                    
            # Track-Nummer
            for key in ["TRCK", "TRACKNUMBER"]:
                if key in tags:
                    track_info = str(tags[key][0]) if isinstance(tags[key], list) else str(tags[key])
                    if "/" in track_info:
                        parts = track_info.split("/")
                        metadata["track_number"] = parts[0]
                        metadata["total_tracks"] = parts[1] if len(parts) > 1 else None
                    else:
                        metadata["track_number"] = track_info
                    break
                    
            # Disc-Nummer
            for key in ["TPOS", "DISCNUMBER"]:
                if key in tags:
                    disc_info = str(tags[key][0]) if isinstance(tags[key], list) else str(tags[key])
                    if "/" in disc_info:
                        parts = disc_info.split("/")
                        metadata["disc_number"] = parts[0]
                        metadata["total_discs"] = parts[1] if len(parts) > 1 else None
                    else:
                        metadata["disc_number"] = disc_info
                    break
                    
            # Copyright
            for key in ["TCOP", "COPYRIGHT", "\\xa9cpy", "©cpy"]:
                if key in tags:
                    metadata["copyright"] = (
                        str(tags[key][0]) if isinstance(tags[key], list) else str(tags[key])
                    )
                    break
                    
            # ISRC
            for key in ["TSRC", "ISRC"]:
                if key in tags:
                    metadata["isrc"] = (
                        str(tags[key][0]) if isinstance(tags[key], list) else str(tags[key])
                    )
                    break
                    
            # Lyrics
            for key in ["USLT", "LYRICS", "\\xa9lyr", "©lyr"]:
                if key in tags:
                    metadata["lyrics"] = (
                        str(tags[key][0]) if isinstance(tags[key], list) else str(tags[key])
                    )
                    break
                    
            # Kommentare
            for key in ["COMM", "COMMENT", "\\xa9cmt", "©cmt"]:
                if key in tags:
                    comment_data = tags[key][0] if isinstance(tags[key], list) else tags[key]
                    # Bei ID3-Tags kann der Kommentar ein Objekt mit Beschreibung sein
                    if hasattr(comment_data, "text"):
                        metadata["comments"] = str(comment_data.text)
                    else:
                        metadata["comments"] = str(comment_data)
                    break
                    
            # Bewertung
            for key in ["POPM", "RATING"]:
                if key in tags:
                    rating_data = tags[key][0] if isinstance(tags[key], list) else tags[key]
                    # Bei ID3-Tags kann die Bewertung ein Objekt mit Rating sein
                    if hasattr(rating_data, "rating"):
                        metadata["rating"] = rating_data.rating
                    else:
                        metadata["rating"] = str(rating_data)
                    break
                    
            # BPM
            for key in ["TBPM", "BPM"]:
                if key in tags:
                    metadata["bpm"] = (
                        str(tags[key][0]) if isinstance(tags[key], list) else str(tags[key])
                    )
                    break
                    
            # Cover-Art prüfen
            for key in ["APIC:", "covr", "COVR", "covr"]:
                if key in tags:
                    metadata["has_cover"] = True
                    break
                    
        except ID3NoHeaderError:
            logger.debug(f"Keine ID3-Tags gefunden in {file_path}")
        except Exception as e:
            logger.error(f"Fehler beim Extrahieren der Metadaten aus {file_path}: {e}")
            
        return metadata
        
    async def extract_telegram_metadata(self, message: Any) -> Dict[str, Any]:
        """
        Extrahiert Metadaten aus einer Telegram-Nachricht.
        
        Args:
            message: Telegram-Nachricht mit Audiodatei
            
        Returns:
            Dictionary mit Telegram-Metadaten
        """
        metadata: Dict[str, Any] = {
            "telegram_caption": None,
            "telegram_date": None,
            "telegram_sender": None,
            "telegram_message_id": None,
            "telegram_group_id": None,
            "telegram_file_name": None,
            "telegram_file_size": None,
            "telegram_mime_type": None,
        }
        
        try:
            # Nachrichteninformationen
            if hasattr(message, 'message') and message.message:
                metadata["telegram_caption"] = message.message
                
            if hasattr(message, 'date') and message.date:
                metadata["telegram_date"] = message.date.isoformat() if hasattr(message.date, 'isoformat') else str(message.date)
                
            if hasattr(message, 'sender') and message.sender:
                sender = message.sender
                if hasattr(sender, 'first_name') or hasattr(sender, 'last_name'):
                    name_parts = []
                    if hasattr(sender, 'first_name') and sender.first_name:
                        name_parts.append(sender.first_name)
                    if hasattr(sender, 'last_name') and sender.last_name:
                        name_parts.append(sender.last_name)
                    metadata["telegram_sender"] = " ".join(name_parts)
                elif hasattr(sender, 'title') and sender.title:
                    metadata["telegram_sender"] = sender.title
                    
            if hasattr(message, 'id'):
                metadata["telegram_message_id"] = message.id
                
            # Gruppeninformationen
            if hasattr(message, 'chat') and message.chat:
                chat = message.chat
                if hasattr(chat, 'id'):
                    metadata["telegram_group_id"] = chat.id
                    
            # Dateiinformationen
            if hasattr(message, 'media') and hasattr(message.media, 'document'):
                document = message.media.document
                if hasattr(document, 'attributes'):
                    for attr in document.attributes:
                        if hasattr(attr, 'file_name'):
                            metadata["telegram_file_name"] = attr.file_name
                        if hasattr(attr, 'title') and attr.title:
                            # Verwende den Titel aus den Attributen, falls vorhanden
                            if not metadata["title"]:
                                metadata["title"] = attr.title
                        if hasattr(attr, 'performer') and attr.performer:
                            # Verwende den Performer aus den Attributen, falls vorhanden
                            if not metadata["artist"]:
                                metadata["artist"] = attr.performer
                                
                if hasattr(document, 'size'):
                    metadata["telegram_file_size"] = document.size
                    
                if hasattr(document, 'mime_type'):
                    metadata["telegram_mime_type"] = document.mime_type
                    
        except Exception as e:
            logger.error(f"Fehler beim Extrahieren der Telegram-Metadaten: {e}")
            
        return metadata
        
    async def query_musicbrainz(self, title: str, artist: str = None) -> Optional[Dict[str, Any]]:
        """
        Fragt MusicBrainz-API für erweiterte Metadaten ab.
        
        Args:
            title: Titel des Tracks
            artist: Künstler (optional)
            
        Returns:
            Dictionary mit MusicBrainz-Metadaten oder None
        """
        if not self.session:
            logger.warning("Keine HTTP-Session verfügbar für MusicBrainz-Abfrage")
            return None
            
        try:
            # Erstelle die Suchanfrage
            query_parts = [f'title:"{title}"']
            if artist:
                query_parts.append(f'artist:"{artist}"')
                
            query = " AND ".join(query_parts)
            params = {
                "query": query,
                "fmt": "json",
                "limit": 1,
            }
            
            # Führe die Anfrage aus
            async with self.session.get(
                EXTERNAL_APIS["musicbrainz"], 
                params=params,
                headers={"User-Agent": "TelegramAudioDownloader/1.0.0 ( https://github.com/yourusername/telegram-audio-downloader )"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("recordings"):
                        recording = data["recordings"][0]
                        return {
                            "mbid": recording.get("id"),
                            "title": recording.get("title"),
                            "artist_credit": [ac.get("name") for ac in recording.get("artist-credit", [])],
                            "release_count": recording.get("release-count"),
                            "first_release_date": recording.get("first-release-date"),
                        }
        except Exception as e:
            logger.error(f"Fehler bei MusicBrainz-Abfrage für {title}: {e}")
            
        return None
        
    async def query_lastfm(self, title: str, artist: str) -> Optional[Dict[str, Any]]:
        """
        Fragt Last.fm-API für erweiterte Metadaten ab.
        
        Args:
            title: Titel des Tracks
            artist: Künstler
            
        Returns:
            Dictionary mit Last.fm-Metadaten oder None
        """
        if not self.session:
            logger.warning("Keine HTTP-Session verfügbar für Last.fm-Abfrage")
            return None
            
        api_key = API_KEYS.get("lastfm")
        if not api_key or api_key == "YOUR_LASTFM_API_KEY":
            logger.debug("Kein Last.fm API-Key konfiguriert")
            return None
            
        try:
            params = {
                "method": "track.getInfo",
                "api_key": api_key,
                "artist": artist,
                "track": title,
                "format": "json",
            }
            
            # Führe die Anfrage aus
            async with self.session.get(
                EXTERNAL_APIS["lastfm"], 
                params=params
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if "track" in data:
                        track = data["track"]
                        return {
                            "name": track.get("name"),
                            "artist": track.get("artist", {}).get("name"),
                            "album": track.get("album", {}).get("title"),
                            "listeners": track.get("listeners"),
                            "playcount": track.get("playcount"),
                            "duration": track.get("duration"),
                            "toptags": [tag.get("name") for tag in track.get("toptags", {}).get("tag", [])],
                            "wiki": track.get("wiki", {}).get("summary") if track.get("wiki") else None,
                        }
        except Exception as e:
            logger.error(f"Fehler bei Last.fm-Abfrage für {title} von {artist}: {e}")
            
        return None
        
    async def enrich_metadata(self, local_metadata: Dict[str, Any], telegram_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Bereichert lokale Metadaten mit externen APIs.
        
        Args:
            local_metadata: Lokale Metadaten aus der Audiodatei
            telegram_metadata: Metadaten aus der Telegram-Nachricht
            
        Returns:
            Erweitertes Metadaten-Dictionary
        """
        # Kombiniere alle Metadaten
        enriched_metadata = {**telegram_metadata, **local_metadata}
        
        # Extrahiere Titel und Künstler für API-Abfragen
        title = enriched_metadata.get("title") or enriched_metadata.get("telegram_caption")
        artist = enriched_metadata.get("artist") or enriched_metadata.get("performer")
        
        # Wenn wir Titel und Künstler haben, fragen wir externe APIs ab
        if title:
            # MusicBrainz-Abfrage
            if artist:
                mb_data = await self.query_musicbrainz(title, artist)
                if mb_data:
                    enriched_metadata.update({
                        "musicbrainz_mbid": mb_data.get("mbid"),
                        "musicbrainz_artist_credit": mb_data.get("artist_credit"),
                        "musicbrainz_release_count": mb_data.get("release_count"),
                        "musicbrainz_first_release_date": mb_data.get("first_release_date"),
                    })
                    
            # Last.fm-Abfrage
            if artist:
                lastfm_data = await self.query_lastfm(title, artist)
                if lastfm_data:
                    enriched_metadata.update({
                        "lastfm_name": lastfm_data.get("name"),
                        "lastfm_artist": lastfm_data.get("artist"),
                        "lastfm_album": lastfm_data.get("album"),
                        "lastfm_listeners": lastfm_data.get("listeners"),
                        "lastfm_playcount": lastfm_data.get("playcount"),
                        "lastfm_duration": lastfm_data.get("duration"),
                        "lastfm_tags": lastfm_data.get("toptags"),
                        "lastfm_wiki": lastfm_data.get("wiki"),
                    })
                    
        return enriched_metadata
        
    def save_metadata_to_file(self, metadata: Dict[str, Any], file_path: Path) -> None:
        """
        Speichert Metadaten in einer separaten JSON-Datei.
        
        Args:
            metadata: Metadaten-Dictionary
            file_path: Pfad zur zugehörigen Audiodatei
        """
        try:
            # Erstelle den Metadaten-Dateinamen
            metadata_file = file_path.with_suffix(".metadata.json")
            
            # Speichere die Metadaten
            with open(metadata_file, "w", encoding="utf-8") as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2, default=str)
                
            logger.debug(f"Metadaten gespeichert in {metadata_file}")
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Metadaten in {metadata_file}: {e}")

# Hilfsfunktionen für die Verwendung außerhalb der Klasse
@with_file_error_handling()
def extract_basic_metadata(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Extrahiert grundlegende Metadaten aus einer Audiodatei.
    
    Args:
        file_path: Pfad zur Audiodatei
        
    Returns:
        Dictionary mit grundlegenden Metadaten
    """
    file_path = Path(file_path)
    metadata: Dict[str, Any] = {
        "title": None,
        "artist": None,
        "album": None,
        "date": None,
        "genre": None,
        "duration": None,
        "bitrate": None,
        "format": None,
        "has_cover": False,
    }
    
    try:
        audio_file = mutagen.File(file_path)
        if audio_file is None:
            logger.warning(f"Konnte Metadaten nicht aus {file_path} extrahieren")
            return metadata
            
        # Grundlegende Informationen
        info = audio_file.info
        metadata["duration"] = getattr(info, "length", None)
        metadata["bitrate"] = getattr(info, "bitrate", None)
        metadata["format"] = file_path.suffix.lower()[1:]  # ohne Punkt
        
        # Tags extrahieren (verschiedene Formate haben verschiedene Tag-Namen)
        tags = audio_file.tags if audio_file.tags else {}
        
        # Titel
        for key in ["TIT2", "TITLE", "\\xa9nam", "©nam"]:
            if key in tags:
                metadata["title"] = (
                    str(tags[key][0]) if isinstance(tags[key], list) else str(tags[key])
                )
                break
                
        # Künstler
        for key in ["TPE1", "ARTIST", "\\xa9ART", "©ART"]:
            if key in tags:
                metadata["artist"] = (
                    str(tags[key][0]) if isinstance(tags[key], list) else str(tags[key])
                )
                break
                
        # Album
        for key in ["TALB", "ALBUM", "\\xa9alb", "©alb"]:
            if key in tags:
                metadata["album"] = (
                    str(tags[key][0]) if isinstance(tags[key], list) else str(tags[key])
                )
                break
                
        # Jahr/Datum
        for key in ["TDRC", "TDRL", "DATE", "\\xa9day", "©day"]:
            if key in tags:
                metadata["date"] = (
                    str(tags[key][0]) if isinstance(tags[key], list) else str(tags[key])
                )
                break
                
        # Genre
        for key in ["TCON", "GENRE", "\\xa9gen", "©gen"]:
            if key in tags:
                metadata["genre"] = (
                    str(tags[key][0]) if isinstance(tags[key], list) else str(tags[key])
                )
                break
                
        # Cover-Art prüfen
        for key in ["APIC:", "covr", "COVR", "covr"]:
            if key in tags:
                metadata["has_cover"] = True
                break
                
    except ID3NoHeaderError:
        logger.debug(f"Keine ID3-Tags gefunden in {file_path}")
    except Exception as e:
        logger.error(f"Fehler beim Extrahieren der Metadaten aus {file_path}: {e}")
        
    return metadata