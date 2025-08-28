#!/usr/bin/env python3
"""
Integration Tests - Telegram Audio Downloader
============================================

Tests für die Interaktion zwischen Downloader und Datenbank.
"""

import os
import sys
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from telegram_audio_downloader.downloader import AudioDownloader, LRUCache
from telegram_audio_downloader.database import init_db, reset_db
from telegram_audio_downloader.models import AudioFile, DownloadStatus, TelegramGroup


class TestIntegration:
    """Integrationstests für den kompletten Download-Workflow."""
    
    @pytest.fixture(autouse=True)
    async def setup_test_environment(self):
        """Setup test environment."""
        # Create temporary directory
        self.temp_dir = tempfile.mkdtemp(prefix="integration_test_")
        self.download_dir = Path(self.temp_dir) / "downloads"
        self.download_dir.mkdir()
        
        # Setup test database
        self.test_db_path = Path(self.temp_dir) / "test.db"
        os.environ["DB_PATH"] = str(self.test_db_path)
        
        # Reset database
        reset_db()
        
        # Setup mock data
        self._setup_mock_data()
        
        yield
        
        # Cleanup
        import shutil
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def _setup_mock_data(self):
        """Setup mock data for testing."""
        self.mock_messages = []
        for i in range(5):
            mock_msg = Mock()
            mock_msg.id = i + 1
            mock_msg.date = "2024-01-20T10:00:00Z"
            mock_msg.text = f"Test Audio File {i+1}"
            
            mock_audio = Mock()
            mock_audio.file_id = f"test_file_id_{i}"
            mock_audio.duration = 180
            mock_audio.title = f"Test Song {i+1}"
            mock_audio.performer = "Test Artist"
            mock_audio.file_size = 5242880
            
            mock_msg.audio = mock_audio
            self.mock_messages.append(mock_msg)
    
    @pytest.mark.asyncio
    async def test_complete_download_workflow(self):
        """Test kompletter Download-Workflow von der Telegram-API bis zur gespeicherten Datei."""
        # Initialize downloader
        downloader = AudioDownloader(
            download_dir=str(self.download_dir),
            max_concurrent_downloads=2
        )
        
        # Mock Telegram client
        mock_client = AsyncMock()
        mock_client.get_entity.return_value = Mock(
            id=-1001234567890,
            title="Test Music Group",
            username="test_music_group"
        )
        mock_client.iter_messages.return_value = self.mock_messages
        
        # Mock file download
        test_file_content = b"ID3\x03\x00\x00\x00" + b"\x00" * 1000
        mock_client.download_media.return_value = test_file_content
        
        with patch('telegram_audio_downloader.downloader.TelegramClient') as mock_client_class:
            mock_client_class.return_value = mock_client
            
            # Initialize client
            await downloader.initialize_client()
            
            # Perform download
            result = await downloader.download_audio_files(
                group_name="@test_music_group",
                limit=5
            )
            
            # Verify results
            assert result["completed"] == 5
            assert result["failed"] == 0
            assert result["total_size"] > 0
            
            # Verify database records
            downloaded_files = AudioFile.select().where(
                AudioFile.status == DownloadStatus.COMPLETED.value
            )
            assert len(list(downloaded_files)) == 5
            
            # Verify files were created
            downloaded_files = list(self.download_dir.glob("*.mp3"))
            assert len(downloaded_files) == 5
    
    @pytest.mark.asyncio
    async def test_database_interactions_during_download(self):
        """Test Datenbankinteraktionen während des Downloads."""
        # Initialize downloader
        downloader = AudioDownloader(download_dir=str(self.download_dir))
        
        # Mock Telegram client
        mock_client = AsyncMock()
        mock_client.get_entity.return_value = Mock(
            id=-1001234567890,
            title="Test Music Group",
            username="test_music_group"
        )
        mock_client.iter_messages.return_value = [self.mock_messages[0]]
        
        # Mock file download
        test_file_content = b"ID3\x03\x00\x00\x00" + b"\x00" * 1000
        mock_client.download_media.return_value = test_file_content
        
        with patch('telegram_audio_downloader.downloader.TelegramClient') as mock_client_class:
            mock_client_class.return_value = mock_client
            
            # Initialize client
            await downloader.initialize_client()
            
            # Check initial database state
            initial_count = AudioFile.select().count()
            assert initial_count == 0
            
            # Perform download
            await downloader.download_audio_files(
                group_name="@test_music_group",
                limit=1
            )
            
            # Check database state after download
            final_count = AudioFile.select().count()
            assert final_count == 1
            
            # Verify record details
            record = AudioFile.get()
            assert record.file_id == "test_file_id_0"
            assert record.status == DownloadStatus.COMPLETED.value
            assert record.group_id == -1001234567890
    
    @pytest.mark.asyncio
    async def test_cross_component_error_handling(self):
        """Test Fehlerbehandlung über Komponentengrenzen hinweg."""
        # Initialize downloader
        downloader = AudioDownloader(download_dir=str(self.download_dir))
        
        # Test network error during client initialization
        with patch('telegram_audio_downloader.downloader.TelegramClient') as mock_client_class:
            mock_client_class.side_effect = ConnectionError("Network failure")
            
            with pytest.raises(ConnectionError):
                await downloader.initialize_client()
        
        # Test database error during download
        with patch('telegram_audio_downloader.downloader.TelegramClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get_entity.return_value = Mock(
                id=-1001234567890,
                title="Test Music Group",
                username="test_music_group"
            )
            mock_client.iter_messages.return_value = [self.mock_messages[0]]
            mock_client_class.return_value = mock_client
            
            # Mock database error
            with patch('telegram_audio_downloader.models.AudioFile.create') as mock_create:
                mock_create.side_effect = Exception("Database error")
                
                await downloader.initialize_client()
                
                # Perform download - should handle error gracefully
                result = await downloader.download_audio_files(
                    group_name="@test_music_group",
                    limit=1
                )
                
                # Verify error was handled
                assert result["completed"] == 0
                assert result["failed"] == 1
    
    @pytest.mark.asyncio
    async def test_lru_cache_integration(self):
        """Test Integration des LRU-Caches mit der Datenbank."""
        # Initialize downloader
        downloader = AudioDownloader(download_dir=str(self.download_dir))
        
        # Load downloaded files into cache
        downloader._load_downloaded_files()
        
        # Initially cache should be empty
        assert len(downloader._downloaded_files_cache) == 0
        
        # Add a record to database
        AudioFile.create(
            file_id="cached_file_123",
            group_id=-1001234567890,
            message_id=1,
            file_name="cached_file.mp3",
            file_size=1024,
            status=DownloadStatus.COMPLETED.value
        )
        
        # Reload cache
        downloader._load_downloaded_files()
        
        # Cache should now contain the file
        assert len(downloader._downloaded_files_cache) == 1
        assert "cached_file_123" in downloader._downloaded_files_cache
        
        # Test cache lookup
        assert downloader._downloaded_files_cache.get("cached_file_123") is True
        assert downloader._downloaded_files_cache.get("nonexistent_file") is None

    @pytest.mark.asyncio
    async def test_concurrent_database_access(self):
        """Test gleichzeitiger Datenbankzugriff während paralleler Downloads."""
        # Initialize downloader with higher concurrency
        downloader = AudioDownloader(
            download_dir=str(self.download_dir),
            max_concurrent_downloads=3
        )
        
        # Mock Telegram client with multiple messages
        mock_client = AsyncMock()
        mock_client.get_entity.return_value = Mock(
            id=-1001234567890,
            title="Test Music Group",
            username="test_music_group"
        )
        mock_client.iter_messages.return_value = self.mock_messages[:3]
        
        # Mock file download
        test_file_content = b"ID3\x03\x00\x00\x00" + b"\x00" * 1000
        mock_client.download_media.return_value = test_file_content
        
        with patch('telegram_audio_downloader.downloader.TelegramClient') as mock_client_class:
            mock_client_class.return_value = mock_client
            
            # Initialize client
            await downloader.initialize_client()
            
            # Perform concurrent downloads
            await downloader.download_audio_files(
                group_name="@test_music_group",
                limit=3
            )
            
            # Verify database records
            downloaded_files = AudioFile.select().where(
                AudioFile.status == DownloadStatus.COMPLETED.value
            )
            assert len(list(downloaded_files)) == 3
            
            # Verify all files have the same group
            for file_record in downloaded_files:
                assert file_record.group_id == -1001234567890

    @pytest.mark.asyncio
    async def test_database_transaction_behavior(self):
        """Test Transaktionsverhalten der Datenbank."""
        # Initialize downloader
        downloader = AudioDownloader(download_dir=str(self.download_dir))
        
        # Mock Telegram client
        mock_client = AsyncMock()
        mock_client.get_entity.return_value = Mock(
            id=-1001234567890,
            title="Test Music Group",
            username="test_music_group"
        )
        
        # Mock file download with error on second file
        test_file_content = b"ID3\x03\x00\x00\x00" + b"\x00" * 1000
        
        with patch('telegram_audio_downloader.downloader.TelegramClient') as mock_client_class:
            mock_client_class.return_value = mock_client
            
            # Initialize client
            await downloader.initialize_client()
            
            # Test successful transaction
            mock_client.iter_messages.return_value = [self.mock_messages[0]]
            mock_client.download_media.return_value = test_file_content
            
            await downloader.download_audio_files(
                group_name="@test_music_group",
                limit=1
            )
            
            # Verify successful transaction
            success_count = AudioFile.select().where(
                AudioFile.status == DownloadStatus.COMPLETED.value
            ).count()
            assert success_count == 1
            
            # Test failed transaction
            mock_client.iter_messages.return_value = [self.mock_messages[1]]
            mock_client.download_media.side_effect = Exception("Download failed")
            
            await downloader.download_audio_files(
                group_name="@test_music_group",
                limit=1
            )
            
            # Verify failed transaction is recorded
            failed_count = AudioFile.select().where(
                AudioFile.status == DownloadStatus.FAILED.value
            ).count()
            assert failed_count == 1

    @pytest.mark.asyncio
    async def test_cache_consistency_with_database(self):
        """Test Konsistenz zwischen Cache und Datenbank."""
        # Initialize downloader
        downloader = AudioDownloader(download_dir=str(self.download_dir))
        
        # Add records to database
        for i in range(3):
            AudioFile.create(
                file_id=f"file_{i}",
                group_id=-1001234567890,
                message_id=i+1,
                file_name=f"file_{i}.mp3",
                file_size=1024,
                status=DownloadStatus.COMPLETED.value
            )
        
        # Reload cache
        downloader._load_downloaded_files()
        
        # Verify cache consistency
        assert len(downloader._downloaded_files_cache) == 3
        for i in range(3):
            assert f"file_{i}" in downloader._downloaded_files_cache
        
        # Add new record to database
        AudioFile.create(
            file_id="new_file",
            group_id=-1001234567890,
            message_id=4,
            file_name="new_file.mp3",
            file_size=2048,
            status=DownloadStatus.COMPLETED.value
        )
        
        # Reload cache and verify new record
        downloader._load_downloaded_files()
        assert len(downloader._downloaded_files_cache) == 4
        assert "new_file" in downloader._downloaded_files_cache

    @pytest.mark.asyncio
    async def test_download_resume_integration(self):
        """Test Integration von Download-Wiederaufnahme mit Datenbank."""
        # Initialize downloader
        downloader = AudioDownloader(download_dir=str(self.download_dir))
        
        # Mock Telegram client
        mock_client = AsyncMock()
        mock_client.get_entity.return_value = Mock(
            id=-1001234567890,
            title="Test Music Group",
            username="test_music_group"
        )
        mock_client.iter_messages.return_value = [self.mock_messages[0]]
        
        # Create partial download record
        partial_file_path = str(self.download_dir / "partial_test.mp3.partial")
        with open(partial_file_path, "wb") as f:
            f.write(b"partial_content")
        
        # Add partial record to database
        AudioFile.create(
            file_id="test_file_id_0",
            group_id=-1001234567890,
            message_id=1,
            file_name="test_file.mp3",
            file_size=2048,
            status=DownloadStatus.FAILED.value,
            partial_file_path=partial_file_path,
            downloaded_bytes=1024
        )
        
        # Mock file download to complete the partial download
        test_file_content = b"ID3\x03\x00\x00\x00" + b"\x00" * 1000
        mock_client.download_media.return_value = test_file_content
        
        with patch('telegram_audio_downloader.downloader.TelegramClient') as mock_client_class:
            mock_client_class.return_value = mock_client
            
            # Initialize client
            await downloader.initialize_client()
            
            # Perform download - should resume partial download
            await downloader.download_audio_files(
                group_name="@test_music_group",
                limit=1
            )
            
            # Verify download was completed
            completed_file = AudioFile.get(AudioFile.file_id == "test_file_id_0")
            assert completed_file.status == DownloadStatus.COMPLETED.value
            assert completed_file.downloaded_bytes == 2048


if __name__ == "__main__":
    pytest.main([__file__, "-v"])