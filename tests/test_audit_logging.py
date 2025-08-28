#!/usr/bin/env python3
"""
Audit-Logging Tests - Telegram Audio Downloader
============================================

Tests für das Audit-Logging-System.
"""

import os
import sys
import json
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from telegram_audio_downloader.audit_logging import (
    get_audit_logger,
    AuditLogger,
    log_user_login,
    log_user_logout,
    log_configuration_change,
    log_data_change,
    log_system_event,
    log_security_event
)


class TestAuditLogger:
    """Tests für den AuditLogger."""
    
    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp(prefix="audit_logging_test_")
        self.log_dir = Path(self.temp_dir) / "logs"
        self.log_dir.mkdir()
        
        # Setze Log-Datei-Pfad
        self.log_file = self.log_dir / "audit_test.log"
        
        yield
        
        # Cleanup
        import shutil
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def test_audit_logger_creation(self):
        """Test Erstellung des AuditLoggers."""
        logger = AuditLogger(str(self.log_file))
        assert logger is not None
        assert logger.log_file == self.log_file
        assert logger.logger is not None
    
    def test_log_user_login(self):
        """Test Logging von Benutzeranmeldungen."""
        logger = AuditLogger(str(self.log_file))
        
        # Logge eine Benutzeranmeldung
        logger.log_user_login("user123", "192.168.1.1")
        
        # Prüfe Log-Datei
        assert self.log_file.exists()
        with open(self.log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            assert len(lines) == 1
            
            # Prüfe, ob die Zeile gültiges JSON ist
            parsed = json.loads(lines[0].strip())
            assert parsed["event_type"] == "user_login"
            assert parsed["user_id"] == "user123"
            assert parsed["ip_address"] == "192.168.1.1"
            assert "timestamp" in parsed
            assert "event_hash" in parsed
    
    def test_log_user_logout(self):
        """Test Logging von Benutzerabmeldungen."""
        logger = AuditLogger(str(self.log_file))
        
        # Logge eine Benutzerabmeldung
        logger.log_user_logout("user123")
        
        # Prüfe Log-Datei
        assert self.log_file.exists()
        with open(self.log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            assert len(lines) == 1
            
            # Prüfe, ob die Zeile gültiges JSON ist
            parsed = json.loads(lines[0].strip())
            assert parsed["event_type"] == "user_logout"
            assert parsed["user_id"] == "user123"
    
    def test_log_configuration_change(self):
        """Test Logging von Konfigurationsänderungen."""
        logger = AuditLogger(str(self.log_file))
        
        # Logge eine Konfigurationsänderung
        logger.log_configuration_change(
            "user123",
            "max_concurrent_downloads",
            3,
            5,
            "Performance optimization"
        )
        
        # Prüfe Log-Datei
        assert self.log_file.exists()
        with open(self.log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            assert len(lines) == 1
            
            # Prüfe, ob die Zeile gültiges JSON ist
            parsed = json.loads(lines[0].strip())
            assert parsed["event_type"] == "configuration_change"
            assert parsed["user_id"] == "user123"
            assert parsed["config_key"] == "max_concurrent_downloads"
            assert parsed["old_value"] == 3
            assert parsed["new_value"] == 5
            assert parsed["reason"] == "Performance optimization"
    
    def test_log_data_change(self):
        """Test Logging von Datenänderungen."""
        logger = AuditLogger(str(self.log_file))
        
        # Logge eine Datenänderung
        logger.log_data_change(
            "user123",
            "audio_files",
            "12345",
            "update",
            {"title": "Old Title"},
            {"title": "New Title", "performer": "New Artist"}
        )
        
        # Prüfe Log-Datei
        assert self.log_file.exists()
        with open(self.log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            assert len(lines) == 1
            
            # Prüfe, ob die Zeile gültiges JSON ist
            parsed = json.loads(lines[0].strip())
            assert parsed["event_type"] == "data_change"
            assert parsed["user_id"] == "user123"
            assert parsed["table"] == "audio_files"
            assert parsed["record_id"] == "12345"
            assert parsed["action"] == "update"
            assert parsed["old_data"]["title"] == "Old Title"
            assert parsed["new_data"]["title"] == "New Title"
            assert parsed["new_data"]["performer"] == "New Artist"
    
    def test_log_system_event(self):
        """Test Logging von Systemereignissen."""
        logger = AuditLogger(str(self.log_file))
        
        # Logge ein Systemereignis
        logger.log_system_event(
            "backup_completed",
            "Database backup completed successfully",
            "INFO",
            {"backup_size": "1.2GB", "duration": "5m"}
        )
        
        # Prüfe Log-Datei
        assert self.log_file.exists()
        with open(self.log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            assert len(lines) == 1
            
            # Prüfe, ob die Zeile gültiges JSON ist
            parsed = json.loads(lines[0].strip())
            assert parsed["event_type"] == "backup_completed"
            assert parsed["description"] == "Database backup completed successfully"
            assert parsed["severity"] == "INFO"
            assert parsed["details"]["backup_size"] == "1.2GB"
            assert parsed["details"]["duration"] == "5m"
    
    def test_log_security_event(self):
        """Test Logging von sicherheitsrelevanten Ereignissen."""
        logger = AuditLogger(str(self.log_file))
        
        # Logge ein sicherheitsrelevantes Ereignis
        logger.log_security_event(
            "failed_login",
            "Failed login attempt",
            "user123",
            "192.168.1.100",
            {"attempts": 3, "blocked": False}
        )
        
        # Prüfe Log-Datei
        assert self.log_file.exists()
        with open(self.log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            assert len(lines) == 1
            
            # Prüfe, ob die Zeile gültiges JSON ist
            parsed = json.loads(lines[0].strip())
            assert parsed["event_type"] == "failed_login"
            assert parsed["description"] == "Failed login attempt"
            assert parsed["user_id"] == "user123"
            assert parsed["ip_address"] == "192.168.1.100"
            assert parsed["details"]["attempts"] == 3
            assert parsed["details"]["blocked"] == False
            assert parsed["security_relevant"] == True
    
    def test_sensitive_data_masking(self):
        """Test Maskierung sensibler Daten."""
        logger = AuditLogger(str(self.log_file))
        
        # Logge eine Konfigurationsänderung mit sensiblen Daten
        logger.log_configuration_change(
            "user123",
            "api_hash",
            "old_secret_key",
            "new_secret_key"
        )
        
        # Prüfe Log-Datei
        assert self.log_file.exists()
        with open(self.log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            assert len(lines) == 1
            
            # Prüfe, ob die Zeile gültiges JSON ist
            parsed = json.loads(lines[0].strip())
            # Sensible Daten sollten maskiert sein
            assert parsed["old_value"] == "********"
            assert parsed["new_value"] == "********"
    
    def test_get_audit_events(self):
        """Test Abrufen von Audit-Events."""
        logger = AuditLogger(str(self.log_file))
        
        # Logge verschiedene Ereignisse
        logger.log_user_login("user1", "192.168.1.1")
        logger.log_user_login("user2", "192.168.1.2")
        logger.log_configuration_change("user1", "setting1", "old", "new")
        
        # Hole alle Ereignisse
        events = logger.get_audit_events()
        assert len(events) == 3
        
        # Filtere nach Ereignistyp
        login_events = logger.get_audit_events(event_type="user_login")
        assert len(login_events) == 2
        
        # Filtere nach Benutzer-ID
        user1_events = logger.get_audit_events(user_id="user1")
        assert len(user1_events) == 2
        
        # Filtere nach Zeitraum
        now = datetime.now()
        future = now + timedelta(hours=1)
        future_events = logger.get_audit_events(start_time=future)
        assert len(future_events) == 0


class TestAuditLoggingFunctions:
    """Tests für die Audit-Logging-Funktionen."""
    
    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp(prefix="audit_functions_test_")
        self.log_dir = Path(self.temp_dir) / "logs"
        self.log_dir.mkdir()
        
        # Setze globale Log-Datei
        import telegram_audio_downloader.audit_logging as audit_module
        audit_module._audit_logger = AuditLogger(str(self.log_dir / "audit_functions_test.log"))
        
        yield
        
        # Setze globale Instanz zurück
        audit_module._audit_logger = None
        
        # Cleanup
        import shutil
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def test_log_user_login_function(self):
        """Test log_user_login Funktion."""
        log_user_login("test_user", "192.168.1.1")
        # Wenn keine Ausnahme geworfen wird, ist der Test erfolgreich
        assert True
    
    def test_log_user_logout_function(self):
        """Test log_user_logout Funktion."""
        log_user_logout("test_user")
        # Wenn keine Ausnahme geworfen wird, ist der Test erfolgreich
        assert True
    
    def test_log_configuration_change_function(self):
        """Test log_configuration_change Funktion."""
        log_configuration_change(
            "test_user",
            "test_setting",
            "old_value",
            "new_value"
        )
        # Wenn keine Ausnahme geworfen wird, ist der Test erfolgreich
        assert True
    
    def test_log_data_change_function(self):
        """Test log_data_change Funktion."""
        log_data_change(
            "test_user",
            "test_table",
            "123",
            "update",
            {"old": "data"},
            {"new": "data"}
        )
        # Wenn keine Ausnahme geworfen wird, ist der Test erfolgreich
        assert True
    
    def test_log_system_event_function(self):
        """Test log_system_event Funktion."""
        log_system_event(
            "test_event",
            "Test system event",
            "INFO",
            {"detail": "value"}
        )
        # Wenn keine Ausnahme geworfen wird, ist der Test erfolgreich
        assert True
    
    def test_log_security_event_function(self):
        """Test log_security_event Funktion."""
        log_security_event(
            "test_security_event",
            "Test security event",
            "test_user",
            "192.168.1.1",
            {"threat": "low"}
        )
        # Wenn keine Ausnahme geworfen wird, ist der Test erfolgreich
        assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])