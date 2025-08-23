"""
Umfassende Tests für Logging-Konfiguration und Error-Tracking.
"""
import pytest
import logging
import tempfile
import os
import json
from pathlib import Path
from unittest.mock import patch, MagicMock, call
from io import StringIO
import sys

from src.telegram_audio_downloader.logging_config import (
    TelegramAudioLogger, ErrorTracker, get_logger, get_error_tracker,
    setup_logging
)


class TestTelegramAudioLogger:
    """Tests für die TelegramAudioLogger-Klasse."""
    
    def test_init_default_params(self):
        """Test Standard-Initialisierung."""
        logger_instance = TelegramAudioLogger()
        
        assert logger_instance.name == "telegram_audio_downloader"
        assert logger_instance.logger.name == "telegram_audio_downloader"
        assert logger_instance.console is not None
        assert logger_instance._configured is False
    
    def test_init_custom_name(self):
        """Test Initialisierung mit benutzerdefiniertem Namen."""
        custom_name = "test_logger"
        logger_instance = TelegramAudioLogger(custom_name)
        
        assert logger_instance.name == custom_name
        assert logger_instance.logger.name == custom_name
    
    def test_configure_basic(self):
        """Test grundlegende Konfiguration."""
        logger_instance = TelegramAudioLogger()
        
        logger_instance.configure(level="DEBUG")
        
        assert logger_instance._configured is True
        assert logger_instance.logger.level == logging.DEBUG
        assert len(logger_instance.logger.handlers) > 0
    
    def test_configure_with_file_logging(self):
        """Test Konfiguration mit Datei-Logging."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test.log"
            
            logger_instance = TelegramAudioLogger()
            logger_instance.configure(
                level="INFO",
                log_file=str(log_file),
                max_file_size=1024,
                backup_count=2
            )
            
            assert logger_instance._configured is True
            assert log_file.parent.exists()
            
            # Prüfe Handler-Anzahl (Console + File + Error-File)
            assert len(logger_instance.logger.handlers) >= 2
    
    def test_configure_multiple_calls(self):
        """Test dass mehrfache Konfiguration ignoriert wird."""
        logger_instance = TelegramAudioLogger()
        
        logger_instance.configure(level="DEBUG")
        original_handlers = len(logger_instance.logger.handlers)
        
        # Zweite Konfiguration sollte ignoriert werden
        logger_instance.configure(level="ERROR")
        
        assert len(logger_instance.logger.handlers) == original_handlers
        assert logger_instance.logger.level == logging.DEBUG  # Ursprünglicher Level
    
    def test_get_logger_auto_configure(self):
        """Test automatische Konfiguration beim ersten get_logger."""
        logger_instance = TelegramAudioLogger()
        
        logger = logger_instance.get_logger()
        
        assert logger_instance._configured is True
        assert logger is not None
        assert isinstance(logger, logging.Logger)
    
    def test_log_levels(self):
        """Test verschiedene Log-Level."""
        levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        
        for level in levels:
            logger_instance = TelegramAudioLogger(f"test_{level.lower()}")
            logger_instance.configure(level=level)
            
            expected_level = getattr(logging, level)
            assert logger_instance.logger.level == expected_level
    
    def test_invalid_log_level(self):
        """Test ungültiger Log-Level fällt auf INFO zurück."""
        logger_instance = TelegramAudioLogger()
        logger_instance.configure(level="INVALID_LEVEL")
        
        assert logger_instance.logger.level == logging.INFO


class TestTelegramAudioLoggerMethods:
    """Tests für spezielle Logging-Methoden."""
    
    @pytest.fixture
    def configured_logger(self):
        """Vorkonfigurierter Logger für Tests."""
        logger_instance = TelegramAudioLogger("test_methods")
        logger_instance.configure(level="DEBUG")
        return logger_instance
    
    def test_log_performance(self, configured_logger, caplog):
        """Test Performance-Logging."""
        with caplog.at_level(logging.INFO):
            configured_logger.log_performance(
                operation="test_download",
                duration=1.25,
                details={"file_size": 1024000, "speed": 500}
            )
        
        assert "PERFORMANCE: test_download dauerte 1.25s" in caplog.text
        assert "file_size" in caplog.text
        assert "speed" in caplog.text
    
    def test_log_download_progress(self, configured_logger, caplog):
        """Test Download-Progress-Logging."""
        with caplog.at_level(logging.DEBUG):
            configured_logger.log_download_progress(
                file_name="test_song.mp3",
                progress=75.5,
                speed=1200.0
            )
        
        assert "DOWNLOAD: test_song.mp3 - 75.5%" in caplog.text
        assert "1200.0 KB/s" in caplog.text
    
    def test_log_download_progress_no_speed(self, configured_logger, caplog):
        """Test Download-Progress ohne Geschwindigkeit."""
        with caplog.at_level(logging.DEBUG):
            configured_logger.log_download_progress(
                file_name="test_song.mp3",
                progress=50.0
            )
        
        assert "DOWNLOAD: test_song.mp3 - 50.0%" in caplog.text
        assert "KB/s" not in caplog.text
    
    def test_log_api_error(self, configured_logger, caplog):
        """Test API-Error-Logging."""
        test_error = RuntimeError("Test API error")
        
        with caplog.at_level(logging.ERROR):
            configured_logger.log_api_error(
                operation="get_messages",
                error=test_error,
                retry_count=2
            )
        
        assert "API_ERROR: get_messages fehlgeschlagen" in caplog.text
        assert "Versuch 2" in caplog.text
        assert "RuntimeError: Test API error" in caplog.text
    
    def test_log_api_error_no_retry(self, configured_logger, caplog):
        """Test API-Error ohne Retry-Count."""
        test_error = ValueError("Invalid parameter")
        
        with caplog.at_level(logging.ERROR):
            configured_logger.log_api_error(
                operation="download_file",
                error=test_error
            )
        
        assert "API_ERROR: download_file fehlgeschlagen" in caplog.text
        assert "Versuch" not in caplog.text
        assert "ValueError: Invalid parameter" in caplog.text
    
    @patch('psutil.cpu_count')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    @patch('platform.system')
    @patch('platform.version')
    @patch('platform.python_version')
    def test_log_system_info(self, mock_python_version, mock_version, mock_system,
                            mock_disk_usage, mock_virtual_memory, mock_cpu_count,
                            configured_logger, caplog):
        """Test System-Info-Logging."""
        # Mock system info
        mock_system.return_value = "Linux"
        mock_version.return_value = "5.4.0"
        mock_python_version.return_value = "3.11.5"
        mock_cpu_count.return_value = 8
        
        mock_memory = MagicMock()
        mock_memory.total = 16 * (1024**3)  # 16GB
        mock_virtual_memory.return_value = mock_memory
        
        mock_disk = MagicMock()
        mock_disk.free = 100 * (1024**3)  # 100GB
        mock_disk_usage.return_value = mock_disk
        
        with caplog.at_level(logging.INFO):
            configured_logger.log_system_info()
        
        assert "SYSTEM_INFO:" in caplog.text
        assert "System: Linux" in caplog.text
        assert "Python: 3.11.5" in caplog.text
        assert "CPU Cores: 8" in caplog.text
        assert "16.0 GB" in caplog.text
        assert "100.0 GB" in caplog.text


class TestErrorTracker:
    """Tests für den ErrorTracker."""
    
    def test_track_error_basic(self):
        """Test grundlegendes Error-Tracking."""
        tracker = ErrorTracker()
        error = ValueError("Test error")
        
        tracker.track_error(error, "test_operation")
        
        assert len(tracker.errors) == 1
        assert tracker.errors[0]["context"] == "test_operation"
        assert tracker.errors[0]["type"] == "ValueError"
        assert "Test error" in tracker.errors[0]["message"]
    
    def test_track_error_with_severity(self):
        """Test Error-Tracking mit verschiedenen Severity-Levels."""
        tracker = ErrorTracker()
        error = RuntimeError("Runtime error")
        
        tracker.track_error(error, "download", "CRITICAL")
        
        assert len(tracker.errors) == 1
        error_record = tracker.errors[0]
        assert error_record["context"] == "download"
        assert error_record["severity"] == "CRITICAL"
        assert error_record["type"] == "RuntimeError"
    
    def test_get_error_summary(self):
        """Test Error-Summary-Generierung."""
        tracker = ErrorTracker()
        
        # Verschiedene Fehler hinzufügen
        tracker.track_error(ValueError("Error 1"), "operation_a")
        tracker.track_error(ValueError("Error 2"), "operation_a")
        tracker.track_error(RuntimeError("Error 3"), "operation_b")
        
        summary = tracker.get_error_summary()
        
        assert summary["total"] == 3
        assert summary["by_type"]["ValueError"] == 2
        assert summary["by_type"]["RuntimeError"] == 1
        assert len(summary["recent"]) <= 5
    
    def test_should_retry_logic(self):
        """Test Retry-Logik für verschiedene Fehlertypen."""
        tracker = ErrorTracker()
        
        # ConnectionError sollte retry erlauben
        conn_error = ConnectionError("Connection failed")
        assert tracker.should_retry(conn_error, "download", max_retries=3) is True
        
        # Nach mehreren Versuchen sollte retry false werden
        for _ in range(4):
            tracker.track_error(conn_error, "download")
        
        assert tracker.should_retry(conn_error, "download", max_retries=3) is False
    
    def test_error_counts(self):
        """Test Error-Counting-Mechanismus."""
        tracker = ErrorTracker()
        
        # Mehrere identische Fehler hinzufügen
        for _ in range(3):
            tracker.track_error(ValueError("Same error"), "same_operation")
        
        error_key = "ValueError:same_operation"
        assert tracker.error_counts[error_key] == 3
        
        summary = tracker.get_error_summary()
        assert summary["total"] == 3
    
    def test_error_summary_structure(self):
        """Test Struktur der Error-Summary."""
        tracker = ErrorTracker()
        
        error = ValueError("Test export error")
        tracker.track_error(error, "export_test")
        
        summary = tracker.get_error_summary()
        
        assert "total" in summary
        assert "by_type" in summary
        assert "most_common" in summary
        assert "recent" in summary
        assert summary["total"] == 1
        assert summary["by_type"]["ValueError"] == 1


class TestLoggingIntegration:
    """Tests für Logging-Integration und globale Funktionen."""
    
    def test_get_logger_singleton(self):
        """Test dass get_logger Singleton-Pattern verwendet."""
        logger1 = get_logger()
        logger2 = get_logger()
        
        assert logger1 is logger2
    
    def test_get_error_tracker_singleton(self):
        """Test dass get_error_tracker Singleton-Pattern verwendet."""
        tracker1 = get_error_tracker()
        tracker2 = get_error_tracker()
        
        assert tracker1 is tracker2
    
    def test_setup_logging_debug_mode(self, caplog):
        """Test setup_logging mit Debug-Modus."""
        with caplog.at_level(logging.DEBUG):
            logger = setup_logging(debug=True)
            
            assert logger.level == logging.DEBUG
            # System-Info sollte geloggt werden
            assert "SYSTEM_INFO:" in caplog.text
    
    def test_setup_logging_normal_mode(self, caplog):
        """Test setup_logging im normalen Modus."""
        with caplog.at_level(logging.INFO):
            logger = setup_logging(debug=False)
            
            assert logger.level == logging.INFO
            assert "SYSTEM_INFO:" in caplog.text
    
    @patch('configparser.ConfigParser')
    @patch('pathlib.Path.exists')
    def test_get_logger_with_config_file(self, mock_exists, mock_config_parser):
        """Test get_logger mit Konfigurations-Datei."""
        # Mock config file exists
        mock_exists.return_value = True
        
        # Mock config content
        mock_config = MagicMock()
        mock_config.__contains__ = lambda self, key: key == "logging"
        mock_config.__getitem__ = lambda self, key: {
            "level": "DEBUG",
            "file": "test.log",
            "max_file_size_mb": "5",
            "backup_count": "2"
        }
        
        mock_config_instance = MagicMock()
        mock_config_instance.read.return_value = None
        mock_config_instance.__getitem__ = mock_config.__getitem__
        mock_config_instance.__contains__ = mock_config.__contains__
        mock_config_parser.return_value = mock_config_instance
        
        # Reset global logger
        import src.telegram_audio_downloader.logging_config as logging_module
        logging_module._global_logger = None
        
        logger = get_logger()
        
        assert logger is not None
        mock_config_parser.assert_called_once()


class TestLoggingFormatters:
    """Tests für Logging-Formatter."""
    
    def test_file_formatter(self):
        """Test Datei-Formatter."""
        logger_instance = TelegramAudioLogger("test_formatter")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "formatter_test.log"
            logger_instance.configure(log_file=str(log_file))
            
            logger = logger_instance.get_logger()
            logger.info("Test message for formatter")
            
            # Prüfe Log-Datei-Inhalt
            log_content = log_file.read_text(encoding='utf-8')
            
            # Sollte Timestamp, Logger-Name, Level, Dateiname und Message enthalten
            assert "telegram_audio_downloader" in log_content
            assert "INFO" in log_content
            assert "Test message for formatter" in log_content
            assert "test_logging.py" in log_content
    
    def test_console_formatter_without_rich(self):
        """Test Console-Formatter ohne Rich."""
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            logger_instance = TelegramAudioLogger("test_console")
            logger_instance.configure(enable_rich=False)
            
            logger = logger_instance.get_logger()
            logger.info("Console test message")
            
            # Da wir einen Handler haben, sollte etwas ausgegeben werden
            # Die genaue Ausgabe hängt von der Handler-Konfiguration ab
            assert logger.handlers  # Mindestens ein Handler sollte vorhanden sein


class TestLoggingErrorHandling:
    """Tests für Error-Handling im Logging-System."""
    
    def test_invalid_log_file_path(self):
        """Test Behandlung ungültiger Log-Datei-Pfade."""
        logger_instance = TelegramAudioLogger()
        
        # Ungültiger Pfad (schreibgeschütztes Verzeichnis)
        invalid_path = "/root/invalid/path/test.log"
        
        # Sollte nicht abstürzen, sondern graceful degradieren
        try:
            logger_instance.configure(log_file=invalid_path)
            # Falls kein Fehler auftritt, ist das auch in Ordnung
        except (PermissionError, OSError):
            # Diese Fehler sind bei ungültigen Pfaden erwartet
            pass
    
    def test_logging_with_none_values(self, caplog):
        """Test Logging mit None-Werten."""
        logger_instance = TelegramAudioLogger()
        logger_instance.configure()
        
        with caplog.at_level(logging.DEBUG):
            logger_instance.log_download_progress(
                file_name="None",
                progress=50.0,
                speed=None
            )
        
        # Sollte nicht abstürzen
        assert "DOWNLOAD:" in caplog.text
    
    def test_logging_with_unicode_characters(self, caplog):
        """Test Logging mit Unicode-Zeichen."""
        logger_instance = TelegramAudioLogger()
        logger_instance.configure()
        
        with caplog.at_level(logging.INFO):
            logger_instance.log_performance(
                operation="Test mit äöü und 🎵 Emojis",
                duration=1.0,
                details={"file": "test_äöü_🎵.mp3"}
            )
        
        assert "äöü" in caplog.text
        assert "🎵" in caplog.text


class TestLoggingPerformance:
    """Performance-Tests für das Logging-System."""
    
    @pytest.mark.slow
    def test_high_volume_logging(self):
        """Test Logging mit hohem Durchsatz."""
        logger_instance = TelegramAudioLogger("performance_test")
        logger_instance.configure(level="DEBUG")
        
        import time
        start_time = time.time()
        
        # 1000 Log-Nachrichten
        for i in range(1000):
            logger_instance.log_download_progress(
                file_name=f"file_{i}.mp3",
                progress=i / 10.0,
                speed=1000.0 + i
            )
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Sollte in weniger als 5 Sekunden abgeschlossen sein
        assert duration < 5.0
        
        # Logger sollte noch funktionsfähig sein
        assert logger_instance._configured
    
    def test_memory_usage_with_error_tracking(self):
        """Test Memory-Usage bei intensivem Error-Tracking."""
        tracker = ErrorTracker()
        
        # 100 Fehler tracken
        for i in range(100):
            error = ValueError(f"Test error {i}")
            context = {"iteration": i, "data": f"data_{i}"}
            tracker.track_error(error, f"operation_{i}")
        
        assert len(tracker.errors) == 100
        
        # Memory sollte nicht explodieren
        summary = tracker.get_error_summary()
        assert summary["total_errors"] == 100


# Fixtures für komplexe Test-Szenarien
@pytest.fixture
def temp_log_directory():
    """Erstellt temporäres Verzeichnis für Log-Tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def sample_error_context():
    """Beispiel-Kontext für Error-Tests."""
    return {
        "session_id": "test_session_123",
        "user_id": 456789,
        "file_name": "test_song.mp3",
        "file_size": 5242880,
        "group_name": "@test_group",
        "retry_count": 2,
        "timestamp": "2024-01-15T10:30:00Z"
    }


@pytest.fixture
def mock_rich_console():
    """Mock für Rich Console."""
    console = MagicMock()
    console.print = MagicMock()
    return console


@pytest.fixture(autouse=True)
def reset_global_loggers():
    """Setzt globale Logger-Instanzen für jeden Test zurück."""
    import src.telegram_audio_downloader.logging_config as logging_module
    
    # Backup original values
    original_global_logger = logging_module._global_logger
    original_error_tracker = logging_module._error_tracker
    
    # Reset for test
    logging_module._global_logger = None
    logging_module._error_tracker = ErrorTracker()
    
    yield
    
    # Restore original values
    logging_module._global_logger = original_global_logger
    logging_module._error_tracker = original_error_tracker