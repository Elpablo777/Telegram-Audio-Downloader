"""
Dateioperationen für den Telegram Audio Downloader.
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

# Ungültige Zeichen für Dateinamen (erweitert für bessere Kompatibilität)
INVALID_FILENAME_CHARS = r'[<>:"/\\|?*\x00-\x1f\x7f-\x9f]'
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
    Bereinigt einen Dateinamen von ungültigen Zeichen.
    
    Entfernt oder ersetzt problematische Zeichen:
    - Ungültige Dateisystemzeichen (< > : " / \\ | ? * und Steuerzeichen)
    - Emojis und problematische Unicode-Zeichen
    - Führende/nachgestellte Punkte und Leerzeichen
    - Reservierte Windows-Namen

    Args:
        filename: Der zu bereinigende Dateiname
        max_length: Maximale Länge des Dateinamens

    Returns:
        Bereinigter Dateiname
    """
    if not filename:
        return "unknown_file"

    # Ursprünglichen Dateinamen für Fallback speichern

    # 1. Ungültige Dateisystem-Zeichen ersetzen (inklusive Steuerzeichen)
    sanitized = re.sub(INVALID_FILENAME_CHARS, "_", filename)
    
    # 2. Emojis und problematische Unicode-Zeichen handhaben
    # Entferne nur Emojis, behalte normale internationale Zeichen (Chinesisch, Kyrillisch, etc.)
    # Spezifische Emoji-Bereiche ohne Überlappung mit normalen Zeichen
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # Emoticons
        "\U0001F300-\U0001F5FF"  # Symbole & Piktogramme
        "\U0001F680-\U0001F6FF"  # Transport & Karten
        "\U0001F1E0-\U0001F1FF"  # Flags
        "\U00002702-\U000027B0"  # Dingbats
        "\U0001F900-\U0001F9FF"  # Ergänzende Symbole
        "\U0001FA70-\U0001FAFF"  # Symbole und Piktogramme Extended-A
        "\U00002600-\U000026FF"  # Verschiedene Symbole
        "]+", flags=re.UNICODE)
    sanitized = emoji_pattern.sub("_", sanitized)

    # 3. Problematische Unicode-Zeichen ersetzen (behalte normale internationale Zeichen)
    # Nur sehr problematische Zeichen ersetzen, normale Akzente etc. beibehalten
    problematic_unicode = re.compile(r'[\u200B-\u200F\u202A-\u202E\u2060-\u206F\uFEFF]')  # Unsichtbare/Steuerzeichen
    sanitized = problematic_unicode.sub("_", sanitized)

    # 4. Mehrfache Punkte normalisieren (aber nicht komplett entfernen für Tests)
    sanitized = re.sub(r"\.{2,}", ".", sanitized)  # Nur 2+ Punkte zu einem reduzieren
    
    # 5. Mehrfache Leerzeichen und Unterstriche normalisieren
    sanitized = re.sub(r"\s+", " ", sanitized)
    sanitized = re.sub(r"_{2,}", "_", sanitized)

    # 6. Trimmen von Leerzeichen, aber Punkte nur am Ende entfernen wenn es kein Extension-Punkt ist
    sanitized = sanitized.strip()
    # Entferne führende Punkte
    sanitized = sanitized.lstrip(".")
    # Entferne nachgestellte Punkte nur wenn sie nicht Teil einer Dateiendung sind
    if sanitized.endswith(".") and "." not in sanitized[:-1]:
        sanitized = sanitized.rstrip(".")

    # 7. Prüfung ob nach Bereinigung noch etwas übrig ist
    if not sanitized or sanitized in [".", ".."]:
        return "unknown_file"

    # 8. Reservierte Namen prüfen
    name_without_ext = Path(sanitized).stem.upper()
    if name_without_ext in RESERVED_NAMES:
        sanitized = f"_{sanitized}"

    # 9. Länge begrenzen
    if len(sanitized) > max_length:
        name, ext = os.path.splitext(sanitized)
        max_name_length = max_length - len(ext)
        if max_name_length > 0:
            sanitized = name[:max_name_length] + ext
        else:
            # Wenn Extension zu lang ist, nur die Extension verwenden
            sanitized = ext[:max_length] if ext else "file"

    # 10. Finaler Fallback
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
        "track_number": None,
    }

    if not file_path.exists():
        raise FileOperationError(f"Datei nicht gefunden: {file_path}")

    try:
        audio_file = mutagen.File(str(file_path))
        if audio_file is None:
            logger.warning(f"Konnte Metadaten nicht lesen: {file_path}")
            return metadata

        # Allgemeine Metadaten extrahieren
        if hasattr(audio_file, "tags") and audio_file.tags:
            # MP3 ID3-Tags
            if hasattr(audio_file.tags, "getall"):
                if audio_file.tags.getall("TIT2"):
                    metadata["title"] = str(audio_file.tags.getall("TIT2")[0])
                if audio_file.tags.getall("TPE1"):
                    metadata["artist"] = str(audio_file.tags.getall("TPE1")[0])
                if audio_file.tags.getall("TALB"):
                    metadata["album"] = str(audio_file.tags.getall("TALB")[0])
                if audio_file.tags.getall("TDRC"):
                    metadata["date"] = str(audio_file.tags.getall("TDRC")[0])
                if audio_file.tags.getall("TCON"):
                    metadata["genre"] = str(audio_file.tags.getall("TCON")[0])
                if audio_file.tags.getall("TCOM"):
                    metadata["composer"] = str(audio_file.tags.getall("TCOM")[0])
                if audio_file.tags.getall("TRCK"):
                    metadata["track_number"] = str(audio_file.tags.getall("TRCK")[0])

            # Andere Formate (FLAC, OGG, etc.)
            else:
                if "title" in audio_file:
                    metadata["title"] = audio_file["title"][0] if isinstance(audio_file["title"], list) else audio_file["title"]
                if "artist" in audio_file:
                    metadata["artist"] = audio_file["artist"][0] if isinstance(audio_file["artist"], list) else audio_file["artist"]
                if "album" in audio_file:
                    metadata["album"] = audio_file["album"][0] if isinstance(audio_file["album"], list) else audio_file["album"]
                if "date" in audio_file:
                    metadata["date"] = audio_file["date"][0] if isinstance(audio_file["date"], list) else audio_file["date"]
                if "genre" in audio_file:
                    metadata["genre"] = audio_file["genre"][0] if isinstance(audio_file["genre"], list) else audio_file["genre"]
                if "composer" in audio_file:
                    metadata["composer"] = audio_file["composer"][0] if isinstance(audio_file["composer"], list) else audio_file["composer"]
                if "tracknumber" in audio_file:
                    metadata["track_number"] = audio_file["tracknumber"][0] if isinstance(audio_file["tracknumber"], list) else audio_file["tracknumber"]

        # Dateiinformationen
        if hasattr(audio_file, "info"):
            metadata["duration"] = getattr(audio_file.info, "length", None)
            metadata["bitrate"] = getattr(audio_file.info, "bitrate", None)
            metadata["sample_rate"] = getattr(audio_file.info, "sample_rate", None)

    except Exception as e:
        logger.warning(f"Fehler beim Lesen der Metadaten von {file_path}: {e}")

    return metadata


@with_file_error_handling()
def is_audio_file(file_path: Union[str, Path]) -> bool:
    """
    Prüft, ob es sich bei der Datei um eine unterstützte Audio-Datei handelt.

    Args:
        file_path: Pfad zur Datei

    Returns:
        True, wenn es sich um eine Audio-Datei handelt
    """
    file_path = Path(file_path)
    return file_path.suffix.lower() in AUDIO_EXTENSIONS


@with_file_error_handling()
def create_download_directory(base_path: Union[str, Path]) -> Path:
    """
    Erstellt das Download-Verzeichnis, falls es nicht existiert.

    Args:
        base_path: Basispfad für das Download-Verzeichnis

    Returns:
        Path-Objekt des Download-Verzeichnisses
    """
    download_path = Path(base_path)
    download_path.mkdir(parents=True, exist_ok=True)
    return download_path


@with_file_error_handling()
def format_file_size(size_bytes: int) -> str:
    """
    Formatiert die Dateigröße in ein lesbares Format.

    Args:
        size_bytes: Dateigröße in Bytes

    Returns:
        Formatierter Dateigröße-String
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size = float(size_bytes)
    
    while size >= 1024.0 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1
    
    return f"{size:.1f} {size_names[i]}"


@with_file_error_handling()
def format_duration(seconds: float) -> str:
    """
    Formatiert die Dauer in ein lesbares Format.

    Args:
        seconds: Dauer in Sekunden

    Returns:
        Formatierter Dauer-String
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"