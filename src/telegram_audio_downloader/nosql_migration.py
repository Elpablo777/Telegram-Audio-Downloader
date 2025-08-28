"""
Datenbank-Migration zu NoSQL für den Telegram Audio Downloader.

Hybrid-Ansatz für:
- Dokumentenorientiert (MongoDB)
- Zeitreihendatenbank (InfluxDB)
- Graph-Datenbank (Neo4j)
- Schlüssel-Wert-Speicher (Redis)
"""

import json
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
import sqlite3

# Bedingter Import für NoSQL-Datenbanken
try:
    from pymongo import MongoClient
    from influxdb_client import InfluxDBClient, Point
    from redis import Redis
    # Neo4j-Import wird bei Bedarf erfolgen
    HAS_NOSQL_DRIVERS = True
except ImportError:
    HAS_NOSQL_DRIVERS = False
    MongoClient = None
    InfluxDBClient = None
    Point = None
    Redis = None

from .models import AudioFile, TelegramGroup, db
from .logging_config import get_logger

logger = get_logger(__name__)


class NoSQLMigrationManager:
    """Verwaltet die Migration zu NoSQL-Datenbanken."""
    
    def __init__(self, sqlite_db_path: str = None):
        """
        Initialisiert den NoSQL-MigrationManager.
        
        Args:
            sqlite_db_path: Pfad zur SQLite-Datenbank
        """
        self.sqlite_db_path = sqlite_db_path or db.database
        self.nosql_configs = {}
        self.migration_status = {}
        
        logger.info("NoSQLMigrationManager initialisiert")
    
    def configure_mongodb(self, connection_string: str, database_name: str) -> None:
        """
        Konfiguriert die MongoDB-Verbindung.
        
        Args:
            connection_string: MongoDB-Verbindungsstring
            database_name: Name der MongoDB-Datenbank
        """
        self.nosql_configs["mongodb"] = {
            "connection_string": connection_string,
            "database_name": database_name
        }
        logger.debug("MongoDB-Konfiguration hinzugefügt")
    
    def configure_influxdb(self, url: str, token: str, org: str, bucket: str) -> None:
        """
        Konfiguriert die InfluxDB-Verbindung.
        
        Args:
            url: InfluxDB-URL
            token: Authentifizierungs-Token
            org: Organisation
            bucket: Bucket-Name
        """
        self.nosql_configs["influxdb"] = {
            "url": url,
            "token": token,
            "org": org,
            "bucket": bucket
        }
        logger.debug("InfluxDB-Konfiguration hinzugefügt")
    
    def configure_redis(self, host: str, port: int, db: int = 0) -> None:
        """
        Konfiguriert die Redis-Verbindung.
        
        Args:
            host: Redis-Host
            port: Redis-Port
            db: Redis-Datenbanknummer
        """
        self.nosql_configs["redis"] = {
            "host": host,
            "port": port,
            "db": db
        }
        logger.debug("Redis-Konfiguration hinzugefügt")
    
    def configure_neo4j(self, uri: str, username: str, password: str) -> None:
        """
        Konfiguriert die Neo4j-Verbindung.
        
        Args:
            uri: Neo4j-URI
            username: Benutzername
            password: Passwort
        """
        self.nosql_configs["neo4j"] = {
            "uri": uri,
            "username": username,
            "password": password
        }
        logger.debug("Neo4j-Konfiguration hinzugefügt")
    
    def migrate_to_mongodb(self) -> bool:
        """
        Migriert Daten zu MongoDB.
        
        Returns:
            True, wenn die Migration erfolgreich war
        """
        if not HAS_NOSQL_DRIVERS or "mongodb" not in self.nosql_configs:
            logger.warning("MongoDB-Migration nicht möglich: Treiber nicht verfügbar oder nicht konfiguriert")
            return False
        
        try:
            config = self.nosql_configs["mongodb"]
            client = MongoClient(config["connection_string"])
            mongodb = client[config["database_name"]]
            
            # Migriere AudioFile-Daten
            audio_collection = mongodb["audio_files"]
            audio_files = self._get_all_audio_files()
            
            if audio_files:
                result = audio_collection.insert_many(audio_files)
                logger.info(f"{len(result.inserted_ids)} AudioFile-Datensätze zu MongoDB migriert")
            
            # Migriere TelegramGroup-Daten
            group_collection = mongodb["telegram_groups"]
            telegram_groups = self._get_all_telegram_groups()
            
            if telegram_groups:
                result = group_collection.insert_many(telegram_groups)
                logger.info(f"{len(result.inserted_ids)} TelegramGroup-Datensätze zu MongoDB migriert")
            
            client.close()
            self.migration_status["mongodb"] = "completed"
            return True
            
        except Exception as e:
            logger.error(f"Fehler bei der MongoDB-Migration: {e}")
            self.migration_status["mongodb"] = f"failed: {str(e)}"
            return False
    
    def migrate_to_influxdb(self) -> bool:
        """
        Migriert Zeitreihendaten zu InfluxDB.
        
        Returns:
            True, wenn die Migration erfolgreich war
        """
        if not HAS_NOSQL_DRIVERS or "influxdb" not in self.nosql_configs:
            logger.warning("InfluxDB-Migration nicht möglich: Treiber nicht verfügbar oder nicht konfiguriert")
            return False
        
        try:
            config = self.nosql_configs["influxdb"]
            client = InfluxDBClient(url=config["url"], token=config["token"], org=config["org"])
            write_api = client.write_api()
            
            # Migriere Download-Statistiken als Zeitreihendaten
            download_stats = self._get_download_statistics()
            
            points = []
            for stat in download_stats:
                point = Point("downloads") \
                    .tag("status", stat["status"]) \
                    .field("count", stat["count"]) \
                    .field("total_size", stat["total_size"]) \
                    .time(stat["timestamp"])
                points.append(point)
            
            if points:
                write_api.write(bucket=config["bucket"], org=config["org"], record=points)
                logger.info(f"{len(points)} Download-Statistikpunkte zu InfluxDB migriert")
            
            client.close()
            self.migration_status["influxdb"] = "completed"
            return True
            
        except Exception as e:
            logger.error(f"Fehler bei der InfluxDB-Migration: {e}")
            self.migration_status["influxdb"] = f"failed: {str(e)}"
            return False
    
    def migrate_to_redis(self) -> bool:
        """
        Migriert Cache-Daten zu Redis.
        
        Returns:
            True, wenn die Migration erfolgreich war
        """
        if not HAS_NOSQL_DRIVERS or "redis" not in self.nosql_configs:
            logger.warning("Redis-Migration nicht möglich: Treiber nicht verfügbar oder nicht konfiguriert")
            return False
        
        try:
            config = self.nosql_configs["redis"]
            redis_client = Redis(host=config["host"], port=config["port"], db=config["db"])
            
            # Migriere häufig abgerufene AudioFile-Daten
            audio_files = self._get_frequently_accessed_audio_files()
            
            for audio_file in audio_files:
                key = f"audio_file:{audio_file['file_id']}"
                redis_client.set(key, json.dumps(audio_file))
            
            logger.info(f"{len(audio_files)} AudioFile-Datensätze zu Redis migriert")
            
            # Migriere Gruppenstatistiken
            group_stats = self._get_group_statistics()
            for group_id, stats in group_stats.items():
                key = f"group_stats:{group_id}"
                redis_client.set(key, json.dumps(stats))
            
            logger.info(f"{len(group_stats)} Gruppenstatistik-Einträge zu Redis migriert")
            
            redis_client.close()
            self.migration_status["redis"] = "completed"
            return True
            
        except Exception as e:
            logger.error(f"Fehler bei der Redis-Migration: {e}")
            self.migration_status["redis"] = f"failed: {str(e)}"
            return False
    
    def migrate_to_neo4j(self) -> bool:
        """
        Migriert Beziehungsdaten zu Neo4j.
        
        Returns:
            True, wenn die Migration erfolgreich war
        """
        if not HAS_NOSQL_DRIVERS or "neo4j" not in self.nosql_configs:
            logger.warning("Neo4j-Migration nicht möglich: Treiber nicht verfügbar oder nicht konfiguriert")
            return False
        
        try:
            # Bedingter Import für Neo4j
            try:
                from neo4j import GraphDatabase
            except ImportError:
                logger.warning("Neo4j-Treiber nicht installiert")
                return False
            
            config = self.nosql_configs["neo4j"]
            driver = GraphDatabase.driver(config["uri"], auth=(config["username"], config["password"]))
            
            # Migriere Gruppen- und Datei-Beziehungen
            with driver.session() as session:
                # Erstelle Gruppenknoten
                telegram_groups = self._get_all_telegram_groups()
                for group in telegram_groups:
                    session.run(
                        "MERGE (g:TelegramGroup {id: $id}) "
                        "SET g.group_id = $group_id, g.title = $title",
                        id=group["id"],
                        group_id=group["group_id"],
                        title=group["title"]
                    )
                
                # Erstelle Dateiknoten und Beziehungen
                audio_files = self._get_all_audio_files()
                for audio in audio_files:
                    session.run(
                        "MERGE (a:AudioFile {file_id: $file_id}) "
                        "SET a.file_name = $file_name, a.title = $title "
                        "WITH a "
                        "MATCH (g:TelegramGroup {id: $group_id}) "
                        "MERGE (a)-[:BELONGS_TO]->(g)",
                        file_id=audio["file_id"],
                        file_name=audio["file_name"],
                        title=audio["title"],
                        group_id=audio["group_id"]
                    )
            
            logger.info("Daten zu Neo4j migriert")
            driver.close()
            self.migration_status["neo4j"] = "completed"
            return True
            
        except Exception as e:
            logger.error(f"Fehler bei der Neo4j-Migration: {e}")
            self.migration_status["neo4j"] = f"failed: {str(e)}"
            return False
    
    def run_full_migration(self) -> Dict[str, Any]:
        """
        Führt eine vollständige Migration zu allen konfigurierten NoSQL-Datenbanken durch.
        
        Returns:
            Dictionary mit Migrationsstatus
        """
        logger.info("Starte vollständige NoSQL-Migration")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "migrations": {}
        }
        
        # Führe Migrationen in einer bestimmten Reihenfolge durch
        migration_methods = [
            ("mongodb", self.migrate_to_mongodb),
            ("influxdb", self.migrate_to_influxdb),
            ("redis", self.migrate_to_redis),
            ("neo4j", self.migrate_to_neo4j)
        ]
        
        for db_name, migration_method in migration_methods:
            if db_name in self.nosql_configs:
                logger.info(f"Starte Migration zu {db_name}")
                try:
                    success = migration_method()
                    results["migrations"][db_name] = {
                        "status": "completed" if success else "failed",
                        "timestamp": datetime.now().isoformat()
                    }
                except Exception as e:
                    logger.error(f"Fehler bei der Migration zu {db_name}: {e}")
                    results["migrations"][db_name] = {
                        "status": "error",
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    }
            else:
                results["migrations"][db_name] = {
                    "status": "skipped",
                    "reason": "not configured"
                }
        
        return results
    
    def get_migration_status(self) -> Dict[str, Any]:
        """
        Gibt den aktuellen Migrationsstatus zurück.
        
        Returns:
            Dictionary mit Migrationsstatus
        """
        return {
            "timestamp": datetime.now().isoformat(),
            "configured_databases": list(self.nosql_configs.keys()),
            "migration_status": self.migration_status
        }
    
    def _get_all_audio_files(self) -> List[Dict[str, Any]]:
        """
        Holt alle AudioFile-Datensätze aus der SQLite-Datenbank.
        
        Returns:
            Liste von AudioFile-Datensätzen
        """
        try:
            conn = sqlite3.connect(self.sqlite_db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM audio_files")
            rows = cursor.fetchall()
            
            # Konvertiere zu Dictionaries
            audio_files = [dict(row) for row in rows]
            
            conn.close()
            return audio_files
            
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der AudioFile-Daten: {e}")
            return []
    
    def _get_all_telegram_groups(self) -> List[Dict[str, Any]]:
        """
        Holt alle TelegramGroup-Datensätze aus der SQLite-Datenbank.
        
        Returns:
            Liste von TelegramGroup-Datensätzen
        """
        try:
            conn = sqlite3.connect(self.sqlite_db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM telegram_groups")
            rows = cursor.fetchall()
            
            # Konvertiere zu Dictionaries
            telegram_groups = [dict(row) for row in rows]
            
            conn.close()
            return telegram_groups
            
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der TelegramGroup-Daten: {e}")
            return []
    
    def _get_download_statistics(self) -> List[Dict[str, Any]]:
        """
        Holt Download-Statistiken für die InfluxDB-Migration.
        
        Returns:
            Liste von Statistikdaten
        """
        try:
            conn = sqlite3.connect(self.sqlite_db_path)
            cursor = conn.cursor()
            
            # Hole aggregierte Download-Statistiken
            cursor.execute("""
                SELECT 
                    status,
                    COUNT(*) as count,
                    SUM(file_size) as total_size,
                    datetime('now') as timestamp
                FROM audio_files 
                GROUP BY status
            """)
            
            rows = cursor.fetchall()
            stats = [
                {
                    "status": row[0],
                    "count": row[1],
                    "total_size": row[2] or 0,
                    "timestamp": row[3]
                }
                for row in rows
            ]
            
            conn.close()
            return stats
            
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Download-Statistiken: {e}")
            return []
    
    def _get_frequently_accessed_audio_files(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Holt häufig abgerufene AudioFile-Daten für Redis.
        
        Args:
            limit: Maximale Anzahl von Datensätzen
            
        Returns:
            Liste von AudioFile-Datensätzen
        """
        try:
            # In einer echten Implementierung würden wir hier
            # Zugriffsstatistiken aus der Datenbank abrufen
            # Für dieses Beispiel verwenden wir einfach die neuesten Dateien
            
            conn = sqlite3.connect(self.sqlite_db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM audio_files 
                WHERE downloaded_at IS NOT NULL
                ORDER BY downloaded_at DESC
                LIMIT ?
            """, (limit,))
            
            rows = cursor.fetchall()
            audio_files = [dict(row) for row in rows]
            
            conn.close()
            return audio_files
            
        except Exception as e:
            logger.error(f"Fehler beim Abrufen häufig abgerufener AudioFile-Daten: {e}")
            return []
    
    def _get_group_statistics(self) -> Dict[str, Dict[str, Any]]:
        """
        Holt Gruppenstatistiken für Redis.
        
        Returns:
            Dictionary mit Gruppenstatistiken
        """
        try:
            conn = sqlite3.connect(self.sqlite_db_path)
            cursor = conn.cursor()
            
            # Hole Gruppenstatistiken
            cursor.execute("""
                SELECT 
                    g.group_id,
                    COUNT(a.id) as file_count,
                    SUM(a.file_size) as total_size,
                    MAX(a.downloaded_at) as last_download
                FROM telegram_groups g
                LEFT JOIN audio_files a ON g.id = a.group_id
                GROUP BY g.id, g.group_id
            """)
            
            rows = cursor.fetchall()
            stats = {
                str(row[0]): {
                    "file_count": row[1],
                    "total_size": row[2] or 0,
                    "last_download": row[3]
                }
                for row in rows
            }
            
            conn.close()
            return stats
            
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Gruppenstatistiken: {e}")
            return {}


# Globale Instanz des MigrationManagers
_migration_manager: Optional[NoSQLMigrationManager] = None


def get_nosql_migration_manager() -> NoSQLMigrationManager:
    """
    Gibt die globale Instanz des NoSQLMigrationManager zurück.
    
    Returns:
        NoSQLMigrationManager-Instanz
    """
    global _migration_manager
    if _migration_manager is None:
        _migration_manager = NoSQLMigrationManager()
    return _migration_manager


def configure_mongodb_migration(connection_string: str, database_name: str) -> None:
    """
    Konfiguriert die MongoDB-Migration.
    
    Args:
        connection_string: MongoDB-Verbindungsstring
        database_name: Name der MongoDB-Datenbank
    """
    try:
        manager = get_nosql_migration_manager()
        manager.configure_mongodb(connection_string, database_name)
    except Exception as e:
        logger.error(f"Fehler bei der MongoDB-Konfiguration: {e}")


def configure_influxdb_migration(url: str, token: str, org: str, bucket: str) -> None:
    """
    Konfiguriert die InfluxDB-Migration.
    
    Args:
        url: InfluxDB-URL
        token: Authentifizierungs-Token
        org: Organisation
        bucket: Bucket-Name
    """
    try:
        manager = get_nosql_migration_manager()
        manager.configure_influxdb(url, token, org, bucket)
    except Exception as e:
        logger.error(f"Fehler bei der InfluxDB-Konfiguration: {e}")


def configure_redis_migration(host: str, port: int, db: int = 0) -> None:
    """
    Konfiguriert die Redis-Migration.
    
    Args:
        host: Redis-Host
        port: Redis-Port
        db: Redis-Datenbanknummer
    """
    try:
        manager = get_nosql_migration_manager()
        manager.configure_redis(host, port, db)
    except Exception as e:
        logger.error(f"Fehler bei der Redis-Konfiguration: {e}")


def configure_neo4j_migration(uri: str, username: str, password: str) -> None:
    """
    Konfiguriert die Neo4j-Migration.
    
    Args:
        uri: Neo4j-URI
        username: Benutzername
        password: Passwort
    """
    try:
        manager = get_nosql_migration_manager()
        manager.configure_neo4j(uri, username, password)
    except Exception as e:
        logger.error(f"Fehler bei der Neo4j-Konfiguration: {e}")


def run_nosql_migration() -> Dict[str, Any]:
    """
    Führt eine vollständige NoSQL-Migration durch.
    
    Returns:
        Dictionary mit Migrationsstatus
    """
    try:
        manager = get_nosql_migration_manager()
        return manager.run_full_migration()
    except Exception as e:
        logger.error(f"Fehler bei der NoSQL-Migration: {e}")
        return {
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }


def get_nosql_migration_status() -> Dict[str, Any]:
    """
    Gibt den aktuellen NoSQL-Migrationsstatus zurück.
    
    Returns:
        Dictionary mit Migrationsstatus
    """
    try:
        manager = get_nosql_migration_manager()
        return manager.get_migration_status()
    except Exception as e:
        logger.error(f"Fehler beim Abrufen des Migrationsstatus: {e}")
        return {
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }