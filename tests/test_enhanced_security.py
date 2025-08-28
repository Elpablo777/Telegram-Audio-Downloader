"""
Tests für die erweiterten Sicherheitsfunktionen.
"""

import unittest
import tempfile
import os
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.telegram_audio_downloader.enhanced_security import (
    FileAccessControl, FileIntegrityChecker, SandboxingManager, AuditLogger,
    SecurityEvent, get_file_access_control, get_file_integrity_checker,
    get_audit_logger, check_file_access, verify_file_integrity,
    secure_file_operation, log_security_event
)

class TestFileAccessControl(unittest.TestCase):
    """Tests für die FileAccessControl-Klasse."""
    
    def setUp(self):
        """Erstellt eine Instanz der FileAccessControl-Klasse."""
        # Setze die globale Instanz zurück
        global _file_access_control
        _file_access_control = None
        self.access_control = FileAccessControl({"user1", "user2"})
    
    def test_check_file_access_allowed(self):
        """Testet den Zugriff auf eine Datei mit erlaubtem Benutzer."""
        file_path = Path("test.txt")
        result = self.access_control.check_file_access(file_path, "user1")
        self.assertTrue(result)
    
    def test_check_file_access_denied(self):
        """Testet den Zugriff auf eine Datei mit nicht erlaubtem Benutzer."""
        file_path = Path("test.txt")
        result = self.access_control.check_file_access(file_path, "user3")
        self.assertFalse(result)
    
    def test_check_file_access_no_user(self):
        """Testet den Zugriff auf eine Datei ohne Benutzerangabe."""
        file_path = Path("test.txt")
        result = self.access_control.check_file_access(file_path)
        self.assertFalse(result)
    
    def test_check_file_access_no_restriction(self):
        """Testet den Zugriff auf eine Datei ohne Benutzerbeschränkung."""
        access_control = FileAccessControl()
        file_path = Path("test.txt")
        result = access_control.check_file_access(file_path, "user1")
        self.assertTrue(result)
    
    def test_add_allowed_user(self):
        """Testet das Hinzufügen eines erlaubten Benutzers."""
        self.access_control.add_allowed_user("user3")
        self.assertIn("user3", self.access_control.allowed_users)
    
    def test_remove_allowed_user(self):
        """Testet das Entfernen eines erlaubten Benutzers."""
        self.access_control.remove_allowed_user("user1")
        self.assertNotIn("user1", self.access_control.allowed_users)
    
    def test_security_events(self):
        """Testet die Protokollierung von Sicherheitsereignissen."""
        initial_events = len(self.access_control.security_events)
        self.access_control._log_security_event("test_event", "Testereignis", "low")
        self.assertEqual(len(self.access_control.security_events), initial_events + 1)

class TestFileIntegrityChecker(unittest.TestCase):
    """Tests für die FileIntegrityChecker-Klasse."""
    
    def setUp(self):
        """Erstellt eine Instanz der FileIntegrityChecker-Klasse."""
        # Setze die globale Instanz zurück
        global _file_integrity_checker
        _file_integrity_checker = None
        self.integrity_checker = FileIntegrityChecker()
    
    def test_calculate_file_hash(self):
        """Testet die Berechnung des Hash einer Datei."""
        # Erstelle eine temporäre Datei
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("Testinhalt")
            temp_file_path = Path(f.name)
        
        try:
            file_hash = self.integrity_checker.calculate_file_hash(temp_file_path)
            self.assertIsInstance(file_hash, str)
            self.assertEqual(len(file_hash), 64)  # SHA256 Hash Länge
        finally:
            # Lösche die temporäre Datei
            temp_file_path.unlink()
    
    def test_verify_file_integrity_new_file(self):
        """Testet die Integritätsprüfung einer neuen Datei."""
        # Erstelle eine temporäre Datei
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("Testinhalt")
            temp_file_path = Path(f.name)
        
        try:
            result = self.integrity_checker.verify_file_integrity(temp_file_path)
            self.assertTrue(result)
        finally:
            # Lösche die temporäre Datei
            temp_file_path.unlink()
    
    def test_verify_file_integrity_known_file(self):
        """Testet die Integritätsprüfung einer bekannten Datei."""
        # Erstelle eine temporäre Datei
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("Testinhalt")
            temp_file_path = Path(f.name)
        
        try:
            # Füge die Datei als bekannt hinzu
            self.integrity_checker.add_known_file(temp_file_path)
            
            # Prüfe die Integrität
            result = self.integrity_checker.verify_file_integrity(temp_file_path)
            self.assertTrue(result)
        finally:
            # Lösche die temporäre Datei
            temp_file_path.unlink()
    
    def test_verify_file_integrity_modified_file(self):
        """Testet die Integritätsprüfung einer modifizierten Datei."""
        # Erstelle eine temporäre Datei
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("Testinhalt")
            temp_file_path = Path(f.name)
        
        try:
            # Füge die Datei als bekannt hinzu
            self.integrity_checker.add_known_file(temp_file_path)
            
            # Modifiziere die Datei
            with open(temp_file_path, "w") as f:
                f.write("Modifizierter Inhalt")
            
            # Prüfe die Integrität
            result = self.integrity_checker.verify_file_integrity(temp_file_path)
            self.assertFalse(result)
        finally:
            # Lösche die temporäre Datei
            temp_file_path.unlink()
    
    def test_verify_file_integrity_expected_hash(self):
        """Testet die Integritätsprüfung mit erwartetem Hash."""
        # Erstelle eine temporäre Datei
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("Testinhalt")
            temp_file_path = Path(f.name)
        
        try:
            # Berechne den erwarteten Hash
            expected_hash = self.integrity_checker.calculate_file_hash(temp_file_path)
            
            # Prüfe die Integrität mit dem erwarteten Hash
            result = self.integrity_checker.verify_file_integrity(temp_file_path, expected_hash)
            self.assertTrue(result)
        finally:
            # Lösche die temporäre Datei
            temp_file_path.unlink()
    
    def test_verify_file_integrity_wrong_hash(self):
        """Testet die Integritätsprüfung mit falschem Hash."""
        # Erstelle eine temporäre Datei
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("Testinhalt")
            temp_file_path = Path(f.name)
        
        try:
            # Prüfe die Integrität mit einem falschen Hash
            result = self.integrity_checker.verify_file_integrity(temp_file_path, "falscher_hash")
            self.assertFalse(result)
        finally:
            # Lösche die temporäre Datei
            temp_file_path.unlink()
    
    def test_verify_file_integrity_nonexistent_file(self):
        """Testet die Integritätsprüfung einer nicht existierenden Datei."""
        file_path = Path("nicht_existierende_datei.txt")
        result = self.integrity_checker.verify_file_integrity(file_path)
        self.assertFalse(result)

class TestSandboxingManager(unittest.TestCase):
    """Tests für die SandboxingManager-Klasse."""
    
    def test_sandboxing_manager_temp_dir(self):
        """Testet den Sandboxing-Manager mit temporärem Verzeichnis."""
        with SandboxingManager() as sandbox:
            self.assertIsInstance(sandbox, SandboxingManager)
            self.assertTrue(sandbox.sandbox_dir.exists())
            self.assertTrue(sandbox._cleanup_on_exit)
    
    def test_sandboxing_manager_custom_dir(self):
        """Testet den Sandboxing-Manager mit benutzerdefiniertem Verzeichnis."""
        with tempfile.TemporaryDirectory() as temp_dir:
            sandbox_dir = Path(temp_dir) / "sandbox"
            with SandboxingManager(sandbox_dir) as sandbox:
                self.assertIsInstance(sandbox, SandboxingManager)
                self.assertEqual(sandbox.sandbox_dir, sandbox_dir)
                self.assertFalse(sandbox._cleanup_on_exit)
    
    def test_secure_file_operation_success(self):
        """Testet eine erfolgreiche sichere Dateioperation."""
        def test_operation(x, y):
            return x + y
        
        with SandboxingManager() as sandbox:
            result = sandbox.secure_file_operation(test_operation, 2, 3)
            self.assertEqual(result, 5)
    
    def test_secure_file_operation_exception(self):
        """Testet eine fehlgeschlagene sichere Dateioperation."""
        def failing_operation():
            raise Exception("Testfehler")
        
        with SandboxingManager() as sandbox:
            with self.assertRaises(Exception):
                sandbox.secure_file_operation(failing_operation)

class TestAuditLogger(unittest.TestCase):
    """Tests für die AuditLogger-Klasse."""
    
    def setUp(self):
        """Erstellt eine Instanz der AuditLogger-Klasse."""
        # Setze die globale Instanz zurück
        global _audit_logger
        _audit_logger = None
        self.temp_dir = tempfile.mkdtemp()
        self.log_file = Path(self.temp_dir) / "audit.log"
        self.audit_logger = AuditLogger(self.log_file)
    
    def tearDown(self):
        """Räumt die temporären Dateien auf."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_log_event(self):
        """Testet die Protokollierung eines Ereignisses."""
        from datetime import datetime
        
        event = SecurityEvent(
            timestamp=datetime.fromisoformat("2023-01-01T12:00:00"),
            event_type="test_event",
            description="Testereignis",
            severity="low",
            user="testuser",
            details={"key": "value"}
        )
        
        self.audit_logger.log_event(event)
        
        # Prüfe, ob das Ereignis in der Log-Datei gespeichert wurde
        self.assertTrue(self.log_file.exists())
        with open(self.log_file, "r") as f:
            lines = f.readlines()
            self.assertEqual(len(lines), 1)
            
            # Prüfe den Inhalt der Log-Zeile
            logged_event = json.loads(lines[0])
            self.assertEqual(logged_event["event_type"], "test_event")
            self.assertEqual(logged_event["description"], "Testereignis")
            self.assertEqual(logged_event["severity"], "low")
            self.assertEqual(logged_event["user"], "testuser")
            self.assertEqual(logged_event["details"], {"key": "value"})

class TestGlobalFunctions(unittest.TestCase):
    """Tests für die globalen Hilfsfunktionen."""
    
    def setUp(self):
        """Setzt die globalen Instanzen zurück."""
        global _file_access_control, _file_integrity_checker, _audit_logger
        _file_access_control = None
        _file_integrity_checker = None
        _audit_logger = None
    
    def test_get_file_access_control(self):
        """Testet die Erstellung der Zugriffskontrolle."""
        access_control = get_file_access_control({"user1"})
        self.assertIsInstance(access_control, FileAccessControl)
        self.assertIn("user1", access_control.allowed_users)
        
        # Prüfe, ob die gleiche Instanz zurückgegeben wird
        access_control2 = get_file_access_control()
        self.assertIs(access_control, access_control2)
    
    def test_get_file_integrity_checker(self):
        """Testet die Erstellung des Dateiintegritätsprüfers."""
        integrity_checker = get_file_integrity_checker()
        self.assertIsInstance(integrity_checker, FileIntegrityChecker)
        self.assertEqual(integrity_checker.hash_algorithm, "sha256")
        
        # Prüfe, ob die gleiche Instanz zurückgegeben wird
        integrity_checker2 = get_file_integrity_checker()
        self.assertIs(integrity_checker, integrity_checker2)
    
    def test_get_audit_logger(self):
        """Testet die Erstellung des Audit-Loggers."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "audit.log"
            audit_logger = get_audit_logger(log_file)
            self.assertIsInstance(audit_logger, AuditLogger)
            self.assertEqual(audit_logger.log_file, log_file)
            
            # Prüfe, ob die gleiche Instanz zurückgegeben wird
            audit_logger2 = get_audit_logger()
            self.assertIs(audit_logger, audit_logger2)
    
    def test_check_file_access(self):
        """Testet die globale Funktion zur Zugriffsprüfung."""
        with patch('src.telegram_audio_downloader.enhanced_security.get_file_access_control') as mock_get_access_control:
            mock_access_control = MagicMock()
            mock_get_access_control.return_value = mock_access_control
            mock_access_control.check_file_access.return_value = True
            
            result = check_file_access(Path("test.txt"), "user1")
            self.assertTrue(result)
            mock_access_control.check_file_access.assert_called_once_with(Path("test.txt"), "user1")
    
    def test_verify_file_integrity(self):
        """Testet die globale Funktion zur Integritätsprüfung."""
        with patch('src.telegram_audio_downloader.enhanced_security.get_file_integrity_checker') as mock_get_integrity_checker:
            mock_integrity_checker = MagicMock()
            mock_get_integrity_checker.return_value = mock_integrity_checker
            mock_integrity_checker.verify_file_integrity.return_value = True
            
            result = verify_file_integrity(Path("test.txt"), "expected_hash")
            self.assertTrue(result)
            mock_integrity_checker.verify_file_integrity.assert_called_once_with(Path("test.txt"), "expected_hash")
    
    def test_secure_file_operation(self):
        """Testet die globale Funktion zur sicheren Dateioperation."""
        def test_operation(x, y):
            return x + y
        
        with patch('src.telegram_audio_downloader.enhanced_security.SandboxingManager') as mock_sandbox_manager:
            mock_sandbox = MagicMock()
            mock_sandbox_manager.return_value.__enter__.return_value = mock_sandbox
            mock_sandbox.secure_file_operation.return_value = 5
            
            result = secure_file_operation(test_operation, 2, 3)
            self.assertEqual(result, 5)
            mock_sandbox.secure_file_operation.assert_called_once_with(test_operation, 2, 3)
    
    def test_log_security_event(self):
        """Testet die globale Funktion zur Protokollierung von Sicherheitsereignissen."""
        with patch('src.telegram_audio_downloader.enhanced_security.get_file_access_control') as mock_get_access_control, \
             patch('src.telegram_audio_downloader.enhanced_security.get_audit_logger') as mock_get_audit_logger:
            mock_access_control = MagicMock()
            mock_audit_logger = MagicMock()
            mock_get_access_control.return_value = mock_access_control
            mock_get_audit_logger.return_value = mock_audit_logger
            
            log_security_event("test_event", "Testereignis", "low", "testuser", {"key": "value"})
            
            # Prüfe, ob die Ereignisprotokollierung aufgerufen wurde
            mock_access_control._log_security_event.assert_called_once_with(
                "test_event", "Testereignis", "low", "testuser", {"key": "value"}
            )
            
            # Prüfe, ob das Audit-Logging aufgerufen wurde
            mock_audit_logger.log_event.assert_called_once()
            called_event = mock_audit_logger.log_event.call_args[0][0]
            self.assertIsInstance(called_event, SecurityEvent)
            self.assertEqual(called_event.event_type, "test_event")
            self.assertEqual(called_event.description, "Testereignis")
            self.assertEqual(called_event.severity, "low")
            self.assertEqual(called_event.user, "testuser")
            self.assertEqual(called_event.details, {"key": "value"})

if __name__ == "__main__":
    unittest.main()