"""
Datenbank-Tests für den Telegram Audio Downloader.

Umfassende Teststrategie für:
- Einheitstests
- Integrationstests
- Lasttests
- Sicherheitstests
"""

import unittest
import tempfile
import os
from pathlib import Path
from typing import Dict, Any
import sqlite3
import time
from concurrent.futures import ThreadPoolExecutor

from .models import AudioFile, TelegramGroup, db, DownloadStatus
from .database import init_db
from .database_indexing import DatabaseIndexer
from .database_migrations import MigrationManager
from .database_pooling import DatabaseConnectionPool
from .extended_models import User, DownloadQueue, Tag, Playlist
from .database_security import DatabaseSecurityManager
from .database_backup import DatabaseBackupManager
from .database_monitoring import DatabasePerformanceMonitor
from .database_caching import InMemoryCache
from .database_replication import DatabaseReplicator
from .database_scaling import DatabaseSharder
from .database_validation import DatabaseValidator
from .database_documentation import DatabaseDocumentation

import logging
logger = logging.getLogger(__name__)


class DatabaseTestCase(unittest.TestCase):
    """Basisklasse für Datenbank-Tests."""
    
    def setUp(self):
        """Richtet die Testumgebung ein."""
        # Erstelle temporäre Datenbank für Tests
        self.test_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.test_db.close()
        
        # Initialisiere Datenbank mit Testpfad
        self.original_db = db
        init_db(self.test_db.name)
        
        # Erstelle Testdaten
        self._create_test_data()
    
    def tearDown(self):
        """Räumt die Testumgebung auf."""
        # Schließe Datenbankverbindung
        if not db.is_closed():
            db.close()
        
        # Lösche temporäre Datenbankdatei
        try:
            os.unlink(self.test_db.name)
        except Exception as e:
            logger.warning(f"Fehler beim Löschen der Testdatenbank: {e}")
    
    def _create_test_data(self):
        """Erstellt Testdaten für die Tests."""
        try:
            # Erstelle Test-Telegram-Gruppe
            self.test_group = TelegramGroup.create(
                group_id=123456789,
                title="Test Group",
                username="test_group"
            )
            
            # Erstelle Test-Audiodatei
            self.test_audio = AudioFile.create(
                file_id="test_file_001",
                file_name="test_audio.mp3",
                file_size=1024000,
                duration=180,
                title="Test Audio",
                performer="Test Artist",
                group=self.test_group,
                status=DownloadStatus.COMPLETED.value
            )
        except Exception as e:
            logger.error(f"Fehler beim Erstellen von Testdaten: {e}")


class DatabaseUnitTests(DatabaseTestCase):
    """Einheitstests für die Datenbank."""
    
    def test_audio_file_creation(self):
        """Testet die Erstellung eines AudioFile-Datensatzes."""
        audio = AudioFile.create(
            file_id="unit_test_001",
            file_name="unit_test.mp3",
            file_size=2048000,
            duration=240,
            title="Unit Test Audio",
            performer="Unit Test Artist",
            group=self.test_group,
            status=DownloadStatus.PENDING.value
        )
        
        self.assertIsNotNone(audio.id)
        self.assertEqual(audio.file_id, "unit_test_001")
        self.assertEqual(audio.file_name, "unit_test.mp3")
        self.assertEqual(audio.status, DownloadStatus.PENDING.value)
    
    def test_telegram_group_creation(self):
        """Testet die Erstellung eines TelegramGroup-Datensatzes."""
        group = TelegramGroup.create(
            group_id=987654321,
            title="Unit Test Group",
            username="unit_test_group"
        )
        
        self.assertIsNotNone(group.id)
        self.assertEqual(group.group_id, 987654321)
        self.assertEqual(group.title, "Unit Test Group")
    
    def test_audio_file_query(self):
        """Testet das Abfragen von AudioFile-Datensätzen."""
        # Teste das Finden per file_id
        audio = AudioFile.get_by_file_id("test_file_001")
        self.assertIsNotNone(audio)
        self.assertEqual(audio.file_name, "test_audio.mp3")
        
        # Teste das Filtern nach Status
        completed_files = AudioFile.select().where(
            AudioFile.status == DownloadStatus.COMPLETED.value
        )
        self.assertGreater(len(completed_files), 0)
    
    def test_extended_model_creation(self):
        """Testet die Erstellung von erweiterten Modellen."""
        # Teste User-Modell
        user = User.create(
            username="testuser",
            email="test@example.com",
            password_hash="fake_hashed_password_for_testing",  # Bandit: safe test password
            is_active=True
        )
        self.assertIsNotNone(user.id)
        self.assertEqual(user.username, "testuser")
        
        # Teste Tag-Modell
        tag = Tag.create(
            name="Test Tag",
            description="A tag for testing"
        )
        self.assertIsNotNone(tag.id)
        self.assertEqual(tag.name, "Test Tag")


class DatabaseIntegrationTests(DatabaseTestCase):
    """Integrationstests für die Datenbank."""
    
    def test_database_initialization(self):
        """Testet die Datenbankinitialisierung."""
        # Schließe aktuelle Verbindung
        if not db.is_closed():
            db.close()
        
        # Erstelle neue temporäre Datenbank
        new_test_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        new_test_db.close()
        
        try:
            # Initialisiere neue Datenbank
            initialized_db = init_db(new_test_db.name)
            self.assertIsNotNone(initialized_db)
            self.assertFalse(initialized_db.is_closed())
            
            # Prüfe, ob Tabellen existieren
            tables = initialized_db.get_tables()
            self.assertIn('audio_files', tables)
            self.assertIn('telegram_groups', tables)
            
        finally:
            # Aufräumen
            if not initialized_db.is_closed():
                initialized_db.close()
            os.unlink(new_test_db.name)
    
    def test_indexing_integration(self):
        """Testet die Integration der Datenbankindizierung."""
        indexer = DatabaseIndexer()
        
        # Erstelle zusätzliche Testdaten
        for i in range(10):
            AudioFile.create(
                file_id=f"index_test_{i:03d}",
                file_name=f"index_test_{i:03d}.mp3",
                group=self.test_group,
                status=DownloadStatus.COMPLETED.value if i % 2 == 0 else DownloadStatus.PENDING.value
            )
        
        # Optimiere Datenbank
        indexer.optimize_database()
        
        # Prüfe Index-Statistiken
        stats = indexer.get_index_statistics()
        self.assertGreater(stats["total_indexes"], 0)
    
    def test_migration_integration(self):
        """Testet die Integration der Datenbankmigration."""
        migration_manager = MigrationManager()
        
        # Prüfe aktuelle Version
        current_version = migration_manager.get_current_version()
        self.assertIsInstance(current_version, int)
        
        # Teste Migration auf neueste Version
        success = migration_manager.migrate()
        self.assertTrue(success)
    
    def test_security_integration(self):
        """Testet die Integration der Datenbanksicherheit."""
        security_manager = DatabaseSecurityManager()
        
        # Teste Datenverschlüsselung
        test_data = "Sensitive test data"
        encrypted = security_manager.encrypt_data(test_data)
        self.assertNotEqual(encrypted, test_data)
        
        # Teste Datenentschlüsselung
        decrypted = security_manager.decrypt_data(encrypted)
        self.assertEqual(decrypted, test_data)


class DatabaseLoadTests(DatabaseTestCase):
    """Lasttests für die Datenbank."""
    
    def test_concurrent_reads(self):
        """Testet gleichzeitige Leseoperationen."""
        # Erstelle mehr Testdaten
        for i in range(100):
            AudioFile.create(
                file_id=f"load_test_{i:03d}",
                file_name=f"load_test_{i:03d}.mp3",
                group=self.test_group,
                status=DownloadStatus.COMPLETED.value
            )
        
        def read_operation():
            # Führe mehrere Abfragen durch
            count = AudioFile.select().count()
            completed = AudioFile.select().where(
                AudioFile.status == DownloadStatus.COMPLETED.value
            ).count()
            return count, completed
        
        # Führe gleichzeitige Leseoperationen durch
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(read_operation) for _ in range(50)]
            results = [future.result() for future in futures]
        
        # Prüfe Ergebnisse
        for count, completed in results:
            self.assertGreaterEqual(count, 100)
            self.assertGreaterEqual(completed, 50)
    
    def test_concurrent_writes(self):
        """Testet gleichzeitige Schreiboperationen."""
        def write_operation(index):
            audio = AudioFile.create(
                file_id=f"concurrent_{index:04d}",
                file_name=f"concurrent_{index:04d}.mp3",
                group=self.test_group,
                status=DownloadStatus.PENDING.value
            )
            return audio.id
        
        # Führe gleichzeitige Schreiboperationen durch
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(write_operation, i) for i in range(50)]
            results = [future.result() for future in futures]
        
        # Prüfe, ob alle Datensätze erstellt wurden
        self.assertEqual(len(results), 50)
        for result in results:
            self.assertIsNotNone(result)
    
    def test_performance_under_load(self):
        """Testet die Datenbankperformance unter Last."""
        # Erstelle Testdaten
        for i in range(1000):
            AudioFile.create(
                file_id=f"perf_test_{i:04d}",
                file_name=f"perf_test_{i:04d}.mp3",
                group=self.test_group,
                status=DownloadStatus.COMPLETED.value
            )
        
        # Messung der Abfrageperformance
        start_time = time.time()
        for _ in range(100):
            AudioFile.select().where(
                AudioFile.status == DownloadStatus.COMPLETED.value
            ).count()
        end_time = time.time()
        
        # Prüfe, ob die Performance innerhalb akzeptabler Grenzen liegt
        total_time = end_time - start_time
        avg_time_per_query = total_time / 100
        self.assertLess(avg_time_per_query, 0.1)  # < 100ms pro Abfrage


class DatabaseSecurityTests(DatabaseTestCase):
    """Sicherheitstests für die Datenbank."""
    
    def test_data_encryption(self):
        """Testet die Datenverschlüsselung."""
        security_manager = DatabaseSecurityManager()
        
        # Teste verschiedene Datentypen
        test_cases = [
            "Simple text",
            "Text with special characters: äöü@#$%",
            "123456789",
            "",
            "Very long text " * 100
        ]
        
        for test_data in test_cases:
            encrypted = security_manager.encrypt_data(test_data)
            decrypted = security_manager.decrypt_data(encrypted)
            self.assertEqual(decrypted, test_data)
    
    def test_sql_injection_protection(self):
        """Testet den Schutz vor SQL-Injection."""
        # Versuche gefährliche Eingaben
        dangerous_inputs = [
            "'; DROP TABLE audio_files; --",
            "'; DELETE FROM audio_files; --",
            "'; UPDATE audio_files SET file_name='hacked'; --"
        ]
        
        for dangerous_input in dangerous_inputs:
            # Diese sollten als normale Strings behandelt werden, nicht als SQL
            try:
                audio = AudioFile.create(
                    file_id=f"danger_test_{hash(dangerous_input)}",
                    file_name=dangerous_input,  # Dies sollte sicher sein
                    group=self.test_group,
                    status=DownloadStatus.PENDING.value
                )
                # Wenn wir hier ankommen, wurde die Eingabe sicher behandelt
                self.assertIsNotNone(audio.id)
            except Exception as e:
                # Peewee sollte Parameter escapen, daher sollte dies nicht zu einer SQL-Injection führen
                self.fail(f"Unerwartete Ausnahme bei gefährlicher Eingabe: {e}")


def run_database_tests(test_type: str = "all") -> unittest.TestResult:
    """
    Führt Datenbank-Tests aus.
    
    Args:
        test_type: Art der Tests ('unit', 'integration', 'load', 'security', 'all')
        
    Returns:
        TestResult-Objekt
    """
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    if test_type in ["unit", "all"]:
        suite.addTests(loader.loadTestsFromTestCase(DatabaseUnitTests))
    
    if test_type in ["integration", "all"]:
        suite.addTests(loader.loadTestsFromTestCase(DatabaseIntegrationTests))
    
    if test_type in ["load", "all"]:
        suite.addTests(loader.loadTestsFromTestCase(DatabaseLoadTests))
    
    if test_type in ["security", "all"]:
        suite.addTests(loader.loadTestsFromTestCase(DatabaseSecurityTests))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


def run_all_database_tests() -> Dict[str, Any]:
    """
    Führt alle Datenbank-Tests aus und gibt eine Zusammenfassung zurück.
    
    Returns:
        Dictionary mit Testergebnissen
    """
    logger.info("Starte alle Datenbank-Tests")
    
    results = {
        "timestamp": time.time(),
        "tests": {},
        "summary": {}
    }
    
    test_types = ["unit", "integration", "load", "security"]
    
    for test_type in test_types:
        logger.info(f"Führe {test_type}-Tests aus")
        try:
            result = run_database_tests(test_type)
            results["tests"][test_type] = {
                "tests_run": result.testsRun,
                "failures": len(result.failures),
                "errors": len(result.errors),
                "success": result.wasSuccessful()
            }
        except Exception as e:
            logger.error(f"Fehler beim Ausführen von {test_type}-Tests: {e}")
            results["tests"][test_type] = {
                "tests_run": 0,
                "failures": 0,
                "errors": 1,
                "success": False,
                "error": str(e)
            }
    
    # Erstelle Zusammenfassung
    total_tests = sum(results["tests"][t]["tests_run"] for t in test_types)
    total_failures = sum(results["tests"][t]["failures"] for t in test_types)
    total_errors = sum(results["tests"][t]["errors"] for t in test_types)
    all_successful = all(results["tests"][t]["success"] for t in test_types)
    
    results["summary"] = {
        "total_tests_run": total_tests,
        "total_failures": total_failures,
        "total_errors": total_errors,
        "all_tests_successful": all_successful
    }
    
    logger.info(f"Datenbank-Tests abgeschlossen: {total_tests} Tests, "
                f"{total_failures} Fehlschläge, {total_errors} Fehler")
    
    return results


if __name__ == "__main__":
    # Wenn das Skript direkt ausgeführt wird, führe alle Tests aus
    results = run_all_database_tests()
    print(f"Testergebnisse: {results}")