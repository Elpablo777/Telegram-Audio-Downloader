"""
Datenbankmodelle für den Telegram Audio Downloader.
"""

import weakref
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, Any, Dict, Set
from collections import defaultdict

from peewee import (
    BooleanField,
    CharField,
    DateTimeField,
    ForeignKeyField,
    IntegerField,
    Model,
    SqliteDatabase,
    TextField,
)

# Datenbank-Initialisierung erfolgt in database.py
db = SqliteDatabase(None)  # Wird später initialisiert


class BaseModel(Model):
    """Basisklasse für alle Modelle mit gemeinsamen Feldern."""

    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)

    def save(self, *args: Any, **kwargs: Any) -> Any:
        self.updated_at = datetime.now()
        return super().save(*args, **kwargs)


class DownloadStatus(Enum):
    """Status einer heruntergeladenen Datei."""

    PENDING = "pending"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class TelegramGroup(BaseModel):
    """Modell für eine Telegram-Gruppe."""

    group_id = IntegerField(unique=True)
    title = CharField(max_length=255)
    username = CharField(max_length=255, null=True)
    last_checked = DateTimeField(null=True)

    class Meta:
        table_name = "telegram_groups"
        database = db


class GroupProgress(BaseModel):
    """Modell für den Fortschritt einer Gruppe (letzte verarbeitete Nachrichten-ID)."""

    group_id = IntegerField(unique=True)  # Direktes Feld statt ForeignKey
    group_title = CharField(max_length=255, null=True)
    group_username = CharField(max_length=255, null=True)
    last_message_id = IntegerField()
    last_updated = DateTimeField(default=datetime.now)

    class Meta:
        table_name = "group_progress"
        database = db
        indexes = (
            (('group_id',), True),  # Eindeutiger Index für group_id
        )


class AudioFile(BaseModel):
    """Modell für eine Audiodatei mit speichereffizienten Methoden."""

    file_id = CharField(max_length=255, unique=True)
    file_unique_id = CharField(max_length=255, null=True)  # Hinzugefügtes Feld
    file_name = CharField(max_length=510)  # Vergrößert auf 510
    file_size = IntegerField()
    mime_type = CharField(max_length=100, null=True)
    duration = IntegerField(null=True)
    title = CharField(max_length=255, null=True)
    performer = CharField(max_length=255, null=True)
    album = CharField(max_length=255, null=True)
    date = CharField(max_length=50, null=True)
    genre = CharField(max_length=100, null=True)
    composer = CharField(max_length=255, null=True)
    track_number = CharField(max_length=10, null=True)
    local_path = TextField(null=True)  # Hinzugefügtes Feld
    status = CharField(max_length=20, default=DownloadStatus.PENDING.value)
    error_message = TextField(null=True)
    downloaded_at = DateTimeField(null=True)
    partial_file_path = TextField(null=True)  # Hinzugefügtes Feld
    downloaded_bytes = IntegerField(default=0)
    checksum_md5 = CharField(max_length=32, null=True)  # Hinzugefügtes Feld
    checksum_verified = BooleanField(default=False)  # Hinzugefügtes Feld
    download_attempts = IntegerField(default=0)
    last_attempt_at = DateTimeField(null=True)
    group = ForeignKeyField(TelegramGroup, backref='audio_files', on_delete='CASCADE', null=True)  # null=True hinzugefügt
    resume_offset = IntegerField(default=0)
    resume_checksum = CharField(max_length=255, null=True)
    message_id = IntegerField(null=True)

    class Meta:
        table_name = "audio_files"
        database = db

    @property
    def file_extension(self) -> str:
        """Gibt die Dateiendung zurück."""
        try:
            # Verwende getattr für sicheren Zugriff
            file_name = getattr(self, 'file_name', '')
            return Path(str(file_name)).suffix.lower()
        except Exception:
            return ""

    @property
    def is_downloaded(self) -> bool:
        """Überprüft, ob die Datei heruntergeladen wurde."""
        try:
            status = getattr(self, 'status', '')
            local_path = getattr(self, 'local_path', None)
            return str(status) == DownloadStatus.COMPLETED.value and bool(local_path)
        except Exception:
            return False

    @property
    def is_partially_downloaded(self) -> bool:
        """Überprüft, ob die Datei teilweise heruntergeladen wurde."""
        try:
            downloaded_bytes = getattr(self, 'downloaded_bytes', 0)
            file_size = getattr(self, 'file_size', 0)
            partial_file_path = getattr(self, 'partial_file_path', None)
            
            # Konvertiere in Integer, falls notwendig
            if hasattr(downloaded_bytes, '__int__'):
                downloaded_bytes = downloaded_bytes.__int__()
            if hasattr(file_size, '__int__'):
                file_size = file_size.__int__()
                
            downloaded_bytes_int = int(downloaded_bytes)
            file_size_int = int(file_size)
            
            return (
                downloaded_bytes_int > 0
                and downloaded_bytes_int < file_size_int
                and partial_file_path is not None
            )
        except (ValueError, TypeError):
            return False

    @property
    def download_progress(self) -> float:
        """Gibt den Download-Fortschritt als Prozentsatz zurück."""
        try:
            file_size = getattr(self, 'file_size', 0)
            downloaded_bytes = getattr(self, 'downloaded_bytes', 0)
            
            # Konvertiere in Integer, falls notwendig
            if hasattr(file_size, '__int__'):
                file_size = file_size.__int__()
            if hasattr(downloaded_bytes, '__int__'):
                downloaded_bytes = downloaded_bytes.__int__()
                
            file_size_int = int(file_size)
            downloaded_bytes_int = int(downloaded_bytes)
            
            if file_size_int <= 0:
                return 0.0
            progress = (float(downloaded_bytes_int) / float(file_size_int)) * 100
            return min(100.0, progress)
        except (ValueError, TypeError):
            return 0.0

    def can_resume_download(self) -> bool:
        """Überprüft, ob der Download fortgesetzt werden kann."""
        try:
            status = getattr(self, 'status', '')
            partial_file_path = getattr(self, 'partial_file_path', None)
            
            is_partial = self.is_partially_downloaded
            
            # Stelle sicher, dass alle Bedingungen erfüllt sind und gib einen expliziten Boolean zurück
            can_resume = (
                str(status) in [DownloadStatus.FAILED.value, DownloadStatus.DOWNLOADING.value]
                and is_partial
                and partial_file_path is not None
                and Path(str(partial_file_path)).exists()
            )
            return bool(can_resume)
        except Exception:
            return False

    @classmethod
    def get_completed_files_cache(cls, max_cache_size: int = 50000) -> Set[str]:
        """
        Gibt eine Menge von file_ids für bereits heruntergeladene Dateien zurück.
        Verwendet eine begrenzte Menge, um Speicher zu sparen.
        
        Args:
            max_cache_size: Maximale Anzahl von Datei-IDs im Cache
            
        Returns:
            Menge von file_ids für abgeschlossene Downloads
        """
        # Verwende eine begrenzte Menge, um Speicher zu sparen
        completed_files = set()
        query = cls.select(cls.file_id).where(
            cls.status == DownloadStatus.COMPLETED.value
        ).limit(max_cache_size)
        
        for audio_file in query:
            completed_files.add(audio_file.file_id)
            
        return completed_files

    @classmethod
    def get_files_by_group(cls, group_id: int, limit: int = 1000) -> list:
        """
        Gibt eine begrenzte Liste von Dateien für eine Gruppe zurück.
        
        Args:
            group_id: ID der Telegram-Gruppe
            limit: Maximale Anzahl zurückzugebender Dateien
            
        Returns:
            Liste von AudioFile-Objekten
        """
        return list(cls.select().where(cls.group == group_id).limit(limit))

    def to_dict(self, include_metadata: bool = True) -> Dict[str, Any]:
        """
        Konvertiert das AudioFile-Objekt in ein Dictionary.
        Reduziert den Speicherverbrauch durch selektive Serialisierung.
        
        Args:
            include_metadata: Ob Metadaten (Titel, Interpret) enthalten sein sollen
            
        Returns:
            Dictionary-Repräsentation des Objekts
        """
        try:
            file_id = getattr(self, 'file_id', '')
            file_name = getattr(self, 'file_name', '')
            file_size = getattr(self, 'file_size', 0)
            status = getattr(self, 'status', '')
            
            # Konvertiere in Integer, falls notwendig
            if hasattr(file_size, '__int__'):
                file_size = file_size.__int__()
            
            result = {
                "file_id": str(file_id),
                "file_name": str(file_name),
                "file_size": int(file_size),
                "status": str(status),
            }
            
            if include_metadata:
                title = getattr(self, 'title', None)
                performer = getattr(self, 'performer', None)
                if title:
                    result["title"] = str(title)
                if performer:
                    result["performer"] = str(performer)
                    
            local_path = getattr(self, 'local_path', None)
            if local_path:
                result["local_path"] = str(local_path)
                
            return result
        except Exception:
            # Fallback-Werte im Fehlerfall
            return {
                "file_id": "",
                "file_name": "",
                "file_size": 0,
                "status": "",
            }
