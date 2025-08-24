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


@with_database_error_handling
def init_db(db_path: Optional[str] = None) -> SqliteDatabase:
    """
    Initialisiert die Datenbank.
    
    Args:
        db_path: Optionaler Pfad zur Datenbankdatei
        
    Returns:
        Initialisierte SqliteDatabase-Instanz
    """
    global db
    
    if db_path is None:
        db_path = os.getenv('DATABASE_PATH', 'data/telegram_audio.db')
    
    # Stelle sicher, dass das Datenbankverzeichnis existiert
    db_dir = Path(db_path).parent
    db_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialisiere die Datenbank
    db = SqliteDatabase(db_path)
    
    # Verbinde mit der Datenbank
    db.connect()
    
    # Erstelle die Tabellen
    db.create_tables([TelegramGroup, AudioFile], safe=True)
    
    # Füge die neuen Felder hinzu, falls sie noch nicht existieren
    try:
        with db.atomic():
            # Prüfe, ob die resume_offset-Spalte existiert
            cursor = db.execute_sql("PRAGMA table_info(audio_files);")
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'resume_offset' not in columns:
                db.execute_sql("ALTER TABLE audio_files ADD COLUMN resume_offset INTEGER DEFAULT 0;")
            
            if 'resume_checksum' not in columns:
                db.execute_sql("ALTER TABLE audio_files ADD COLUMN resume_checksum VARCHAR(255) NULL;")
    except Exception as e:
        logger.warning(f"Fehler beim Hinzufügen der Resume-Felder: {e}")
    
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

    return db


@with_database_error_handling
def close_db() -> None:
    """Schließt die Datenbankverbindung."""
    if not db.is_closed():
        db.close()


@with_database_error_handling
def reset_db() -> SqliteDatabase:
    """
    Setzt die Datenbank zurück (nur für Testzwecke).
    Achtung: Löscht alle Daten!

    Returns:
        Die zurückgesetzte Datenbank-Instanz
    """
    if db.is_closed():
        db.connect()

    with db.atomic():
        # Alle Tabellen löschen
        db.drop_tables([AudioFile, TelegramGroup], safe=True, cascade=True)

        # Tabellen neu erstellen
        db.create_tables([TelegramGroup, AudioFile])

    return db