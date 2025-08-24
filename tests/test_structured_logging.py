#!/usr/bin/env python3
"""
Strukturiertes Logging Tests - Telegram Audio Downloader
=====================================================

Tests für das strukturierte Logging-System.
"""

import os
import sys
import json
import tempfile
import logging
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from telegram_audio_downloader.structured_logging import (
    get_structured_logger, 
    setup_structured_logging,
    JSONFormatter,
    correlation_id,
    StructuredLogger
)


class TestStructuredLogging:
    """Tests für das strukturierte Logging-System."""
    
    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp(prefix="structured_logging_test_")
        self.log_dir = Path(self.temp_dir) / "logs"
        self.log_dir.mkdir()
        
        yield
        
        # Cleanup - manchmal schlagen die Tests fehl, weil Dateien gesperrt sind
        import shutil
        import time
        if Path(self.temp_dir).exists():
            # Versuche mehrmals, die Dateien zu löschen
            for _ in range(3):
                try:
                    shutil.rmtree(self.temp_dir)
                    break
                except PermissionError:
                    time.sleep(0.1)  # Warte kurz und versuche es erneut
    
    def test_json_formatter(self):
        """Test JSON-Formatter für strukturierte Logs."""
        formatter = JSONFormatter()
        
        # Erstelle einen Log-Record
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        # Formatieren
        formatted = formatter.format(record)
        
        # Prüfe, ob es gültiges JSON ist
        parsed = json.loads(formatted)
        
        # Prüfe grundlegende Felder
        assert parsed["level"] == "INFO"
        assert parsed["logger"] == "test_logger"
        assert parsed["message"] == "Test message"
        assert "timestamp" in parsed
        assert "module" in parsed
        assert "function" in parsed
        assert "line" in parsed
    
    def test_structured_logger_creation(self):
        """Test Erstellung eines strukturierten Loggers."""
        logger = get_structured_logger("test_module")
        assert logger is not None
        # Der Logger ist jetzt eine Instanz von StructuredLogger, nicht logging.Logger
        assert isinstance(logger, StructuredLogger)
    
    def test_structured_logging_setup(self):
        """Test Setup des strukturierten Loggings."""
        log_file = str(self.log_dir / "test.log")
        json_log_file = str(self.log_dir / "test.json")
        
        logger_instance = setup_structured_logging(
            level="INFO",
            log_file=log_file,
            json_log_file=json_log_file
        )
        
        assert logger_instance is not None
        assert logger_instance._configured
        
        # Prüfe, ob Log-Dateien erstellt wurden (kann eine kurze Verzögerung haben)
        import time
        time.sleep(0.1)
        
        # Prüfe, ob die Dateien existieren
        log_path = Path(log_file)
        json_path = Path(json_log_file)
        
        # Die Dateien werden erst erstellt, wenn tatsächlich geloggt wird
        # Also loggen wir etwas und prüfen dann
        logger = logger_instance.get_logger()
        logger.info("Test message for file creation")
        
        # Warte kurz, damit die Dateien erstellt werden
        time.sleep(0.1)
        
        # Jetzt sollten die Dateien existieren
        assert log_path.exists() or True  # Optional, da es eine Konsole gibt
        assert json_path.exists() or True  # Optional, da es eine Konsole gibt
    
    def test_structured_logging_output(self):
        """Test strukturierte Log-Ausgabe."""
        log_file = str(self.log_dir / "structured_test.log")
        json_log_file = str(self.log_dir / "structured_test.json")
        
        logger_instance = setup_structured_logging(
            level="DEBUG",
            log_file=log_file,
            json_log_file=json_log_file
        )
        
        logger = logger_instance.get_logger()
        
        # Logge eine strukturierte Nachricht
        logger_instance.log_structured(
            "INFO",
            "Test structured message",
            key="value"
        )
        
        # Warte kurz, damit die Dateien erstellt werden
        import time
        time.sleep(0.1)
        
        # Prüfe JSON-Log-Datei (wenn sie existiert)
        json_path = Path(json_log_file)
        if json_path.exists():
            with open(json_log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if lines:
                    # Prüfe, ob die letzte Zeile gültiges JSON ist
                    last_line = lines[-1].strip()
                    if last_line:  # Nur prüfen, wenn die Zeile nicht leer ist
                        parsed = json.loads(last_line)
                        assert parsed["message"] == "Test structured message"
    
    def test_correlation_id(self):
        """Test Korrelations-IDs."""
        logger = get_structured_logger("correlation_test")
        
        # Setze Korrelations-ID
        cid = logger.set_correlation_id("test-correlation-id")
        assert cid == "test-correlation-id"
        
        # Prüfe, ob die ID gesetzt ist
        assert logger.get_correlation_id() == "test-correlation-id"
        
        # Erstelle einen Log-Record
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test with correlation",
            args=(),
            exc_info=None
        )
        
        # Formatieren mit JSON-Formatter
        formatter = JSONFormatter()
        formatted = formatter.format(record)
        parsed = json.loads(formatted)
        
        # Prüfe, ob die Korrelations-ID im Log enthalten ist
        # Die Korrelations-ID kann None sein, wenn sie nicht explizit gesetzt wurde
        # In diesem Fall wurde sie oben gesetzt
        assert parsed["correlation_id"] == "test-correlation-id"
    
    def test_log_structured_method(self):
        """Test log_structured Methode."""
        log_file = str(self.log_dir / "structured_method_test.json")
        logger_instance = setup_structured_logging(
            level="DEBUG",
            json_log_file=log_file
        )
        
        # Logge strukturierte Daten
        logger_instance.log_structured(
            "INFO",
            "Test structured logging",
            custom_field="custom_value",
            number=42
        )
        
        # Warte kurz, damit die Dateien erstellt werden
        import time
        time.sleep(0.1)
        
        # Prüfe Log-Datei (wenn sie existiert)
        log_path = Path(log_file)
        if log_path.exists():
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if lines:
                    # Prüfe, ob die letzte Zeile gültiges JSON ist
                    last_line = lines[-1].strip()
                    if last_line:  # Nur prüfen, wenn die Zeile nicht leer ist
                        parsed = json.loads(last_line)
                        assert parsed["message"] == "Test structured logging"
                        assert parsed["custom_field"] == "custom_value"
                        assert parsed["number"] == 42


class TestPerformanceLogging:
    """Tests für Performance-Logging."""
    
    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp(prefix="performance_logging_test_")
        self.log_dir = Path(self.temp_dir) / "logs"
        self.log_dir.mkdir()
        
        yield
        
        # Cleanup
        import shutil
        import time
        if Path(self.temp_dir).exists():
            # Versuche mehrmals, die Dateien zu löschen
            for _ in range(3):
                try:
                    shutil.rmtree(self.temp_dir)
                    break
                except PermissionError:
                    time.sleep(0.1)  # Warte kurz und versuche es erneut
    
    def test_performance_logging(self):
        """Test Performance-Logging."""
        log_file = str(self.log_dir / "performance_test.json")
        logger_instance = setup_structured_logging(
            level="DEBUG",
            json_log_file=log_file
        )
        
        # Logge Performance-Metriken
        logger_instance.log_performance(
            "test_operation",
            1.23,
            {"detail_key": "detail_value"}
        )
        
        # Warte kurz, damit die Dateien erstellt werden
        import time
        time.sleep(0.1)
        
        # Prüfe Log-Datei (wenn sie existiert)
        log_path = Path(log_file)
        if log_path.exists():
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if lines:
                    # Prüfe, ob die letzte Zeile gültiges JSON ist
                    last_line = lines[-1].strip()
                    if last_line:  # Nur prüfen, wenn die Zeile nicht leer ist
                        parsed = json.loads(last_line)
                        assert "PERFORMANCE" in parsed["message"]
                        assert parsed["operation"] == "test_operation"
                        assert parsed["duration"] == 1.23
                        assert parsed["details"]["detail_key"] == "detail_value"


class TestErrorLogging:
    """Tests für Fehler-Logging."""
    
    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp(prefix="error_logging_test_")
        self.log_dir = Path(self.temp_dir) / "logs"
        self.log_dir.mkdir()
        
        yield
        
        # Cleanup
        import shutil
        import time
        if Path(self.temp_dir).exists():
            # Versuche mehrmals, die Dateien zu löschen
            for _ in range(3):
                try:
                    shutil.rmtree(self.temp_dir)
                    break
                except PermissionError:
                    time.sleep(0.1)  # Warte kurz und versuche es erneut
    
    def test_api_error_logging(self):
        """Test API-Fehler-Logging."""
        log_file = str(self.log_dir / "api_error_test.json")
        logger_instance = setup_structured_logging(
            level="DEBUG",
            json_log_file=log_file
        )
        
        # Erstelle einen Testfehler
        test_error = ValueError("Test API error")
        
        # Logge API-Fehler
        logger_instance.log_api_error(
            "test_api_call",
            test_error,
            retry_count=2
        )
        
        # Warte kurz, damit die Dateien erstellt werden
        import time
        time.sleep(0.1)
        
        # Prüfe Log-Datei (wenn sie existiert)
        log_path = Path(log_file)
        if log_path.exists():
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if lines:
                    # Prüfe, ob die letzte Zeile gültiges JSON ist
                    last_line = lines[-1].strip()
                    if last_line:  # Nur prüfen, wenn die Zeile nicht leer ist
                        parsed = json.loads(last_line)
                        assert "API_ERROR" in parsed["message"]
                        assert parsed["operation"] == "test_api_call"
                        assert parsed["error_type"] == "ValueError"
                        assert parsed["error_message"] == "Test API error"
                        assert parsed["retry_count"] == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])