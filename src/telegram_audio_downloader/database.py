"""
Datenbank-Initialisierung und -Verwaltung für den Telegram Audio Downloader.
"""

import os
from pathlib import Path
from typing import Optional

from peewee import OperationalError, SqliteDatabase
from playhouse.migrate import SqliteMigrator

from .db_error_handler import handle_database_error, with_database_error_handling
from .error_handling import DatabaseError
from .models import AudioFile, TelegramGroup, db
from .logging_config import get_logger
from .database_indexing import optimize_database_indexes
from .database_migrations import run_migrations
from .extended_models import create_extended_tables

logger = get_logger(__name__)

# Standard-Datenbankpfad
DEFAULT_DB_PATH = Path("data/audio_downloader.db")
DB_PATH = os.getenv("DB_PATH", str(DEFAULT_DB_PATH))


class Database:
    """Datenbank-Wrapper-Klasse für den Telegram Audio Downloader."""
    
    _instance = None
    _initialized = False
    
    def __new__(cls, db_path: Optional[str] = None):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialisiert die Datenbank.
        
        Args:
            db_path: Optionaler Pfad zur Datenbankdatei
        """
        if Database._initialized:
            return
            
        self.db_path = db_path or os.getenv('DATABASE_PATH', str(DEFAULT_DB_PATH))
        self.db_instance = None
        Database._initialized = True
        
    def init(self) -> SqliteDatabase:
        """
        Initialisiert die Datenbank.
        
        Returns:
            Initialisierte SqliteDatabase-Instanz
        """
        global db
        
        # Stelle sicher, dass das Datenbankverzeichnis existiert
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialisiere die Datenbank mit dem Pfad
        if db.database is None:
            db.init(self.db_path)
        elif db.database != self.db_path:
            # Wenn bereits initialisiert, aber mit anderem Pfad, schließe und reinitialisiere
            if not db.is_closed():
                db.close()
            db.init(self.db_path)
            
        self.db_instance = db
        
        # Verbinde mit der Datenbank
        if db.is_closed():
            db.connect()
        
        # Erstelle die Tabellen
        db.create_tables([TelegramGroup, AudioFile], safe=True)
        
        # Füge die neuen Felder hinzu, falls sie noch nicht existieren
        try:
            with db.atomic():
                # Prüfe, ob die Spalten existieren und füge sie ggf. hinzu
                cursor = db.execute_sql("PRAGMA table_info(audio_files);")
                columns = {row[1]: row[2] for row in cursor.fetchall()}  # {name: type}
                
                # Füge mime_type hinzu, falls nicht vorhanden
                if 'mime_type' not in columns:
                    db.execute_sql("ALTER TABLE audio_files ADD COLUMN mime_type VARCHAR(100) NULL;")
                
                # Füge resume_offset hinzu, falls nicht vorhanden
                if 'resume_offset' not in columns:
                    db.execute_sql("ALTER TABLE audio_files ADD COLUMN resume_offset INTEGER DEFAULT 0;")
                
                # Füge resume_checksum hinzu, falls nicht vorhanden
                if 'resume_checksum' not in columns:
                    db.execute_sql("ALTER TABLE audio_files ADD COLUMN resume_checksum VARCHAR(255) NULL;")
                
                # Füge local_path hinzu, falls nicht vorhanden
                if 'local_path' not in columns:
                    db.execute_sql("ALTER TABLE audio_files ADD COLUMN local_path VARCHAR(500) NULL;")
                
                # Füge partial_file_path hinzu, falls nicht vorhanden
                if 'partial_file_path' not in columns:
                    db.execute_sql("ALTER TABLE audio_files ADD COLUMN partial_file_path VARCHAR(500) NULL;")
                
                # Füge downloaded_bytes hinzu, falls nicht vorhanden
                if 'downloaded_bytes' not in columns:
                    db.execute_sql("ALTER TABLE audio_files ADD COLUMN downloaded_bytes INTEGER DEFAULT 0;")
                
                # Füge last_attempt_at hinzu, falls nicht vorhanden
                if 'last_attempt_at' not in columns:
                    db.execute_sql("ALTER TABLE audio_files ADD COLUMN last_attempt_at DATETIME NULL;")
                
                # Füge message_id hinzu, falls nicht vorhanden
                if 'message_id' not in columns:
                    db.execute_sql("ALTER TABLE audio_files ADD COLUMN message_id INTEGER NULL;")
        except Exception as e:
            logger.warning(f"Fehler beim Hinzufügen der Felder: {e}")
        
        # Optimiere die Datenbankindizes
        try:
            optimize_database_indexes()
        except Exception as e:
            logger.warning(f"Fehler bei der Datenbank-Indizierung: {e}")
            # Nicht kritisch - die Anwendung kann weiterlaufen
        
        # Führe Datenbankmigrationen aus
        try:
            run_migrations()
        except Exception as e:
            logger.warning(f"Fehler bei der Datenbank-Migration: {e}")
            # Nicht kritisch - die Anwendung kann weiterlaufen
        
        # Erstelle erweiterte Tabellen
        try:
            create_extended_tables()
        except Exception as e:
            logger.warning(f"Fehler beim Erstellen der erweiterten Tabellen: {e}")
            # Nicht kritisch - die Anwendung kann weiterlaufen

        logger.info(f"Datenbank erfolgreich initialisiert: {self.db_path}")
        return db

    def close(self) -> None:
        """Schließt die Datenbankverbindung."""
        global db
        if db and not db.is_closed():
            db.close()

    def reset(self) -> SqliteDatabase:
        """
        Setzt die Datenbank zurück (nur für Testzwecke).
        Achtung: Löscht alle Daten!

        Returns:
            Die zurückgesetzte Datenbank-Instanz
        """
        global db
        if db and db.is_closed():
            db.connect()

        with db.atomic():
            # Alle Tabellen löschen
            db.drop_tables([AudioFile, TelegramGroup], safe=True, cascade=True)

            # Tabellen neu erstellen
            db.create_tables([TelegramGroup, AudioFile])

        return db


@with_database_error_handling
def init_db(db_path: Optional[str] = None) -> SqliteDatabase:
    """
    Initialisiert die Datenbank.
    
    Args:
        db_path: Optionaler Pfad zur Datenbankdatei
        
    Returns:
        Initialisierte SqliteDatabase-Instanz
    """
    database = Database(db_path)
    return database.init()


@with_database_error_handling
def close_db() -> None:
    """Schließt die Datenbankverbindung."""
    global db
    if db and not db.is_closed():
        db.close()


@with_database_error_handling
def reset_db() -> SqliteDatabase:
    """Setzt die Datenbank zurück (nicht für Produktivumgebung geeignet)."""
    global db
    if not db.is_closed():
        db.close()
    
    # Tabellen löschen und neu erstellen
    db.drop_tables([AudioFile, TelegramGroup], safe=True)
    db.create_tables([AudioFile, TelegramGroup], safe=True)
    
    logger.info("Datenbank zurückgesetzt")
    return db


@with_database_error_handling
def get_db_connection() -> SqliteDatabase:
    """
    Gibt die aktuelle Datenbankverbindung zurück.
    
    Returns:
        Aktive SqliteDatabase-Instanz
    """
    global db
    if db is None or db.is_closed():
        init_db()
    return db

