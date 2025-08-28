#!/usr/bin/env python3
"""
Metadatentests - Telegram Audio Downloader
========================================

Umfassende Tests für Audio-Metadaten-Extraktion und -Verarbeitung.
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from telegram_audio_downloader.downloader import AudioDownloader
from telegram_audio_downloader.utils import (
    sanitize_filename, 
    create_filename_from_metadata,
    extract_audio_metadata
)
from telegram_audio_downloader.models import AudioFile, DownloadStatus


class TestMetadataExtraction:
    """Tests für Metadaten-Extraktion."""
    
    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp(prefix="metadata_test_")
        self.download_dir = Path(self.temp_dir) / "downloads"
        self.download_dir.mkdir()
        
        yield
        
        # Cleanup
        import shutil
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def test_extract_metadata_from_document(self):
        """Test Extraktion von Metadaten aus einem Document."""
        # Erstelle ein Mock-Document mit Metadaten
        mock_document = Mock()
        mock_document.id = 12345
        mock_document.mime_type = "audio/mpeg"
        mock_document.size = 1048576  # 1MB
        
        # Erstelle Mock-Attribute
        mock_attrs = Mock()
        mock_attrs.title = "Test Song"
        mock_attrs.performer = "Test Artist"
        mock_attrs.duration = 180  # 3 Minuten
        
        # Mock die Attribute
        mock_document.attributes = [mock_attrs]
        
        # Erstelle einen Downloader und teste die Extraktion
        downloader = AudioDownloader(download_dir=str(self.download_dir))
        audio_info = downloader._extract_audio_info(mock_document)
        
        # Prüfe die extrahierten Informationen
        assert audio_info["file_id"] == "12345"
        assert audio_info["title"] == "Test Song"
        assert audio_info["performer"] == "Test Artist"
        assert audio_info["duration"] == 180
        assert audio_info["file_size"] == 1048576
        assert audio_info["mime_type"] == "audio/mpeg"
    
    def test_extract_metadata_missing_title(self):
        """Test Extraktion mit fehlendem Titel."""
        mock_document = Mock()
        mock_document.id = 67890
        mock_document.mime_type = "audio/flac"
        mock_document.size = 2097152  # 2MB
        
        # Erstelle Mock-Attribute ohne Titel
        mock_attrs = Mock()
        mock_attrs.title = None
        mock_attrs.performer = "Another Artist"
        mock_attrs.duration = 240
        
        mock_document.attributes = [mock_attrs]
        
        downloader = AudioDownloader(download_dir=str(self.download_dir))
        audio_info = downloader._extract_audio_info(mock_document)
        
        # Ohne Titel sollte ein generischer Name erstellt werden
        assert audio_info["file_id"] == "67890"
        assert audio_info["performer"] == "Another Artist"
        assert audio_info["duration"] == 240
    
    def test_extract_metadata_missing_performer(self):
        """Test Extraktion mit fehlendem Interpret."""
        mock_document = Mock()
        mock_document.id = 11111
        mock_document.mime_type = "audio/ogg"
        mock_document.size = 524288  # 0.5MB
        
        # Erstelle Mock-Attribute ohne Interpret
        mock_attrs = Mock()
        mock_attrs.title = "Solo Track"
        mock_attrs.performer = None
        mock_attrs.duration = 120
        
        mock_document.attributes = [mock_attrs]
        
        downloader = AudioDownloader(download_dir=str(self.download_dir))
        audio_info = downloader._extract_audio_info(mock_document)
        
        # Ohne Interpret sollte nur der Titel verwendet werden
        assert audio_info["title"] == "Solo Track"
        assert audio_info["performer"] is None
        assert audio_info["duration"] == 120
    
    def test_extract_metadata_no_attributes(self):
        """Test Extraktion ohne Attribute."""
        mock_document = Mock()
        mock_document.id = 22222
        mock_document.mime_type = "audio/wav"
        mock_document.size = 4194304  # 4MB
        mock_document.attributes = []  # Keine Attribute
        
        downloader = AudioDownloader(download_dir=str(self.download_dir))
        audio_info = downloader._extract_audio_info(mock_document)
        
        # Ohne Attribute sollten Standardwerte verwendet werden
        assert audio_info["file_id"] == "22222"
        assert audio_info["mime_type"] == "audio/wav"
        assert audio_info["file_size"] == 4194304


class TestMetadataFileNaming:
    """Tests für Dateibenennung basierend auf Metadaten."""
    
    def test_filename_with_artist_and_title(self):
        """Test Dateiname mit Künstler und Titel."""
        filename = create_filename_from_metadata(
            title="Bohemian Rhapsody",
            performer="Queen",
            file_id="12345",
            extension=".mp3"
        )
        assert filename == "Queen - Bohemian Rhapsody.mp3"
    
    def test_filename_with_title_only(self):
        """Test Dateiname nur mit Titel."""
        filename = create_filename_from_metadata(
            title="Stairway to Heaven",
            file_id="67890",
            extension=".flac"
        )
        assert filename == "Stairway to Heaven.flac"
    
    def test_filename_with_performer_only(self):
        """Test Dateiname nur mit Interpret."""
        filename = create_filename_from_metadata(
            performer="Led Zeppelin",
            file_id="11111",
            extension=".ogg"
        )
        # Wenn nur der Interpret vorhanden ist, sollte der Titel verwendet werden
        assert "Led Zeppelin" in filename
        assert filename.endswith(".ogg")
    
    def test_filename_without_metadata(self):
        """Test Dateiname ohne Metadaten."""
        filename = create_filename_from_metadata(
            file_id="22222",
            extension=".wav"
        )
        # Ohne Metadaten sollte ein generischer Name erstellt werden
        assert filename.startswith("audio_22222")
        assert filename.endswith(".wav")
    
    def test_filename_sanitization(self):
        """Test Sanitisierung von Dateinamen aus Metadaten."""
        filename = create_filename_from_metadata(
            title="Song with <>:\"|?* characters",
            performer="Artist / Band \\ Name",
            file_id="33333",
            extension=".mp3"
        )
        # Problematische Zeichen sollten entfernt oder ersetzt werden
        assert "<" not in filename
        assert ">" not in filename
        assert ":" not in filename
        assert "\"" not in filename
        assert "|" not in filename
        assert "?" not in filename
        assert "*" not in filename
        assert "/" not in filename
        assert "\\" not in filename


class TestMetadataEdgeCases:
    """Tests für Metadaten-Sonderfälle."""
    
    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp(prefix="metadata_edge_test_")
        self.download_dir = Path(self.temp_dir) / "downloads"
        self.download_dir.mkdir()
        
        yield
        
        # Cleanup
        import shutil
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def test_very_long_metadata(self):
        """Test sehr lange Metadaten."""
        # Erstelle sehr lange Titel und Interpret-Namen
        long_title = "Very Long Song Title " * 20  # 400+ Zeichen
        long_performer = "Extremely Long Artist Name " * 20  # 400+ Zeichen
        
        filename = create_filename_from_metadata(
            title=long_title,
            performer=long_performer,
            file_id="44444",
            extension=".mp3"
        )
        
        # Der Dateiname sollte eine angemessene Länge haben
        assert len(filename) <= 255  # Maximale Dateinamenlänge
        assert filename.endswith(".mp3")
    
    def test_unicode_metadata(self):
        """Test Unicode-Metadaten."""
        unicode_title = "Música Española"
        unicode_performer = "Björk Guðmundsdóttir"
        
        filename = create_filename_from_metadata(
            title=unicode_title,
            performer=unicode_performer,
            file_id="55555",
            extension=".flac"
        )
        
        # Unicode-Zeichen sollten erhalten bleiben
        assert unicode_title in filename or "Música" in filename
        assert unicode_performer in filename or "Björk" in filename
        assert filename.endswith(".flac")
    
    def test_special_characters_in_metadata(self):
        """Test Sonderzeichen in Metadaten."""
        special_title = "Song @ # $ % ^ & * ( ) + = { } [ ]"
        special_performer = "Artist ~ ` ! ? ; ' , . < >"
        
        filename = create_filename_from_metadata(
            title=special_title,
            performer=special_performer,
            file_id="66666",
            extension=".ogg"
        )
        
        # Die meisten Sonderzeichen sollten erhalten bleiben
        # (außer diejenigen, die für Dateisysteme problematisch sind)
        assert filename.endswith(".ogg")
    
    def test_empty_metadata_fields(self):
        """Test leere Metadaten-Felder."""
        filename = create_filename_from_metadata(
            title="",  # Leerer Titel
            performer="",  # Leer
            file_id="77777",
            extension=".wav"
        )
        
        # Leere Felder sollten nicht zu Fehlern führen
        assert filename is not None
        assert filename.endswith(".wav")
    
    def test_none_metadata_fields(self):
        """Test None-Metadaten-Felder."""
        filename = create_filename_from_metadata(
            title=None,
            performer=None,
            file_id="88888",
            extension=".mp3"
        )
        
        # None-Felder sollten nicht zu Fehlern führen
        assert filename is not None
        assert filename.endswith(".mp3")


class TestMetadataDatabaseStorage:
    """Tests für Speicherung von Metadaten in der Datenbank."""
    
    @pytest.fixture(autouse=True)
    def setup_test_database(self):
        """Setup test database."""
        self.temp_dir = tempfile.mkdtemp(prefix="metadata_db_test_")
        self.test_db_path = Path(self.temp_dir) / "test.db"
        os.environ["DB_PATH"] = str(self.test_db_path)
        
        # Initialisiere die Datenbank
        from telegram_audio_downloader.database import init_db, reset_db
        reset_db()
        init_db()
        
        yield
        
        # Cleanup
        import shutil
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def test_store_complete_metadata(self):
        """Test Speicherung vollständiger Metadaten."""
        # Erstelle eine Testgruppe
        from telegram_audio_downloader.models import TelegramGroup
        group = TelegramGroup.create(
            group_id=123456,
            title="Metadata Test Group"
        )
        
        # Erstelle eine Audiodatei mit vollständigen Metadaten
        audio_file = AudioFile.create(
            file_id="metadata_test_1",
            file_unique_id="unique_1",
            file_name="test.mp3",
            file_size=1048576,
            mime_type="audio/mpeg",
            duration=180,
            title="Complete Metadata Song",
            performer="Complete Metadata Artist",
            group=group,
            status=DownloadStatus.COMPLETED.value
        )
        
        # Prüfe, ob alle Metadaten gespeichert wurden
        assert audio_file.title == "Complete Metadata Song"
        assert audio_file.performer == "Complete Metadata Artist"
        assert audio_file.duration == 180
    
    def test_store_partial_metadata(self):
        """Test Speicherung teilweiser Metadaten."""
        from telegram_audio_downloader.models import TelegramGroup
        group = TelegramGroup.create(
            group_id=789012,
            title="Partial Metadata Test Group"
        )
        
        # Erstelle eine Audiodatei mit teilweisen Metadaten
        audio_file = AudioFile.create(
            file_id="metadata_test_2",
            file_unique_id="unique_2",
            file_name="partial.mp3",
            file_size=2097152,
            mime_type="audio/flac",
            title="Partial Metadata Song",
            # Kein Interpret
            duration=240,
            group=group,
            status=DownloadStatus.COMPLETED.value
        )
        
        # Prüfe die gespeicherten Werte
        assert audio_file.title == "Partial Metadata Song"
        assert audio_file.performer is None
        assert audio_file.duration == 240
    
    def test_store_unicode_metadata(self):
        """Test Speicherung von Unicode-Metadaten."""
        from telegram_audio_downloader.models import TelegramGroup
        group = TelegramGroup.create(
            group_id=345678,
            title="Unicode Metadata Test Group"
        )
        
        # Erstelle eine Audiodatei mit Unicode-Metadaten
        unicode_title = "Música Española"
        unicode_performer = "Björk Guðmundsdóttir"
        
        audio_file = AudioFile.create(
            file_id="metadata_test_3",
            file_unique_id="unique_3",
            file_name="unicode.mp3",
            file_size=3145728,
            mime_type="audio/ogg",
            duration=300,
            title=unicode_title,
            performer=unicode_performer,
            group=group,
            status=DownloadStatus.COMPLETED.value
        )
        
        # Prüfe, ob Unicode korrekt gespeichert wurde
        assert audio_file.title == unicode_title
        assert audio_file.performer == unicode_performer


class TestMetadataConsistency:
    """Tests für Metadaten-Konsistenz."""
    
    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp(prefix="metadata_consistency_test_")
        self.download_dir = Path(self.temp_dir) / "downloads"
        self.download_dir.mkdir()
        
        yield
        
        # Cleanup
        import shutil
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def test_metadata_consistency_across_functions(self):
        """Test Konsistenz von Metadaten zwischen Funktionen."""
        # Erstelle Test-Metadaten
        title = "Consistency Test Song"
        performer = "Consistency Test Artist"
        file_id = "99999"
        
        # Erstelle Dateiname aus Metadaten
        filename = create_filename_from_metadata(
            title=title,
            performer=performer,
            file_id=file_id,
            extension=".mp3"
        )
        
        # Prüfe, ob der Dateiname die Metadaten enthält
        assert title in filename
        assert performer in filename
        assert filename.endswith(".mp3")
    
    def test_metadata_extraction_consistency(self):
        """Test Konsistenz der Metadaten-Extraktion."""
        # Erstelle ein Mock-Document
        mock_document = Mock()
        mock_document.id = 12345
        mock_document.mime_type = "audio/mpeg"
        mock_document.size = 1048576
        
        mock_attrs = Mock()
        mock_attrs.title = "Extraction Test Song"
        mock_attrs.performer = "Extraction Test Artist"
        mock_attrs.duration = 180
        
        mock_document.attributes = [mock_attrs]
        
        # Extrahiere Metadaten
        downloader = AudioDownloader(download_dir=str(self.download_dir))
        audio_info = downloader._extract_audio_info(mock_document)
        
        # Erstelle Dateiname aus den extrahierten Metadaten
        filename = create_filename_from_metadata(
            title=audio_info.get("title"),
            performer=audio_info.get("performer"),
            file_id=audio_info.get("file_id"),
            extension=Path(audio_info.get("file_name", "")).suffix or ".mp3"
        )
        
        # Prüfe Konsistenz
        assert "Extraction Test Song" in filename
        assert "Extraction Test Artist" in filename
        assert "12345" in filename


if __name__ == "__main__":
    pytest.main([__file__, "-v"])