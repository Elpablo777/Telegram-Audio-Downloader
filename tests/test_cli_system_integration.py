#!/usr/bin/env python3
"""
Tests für die CLI-Systemintegration - Telegram Audio Downloader
==============================================================

Tests für den neuen CLI-Befehl zum Anzeigen des Download-Verzeichnisses.
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest
import click
from click.testing import CliRunner

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from telegram_audio_downloader.cli import cli
from telegram_audio_downloader.config import Config

class TestCLISystemIntegration:
    """Tests für die CLI-Systemintegration."""
    
    @pytest.fixture
    def runner(self):
        """Erstellt einen CLI-Runner für die Tests."""
        return CliRunner()
    
    @pytest.fixture
    def temp_config(self):
        """Erstellt eine temporäre Konfiguration für die Tests."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_content = """
            api_id: "12345"
            api_hash: "test_hash"
            download_dir: "/tmp/test_downloads"
            max_concurrent_downloads: 3
            """
            f.write(config_content)
            f.flush()
            yield f.name
        os.unlink(f.name)
    
    @patch('telegram_audio_downloader.cli.AudioDownloader')
    @patch('telegram_audio_downloader.cli.init_db')
    def test_show_downloads_command(self, mock_init_db, mock_downloader_class, runner, temp_config):
        """Test für den show_downloads CLI-Befehl."""
        # Mock den Downloader
        mock_downloader_instance = Mock()
        mock_downloader_instance.show_downloads_in_file_manager.return_value = True
        mock_downloader_class.return_value = mock_downloader_instance
        
        # Mock die Datenbank-Initialisierung
        mock_init_db.return_value = None
        
        # Führe den CLI-Befehl aus
        result = runner.invoke(cli, ['--config', temp_config, 'show-downloads'])
        
        # Überprüfe das Ergebnis
        assert result.exit_code == 0
        assert "Download-Verzeichnis" in result.output
        assert "im Dateimanager geöffnet" in result.output
        
        # Überprüfe, ob der Downloader korrekt initialisiert wurde
        mock_downloader_class.assert_called_once()
        mock_downloader_instance.show_downloads_in_file_manager.assert_called_once()
    
    @patch('telegram_audio_downloader.cli.AudioDownloader')
    @patch('telegram_audio_downloader.cli.init_db')
    @patch('telegram_audio_downloader.cli.Path.exists')
    def test_show_downloads_command_directory_not_exists(self, mock_exists, mock_init_db, mock_downloader_class, runner, temp_config):
        """Test für den show_downloads CLI-Befehl wenn das Verzeichnis nicht existiert."""
        # Mock dass das Verzeichnis nicht existiert
        mock_exists.return_value = False
        
        # Mock den Downloader
        mock_downloader_instance = Mock()
        mock_downloader_instance.show_downloads_in_file_manager.return_value = True
        mock_downloader_class.return_value = mock_downloader_instance
        
        # Mock die Datenbank-Initialisierung
        mock_init_db.return_value = None
        
        # Führe den CLI-Befehl aus
        result = runner.invoke(cli, ['--config', temp_config, 'show-downloads'], input='n')
        
        # Überprüfe das Ergebnis
        assert result.exit_code == 0
        assert "existiert nicht" in result.output
    
    @patch('telegram_audio_downloader.cli.AudioDownloader')
    @patch('telegram_audio_downloader.cli.init_db')
    def test_show_downloads_command_with_custom_output(self, mock_init_db, mock_downloader_class, runner, temp_config):
        """Test für den show_downloads CLI-Befehl mit benutzerdefiniertem Ausgabeverzeichnis."""
        # Mock den Downloader
        mock_downloader_instance = Mock()
        mock_downloader_instance.show_downloads_in_file_manager.return_value = True
        mock_downloader_class.return_value = mock_downloader_instance
        
        # Mock die Datenbank-Initialisierung
        mock_init_db.return_value = None
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Führe den CLI-Befehl aus
            result = runner.invoke(cli, ['--config', temp_config, 'show-downloads', '--output', temp_dir])
            
            # Überprüfe das Ergebnis
            assert result.exit_code == 0
            assert "Download-Verzeichnis" in result.output
            assert "im Dateimanager geöffnet" in result.output
            
            # Überprüfe, ob der Downloader mit dem richtigen Verzeichnis initialisiert wurde
            mock_downloader_class.assert_called_once()
            mock_downloader_instance.show_downloads_in_file_manager.assert_called_once()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])