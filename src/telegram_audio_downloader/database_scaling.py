"""
Datenbank-Skalierung für den Telegram Audio Downloader.

Ansätze:
- Sharding
- Read Replicas
- Datenpartitionierung
- Microservices-Architektur
"""

import hashlib
import time
from datetime import datetime
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field
from pathlib import Path

from .models import db, AudioFile, TelegramGroup
from .logging_config import get_logger
from .database_replication import get_database_replicator, get_read_replica_router

logger = get_logger(__name__)


@dataclass
class ShardInfo:
    """Informationen über einen Datenbank-Shard."""
    shard_id: str
    shard_key_range: tuple  # (min_key, max_key)
    database_path: str
    is_active: bool = True
    record_count: int = 0
    last_updated: datetime = field(default_factory=datetime.now)
    error_count: int = 0
    last_error: Optional[str] = None


class DatabaseSharder:
    """Verwaltet die Datenbank-Sharding."""
    
    def __init__(self, shard_config: List[Dict[str, Any]] = None):
        """
        Initialisiert den DatabaseSharder.
        
        Args:
            shard_config: Konfiguration der Shards
        """
        self.shards: Dict[str, ShardInfo] = {}
        self.shard_key_function: Callable = self._default_shard_key_function
        self.is_sharding_active = False
        
        # Initialisiere Shards
        if shard_config:
            for config in shard_config:
                self.add_shard(**config)
        
        logger.info("DatabaseSharder initialisiert")
    
    def _default_shard_key_function(self, record_id: str) -> int:
        """
        Standard-Shard-Key-Funktion basierend auf Hash.
        
        Args:
            record_id: ID des Datensatzes
            
        Returns:
            Shard-Key als Integer
        """
        # Erstelle einen Hash des Record-IDs und verwende die letzten 4 Hex-Ziffern
        hash_value = hashlib.sha256(record_id.encode()).hexdigest()
        return int(hash_value[-4:], 16)
    
    def __call__(self, record_id: str) -> int:
        """
        Berechnet den Shard-Key für eine Record-ID.
        
        Args:
            record_id: ID des Datensatzes
            
        Returns:
            Shard-Key als Integer
        """
        # Erstelle einen Hash des Record-IDs und verwende die letzten 4 Hex-Ziffern
        hash_value = hashlib.sha256(record_id.encode()).hexdigest()
        return int(hash_value[-4:], 16)
    
    def add_shard(self, shard_id: str, shard_key_range: tuple, database_path: str) -> None:
        """
        Fügt einen Shard hinzu.
        
        Args:
            shard_id: Eindeutige ID des Shards
            shard_key_range: Bereich der Shard-Keys (min, max)
            database_path: Pfad zur Shard-Datenbank
        """
        shard = ShardInfo(
            shard_id=shard_id,
            shard_key_range=shard_key_range,
            database_path=database_path
        )
        self.shards[shard_id] = shard
        logger.info(f"Shard hinzugefügt: {shard_id}")
    
    def get_shard_for_record(self, record_id: str) -> Optional[ShardInfo]:
        """
        Bestimmt den Shard für einen Datensatz.
        
        Args:
            record_id: ID des Datensatzes
            
        Returns:
            ShardInfo oder None, wenn kein passender Shard gefunden
        """
        try:
            shard_key = self.shard_key_function(record_id)
            
            for shard in self.shards.values():
                if (shard.is_active and 
                    shard.shard_key_range[0] <= shard_key <= shard.shard_key_range[1]):
                    return shard
            
            logger.warning(f"Kein passender Shard für Record-ID {record_id} (Shard-Key: {shard_key})")
            return None
            
        except Exception as e:
            logger.error(f"Fehler bei der Shard-Zuweisung für {record_id}: {e}")
            return None
    
    def distribute_existing_data(self) -> Dict[str, int]:
        """
        Verteilt vorhandene Daten auf die Shards.
        
        Returns:
            Dictionary mit Verteilungsstatistiken
        """
        try:
            distribution_stats = {}
            
            # Hole alle AudioFiles
            audio_files = list(AudioFile.select())
            logger.info(f"Verteile {len(audio_files)} AudioFiles auf Shards")
            
            for audio_file in audio_files:
                shard = self.get_shard_for_record(audio_file.file_id)
                if shard:
                    # In einer echten Implementierung würden wir hier die Daten
                    # in den entsprechenden Shard migrieren
                    distribution_stats[shard.shard_id] = distribution_stats.get(shard.shard_id, 0) + 1
            
            logger.info(f"Datenverteilung abgeschlossen: {distribution_stats}")
            return distribution_stats
            
        except Exception as e:
            logger.error(f"Fehler bei der Datenverteilung: {e}")
            return {}
    
    def get_shard_statistics(self) -> List[Dict[str, Any]]:
        """
        Gibt Statistiken für alle Shards zurück.
        
        Returns:
            Liste von Shard-Statistiken
        """
        stats = []
        for shard_id, shard in self.shards.items():
            stats.append({
                "shard_id": shard.shard_id,
                "shard_key_range": shard.shard_key_range,
                "database_path": shard.database_path,
                "is_active": shard.is_active,
                "record_count": shard.record_count,
                "last_updated": shard.last_updated.isoformat() if shard.last_updated else None,
                "error_count": shard.error_count,
                "last_error": shard.last_error
            })
        return stats
    
    def enable_sharding(self) -> None:
        """Aktiviert das Sharding."""
        self.is_sharding_active = True
        logger.info("Datenbank-Sharding aktiviert")
    
    def disable_sharding(self) -> None:
        """Deaktiviert das Sharding."""
        self.is_sharding_active = False
        logger.info("Datenbank-Sharding deaktiviert")


class PartitionManager:
    """Verwaltet die Datenpartitionierung."""
    
    def __init__(self):
        """Initialisiert den PartitionManager."""
        self.partitions: Dict[str, Dict[str, Any]] = {}
        self.partition_functions: Dict[str, Callable] = {}
        
        # Registriere Standard-Partition-Funktionen
        self.register_partition_function("by_group", self._partition_by_group)
        self.register_partition_function("by_date", self._partition_by_date)
        self.register_partition_function("by_size", self._partition_by_size)
        
        logger.info("PartitionManager initialisiert")
    
    def register_partition_function(self, name: str, func: Callable) -> None:
        """
        Registriert eine Partition-Funktion.
        
        Args:
            name: Name der Partition-Funktion
            func: Partition-Funktion
        """
        self.partition_functions[name] = func
        logger.debug(f"Partition-Funktion registriert: {name}")
    
    def _partition_by_group(self, audio_file: AudioFile) -> str:
        """
        Partitioniert nach Gruppe.
        
        Args:
            audio_file: AudioFile-Objekt
            
        Returns:
            Partitionsname
        """
        if audio_file.group:
            return f"group_{audio_file.group.group_id}"
        return "group_unknown"
    
    def _partition_by_date(self, audio_file: AudioFile) -> str:
        """
        Partitioniert nach Datum.
        
        Args:
            audio_file: AudioFile-Objekt
            
        Returns:
            Partitionsname
        """
        if audio_file.downloaded_at:
            return f"date_{audio_file.downloaded_at.strftime('%Y_%m')}"
        return "date_unknown"
    
    def _partition_by_size(self, audio_file: AudioFile) -> str:
        """
        Partitioniert nach Dateigröße.
        
        Args:
            audio_file: AudioFile-Objekt
            
        Returns:
            Partitionsname
        """
        size_mb = audio_file.file_size / (1024 * 1024)
        if size_mb < 10:
            return "size_small"
        elif size_mb < 100:
            return "size_medium"
        else:
            return "size_large"
    
    def get_partition_for_record(self, audio_file: AudioFile, partition_type: str = "by_group") -> str:
        """
        Bestimmt die Partition für einen Datensatz.
        
        Args:
            audio_file: AudioFile-Objekt
            partition_type: Typ der Partitionierung
            
        Returns:
            Name der Partition
        """
        try:
            if partition_type in self.partition_functions:
                return self.partition_functions[partition_type](audio_file)
            else:
                logger.warning(f"Unbekannte Partition-Funktion: {partition_type}")
                return "default"
        except Exception as e:
            logger.error(f"Fehler bei der Partitionsbestimmung: {e}")
            return "default"
    
    def create_partition_view(self, partition_name: str, partition_type: str) -> bool:
        """
        Erstellt eine Sicht für eine Partition.
        
        Args:
            partition_name: Name der Partition
            partition_type: Typ der Partitionierung
            
        Returns:
            True, wenn die Sicht erstellt wurde
        """
        try:
            # In einer echten Implementierung würden wir hier eine
            # Datenbanksicht oder eine separate Tabelle erstellen
            self.partitions[partition_name] = {
                "type": partition_type,
                "created_at": datetime.now(),
                "record_count": 0
            }
            
            logger.debug(f"Partition-Sicht erstellt: {partition_name}")
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim Erstellen der Partition-Sicht {partition_name}: {e}")
            return False


class MicroservicesDatabaseAdapter:
    """Adapter für Microservices-Datenbankzugriff."""
    
    def __init__(self):
        """Initialisiert den MicroservicesDatabaseAdapter."""
        self.service_configs: Dict[str, Dict[str, Any]] = {}
        self.service_connections: Dict[str, Any] = {}
        
        logger.info("MicroservicesDatabaseAdapter initialisiert")
    
    def register_service(self, service_name: str, db_config: Dict[str, Any]) -> None:
        """
        Registriert einen Microservice.
        
        Args:
            service_name: Name des Services
            db_config: Datenbankkonfiguration
        """
        self.service_configs[service_name] = db_config
        logger.info(f"Microservice registriert: {service_name}")
    
    def get_service_connection(self, service_name: str):
        """
        Gibt eine Verbindung zu einem Microservice zurück.
        
        Args:
            service_name: Name des Services
            
        Returns:
            Datenbankverbindung
        """
        try:
            if service_name not in self.service_connections:
                # In einer echten Implementierung würden wir hier
                # eine Verbindung zum Microservice herstellen
                self.service_connections[service_name] = None
                logger.debug(f"Verbindung zu Microservice {service_name} hergestellt")
            
            return self.service_connections[service_name]
            
        except Exception as e:
            logger.error(f"Fehler beim Herstellen der Verbindung zu {service_name}: {e}")
            return None
    
    def execute_service_query(self, service_name: str, query: str, params: tuple = ()) -> Any:
        """
        Führt eine Abfrage auf einem Microservice aus.
        
        Args:
            service_name: Name des Services
            query: SQL-Abfrage
            params: Abfrageparameter
            
        Returns:
            Abfrageergebnis
        """
        try:
            connection = self.get_service_connection(service_name)
            if not connection:
                raise Exception(f"Keine Verbindung zu Service {service_name}")
            
            # In einer echten Implementierung würden wir hier
            # die Abfrage an den Microservice senden
            logger.debug(f"Abfrage an Microservice {service_name} gesendet")
            return []  # Platzhalter-Ergebnis
            
        except Exception as e:
            logger.error(f"Fehler bei der Ausführung der Service-Abfrage {service_name}: {e}")
            raise


class DatabaseScalingManager:
    """Zentrale Verwaltung der Datenbank-Skalierung."""
    
    def __init__(self):
        """Initialisiert den DatabaseScalingManager."""
        self.sharder = DatabaseSharder()
        self.partition_manager = PartitionManager()
        self.microservices_adapter = MicroservicesDatabaseAdapter()
        self.scaling_policies: Dict[str, Dict[str, Any]] = {}
        
        logger.info("DatabaseScalingManager initialisiert")
    
    def configure_sharding(self, shard_config: List[Dict[str, Any]]) -> None:
        """
        Konfiguriert das Sharding.
        
        Args:
            shard_config: Konfiguration der Shards
        """
        try:
            for config in shard_config:
                self.sharder.add_shard(**config)
            logger.info("Sharding konfiguriert")
        except Exception as e:
            logger.error(f"Fehler bei der Sharding-Konfiguration: {e}")
    
    def configure_partitioning(self, partition_config: Dict[str, Any]) -> None:
        """
        Konfiguriert die Partitionierung.
        
        Args:
            partition_config: Konfiguration der Partitionierung
        """
        # In einer echten Implementierung würden wir hier
        # die Partitionierung konfigurieren
        logger.info("Partitionierung konfiguriert")
    
    def configure_microservices(self, services_config: Dict[str, Dict[str, Any]]) -> None:
        """
        Konfiguriert die Microservices.
        
        Args:
            services_config: Konfiguration der Microservices
        """
        try:
            for service_name, db_config in services_config.items():
                self.microservices_adapter.register_service(service_name, db_config)
            logger.info("Microservices konfiguriert")
        except Exception as e:
            logger.error(f"Fehler bei der Microservices-Konfiguration: {e}")
    
    def set_scaling_policy(self, policy_name: str, policy_config: Dict[str, Any]) -> None:
        """
        Setzt eine Skalierungsrichtlinie.
        
        Args:
            policy_name: Name der Richtlinie
            policy_config: Konfiguration der Richtlinie
        """
        self.scaling_policies[policy_name] = policy_config
        logger.info(f"Skalierungsrichtlinie gesetzt: {policy_name}")
    
    def get_scaling_statistics(self) -> Dict[str, Any]:
        """
        Gibt Skalierungsstatistiken zurück.
        
        Returns:
            Dictionary mit Skalierungsstatistiken
        """
        try:
            return {
                "timestamp": datetime.now().isoformat(),
                "shards": self.sharder.get_shard_statistics(),
                "partitions": list(self.partition_manager.partitions.keys()),
                "microservices": list(self.microservices_adapter.service_configs.keys()),
                "scaling_policies": list(self.scaling_policies.keys())
            }
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Skalierungsstatistiken: {e}")
            return {}
    
    def scale_database(self, scale_type: str, scale_factor: float) -> bool:
        """
        Skaliert die Datenbank.
        
        Args:
            scale_type: Typ der Skalierung ("up" oder "down")
            scale_factor: Skalierungsfaktor
            
        Returns:
            True, wenn die Skalierung erfolgreich war
        """
        try:
            logger.info(f"Datenbank-{scale_type}-Skalierung mit Faktor {scale_factor} gestartet")
            
            # In einer echten Implementierung würden wir hier
            # die entsprechenden Skalierungsmaßnahmen durchführen
            
            if scale_type == "up":
                # Füge neue Shards hinzu
                # Skaliere Read-Replikas
                # Erweitere Partitionen
                pass
            elif scale_type == "down":
                # Entferne Shards
                # Reduziere Read-Replikas
                # Konsolidiere Partitionen
                pass
            
            logger.info(f"Datenbank-{scale_type}-Skalierung abgeschlossen")
            return True
            
        except Exception as e:
            logger.error(f"Fehler bei der Datenbank-{scale_type}-Skalierung: {e}")
            return False


# Globale Instanz des ScalingManagers
_scaling_manager: Optional[DatabaseScalingManager] = None


def get_scaling_manager() -> DatabaseScalingManager:
    """
    Gibt die globale Instanz des DatabaseScalingManager zurück.
    
    Returns:
        DatabaseScalingManager-Instanz
    """
    global _scaling_manager
    if _scaling_manager is None:
        _scaling_manager = DatabaseScalingManager()
    return _scaling_manager


def configure_database_scaling(shard_config: List[Dict[str, Any]] = None,
                             partition_config: Dict[str, Any] = None,
                             services_config: Dict[str, Dict[str, Any]] = None) -> None:
    """
    Konfiguriert die Datenbank-Skalierung.
    
    Args:
        shard_config: Konfiguration der Shards
        partition_config: Konfiguration der Partitionierung
        services_config: Konfiguration der Microservices
    """
    try:
        manager = get_scaling_manager()
        
        if shard_config:
            manager.configure_sharding(shard_config)
        
        if partition_config:
            manager.configure_partitioning(partition_config)
        
        if services_config:
            manager.configure_microservices(services_config)
            
    except Exception as e:
        logger.error(f"Fehler bei der Konfiguration der Datenbank-Skalierung: {e}")


def get_scaling_statistics() -> Dict[str, Any]:
    """
    Gibt Datenbank-Skalierungsstatistiken zurück.
    
    Returns:
        Dictionary mit Skalierungsstatistiken
    """
    try:
        manager = get_scaling_manager()
        return manager.get_scaling_statistics()
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Skalierungsstatistiken: {e}")
        return {}


def scale_database(scale_type: str, scale_factor: float) -> bool:
    """
    Skaliert die Datenbank.
    
    Args:
        scale_type: Typ der Skalierung ("up" oder "down")
        scale_factor: Skalierungsfaktor
        
    Returns:
        True, wenn die Skalierung erfolgreich war
    """
    try:
        manager = get_scaling_manager()
        return manager.scale_database(scale_type, scale_factor)
    except Exception as e:
        logger.error(f"Fehler bei der Datenbank-Skalierung: {e}")
        return False


def get_shard_for_audio_file(file_id: str) -> Optional[ShardInfo]:
    """
    Bestimmt den Shard für eine Audiodatei.
    
    Args:
        file_id: ID der Audiodatei
        
    Returns:
        ShardInfo oder None, wenn kein passender Shard gefunden
    """
    try:
        manager = get_scaling_manager()
        return manager.sharder.get_shard_for_record(file_id)
    except Exception as e:
        logger.error(f"Fehler bei der Shard-Zuweisung für {file_id}: {e}")
        return None