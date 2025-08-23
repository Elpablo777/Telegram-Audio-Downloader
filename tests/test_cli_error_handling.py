"""
Tests für die CLI-Fehlerbehandlung des Telegram Audio Downloaders.
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


class TestCLIErrorHandling:
    """Tests für die Fehlerbehandlung in der CLI."""

    @patch('src.telegram_audio_downloader.cli.check_env')
    def test_download_command_auth_error(self, mock_check_env):
        """Test Download-Command bei Authentifizierungsfehler."""
        mock_check_env.return_value = True
        
        runner = CliRunner()
        
        # Test mit Authentifizierungsfehler
        with patch('src.telegram_audio_downloader.cli.init_db') as mock_init_db:
            mock_init_db.side_effect = AuthenticationError("Ungültige API-Zugangsdaten")
            
            result = runner.invoke(download, ['@testgroup'])
            assert result.exit_code == 1  # Sollte mit Fehler beenden

    @patch('src.telegram_audio_downloader.cli.check_env')
    def test_download_command_network_error(self, mock_check_env):
        """Test Download-Command bei Netzwerkfehler."""
        mock_check_env.return_value = True
        
        runner = CliRunner()
        
        # Test mit Netzwerkfehler
        with patch('src.telegram_audio_downloader.cli.init_db') as mock_init_db:
            mock_init_db.side_effect = NetworkError("Keine Internetverbindung")
            
            result = runner.invoke(download, ['@testgroup'])
            assert result.exit_code == 1  # Sollte mit Fehler beenden

    @patch('src.telegram_audio_downloader.cli.check_env')
    def test_download_command_database_error(self, mock_check_env):
        """Test Download-Command bei Datenbankfehler."""
        mock_check_env.return_value = True
        
        runner = CliRunner()
        
        # Test mit Datenbankfehler
        with patch('src.telegram_audio_downloader.cli.init_db') as mock_init_db:
            mock_init_db.side_effect = DatabaseError("Datenbankverbindungsfehler")
            
            result = runner.invoke(download, ['@testgroup'])
            assert result.exit_code == 1  # Sollte mit Fehler beenden

    @patch('src.telegram_audio_downloader.cli.check_env')
    @patch('src.telegram_audio_downloader.cli.init_db')
    def test_download_command_file_operation_error(self, mock_init_db, mock_check_env):
        """Test Download-Command bei Dateioperationsfehler."""
        mock_check_env.return_value = True
        
        runner = CliRunner()
        
        # Test mit Dateioperationsfehler
        with patch('src.telegram_audio_downloader.cli.AudioDownloader') as mock_downloader:
            mock_downloader_instance = MagicMock()
            mock_downloader.return_value = mock_downloader_instance
            
            with patch('src.telegram_audio_downloader.cli.asyncio.run') as mock_asyncio_run:
                mock_asyncio_run.side_effect = FileOperationError("Kann Ausgabeverzeichnis nicht erstellen")
                
                result = runner.invoke(download, ['@testgroup', '--output', '/invalid/path'])
                assert result.exit_code == 1  # Sollte mit Fehler beenden

    @patch('src.telegram_audio_downloader.cli.check_env')
    @patch('src.telegram_audio_downloader.cli.init_db')
    def test_download_command_download_error(self, mock_init_db, mock_check_env):
        """Test Download-Command bei Downloadfehler."""
        mock_check_env.return_value = True
        
        runner = CliRunner()
        
        # Test mit Downloadfehler
        with patch('src.telegram_audio_downloader.cli.AudioDownloader') as mock_downloader:
            mock_downloader_instance = MagicMock()
            mock_downloader.return_value = mock_downloader_instance
            
            with patch('src.telegram_audio_downloader.cli.asyncio.run') as mock_asyncio_run:
                mock_asyncio_run.side_effect = DownloadError("Download fehlgeschlagen")
                
                result = runner.invoke(download, ['@testgroup'])
                assert result.exit_code == 1  # Sollte mit Fehler beenden

    @patch('src.telegram_audio_downloader.cli.check_env')
    @patch('src.telegram_audio_downloader.cli.init_db')
    def test_download_command_telegram_api_error(self, mock_init_db, mock_check_env):
        """Test Download-Command bei Telegram-API-Fehler."""
        mock_check_env.return_value = True
        
        runner = CliRunner()
        
        # Test mit Telegram-API-Fehler
        with patch('src.telegram_audio_downloader.cli.AudioDownloader') as mock_downloader:
            mock_downloader_instance = MagicMock()
            mock_downloader.return_value = mock_downloader_instance
            
            with patch('src.telegram_audio_downloader.cli.asyncio.run') as mock_asyncio_run:
                mock_asyncio_run.side_effect = TelegramAPIError("Telegram API Fehler")
                
                result = runner.invoke(download, ['@testgroup'])
                assert result.exit_code == 1  # Sollte mit Fehler beenden

    def test_search_command_database_error(self):
        """Test Search-Command bei Datenbankfehler."""
        runner = CliRunner()
        
        # Test mit Datenbankfehler
        with patch('src.telegram_audio_downloader.cli.init_db') as mock_init_db:
            mock_init_db.side_effect = DatabaseError("Datenbankverbindungsfehler")
            
            result = runner.invoke(search, ['test'])
            assert result.exit_code == 1  # Sollte mit Fehler beenden

    def test_performance_command_database_error(self):
        """Test Performance-Command bei Datenbankfehler."""
        runner = CliRunner()
        
        # Test mit Datenbankfehler
        with patch('src.telegram_audio_downloader.cli.init_db') as mock_init_db:
            mock_init_db.side_effect = DatabaseError("Datenbankverbindungsfehler")
            
            result = runner.invoke(performance)
            assert result.exit_code == 1  # Sollte mit Fehler beenden


class TestCLIConfigurationErrors:
    """Tests für Konfigurationsfehler in der CLI."""

    def test_cli_missing_env_vars(self):
        """Test CLI bei fehlenden Umgebungsvariablen."""
        runner = CliRunner()
        
        # Test mit fehlenden Umgebungsvariablen
        with patch('src.telegram_audio_downloader.cli.check_env') as mock_check_env:
            mock_check_env.return_value = False
            
            result = runner.invoke(cli, ['--help'])
            # Der help-Befehl sollte trotzdem funktionieren
            assert result.exit_code == 0

    @patch('src.telegram_audio_downloader.cli.check_env')
    def test_cli_database_init_error(self, mock_check_env):
        """Test CLI bei Datenbankinitialisierungsfehler."""
        mock_check_env.return_value = True
        
        runner = CliRunner()
        
        # Test mit Datenbankinitialisierungsfehler
        with patch('src.telegram_audio_downloader.cli.init_db') as mock_init_db:
            mock_init_db.side_effect = DatabaseError("Datenbankinitialisierungsfehler")
            
            result = runner.invoke(cli, ['--help'])
            assert result.exit_code == 1  # Sollte mit Fehler beenden


if __name__ == '__main__':
    pytest.main([__file__])