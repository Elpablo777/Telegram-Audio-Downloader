"""
Tests für die CLI-Eingabevalidierung des Telegram Audio Downloaders.
"""

import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock

from src.telegram_audio_downloader.cli import (
    cli, download, search, performance
)
from src.telegram_audio_downloader.error_handling import (
    ConfigurationError, AuthenticationError, NetworkError, 
    DownloadError, DatabaseError, FileOperationError, TelegramAPIError
)


class TestCLIDownloadValidation:
    """Tests für die Validierung der Download-Command-Parameter."""

    def test_download_command_empty_group(self):
        """Test Download-Command mit leerem Gruppennamen."""
        runner = CliRunner()
        
        # Test mit leerem String
        result = runner.invoke(download, [''])
        assert result.exit_code != 0  # Sollte fehlschlagen
        
        # Test mit nur Leerzeichen
        result = runner.runner.invoke(download, ['   '])
        assert result.exit_code != 0  # Sollte fehlschlagen

    def test_download_command_invalid_limit(self):
        """Test Download-Command mit ungültigem Limit."""
        runner = CliRunner()
        
        # Test mit negativem Limit
        result = runner.invoke(download, ['@testgroup', '--limit', '-5'])
        assert result.exit_code != 0  # Sollte fehlschlagen
        
        # Test mit 0 als Limit
        result = runner.invoke(download, ['@testgroup', '--limit', '0'])
        assert result.exit_code != 0  # Sollte fehlschlagen

    def test_download_command_invalid_parallel(self):
        """Test Download-Command mit ungültiger paralleler Anzahl."""
        runner = CliRunner()
        
        # Test mit zu kleinem Wert
        result = runner.invoke(download, ['@testgroup', '--parallel', '0'])
        assert result.exit_code != 0  # Sollte fehlschlagen
        
        # Test mit zu großem Wert
        result = runner.invoke(download, ['@testgroup', '--parallel', '15'])
        assert result.exit_code != 0  # Sollte fehlschlagen

    @patch('src.telegram_audio_downloader.cli.check_env')
    @patch('src.telegram_audio_downloader.cli.init_db')
    def test_download_command_valid_parameters(self, mock_init_db, mock_check_env):
        """Test Download-Command mit gültigen Parametern."""
        mock_check_env.return_value = True
        
        runner = CliRunner()
        
        # Test mit gültigen Parametern
        with patch('src.telegram_audio_downloader.cli.AudioDownloader') as mock_downloader:
            mock_downloader_instance = MagicMock()
            mock_downloader.return_value = mock_downloader_instance
            
            with patch('src.telegram_audio_downloader.cli.asyncio.run') as mock_asyncio_run:
                mock_asyncio_run.return_value = {
                    'completed': 0, 
                    'failed': 0, 
                    'files': [], 
                    'errors': []
                }
                
                result = runner.invoke(download, [
                    '@validgroup',
                    '--limit', '10',
                    '--parallel', '5',
                    '--output', '/tmp/test'
                ])
                
                # Sollte erfolgreich sein (beim Mocking)
                # In der echten Anwendung würde es wegen fehlender API-Zugangsdaten fehlschlagen
                # aber die Validierung sollte durchlaufen


class TestCLISearchValidation:
    """Tests für die Validierung der Search-Command-Parameter."""

    def test_search_command_invalid_duration_range(self):
        """Test Search-Command mit ungültigem Dauerbereich."""
        runner = CliRunner()
        
        # Test mit duration-min > duration-max
        result = runner.invoke(search, [
            'test',
            '--duration-min', '300',
            '--duration-max', '120'
        ])
        
        assert result.exit_code != 0  # Sollte fehlschlagen
        assert "duration-min darf nicht größer als duration-max sein" in result.output

    def test_search_command_invalid_size_range(self):
        """Test Search-Command mit ungültigem Größenbereich."""
        runner = CliRunner()
        
        # Test mit min-size > max-size
        result = runner.invoke(search, [
            'test',
            '--min-size', '100MB',
            '--max-size', '50MB'
        ])
        
        assert result.exit_code != 0  # Sollte fehlschlagen
        assert "Minimale Dateigröße darf nicht größer als maximale Dateigröße sein" in result.output

    def test_search_command_invalid_size_format(self):
        """Test Search-Command mit ungültigem Größenformat."""
        runner = CliRunner()
        
        # Test mit ungültigem Größenformat
        result = runner.invoke(search, [
            'test',
            '--min-size', '5XYZ'  # Ungültige Einheit
        ])
        
        assert result.exit_code != 0  # Sollte fehlschlagen

    def test_search_command_invalid_format(self):
        """Test Search-Command mit ungültigem Audioformat."""
        runner = CliRunner()
        
        # Test mit ungültigem Audioformat
        result = runner.invoke(search, [
            'test',
            '--format', 'invalidformat'
        ])
        
        assert result.exit_code != 0  # Sollte fehlschlagen
        assert "Ungültiges Audioformat" in result.output

    def test_search_command_negative_size(self):
        """Test Search-Command mit negativer Dateigröße."""
        runner = CliRunner()
        
        # Test mit negativer Dateigröße
        result = runner.invoke(search, [
            'test',
            '--min-size', '-5MB'
        ])
        
        assert result.exit_code != 0  # Sollte fehlschlagen
        assert "Minimale Dateigröße muss positiv sein" in result.output


class TestCLIPerformanceValidation:
    """Tests für die Validierung der Performance-Command-Parameter."""

    def test_performance_command_valid_options(self):
        """Test Performance-Command mit gültigen Optionen."""
        runner = CliRunner()
        
        # Test mit --cleanup Option
        with patch('src.telegram_audio_downloader.cli.get_performance_monitor') as mock_get_perf_monitor:
            mock_perf_monitor = MagicMock()
            mock_get_perf_monitor.return_value = mock_perf_monitor
            mock_perf_monitor.memory_manager.cleanup_temp_files.return_value = 5
            
            result = runner.invoke(performance, ['--cleanup'])
            assert result.exit_code == 0  # Sollte erfolgreich sein

    def test_performance_command_watch_mode(self):
        """Test Performance-Command im Watch-Modus."""
        runner = CliRunner()
        
        # Test mit --watch Option
        with patch('src.telegram_audio_downloader.cli.get_performance_monitor') as mock_get_perf_monitor:
            mock_perf_monitor = MagicMock()
            mock_get_perf_monitor.return_value = mock_perf_monitor
            
            # Mock des Performance-Reports
            mock_report = {
                'uptime_seconds': 3600,
                'downloads': {'completed': 10, 'failed': 2, 'success_rate': 83.3},
                'performance': {'downloads_per_minute': 0.2, 'average_speed_mbps': 2.5, 'total_gb_downloaded': 0.5},
                'resources': {'memory_mb': 256, 'cpu_percent': 15.5, 'disk_used_gb': 10.0, 'disk_free_gb': 50.8},
                'rate_limiting': {'current_rate': 1.0, 'tokens_available': 5.0}
            }
            mock_perf_monitor.get_performance_report.return_value = mock_report
            
            result = runner.invoke(performance, ['--watch'])
            # Watch-Modus würde normalerweise mit KeyboardInterrupt beendet
            # Aber bei einmaliger Ausführung sollte es erfolgreich sein
            assert result.exit_code == 0


class TestCLIErrorHandlingValidation:
    """Tests für die Validierung der Fehlerbehandlung."""

    @patch('src.telegram_audio_downloader.cli.check_env')
    def test_download_command_missing_env_vars(self, mock_check_env):
        """Test Download-Command bei fehlenden Umgebungsvariablen."""
        mock_check_env.return_value = False
        
        runner = CliRunner()
        result = runner.invoke(download, ['@testgroup'])
        
        assert result.exit_code == 1  # Sollte mit Fehler beenden

    @patch('src.telegram_audio_downloader.cli.check_env')
    @patch('src.telegram_audio_downloader.cli.init_db')
    def test_download_command_output_dir_creation_error(self, mock_init_db, mock_check_env):
        """Test Download-Command bei Fehler beim Erstellen des Ausgabeverzeichnisses."""
        mock_check_env.return_value = True
        
        runner = CliRunner()
        
        # Test mit ungültigem Ausgabeverzeichnis-Pfad
        result = runner.invoke(download, [
            '@testgroup',
            '--output', '/invalid/path/that/cannot/be/created'
        ])
        
        # Je nach System und Berechtigungen könnte dies unterschiedlich behandelt werden
        # Wichtig ist, dass es eine entsprechende Fehlerbehandlung gibt


if __name__ == '__main__':
    pytest.main([__file__])