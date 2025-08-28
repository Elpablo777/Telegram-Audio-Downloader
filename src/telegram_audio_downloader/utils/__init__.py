"""
Hilfsfunktionen für den Telegram Audio Downloader.
"""

import hashlib
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

import mutagen
from mutagen.id3 import ID3NoHeaderError

# Korrigiere den Import von error_handling
from ..error_handling import FileOperationError, handle_error
from ..file_error_handler import handle_file_error, with_file_error_handling

try:
    from pydub import AudioSegment

    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    AudioSegment = None

logger = logging.getLogger(__name__)

# Unterstützte Audio-Formate
AUDIO_EXTENSIONS = {".mp3", ".m4a", ".ogg", ".flac", ".wav", ".opus", ".aac", ".wma"}

# Ungültige Zeichen für Dateinamen
INVALID_FILENAME_CHARS = r'[<>:"/\\|?*]'

# Erweiterte Regex-Muster für problematische Unicode-Zeichen
EMOJI_PATTERN = r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002600-\U000027BF\U0001F900-\U0001F9FF\U0001F018-\U0001F270\U0001F000-\U0001F02F]'
CONTROL_CHARS_PATTERN = r'[\x00-\x1F\x7F-\x9F]'  # Control characters
ZERO_WIDTH_PATTERN = r'[\u200B\u200C\u200D\u2060\uFEFF]'  # Zero-width characters
BIDI_CONTROL_PATTERN = r'[\u202A-\u202E\u2066-\u2069]'  # Bidirectional text controls
RESERVED_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    "COM1",
    "COM2",
    "COM3",
    "COM4",
    "COM5",
    "COM6",
    "COM7",
    "COM8",
    "COM9",
    "LPT1",
    "LPT2",
    "LPT3",
    "LPT4",
    "LPT5",
    "LPT6",
    "LPT7",
    "LPT8",
    "LPT9",
}


@with_file_error_handling()
def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """
    Bereinigt einen Dateinamen von ungültigen Zeichen, Emojis und problematischen Unicode-Zeichen.

    Args:
        filename: Der zu bereinigende Dateiname
        max_length: Maximale Länge des Dateinamens

    Returns:
        Bereinigter Dateiname
    """
    if not filename:
        return "unknown_file"

    # 1. Emojis entfernen/ersetzen
    sanitized = re.sub(EMOJI_PATTERN, "_", filename)
    
    # 2. Control characters entfernen
    sanitized = re.sub(CONTROL_CHARS_PATTERN, "", sanitized)
    
    # 3. Zero-width characters entfernen
    sanitized = re.sub(ZERO_WIDTH_PATTERN, "", sanitized)
    
    # 4. Bidirectional text control characters entfernen
    sanitized = re.sub(BIDI_CONTROL_PATTERN, "", sanitized)

    # 5. Ungültige Dateisystem-Zeichen ersetzen
    sanitized = re.sub(INVALID_FILENAME_CHARS, "_", sanitized)

    # 6. Mehrfache Punkte und Leerzeichen bereinigen
    sanitized = re.sub(r"\.+", ".", sanitized)
    sanitized = re.sub(r"\s+", " ", sanitized)
    
    # 7. Mehrfache Unterstriche durch einen ersetzen
    sanitized = re.sub(r"_+", "_", sanitized)

    # 8. Trimmen
    sanitized = sanitized.strip(" ._")

    # 9. Reservierte Namen prüfen
    if sanitized:
        name_without_ext = Path(sanitized).stem.upper()
        if name_without_ext in RESERVED_NAMES:
            sanitized = f"_{sanitized}"

        if max_name_length <= 0:
            sanitized = "unknown_file" + ext
        else:
            sanitized = name[:max_name_length] + ext

    return sanitized or "unknown_file"


@with_file_error_handling()
def create_filename_from_metadata(
    title: Optional[str] = None,
    performer: Optional[str] = None,
    file_id: Optional[str] = None,
    extension: str = ".mp3",
) -> str:
    """
    Erstellt einen Dateinamen aus Metadaten.

    Args:
        title: Titel des Tracks
        performer: Künstler/Interpret
        file_id: Fallback-ID für den Dateinamen
        extension: Dateiendung

    Returns:
        Generierter Dateiname
    """
    # Verwende eine vereinfachte Logik, um den zirkulären Import zu vermeiden
    parts = []

    if performer:
        parts.append(sanitize_filename(performer))

    if title:
        parts.append(sanitize_filename(title))

    if parts:
        filename = " - ".join(parts)
    elif file_id:
        filename = f"audio_{file_id}"
    else:
        filename = f"audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    return sanitize_filename(f"{filename}{extension}")


@with_file_error_handling()
def get_unique_filepath(base_path: Path) -> Path:
    """
    Erstellt einen eindeutigen Dateipfad, falls die Datei bereits existiert.

    Args:
        base_path: Basis-Dateipfad

    Returns:
        Eindeutiger Dateipfad
    """
    if not base_path.exists():
        return base_path

    counter = 1
    while True:
        stem = base_path.stem
        suffix = base_path.suffix
        parent = base_path.parent

        new_path = parent / f"{stem}_{counter}{suffix}"
        if not new_path.exists():
            return new_path
        counter += 1


@with_file_error_handling()
def calculate_file_hash(file_path: Union[str, Path], algorithm: str = "md5") -> str:
    """
    Berechnet den Hash einer Datei.

    Args:
        file_path: Pfad zur Datei
        algorithm: Hash-Algorithmus (md5, sha1, sha256)

    Returns:
        Hex-String des Datei-Hashes
    """
    hash_func = getattr(hashlib, algorithm.lower())()

    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_func.update(chunk)

    return hash_func.hexdigest()


@with_file_error_handling()
def extract_audio_metadata(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Extrahiert erweiterte Metadaten aus einer Audiodatei mit mutagen.

    Args:
        file_path: Pfad zur Audiodatei

    Returns:
        Dictionary mit erweiterten Metadaten
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
        for key in ["TIT2", "TITLE", "\xa9nam", "\xa9nam"]:
            if key in tags:
                metadata["title"] = (
                    str(tags[key][0]) if isinstance(tags[key], list) else str(tags[key])
                )
                break

        # Künstler
        for key in ["TPE1", "ARTIST", "\xa9ART", "\xa9ART"]:
            if key in tags:
                metadata["artist"] = (
                    str(tags[key][0]) if isinstance(tags[key], list) else str(tags[key])
                )
                break

        # Album
        for key in ["TALB", "ALBUM", "\xa9alb", "\xa9alb"]:
            if key in tags:
                metadata["album"] = (
                    str(tags[key][0]) if isinstance(tags[key], list) else str(tags[key])
                )
                break

        # Jahr/Datum
        for key in ["TDRC", "TDRL", "DATE", "\xa9day", "\xa9day"]:
            if key in tags:
                metadata["date"] = (
                    str(tags[key][0]) if isinstance(tags[key], list) else str(tags[key])
                )
                break

        # Genre
        for key in ["TCON", "GENRE", "\xa9gen", "\xa9gen"]:
            if key in tags:
                metadata["genre"] = (
                    str(tags[key][0]) if isinstance(tags[key], list) else str(tags[key])
                )
                break

        # Komponist
        for key in ["TCOM", "COMPOSER", "\xa9wrt", "\xa9wrt"]:
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
        for key in ["TCOP", "COPYRIGHT", "\xa9cpy", "\xa9cpy"]:
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
        for key in ["USLT", "LYRICS", "\xa9lyr", "\xa9lyr"]:
            if key in tags:
                metadata["lyrics"] = (
                    str(tags[key][0]) if isinstance(tags[key], list) else str(tags[key])
                )
                break

        # Kommentare
        for key in ["COMM", "COMMENT", "\xa9cmt", "\xa9cmt"]:
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


@with_file_error_handling()
def get_audio_duration(file_path: Union[str, Path]) -> Optional[float]:
    """
    Ermittelt die Dauer einer Audiodatei in Sekunden.

    Args:
        file_path: Pfad zur Audiodatei

    Returns:
        Dauer in Sekunden oder None bei Fehler
    """
    if not PYDUB_AVAILABLE:
        logger.warning(
            "pydub ist nicht verfügbar - Audiodauer kann nicht ermittelt werden"
        )
        return None

    try:
        audio = AudioSegment.from_file(file_path)
        return len(audio) / 1000.0  # Konvertierung von ms zu Sekunden
    except Exception as e:
        logger.error(f"Fehler beim Ermitteln der Audiodauer für {file_path}: {e}")
        return None


def format_file_size(size_bytes: int) -> str:
    """
    Formatiert eine Dateigröße in menschenlesbarer Form.

    Args:
        size_bytes: Größe in Bytes

    Returns:
        Formatierte Größenangabe
    """
    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1

    return f"{size_bytes:.1f} {size_names[i]}"


def format_duration(seconds: Optional[float]) -> str:
    """
    Formatiert eine Zeitdauer in menschenlesbarer Form.

    Args:
        seconds: Dauer in Sekunden

    Returns:
        Formatierte Zeitangabe (MM:SS oder HH:MM:SS)
    """
    if seconds is None or seconds <= 0:
        return "00:00"

    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"


def is_audio_file(file_path: Union[str, Path]) -> bool:
    """
    Überprüft, ob eine Datei eine Audiodatei ist.

    Args:
        file_path: Pfad zur Datei

    Returns:
        True, wenn es eine Audiodatei ist
    """
    return Path(file_path).suffix.lower() in AUDIO_EXTENSIONS


@with_file_error_handling()
def ensure_directory_exists(directory: Union[str, Path]) -> Path:
    """
    Stellt sicher, dass ein Verzeichnis existiert.

    Args:
        directory: Pfad zum Verzeichnis

    Returns:
        Path-Objekt des Verzeichnisses
    """
    dir_path = Path(directory)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def get_file_extension_from_mime(mime_type: str) -> str:
    """
    Ermittelt die Dateiendung basierend auf dem MIME-Type.

    Args:
        mime_type: MIME-Type der Datei

    Returns:
        Dateiendung mit Punkt (z.B. '.mp3')
    """
    mime_to_ext = {
        "audio/mpeg": ".mp3",
        "audio/mp3": ".mp3",
        "audio/mp4": ".m4a",
        "audio/m4a": ".m4a",
        "audio/ogg": ".ogg",
        "audio/flac": ".flac",
        "audio/wav": ".wav",
        "audio/x-wav": ".wav",
        "audio/opus": ".opus",
        "audio/aac": ".aac",
        "audio/x-ms-wma": ".wma",
    }

    return mime_to_ext.get(mime_type.lower(), ".mp3")


def validate_config_file(config_path: Union[str, Path]) -> bool:
    """
    Validiert eine Konfigurationsdatei.

    Args:
        config_path: Pfad zur Konfigurationsdatei

    Returns:
        True, wenn die Konfiguration gültig ist
    """
    config_path = Path(config_path)

    if not config_path.exists():
        logger.error(f"Konfigurationsdatei nicht gefunden: {config_path}")
        return False

    # Hier könnte eine detailliertere Validierung stehen
    return True


@with_file_error_handling()
def create_backup_filename(original_path: Union[str, Path]) -> Path:
    """
    Erstellt einen Backup-Dateinamen.

    Args:
        original_path: Ursprünglicher Dateipfad

    Returns:
        Backup-Dateipfad
    """
    original_path = Path(original_path)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    return (
        original_path.parent
        / f"{original_path.stem}_{timestamp}_backup{original_path.suffix}"
    )