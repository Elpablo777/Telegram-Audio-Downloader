"""
Umfassende Tests für die CLI-Interface mit Click und Rich.
"""
import pytest
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
from click.testing import CliRunner

from src.telegram_audio_downloader.cli import (
    cli, download, search, performance, stats, groups, metadata,
    print_banner, check_env
)
from src.telegram_audio_downloader.models import DownloadStatus


class TestCLIBasics:
    """Tests für grundlegende CLI-Funktionalität."""
    
    def test_print_banner(self, capsys):
        """Test Banner-Ausgabe."""
        print_banner()
        captured = capsys.readouterr()
        
        assert "Telegram Audio Downloader" in captured.out
        assert "v0.1.0" in captured.out
        assert "╔" in captured.out
    
    def test_check_env_success(self, monkeypatch):
        """Test Umgebungsvariablen-Check bei korrekten Werten."""
        monkeypatch.setenv("API_ID", "12345")
        monkeypatch.setenv("API_HASH", "test_api_hash")
        
        result = check_env()
        assert result is True
    
    def test_check_env_missing_vars(self, monkeypatch):
        """Test Umgebungsvariablen-Check bei fehlenden Werten."""
        monkeypatch.delenv("API_ID", raising=False)
        monkeypatch.delenv("API_HASH", raising=False)
        
        with patch('src.telegram_audio_downloader.cli.console') as mock_console:
            result = check_env()
            
            assert result is False
            mock_console.print.assert_called()
    
    def test_cli_main_group(self):
        """Test Haupt-CLI-Gruppe."""
        runner = CliRunner()
        result = runner.invoke(cli, ['--help'])
        
        assert result.exit_code == 0
        assert "Telegram Audio Downloader" in result.output


class TestDownloadCommand:
    """Tests für den Download-Command."""
    
    @patch('src.telegram_audio_downloader.cli.check_env')
    @patch('src.telegram_audio_downloader.cli.init_db')
    @patch('src.telegram_audio_downloader.cli.AudioDownloader')
    @patch('src.telegram_audio_downloader.cli.asyncio.run')
    def test_download_command_success(self, mock_asyncio_run, mock_downloader_class, 
                                    mock_init_db, mock_check_env):
        """Test erfolgreicher Download-Command."""
        mock_check_env.return_value = True
        mock_downloader = MagicMock()
        mock_downloader_class.return_value = mock_downloader
        
        mock_result = {
            'completed': 5,
            'failed': 1,
            'files': ['song1.mp3', 'song2.mp3'],
            'errors': ['Error downloading song6.mp3']
        }
        mock_asyncio_run.return_value = mock_result
        
        runner = CliRunner()
        result = runner.invoke(download, ['@testgroup', '--limit', '10'])
        
        assert result.exit_code == 0
        mock_check_env.assert_called_once()
        mock_init_db.assert_called_once()
    
    @patch('src.telegram_audio_downloader.cli.check_env')
    def test_download_command_missing_env(self, mock_check_env):
        """Test Download-Command bei fehlenden Umgebungsvariablen."""
        mock_check_env.return_value = False
        
        runner = CliRunner()
        result = runner.invoke(download, ['@testgroup'])
        
        assert result.exit_code == 1
        mock_check_env.assert_called_once()
    
    @patch('src.telegram_audio_downloader.cli.check_env')
    @patch('src.telegram_audio_downloader.cli.init_db')
    @patch('src.telegram_audio_downloader.cli.AudioDownloader')
    def test_download_command_with_options(self, mock_downloader_class, mock_init_db, mock_check_env):
        """Test Download-Command mit Optionen."""
        mock_check_env.return_value = True
        mock_downloader = MagicMock()
        mock_downloader_class.return_value = mock_downloader
        
        with patch('src.telegram_audio_downloader.cli.asyncio.run') as mock_asyncio_run:
            mock_asyncio_run.return_value = {'completed': 0, 'failed': 0, 'files': [], 'errors': []}
            
            runner = CliRunner()
            result = runner.invoke(download, [
                '@testgroup',
                '--limit', '50',
                '--parallel', '5',
                '--output', '/tmp/downloads'
            ])
            
            assert result.exit_code == 0
            mock_downloader_class.assert_called_with(
                download_dir='/tmp/downloads',
                max_concurrent_downloads=5
            )


class TestSearchCommand:
    """Tests für den Search-Command."""
    
    @patch('src.telegram_audio_downloader.cli.init_db')
    @patch('src.telegram_audio_downloader.cli.AudioFile')
    def test_search_command_basic(self, mock_audio_file, mock_init_db):
        """Test grundlegender Search-Command."""
        mock_files = []
        for i in range(3):
            mock_file = MagicMock()
            mock_file.title = f"Test Song {i}"
            mock_file.performer = "Test Artist"
            mock_file.file_name = f"test_song_{i}.mp3"
            mock_file.file_size = 1024000
            mock_file.duration = 180
            mock_file.status = DownloadStatus.COMPLETED.value
            mock_files.append(mock_file)
        
        mock_audio_file.select.return_value.where.return_value.limit.return_value = mock_files
        
        with patch('src.telegram_audio_downloader.cli.console') as mock_console:
            runner = CliRunner()
            result = runner.invoke(search, ['test'])
            
            assert result.exit_code == 0
            mock_init_db.assert_called_once()
            mock_console.print.assert_called()
    
    @patch('src.telegram_audio_downloader.cli.init_db')
    @patch('src.telegram_audio_downloader.cli.AudioFile')
    def test_search_command_no_results(self, mock_audio_file, mock_init_db):
        """Test Search-Command ohne Ergebnisse."""
        mock_audio_file.select.return_value.where.return_value.limit.return_value = []
        
        with patch('src.telegram_audio_downloader.cli.console') as mock_console:
            runner = CliRunner()
            result = runner.invoke(search, ['nonexistent'])
            
            assert result.exit_code == 0
            mock_console.print.assert_called()


class TestPerformanceCommand:
    """Tests für den Performance-Command."""
    
    @patch('src.telegram_audio_downloader.cli.get_performance_monitor')
    def test_performance_command_report(self, mock_get_perf_monitor):
        """Test Performance-Report."""
        mock_perf_monitor = MagicMock()
        mock_get_perf_monitor.return_value = mock_perf_monitor
        
        mock_report = {
            'uptime_seconds': 3600,
            'downloads': {'completed': 10, 'failed': 2, 'success_rate': 83.3},
            'performance': {'downloads_per_minute': 0.2, 'average_speed_mbps': 2.5},
            'resources': {'memory_mb': 256, 'cpu_percent': 15.5, 'disk_free_gb': 50.8},
            'rate_limiting': {'current_rate': 1.0, 'tokens_available': 5.0}
        }
        mock_perf_monitor.get_performance_report.return_value = mock_report
        
        with patch('src.telegram_audio_downloader.cli.console') as mock_console:
            runner = CliRunner()
            result = runner.invoke(performance)
            
            assert result.exit_code == 0
            mock_perf_monitor.get_performance_report.assert_called_once()
    
    @patch('src.telegram_audio_downloader.cli.get_performance_monitor')
    def test_performance_command_cleanup(self, mock_get_perf_monitor):
        """Test Performance-Cleanup."""
        mock_perf_monitor = MagicMock()
        mock_get_perf_monitor.return_value = mock_perf_monitor
        
        mock_perf_monitor.memory_manager.cleanup_temp_files.return_value = 5
        
        with patch('src.telegram_audio_downloader.cli.console') as mock_console:
            runner = CliRunner()
            result = runner.invoke(performance, ['--cleanup'])
            
            assert result.exit_code == 0
            mock_perf_monitor.memory_manager.cleanup_temp_files.assert_called_once()


class TestStatsCommand:
    """Tests für den Stats-Command."""
    
    @patch('src.telegram_audio_downloader.cli.init_db')
    @patch('src.telegram_audio_downloader.cli.AudioFile')
    @patch('src.telegram_audio_downloader.cli.TelegramGroup')
    def test_stats_command_basic(self, mock_telegram_group, mock_audio_file, mock_init_db):
        """Test grundlegende Stats-Ausgabe."""
        mock_audio_file.select.return_value.count.return_value = 100
        mock_audio_file.select.return_value.where.return_value.count.side_effect = [80, 15, 5]
        mock_telegram_group.select.return_value.count.return_value = 5
        
        with patch('src.telegram_audio_downloader.cli.console') as mock_console:
            runner = CliRunner()
            result = runner.invoke(stats)
            
            assert result.exit_code == 0
            mock_init_db.assert_called_once()


class TestGroupsCommand:
    """Tests für den Groups-Command."""
    
    @patch('src.telegram_audio_downloader.cli.init_db')
    @patch('src.telegram_audio_downloader.cli.TelegramGroup')
    def test_groups_command_list(self, mock_telegram_group, mock_init_db):
        """Test Gruppen-Auflistung."""
        mock_groups = []
        for i in range(3):
            mock_group = MagicMock()
            mock_group.title = f"Test Group {i}"
            mock_group.username = f"testgroup{i}"
            mock_group.group_id = 12345 + i
            mock_groups.append(mock_group)
        
        mock_telegram_group.select.return_value = mock_groups
        
        with patch('src.telegram_audio_downloader.cli.console') as mock_console:
            runner = CliRunner()
            result = runner.invoke(groups)
            
            assert result.exit_code == 0
            mock_init_db.assert_called_once()


class TestMetadataCommand:
    """Tests für den Metadata-Command."""
    
    @patch('src.telegram_audio_downloader.cli.init_db')
    @patch('src.telegram_audio_downloader.cli.AudioFile')
    def test_metadata_command_analyze(self, mock_audio_file, mock_init_db):
        """Test Metadaten-Analyse."""
        mock_files = []
        for i in range(5):
            mock_file = MagicMock()
            mock_file.title = f"Song {i}" if i < 3 else None
            mock_file.performer = f"Artist {i}" if i < 2 else None
            mock_file.file_name = f"song_{i}.mp3"
            mock_files.append(mock_file)
        
        mock_audio_file.select.return_value.where.return_value = mock_files
        
        with patch('src.telegram_audio_downloader.cli.console') as mock_console:
            runner = CliRunner()
            result = runner.invoke(metadata, ['--analyze'])
            
            assert result.exit_code == 0
            mock_init_db.assert_called_once()


class TestCLIErrorHandling:
    """Tests für CLI-Fehlerbehandlung."""
    
    @patch('src.telegram_audio_downloader.cli.init_db')
    def test_database_connection_error(self, mock_init_db):
        """Test Datenbankverbindungsfehler."""
        mock_init_db.side_effect = Exception("Database connection failed")
        
        runner = CliRunner()
        result = runner.invoke(stats)
        
        assert result.exit_code == 1


# Fixtures
@pytest.fixture
def cli_runner():
    """CLI-Runner für Tests."""
    return CliRunner()


@pytest.fixture
def mock_audio_files():
    """Mock-Audiodateien für Tests."""
    files = []
    for i in range(10):
        mock_file = MagicMock()
        mock_file.id = i + 1
        mock_file.file_name = f"test_song_{i}.mp3"
        mock_file.title = f"Test Song {i}"
        mock_file.performer = f"Artist {i % 3}"
        mock_file.file_size = 1024000 + (i * 100000)
        mock_file.duration = 180 + (i * 30)
        mock_file.mime_type = "audio/mpeg"
        mock_file.status = DownloadStatus.COMPLETED.value
        files.append(mock_file)
    return files