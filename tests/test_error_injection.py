#!/usr/bin/env python3
"""
Error Injection Tests - Telegram Audio Downloader
================================================

Tests für Fehlerfälle mit gezielter Fehlerinjektion.
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

from telegram_audio_downloader.downloader import AudioDownloader
from telegram_audio_downloader.models import AudioFile, DownloadStatus


class ErrorInjector:
    """Klasse zur Injektion von Fehlern für Tests."""
    
    @staticmethod
    def inject_network_error():
        """Injiziert einen Netzwerkfehler."""
        return ConnectionError("Network connection failed")
    
    @staticmethod
    def inject_disk_full_error():
        """Injiziert einen Fehler wegen vollem Festplattenspeicher."""
        return OSError("No space left on device")
    
    @staticmethod
    def inject_invalid_api_response():
        """Injiziert eine ungültige API-Antwort."""
        return ValueError("Invalid API response format")
    
    @staticmethod
    def inject_timeout_error():
        """Injiziert einen Timeout-Fehler."""
        return asyncio.TimeoutError("Request timed out")


class TestErrorInjection:
    """Tests für Fehlerinjektion."""
    
    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp(prefix="error_test_")
        self.download_dir = Path(self.temp_dir) / "downloads"
        self.download_dir.mkdir()
        
        # Setup test database
        test_db_path = Path(self.temp_dir) / "test.db"
        os.environ["DB_PATH"] = str(test_db_path)
        
        # Create test message
        self.mock_message = Mock()
        self.mock_message.id = 1
        self.mock_message.date = "2024-01-20T10:00:00Z"
        self.mock_message.text = "Test Audio File"
        
        mock_audio = Mock()
        mock_audio.file_id = "test_file_id"
        mock_audio.duration = 180
        mock_audio.title = "Test Song"
        mock_audio.performer = "Test Artist"
        mock_audio.file_size = 5242880
        
        self.mock_message.audio = mock_audio
        
        yield
        
        # Cleanup
        import shutil
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    @pytest.mark.asyncio
    async def test_network_error_during_download(self):
        """Test Netzwerkfehler während des Downloads."""
        # Initialize downloader
        downloader = AudioDownloader(download_dir=str(self.download_dir))
        
        # Mock Telegram client
        mock_client = AsyncMock()
        mock_client.get_entity.return_value = Mock(
            id=-1001234567890,
            title="Test Music Group",
            username="test_music_group"
        )
        mock_client.iter_messages.return_value = [self.mock_message]
        
        # Inject network error during download
        network_error = ErrorInjector.inject_network_error()
        mock_client.download_media.side_effect = network_error
        
        with patch('telegram_audio_downloader.downloader.TelegramClient') as mock_client_class:
            mock_client_class.return_value = mock_client
            
            # Initialize client
            await downloader.initialize_client()
            
            # Perform download - should handle network error gracefully
            result = await downloader.download_audio_files(
                group_name="@test_music_group",
                limit=1
            )
            
            # Verify error handling
            assert result["completed"] == 0
            assert result["failed"] == 1
            
            # Verify database record shows failure
            failed_files = AudioFile.select().where(
                AudioFile.status == DownloadStatus.FAILED.value
            )
            assert len(list(failed_files)) == 1
            
            # Verify error message is recorded
            failed_file = failed_files[0]
            assert "Network" in failed_file.error_message
    
    @pytest.mark.asyncio
    async def test_disk_full_error(self):
        """Test vollständiger Festplattenspeicher."""
        # Initialize downloader
        downloader = AudioDownloader(download_dir=str(self.download_dir))
        
        # Mock Telegram client
        mock_client = AsyncMock()
        mock_client.get_entity.return_value = Mock(
            id=-1001234567890,
            title="Test Music Group",
            username="test_music_group"
        )
        mock_client.iter_messages.return_value = [self.mock_message]
        
        # Inject disk full error during download
        disk_full_error = ErrorInjector.inject_disk_full_error()
        mock_client.download_media.side_effect = disk_full_error
        
        with patch('telegram_audio_downloader.downloader.TelegramClient') as mock_client_class:
            mock_client_class.return_value = mock_client
            
            # Initialize client
            await downloader.initialize_client()
            
            # Perform download - should handle disk full error gracefully
            result = await downloader.download_audio_files(
                group_name="@test_music_group",
                limit=1
            )
            
            # Verify error handling
            assert result["completed"] == 0
            assert result["failed"] == 1
            
            # Verify database record shows failure
            failed_files = AudioFile.select().where(
                AudioFile.status == DownloadStatus.FAILED.value
            )
            assert len(list(failed_files)) == 1
            
            # Verify error message is recorded
            failed_file = failed_files[0]
            assert "space" in failed_file.error_message.lower()
    
    @pytest.mark.asyncio
    async def test_invalid_api_response(self):
        """Test ungültige API-Antworten."""
        # Initialize downloader
        downloader = AudioDownloader(download_dir=str(self.download_dir))
        
        # Mock Telegram client with invalid response
        mock_client = AsyncMock()
        mock_client.get_entity.side_effect = ErrorInjector.inject_invalid_api_response()
        
        with patch('telegram_audio_downloader.downloader.TelegramClient') as mock_client_class:
            mock_client_class.return_value = mock_client
            
            # Initialize client - should handle invalid API response
            with pytest.raises(ValueError):
                await downloader.initialize_client()
    
    @pytest.mark.asyncio
    async def test_timeout_error(self):
        """Test Zeitüberschreitungen."""
        # Initialize downloader
        downloader = AudioDownloader(download_dir=str(self.download_dir))
        
        # Mock Telegram client
        mock_client = AsyncMock()
        mock_client.get_entity.return_value = Mock(
            id=-1001234567890,
            title="Test Music Group",
            username="test_music_group"
        )
        mock_client.iter_messages.return_value = [self.mock_message]
        
        # Inject timeout error during download
        timeout_error = ErrorInjector.inject_timeout_error()
        mock_client.download_media.side_effect = timeout_error
        
        with patch('telegram_audio_downloader.downloader.TelegramClient') as mock_client_class:
            mock_client_class.return_value = mock_client
            
            # Initialize client
            await downloader.initialize_client()
            
            # Perform download - should handle timeout error gracefully
            result = await downloader.download_audio_files(
                group_name="@test_music_group",
                limit=1
            )
            
            # Verify error handling
            assert result["completed"] == 0
            assert result["failed"] == 1
            
            # Verify database record shows failure
            failed_files = AudioFile.select().where(
                AudioFile.status == DownloadStatus.FAILED.value
            )
            assert len(list(failed_files)) == 1
            
            # Verify error message is recorded
            failed_file = failed_files[0]
            assert "timeout" in failed_file.error_message.lower()
    
    @pytest.mark.asyncio
    async def test_multiple_concurrent_errors(self):
        """Test mehrere gleichzeitige Fehler."""
        # Initialize downloader
        downloader = AudioDownloader(
            download_dir=str(self.download_dir),
            max_concurrent_downloads=3
        )
        
        # Create multiple test messages
        mock_messages = []
        for i in range(3):
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
            mock_messages.append(mock_msg)
        
        # Mock Telegram client
        mock_client = AsyncMock()
        mock_client.get_entity.return_value = Mock(
            id=-1001234567890,
            title="Test Music Group",
            username="test_music_group"
        )
        mock_client.iter_messages.return_value = mock_messages
        
        # Inject different errors for different downloads
        def download_side_effect(*args, **kwargs):
            # First call: network error
            # Second call: disk full error
            # Third call: timeout error
            call_count = getattr(download_side_effect, 'call_count', 0)
            download_side_effect.call_count = call_count + 1
            
            if call_count == 0:
                raise ErrorInjector.inject_network_error()
            elif call_count == 1:
                raise ErrorInjector.inject_disk_full_error()
            else:
                raise ErrorInjector.inject_timeout_error()
        
        mock_client.download_media.side_effect = download_side_effect
        
        with patch('telegram_audio_downloader.downloader.TelegramClient') as mock_client_class:
            mock_client_class.return_value = mock_client
            
            # Initialize client
            await downloader.initialize_client()
            
            # Perform downloads - should handle all errors gracefully
            result = await downloader.download_audio_files(
                group_name="@test_music_group",
                limit=3
            )
            
            # Verify error handling
            assert result["completed"] == 0
            assert result["failed"] == 3
            
            # Verify database records show failures
            failed_files = AudioFile.select().where(
                AudioFile.status == DownloadStatus.FAILED.value
            )
            assert len(list(failed_files)) == 3
            
            # Verify different error messages are recorded
            error_messages = [file.error_message for file in failed_files]
            assert any("Network" in msg for msg in error_messages)
            assert any("space" in msg.lower() for msg in error_messages)
            assert any("timeout" in msg.lower() for msg in error_messages)
    
    @pytest.mark.asyncio
    async def test_retry_mechanism(self):
        """Test Retry-Mechanismus bei Fehlern."""
        # Initialize downloader
        downloader = AudioDownloader(download_dir=str(self.download_dir))
        
        # Mock Telegram client
        mock_client = AsyncMock()
        mock_client.get_entity.return_value = Mock(
            id=-1001234567890,
            title="Test Music Group",
            username="test_music_group"
        )
        mock_client.iter_messages.return_value = [self.mock_message]
        
        # Inject temporary error that succeeds on retry
        call_count = 0
        def download_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # First call: network error
                raise ErrorInjector.inject_network_error()
            else:
                # Second call: success
                return b"ID3\x03\x00\x00\x00" + b"\x00" * 1000
        
        mock_client.download_media.side_effect = download_side_effect
        
        with patch('telegram_audio_downloader.downloader.TelegramClient') as mock_client_class:
            mock_client_class.return_value = mock_client
            
            # Initialize client
            await downloader.initialize_client()
            
            # Perform download - should retry and succeed
            result = await downloader.download_audio_files(
                group_name="@test_music_group",
                limit=1
            )
            
            # Verify retry mechanism worked
            assert result["completed"] == 1
            assert result["failed"] == 0
            assert call_count == 2  # Should have been called twice
            
            # Verify database record shows success
            completed_files = AudioFile.select().where(
                AudioFile.status == DownloadStatus.COMPLETED.value
            )
            assert len(list(completed_files)) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])