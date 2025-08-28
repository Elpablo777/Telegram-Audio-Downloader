"""
Tests für die erweiterte Protokollierung.
"""

import unittest
import json
from datetime import datetime
from pathlib import Path

from src.telegram_audio_downloader.advanced_logging import (
    AdvancedLogger, LogLevel, LogEntry
)
from src.telegram_audio_downloader.error_handling import TelegramAudioError

class TestLogLevel(unittest.TestCase):
    """Tests für die LogLevel-Enum."""
    
    def test_log_level_values(self):
        """Testet die LogLevel-Werte."""
        self.assertEqual(LogLevel.DEBUG.value, "DEBUG")
        self.assertEqual(LogLevel.INFO.value, "INFO")
        self.assertEqual(LogLevel.WARNING.value, "WARNING")
        self.assertEqual(LogLevel.ERROR.value, "ERROR")
        self.assertEqual(LogLevel.CRITICAL.value, "CRITICAL")

class TestLogEntry(unittest.TestCase):
    """Tests für die LogEntry-Datenklasse."""
    
    def test_log_entry_creation(self):
        """Testet die Erstellung eines LogEntry."""
        timestamp = datetime.now()
        entry = LogEntry(
            timestamp=timestamp,
            level=LogLevel.INFO,
            module="test_module",
            message="Test message"
        )
        
        self.assertEqual(entry.timestamp, timestamp)
        self.assertEqual(entry.level, LogLevel.INFO)
        self.assertEqual(entry.module, "test_module")
        self.assertEqual(entry.message, "Test message")
        self.assertIsNone(entry.user_action)
        self.assertIsNone(entry.performance_metrics)
        self.assertIsNone(entry.system_info)
        self.assertIsNone(entry.error_details)
        self.assertIsNone(entry.context)
        self.assertIsNone(entry.trace_id)

class TestAdvancedLogger(unittest.TestCase):
    """Tests für die AdvancedLogger-Klasse."""
    
    def test_format_log_entry(self):
        """Testet das Formatieren von Protokolleinträgen."""
        # Erstelle einen Logger mit einem temporären Verzeichnis
        logger = AdvancedLogger("test_logs")
        
        timestamp = datetime.now()
        entry = LogEntry(
            timestamp=timestamp,
            level=LogLevel.INFO,
            module="test_module",
            message="Test message",
            user_action="test_action",
            context={"key": "value"}
        )
        
        formatted = logger._format_log_entry(entry)
        self.assertIsInstance(formatted, str)
        
        # Prüfe, ob der formatierte String gültiges JSON ist
        parsed = json.loads(formatted)
        self.assertEqual(parsed["module"], "test_module")
        self.assertEqual(parsed["message"], "Test message")
        self.assertEqual(parsed["user_action"], "test_action")
        self.assertEqual(parsed["context"], {"key": "value"})

if __name__ == "__main__":
    unittest.main()