#!/usr/bin/env python3
"""
Erweiterte Fehlerbehandlung Tests - Telegram Audio Downloader
==========================================================

Tests für das erweiterte Fehlerbehandlungssystem.
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from telegram_audio_downloader.enhanced_error_handling import (
    get_error_handler,
    BaseError,
    NetworkError,
    FilesystemError,
    APIError,
    ValidationError,
    ConfigurationError,
    AuthenticationError,
    DatabaseError,
    DownloadError,
    ErrorCategory,
    error_context
)


class TestErrorCategories:
    """Tests für Fehlerkategorien."""
    
    def test_error_category_constants(self):
        """Test Fehlerkategorie-Konstanten."""
        assert ErrorCategory.NETWORK == "network"
        assert ErrorCategory.FILESYSTEM == "filesystem"
        assert ErrorCategory.API == "api"
        assert ErrorCategory.VALIDATION == "validation"
        assert ErrorCategory.CONFIGURATION == "configuration"
        assert ErrorCategory.AUTHENTICATION == "authentication"
        assert ErrorCategory.DATABASE == "database"
        assert ErrorCategory.DOWNLOAD == "download"
        assert ErrorCategory.UNKNOWN == "unknown"


class TestErrorClasses:
    """Tests für Fehlerklassen."""
    
    def test_base_error(self):
        """Test Basisklasse für Fehler."""
        error = BaseError("Test error message")
        assert error.message == "Test error message"
        assert error.category == ErrorCategory.UNKNOWN
        assert error.context == {}
        assert error.error_code is None
    
    def test_network_error(self):
        """Test Netzwerkfehler."""
        context = {"url": "http://test.com"}
        error = NetworkError("Network error", context)
        assert error.message == "Network error"
        assert error.category == ErrorCategory.NETWORK
        assert error.context == context
    
    def test_filesystem_error(self):
        """Test Dateisystemfehler."""
        context = {"path": "/test/path"}
        error = FilesystemError("Filesystem error", context)
        assert error.message == "Filesystem error"
        assert error.category == ErrorCategory.FILESYSTEM
        assert error.context == context
    
    def test_api_error(self):
        """Test API-Fehler."""
        context = {"endpoint": "/api/test"}
        error = APIError("API error", context)
        assert error.message == "API error"
        assert error.category == ErrorCategory.API
        assert error.context == context
    
    def test_validation_error(self):
        """Test Validierungsfehler."""
        context = {"field": "test_field"}
        error = ValidationError("Validation error", context)
        assert error.message == "Validation error"
        assert error.category == ErrorCategory.VALIDATION
        assert error.context == context
    
    def test_configuration_error(self):
        """Test Konfigurationsfehler."""
        context = {"config_key": "test_key"}
        error = ConfigurationError("Configuration error", context)
        assert error.message == "Configuration error"
        assert error.category == ErrorCategory.CONFIGURATION
        assert error.context == context
    
    def test_authentication_error(self):
        """Test Authentifizierungsfehler."""
        context = {"user": "test_user"}
        error = AuthenticationError("Authentication error", context)
        assert error.message == "Authentication error"
        assert error.category == ErrorCategory.AUTHENTICATION
        assert error.context == context
    
    def test_database_error(self):
        """Test Datenbankfehler."""
        context = {"table": "test_table"}
        error = DatabaseError("Database error", context)
        assert error.message == "Database error"
        assert error.category == ErrorCategory.DATABASE
        assert error.context == context
    
    def test_download_error(self):
        """Test Download-Fehler."""
        context = {"file": "test_file.mp3"}
        error = DownloadError("Download error", context)
        assert error.message == "Download error"
        assert error.category == ErrorCategory.DOWNLOAD
        assert error.context == context


class TestErrorHandler:
    """Tests für den ErrorHandler."""
    
    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Setup test environment."""
        # Setze den globalen ErrorHandler zurück
        from telegram_audio_downloader.enhanced_error_handling import _error_handler
        if _error_handler is not None:
            _error_handler.notification_handlers.clear()
            _error_handler.auto_recovery_strategies.clear()
        
        yield
        
        # Setze den globalen ErrorHandler zurück
        from telegram_audio_downloader.enhanced_error_handling import _error_handler
        if _error_handler is not None:
            _error_handler.notification_handlers.clear()
            _error_handler.auto_recovery_strategies.clear()
    
    def test_error_handler_creation(self):
        """Test Erstellung des ErrorHandlers."""
        handler = get_error_handler()
        assert handler is not None
        assert len(handler.notification_handlers) == 0
        assert len(handler.auto_recovery_strategies) == 0
    
    def test_add_notification_handler(self):
        """Test Hinzufügen von Benachrichtigungshandlern."""
        handler = get_error_handler()
        
        # Erstelle einen Mock-Handler
        mock_handler = Mock()
        
        # Füge Handler hinzu
        handler.add_notification_handler(mock_handler)
        
        # Prüfe, ob Handler hinzugefügt wurde
        assert len(handler.notification_handlers) == 1
        assert handler.notification_handlers[0] == mock_handler
    
    def test_add_auto_recovery_strategy(self):
        """Test Hinzufügen von Auto-Recovery-Strategien."""
        handler = get_error_handler()
        
        # Erstelle eine Mock-Strategie
        mock_strategy = Mock()
        
        # Füge Strategie hinzu
        handler.add_auto_recovery_strategy(ErrorCategory.NETWORK, mock_strategy)
        
        # Prüfe, ob Strategie hinzugefügt wurde
        assert len(handler.auto_recovery_strategies) == 1
        assert handler.auto_recovery_strategies[ErrorCategory.NETWORK] == mock_strategy
    
    @pytest.mark.asyncio
    @patch('telegram_audio_downloader.enhanced_error_handling.asyncio.create_task')
    def test_handle_error(self, mock_create_task):
        """Test Fehlerbehandlung."""
        # Mock die asynchrone Funktionalität
        mock_create_task.return_value = None
        
        handler = get_error_handler()
        
        # Erstelle einen Testfehler
        error = DownloadError("Test download error", {"file": "test.mp3"})
        
        # Handle den Fehler
        handler.handle_error(error, "test_context")
        
        # Da wir keine Ausnahme erwarten, ist der Test erfolgreich
        assert True
    
    def test_set_error_context(self):
        """Test Setzen von Fehlerkontext."""
        handler = get_error_handler()
        
        # Setze Kontext
        handler.set_error_context(user_action="test_action", user_id="123")
        
        # Prüfe Kontext
        context = handler.get_error_context()
        assert context["user_action"] == "test_action"
        assert context["user_id"] == "123"
    
    def test_error_context_isolation(self):
        """Test Isolation des Fehlerkontexts."""
        handler1 = get_error_handler()
        handler2 = get_error_handler()
        
        # Setze Kontext für Handler 1
        handler1.set_error_context(test_key="value1")
        
        # Prüfe, dass Handler 2 den gleichen Kontext hat (gleiche globale Instanz)
        context2 = handler2.get_error_context()
        assert context2["test_key"] == "value1"


class TestErrorConversion:
    """Tests für Fehlerkonvertierung."""
    
    def test_convert_file_not_found_error(self):
        """Test Konvertierung von FileNotFoundError."""
        handler = get_error_handler()
        
        # Erstelle eine FileNotFoundError
        original_error = FileNotFoundError("File not found")
        
        # Konvertiere den Fehler
        converted_error = handler._convert_exception(original_error, "test_func")
        
        # Prüfe, ob es ein FilesystemError ist
        assert isinstance(converted_error, FilesystemError)
        assert converted_error.message == "File not found"
        assert "original_exception" in converted_error.context
    
    def test_convert_permission_error(self):
        """Test Konvertierung von PermissionError."""
        handler = get_error_handler()
        
        # Erstelle eine PermissionError
        original_error = PermissionError("Permission denied")
        
        # Konvertiere den Fehler
        converted_error = handler._convert_exception(original_error, "test_func")
        
        # Prüfe, ob es ein FilesystemError ist
        assert isinstance(converted_error, FilesystemError)
        assert converted_error.message == "Permission denied"
    
    def test_convert_connection_error(self):
        """Test Konvertierung von ConnectionError."""
        handler = get_error_handler()
        
        # Erstelle eine ConnectionError
        original_error = ConnectionError("Connection failed")
        
        # Konvertiere den Fehler
        converted_error = handler._convert_exception(original_error, "test_func")
        
        # Prüfe, ob es ein NetworkError ist
        assert isinstance(converted_error, NetworkError)
        assert converted_error.message == "Connection failed"
    
    def test_convert_timeout_error(self):
        """Test Konvertierung von TimeoutError."""
        handler = get_error_handler()
        
        # Erstelle eine TimeoutError
        original_error = TimeoutError("Timeout occurred")
        
        # Konvertiere den Fehler
        converted_error = handler._convert_exception(original_error, "test_func")
        
        # Prüfe, ob es ein NetworkError ist
        assert isinstance(converted_error, NetworkError)
        assert converted_error.message == "Timeout occurred"
    
    def test_convert_value_error(self):
        """Test Konvertierung von ValueError."""
        handler = get_error_handler()
        
        # Erstelle eine ValueError
        original_error = ValueError("Invalid value")
        
        # Konvertiere den Fehler
        converted_error = handler._convert_exception(original_error, "test_func")
        
        # Prüfe, ob es ein ValidationError ist
        assert isinstance(converted_error, ValidationError)
        assert converted_error.message == "Invalid value"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])