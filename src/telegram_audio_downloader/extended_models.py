"""
Erweiterte Datenbankmodelle für den Telegram Audio Downloader.

Neue Modelle:
- User für Zugriffskontrolle
- DownloadQueue für Warteschlangenverwaltung
- Tag für Kategorisierung
- Playlist für Sammlungen
"""

from datetime import datetime
from typing import Optional, List, Set
from enum import Enum

from peewee import (
    BooleanField,
    CharField,
    DateTimeField,
    ForeignKeyField,
    IntegerField,
    ManyToManyField,
    TextField,
)

from .models import BaseModel, db, AudioFile, TelegramGroup


class UserRole(Enum):
    """Benutzerrollen."""
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"


class User(BaseModel):
    """Modell für Benutzer mit Zugriffskontrolle."""
    
    username: CharField = CharField(max_length=100, unique=True)
    email: CharField = CharField(max_length=255, unique=True)
    password_hash: CharField = CharField(max_length=255)  # Gehashtes Passwort
    role: CharField = CharField(
        max_length=20,
        default=UserRole.USER.value,
        choices=[(role.value, role.name) for role in UserRole],
    )
    is_active: BooleanField = BooleanField(default=True)
    last_login: Optional[DateTimeField] = DateTimeField(null=True)
    created_at: DateTimeField = DateTimeField(default=datetime.now)
    
    class Meta:
        table_name = "users"
    
    def __str__(self) -> str:
        return f"User(username='{self.username}', email='{self.email}', role='{self.role}')"


class DownloadPriority(Enum):
    """Prioritäten für Downloads."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class DownloadQueueStatus(Enum):
    """Status für Download-Queue-Einträge."""
    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DownloadQueue(BaseModel):
    """Modell für die Download-Warteschlange."""
    
    audio_file: Optional[ForeignKeyField] = ForeignKeyField(AudioFile, backref="queue_entries", null=True)
    group: Optional[ForeignKeyField] = ForeignKeyField(TelegramGroup, backref="queue_entries", null=True)
    user: Optional[ForeignKeyField] = ForeignKeyField(User, backref="queue_entries", null=True)
    
    # Download-Parameter
    priority: CharField = CharField(
        max_length=20,
        default=DownloadPriority.NORMAL.value,
        choices=[(priority.value, priority.name) for priority in DownloadPriority],
    )
    scheduled_at: Optional[DateTimeField] = DateTimeField(null=True)  # Geplante Download-Zeit
    max_retries: IntegerField = IntegerField(default=3)
    
    # Status
    status: CharField = CharField(
        max_length=20,
        default=DownloadQueueStatus.PENDING.value,
        choices=[(status.value, status.name) for status in DownloadQueueStatus],
    )
    retry_count: IntegerField = IntegerField(default=0)
    error_message: Optional[TextField] = TextField(null=True)
    
    # Abhängigkeiten
    dependencies: Optional[TextField] = TextField(null=True)  # JSON-Liste von abhängigen Datei-IDs
    
    class Meta:
        table_name = "download_queue"
        indexes = (
            # Index für Status-Abfragen
            (("status",), False),
            # Index für Prioritäts-Abfragen
            (("priority", "status"), False),
            # Index für Benutzer-Abfragen
            (("user", "status"), False),
        )
    
    def __str__(self) -> str:
        return f"DownloadQueue(audio_file='{self.audio_file}', priority='{self.priority}', status='{self.status}')"


class Tag(BaseModel):
    """Modell für Tags zur Kategorisierung."""
    
    name: CharField = CharField(max_length=100, unique=True)
    description: Optional[TextField] = TextField(null=True)
    color: Optional[CharField] = CharField(max_length=7, null=True)  # Hex-Farbe (#RRGGBB)
    created_by: Optional[ForeignKeyField] = ForeignKeyField(User, backref="created_tags", null=True)
    
    class Meta:
        table_name = "tags"
    
    def __str__(self) -> str:
        return f"Tag(name='{self.name}')"


class AudioFileTag(BaseModel):
    """Zwischentabelle für die Many-to-Many-Beziehung zwischen AudioFile und Tag."""
    
    audio_file: ForeignKeyField = ForeignKeyField(AudioFile, on_delete="CASCADE")
    tag: ForeignKeyField = ForeignKeyField(Tag, on_delete="CASCADE")
    
    class Meta:
        table_name = "audio_file_tags"
        indexes = (
            # Eindeutiger Index, um Duplikate zu vermeiden
            (("audio_file", "tag"), True),
        )
    
    def __str__(self) -> str:
        return f"AudioFileTag(audio_file_id={self.audio_file_id}, tag_id={self.tag_id})"


class Playlist(BaseModel):
    """Modell für Playlists."""
    
    name: CharField = CharField(max_length=255)
    description: Optional[TextField] = TextField(null=True)
    user: ForeignKeyField = ForeignKeyField(User, backref="playlists")
    is_public: BooleanField = BooleanField(default=False)
    cover_image_path: Optional[TextField] = TextField(null=True)
    created_at: DateTimeField = DateTimeField(default=datetime.now)
    
    class Meta:
        table_name = "playlists"
        indexes = (
            # Index für Benutzer-Abfragen
            (("user",), False),
            # Index für öffentliche Playlists
            (("is_public",), False),
        )
    
    def __str__(self) -> str:
        return f"Playlist(name='{self.name}', user='{self.user.username}')"


class PlaylistAudioFile(BaseModel):
    """Zwischentabelle für die Many-to-Many-Beziehung zwischen Playlist und AudioFile."""
    
    playlist: ForeignKeyField = ForeignKeyField(Playlist, on_delete="CASCADE")
    audio_file: ForeignKeyField = ForeignKeyField(AudioFile, on_delete="CASCADE")
    position: IntegerField = IntegerField()  # Position in der Playlist
    
    class Meta:
        table_name = "playlist_audio_files"
        indexes = (
            # Index für Playlist-Abfragen
            (("playlist", "position"), False),
            # Eindeutiger Index für AudioFile-Position in Playlist
            (("playlist", "audio_file"), True),
        )
    
    def __str__(self) -> str:
        return f"PlaylistAudioFile(playlist_id={self.playlist_id}, audio_file_id={self.audio_file_id}, position={self.position})"


class UserPreference(BaseModel):
    """Modell für Benutzereinstellungen."""
    
    user: ForeignKeyField = ForeignKeyField(User, backref="preferences")
    key: CharField = CharField(max_length=100)
    value: TextField = TextField()
    updated_at: DateTimeField = DateTimeField(default=datetime.now)
    
    class Meta:
        table_name = "user_preferences"
        indexes = (
            # Eindeutiger Index für Benutzer-Schlüssel-Kombination
            (("user", "key"), True),
        )
    
    def __str__(self) -> str:
        return f"UserPreference(user='{self.user.username}', key='{self.key}')"


# Erweiterte Beziehungen für bestehende Modelle
def extend_existing_models() -> None:
    """Erweitert die bestehenden Modelle mit zusätzlichen Beziehungen."""
    
    # Füge Benutzer-Beziehung zu AudioFile hinzu
    if not hasattr(AudioFile, 'created_by'):
        AudioFile.add_field('created_by', ForeignKeyField(User, backref="created_audio_files", null=True))
    
    # Füge Benutzer-Beziehung zu TelegramGroup hinzu
    if not hasattr(TelegramGroup, 'created_by'):
        TelegramGroup.add_field('created_by', ForeignKeyField(User, backref="created_groups", null=True))


def create_extended_tables() -> None:
    """Erstellt die Tabellen für die erweiterten Modelle."""
    with db:
        # Erstelle die Tabellen
        db.create_tables([
            User,
            DownloadQueue,
            Tag,
            AudioFileTag,
            Playlist,
            PlaylistAudioFile,
            UserPreference,
        ], safe=True)
        
        # Erweitere bestehende Modelle
        extend_existing_models()


def get_user_playlists(user_id: int) -> List[Playlist]:
    """
    Gibt alle Playlists eines Benutzers zurück.
    
    Args:
        user_id: ID des Benutzers
        
    Returns:
        Liste von Playlist-Objekten
    """
    return list(Playlist.select().where(Playlist.user == user_id))


def get_playlist_audio_files(playlist_id: int) -> List[AudioFile]:
    """
    Gibt alle Audiodateien einer Playlist zurück.
    
    Args:
        playlist_id: ID der Playlist
        
    Returns:
        Liste von AudioFile-Objekten
    """
    return list(
        AudioFile.select()
        .join(PlaylistAudioFile)
        .where(PlaylistAudioFile.playlist == playlist_id)
        .order_by(PlaylistAudioFile.position)
    )


def get_audio_file_tags(audio_file_id: int) -> List[Tag]:
    """
    Gibt alle Tags einer Audiodatei zurück.
    
    Args:
        audio_file_id: ID der Audiodatei
        
    Returns:
        Liste von Tag-Objekten
    """
    return list(
        Tag.select()
        .join(AudioFileTag)
        .where(AudioFileTag.audio_file == audio_file_id)
    )


def add_tag_to_audio_file(audio_file_id: int, tag_id: int) -> bool:
    """
    Fügt ein Tag zu einer Audiodatei hinzu.
    
    Args:
        audio_file_id: ID der Audiodatei
        tag_id: ID des Tags
        
    Returns:
        True, wenn das Tag hinzugefügt wurde
    """
    try:
        AudioFileTag.get_or_create(
            audio_file=audio_file_id,
            tag=tag_id
        )
        return True
    except Exception as e:
        print(f"Fehler beim Hinzufügen des Tags: {e}")
        return False


def remove_tag_from_audio_file(audio_file_id: int, tag_id: int) -> bool:
    """
    Entfernt ein Tag von einer Audiodatei.
    
    Args:
        audio_file_id: ID der Audiodatei
        tag_id: ID des Tags
        
    Returns:
        True, wenn das Tag entfernt wurde
    """
    try:
        query = AudioFileTag.delete().where(
            (AudioFileTag.audio_file == audio_file_id) &
            (AudioFileTag.tag == tag_id)
        )
        return query.execute() > 0
    except Exception as e:
        print(f"Fehler beim Entfernen des Tags: {e}")
        return False