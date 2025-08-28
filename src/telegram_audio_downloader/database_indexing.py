"""
Datenbank-Indizierung für den Telegram Audio Downloader.

Optimiert die Datenbankperformance durch strategische Indizierung:
- AudioFile.file_id (eindeutig)
- AudioFile.status (häufige Abfragen)
- AudioFile.group (Fremdschlüssel)
- TelegramGroup.group_id (eindeutig)
- AudioFile.downloaded_at (Sortierung/Filterung)
"""

from typing import List
from peewee import OperationalError
from playhouse.migrate import SqliteMigrator, migrate

from .models import AudioFile, TelegramGroup, db
from .logging_config import get_logger

logger = get_logger(__name__)


class DatabaseIndexer:
    """Verwaltet die Datenbankindizierung."""
    
    def __init__(self):
        """Initialisiert den DatabaseIndexer."""
        self.migrator = SqliteMigrator(db)
        self.existing_indexes = set()
        self._load_existing_indexes()
        
    def _load_existing_indexes(self) -> None:
        """Lädt die vorhandenen Indizes aus der Datenbank."""
        try:
            # Abfrage der vorhandenen Indizes
            cursor = db.execute_sql("SELECT name FROM sqlite_master WHERE type='index';")
            for row in cursor.fetchall():
                self.existing_indexes.add(row[0])
            logger.debug(f"Gefundene Indizes: {self.existing_indexes}")
        except Exception as e:
            logger.error(f"Fehler beim Laden der vorhandenen Indizes: {e}")
    
    def create_index(self, table_name: str, column_name: str, unique: bool = False, 
                     index_name: str = None) -> bool:
        """
        Erstellt einen Index für eine Spalte.
        
        Args:
            table_name: Name der Tabelle
            column_name: Name der Spalte
            unique: Ob der Index eindeutig sein soll
            index_name: Optionaler Name für den Index
            
        Returns:
            True, wenn der Index erfolgreich erstellt wurde
        """
        # Generiere Index-Name, wenn nicht angegeben
        if not index_name:
            index_name = f"idx_{table_name}_{column_name}"
            if unique:
                index_name = f"unique_{index_name}"
        
        # Prüfe, ob der Index bereits existiert
        if index_name in self.existing_indexes:
            logger.debug(f"Index {index_name} existiert bereits")
            return True
        
        try:
            # Erstelle den Index
            if unique:
                db.execute_sql(
                    f"CREATE UNIQUE INDEX IF NOT EXISTS {index_name} "
                    f"ON {table_name} ({column_name});"
                )
            else:
                db.execute_sql(
                    f"CREATE INDEX IF NOT EXISTS {index_name} "
                    f"ON {table_name} ({column_name});"
                )
            
            # Aktualisiere die Liste der vorhandenen Indizes
            self.existing_indexes.add(index_name)
            logger.info(f"Index {index_name} erfolgreich erstellt")
            return True
            
        except OperationalError as e:
            logger.error(f"Fehler beim Erstellen des Index {index_name}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unerwarteter Fehler beim Erstellen des Index {index_name}: {e}")
            return False
    
    def create_composite_index(self, table_name: str, columns: List[str], 
                              index_name: str = None) -> bool:
        """
        Erstellt einen zusammengesetzten Index für mehrere Spalten.
        
        Args:
            table_name: Name der Tabelle
            columns: Liste der Spaltennamen
            index_name: Optionaler Name für den Index
            
        Returns:
            True, wenn der Index erfolgreich erstellt wurde
        """
        # Generiere Index-Name, wenn nicht angegeben
        if not index_name:
            cols_str = "_".join(columns)
            index_name = f"idx_{table_name}_{cols_str}"
        
        # Prüfe, ob der Index bereits existiert
        if index_name in self.existing_indexes:
            logger.debug(f"Index {index_name} existiert bereits")
            return True
        
        try:
            # Erstelle den zusammengesetzten Index
            columns_str = ", ".join(columns)
            db.execute_sql(
                f"CREATE INDEX IF NOT EXISTS {index_name} "
                f"ON {table_name} ({columns_str});"
            )
            
            # Aktualisiere die Liste der vorhandenen Indizes
            self.existing_indexes.add(index_name)
            logger.info(f"Zusammengesetzter Index {index_name} erfolgreich erstellt")
            return True
            
        except OperationalError as e:
            logger.error(f"Fehler beim Erstellen des zusammengesetzten Index {index_name}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unerwarteter Fehler beim Erstellen des zusammengesetzten Index {index_name}: {e}")
            return False
    
    def optimize_database(self) -> None:
        """Optimiert die Datenbank durch Erstellen strategischer Indizes."""
        logger.info("Starte Datenbank-Optimierung durch Indizierung")
        
        # Indizes für AudioFile
        self.create_index("audio_files", "file_id", unique=True)
        self.create_index("audio_files", "status")
        self.create_index("audio_files", "group_id")  # Fremdschlüssel
        self.create_index("audio_files", "downloaded_at")
        self.create_index("audio_files", "title")
        self.create_index("audio_files", "performer")
        
        # Indizes für TelegramGroup
        self.create_index("telegram_groups", "group_id", unique=True)
        self.create_index("telegram_groups", "title")
        self.create_index("telegram_groups", "username")
        
        # Zusammengesetzte Indizes für häufige Abfragen
        self.create_composite_index("audio_files", ["group_id", "status"])
        self.create_composite_index("audio_files", ["status", "downloaded_at"])
        self.create_composite_index("audio_files", ["group_id", "downloaded_at"])
        
        logger.info("Datenbank-Optimierung abgeschlossen")
    
    def get_index_statistics(self) -> dict:
        """
        Gibt Statistiken über die vorhandenen Indizes zurück.
        
        Returns:
            Dictionary mit Index-Statistiken
        """
        try:
            # Abfrage der Index-Statistiken
            cursor = db.execute_sql("""
                SELECT 
                    name,
                    tbl_name,
                    sql
                FROM sqlite_master 
                WHERE type='index' AND name NOT LIKE 'sqlite_%'
                ORDER BY tbl_name, name;
            """)
            
            indexes = []
            for row in cursor.fetchall():
                indexes.append({
                    "name": row[0],
                    "table": row[1],
                    "definition": row[2]
                })
            
            return {
                "total_indexes": len(indexes),
                "indexes": indexes
            }
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Index-Statistiken: {e}")
            return {"total_indexes": 0, "indexes": []}
    
    def drop_index(self, index_name: str) -> bool:
        """
        Löscht einen Index.
        
        Args:
            index_name: Name des zu löschenden Index
            
        Returns:
            True, wenn der Index erfolgreich gelöscht wurde
        """
        try:
            db.execute_sql(f"DROP INDEX IF EXISTS {index_name};")
            if index_name in self.existing_indexes:
                self.existing_indexes.remove(index_name)
            logger.info(f"Index {index_name} erfolgreich gelöscht")
            return True
        except OperationalError as e:
            logger.error(f"Fehler beim Löschen des Index {index_name}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unerwarteter Fehler beim Löschen des Index {index_name}: {e}")
            return False


def optimize_database_indexes() -> None:
    """
    Optimiert die Datenbankindizes.
    Diese Funktion sollte beim Start der Anwendung aufgerufen werden.
    """
    try:
        indexer = DatabaseIndexer()
        indexer.optimize_database()
        
        # Zeige Index-Statistiken
        stats = indexer.get_index_statistics()
        logger.info(f"Datenbank hat {stats['total_indexes']} Indizes")
        
    except Exception as e:
        logger.error(f"Fehler bei der Datenbank-Indizierung: {e}")