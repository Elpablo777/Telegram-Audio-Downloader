#!/usr/bin/env python3
"""
Basic Download Test - Telegram Audio Downloader
=============================================

Grundlegender Test für die Download-Funktionalität.
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from telegram_audio_downloader.downloader import AudioDownloader
from telegram_audio_downloader.models import AudioFile, DownloadStatus, TelegramGroup


class AsyncIterator:
    """Hilfsklasse für async iterators."""
    def __init__(self, items):
        self.items = items

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.items:
            return self.items.pop(0)
        raise StopAsyncIteration


class TestBasicDownload:
    """Grundlegende Download-Tests."""
    
    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp(prefix="basic_download_test_")
        self.download_dir = Path(self.temp_dir) / "downloads"
        self.download_dir.mkdir()
        
        # Setup test database
        self.test_db_path = Path(self.temp_dir) / "test.db"
        os.environ["DB_PATH"] = str(self.test_db_path)
        
        # Setup API credentials
        os.environ["API_ID"] = "123456"
        os.environ["API_HASH"] = "test_api_hash"
        os.environ["SESSION_NAME"] = "test_session"
        
        yield
        
        # Cleanup environment variables
        if "API_ID" in os.environ:
            del os.environ["API_ID"]
        if "API_HASH" in os.environ:
            del os.environ["API_HASH"]
        if "SESSION_NAME" in os.environ:
            del os.environ["SESSION_NAME"]
        
        # Cleanup
        import shutil
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def create_mock_message(self, file_id="test_file_id", title="Test Song", performer="Test Artist"):
        """Erstellt eine Mock-Nachricht."""
        mock_message = Mock()
        mock_message.id = 1
        mock_message.date = "2024-01-20T10:00:00Z"
        mock_message.text = "Test Audio File"
        
        mock_audio = Mock()
        mock_audio.file_id = file_id
        mock_audio.duration = 180
        mock_audio.title = title
        mock_audio.performer = performer
        mock_audio.file_size = 5242880  # 5MB
        
        mock_message.audio = mock_audio
        return mock_message
    
    @pytest.mark.asyncio
    async def test_basic_download_workflow(self):
        """Test des grundlegenden Download-Workflows."""
        # Initialize downloader
        downloader = AudioDownloader(download_dir=str(self.download_dir))
        
        # Create mock message
        mock_message = self.create_mock_message()
        
        # Mock Telegram client
        mock_client = AsyncMock()
        mock_entity = Mock()
        mock_entity.id = -1001234567890
        mock_entity.title = "Test Music Group"
        mock_entity.username = "test_music_group"
        mock_client.get_entity.return_value = mock_entity
        mock_client.iter_messages.return_value = AsyncIterator([mock_message])
        
        # Mock file download
        test_file_content = b"ID3\x03\x00\x00\x00" + b"\x00" * 5242870  # 5MB
        mock_client.download_media.return_value = test_file_content
        
        with patch('telegram_audio_downloader.downloader.TelegramClient') as mock_client_class:
            mock_client_class.return_value = mock_client
            
            # Initialize client
            await downloader.initialize_client()
            
            # Perform download
            await downloader.download_audio_files(
                group_name="@test_music_group",
                limit=1
            )
            
            # Verify database record was created
            audio_files = list(AudioFile.select())
            assert len(audio_files) == 1
            
            audio_file = audio_files[0]
            assert audio_file.file_id == "test_file_id"
            assert audio_file.status == DownloadStatus.COMPLETED.value
            assert audio_file.file_size == 5242880
            
            # Verify file was downloaded
            downloaded_files = list(self.download_dir.glob("*.mp3"))
            assert len(downloaded_files) == 1
            
            # Verify file content
            downloaded_file = downloaded_files[0]
            assert downloaded_file.exists()
            assert downloaded_file.stat().st_size == 5242880
    
    @pytest.mark.asyncio
    async def test_download_with_existing_file(self):
        """Test Download mit bereits existierender Datei."""
        # Initialize downloader
        downloader = AudioDownloader(download_dir=str(self.download_dir))
        
        # Create a Telegram group with get_or_create to avoid UNIQUE constraint
        test_group, created = TelegramGroup.get_or_create(
            group_id=-1001234567891,  # Different group ID to avoid conflict
            defaults={
                "title": "Test Music Group 2",
                "username": "test_music_group_2"
            }
        )
        
        # Create an existing record in the database with get_or_create
        existing_file, created = AudioFile.get_or_create(
            file_id="existing_file_id",
            defaults={
                "group": test_group,
                "message_id": 1,
                "file_name": "existing_file.mp3",
                "file_size": 1024,
                "mime_type": "audio/mpeg",
                "status": DownloadStatus.COMPLETED.value
            }
        )
        
        # Create mock message with the same file ID
        mock_message = self.create_mock_message(file_id="existing_file_id")
        
        # Mock Telegram client
        mock_client = AsyncMock()
        mock_entity = Mock()
        mock_entity.id = -1001234567891  # Different group ID
        mock_entity.title = "Test Music Group 2"
        mock_entity.username = "test_music_group_2"
        mock_client.get_entity.return_value = mock_entity
        mock_client.iter_messages.return_value = AsyncIterator([mock_message])
        
        with patch('telegram_audio_downloader.downloader.TelegramClient') as mock_client_class:
            mock_client_class.return_value = mock_client
            
            # Initialize client
            await downloader.initialize_client()
            
            # Perform download - should skip existing file
            await downloader.download_audio_files(
                group_name="@test_music_group_2",
                limit=1
            )
            
            # Verify no new files were downloaded
            downloaded_files = list(self.download_dir.glob("*.mp3"))
            assert len(downloaded_files) == 0  # No new files should be downloaded
            
            # Verify database still has only one record
            audio_files = list(AudioFile.select())
            assert len(audio_files) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])