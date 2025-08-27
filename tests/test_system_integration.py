#!/usr/bin/env python3
"""
Tests für die Systemintegration - Telegram Audio Downloader
==========================================================

Tests für die erweiterte Systemintegration mit Benachrichtigungen,
Shell-Integration, Dateimanager und Medienbibliotheken.
"""

import os
import sys
import tempfile
import platform
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from telegram_audio_downloader.system_integration import (
    SystemNotifier, SystemNotification, ShellIntegration, 
    FileManagerIntegration, MediaLibraryIntegration,
    send_system_notification, add_to_system_path, create_shell_alias,
    show_in_default_file_manager, add_to_default_media_library
)

class TestSystemNotifier:
    """Tests für den Systembenachrichtigungsmanager."""
    
    def test_system_notification_creation(self):
        """Test erstellt eine Systembenachrichtigung."""
        notification = SystemNotification(
            title="Test",
            message="Test message",
            icon="/path/to/icon.png",
            timeout=3000
        )
        
        assert notification.title == "Test"
        assert notification.message == "Test message"
        assert notification.icon == "/path/to/icon.png"
        assert notification.timeout == 3000
    
    @patch('telegram_audio_downloader.system_integration.platform.system')
    def test_notification_backend_detection_windows(self, mock_system):
        """Test erkennt Windows-Benachrichtigungs-Backend."""
        mock_system.return_value = "Windows"
        
        notifier = SystemNotifier()
        assert notifier.platform == "windows"
        # Auf Windows sollte das Backend erkannt werden
        assert notifier.notification_backend in ["windows", "none"]
    
    @patch('telegram_audio_downloader.system_integration.platform.system')
    @patch('telegram_audio_downloader.system_integration.subprocess.run')
    def test_is_tool_available(self, mock_run, mock_system):
        """Test prüft, ob ein Tool verfügbar ist."""
        mock_system.return_value = "Linux"
        mock_run.return_value = Mock()
        
        notifier = SystemNotifier()
        # Mock das System als Linux
        notifier.platform = "linux"
        result = notifier._is_tool_available("notify-send")
        
        assert isinstance(result, bool)
        # Prüfe, ob subprocess.run aufgerufen wurde
        assert mock_run.called
    
    @patch('telegram_audio_downloader.system_integration.platform.system')
    def test_send_notification_unavailable_backend(self, mock_system):
        """Test sendet Benachrichtigung mit nicht verfügbarem Backend."""
        mock_system.return_value = "Unknown"
        
        notifier = SystemNotifier()
        notifier.notification_backend = "none"
        
        notification = SystemNotification(
            title="Test",
            message="Test message"
        )
        
        result = notifier.send_notification(notification)
        assert result is False  # Kein Backend verfügbar

class TestShellIntegration:
    """Tests für die Shell-Integration."""
    
    def test_shell_detection_windows(self):
        """Test erkennt Windows-Shell."""
        with patch('sys.platform', 'win32'):
            shell_integration = ShellIntegration()
            assert shell_integration.shell == "powershell"
    
    def test_shell_detection_unix(self):
        """Test erkennt Unix-Shells."""
        with patch.dict(os.environ, {'SHELL': '/bin/bash'}):
            shell_integration = ShellIntegration()
            assert shell_integration.shell == "bash"
    
    @patch('telegram_audio_downloader.system_integration.Path.home')
    def test_get_shell_config_file_bash(self, mock_home):
        """Test erhält Bash-Konfigurationsdatei."""
        mock_home.return_value = Path("/home/test")
        
        shell_integration = ShellIntegration()
        shell_integration.shell = "bash"
        config_file = shell_integration._get_shell_config_file()
        
        assert config_file == Path("/home/test/.bashrc")
    
    def test_create_alias_windows(self):
        """Test erstellt PowerShell-Alias."""
        with patch('sys.platform', 'win32'):
            with patch('builtins.open', MagicMock()):
                shell_integration = ShellIntegration()
                result = shell_integration.create_alias("tad", "telegram-audio-downloader")
                assert isinstance(result, bool)

class TestFileManagerIntegration:
    """Tests für die Dateimanager-Integration."""
    
    @patch('telegram_audio_downloader.system_integration.platform.system')
    def test_platform_detection(self, mock_system):
        """Test erkennt die Plattform."""
        mock_system.return_value = "Windows"
        file_manager = FileManagerIntegration()
        assert file_manager.platform == "windows"
    
    def test_is_tool_available(self):
        """Test prüft Tool-Verfügbarkeit."""
        file_manager = FileManagerIntegration()
        # Dies sollte ohne Fehler ausgeführt werden
        result = file_manager._is_tool_available("python")
        assert isinstance(result, bool)

class TestMediaLibraryIntegration:
    """Tests für die Medienbibliothek-Integration."""
    
    @patch('telegram_audio_downloader.system_integration.platform.system')
    def test_platform_detection(self, mock_system):
        """Test erkennt die Plattform."""
        mock_system.return_value = "Darwin"
        media_library = MediaLibraryIntegration()
        assert media_library.platform == "darwin"
    
    def test_is_tool_available(self):
        """Test prüft Tool-Verfügbarkeit."""
        media_library = MediaLibraryIntegration()
        # Dies sollte ohne Fehler ausgeführt werden
        result = media_library._is_tool_available("python")
        assert isinstance(result, bool)

class TestGlobalFunctions:
    """Tests für die globalen Hilfsfunktionen."""
    
    @patch('telegram_audio_downloader.system_integration.get_system_notifier')
    def test_send_system_notification(self, mock_get_notifier):
        """Test sendet Systembenachrichtigung."""
        mock_notifier = Mock()
        mock_notifier.send_notification.return_value = True
        mock_get_notifier.return_value = mock_notifier
        
        result = send_system_notification("Test", "Message")
        assert result is True
        mock_notifier.send_notification.assert_called_once()
    
    @patch('telegram_audio_downloader.system_integration.get_shell_integration')
    def test_add_to_system_path(self, mock_get_shell):
        """Test fügt Pfad zum System hinzu."""
        mock_shell = Mock()
        mock_shell.add_to_path.return_value = True
        mock_get_shell.return_value = mock_shell
        
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir)
            result = add_to_system_path(path)
            assert result is True
            mock_shell.add_to_path.assert_called_once_with(path)
    
    @patch('telegram_audio_downloader.system_integration.get_file_manager_integration')
    def test_show_in_default_file_manager(self, mock_get_file_manager):
        """Test zeigt Datei im Dateimanager an."""
        mock_file_manager = Mock()
        mock_file_manager.show_in_file_manager.return_value = True
        mock_get_file_manager.return_value = mock_file_manager
        
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir)
            result = show_in_default_file_manager(path)
            assert result is True
            mock_file_manager.show_in_file_manager.assert_called_once_with(path)
    
    @patch('telegram_audio_downloader.system_integration.get_media_library_integration')
    def test_add_to_default_media_library(self, mock_get_media_library):
        """Test fügt Datei zur Medienbibliothek hinzu."""
        mock_media_library = Mock()
        mock_media_library.add_to_media_library.return_value = True
        mock_get_media_library.return_value = mock_media_library
        
        with tempfile.NamedTemporaryFile() as temp_file:
            path = Path(temp_file.name)
            result = add_to_default_media_library(path)
            assert result is True
            mock_media_library.add_to_media_library.assert_called_once_with(path)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])