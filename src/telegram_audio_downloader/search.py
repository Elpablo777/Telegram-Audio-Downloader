"""
Suchfunktionen für den Telegram Audio Downloader.
"""

import logging
from typing import List, Optional
from datetime import datetime

from telethon import TelegramClient
from telethon.tl.types import Document, DocumentAttributeAudio, Message, MessageMediaDocument

from .models import AudioFile, TelegramGroup
from .error_handling import handle_error, SearchError
from .logging_config import get_logger
from .utils.file_operations import sanitize_filename

logger = get_logger(__name__)


async def search_audio_files(
    client: TelegramClient, 
    group_entity, 
    query: Optional[str] = None,
    limit: Optional[int] = None
) -> List[dict]:
    """
    Sucht nach Audiodateien in einer Telegram-Gruppe.
    
    Args:
        client: TelegramClient-Instanz
        group_entity: Telegram-Gruppe
        query: Optionale Suchanfrage (Titel, Künstler, etc.)
        limit: Maximale Anzahl an Ergebnissen
        
    Returns:
        Liste von Audiodatei-Informationen
    """
    try:
        audio_files = []
        count = 0
        
        async for message in client.iter_messages(group_entity, limit=limit):
            if not hasattr(message, "media") or not isinstance(
                message.media, MessageMediaDocument
            ):
                continue

            document = message.media.document
            if not document or not _is_audio_file(document):
                continue

            # Extrahiere Audio-Informationen
            audio_info = _extract_audio_info(document, message)
            
            # Filtere nach Suchanfrage, falls vorhanden
            if query and not _matches_query(audio_info, query):
                continue
                
            audio_files.append(audio_info)
            count += 1
            
            if limit and count >= limit:
                break

        logger.info(f"{count} Audiodateien gefunden")
        return audio_files
        
    except Exception as e:
        error = SearchError(f"Fehler bei der Suche nach Audiodateien: {e}")
        handle_error(error, "search_audio_files")
        raise error


def _is_audio_file(document: Document) -> bool:
    """Überprüft, ob es sich bei dem Dokument um eine Audiodatei handelt."""
    try:
        # Überprüfe die Dateiendung
        if document.mime_type:
            if any(audio_type in document.mime_type for audio_type in ["audio", "mpeg"]):
                return True

        # Überprüfe die Attribute
        for attr in document.attributes:
            if isinstance(attr, DocumentAttributeAudio):
                return True

        return False
    except Exception as e:
        logger.warning(f"Fehler bei der Audio-Datei-Erkennung: {e}")
        return False


def _extract_audio_info(document: Document, message: Message) -> dict:
    """Extrahiert Metadaten aus einem Audio-Dokument."""
    try:
        audio_attrs = next(
            (
                attr
                for attr in document.attributes
                if isinstance(attr, DocumentAttributeAudio)
            ),
            None,
        )

        # Bestimme die Dateiendung
        file_ext = ".mp3"  # Standardendung
        if document.mime_type:
            mime_to_ext = {
                "audio/mpeg": ".mp3",
                "audio/mp3": ".mp3",
                "audio/mp4": ".m4a",
                "audio/x-m4a": ".m4a",
                "audio/flac": ".flac",
                "audio/ogg": ".ogg",
                "audio/wav": ".wav",
                "audio/x-wav": ".wav",
            }
            file_ext = mime_to_ext.get(document.mime_type, file_ext)

        # Extrahiere Metadaten
        title = getattr(audio_attrs, "title", None)
        performer = getattr(audio_attrs, "performer", None)

        # Generiere Dateinamen
        filename = _generate_filename(title, performer, str(document.id), file_ext)

        return {
            "file_id": str(document.id),
            "message_id": message.id,
            "file_name": filename,
            "file_size": document.size,
            "mime_type": document.mime_type or "audio/mpeg",
            "duration": getattr(audio_attrs, "duration", None) if audio_attrs else None,
            "title": title,
            "performer": performer,
            "date": message.date,
        }
    except Exception as e:
        logger.error(f"Fehler beim Extrahieren von Audio-Informationen: {e}")
        # Fallback-Informationen
        return {
            "file_id": str(document.id),
            "message_id": message.id,
            "file_name": f"audio_{document.id}.mp3",
            "file_size": document.size,
            "mime_type": document.mime_type or "audio/mpeg",
            "duration": None,
            "title": None,
            "performer": None,
            "date": message.date,
        }


def _generate_filename(
    title: Optional[str], 
    performer: Optional[str], 
    file_id: str, 
    extension: str
) -> str:
    """Generiert einen Dateinamen aus Metadaten."""
    try:
        parts = []

        if performer:
            parts.append(sanitize_filename(performer))

        if title:
            parts.append(sanitize_filename(title))

        if parts:
            filename = " - ".join(parts)
        else:
            filename = f"audio_{file_id}"

        return sanitize_filename(f"{filename}{extension}")
    except Exception as e:
        logger.warning(f"Fehler bei der Dateinamengenerierung: {e}")
        return f"audio_{file_id}{extension}"


def _matches_query(audio_info: dict, query: str) -> bool:
    """Überprüft, ob die Audio-Informationen zur Suchanfrage passen."""
    query = query.lower()
    
    # Prüfe Titel
    if audio_info.get("title") and query in audio_info["title"].lower():
        return True
        
    # Prüfe Künstler
    if audio_info.get("performer") and query in audio_info["performer"].lower():
        return True
        
    # Prüfe Dateiname
    if query in audio_info.get("file_name", "").lower():
        return True
        
    return False


# Zusätzliche Suchfunktionen

def search_downloaded_files(query: Optional[str] = None) -> List[AudioFile]:
    """
    Sucht in bereits heruntergeladenen Dateien.
    
    Args:
        query: Optionale Suchanfrage
        
    Returns:
        Liste von AudioFile-Objekten
    """
    try:
        if query:
            # Suche in mehreren Feldern
            results = AudioFile.select().where(
                (AudioFile.title.contains(query)) |
                (AudioFile.performer.contains(query)) |
                (AudioFile.file_name.contains(query))
            )
        else:
            # Gib alle heruntergeladenen Dateien zurück
            results = AudioFile.select().where(
                AudioFile.status == "completed"
            )
            
        return list(results)
    except Exception as e:
        error = SearchError(f"Fehler bei der Suche in heruntergeladenen Dateien: {e}")
        handle_error(error, "search_downloaded_files")
        return []


def search_groups(query: Optional[str] = None) -> List[TelegramGroup]:
    """
    Sucht in Telegram-Gruppen.
    
    Args:
        query: Optionale Suchanfrage
        
    Returns:
        Liste von TelegramGroup-Objekten
    """
    try:
        if query:
            # Suche in mehreren Feldern
            results = TelegramGroup.select().where(
                (TelegramGroup.title.contains(query)) |
                (TelegramGroup.username.contains(query))
            )
        else:
            # Gib alle Gruppen zurück
            results = TelegramGroup.select()
            
        return list(results)
    except Exception as e:
        error = SearchError(f"Fehler bei der Suche in Gruppen: {e}")
        handle_error(error, "search_groups")
        return []