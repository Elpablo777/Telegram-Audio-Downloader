"""
Umfassende Tests für Database Operations, Connections und Migrations.
"""
import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime

from src.telegram_audio_downloader.database import init_db, close_db, migrate_database
from src.telegram_audio_downloader.models import (
    db, AudioFile, TelegramGroup, DownloadStatus, BaseModel
)
from peewee import SqliteDatabase, OperationalError, IntegrityError


class TestDatabaseInitialization:
    """Tests für Datenbank-Initialisierung."""
    
    def test_init_db_default_path(self):
        """Test Datenbank-Initialisierung mit Standard-Pfad."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            temp_path = temp_db.name
        
        try:
            # Datei löschen, damit sie neu erstellt wird
            os.unlink(temp_path)
            
            database = init_db(temp_path)
            
            assert isinstance(database, SqliteDatabase)
            assert Path(temp_path).exists()
            assert database.is_closed() is False
            
            # Tabellen sollten existieren
            assert AudioFile.table_exists()
            assert TelegramGroup.table_exists()
            
        finally:
            close_db()
            if Path(temp_path).exists():
                os.unlink(temp_path)
    
    def test_init_db_custom_path(self):
        """Test Datenbank-Initialisierung mit benutzerdefiniertem Pfad."""
        with tempfile.TemporaryDirectory() as temp_dir:
            custom_path = Path(temp_dir) / "custom" / "test.db"
            
            database = init_db(str(custom_path))
            
            assert isinstance(database, SqliteDatabase)
            assert custom_path.exists()
            assert custom_path.parent.exists()  # Verzeichnis wurde erstellt
            
            close_db()
    
    def test_init_db_creates_directory(self):
        """Test dass init_db fehlende Verzeichnisse erstellt."""
        with tempfile.TemporaryDirectory() as temp_dir:
            nested_path = Path(temp_dir) / "level1" / "level2" / "test.db"
            
            database = init_db(str(nested_path))
            
            assert nested_path.exists()
            assert nested_path.parent.exists()
            
            close_db()
    
    def test_init_db_with_pragma_settings(self):
        """Test Datenbank-Initialisierung mit Pragma-Einstellungen."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            temp_path = temp_db.name
        
        try:
            os.unlink(temp_path)
            
            database = init_db(temp_path)
            
            # Teste Pragma-Einstellungen
            cursor = database.execute_sql("PRAGMA journal_mode")
            journal_mode = cursor.fetchone()[0]
            assert journal_mode.upper() == "WAL"
            
            cursor = database.execute_sql("PRAGMA foreign_keys")
            foreign_keys = cursor.fetchone()[0]
            assert foreign_keys == 1
            
        finally:
            close_db()
            if Path(temp_path).exists():
                os.unlink(temp_path)
    
    def test_init_db_existing_database(self):
        """Test Initialisierung einer bereits existierenden Datenbank."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            temp_path = temp_db.name
        
        try:
            # Erste Initialisierung
            database1 = init_db(temp_path)
            close_db()
            
            # Zweite Initialisierung derselben Datei
            database2 = init_db(temp_path)
            
            assert isinstance(database2, SqliteDatabase)
            assert Path(temp_path).exists()
            
        finally:
            close_db()
            if Path(temp_path).exists():
                os.unlink(temp_path)


class TestDatabaseConnection:
    """Tests für Datenbankverbindungen."""
    
    def test_close_db(self):
        """Test Datenbankverbindung schließen."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            temp_path = temp_db.name
        
        try:
            database = init_db(temp_path)
            assert not database.is_closed()
            
            close_db()
            assert database.is_closed()
            
        finally:
            if Path(temp_path).exists():
                os.unlink(temp_path)
    
    def test_database_reconnection(self):
        """Test Datenbankverbindung nach Trennung wiederherstellen."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            temp_path = temp_db.name
        
        try:
            # Erste Verbindung
            database1 = init_db(temp_path)
            assert not database1.is_closed()
            
            close_db()
            assert database1.is_closed()
            
            # Zweite Verbindung
            database2 = init_db(temp_path)
            assert not database2.is_closed()
            
        finally:
            close_db()
            if Path(temp_path).exists():
                os.unlink(temp_path)
    
    def test_database_connection_error(self):
        """Test Fehlerbehandlung bei Verbindungsproblemen."""
        # Versuche Verbindung zu ungültigem Pfad
        invalid_path = "/invalid/path/that/does/not/exist/test.db"
        
        with pytest.raises(Exception):  # Verschiedene Exceptions möglich
            init_db(invalid_path)


class TestDatabaseModels:
    """Tests für Datenbankmodelle."""
    
    @pytest.fixture
    def test_database(self):
        """Erstellt Test-Datenbank."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            temp_path = temp_db.name
        
        try:
            database = init_db(temp_path)
            yield database
        finally:
            close_db()
            if Path(temp_path).exists():
                os.unlink(temp_path)
    
    def test_telegram_group_creation(self, test_database):
        """Test TelegramGroup-Erstellung."""
        group = TelegramGroup.create(
            group_id=12345,
            title="Test Group",
            username="testgroup"
        )
        
        assert group.id is not None
        assert group.group_id == 12345
        assert group.title == "Test Group"
        assert group.username == "testgroup"
        assert group.created_at is not None
        assert group.updated_at is not None
    
    def test_telegram_group_unique_constraint(self, test_database):
        """Test Eindeutigkeitsbeschränkung für group_id."""
        TelegramGroup.create(
            group_id=12345,
            title="First Group",
            username="firstgroup"
        )
        
        # Zweite Gruppe mit derselben group_id sollte fehlschlagen
        with pytest.raises(IntegrityError):
            TelegramGroup.create(
                group_id=12345,
                title="Second Group",
                username="secondgroup"
            )
    
    def test_audio_file_creation(self, test_database):
        """Test AudioFile-Erstellung."""
        # Erst eine Gruppe erstellen
        group = TelegramGroup.create(
            group_id=12345,
            title="Test Group",
            username="testgroup"
        )
        
        audio_file = AudioFile.create(
            file_id="test_file_123",
            file_unique_id="unique_123",
            file_name="test_song.mp3",
            file_size=1024000,
            mime_type="audio/mpeg",
            duration=180,
            title="Test Song",
            performer="Test Artist",
            group=group,
            status=DownloadStatus.PENDING.value
        )
        
        assert audio_file.id is not None
        assert audio_file.file_id == "test_file_123"
        assert audio_file.file_unique_id == "unique_123"
        assert audio_file.file_name == "test_song.mp3"
        assert audio_file.file_size == 1024000
        assert audio_file.mime_type == "audio/mpeg"
        assert audio_file.duration == 180
        assert audio_file.title == "Test Song"
        assert audio_file.performer == "Test Artist"
        assert audio_file.group == group
        assert audio_file.status == DownloadStatus.PENDING.value
        assert audio_file.created_at is not None
    
    def test_audio_file_unique_constraint(self, test_database):
        """Test Eindeutigkeitsbeschränkung für file_id."""
        group = TelegramGroup.create(
            group_id=12345,
            title="Test Group",
            username="testgroup"
        )
        
        AudioFile.create(
            file_id="duplicate_file",
            file_unique_id="unique_1",
            file_name="first.mp3",
            file_size=1000000,
            mime_type="audio/mpeg",
            group=group
        )
        
        # Zweite Datei mit derselben file_id sollte fehlschlagen
        with pytest.raises(IntegrityError):
            AudioFile.create(
                file_id="duplicate_file",
                file_unique_id="unique_2",
                file_name="second.mp3",
                file_size=2000000,
                mime_type="audio/mpeg",
                group=group
            )
    
    def test_base_model_timestamps(self, test_database):
        """Test automatische Zeitstempel in BaseModel."""
        group = TelegramGroup.create(
            group_id=12345,
            title="Test Group",
            username="testgroup"
        )
        
        original_updated = group.updated_at
        
        # Kurz warten und dann updaten
        import time
        time.sleep(0.01)
        
        group.title = "Updated Group"
        group.save()
        
        assert group.updated_at > original_updated
    
    def test_foreign_key_relationship(self, test_database):
        """Test Foreign-Key-Beziehung zwischen AudioFile und TelegramGroup."""
        group = TelegramGroup.create(
            group_id=12345,
            title="Test Group",
            username="testgroup"
        )
        
        audio_file = AudioFile.create(
            file_id="test_file",
            file_unique_id="unique_test",
            file_name="test.mp3",
            file_size=1000000,
            mime_type="audio/mpeg",
            group=group
        )
        
        # Lade AudioFile neu und teste Beziehung
        retrieved_file = AudioFile.get(AudioFile.id == audio_file.id)
        assert retrieved_file.group.id == group.id
        assert retrieved_file.group.title == "Test Group"


class TestDatabaseQueries:
    """Tests für Datenbankabfragen."""
    
    @pytest.fixture
    def populated_database(self):
        """Erstellt Test-Datenbank mit Beispieldaten."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            temp_path = temp_db.name
        
        try:
            database = init_db(temp_path)
            
            # Erstelle Test-Gruppen
            groups = []
            for i in range(3):
                group = TelegramGroup.create(
                    group_id=12345 + i,
                    title=f"Test Group {i}",
                    username=f"testgroup{i}"
                )
                groups.append(group)
            
            # Erstelle Test-Audiodateien
            for i in range(10):
                AudioFile.create(
                    file_id=f"file_{i}",
                    file_unique_id=f"unique_{i}",
                    file_name=f"song_{i}.mp3",
                    file_size=1000000 + (i * 100000),
                    mime_type="audio/mpeg",
                    duration=180 + (i * 30),
                    title=f"Song {i}",
                    performer=f"Artist {i % 3}",
                    group=groups[i % 3],
                    status=[
                        DownloadStatus.COMPLETED.value,
                        DownloadStatus.PENDING.value,
                        DownloadStatus.FAILED.value
                    ][i % 3]
                )
            
            yield database
            
        finally:
            close_db()
            if Path(temp_path).exists():
                os.unlink(temp_path)
    
    def test_query_all_files(self, populated_database):
        """Test Abfrage aller Dateien."""
        files = AudioFile.select()
        assert files.count() == 10
    
    def test_query_files_by_status(self, populated_database):
        """Test Abfrage nach Status."""
        completed_files = AudioFile.select().where(
            AudioFile.status == DownloadStatus.COMPLETED.value
        )
        pending_files = AudioFile.select().where(
            AudioFile.status == DownloadStatus.PENDING.value
        )
        failed_files = AudioFile.select().where(
            AudioFile.status == DownloadStatus.FAILED.value
        )
        
        # Bei 10 Dateien mit 3 verschiedenen Status sollten etwa 3-4 pro Status sein
        assert completed_files.count() >= 3
        assert pending_files.count() >= 3
        assert failed_files.count() >= 3
    
    def test_query_files_by_group(self, populated_database):
        """Test Abfrage nach Gruppe."""
        group = TelegramGroup.get(TelegramGroup.group_id == 12345)
        files_in_group = AudioFile.select().where(AudioFile.group == group)
        
        assert files_in_group.count() >= 3  # Mindestens 3 Dateien pro Gruppe
    
    def test_query_files_by_performer(self, populated_database):
        """Test Abfrage nach Künstler."""
        artist_files = AudioFile.select().where(AudioFile.performer == "Artist 0")
        assert artist_files.count() >= 3
    
    def test_query_files_by_size_range(self, populated_database):
        """Test Abfrage nach Dateigröße."""
        large_files = AudioFile.select().where(AudioFile.file_size > 1500000)
        assert large_files.count() > 0
        
        for file in large_files:
            assert file.file_size > 1500000
    
    def test_query_with_join(self, populated_database):
        """Test Join-Query zwischen AudioFile und TelegramGroup."""
        from peewee import fn
        
        # Zähle Dateien pro Gruppe
        group_counts = (AudioFile
                       .select(TelegramGroup.title, fn.COUNT(AudioFile.id).alias('file_count'))
                       .join(TelegramGroup)
                       .group_by(TelegramGroup.title))
        
        assert group_counts.count() == 3  # 3 Gruppen
        
        for group_count in group_counts:
            assert group_count.file_count > 0
    
    def test_query_aggregation(self, populated_database):
        """Test Aggregations-Queries."""
        from peewee import fn
        
        # Gesamtanzahl Dateien
        total_files = AudioFile.select().count()
        assert total_files == 10
        
        # Gesamtgröße aller Dateien
        total_size = AudioFile.select(fn.SUM(AudioFile.file_size)).scalar()
        assert total_size > 10000000  # Mindestens 10MB
        
        # Durchschnittliche Dateigröße
        avg_size = AudioFile.select(fn.AVG(AudioFile.file_size)).scalar()
        assert avg_size > 1000000  # Mindestens 1MB
    
    def test_query_ordering(self, populated_database):
        """Test Sortierung."""
        # Nach Größe sortiert (aufsteigend)
        files_asc = AudioFile.select().order_by(AudioFile.file_size)
        files_list = list(files_asc)
        
        for i in range(len(files_list) - 1):
            assert files_list[i].file_size <= files_list[i + 1].file_size
        
        # Nach Größe sortiert (absteigend)
        files_desc = AudioFile.select().order_by(AudioFile.file_size.desc())
        files_list_desc = list(files_desc)
        
        for i in range(len(files_list_desc) - 1):
            assert files_list_desc[i].file_size >= files_list_desc[i + 1].file_size
    
    def test_query_limiting(self, populated_database):
        """Test Limit und Offset."""
        # Erste 5 Dateien
        first_five = AudioFile.select().limit(5)
        assert first_five.count() == 5
        
        # Nächste 5 Dateien (Offset 5)
        next_five = AudioFile.select().offset(5).limit(5)
        assert next_five.count() == 5
        
        # Stelle sicher, dass es verschiedene Dateien sind
        first_ids = [f.id for f in first_five]
        next_ids = [f.id for f in next_five]
        assert set(first_ids).isdisjoint(set(next_ids))


class TestDatabaseMigrations:
    """Tests für Datenbank-Migrationen."""
    
    def test_migrate_database_no_changes(self):
        """Test Migration ohne Änderungen."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            temp_path = temp_db.name
        
        try:
            database = init_db(temp_path)
            
            # Migration sollte ohne Fehler durchlaufen
            migrate_database(database)
            
            # Tabellen sollten noch existieren
            assert AudioFile.table_exists()
            assert TelegramGroup.table_exists()
            
        finally:
            close_db()
            if Path(temp_path).exists():
                os.unlink(temp_path)
    
    @patch('src.telegram_audio_downloader.database.SqliteMigrator')
    def test_migrate_database_with_changes(self, mock_migrator_class):
        """Test Migration mit Änderungen."""
        mock_migrator = MagicMock()
        mock_migrator_class.return_value = mock_migrator
        
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            temp_path = temp_db.name
        
        try:
            database = init_db(temp_path)
            
            with patch('src.telegram_audio_downloader.database.migrate') as mock_migrate:
                migrate_database(database)
                
                # Migration sollte aufgerufen worden sein
                mock_migrator_class.assert_called_once_with(database)
            
        finally:
            close_db()
            if Path(temp_path).exists():
                os.unlink(temp_path)


class TestDatabasePerformance:
    """Performance-Tests für Datenbank."""
    
    @pytest.mark.slow
    def test_bulk_insert_performance(self):
        """Test Performance bei Bulk-Inserts."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            temp_path = temp_db.name
        
        try:
            database = init_db(temp_path)
            
            # Erstelle eine Gruppe
            group = TelegramGroup.create(
                group_id=12345,
                title="Performance Test Group",
                username="perfgroup"
            )
            
            # Bulk-Insert von 1000 Dateien
            import time
            start_time = time.time()
            
            with database.atomic():
                for i in range(1000):
                    AudioFile.create(
                        file_id=f"perf_file_{i}",
                        file_unique_id=f"perf_unique_{i}",
                        file_name=f"perf_song_{i}.mp3",
                        file_size=1000000,
                        mime_type="audio/mpeg",
                        group=group
                    )
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Sollte in weniger als 10 Sekunden abgeschlossen sein
            assert duration < 10.0
            
            # Verifikation
            total_files = AudioFile.select().count()
            assert total_files == 1000
            
        finally:
            close_db()
            if Path(temp_path).exists():
                os.unlink(temp_path)


class TestDatabaseErrorHandling:
    """Tests für Datenbankfehlerbehandlung."""
    
    def test_database_locked_error(self):
        """Test Behandlung von Database-Locked-Fehlern."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            temp_path = temp_db.name
        
        try:
            database = init_db(temp_path)
            
            # Simuliere Lock durch zweite Verbindung
            with patch.object(database, 'execute_sql') as mock_execute:
                mock_execute.side_effect = OperationalError("database is locked")
                
                with pytest.raises(OperationalError, match="database is locked"):
                    TelegramGroup.create(
                        group_id=12345,
                        title="Test Group",
                        username="testgroup"
                    )
            
        finally:
            close_db()
            if Path(temp_path).exists():
                os.unlink(temp_path)
    
    def test_invalid_query_error(self):
        """Test Behandlung von ungültigen Queries."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            temp_path = temp_db.name
        
        try:
            database = init_db(temp_path)
            
            # Ungültiger Query
            with pytest.raises(OperationalError):
                database.execute_sql("INVALID SQL STATEMENT")
            
        finally:
            close_db()
            if Path(temp_path).exists():
                os.unlink(temp_path)