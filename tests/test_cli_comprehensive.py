#!/usr/bin/env python3
"""
Umfassende CLI-Tests - Telegram Audio Downloader
==============================================

Umfassende Tests für alle CLI-Befehle und -Optionen.
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest
from click.testing import CliRunner

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from telegram_audio_downloader.cli import cli, download, search, performance, config
from telegram_audio_downloader.models import AudioFile, DownloadStatus


class TestCLIComprehensive:
    """Umfassende Tests für die CLI."""
    
    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Setup test environment."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp(prefix="cli_test_")
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
    
    def test_cli_main_help(self):
        """Test Haupt-Hilfe der CLI."""
        result = self.runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert "Usage:" in result.output
        assert "download" in result.output
        assert "search" in result.output
        assert "performance" in result.output
        assert "config" in result.output
    
    def test_cli_version(self):
        """Test CLI Versionsanzeige."""
        result = self.runner.invoke(cli, ['--version'])
        assert result.exit_code == 0
        # Version sollte angezeigt werden (kann leer sein in Tests)
    
    @patch('telegram_audio_downloader.cli.check_env')
    @patch('telegram_audio_downloader.cli.init_db')
    def test_download_command_all_options(self, mock_init_db, mock_check_env):
        """Test Download-Command mit allen Optionen."""
        mock_check_env.return_value = True
        
        # Test mit allen verfügbaren Optionen
        with patch('telegram_audio_downloader.cli.AudioDownloader') as mock_downloader:
            mock_downloader_instance = MagicMock()
            mock_downloader.return_value = mock_downloader_instance
            
            with patch('telegram_audio_downloader.cli.asyncio.run') as mock_asyncio_run:
                mock_asyncio_run.return_value = {
                    'completed': 5,
                    'failed': 0,
                    'files': ['file1.mp3', 'file2.mp3'],
                    'errors': []
                }
                
                result = self.runner.invoke(download, [
                    '@testgroup',
                    '--limit', '10',
                    '--parallel', '3',
                    '--output', str(self.download_dir),
                    '--resume'
                ])
                
                assert result.exit_code == 0
    
    def test_download_command_invalid_group(self):
        """Test Download-Command mit ungültiger Gruppe."""
        result = self.runner.invoke(download, [''])
        assert result.exit_code != 0
        assert "Group identifier is required" in result.output
    
    def test_download_command_invalid_limit_range(self):
        """Test Download-Command mit ungültigem Limit-Bereich."""
        result = self.runner.invoke(download, ['@testgroup', '--limit', '-1'])
        assert result.exit_code != 0
        
        result = self.runner.invoke(download, ['@testgroup', '--limit', '0'])
        assert result.exit_code != 0
    
    def test_download_command_invalid_parallel_range(self):
        """Test Download-Command mit ungültiger paralleler Anzahl."""
        result = self.runner.invoke(download, ['@testgroup', '--parallel', '0'])
        assert result.exit_code != 0
        
        result = self.runner.invoke(download, ['@testgroup', '--parallel', '15'])
        assert result.exit_code != 0
    
    def test_search_command_help(self):
        """Test Search-Command Hilfe."""
        result = self.runner.invoke(search, ['--help'])
        assert result.exit_code == 0
        assert "Usage:" in result.output
    
    def test_search_command_with_query(self):
        """Test Search-Command mit Suchanfrage."""
        # Erstelle Testdaten
        from telegram_audio_downloader.database import init_db, reset_db
        reset_db()
        init_db()
        
        # Füge Testdaten hinzu
        AudioFile.create(
            file_id="test_file_1",
            file_name="test_song.mp3",
            file_size=1048576,
            mime_type="audio/mpeg",
            title="Test Song",
            performer="Test Artist",
            status=DownloadStatus.COMPLETED.value
        )
        
        result = self.runner.invoke(search, ['test'])
        assert result.exit_code == 0
        # Suchergebnisse sollten angezeigt werden
    
    def test_search_command_with_filters(self):
        """Test Search-Command mit Filtern."""
        result = self.runner.invoke(search, [
            'test',
            '--min-size', '1MB',
            '--max-size', '10MB',
            '--format', 'mp3'
        ])
        assert result.exit_code == 0
    
    def test_search_command_invalid_size_format(self):
        """Test Search-Command mit ungültigem Größenformat."""
        result = self.runner.invoke(search, ['test', '--min-size', 'invalid'])
        assert result.exit_code != 0
    
    def test_performance_command_help(self):
        """Test Performance-Command Hilfe."""
        result = self.runner.invoke(performance, ['--help'])
        assert result.exit_code == 0
        assert "Usage:" in result.output
    
    def test_performance_command_with_options(self):
        """Test Performance-Command mit Optionen."""
        with patch('telegram_audio_downloader.cli.get_performance_monitor') as mock_get_perf_monitor:
            mock_perf_monitor = MagicMock()
            mock_get_perf_monitor.return_value = mock_perf_monitor
            mock_perf_monitor.memory_manager.cleanup_temp_files.return_value = 5
            
            result = self.runner.invoke(performance, ['--cleanup'])
            assert result.exit_code == 0
    
    def test_config_command_help(self):
        """Test Config-Command Hilfe."""
        result = self.runner.invoke(config, ['--help'])
        assert result.exit_code == 0
        assert "Usage:" in result.output
    
    def test_config_command_show(self):
        """Test Config-Command Anzeige."""
        result = self.runner.invoke(config, ['show'])
        assert result.exit_code == 0
        # Konfiguration sollte angezeigt werden
    
    def test_config_command_set(self):
        """Test Config-Command Setzen."""
        result = self.runner.invoke(config, ['set', 'test_key', 'test_value'])
        assert result.exit_code == 0
        # Wert sollte gesetzt werden (in Tests wird dies gemockt)
    
    def test_invalid_command(self):
        """Test ungültiger Befehl."""
        result = self.runner.invoke(cli, ['invalid_command'])
        assert result.exit_code != 0
        assert "No such command" in result.output or "is not a valid" in result.output


class TestCLIOutputFormatting:
    """Tests für CLI-Ausgabeformatierungen."""
    
    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Setup test environment."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp(prefix="cli_output_test_")
        yield
        
        # Cleanup
        import shutil
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def test_error_output_formatting(self):
        """Test Formatierung von Fehlerausgaben."""
        result = self.runner.invoke(download, [''])
        assert result.exit_code != 0
        # Fehler sollten in einem bestimmten Format ausgegeben werden
    
    def test_success_output_formatting(self):
        """Test Formatierung von Erfolgsausgaben."""
        with patch('telegram_audio_downloader.cli.check_env') as mock_check_env:
            mock_check_env.return_value = True
            
            with patch('telegram_audio_downloader.cli.init_db'):
                with patch('telegram_audio_downloader.cli.AudioDownloader') as mock_downloader:
                    mock_downloader_instance = MagicMock()
                    mock_downloader.return_value = mock_downloader_instance
                    
                    with patch('telegram_audio_downloader.cli.asyncio.run') as mock_asyncio_run:
                        mock_asyncio_run.return_value = {
                            'completed': 3,
                            'failed': 1,
                            'files': ['file1.mp3', 'file2.mp3', 'file3.mp3'],
                            'errors': ['Download failed for file4.mp3']
                        }
                        
                        result = self.runner.invoke(download, ['@testgroup'])
                        assert result.exit_code == 0
                        # Erfolgsausgabe sollte formatiert sein


class TestCLIInteractiveInput:
    """Tests für interaktive CLI-Eingaben."""
    
    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Setup test environment."""
        self.runner = CliRunner()
        yield
    
    def test_interactive_prompt_confirmation(self):
        """Test interaktive Bestätigungsabfragen."""
        # Dieser Test ist schwierig ohne echte Interaktivität
        # In der Regel würden solche Tests mit input() mocking erfolgen
        pass
    
    def test_interactive_prompt_choices(self):
        """Test interaktive Auswahlmöglichkeiten."""
        # Ähnlich wie oben, benötigt input() mocking
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])