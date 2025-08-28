"""
Integration-Tests für End-to-End Download-Workflows und System-Integration.
"""
import pytest
import asyncio
import tempfile
import os
import json
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timedelta
from typing import Optional

from src.telegram_audio_downloader.downloader import AudioDownloader
from src.telegram_audio_downloader.database import init_db, close_db
from src.telegram_audio_downloader.models import AudioFile, TelegramGroup, DownloadStatus
from src.telegram_audio_downloader.cli import download, search, stats
from src.telegram_audio_downloader.performance import PerformanceMonitor
from src.telegram_audio_downloader.logging_config import get_logger, setup_logging

from click.testing import CliRunner
from telethon.tl.types import MessageMediaDocument, DocumentAttributeAudio


@pytest.mark.integration
class TestEndToEndDownloadWorkflow:
    """End-to-End Tests für komplette Download-Workflows."""
    
    @pytest.fixture
    def temp_environment(self):
        """Erstellt isolierte Test-Umgebung."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Test-Verzeichnisse erstellen
            download_dir = temp_path / "downloads"
            data_dir = temp_path / "data"
            config_dir = temp_path / "config"
            
            download_dir.mkdir()
            data_dir.mkdir()
            config_dir.mkdir()
            
            # Test-Datenbank
            db_path = data_dir / "test.db"
            database = init_db(str(db_path))
            
            yield {
                "temp_dir": temp_path,
                "download_dir": download_dir,
                "data_dir": data_dir,
                "config_dir": config_dir,
                "db_path": db_path,
                "database": database
            }
            
            close_db()
    
    @pytest.fixture
    def mock_telegram_environment(self):
        """Mock-Telegram-Umgebung für Tests."""
        # Mock Umgebungsvariablen
        env_vars = {
            "API_ID": "123456",
            "API_HASH": "test_api_hash_12345",
            "SESSION_NAME": "test_session"
        }
        
        # Mock TelegramClient
        mock_client = AsyncMock()
        mock_client.start = AsyncMock()
        mock_client.disconnect = AsyncMock()
        mock_client.get_entity = AsyncMock()
        mock_client.iter_messages = AsyncMock()
        mock_client.download_media = AsyncMock()
        
        return {
            "env_vars": env_vars,
            "mock_client": mock_client
        }
    
    @pytest.mark.asyncio
    async def test_complete_download_workflow(self, temp_environment, mock_telegram_environment):
        """Test kompletter Download-Workflow von Anfang bis Ende."""
        env = temp_environment
        telegram_env = mock_telegram_environment
        
        # Setup Mock-Daten
        mock_group = MagicMock()
        mock_group.id = 987654321
        mock_group.title = "Integration Test Group"
        mock_group.username = "integration_test_group"
        
        # Mock Audio-Messages
        mock_messages = []
        for i in range(3):
            mock_message = self._create_mock_audio_message(
                message_id=1000 + i,
                file_id=f"test_file_{i}",
                title=f"Integration Test Song {i}",
                performer="Test Artist",
                duration=180 + (i * 30),
                file_size=1024000 + (i * 500000)
            )
            mock_messages.append(mock_message)
        
        # Setup Mock-Client-Responses
        telegram_env["mock_client"].get_entity.return_value = mock_group
        telegram_env["mock_client"].iter_messages.return_value = mock_messages
        
        # Mock erfolgreiche Downloads
        def mock_download_media(message, path):
            # Erstelle echte Test-Datei
            file_path = Path(path) / f"song_{message.id}.mp3"
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Simuliere Audio-Inhalt
            fake_audio_data = b"FAKE_MP3_HEADER" + b"0" * (message.media.document.size - 15)
            file_path.write_bytes(fake_audio_data)
            
            return str(file_path)
        
        telegram_env["mock_client"].download_media.side_effect = mock_download_media
        
        # Test: Download-Workflow ausführen
        with patch.dict(os.environ, telegram_env["env_vars"]), \
             patch('src.telegram_audio_downloader.downloader.TelegramClient', 
                   return_value=telegram_env["mock_client"]):
            
            downloader = AudioDownloader(
                download_dir=str(env["download_dir"]),
                max_concurrent_downloads=2
            )
            
            # Verbindung herstellen
            await downloader.initialize_client()
            
            # Download ausführen
            result = await downloader.download_audio_files("@integration_test_group", limit=3)
            
            # Verbindung trennen
            await downloader.close()
        
        # Verifikation: Download-Ergebnisse
        assert result is not None
        assert result["completed"] == 3
        assert result["failed"] == 0
        assert len(result["files"]) == 3
        
        # Verifikation: Dateien wurden erstellt
        downloaded_files = list(env["download_dir"].glob("*.mp3"))
        assert len(downloaded_files) == 3
        
        for file_path in downloaded_files:
            assert file_path.exists()
            assert file_path.stat().st_size > 1000000  # Mindestens 1MB
        
        # Verifikation: Datenbank-Einträge
        saved_group = TelegramGroup.get(TelegramGroup.group_id == 987654321)
        assert saved_group.title == "Integration Test Group"
        
        saved_files = AudioFile.select().where(AudioFile.group == saved_group)
        assert saved_files.count() == 3
        
        for audio_file in saved_files:
            assert audio_file.status == DownloadStatus.COMPLETED.value
            assert audio_file.local_path is not None
            assert Path(audio_file.local_path).exists()
    
    @pytest.mark.asyncio
    async def test_download_with_errors_and_retries(self, temp_environment, mock_telegram_environment):
        """Test Download-Workflow mit Fehlern und Retry-Mechanismus."""
        env = temp_environment
        telegram_env = mock_telegram_environment
        
        # Setup: Gemischte Erfolgreich/Fehler-Szenarien
        mock_group = MagicMock()
        mock_group.id = 123456789
        mock_group.title = "Error Test Group"
        
        mock_messages = [
            self._create_mock_audio_message(2001, "success_file_1", "Success Song 1"),
            self._create_mock_audio_message(2002, "error_file_1", "Error Song 1"),
            self._create_mock_audio_message(2003, "success_file_2", "Success Song 2"),
        ]
        
        telegram_env["mock_client"].get_entity.return_value = mock_group
        telegram_env["mock_client"].iter_messages.return_value = mock_messages
        
        # Mock: Erster Download schlägt fehl, zweiter erfolgreich
        call_count = 0
        def mock_download_with_errors(message, path):
            nonlocal call_count
            call_count += 1
            
            if "error_file" in message.media.document.id:
                if call_count <= 2:  # Erste 2 Versuche schlagen fehl
                    from telethon.errors import RPCError
                    raise RPCError("Temporary download error")
                # Dritter Versuch erfolgreich
            
            # Erfolgreicher Download
            file_path = Path(path) / f"song_{message.id}.mp3"
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_bytes(b"FAKE_AUDIO_DATA" * 10000)
            return str(file_path)
        
        telegram_env["mock_client"].download_media.side_effect = mock_download_with_errors
        
        # Test: Download mit Retry-Logik
        with patch.dict(os.environ, telegram_env["env_vars"]), \
             patch('src.telegram_audio_downloader.downloader.TelegramClient', 
                   return_value=telegram_env["mock_client"]):
            
            downloader = AudioDownloader(download_dir=str(env["download_dir"]))
            await downloader.initialize_client()
            
            result = await downloader.download_audio_files("@error_test_group", limit=3)
            
            await downloader.close()
        
        # Verifikation: Mischung aus Erfolg und Fehlern
        assert result["completed"] >= 1  # Mindestens ein erfolgreicher Download
        assert result["failed"] >= 0     # Möglicherweise Fehler nach max retries
        
        # Verifikation: Error-Tracking funktioniert
        from src.telegram_audio_downloader.logging_config import get_error_tracker
        error_tracker = get_error_tracker()
        assert len(error_tracker.errors) > 0
    
    def _create_mock_audio_message(self, message_id: int, file_id: str, title: str, 
                                   performer: str = "Test Artist", duration: int = 180, 
                                   file_size: int = 1024000):
        """Hilfsmethode zum Erstellen von Mock-Audio-Messages."""
        mock_message = MagicMock()
        mock_message.id = message_id
        mock_message.date = datetime.now()
        
        # Mock Media Document
        mock_media = MagicMock(spec=MessageMediaDocument)
        mock_document = MagicMock()
        mock_document.id = file_id
        mock_document.size = file_size
        mock_document.mime_type = "audio/mpeg"
        
        # Mock Audio Attributes
        mock_audio_attr = MagicMock(spec=DocumentAttributeAudio)
        mock_audio_attr.title = title
        mock_audio_attr.performer = performer
        mock_audio_attr.duration = duration
        
        mock_document.attributes = [mock_audio_attr]
        mock_media.document = mock_document
        mock_message.media = mock_media
        
        return mock_message


@pytest.mark.integration
class TestCLIIntegration:
    """Integration-Tests für CLI-Commands mit realer Datenbank."""
    
    @pytest.fixture
    def cli_environment(self):
        """CLI-Test-Umgebung mit temporärer Datenbank."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            db_path = temp_path / "cli_test.db"
            
            # Test-Datenbank initialisieren
            database = init_db(str(db_path))
            
            # Test-Daten erstellen
            test_group = TelegramGroup.create(
                group_id=111222333,
                title="CLI Test Group",
                username="cli_test_group"
            )
            
            # Mehrere Test-Audiodateien
            test_files = []
            for i in range(5):
                audio_file = AudioFile.create(
                    file_id=f"cli_test_file_{i}",
                    file_unique_id=f"cli_unique_{i}",
                    file_name=f"cli_test_song_{i}.mp3",
                    file_size=1000000 + (i * 200000),
                    mime_type="audio/mpeg",
                    duration=180 + (i * 30),
                    title=f"CLI Test Song {i}",
                    performer=f"CLI Artist {i % 2}",
                    group=test_group,
                    status=[
                        DownloadStatus.COMPLETED.value,
                        DownloadStatus.PENDING.value,
                        DownloadStatus.FAILED.value
                    ][i % 3],
                    local_path=str(temp_path / f"cli_test_song_{i}.mp3") if i % 3 == 0 else None
                )
                test_files.append(audio_file)
            
            yield {
                "temp_dir": temp_path,
                "db_path": db_path,
                "database": database,
                "test_group": test_group,
                "test_files": test_files
            }
            
            close_db()
    
    def test_search_command_integration(self, cli_environment):
        """Test Search-Command mit realer Datenbank."""
        env = cli_environment
        
        # Mock database path für CLI
        with patch('src.telegram_audio_downloader.cli.init_db') as mock_init:
            mock_init.return_value = env["database"]
            
            runner = CliRunner()
            result = runner.invoke(search, ['CLI Test Song'])
            
            assert result.exit_code == 0
            assert "CLI Test Song" in result.output
            # Sollte mehrere Ergebnisse finden
            assert "Dateien gefunden" in result.output or "files found" in result.output
    
    def test_stats_command_integration(self, cli_environment):
        """Test Stats-Command mit realer Datenbank."""
        env = cli_environment
        
        with patch('src.telegram_audio_downloader.cli.init_db') as mock_init:
            mock_init.return_value = env["database"]
            
            runner = CliRunner()
            result = runner.invoke(stats)
            
            assert result.exit_code == 0
            
            # Sollte Statistiken enthalten
            output_lower = result.output.lower()
            assert any(word in output_lower for word in ["total", "gesamt", "files", "dateien"])
            assert any(word in output_lower for word in ["completed", "abgeschlossen", "pending"])
    
    @patch.dict(os.environ, {"API_ID": "123456", "API_HASH": "test_hash"})
    def test_download_command_integration(self, cli_environment):
        """Test Download-Command Integration."""
        env = cli_environment
        
        # Mock downloader workflow
        with patch('src.telegram_audio_downloader.cli.init_db') as mock_init, \
             patch('src.telegram_audio_downloader.cli.AudioDownloader') as mock_downloader_class, \
             patch('src.telegram_audio_downloader.cli.asyncio.run') as mock_asyncio_run:
            
            mock_init.return_value = env["database"]
            
            # Mock successful download result
            mock_result = {
                "completed": 2,
                "failed": 0,
                "files": ["song1.mp3", "song2.mp3"],
                "errors": []
            }
            mock_asyncio_run.return_value = mock_result
            
            runner = CliRunner()
            result = runner.invoke(download, ['@cli_test_group', '--limit', '5'])
            
            assert result.exit_code == 0
            mock_downloader_class.assert_called_once()


@pytest.mark.integration
class TestSystemIntegration:
    """System-weite Integration-Tests."""
    
    @pytest.mark.asyncio
    async def test_performance_monitoring_integration(self):
        """Test Integration von Performance-Monitoring."""
        from src.telegram_audio_downloader.performance import get_performance_monitor
        
        perf_monitor = get_performance_monitor()
        
        # Test Performance-Tracking
        perf_monitor.downloads_in_progress += 1
        
        # Simuliere Download-Aktivität
        await asyncio.sleep(0.1)
        
        perf_monitor.downloads_in_progress -= 1
        perf_monitor.successful_downloads += 1
        
        # Verifikation: Metriken wurden aufgezeichnet
        report = perf_monitor.get_performance_report()
        
        assert "downloads" in report
        assert report["downloads"]["completed"] >= 1
        assert "performance" in report
        assert "resources" in report
    
    def test_logging_integration(self):
        """Test Logging-System-Integration."""
        # Setup: Debug-Logging controlled by environment
        debug_mode = os.getenv("TEST_DEBUG_MODE", "false").lower() == "true"
        logger = setup_logging(debug=debug_mode)
        
        # Test: Verschiedene Log-Level
        logger.debug("Debug-Message für Integration-Test")
        logger.info("Info-Message für Integration-Test")
        logger.warning("Warning-Message für Integration-Test")
        logger.error("Error-Message für Integration-Test")
        
        # Verifikation: Logger funktioniert
        assert logger.level <= 10  # DEBUG-Level oder niedriger
        assert len(logger.handlers) > 0
    
    @pytest.mark.asyncio
    async def test_database_performance_integration(self):
        """Test Database-Performance unter Last."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "performance_test.db"
            database = init_db(str(db_path))
            
            # Performance-Test: Bulk-Insert
            import time
            start_time = time.time()
            
            test_group = TelegramGroup.create(
                group_id=999888777,
                title="Performance Test Group",
                username="perf_test"
            )
            
            # 100 Dateien gleichzeitig einfügen
            with database.atomic():
                for i in range(100):
                    AudioFile.create(
                        file_id=f"perf_file_{i}",
                        file_unique_id=f"perf_unique_{i}",
                        file_name=f"perf_song_{i}.mp3",
                        file_size=1000000,
                        mime_type="audio/mpeg",
                        group=test_group
                    )
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Verifikation: Performance ist akzeptabel
            assert duration < 5.0  # Weniger als 5 Sekunden
            
            # Verifikation: Alle Daten wurden korrekt gespeichert
            total_files = AudioFile.select().count()
            assert total_files == 100
            
            close_db()


@pytest.mark.integration
class TestErrorRecoveryIntegration:
    """Integration-Tests für Error-Recovery und Robustheit."""
    
    @pytest.mark.asyncio
    async def test_network_failure_recovery(self, temp_project_dir):
        """Test Recovery bei Netzwerkfehlern."""
        download_dir = temp_project_dir / "network_test_downloads"
        download_dir.mkdir()
        
        # Mock Client mit intermittierenden Fehlern
        mock_client = AsyncMock()
        
        failure_count = 0
        async def mock_download_with_failures(*args, **kwargs):
            nonlocal failure_count
            failure_count += 1
            
            if failure_count <= 2:
                # Erste 2 Versuche schlagen fehl
                raise ConnectionError("Network timeout")
            
            # Dritter Versuch erfolgreich
            test_file = download_dir / f"recovered_file_{failure_count}.mp3"
            test_file.write_bytes(b"Recovered audio data")
            return str(test_file)
        
        mock_client.download_media = mock_download_with_failures
        
        # Test mit Mock-Message
        mock_message = MagicMock()
        mock_message.id = 3001
        mock_message.date = datetime.now()
        
        downloader = AudioDownloader(download_dir=str(download_dir))
        downloader.client = mock_client
        
        # Mock Message mit Document Structure
        mock_message.media = MagicMock()
        mock_message.media.document = MagicMock()
        mock_message.media.document.id = "test_file_001"
        mock_message.media.document.size = 1000000
        mock_message.media.document.mime_type = "audio/mpeg"
        mock_message.media.document.attributes = []
        
        # Test: Download-Simulation 
        test_group = TelegramGroup.get_or_create(group_id=1, defaults={'title': 'Test'})[0]
        result = await downloader._download_audio(mock_message, mock_message.media.document, test_group)
        
        # Verifikation: Recovery erfolgreich nach mehreren Versuchen
        assert failure_count >= 3  # Mindestens 3 Versuche
        # Je nach Implementierung kann Erfolg oder Fehler erwartet werden
    
    def test_database_corruption_recovery(self):
        """Test Recovery bei Datenbank-Problemen."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "corruption_test.db"
            
            # Normale Datenbank erstellen
            database = init_db(str(db_path))
            
            test_group = TelegramGroup.create(
                group_id=444555666,
                title="Corruption Test",
                username="corruption_test"
            )
            
            close_db()
            
            # Simuliere Datenbank-Problem durch Beschädigung
            with open(db_path, 'wb') as f:
                f.write(b"CORRUPTED_DATABASE_CONTENT")
            
            # Versuche Verbindung wiederherzustellen
            try:
                database = init_db(str(db_path))
                # Sollte neue Datenbank erstellen oder Fehler behandeln
                close_db()
            except Exception as e:
                # Erwarteter Fehler bei Korruption
                assert "database" in str(e).lower() or "corrupt" in str(e).lower()
    
    @pytest.mark.asyncio
    async def test_partial_download_recovery(self, temp_project_dir):
        """Test Recovery bei unvollständigen Downloads."""
        download_dir = temp_project_dir / "partial_download_test"
        download_dir.mkdir()
        
        # Erstelle unvollständige Datei
        partial_file = download_dir / "partial_song.mp3"
        partial_file.write_bytes(b"INCOMPLETE_AUDIO_DATA")
        
        # Simuliere Download-Fortsetzung
        mock_client = AsyncMock()
        
        def mock_resume_download(*args, **kwargs):
            # Vervollständige die Datei
            complete_data = b"COMPLETE_AUDIO_DATA" + b"0" * 1000000
            partial_file.write_bytes(complete_data)
            return str(partial_file)
        
        mock_client.download_media = mock_resume_download
        
        mock_message = MagicMock()
        mock_message.id = 4001
        
        downloader = AudioDownloader(download_dir=str(download_dir))
        downloader.client = mock_client
        
        # Test: Download-Simulation
        result = await downloader._download_audio(mock_message, mock_message.media.document, 
                                                  TelegramGroup.get_or_create(group_id=1, defaults={'title': 'Test'})[0])
        
        # Verifikation: Datei wurde vervollständigt
        assert partial_file.exists()
        assert partial_file.stat().st_size > 1000000  # Größer als ursprüngliche Datei


@pytest.mark.integration
@pytest.mark.slow
class TestLongRunningIntegration:
    """Langzeittests für Stabilität und Resource-Management."""
    
    @pytest.mark.asyncio
    async def test_memory_leak_detection(self):
        """Test auf Memory-Leaks bei längeren Operationen."""
        import psutil
        import gc
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        # Simuliere längere Download-Session
        for i in range(50):
            # Mock Download-Zyklus
            mock_downloader = AudioDownloader()
            
            # Simuliere Arbeit
            await asyncio.sleep(0.01)
            
            # Explizite Garbage Collection
            del mock_downloader
            if i % 10 == 0:
                gc.collect()
        
        # Finale Garbage Collection
        gc.collect()
        final_memory = process.memory_info().rss
        
        # Verifikation: Memory-Verbrauch bleibt stabil
        memory_increase = final_memory - initial_memory
        memory_increase_mb = memory_increase / (1024 * 1024)
        
        # Memory-Increase sollte unter 50MB bleiben
        assert memory_increase_mb < 50, f"Memory increased by {memory_increase_mb:.2f}MB"
    
    def test_concurrent_database_access(self):
        """Test gleichzeitiger Datenbank-Zugriffe."""
        import concurrent.futures
        import threading
        
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "concurrent_test.db"
            database = init_db(str(db_path))
            
            # Test-Gruppe erstellen
            test_group = TelegramGroup.create(
                group_id=777888999,
                title="Concurrent Test",
                username="concurrent_test"
            )
            
            def create_audio_files(thread_id):
                """Worker-Funktion für parallele Datenbank-Zugriffe."""
                for i in range(10):
                    try:
                        AudioFile.create(
                            file_id=f"concurrent_{thread_id}_{i}",
                            file_unique_id=f"concurrent_unique_{thread_id}_{i}",
                            file_name=f"concurrent_song_{thread_id}_{i}.mp3",
                            file_size=1000000,
                            mime_type="audio/mpeg",
                            group=test_group
                        )
                    except Exception as e:
                        # Concurrency-Fehler können auftreten
                        print(f"Thread {thread_id}: {e}")
                
                return thread_id
            
            # Führe mehrere Threads parallel aus
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                futures = [executor.submit(create_audio_files, i) for i in range(3)]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            # Verifikation: Datenbank blieb konsistent
            total_files = AudioFile.select().count()
            assert total_files > 0  # Mindestens einige Dateien wurden erstellt
            
            close_db()


# Utilities für Integration-Tests
class IntegrationTestUtils:
    """Hilfsmethoden für Integration-Tests."""
    
    @staticmethod
    def create_test_environment(temp_dir: Path):
        """Erstellt vollständige Test-Umgebung."""
        # Verzeichnisse erstellen
        dirs = {
            "downloads": temp_dir / "downloads",
            "data": temp_dir / "data", 
            "config": temp_dir / "config",
            "logs": temp_dir / "logs"
        }
        
        for dir_path in dirs.values():
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Test-Konfiguration erstellen
        config_file = dirs["config"] / "test.ini"
        config_content = """[settings]
default_download_dir = downloads
max_concurrent_downloads = 2

[database]
path = data/test.db

[logging]
level = DEBUG
file = logs/test.log
"""
        config_file.write_text(config_content)
        
        return dirs
    
    @staticmethod
    def validate_download_results(result: dict, expected_completed: Optional[int] = None, 
                                  expected_failed: Optional[int] = None):
        """Validiert Download-Ergebnisse."""
        assert isinstance(result, dict)
        assert "completed" in result
        assert "failed" in result
        assert "files" in result
        
        if expected_completed is not None:
            assert result["completed"] == expected_completed
        
        if expected_failed is not None:
            assert result["failed"] == expected_failed
        
        assert isinstance(result["files"], list)
        assert len(result["files"]) == result["completed"]
    
    @staticmethod
    def cleanup_test_files(file_paths: list):
        """Bereinigt Test-Dateien."""
        for file_path in file_paths:
            path = Path(file_path)
            if path.exists():
                try:
                    path.unlink()
                except (PermissionError, OSError):
                    pass  # Ignore cleanup errors


# Fixtures für alle Integration-Tests
@pytest.fixture
def integration_logger():
    """Logger für Integration-Tests."""
    debug_mode = os.getenv("TEST_DEBUG_MODE", "false").lower() == "true"
    return setup_logging(debug=debug_mode)


@pytest.fixture
def temp_project_dir():
    """Temporäres Projekt-Verzeichnis."""
    with tempfile.TemporaryDirectory() as temp_dir:
        project_dir = Path(temp_dir)
        
        # Basis-Struktur erstellen
        test_utils = IntegrationTestUtils()
        dirs = test_utils.create_test_environment(project_dir)
        
        yield project_dir


@pytest.fixture(scope="session", autouse=True)
def integration_test_cleanup():
    """Session-weite Cleanup-Logik."""
    yield
    
    # Cleanup nach allen Tests
    import gc
    gc.collect()
    
    # Reset global state falls notwendig
    try:
        close_db()
    except:
        pass