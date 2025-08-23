"""
Umfassende Tests für die AudioDownloader-Klasse.
"""
import pytest
import asyncio
import tempfile
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch, call
from datetime import datetime

from src.telegram_audio_downloader.downloader import AudioDownloader, DownloadStatus
from src.telegram_audio_downloader.models import AudioFile, TelegramGroup
from telethon.errors import FloodWaitError, RPCError
from telethon.tl.types import MessageMediaDocument, DocumentAttributeAudio


class TestAudioDownloaderInit:
    """Tests für die Initialisierung des AudioDownloaders."""
    
    def test_init_default_params(self):
        """Test Initialisierung mit Standard-Parametern."""
        downloader = AudioDownloader()
        
        assert downloader.download_dir == Path("downloads")
        assert downloader.max_concurrent_downloads == 3
        assert downloader.client is None
        assert downloader.performance_monitor is not None
        assert downloader.rate_limiter is not None
    
    def test_init_custom_params(self):
        """Test Initialisierung mit benutzerdefinierten Parametern."""
        custom_dir = "/tmp/custom_downloads"
        max_downloads = 5
        
        downloader = AudioDownloader(
            download_dir=custom_dir,
            max_concurrent_downloads=max_downloads
        )
        
        assert downloader.download_dir == Path(custom_dir)
        assert downloader.max_concurrent_downloads == max_downloads
    
    def test_init_creates_download_dir(self):
        """Test dass Download-Verzeichnis erstellt wird."""
        with tempfile.TemporaryDirectory() as temp_dir:
            custom_dir = Path(temp_dir) / "new_downloads"
            
            downloader = AudioDownloader(download_dir=str(custom_dir))
            
            assert custom_dir.exists()
            assert custom_dir.is_dir()


@pytest.mark.asyncio
class TestAudioDownloaderTelegramConnection:
    """Tests für Telegram-Verbindung und Client-Management."""
    
    async def test_connect_success(self, mock_telegram_client, sample_env_vars):
        """Test erfolgreiche Telegram-Verbindung."""
        downloader = AudioDownloader()
        
        with patch('src.telegram_audio_downloader.downloader.TelegramClient', return_value=mock_telegram_client):
            await downloader.connect()
            
            assert downloader.client == mock_telegram_client
            mock_telegram_client.start.assert_called_once()
    
    async def test_connect_missing_credentials(self):
        """Test Verbindung ohne Credentials."""
        downloader = AudioDownloader()
        
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="API_ID"):
                await downloader.connect()
    
    async def test_disconnect_success(self, mock_telegram_client):
        """Test erfolgreiche Trennung."""
        downloader = AudioDownloader()
        downloader.client = mock_telegram_client
        
        await downloader.disconnect()
        
        mock_telegram_client.disconnect.assert_called_once()
        assert downloader.client is None
    
    async def test_disconnect_without_client(self):
        """Test Trennung ohne aktiven Client."""
        downloader = AudioDownloader()
        
        # Sollte keine Exception werfen
        await downloader.disconnect()


@pytest.mark.asyncio
class TestAudioDownloaderMessageProcessing:
    """Tests für Nachrichten-Verarbeitung und Audio-Erkennung."""
    
    async def test_is_audio_message_with_audio(self):
        """Test Audio-Nachrichten-Erkennung."""
        downloader = AudioDownloader()
        
        # Mock Message mit Audio
        mock_message = MagicMock()
        mock_media = MagicMock(spec=MessageMediaDocument)
        mock_document = MagicMock()
        mock_document.mime_type = "audio/mpeg"
        
        # Mock AudioAttribute
        mock_audio_attr = MagicMock(spec=DocumentAttributeAudio)
        mock_audio_attr.title = "Test Song"
        mock_audio_attr.performer = "Test Artist"
        mock_audio_attr.duration = 180
        
        mock_document.attributes = [mock_audio_attr]
        mock_media.document = mock_document
        mock_message.media = mock_media
        
        result = downloader._is_audio_message(mock_message)
        
        assert result is True
    
    async def test_is_audio_message_without_audio(self):
        """Test Nicht-Audio-Nachrichten."""
        downloader = AudioDownloader()
        
        # Mock Message ohne Audio
        mock_message = MagicMock()
        mock_message.media = None
        
        result = downloader._is_audio_message(mock_message)
        
        assert result is False
    
    async def test_extract_audio_metadata(self):
        """Test Metadaten-Extraktion."""
        downloader = AudioDownloader()
        
        # Mock Message mit Metadaten
        mock_message = MagicMock()
        mock_media = MagicMock(spec=MessageMediaDocument)
        mock_document = MagicMock()
        mock_document.id = 123456
        mock_document.size = 1024000
        mock_document.mime_type = "audio/mpeg"
        
        mock_audio_attr = MagicMock(spec=DocumentAttributeAudio)
        mock_audio_attr.title = "Test Song"
        mock_audio_attr.performer = "Test Artist"
        mock_audio_attr.duration = 180
        
        mock_document.attributes = [mock_audio_attr]
        mock_media.document = mock_document
        mock_message.media = mock_media
        mock_message.id = 789
        mock_message.date = datetime.now()
        
        metadata = downloader._extract_audio_metadata(mock_message)
        
        assert metadata["file_id"] == 123456
        assert metadata["title"] == "Test Song"
        assert metadata["performer"] == "Test Artist"
        assert metadata["duration"] == 180
        assert metadata["file_size"] == 1024000
        assert metadata["mime_type"] == "audio/mpeg"


@pytest.mark.asyncio
class TestAudioDownloaderDownloadProcess:
    """Tests für den Download-Prozess."""
    
    async def test_download_single_file_success(self, mock_telegram_client, temp_project_dir):
        """Test erfolgreicher Einzel-Download."""
        downloader = AudioDownloader(download_dir=str(temp_project_dir / "downloads"))
        downloader.client = mock_telegram_client
        
        # Mock erfolgreichen Download
        test_file_path = temp_project_dir / "downloads" / "test_song.mp3"
        mock_telegram_client.download_media.return_value = str(test_file_path)
        
        # Mock Message
        mock_message = MagicMock()
        mock_media = MagicMock(spec=MessageMediaDocument)
        mock_document = MagicMock()
        mock_document.id = 123456
        mock_document.size = 1024000
        mock_document.mime_type = "audio/mpeg"
        
        mock_audio_attr = MagicMock(spec=DocumentAttributeAudio)
        mock_audio_attr.title = "Test Song"
        mock_audio_attr.performer = "Test Artist"
        mock_audio_attr.duration = 180
        
        mock_document.attributes = [mock_audio_attr]
        mock_media.document = mock_document
        mock_message.media = mock_media
        mock_message.id = 789
        mock_message.date = datetime.now()
        
        # Erstelle Test-Datei
        test_file_path.parent.mkdir(parents=True, exist_ok=True)
        test_file_path.write_bytes(b"fake audio content")
        
        result = await downloader._download_audio_file(mock_message, temp_project_dir / "downloads")
        
        assert result is not None
        assert result["status"] == "completed"
        assert result["local_path"] == str(test_file_path)
        mock_telegram_client.download_media.assert_called_once()
    
    async def test_download_with_flood_wait_error(self, mock_telegram_client):
        """Test Download mit FloodWaitError."""
        downloader = AudioDownloader()
        downloader.client = mock_telegram_client
        
        # Mock FloodWaitError
        mock_telegram_client.download_media.side_effect = FloodWaitError(5)
        
        mock_message = MagicMock()
        mock_media = MagicMock(spec=MessageMediaDocument)
        mock_document = MagicMock()
        mock_document.id = 123456
        
        mock_media.document = mock_document
        mock_message.media = mock_media
        mock_message.id = 789
        mock_message.date = datetime.now()
        
        with patch('asyncio.sleep') as mock_sleep:
            result = await downloader._download_audio_file(mock_message, Path("/tmp"))
            
            assert result is not None
            assert result["status"] == "failed"
            assert "FloodWaitError" in result["error"]
            mock_sleep.assert_called_with(5)
    
    async def test_download_with_rpc_error(self, mock_telegram_client):
        """Test Download mit RPCError."""
        downloader = AudioDownloader()
        downloader.client = mock_telegram_client
        
        # Mock RPCError
        mock_telegram_client.download_media.side_effect = RPCError("Test RPC Error")
        
        mock_message = MagicMock()
        mock_media = MagicMock(spec=MessageMediaDocument)
        mock_document = MagicMock()
        mock_document.id = 123456
        
        mock_media.document = mock_document
        mock_message.media = mock_media
        mock_message.id = 789
        mock_message.date = datetime.now()
        
        result = await downloader._download_audio_file(mock_message, Path("/tmp"))
        
        assert result is not None
        assert result["status"] == "failed"
        assert "RPCError" in result["error"]


@pytest.mark.asyncio
class TestAudioDownloaderGroupProcessing:
    """Tests für Gruppen-Verarbeitung und Batch-Downloads."""
    
    async def test_download_from_group_success(self, mock_telegram_client, mock_telegram_group, temp_project_dir):
        """Test erfolgreicher Gruppen-Download."""
        downloader = AudioDownloader(download_dir=str(temp_project_dir / "downloads"))
        downloader.client = mock_telegram_client
        
        # Mock Messages
        mock_messages = []
        for i in range(3):
            mock_message = MagicMock()
            mock_media = MagicMock(spec=MessageMediaDocument)
            mock_document = MagicMock()
            mock_document.id = 123456 + i
            mock_document.size = 1024000
            mock_document.mime_type = "audio/mpeg"
            
            mock_audio_attr = MagicMock(spec=DocumentAttributeAudio)
            mock_audio_attr.title = f"Test Song {i}"
            mock_audio_attr.performer = "Test Artist"
            mock_audio_attr.duration = 180
            
            mock_document.attributes = [mock_audio_attr]
            mock_media.document = mock_document
            mock_message.media = mock_media
            mock_message.id = 789 + i
            mock_message.date = datetime.now()
            
            mock_messages.append(mock_message)
        
        mock_telegram_client.get_entity.return_value = mock_telegram_group
        mock_telegram_client.iter_messages.return_value = mock_messages
        
        # Mock erfolgreiche Downloads
        def mock_download_side_effect(message, path):
            file_path = path / f"song_{message.id}.mp3"
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_bytes(b"fake audio")
            return str(file_path)
        
        mock_telegram_client.download_media.side_effect = mock_download_side_effect
        
        result = await downloader.download_from_group("@testgroup", limit=10)
        
        assert result is not None
        assert result["completed"] == 3
        assert result["failed"] == 0
        assert len(result["files"]) == 3
        
        mock_telegram_client.get_entity.assert_called_once_with("@testgroup")
        mock_telegram_client.iter_messages.assert_called_once()
    
    async def test_download_from_group_with_limit(self, mock_telegram_client, mock_telegram_group):
        """Test Gruppen-Download mit Limit."""
        downloader = AudioDownloader()
        downloader.client = mock_telegram_client
        
        # Mock viele Messages
        mock_messages = []
        for i in range(20):  # 20 Messages erstellen
            mock_message = MagicMock()
            mock_media = MagicMock(spec=MessageMediaDocument)
            mock_document = MagicMock()
            mock_document.id = 123456 + i
            mock_document.mime_type = "audio/mpeg"
            
            mock_audio_attr = MagicMock(spec=DocumentAttributeAudio)
            mock_audio_attr.title = f"Song {i}"
            mock_document.attributes = [mock_audio_attr]
            
            mock_media.document = mock_document
            mock_message.media = mock_media
            mock_message.id = 789 + i
            mock_message.date = datetime.now()
            
            mock_messages.append(mock_message)
        
        mock_telegram_client.get_entity.return_value = mock_telegram_group
        mock_telegram_client.iter_messages.return_value = mock_messages
        mock_telegram_client.download_media.return_value = "/tmp/fake.mp3"
        
        result = await downloader.download_from_group("@testgroup", limit=5)
        
        assert result is not None
        assert result["completed"] <= 5  # Nicht mehr als das Limit
    
    async def test_download_from_group_parallel(self, mock_telegram_client, mock_telegram_group, temp_project_dir):
        """Test parallele Downloads."""
        downloader = AudioDownloader(
            download_dir=str(temp_project_dir / "downloads"),
            max_concurrent_downloads=2
        )
        downloader.client = mock_telegram_client
        
        # Mock mehrere Audio-Messages
        mock_messages = []
        for i in range(4):
            mock_message = MagicMock()
            mock_media = MagicMock(spec=MessageMediaDocument)
            mock_document = MagicMock()
            mock_document.id = 123456 + i
            mock_document.size = 1024000
            mock_document.mime_type = "audio/mpeg"
            
            mock_audio_attr = MagicMock(spec=DocumentAttributeAudio)
            mock_audio_attr.title = f"Parallel Song {i}"
            mock_audio_attr.performer = "Test Artist"
            mock_audio_attr.duration = 180
            
            mock_document.attributes = [mock_audio_attr]
            mock_media.document = mock_document
            mock_message.media = mock_media
            mock_message.id = 789 + i
            mock_message.date = datetime.now()
            
            mock_messages.append(mock_message)
        
        mock_telegram_client.get_entity.return_value = mock_telegram_group
        mock_telegram_client.iter_messages.return_value = mock_messages
        
        # Track concurrent calls
        call_count = 0
        max_concurrent = 0
        
        async def mock_download_with_delay(message, path):
            nonlocal call_count, max_concurrent
            call_count += 1
            max_concurrent = max(max_concurrent, call_count)
            
            # Simuliere Download-Zeit
            await asyncio.sleep(0.1)
            
            file_path = path / f"parallel_song_{message.id}.mp3"
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_bytes(b"fake audio")
            
            call_count -= 1
            return str(file_path)
        
        with patch.object(downloader, '_download_audio_file', side_effect=mock_download_with_delay):
            result = await downloader.download_from_group("@testgroup", limit=4)
        
        assert result is not None
        assert result["completed"] == 4
        assert max_concurrent <= downloader.max_concurrent_downloads


@pytest.mark.asyncio 
class TestAudioDownloaderErrorHandling:
    """Tests für Error-Handling und Retry-Mechanismen."""
    
    async def test_retry_mechanism(self, mock_telegram_client):
        """Test Retry-Mechanismus bei temporären Fehlern."""
        downloader = AudioDownloader()
        downloader.client = mock_telegram_client
        
        # Mock temporäre Fehler gefolgt von Erfolg
        call_count = 0
        def mock_download_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:  # Erste 2 Calls schlagen fehl
                raise RPCError("Temporary error")
            return "/tmp/success.mp3"
        
        mock_telegram_client.download_media.side_effect = mock_download_side_effect
        
        mock_message = MagicMock()
        mock_media = MagicMock(spec=MessageMediaDocument)
        mock_document = MagicMock()
        mock_document.id = 123456
        
        mock_media.document = mock_document
        mock_message.media = mock_media
        mock_message.id = 789
        mock_message.date = datetime.now()
        
        with patch('asyncio.sleep'):  # Skip actual sleep
            result = await downloader._download_audio_file(mock_message, Path("/tmp"))
        
        assert call_count == 3  # 2 Fehlversuche + 1 Erfolg
        # Je nach Implementierung: entweder Erfolg oder Fehler nach max retries
    
    async def test_performance_monitoring_integration(self, mock_telegram_client):
        """Test Integration mit Performance-Monitoring."""
        downloader = AudioDownloader()
        downloader.client = mock_telegram_client
        
        # Mock Performance Monitor
        with patch.object(downloader.performance_monitor, 'start_download') as mock_start, \
             patch.object(downloader.performance_monitor, 'complete_download') as mock_complete:
            
            mock_telegram_client.download_media.return_value = "/tmp/test.mp3"
            
            mock_message = MagicMock()
            mock_media = MagicMock(spec=MessageMediaDocument)
            mock_document = MagicMock()
            mock_document.id = 123456
            mock_document.size = 1024000
            
            mock_media.document = mock_document
            mock_message.media = mock_media
            mock_message.id = 789
            mock_message.date = datetime.now()
            
            await downloader._download_audio_file(mock_message, Path("/tmp"))
            
            mock_start.assert_called_once()
            mock_complete.assert_called_once()


@pytest.mark.slow
@pytest.mark.asyncio
class TestAudioDownloaderIntegration:
    """Integration-Tests für komplette Workflows."""
    
    async def test_full_download_workflow(self, mock_telegram_client, temp_project_dir, sample_env_vars):
        """Test kompletter Download-Workflow."""
        downloader = AudioDownloader(download_dir=str(temp_project_dir / "downloads"))
        
        with patch('src.telegram_audio_downloader.downloader.TelegramClient', return_value=mock_telegram_client):
            # Setup
            await downloader.connect()
            
            # Mock Group und Messages
            mock_group = MagicMock()
            mock_group.id = 987654321
            mock_group.title = "Test Music Group"
            
            mock_message = MagicMock()
            mock_media = MagicMock(spec=MessageMediaDocument)
            mock_document = MagicMock()
            mock_document.id = 123456
            mock_document.size = 1024000
            mock_document.mime_type = "audio/mpeg"
            
            mock_audio_attr = MagicMock(spec=DocumentAttributeAudio)
            mock_audio_attr.title = "Integration Test Song"
            mock_audio_attr.performer = "Test Artist"
            mock_audio_attr.duration = 180
            
            mock_document.attributes = [mock_audio_attr]
            mock_media.document = mock_document
            mock_message.media = mock_media
            mock_message.id = 789
            mock_message.date = datetime.now()
            
            mock_telegram_client.get_entity.return_value = mock_group
            mock_telegram_client.iter_messages.return_value = [mock_message]
            
            # Mock successful download
            test_file = temp_project_dir / "downloads" / "integration_test.mp3"
            test_file.parent.mkdir(parents=True, exist_ok=True)
            test_file.write_bytes(b"fake audio content")
            mock_telegram_client.download_media.return_value = str(test_file)
            
            # Execute
            result = await downloader.download_from_group("@testgroup", limit=1)
            
            # Cleanup
            await downloader.disconnect()
            
            # Verify
            assert result is not None
            assert result["completed"] == 1
            assert result["failed"] == 0
            assert len(result["files"]) == 1
            assert test_file.exists()


# Fixtures für komplexere Test-Szenarien
@pytest.fixture
def complex_audio_message():
    """Erstellt eine komplexe Audio-Nachricht für Tests."""
    mock_message = MagicMock()
    mock_media = MagicMock(spec=MessageMediaDocument)
    mock_document = MagicMock()
    
    # Document Properties
    mock_document.id = 123456789
    mock_document.access_hash = 987654321
    mock_document.file_reference = b"fake_reference"
    mock_document.date = datetime.now()
    mock_document.mime_type = "audio/mpeg"
    mock_document.size = 5242880  # 5MB
    
    # Audio Attributes
    mock_audio_attr = MagicMock(spec=DocumentAttributeAudio)
    mock_audio_attr.duration = 300  # 5 minutes
    mock_audio_attr.title = "Complex Test Song with Special Characters äöü"
    mock_audio_attr.performer = "Test Artist & Band"
    mock_audio_attr.voice = False
    mock_audio_attr.waveform = None
    
    mock_document.attributes = [mock_audio_attr]
    mock_media.document = mock_document
    mock_message.media = mock_media
    mock_message.id = 987654321
    mock_message.date = datetime.now()
    
    return mock_message


@pytest.fixture
def mock_rate_limiter():
    """Mock für Rate-Limiter."""
    rate_limiter = MagicMock()
    rate_limiter.acquire = AsyncMock()
    rate_limiter.get_current_rate.return_value = 1.0
    rate_limiter.get_tokens_available.return_value = 5.0
    return rate_limiter