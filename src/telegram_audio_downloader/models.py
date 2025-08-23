"""
Datenbankmodelle für den Telegram Audio Downloader.
"""
from enum import Enum
from datetime import datetime
from peewee import (
    Model,
    SqliteDatabase,
    CharField,
    IntegerField,
    DateTimeField,
    BooleanField,
    ForeignKeyField,
    TextField,
    FloatField,
)
from pathlib import Path
from typing import Optional

# Datenbank-Initialisierung erfolgt in database.py
db = SqliteDatabase(None)  # Wird später initialisiert


class BaseModel(Model):
    """Basisklasse für alle Modelle mit gemeinsamen Feldern."""
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)

    def save(self, *args, **kwargs):
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
    group_id = IntegerField(unique=True)
    title = CharField(max_length=255)
    username = CharField(max_length=255, null=True)
    last_checked = DateTimeField(null=True)

    class Meta:
        table_name = 'telegram_groups'


class AudioFile(BaseModel):
    """Modell für eine Audiodatei."""
    file_id = CharField(max_length=255, unique=True)
    file_unique_id = CharField(max_length=255, null=True)  # Kann None sein
    file_name = CharField(max_length=510)  # Doppelte Länge für UTF-8 Zeichen
    file_size = IntegerField()
    mime_type = CharField(max_length=100)
    duration = IntegerField(null=True)  # Dauer in Sekunden
    title = CharField(max_length=255, null=True)
    performer = CharField(max_length=255, null=True)
    local_path = TextField(null=True)  # Lokaler Pfad zur Datei
    status = CharField(
        max_length=20,
        default=DownloadStatus.PENDING.value,
        choices=[(status.value, status.name) for status in DownloadStatus]
    )
    error_message = TextField(null=True)
    downloaded_at = DateTimeField(null=True)
    
    # Neue Felder für fortsetzbare Downloads
    partial_file_path = TextField(null=True)  # Pfad zur partiellen Datei
    downloaded_bytes = IntegerField(default=0)  # Bereits heruntergeladene Bytes
    checksum_md5 = CharField(max_length=32, null=True)  # MD5-Checksum
    checksum_verified = BooleanField(default=False)  # Checksum verifiziert
    download_attempts = IntegerField(default=0)  # Anzahl der Download-Versuche
    last_attempt_at = DateTimeField(null=True)  # Zeitpunkt des letzten Versuchs
    
    # Beziehungen
    group = ForeignKeyField(TelegramGroup, backref='audio_files', null=True)
    
    class Meta:
        table_name = 'audio_files'
    
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
            self.downloaded_bytes > 0 and 
            self.downloaded_bytes < self.file_size and
            self.partial_file_path is not None
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
            self.status in [DownloadStatus.FAILED.value, DownloadStatus.DOWNLOADING.value] and
            self.is_partially_downloaded and
            self.partial_file_path and
            Path(self.partial_file_path).exists()
        )
