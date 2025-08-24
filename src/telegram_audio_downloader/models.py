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

    created_at: DateTimeField = DateTimeField(default=datetime.now)
    updated_at: DateTimeField = DateTimeField(default=datetime.now)

    def save(self, *args: Any, **kwargs: Any) -> Any:
        self.updated_at = datetime.now()
        return super().save(*args, **kwargs)

    class Meta:
        database = db


class DownloadStatus(Enum):
    """Status einer heruntergeladenen Datei."""

    PENDING = "pending"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class TelegramGroup(BaseModel):
    """Modell für eine Telegram-Gruppe."""

    group_id: IntegerField = IntegerField(unique=True)
    title: CharField = CharField(max_length=255)
    username: Optional[CharField] = CharField(max_length=255, null=True)
    last_checked: Optional[DateTimeField] = DateTimeField(null=True)

    class Meta:
        table_name = "telegram_groups"


class AudioFile(BaseModel):
    """Modell für eine Audiodatei mit speichereffizienten Methoden."""

    file_id: CharField = CharField(max_length=255, unique=True)
    file_name: CharField = CharField(max_length=255)
    file_size: IntegerField = IntegerField(null=True)
    duration: IntegerField = IntegerField(null=True)
    title: CharField = CharField(max_length=255, null=True)
    performer: CharField = CharField(max_length=255, null=True)
    album: CharField = CharField(max_length=255, null=True)
    date: CharField = CharField(max_length=50, null=True)
    genre: CharField = CharField(max_length=100, null=True)
    composer: CharField = CharField(max_length=255, null=True)
    track_number: CharField = CharField(max_length=10, null=True)
    group: ForeignKeyField = ForeignKeyField(TelegramGroup, backref='audio_files', on_delete='CASCADE')
    downloaded_at: DateTimeField = DateTimeField(null=True)
    status: CharField = CharField(max_length=50, default=DownloadStatus.PENDING.value)
    error_message: TextField = TextField(null=True)
    download_attempts: IntegerField = IntegerField(default=0)
    # Neue Felder für die fortgeschrittene Download-Wiederaufnahme
    resume_offset: IntegerField = IntegerField(default=0)
    resume_checksum: CharField = CharField(max_length=255, null=True)

    class Meta:
        table_name = "audio_files"

    @property
    def file_extension(self) -> str:
        """Gibt die Dateiendung zurück."""
        return Path(self.file_name).suffix.lower()

    @property
    def is_downloaded(self) -> bool:
        """Überprüft, ob die Datei heruntergeladen wurde."""
        return self.status == DownloadStatus.COMPLETED.value and bool(self.local_path)

    @property
    def is_partially_downloaded(self) -> bool:
        """Überprüft, ob die Datei teilweise heruntergeladen wurde."""
        return (
            self.downloaded_bytes > 0
            and self.downloaded_bytes < self.file_size
            and self.partial_file_path is not None
        )

    @property
    def download_progress(self) -> float:
        """Gibt den Download-Fortschritt als Prozentsatz zurück."""
        if self.file_size <= 0:
            return 0.0
        return min(100.0, (self.downloaded_bytes / self.file_size) * 100)

    def can_resume_download(self) -> bool:
        """Überprüft, ob der Download fortgesetzt werden kann."""
        return (
            self.status
            in [DownloadStatus.FAILED.value, DownloadStatus.DOWNLOADING.value]
            and self.is_partially_downloaded
            and self.partial_file_path
            and Path(self.partial_file_path).exists()
        )

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
        result = {
            "file_id": self.file_id,
            "file_name": self.file_name,
            "file_size": self.file_size,
            "status": self.status,
        }
        
        if include_metadata and self.title:
            result["title"] = self.title
        if include_metadata and self.performer:
            result["performer"] = self.performer
        if self.local_path:
            result["local_path"] = self.local_path
            
        return result