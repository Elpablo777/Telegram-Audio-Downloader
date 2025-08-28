"""
Datenbank-Verbindungspooling für den Telegram Audio Downloader.

Vorteile:
- Bessere Leistung
- Geringere Latenz
- Bessere Skalierbarkeit
- Kontrollierter Ressourcenverbrauch
"""

import threading
import time
from typing import Optional, List
from contextlib import contextmanager
from queue import Queue, Empty
from dataclasses import dataclass, field

from peewee import SqliteDatabase
from .logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class DatabaseConnection:
    """Repräsentiert eine Datenbankverbindung im Pool."""
    connection: SqliteDatabase
    last_used: float = field(default_factory=time.time)
    in_use: bool = False


class DatabaseConnectionPool:
    """Verwaltet einen Pool von Datenbankverbindungen."""
    
    def __init__(self, db_path: str, min_connections: int = 2, max_connections: int = 10,
                 connection_timeout: float = 30.0):
        """
        Initialisiert den Datenbankverbindungspool.
        
        Args:
            db_path: Pfad zur Datenbankdatei
            min_connections: Minimale Anzahl von Verbindungen im Pool
            max_connections: Maximale Anzahl von Verbindungen im Pool
            connection_timeout: Timeout für das Warten auf eine Verbindung (Sekunden)
        """
        self.db_path = db_path
        self.min_connections = min_connections
        self.max_connections = max_connections
        self.connection_timeout = connection_timeout
        
        # Thread-sichere Queue für verfügbare Verbindungen
        self.available_connections: Queue[DatabaseConnection] = Queue(maxsize=max_connections)
        
        # Liste aller Verbindungen (für Aufräumarbeiten)
        self.all_connections: List[DatabaseConnection] = []
        
        # Lock für Thread-Sicherheit
        self._lock = threading.RLock()
        
        # Pool initialisieren
        self._initialize_pool()
        
        logger.info(f"DatabaseConnectionPool initialisiert mit {min_connections}-{max_connections} Verbindungen")
    
    def _initialize_pool(self) -> None:
        """Initialisiert den Verbindungspool mit minimalen Verbindungen."""
        with self._lock:
            for i in range(self.min_connections):
                try:
                    conn = self._create_connection()
                    db_conn = DatabaseConnection(connection=conn)
                    self.available_connections.put(db_conn)
                    self.all_connections.append(db_conn)
                    logger.debug(f"Verbindung {i+1} zum Pool hinzugefügt")
                except Exception as e:
                    logger.error(f"Fehler beim Erstellen der Verbindung {i+1}: {e}")
    
    def _create_connection(self) -> SqliteDatabase:
        """
        Erstellt eine neue Datenbankverbindung.
        
        Returns:
            Neue SqliteDatabase-Instanz
        """
        db = SqliteDatabase(
            self.db_path,
            pragmas={
                "journal_mode": "wal",
                "cache_size": -1024 * 32,  # 32MB Cache
                "foreign_keys": 1,
                "ignore_check_constraints": 0,
                "synchronous": 0,
            },
        )
        
        # Verbindung öffnen
        db.connect()
        return db
    
    @contextmanager
    def get_connection(self):
        """
        Gibt eine Datenbankverbindung aus dem Pool zurück.
        
        Yields:
            SqliteDatabase-Instanz
        """
        conn_wrapper: Optional[DatabaseConnection] = None
        
        try:
            # Versuche, eine Verbindung aus dem Pool zu erhalten
            try:
                conn_wrapper = self.available_connections.get(timeout=self.connection_timeout)
                conn_wrapper.in_use = True
                conn_wrapper.last_used = time.time()
                logger.debug("Verbindung aus Pool erhalten")
            except Empty:
                # Pool ist leer - erstelle eine neue Verbindung, wenn möglich
                with self._lock:
                    if len(self.all_connections) < self.max_connections:
                        try:
                            conn = self._create_connection()
                            conn_wrapper = DatabaseConnection(connection=conn)
                            self.all_connections.append(conn_wrapper)
                            conn_wrapper.in_use = True
                            conn_wrapper.last_used = time.time()
                            logger.debug("Neue Verbindung erstellt")
                        except Exception as e:
                            logger.error(f"Fehler beim Erstellen einer neuen Verbindung: {e}")
                            raise
                    else:
                        # Maximale Anzahl erreicht - warte auf eine verfügbare Verbindung
                        conn_wrapper = self.available_connections.get(timeout=self.connection_timeout)
                        conn_wrapper.in_use = True
                        conn_wrapper.last_used = time.time()
                        logger.debug("Verbindung aus Pool erhalten (nach Warten)")
            
            # Gib die Verbindung zurück
            yield conn_wrapper.connection
            
        except Exception as e:
            logger.error(f"Fehler bei der Verbindungsverwendung: {e}")
            raise
        finally:
            # Verbindung zurückgeben
            if conn_wrapper:
                try:
                    # Schließe offene Transaktionen
                    if not conn_wrapper.connection.is_closed():
                        try:
                            conn_wrapper.connection.rollback()
                        except Exception as rollback_error:
                            logger.debug(f"Rollback fehlgeschlagen (nicht kritisch): {rollback_error}")
                    
                    # Verbindung zurück in den Pool
                    conn_wrapper.in_use = False
                    self.available_connections.put(conn_wrapper)
                    logger.debug("Verbindung zurück in Pool gelegt")
                except Exception as e:
                    logger.error(f"Fehler beim Zurücklegen der Verbindung in den Pool: {e}")
    
    def get_connection_stats(self) -> dict:
        """
        Gibt Statistiken über den Verbindungspool zurück.
        
        Returns:
            Dictionary mit Pool-Statistiken
        """
        with self._lock:
            total_connections = len(self.all_connections)
            available_connections = self.available_connections.qsize()
            in_use_connections = total_connections - available_connections
            
            return {
                "total_connections": total_connections,
                "available_connections": available_connections,
                "in_use_connections": in_use_connections,
                "min_connections": self.min_connections,
                "max_connections": self.max_connections
            }
    
    def close_all_connections(self) -> None:
        """Schließt alle Verbindungen im Pool."""
        with self._lock:
            for conn_wrapper in self.all_connections:
                try:
                    if not conn_wrapper.connection.is_closed():
                        conn_wrapper.connection.close()
                except Exception as e:
                    logger.error(f"Fehler beim Schließen einer Verbindung: {e}")
            
            # Leere die Queues
            while not self.available_connections.empty():
                try:
                    self.available_connections.get_nowait()
                except Empty:
                    break
            
            self.all_connections.clear()
            logger.info("Alle Verbindungen geschlossen")
    
    def cleanup_idle_connections(self, idle_timeout: float = 300.0) -> None:
        """
        Bereinigt inaktive Verbindungen.
        
        Args:
            idle_timeout: Zeit in Sekunden, nach der inaktive Verbindungen geschlossen werden
        """
        with self._lock:
            current_time = time.time()
            active_connections = []
            
            # Prüfe alle Verbindungen
            for conn_wrapper in self.all_connections:
                # Schließe inaktive Verbindungen, die über dem Minimum liegen
                if (not conn_wrapper.in_use and 
                    current_time - conn_wrapper.last_used > idle_timeout and
                    len(active_connections) >= self.min_connections):
                    
                    try:
                        if not conn_wrapper.connection.is_closed():
                            conn_wrapper.connection.close()
                        logger.debug("Inaktive Verbindung geschlossen")
                    except Exception as e:
                        logger.error(f"Fehler beim Schließen einer inaktiven Verbindung: {e}")
                else:
                    active_connections.append(conn_wrapper)
            
            # Aktualisiere die Liste der aktiven Verbindungen
            self.all_connections = active_connections
            
            # Fülle den Pool ggf. wieder auf
            while len(self.all_connections) < self.min_connections:
                try:
                    conn = self._create_connection()
                    conn_wrapper = DatabaseConnection(connection=conn)
                    self.available_connections.put(conn_wrapper)
                    self.all_connections.append(conn_wrapper)
                    logger.debug("Verbindung zur Aufrechterhaltung des Minimums erstellt")
                except Exception as e:
                    logger.error(f"Fehler beim Erstellen einer Verbindung zur Aufrechterhaltung des Minimums: {e}")
                    break


# Globale Instanz des ConnectionPools
_connection_pool: Optional[DatabaseConnectionPool] = None


def get_connection_pool(db_path: str = None) -> DatabaseConnectionPool:
    """
    Gibt die globale Instanz des DatabaseConnectionPool zurück.
    
    Args:
        db_path: Pfad zur Datenbankdatei (nur für die erste Initialisierung)
        
    Returns:
        DatabaseConnectionPool-Instanz
    """
    global _connection_pool
    if _connection_pool is None:
        if db_path is None:
            raise ValueError("db_path ist erforderlich für die erste Initialisierung des ConnectionPools")
        _connection_pool = DatabaseConnectionPool(db_path)
    return _connection_pool


@contextmanager
def pooled_database_connection(db_path: str = None):
    """
    Kontextmanager für eine gepoolte Datenbankverbindung.
    
    Args:
        db_path: Pfad zur Datenbankdatei
        
    Yields:
        SqliteDatabase-Instanz
    """
    pool = get_connection_pool(db_path)
    with pool.get_connection() as conn:
        yield conn


def get_pool_stats() -> dict:
    """
    Gibt Statistiken über den Verbindungspool zurück.
    
    Returns:
        Dictionary mit Pool-Statistiken
    """
    try:
        pool = get_connection_pool()
        return pool.get_connection_stats()
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Pool-Statistiken: {e}")
        return {}


def cleanup_pool_connections(idle_timeout: float = 300.0) -> None:
    """
    Bereinigt inaktive Verbindungen im Pool.
    
    Args:
        idle_timeout: Zeit in Sekunden, nach der inaktive Verbindungen geschlossen werden
    """
    try:
        pool = get_connection_pool()
        pool.cleanup_idle_connections(idle_timeout)
    except Exception as e:
        logger.error(f"Fehler bei der Bereinigung der Pool-Verbindungen: {e}")