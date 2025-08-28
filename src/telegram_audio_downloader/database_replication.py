"""
Datenbank-Replikation für den Telegram Audio Downloader.

Vorteile:
- Ausfallsicherheit
- Leseskalierung
- Geografische Verteilung
- Lastverteilung
"""

import threading
import time
import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any, Callable
from pathlib import Path
from dataclasses import dataclass, field

from .models import db
from .logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class ReplicaInfo:
    """Informationen über eine Datenbank-Replik."""
    replica_id: str
    host: str
    port: int
    database_path: str
    is_master: bool = False
    is_active: bool = True
    last_sync: Optional[datetime] = None
    sync_lag_seconds: float = 0.0
    error_count: int = 0
    last_error: Optional[str] = None


class DatabaseReplicator:
    """Verwaltet die Datenbank-Replikation."""
    
    def __init__(self, master_db_path: str, replicas_config: List[Dict[str, Any]] = None):
        """
        Initialisiert den DatabaseReplicator.
        
        Args:
            master_db_path: Pfad zur Master-Datenbank
            replicas_config: Konfiguration der Replikas
        """
        self.master_db_path = Path(master_db_path)
        self.replicas: Dict[str, ReplicaInfo] = {}
        self.is_replicating = False
        self.replication_thread = None
        self.replication_interval = 30  # Sekunden
        self.sync_callbacks: List[Callable] = []
        
        # Initialisiere Replikas
        if replicas_config:
            for config in replicas_config:
                self.add_replica(**config)
        
        logger.info("DatabaseReplicator initialisiert")
    
    def add_replica(self, replica_id: str, host: str, port: int, database_path: str,
                   is_master: bool = False) -> None:
        """
        Fügt eine Replika hinzu.
        
        Args:
            replica_id: Eindeutige ID der Replika
            host: Host der Replika
            port: Port der Replika
            database_path: Pfad zur Replika-Datenbank
            is_master: Ob es sich um die Master-Replika handelt
        """
        replica = ReplicaInfo(
            replica_id=replica_id,
            host=host,
            port=port,
            database_path=database_path,
            is_master=is_master
        )
        self.replicas[replica_id] = replica
        
        if is_master:
            logger.info(f"Master-Replika hinzugefügt: {replica_id}")
        else:
            logger.info(f"Slave-Replika hinzugefügt: {replica_id}")
    
    def start_replication(self) -> None:
        """Startet die Replikation."""
        if self.is_replicating:
            return
            
        self.is_replicating = True
        self.replication_thread = threading.Thread(target=self._replication_loop, daemon=True)
        self.replication_thread.start()
        logger.info("Datenbank-Replikation gestartet")
    
    def stop_replication(self) -> None:
        """Stoppt die Replikation."""
        self.is_replicating = False
        if self.replication_thread and self.replication_thread.is_alive():
            self.replication_thread.join(timeout=5)
        logger.info("Datenbank-Replikation gestoppt")
    
    def _replication_loop(self) -> None:
        """Hauptschleife für die Replikation."""
        while self.is_replicating:
            try:
                # Führe die Replikation durch
                self._perform_replication()
                
                # Führe registrierte Callbacks aus
                self._execute_sync_callbacks()
                
                # Warte bis zur nächsten Replikation
                time.sleep(self.replication_interval)
                
            except Exception as e:
                logger.error(f"Fehler im Replikations-Loop: {e}")
                time.sleep(self.replication_interval)
    
    def _perform_replication(self) -> None:
        """Führt die eigentliche Replikation durch."""
        try:
            # Hole den aktuellen WAL-Checkpoint der Master-Datenbank
            master_checkpoint = self._get_master_wal_checkpoint()
            
            # Repliziere zu allen aktiven Slave-Replikas
            for replica_id, replica in self.replicas.items():
                if not replica.is_master and replica.is_active:
                    try:
                        self._replicate_to_slave(replica, master_checkpoint)
                        replica.error_count = 0
                        replica.last_error = None
                    except Exception as e:
                        replica.error_count += 1
                        replica.last_error = str(e)
                        logger.error(f"Fehler bei der Replikation zu {replica_id}: {e}")
                        
                        # Deaktiviere Replika nach zu vielen Fehlern
                        if replica.error_count > 5:
                            replica.is_active = False
                            logger.warning(f"Replika {replica_id} deaktiviert wegen zu vieler Fehler")
            
        except Exception as e:
            logger.error(f"Fehler bei der Master-Replikation: {e}")
    
    def _get_master_wal_checkpoint(self) -> Dict[str, Any]:
        """
        Holt den aktuellen WAL-Checkpoint der Master-Datenbank.
        
        Returns:
            Dictionary mit WAL-Checkpoint-Informationen
        """
        try:
            # Schließe die aktuelle Datenbankverbindung
            if not db.is_closed():
                db.close()
            
            # Verbinde direkt mit der Master-Datenbank
            master_conn = sqlite3.connect(str(self.master_db_path))
            
            # Aktiviere WAL-Modus
            master_conn.execute("PRAGMA journal_mode=WAL;")
            
            # Hole WAL-Status
            cursor = master_conn.execute("PRAGMA wal_checkpoint(FULL);")
            checkpoint_info = cursor.fetchone()
            
            # Hole die aktuelle Zeit als Referenz
            timestamp = datetime.now()
            
            master_conn.close()
            
            # Stelle die Datenbankverbindung wieder her
            db.connect()
            
            return {
                "timestamp": timestamp,
                "checkpoint_info": checkpoint_info
            }
            
        except Exception as e:
            logger.error(f"Fehler beim Holen des Master-WAL-Checkpoint: {e}")
            # Stelle die Datenbankverbindung wieder her
            try:
                if db.is_closed():
                    db.connect()
            except Exception as connection_error:
                logger.debug(f"Wiederherstellung der Datenbankverbindung fehlgeschlagen (nicht kritisch): {connection_error}")
            raise
    
    def _replicate_to_slave(self, replica: ReplicaInfo, master_checkpoint: Dict[str, Any]) -> None:
        """
        Repliziert Daten zu einer Slave-Replika.
        
        Args:
            replica: Zielreplika
            master_checkpoint: Master-WAL-Checkpoint
        """
        try:
            replica_path = Path(replica.database_path)
            
            # Erstelle das Verzeichnis, falls es nicht existiert
            replica_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Schließe die aktuelle Datenbankverbindung
            if not db.is_closed():
                db.close()
            
            # Kopiere die Master-Datenbank zur Replika
            import shutil
            shutil.copy2(self.master_db_path, replica_path)
            
            # Kopiere WAL- und SHM-Dateien, falls sie existieren
            wal_file = self.master_db_path.with_suffix('.db-wal')
            shm_file = self.master_db_path.with_suffix('.db-shm')
            
            if wal_file.exists():
                shutil.copy2(wal_file, replica_path.with_suffix('.db-wal'))
            
            if shm_file.exists():
                shutil.copy2(shm_file, replica_path.with_suffix('.db-shm'))
            
            # Aktualisiere Replika-Informationen
            replica.last_sync = datetime.now()
            replica.sync_lag_seconds = 0.0
            
            logger.debug(f"Daten repliziert zu {replica.replica_id}")
            
        except Exception as e:
            logger.error(f"Fehler bei der Replikation zu {replica.replica_id}: {e}")
            raise
        finally:
            # Stelle die Datenbankverbindung wieder her
            try:
                if db.is_closed():
                    db.connect()
            except Exception as e:
                logger.error(f"Fehler beim Wiederherstellen der Datenbankverbindung: {e}")
    
    def _execute_sync_callbacks(self) -> None:
        """Führt registrierte Synchronisations-Callbacks aus."""
        for callback in self.sync_callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"Fehler im Synchronisations-Callback: {e}")
    
    def add_sync_callback(self, callback: Callable) -> None:
        """
        Fügt einen Synchronisations-Callback hinzu.
        
        Args:
            callback: Funktion, die nach jeder Synchronisation aufgerufen wird
        """
        self.sync_callbacks.append(callback)
        logger.debug("Synchronisations-Callback hinzugefügt")
    
    def remove_sync_callback(self, callback: Callable) -> None:
        """
        Entfernt einen Synchronisations-Callback.
        
        Args:
            callback: Zu entfernender Callback
        """
        if callback in self.sync_callbacks:
            self.sync_callbacks.remove(callback)
            logger.debug("Synchronisations-Callback entfernt")
    
    def get_replication_status(self) -> Dict[str, Any]:
        """
        Gibt den Replikationsstatus zurück.
        
        Returns:
            Dictionary mit Replikationsstatus
        """
        try:
            replica_status = []
            for replica_id, replica in self.replicas.items():
                replica_status.append({
                    "replica_id": replica.replica_id,
                    "host": replica.host,
                    "port": replica.port,
                    "is_master": replica.is_master,
                    "is_active": replica.is_active,
                    "last_sync": replica.last_sync.isoformat() if replica.last_sync else None,
                    "sync_lag_seconds": replica.sync_lag_seconds,
                    "error_count": replica.error_count,
                    "last_error": replica.last_error
                })
            
            return {
                "timestamp": datetime.now().isoformat(),
                "is_replicating": self.is_replicating,
                "replica_count": len(self.replicas),
                "active_replicas": len([r for r in self.replicas.values() if r.is_active]),
                "replicas": replica_status
            }
            
        except Exception as e:
            logger.error(f"Fehler beim Abrufen des Replikationsstatus: {e}")
            return {}
    
    def promote_replica(self, replica_id: str) -> bool:
        """
        Fördert eine Replika zum Master.
        
        Args:
            replica_id: ID der zu fördernden Replika
            
        Returns:
            True, wenn die Förderung erfolgreich war
        """
        try:
            if replica_id not in self.replicas:
                logger.error(f"Replika {replica_id} nicht gefunden")
                return False
            
            # Setze alle Replikas auf Slave
            for replica in self.replicas.values():
                replica.is_master = False
            
            # Setze die ausgewählte Replika auf Master
            self.replicas[replica_id].is_master = True
            
            logger.info(f"Replika {replica_id} zum Master befördert")
            return True
            
        except Exception as e:
            logger.error(f"Fehler bei der Förderung der Replika {replica_id}: {e}")
            return False
    
    def enable_replica(self, replica_id: str) -> bool:
        """
        Aktiviert eine Replika.
        
        Args:
            replica_id: ID der zu aktivierenden Replika
            
        Returns:
            True, wenn die Aktivierung erfolgreich war
        """
        try:
            if replica_id not in self.replicas:
                logger.error(f"Replika {replica_id} nicht gefunden")
                return False
            
            self.replicas[replica_id].is_active = True
            self.replicas[replica_id].error_count = 0
            self.replicas[replica_id].last_error = None
            
            logger.info(f"Replika {replica_id} aktiviert")
            return True
            
        except Exception as e:
            logger.error(f"Fehler bei der Aktivierung der Replika {replica_id}: {e}")
            return False
    
    def disable_replica(self, replica_id: str) -> bool:
        """
        Deaktiviert eine Replika.
        
        Args:
            replica_id: ID der zu deaktivierenden Replika
            
        Returns:
            True, wenn die Deaktivierung erfolgreich war
        """
        try:
            if replica_id not in self.replicas:
                logger.error(f"Replika {replica_id} nicht gefunden")
                return False
            
            self.replicas[replica_id].is_active = False
            
            logger.info(f"Replika {replica_id} deaktiviert")
            return True
            
        except Exception as e:
            logger.error(f"Fehler bei der Deaktivierung der Replika {replica_id}: {e}")
            return False


class ReadReplicaRouter:
    """Leitet Leseabfragen an Replikas weiter."""
    
    def __init__(self, replicator: DatabaseReplicator):
        """
        Initialisiert den ReadReplicaRouter.
        
        Args:
            replicator: DatabaseReplicator-Instanz
        """
        self.replicator = replicator
        self.current_replica_index = 0
        
        logger.info("ReadReplicaRouter initialisiert")
    
    def get_read_replica(self) -> Optional[ReplicaInfo]:
        """
        Gibt eine verfügbare Read-Replika zurück.
        
        Returns:
            ReplicaInfo oder None, wenn keine verfügbar
        """
        try:
            # Hole aktive Slave-Replikas
            active_slaves = [
                replica for replica in self.replicator.replicas.values()
                if not replica.is_master and replica.is_active
            ]
            
            if not active_slaves:
                return None
            
            # Round-Robin-Verteilung
            self.current_replica_index = (self.current_replica_index + 1) % len(active_slaves)
            return active_slaves[self.current_replica_index]
            
        except Exception as e:
            logger.error(f"Fehler beim Auswählen der Read-Replika: {e}")
            return None
    
    def execute_read_query(self, query: str, params: tuple = ()) -> Any:
        """
        Führt eine Leseabfrage auf einer Replika aus.
        
        Args:
            query: SQL-Abfrage
            params: Abfrageparameter
            
        Returns:
            Abfrageergebnis
        """
        try:
            replica = self.get_read_replica()
            if not replica:
                # Fallback auf Master-Datenbank
                logger.warning("Keine Read-Replika verfügbar, Fallback auf Master")
                return db.execute_sql(query, params)
            
            # Verbinde mit der Replika-Datenbank
            replica_conn = sqlite3.connect(replica.database_path)
            cursor = replica_conn.execute(query, params)
            result = cursor.fetchall()
            replica_conn.close()
            
            logger.debug(f"Leseabfrage auf Replika {replica.replica_id} ausgeführt")
            return result
            
        except Exception as e:
            logger.error(f"Fehler bei der Ausführung der Leseabfrage: {e}")
            raise


# Globale Instanzen
_replicator: Optional[DatabaseReplicator] = None
_read_router: Optional[ReadReplicaRouter] = None


def get_database_replicator() -> DatabaseReplicator:
    """
    Gibt die globale Instanz des DatabaseReplicator zurück.
    
    Returns:
        DatabaseReplicator-Instanz
    """
    global _replicator
    if _replicator is None:
        # In einer echten Implementierung würden wir hier die Konfiguration laden
        _replicator = DatabaseReplicator(master_db_path=db.database)
    return _replicator


def get_read_replica_router() -> ReadReplicaRouter:
    """
    Gibt die globale Instanz des ReadReplicaRouter zurück.
    
    Returns:
        ReadReplicaRouter-Instanz
    """
    global _read_router
    if _read_router is None:
        replicator = get_database_replicator()
        _read_router = ReadReplicaRouter(replicator)
    return _read_router


def start_database_replication(replicas_config: List[Dict[str, Any]] = None) -> None:
    """
    Startet die Datenbank-Replikation.
    
    Args:
        replicas_config: Konfiguration der Replikas
    """
    try:
        replicator = get_database_replicator()
        
        # Füge Replikas hinzu, falls konfiguriert
        if replicas_config:
            for config in replicas_config:
                replicator.add_replica(**config)
        
        replicator.start_replication()
    except Exception as e:
        logger.error(f"Fehler beim Starten der Datenbank-Replikation: {e}")


def stop_database_replication() -> None:
    """Stoppt die Datenbank-Replikation."""
    try:
        replicator = get_database_replicator()
        replicator.stop_replication()
    except Exception as e:
        logger.error(f"Fehler beim Stoppen der Datenbank-Replikation: {e}")


def get_replication_status() -> Dict[str, Any]:
    """
    Gibt den Datenbank-Replikationsstatus zurück.
    
    Returns:
        Dictionary mit Replikationsstatus
    """
    try:
        replicator = get_database_replicator()
        return replicator.get_replication_status()
    except Exception as e:
        logger.error(f"Fehler beim Abrufen des Replikationsstatus: {e}")
        return {}


def execute_read_query_on_replica(query: str, params: tuple = ()) -> Any:
    """
    Führt eine Leseabfrage auf einer Read-Replika aus.
    
    Args:
        query: SQL-Abfrage
        params: Abfrageparameter
        
    Returns:
        Abfrageergebnis
    """
    try:
        router = get_read_replica_router()
        return router.execute_read_query(query, params)
    except Exception as e:
        logger.error(f"Fehler bei der Ausführung der Read-Replika-Abfrage: {e}")
        raise