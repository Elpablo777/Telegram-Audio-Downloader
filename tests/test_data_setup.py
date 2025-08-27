#!/usr/bin/env python3
"""
Test Data Setup - Telegram Audio Downloader
==========================================

Umfassendes Testdaten-Setup für verschiedene Szenarien.
"""

import os
import sys
import tempfile
from pathlib import Path
from typing import List, Dict, Any
from unittest.mock import Mock
import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from telegram_audio_downloader.models import AudioFile, DownloadStatus, TelegramGroup


class TestDataManager:
    """Manager für Testdaten."""

    def __init__(self):
        self.temp_dir = None
        self.test_data = {}
    
    def setup_test_environment(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp(prefix="test_data_")
        return self.temp_dir
    
    def create_realistic_telegram_messages(self) -> List[Mock]:
        """Erstellt realistischere Telegram-Nachrichten-Mocks."""
        messages = []
        
        # Verschiedene Nachrichtentypen
        message_templates = [
            {
                "id": 1,
                "date": "2024-01-20T10:00:00Z",
                "text": "🎵 New song uploaded!",
                "audio": {
                    "file_id": "audio_001",
                    "duration": 240,  # 4 Minuten
                    "title": "Bohemian Rhapsody",
                    "performer": "Queen",
                    "file_size": 10485760,  # 10MB
                    "mime_type": "audio/mpeg"
                }
            },
            {
                "id": 2,
                "date": "2024-01-20T11:00:00Z",
                "text": "Classical music collection",
                "audio": {
                    "file_id": "audio_002",
                    "duration": 1800,  # 30 Minuten
                    "title": "Symphony No. 9",
                    "performer": "Beethoven",
                    "file_size": 52428800,  # 50MB
                    "mime_type": "audio/flac"
                }
            },
            {
                "id": 3,
                "date": "2024-01-20T12:00:00Z",
                "text": "Podcast episode",
                "audio": {
                    "file_id": "audio_003",
                    "duration": 3600,  # 1 Stunde
                    "title": "Tech Talk Episode 42",
                    "performer": "Tech Podcast Network",
                    "file_size": 62914560,  # 60MB
                    "mime_type": "audio/mp3"
                }
            },
            {
                "id": 4,
                "date": "2024-01-20T13:00:00Z",
                "text": "Short clip",
                "audio": {
                    "file_id": "audio_004",
                    "duration": 30,  # 30 Sekunden
                    "title": "Intro",
                    "performer": "Various Artists",
                    "file_size": 524288,  # 0.5MB
                    "mime_type": "audio/ogg"
                }
            },
            {
                "id": 5,
                "date": "2024-01-20T14:00:00Z",
                "text": "Large file",
                "audio": {
                    "file_id": "audio_005",
                    "duration": 7200,  # 2 Stunden
                    "title": "Live Concert Recording",
                    "performer": "Symphony Orchestra",
                    "file_size": 209715200,  # 200MB
                    "mime_type": "audio/wav"
                }
            }
        ]
        
        for template in message_templates:
            mock_msg = Mock()
            mock_msg.id = template["id"]
            mock_msg.date = template["date"]
            mock_msg.text = template["text"]
            
            mock_audio = Mock()
            audio_data = template["audio"]
            mock_audio.file_id = audio_data["file_id"]
            mock_audio.duration = audio_data["duration"]
            mock_audio.title = audio_data["title"]
            mock_audio.performer = audio_data["performer"]
            mock_audio.file_size = audio_data["file_size"]
            mock_audio.mime_type = audio_data["mime_type"]
            
            mock_msg.audio = mock_audio
            messages.append(mock_msg)
        
        return messages
    
    def create_audio_files_with_various_formats(self) -> List[Dict[str, Any]]:
        """Erstellt verschiedene Audioformate und -größen."""
        audio_files = [
            {
                "file_id": "mp3_small",
                "file_name": "small.mp3",
                "file_size": 1048576,  # 1MB
                "mime_type": "audio/mpeg",
                "duration": 60,
                "title": "Small MP3",
                "performer": "Test Artist"
            },
            {
                "file_id": "flac_medium",
                "file_name": "medium.flac",
                "file_size": 10485760,  # 10MB
                "mime_type": "audio/flac",
                "duration": 300,
                "title": "Medium FLAC",
                "performer": "Test Artist"
            },
            {
                "file_id": "wav_large",
                "file_name": "large.wav",
                "file_size": 104857600,  # 100MB
                "mime_type": "audio/wav",
                "duration": 1800,
                "title": "Large WAV",
                "performer": "Test Artist"
            },
            {
                "file_id": "ogg_small",
                "file_name": "small.ogg",
                "file_size": 2097152,  # 2MB
                "mime_type": "audio/ogg",
                "duration": 120,
                "title": "Small OGG",
                "performer": "Test Artist"
            },
            {
                "file_id": "m4a_medium",
                "file_name": "medium.m4a",
                "file_size": 5242880,  # 5MB
                "mime_type": "audio/mp4",
                "duration": 240,
                "title": "Medium M4A",
                "performer": "Test Artist"
            }
        ]
        return audio_files
    
    def create_inconsistent_metadata_files(self) -> List[Dict[str, Any]]:
        """Erstellt Dateien mit fehlerhaften/inkonsistenten Metadaten."""
        audio_files = [
            {
                "file_id": "no_title",
                "file_name": "no_title.mp3",
                "file_size": 1048576,
                "mime_type": "audio/mpeg",
                "duration": 180,
                "title": None,  # Fehlender Titel
                "performer": "Test Artist"
            },
            {
                "file_id": "no_performer",
                "file_name": "no_performer.mp3",
                "file_size": 1048576,
                "mime_type": "audio/mpeg",
                "duration": 180,
                "title": "Test Song",
                "performer": None  # Fehlender Interpret
            },
            {
                "file_id": "no_duration",
                "file_name": "no_duration.mp3",
                "file_size": 1048576,
                "mime_type": "audio/mpeg",
                "duration": None,  # Fehlende Dauer
                "title": "Test Song",
                "performer": "Test Artist"
            },
            {
                "file_id": "zero_size",
                "file_name": "zero_size.mp3",
                "file_size": 0,  # Null Größe
                "mime_type": "audio/mpeg",
                "duration": 180,
                "title": "Test Song",
                "performer": "Test Artist"
            },
            {
                "file_id": "negative_duration",
                "file_name": "negative_duration.mp3",
                "file_size": 1048576,
                "mime_type": "audio/mpeg",
                "duration": -10,  # Negative Dauer
                "title": "Test Song",
                "performer": "Test Artist"
            }
        ]
        return audio_files
    
    def create_boundary_test_files(self) -> List[Dict[str, Any]]:
        """Erstellt Dateien mit Grenzwerten für Dateigrößen und -namen."""
        audio_files = [
            {
                "file_id": "very_long_filename_" + "x" * 200,  # Sehr langer Dateiname
                "file_name": "very_long_filename_" + "x" * 200 + ".mp3",
                "file_size": 1048576,
                "mime_type": "audio/mpeg",
                "duration": 180,
                "title": "Long Filename Test",
                "performer": "Test Artist"
            },
            {
                "file_id": "zero_byte_file",
                "file_name": "zero.mp3",
                "file_size": 0,  # Null Byte Datei
                "mime_type": "audio/mpeg",
                "duration": 0,
                "title": "Zero Byte File",
                "performer": "Test Artist"
            },
            {
                "file_id": "max_size_file",
                "file_name": "max.mp3",
                "file_size": 4294967296,  # 4GB (Maximale Dateigröße)
                "mime_type": "audio/mpeg",
                "duration": 14400,  # 4 Stunden
                "title": "Max Size File",
                "performer": "Test Artist"
            },
            {
                "file_id": "special_chars_filename",
                "file_name": "special_äöü_ñ_文件.mp3",  # Unicode-Zeichen im Dateinamen
                "file_size": 1048576,
                "mime_type": "audio/mpeg",
                "duration": 180,
                "title": "Special Characters",
                "performer": "Test Artist"
            }
        ]
        return audio_files


class TestTestDataSetup:
    """Tests für das Testdaten-Setup."""
    
    @pytest.fixture(autouse=True)
    def setup_test_data_manager(self):
        """Setup TestDataManager."""
        self.data_manager = TestDataManager()
        self.temp_dir = self.data_manager.setup_test_environment()
        yield
        import shutil
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def test_realistic_telegram_messages(self):
        """Test erstellt realistischere Telegram-Nachrichten-Mocks."""
        messages = self.data_manager.create_realistic_telegram_messages()
        assert len(messages) == 5
        
        # Überprüfe verschiedene Audioformate
        mime_types = [msg.audio.mime_type for msg in messages]
        expected_types = ["audio/mpeg", "audio/flac", "audio/mp3", "audio/ogg", "audio/wav"]
        assert set(mime_types) == set(expected_types)
        
        # Überprüfe verschiedene Dateigrößen
        file_sizes = [msg.audio.file_size for msg in messages]
        assert len(set(file_sizes)) == 5  # Alle Größen sind unterschiedlich
        
        # Überprüfe verschiedene Dauerwerte
        durations = [msg.audio.duration for msg in messages]
        assert min(durations) == 30  # 30 Sekunden
        assert max(durations) == 7200  # 2 Stunden
    
    def test_various_audio_formats(self):
        """Test verschiedene Audioformate und -größen."""
        audio_files = self.data_manager.create_audio_files_with_various_formats()
        assert len(audio_files) == 5
        
        # Überprüfe Formate
        formats = [af["mime_type"] for af in audio_files]
        expected_formats = ["audio/mpeg", "audio/flac", "audio/wav", "audio/ogg", "audio/mp4"]
        assert set(formats) == set(expected_formats)
        
        # Überprüfe Größen
        sizes = [af["file_size"] for af in audio_files]
        assert sorted(sizes) == [1048576, 2097152, 5242880, 10485760, 104857600]
    
    def test_inconsistent_metadata(self):
        """Test fehlerhafte/inkonsistente Metadaten."""
        audio_files = self.data_manager.create_inconsistent_metadata_files()
        assert len(audio_files) == 5
        
        # Überprüfe fehlende Titel
        no_title_file = next(af for af in audio_files if af["file_id"] == "no_title")
        assert no_title_file["title"] is None
        assert no_title_file["performer"] is not None
        
        # Überprüfe fehlende Interpret
        no_performer_file = next(af for af in audio_files if af["file_id"] == "no_performer")
        assert no_performer_file["title"] is not None
        assert no_performer_file["performer"] is None
        
        # Überprüfe fehlende Dauer
        no_duration_file = next(af for af in audio_files if af["file_id"] == "no_duration")
        assert no_duration_file["duration"] is None
        
        # Überprüfe Null-Größe
        zero_size_file = next(af for af in audio_files if af["file_id"] == "zero_size")
        assert zero_size_file["file_size"] == 0
        
        # Überprüfe negative Dauer
        negative_duration_file = next(af for af in audio_files if af["file_id"] == "negative_duration")
        assert negative_duration_file["duration"] < 0
    
    def test_boundary_values(self):
        """Test Grenzwerte für Dateigrößen und -namen."""
        audio_files = self.data_manager.create_boundary_test_files()
        assert len(audio_files) == 4
        
        # Überprüfe sehr langen Dateinamen
        long_filename_file = next(af for af in audio_files if "very_long_filename" in af["file_id"])
        assert len(long_filename_file["file_name"]) > 200
        
        # Überprüfe Null-Byte-Datei
        zero_byte_file = next(af for af in audio_files if af["file_id"] == "zero_byte_file")
        assert zero_byte_file["file_size"] == 0
        
        # Überprüfe maximale Dateigröße
        max_size_file = next(af for af in audio_files if af["file_id"] == "max_size_file")
        assert max_size_file["file_size"] == 4294967296  # 4GB
        
        # Überprüfe Unicode-Zeichen im Dateinamen
        special_chars_file = next(af for af in audio_files if af["file_id"] == "special_chars_filename")
        assert "äöü" in special_chars_file["file_name"] or "ñ" in special_chars_file["file_name"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])