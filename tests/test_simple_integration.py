#!/usr/bin/env python3
"""
Simple Integration Test - Telegram Audio Downloader
=================================================

Einfacher Integrationstest für die Telegram-Downloader-Komponenten.
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


class TestSimpleIntegration:
    """Einfache Integrationstests."""
    
    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp(prefix="simple_integration_test_")
        self.download_dir = Path(self.temp_dir) / "downloads"
        self.download_dir.mkdir()
        
        # Setup test database
        self.test_db_path = Path(self.temp_dir) / "test.db"
        os.environ["DB_PATH"] = str(self.test_db_path)
        
        yield
        
        # Cleanup
        import shutil
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def test_downloader_initialization(self):
        """Test der Downloader-Initialisierung."""
        # Initialize downloader
        downloader = AudioDownloader(download_dir=str(self.download_dir))
        
        # Verify downloader was initialized correctly
        assert downloader.download_dir == self.download_dir
        assert downloader.download_dir.exists()
        assert downloader.max_concurrent_downloads == 3  # Default value
    
    def test_database_integration(self):
        """Test der Datenbank-Integration."""
        # Initialize downloader (this will initialize the database)
        downloader = AudioDownloader(download_dir=str(self.download_dir))
        
        # Create a Telegram group first
        test_group = TelegramGroup.create(
            group_id=-1001234567890,
            title="Test Music Group",
            username="test_music_group"
        )
        
        # Create a test record with all required fields
        test_record = AudioFile.create(
            file_id="test_file_123",
            group=test_group,
            message_id=1,
            file_name="test.mp3",
            file_size=1024,
            mime_type="audio/mpeg",
            status=DownloadStatus.COMPLETED.value
        )
        
        # Verify record was created
        assert test_record.id is not None
        assert test_record.file_id == "test_file_123"
        
        # Verify we can retrieve the record
        retrieved_record = AudioFile.get(AudioFile.file_id == "test_file_123")
        assert retrieved_record.file_id == "test_file_123"
        assert retrieved_record.status == DownloadStatus.COMPLETED.value
        assert retrieved_record.mime_type == "audio/mpeg"
        assert retrieved_record.group.id == test_group.id


if __name__ == "__main__":
    pytest.main([__file__, "-v"])