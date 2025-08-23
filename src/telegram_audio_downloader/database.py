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

# Standard-Datenbankpfad
DEFAULT_DB_PATH = Path("data/audio_downloader.db")
DB_PATH = os.getenv("DB_PATH", str(DEFAULT_DB_PATH))


@with_database_error_handling
def init_db(db_path: Optional[str] = None) -> SqliteDatabase:
    """
    Initialisiert die Datenbank und erstellt die Tabellen, falls sie nicht existieren.

    Args:
        db_path: Optionaler Pfad zur Datenbankdatei

    Returns:
        Die initialisierte Datenbank-Instanz
    """
    # Datenbankpfad setzen
    if db_path is None:
        db_path = DB_PATH

    # Verzeichnis erstellen, falls nicht vorhanden
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    # Datenbank initialisieren
    db.init(
        db_path,
        pragmas={
            "journal_mode": "wal",  # Bessere Parallelität
            "cache_size": -1024 * 32,  # 32MB Cache
            "foreign_keys": 1,  # Fremdschlüssel erzwingen
            "ignore_check_constraints": 0,
            "synchronous": 0,  # Schnellere Schreibvorgänge
        },
    )

    # Tabellen erstellen
    with db:
        db.create_tables([TelegramGroup, AudioFile], safe=True)

        # Datenbank-Migrationen durchführen
        migrator = SqliteMigrator(db)

        try:
            # Beispiel für eine zukünftige Migration:
            # from peewee import IntegerField
            # migrate(
            #     migrator.add_column('audio_files', 'new_field', IntegerField(null=True))
            # )
            pass
        except OperationalError as e:
            handle_database_error(e, "init_db_migration")
            raise DatabaseError(f"Fehler bei der Datenbankmigration: {e}")

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