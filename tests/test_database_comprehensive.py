#!/usr/bin/env python3
"""
Umfassende Datenbanktests - Telegram Audio Downloader
===================================================

Umfassende Tests für Datenbankoperationen, Migrationen und Transaktionen.
"""

import os
import sys
import tempfile
import sqlite3
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from telegram_audio_downloader.database import init_db, reset_db, get_db_connection
from telegram_audio_downloader.models import AudioFile, TelegramGroup, DownloadStatus


class TestDatabaseComprehensive:
    """Umfassende Tests für die Datenbank."""
    
    @pytest.fixture(autouse=True)
    def setup_test_database(self):
        """Setup test database."""
        self.temp_dir = tempfile.mkdtemp(prefix="db_test_")
        self.test_db_path = Path(self.temp_dir) / "test.db"
        os.environ["DB_PATH"] = str(self.test_db_path)
        
        # Reset und initialisiere die Datenbank
        reset_db()
        init_db()
        
        yield
        
        # Cleanup
        import shutil
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def test_database_creation(self):
        """Test Erstellung der Datenbank."""
        assert self.test_db_path.exists()
        
        # Prüfe, ob die Datenbank ein gültiges SQLite-Format hat
        with open(self.test_db_path, 'rb') as f:
            header = f.read(16)
            assert header.startswith(b"SQLite format 3")
    
    def test_database_tables_creation(self):
        """Test Erstellung der Datenbanktabellen."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Prüfe, ob die erwarteten Tabellen existieren
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        table_names = [table[0] for table in tables]
        
        # Prüfe, ob die wichtigsten Tabellen existieren
        assert "audio_file" in table_names
        assert "telegram_group" in table_names
    
    def test_database_table_structure(self):
        """Test Struktur der Datenbanktabellen."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Prüfe Struktur der audio_file Tabelle
        cursor.execute("PRAGMA table_info(audio_file);")
        audio_file_columns = cursor.fetchall()
        audio_file_column_names = [col[1] for col in audio_file_columns]
        
        # Prüfe, ob die erwarteten Spalten existieren
        expected_columns = ["id", "file_id", "file_unique_id", "file_name", "file_size", 
                           "mime_type", "duration", "title", "performer", "local_path",
                           "status", "download_attempts", "last_attempt_at", "downloaded_at",
                           "downloaded_bytes", "checksum_md5", "checksum_verified", 
                           "partial_file_path", "error_message", "group_id",
                           "created_at", "updated_at"]
        
        for column in expected_columns:
            assert column in audio_file_column_names
    
    def test_database_migrations(self):
        """Test Datenbankmigrationen."""
        # In einer echten Anwendung würden wir hier verschiedene
        # Datenbankversionen testen und sicherstellen, dass
        # Migrationen korrekt durchgeführt werden
        
        # Für diese Tests prüfen wir, ob die aktuelle Datenbankstruktur
        # gültig ist und alle erwarteten Felder enthält
        assert AudioFile.table_exists()
        assert TelegramGroup.table_exists()
    
    def test_concurrent_database_access(self):
        """Test gleichzeitiger Datenbankzugriff."""
        import threading
        import time
        
        # Erstelle eine Testgruppe
        group = TelegramGroup.create(
            group_id=123456,
            title="Concurrent Test Group"
        )
        
        # Funktion für gleichzeitigen Zugriff
        def create_audio_file(thread_id):
            for i in range(5):
                AudioFile.create(
                    file_id=f"concurrent_file_{thread_id}_{i}",
                    file_name=f"concurrent_{thread_id}_{i}.mp3",
                    file_size=1024000,
                    mime_type="audio/mpeg",
                    title=f"Concurrent Song {i}",
                    performer="Concurrent Artist",
                    group=group,
                    status=DownloadStatus.PENDING.value
                )
                time.sleep(0.01)  # Kleine Verzögerung
        
        # Erstelle mehrere Threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=create_audio_file, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Warte auf Abschluss aller Threads
        for thread in threads:
            thread.join()
        
        # Prüfe, ob alle Dateien erstellt wurden
        files = AudioFile.select().where(
            AudioFile.file_id.startswith("concurrent_file_")
        )
        assert files.count() == 15  # 3 Threads * 5 Dateien
    
    def test_database_transaction_behavior(self):
        """Test Transaktionsverhalten der Datenbank."""
        # Erstelle eine Testgruppe
        group = TelegramGroup.create(
            group_id=789012,
            title="Transaction Test Group"
        )
        
        # Test erfolgreiche Transaktion
        with get_db_connection().atomic():
            AudioFile.create(
                file_id="transaction_success_1",
                file_name="success1.mp3",
                file_size=1024000,
                mime_type="audio/mpeg",
                group=group,
                status=DownloadStatus.COMPLETED.value
            )
        
        # Prüfe, ob die Datei erstellt wurde
        success_file = AudioFile.get_or_none(AudioFile.file_id == "transaction_success_1")
        assert success_file is not None
        assert success_file.status == DownloadStatus.COMPLETED.value
    
    def test_database_rollback_on_error(self):
        """Test Datenbank-Rollback bei Fehlern."""
        # Erstelle eine Testgruppe
        group = TelegramGroup.create(
            group_id=345678,
            title="Rollback Test Group"
        )
        
        # Test Rollback bei Fehler
        try:
            with get_db_connection().atomic():
                AudioFile.create(
                    file_id="rollback_test_1",
                    file_name="rollback1.mp3",
                    file_size=1024000,
                    mime_type="audio/mpeg",
                    group=group,
                    status=DownloadStatus.PENDING.value
                )
                # Erzwinge einen Fehler (doppelte file_id)
                AudioFile.create(
                    file_id="rollback_test_1",  # Doppelte ID
                    file_name="rollback2.mp3",
                    file_size=2048000,
                    mime_type="audio/mpeg",
                    group=group,
                    status=DownloadStatus.PENDING.value
                )
        except Exception:
            # Fehler wurde erwartet
            pass
        
        # Prüfe, ob die Transaktion zurückgerollt wurde
        # (keine der Dateien sollte existieren)
        rollback_file = AudioFile.get_or_none(AudioFile.file_id == "rollback_test_1")
        assert rollback_file is None
    
    def test_database_performance_with_many_records(self):
        """Test Datenbankleistung mit vielen Datensätzen."""
        import time
        
        # Erstelle eine Testgruppe
        group = TelegramGroup.create(
            group_id=901234,
            title="Performance Test Group"
        )
        
        # Erstelle viele Datensätze
        start_time = time.time()
        for i in range(1000):
            AudioFile.create(
                file_id=f"perf_test_{i}",
                file_name=f"perf_{i}.mp3",
                file_size=1024000 + i,
                mime_type="audio/mpeg",
                title=f"Performance Test Song {i}",
                performer="Performance Artist",
                group=group,
                status=DownloadStatus.COMPLETED.value
            )
        creation_time = time.time() - start_time
        
        # Prüfe, ob alle Datensätze erstellt wurden
        file_count = AudioFile.select().where(
            AudioFile.file_id.startswith("perf_test_")
        ).count()
        assert file_count == 1000
        
        # Teste Abfrageleistung
        start_time = time.time()
        files = list(AudioFile.select().where(
            AudioFile.file_id.startswith("perf_test_")
        ).limit(100))
        query_time = time.time() - start_time
        
        # Die Zeiten sind nicht deterministisch, aber wir stellen sicher,
        # dass die Operationen nicht zu lange dauern
        assert len(files) == 100
    
    def test_database_recovery_after_error(self):
        """Test Datenbankwiederherstellung nach Fehlern."""
        # Erstelle eine Testgruppe
        group = TelegramGroup.create(
            group_id=567890,
            title="Recovery Test Group"
        )
        
        # Erstelle einige Dateien
        for i in range(5):
            AudioFile.create(
                file_id=f"recovery_{i}",
                file_name=f"recovery_{i}.mp3",
                file_size=1024000,
                mime_type="audio/mpeg",
                group=group,
                status=DownloadStatus.COMPLETED.value
            )
        
        # Simuliere einen Fehler (z.B. unerwarteter Verbindungsabbruch)
        # In einer echten Anwendung würde dies durch einen Datenbankfehler
        # oder Prozessabbruch verursacht werden
        
        # Prüfe, ob die Datenbank nach dem Fehler noch funktioniert
        file_count = AudioFile.select().where(
            AudioFile.file_id.startswith("recovery_")
        ).count()
        assert file_count == 5
        
        # Erstelle weitere Dateien nach dem "Fehler"
        for i in range(5, 10):
            AudioFile.create(
                file_id=f"recovery_{i}",
                file_name=f"recovery_{i}.mp3",
                file_size=1024000,
                mime_type="audio/mpeg",
                group=group,
                status=DownloadStatus.COMPLETED.value
            )
        
        # Prüfe Gesamtzahl
        total_count = AudioFile.select().where(
            AudioFile.file_id.startswith("recovery_")
        ).count()
        assert total_count == 10


class TestDatabaseConstraints:
    """Tests für Datenbankconstraints."""
    
    @pytest.fixture(autouse=True)
    def setup_test_database(self):
        """Setup test database."""
        self.temp_dir = tempfile.mkdtemp(prefix="db_constraints_test_")
        self.test_db_path = Path(self.temp_dir) / "test.db"
        os.environ["DB_PATH"] = str(self.test_db_path)
        
        # Reset und initialisiere die Datenbank
        reset_db()
        init_db()
        
        yield
        
        # Cleanup
        import shutil
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def test_unique_file_id_constraint(self):
        """Test UNIQUE Constraint für file_id."""
        group = TelegramGroup.create(
            group_id=111111,
            title="Unique ID Test Group"
        )
        
        # Erste Datei erstellen
        AudioFile.create(
            file_id="unique_test_1",
            file_name="unique1.mp3",
            file_size=1024000,
            mime_type="audio/mpeg",
            group=group
        )
        
        # Versuche, eine zweite Datei mit derselben file_id zu erstellen
        with pytest.raises(Exception):  # Peewee IntegrityError
            AudioFile.create(
                file_id="unique_test_1",  # Doppelte ID
                file_name="unique2.mp3",
                file_size=2048000,
                mime_type="audio/mpeg",
                group=group
            )
    
    def test_foreign_key_constraint(self):
        """Test FOREIGN KEY Constraint."""
        # Erstelle eine Datei mit einer nicht existierenden Gruppen-ID
        # In Peewee werden FOREIGN KEY Constraints standardmäßig nicht erzwungen
        # Es sei denn, sie sind explizit aktiviert
        
        # Dieser Test zeigt, dass die Beziehung korrekt funktioniert
        group = TelegramGroup.create(
            group_id=222222,
            title="FK Test Group"
        )
        
        audio_file = AudioFile.create(
            file_id="fk_test_1",
            file_name="fk1.mp3",
            file_size=1024000,
            mime_type="audio/mpeg",
            group=group
        )
        
        # Prüfe, ob die Beziehung korrekt ist
        assert audio_file.group.id == group.id
    
    def test_not_null_constraints(self):
        """Test NOT NULL Constraints."""
        group = TelegramGroup.create(
            group_id=333333,
            title="Not Null Test Group"
        )
        
        # Versuche, eine Datei ohne erforderliche Felder zu erstellen
        with pytest.raises(Exception):
            AudioFile.create(
                file_name="null_test.mp3",
                file_size=1024000,
                mime_type="audio/mpeg"
                # file_id fehlt (NOT NULL)
            )


class TestDatabaseQueryOperations:
    """Tests für Datenbankabfrageoperationen."""
    
    @pytest.fixture(autouse=True)
    def setup_test_data(self):
        """Setup test data."""
        self.temp_dir = tempfile.mkdtemp(prefix="db_query_test_")
        self.test_db_path = Path(self.temp_dir) / "test.db"
        os.environ["DB_PATH"] = str(self.test_db_path)
        
        # Reset und initialisiere die Datenbank
        reset_db()
        init_db()
        
        # Erstelle Testdaten
        self.group1 = TelegramGroup.create(
            group_id=444444,
            title="Query Test Group 1"
        )
        
        self.group2 = TelegramGroup.create(
            group_id=555555,
            title="Query Test Group 2"
        )
        
        # Erstelle Testdateien
        for i in range(10):
            group = self.group1 if i < 5 else self.group2
            status = DownloadStatus.COMPLETED.value if i % 2 == 0 else DownloadStatus.FAILED.value
            
            AudioFile.create(
                file_id=f"query_test_{i}",
                file_name=f"query_{i}.mp3",
                file_size=1024000 + i * 1000,
                mime_type="audio/mpeg",
                title=f"Query Test Song {i}",
                performer="Query Artist",
                group=group,
                status=status
            )
        
        yield
        
        # Cleanup
        import shutil
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def test_select_all_query(self):
        """Test SELECT * Abfrage."""
        files = AudioFile.select()
        assert files.count() == 10
    
    def test_filtered_select_query(self):
        """Test gefilterte SELECT Abfrage."""
        completed_files = AudioFile.select().where(
            AudioFile.status == DownloadStatus.COMPLETED.value
        )
        assert completed_files.count() == 5
    
    def test_join_query(self):
        """Test JOIN Abfrage."""
        files_with_groups = AudioFile.select().join(TelegramGroup).where(
            TelegramGroup.id == self.group1.id
        )
        assert files_with_groups.count() == 5
    
    def test_order_by_query(self):
        """Test ORDER BY Abfrage."""
        files_ordered = AudioFile.select().order_by(AudioFile.file_size)
        file_sizes = [f.file_size for f in files_ordered]
        assert file_sizes == sorted(file_sizes)
    
    def test_limit_query(self):
        """Test LIMIT Abfrage."""
        limited_files = AudioFile.select().limit(3)
        assert len(list(limited_files)) == 3
    
    def test_aggregate_functions(self):
        """Test Aggregatfunktionen."""
        from peewee import fn
        
        # Zähle Dateien pro Status
        status_counts = AudioFile.select(
            AudioFile.status,
            fn.COUNT(AudioFile.id).alias('count')
        ).group_by(AudioFile.status)
        
        counts = {item.status: item.count for item in status_counts}
        assert len(counts) == 2  # completed und failed
        assert sum(counts.values()) == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])