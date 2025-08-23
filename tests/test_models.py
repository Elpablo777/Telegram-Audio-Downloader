"""
Tests für die Datenbankmodelle.
"""
import pytest
import tempfile
import os
from datetime import datetime
from pathlib import Path

from src.telegram_audio_downloader.models import AudioFile, TelegramGroup, DownloadStatus, db
from src.telegram_audio_downloader.database import init_db, close_db


@pytest.fixture
def test_db():
    """Erstellt eine Test-Datenbank."""
    # Temporäre Datenbankdatei
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(db_fd)
    
    # Datenbank initialisieren
    init_db(db_path)
    
    yield db
    
    # Cleanup
    close_db()
    os.unlink(db_path)


@pytest.fixture
def sample_group(test_db):
    """Erstellt eine Test-Gruppe."""
    group = TelegramGroup.create(
        group_id=12345,
        title="Test Gruppe",
        username="testgroup"
    )
    return group


@pytest.fixture
def sample_audio_file(test_db, sample_group):
    """Erstellt eine Test-Audiodatei."""
    audio_file = AudioFile.create(
        file_id="test_file_123",
        file_unique_id="unique_123",
        file_name="test_song.mp3",
        file_size=1024000,
        mime_type="audio/mpeg",
        duration=180,
        title="Test Song",
        performer="Test Artist",
        group=sample_group,
        status=DownloadStatus.PENDING.value
    )
    return audio_file


class TestTelegramGroup:
    """Tests für das TelegramGroup-Modell."""
    
    def test_create_group(self, test_db):
        """Test Gruppe erstellen."""
        group = TelegramGroup.create(
            group_id=123456,
            title="Neue Gruppe",
            username="neuegruppe"
        )
        
        assert group.group_id == 123456
        assert group.title == "Neue Gruppe"
        assert group.username == "neuegruppe"
        assert group.created_at is not None
    
    def test_group_without_username(self, test_db):
        """Test Gruppe ohne Benutzername."""
        group = TelegramGroup.create(
            group_id=789012,
            title="Private Gruppe"
        )
        
        assert group.username is None
        assert group.title == "Private Gruppe"
    
    def test_unique_group_id(self, test_db, sample_group):
        """Test eindeutige Gruppen-ID."""
        with pytest.raises(Exception):  # Peewee IntegrityError
            TelegramGroup.create(
                group_id=sample_group.group_id,  # Doppelte ID
                title="Andere Gruppe"
            )


class TestAudioFile:
    """Tests für das AudioFile-Modell."""
    
    def test_create_audio_file(self, test_db, sample_group):
        """Test Audiodatei erstellen."""
        audio_file = AudioFile.create(
            file_id="audio_456",
            file_unique_id="unique_456",
            file_name="song.mp3",
            file_size=2048000,
            mime_type="audio/mpeg",
            duration=240,
            title="Neuer Song",
            performer="Neuer Künstler",
            group=sample_group
        )
        
        assert audio_file.file_id == "audio_456"
        assert audio_file.title == "Neuer Song"
        assert audio_file.performer == "Neuer Künstler"
        assert audio_file.group == sample_group
        assert audio_file.status == DownloadStatus.PENDING.value
    
    def test_audio_file_properties(self, sample_audio_file):
        """Test AudioFile-Eigenschaften."""
        assert sample_audio_file.file_extension == ".mp3"
        assert sample_audio_file.is_downloaded == False
    
    def test_audio_file_completed_status(self, test_db, sample_group):
        """Test AudioFile mit completed Status."""
        audio_file = AudioFile.create(
            file_id="completed_file",
            file_unique_id="unique_completed",
            file_name="completed.mp3",
            file_size=1000000,
            mime_type="audio/mpeg",
            local_path="/path/to/completed.mp3",
            status=DownloadStatus.COMPLETED.value,
            downloaded_at=datetime.now(),
            group=sample_group
        )
        
        assert audio_file.is_downloaded == True
        assert audio_file.downloaded_at is not None
    
    def test_unique_file_id(self, test_db, sample_audio_file):
        """Test eindeutige File-ID."""
        with pytest.raises(Exception):  # Peewee IntegrityError
            AudioFile.create(
                file_id=sample_audio_file.file_id,  # Doppelte ID
                file_unique_id="different_unique",
                file_name="different.mp3",
                file_size=500000,
                mime_type="audio/mpeg"
            )


class TestDownloadStatus:
    """Tests für den DownloadStatus-Enum."""
    
    def test_status_values(self):
        """Test Status-Werte."""
        assert DownloadStatus.PENDING.value == "pending"
        assert DownloadStatus.DOWNLOADING.value == "downloading"
        assert DownloadStatus.COMPLETED.value == "completed"
        assert DownloadStatus.FAILED.value == "failed"
        assert DownloadStatus.SKIPPED.value == "skipped"
    
    def test_audio_file_with_status(self, test_db, sample_group):
        """Test AudioFile mit verschiedenen Status."""
        for status in DownloadStatus:
            audio_file = AudioFile.create(
                file_id=f"file_{status.value}",
                file_unique_id=f"unique_{status.value}",
                file_name=f"{status.value}.mp3",
                file_size=1000000,
                mime_type="audio/mpeg",
                status=status.value,
                group=sample_group
            )
            
            assert audio_file.status == status.value


class TestDatabaseQueries:
    """Tests für Datenbankabfragen."""
    
    def test_get_files_by_group(self, test_db, sample_group):
        """Test Dateien nach Gruppe abfragen."""
        # Mehrere Dateien für die Gruppe erstellen
        for i in range(3):
            AudioFile.create(
                file_id=f"file_{i}",
                file_unique_id=f"unique_{i}",
                file_name=f"song_{i}.mp3",
                file_size=1000000,
                mime_type="audio/mpeg",
                group=sample_group
            )
        
        files = AudioFile.select().where(AudioFile.group == sample_group)
        assert files.count() == 3
    
    def test_get_completed_files(self, test_db, sample_group):
        """Test nur abgeschlossene Dateien abfragen."""
        # Dateien mit verschiedenen Status erstellen
        AudioFile.create(
            file_id="completed_1",
            file_unique_id="unique_c1",
            file_name="completed1.mp3",
            file_size=1000000,
            mime_type="audio/mpeg",
            status=DownloadStatus.COMPLETED.value,
            group=sample_group
        )
        
        AudioFile.create(
            file_id="pending_1",
            file_unique_id="unique_p1",
            file_name="pending1.mp3",
            file_size=1000000,
            mime_type="audio/mpeg",
            status=DownloadStatus.PENDING.value,
            group=sample_group
        )
        
        completed_files = AudioFile.select().where(
            AudioFile.status == DownloadStatus.COMPLETED.value
        )
        assert completed_files.count() == 1
    
    def test_search_by_title(self, test_db, sample_group):
        """Test Suche nach Titel."""
        AudioFile.create(
            file_id="search_test",
            file_unique_id="unique_search",
            file_name="searchable.mp3",
            file_size=1000000,
            mime_type="audio/mpeg",
            title="Searchable Song",
            performer="Test Artist",
            group=sample_group
        )
        
        results = AudioFile.select().where(
            AudioFile.title.contains("Searchable")
        )
        assert results.count() == 1
        assert results[0].title == "Searchable Song"


class TestBaseModelFunctionality:
    """Tests für BaseModel-Funktionalität."""
    
    def test_created_at_auto_set(self, test_db):
        """Test automatisches Setzen von created_at."""
        group = TelegramGroup.create(
            group_id=999999,
            title="Timestamp Test"
        )
        
        assert group.created_at is not None
        assert isinstance(group.created_at, datetime)
    
    def test_updated_at_on_save(self, test_db, sample_audio_file):
        """Test Aktualisierung von updated_at beim Speichern."""
        original_updated = sample_audio_file.updated_at
        
        # Kurz warten und dann speichern
        import time
        time.sleep(0.01)
        
        sample_audio_file.title = "Updated Title"
        sample_audio_file.save()
        
        assert sample_audio_file.updated_at > original_updated


if __name__ == "__main__":
    pytest.main([__file__])