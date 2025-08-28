"""
Datenbank-Migrations-Framework für den Telegram Audio Downloader.

Features:
- Versionskontrolle für Schema-Änderungen
- Auf- und Abwärtsmigrationen
- Automatische Anpassung von Testdaten
- Migrations-Validierung
"""

import os
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Callable
from pathlib import Path
from dataclasses import dataclass, field

from peewee import OperationalError
from playhouse.migrate import SqliteMigrator, migrate

from .models import db, AudioFile, TelegramGroup
from .logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class Migration:
    """Repräsentiert eine Datenbankmigration."""
    version: int
    name: str
    description: str
    up_script: str
    down_script: str
    created_at: datetime = field(default_factory=datetime.now)
    
    def get_hash(self) -> str:
        """Berechnet den Hash der Migration."""
        content = f"{self.version}{self.name}{self.description}{self.up_script}{self.down_script}"
        return hashlib.sha256(content.encode()).hexdigest()


class MigrationManager:
    """Verwaltet Datenbankmigrationen."""
    
    def __init__(self, migrations_dir: Path = None):
        """
        Initialisiert den MigrationManager.
        
        Args:
            migrations_dir: Verzeichnis für Migrationsdateien
        """
        self.migrations_dir = migrations_dir or Path("data/migrations")
        self.migrations_dir.mkdir(parents=True, exist_ok=True)
        self.migrator = SqliteMigrator(db)
        self.applied_migrations: List[Dict] = []
        self.available_migrations: List[Migration] = []
        
        # Erstelle die Migrations-Tabelle, falls sie nicht existiert
        self._create_migrations_table()
        
        # Lade angewandte und verfügbare Migrationen
        self._load_applied_migrations()
        self._load_available_migrations()
        
        logger.info("MigrationManager initialisiert")
    
    def _create_migrations_table(self) -> None:
        """Erstellt die Tabelle für Migrations-Tracking."""
        try:
            db.execute_sql("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    version INTEGER UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    hash TEXT NOT NULL,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    up_script TEXT,
                    down_script TEXT
                );
            """)
            logger.debug("Migrations-Tabelle erstellt")
        except Exception as e:
            logger.error(f"Fehler beim Erstellen der Migrations-Tabelle: {e}")
    
    def _load_applied_migrations(self) -> None:
        """Lädt die bereits angewandten Migrationen."""
        try:
            cursor = db.execute_sql("""
                SELECT version, name, description, hash, applied_at, up_script, down_script
                FROM schema_migrations
                ORDER BY version;
            """)
            
            for row in cursor.fetchall():
                self.applied_migrations.append({
                    "version": row[0],
                    "name": row[1],
                    "description": row[2],
                    "hash": row[3],
                    "applied_at": row[4],
                    "up_script": row[5],
                    "down_script": row[6]
                })
            
            logger.debug(f"{len(self.applied_migrations)} angewandte Migrationen geladen")
        except Exception as e:
            logger.error(f"Fehler beim Laden der angewandten Migrationen: {e}")
    
    def _load_available_migrations(self) -> None:
        """Lädt die verfügbaren Migrationen aus dem Dateisystem."""
        try:
            # Lade Migrationen aus JSON-Dateien
            for migration_file in self.migrations_dir.glob("*.json"):
                try:
                    with open(migration_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    migration = Migration(
                        version=data["version"],
                        name=data["name"],
                        description=data["description"],
                        up_script=data["up_script"],
                        down_script=data["down_script"]
                    )
                    
                    self.available_migrations.append(migration)
                except Exception as e:
                    logger.error(f"Fehler beim Laden der Migration {migration_file}: {e}")
            
            # Sortiere nach Versionsnummer
            self.available_migrations.sort(key=lambda m: m.version)
            logger.debug(f"{len(self.available_migrations)} verfügbare Migrationen geladen")
        except Exception as e:
            logger.error(f"Fehler beim Laden der verfügbaren Migrationen: {e}")
    
    def create_migration(self, name: str, description: str, 
                        up_script: str, down_script: str) -> Optional[Migration]:
        """
        Erstellt eine neue Migration.
        
        Args:
            name: Name der Migration
            description: Beschreibung der Migration
            up_script: SQL-Skript für die Aufwärtsmigration
            down_script: SQL-Skript für die Abwärtsmigration
            
        Returns:
            Die erstellte Migration oder None bei Fehler
        """
        try:
            # Bestimme die nächste Versionsnummer
            next_version = 1
            if self.available_migrations:
                next_version = max(m.version for m in self.available_migrations) + 1
            
            # Erstelle die Migration
            migration = Migration(
                version=next_version,
                name=name,
                description=description,
                up_script=up_script,
                down_script=down_script
            )
            
            # Speichere die Migration in einer Datei
            migration_file = self.migrations_dir / f"{next_version:04d}_{name}.json"
            migration_data = {
                "version": migration.version,
                "name": migration.name,
                "description": migration.description,
                "up_script": migration.up_script,
                "down_script": migration.down_script,
                "created_at": migration.created_at.isoformat()
            }
            
            with open(migration_file, 'w', encoding='utf-8') as f:
                json.dump(migration_data, f, indent=2, ensure_ascii=False)
            
            # Füge zur Liste der verfügbaren Migrationen hinzu
            self.available_migrations.append(migration)
            self.available_migrations.sort(key=lambda m: m.version)
            
            logger.info(f"Migration {migration_file} erstellt")
            return migration
            
        except Exception as e:
            logger.error(f"Fehler beim Erstellen der Migration: {e}")
            return None
    
    def migrate(self, target_version: Optional[int] = None) -> bool:
        """
        Führt Migrationen bis zur Zielversion aus.
        
        Args:
            target_version: Zielversionsnummer (None für neueste Version)
            
        Returns:
            True, wenn die Migration erfolgreich war
        """
        try:
            # Bestimme die Zielversion
            if target_version is None:
                if self.available_migrations:
                    target_version = max(m.version for m in self.available_migrations)
                else:
                    target_version = 0
            
            # Bestimme die aktuelle Version
            current_version = 0
            if self.applied_migrations:
                current_version = max(m["version"] for m in self.applied_migrations)
            
            logger.info(f"Migration von Version {current_version} zu {target_version}")
            
            # Führe Migrationen aus
            if target_version > current_version:
                # Aufwärtsmigrationen
                return self._migrate_up(current_version, target_version)
            elif target_version < current_version:
                # Abwärtsmigrationen
                return self._migrate_down(current_version, target_version)
            else:
                logger.info("Keine Migrationen erforderlich")
                return True
                
        except Exception as e:
            logger.error(f"Fehler bei der Migration: {e}")
            return False
    
    def _migrate_up(self, current_version: int, target_version: int) -> bool:
        """
        Führt Aufwärtsmigrationen aus.
        
        Args:
            current_version: Aktuelle Versionsnummer
            target_version: Zielversionsnummer
            
        Returns:
            True, wenn die Migration erfolgreich war
        """
        try:
            # Finde die auszuführenden Migrationen
            migrations_to_apply = [
                m for m in self.available_migrations
                if current_version < m.version <= target_version
            ]
            
            # Führe die Migrationen aus
            for migration in migrations_to_apply:
                logger.info(f"Führe Migration {migration.version}: {migration.name} aus")
                
                # Führe das Up-Skript aus
                try:
                    db.execute_sql(migration.up_script)
                except Exception as e:
                    logger.error(f"Fehler beim Ausführen des Up-Skripts für Migration {migration.version}: {e}")
                    return False
                
                # Erfasse die Migration in der Datenbank
                try:
                    db.execute_sql("""
                        INSERT INTO schema_migrations 
                        (version, name, description, hash, up_script, down_script)
                        VALUES (?, ?, ?, ?, ?, ?);
                    """, (
                        migration.version,
                        migration.name,
                        migration.description,
                        migration.get_hash(),
                        migration.up_script,
                        migration.down_script
                    ))
                except Exception as e:
                    logger.error(f"Fehler beim Erfassen der Migration {migration.version}: {e}")
                    return False
                
                logger.info(f"Migration {migration.version} erfolgreich angewandt")
            
            # Aktualisiere die Liste der angewandten Migrationen
            self._load_applied_migrations()
            return True
            
        except Exception as e:
            logger.error(f"Fehler bei der Aufwärtsmigration: {e}")
            return False
    
    def _migrate_down(self, current_version: int, target_version: int) -> bool:
        """
        Führt Abwärtsmigrationen aus.
        
        Args:
            current_version: Aktuelle Versionsnummer
            target_version: Zielversionsnummer
            
        Returns:
            True, wenn die Migration erfolgreich war
        """
        try:
            # Finde die zurückzusetzenden Migrationen
            migrations_to_rollback = [
                m for m in reversed(self.applied_migrations)
                if target_version < m["version"] <= current_version
            ]
            
            # Führe die Abwärtsmigrationen aus
            for migration_info in migrations_to_rollback:
                logger.info(f"Setze Migration {migration_info['version']}: {migration_info['name']} zurück")
                
                # Führe das Down-Skript aus
                try:
                    if migration_info["down_script"]:
                        db.execute_sql(migration_info["down_script"])
                except Exception as e:
                    logger.error(f"Fehler beim Ausführen des Down-Skripts für Migration {migration_info['version']}: {e}")
                    return False
                
                # Entferne die Migration aus der Datenbank
                try:
                    db.execute_sql("""
                        DELETE FROM schema_migrations WHERE version = ?;
                    """, (migration_info["version"],))
                except Exception as e:
                    logger.error(f"Fehler beim Entfernen der Migration {migration_info['version']}: {e}")
                    return False
                
                logger.info(f"Migration {migration_info['version']} erfolgreich zurückgesetzt")
            
            # Aktualisiere die Liste der angewandten Migrationen
            self._load_applied_migrations()
            return True
            
        except Exception as e:
            logger.error(f"Fehler bei der Abwärtsmigration: {e}")
            return False
    
    def get_migration_status(self) -> Dict[str, any]:
        """
        Gibt den Status der Migrationen zurück.
        
        Returns:
            Dictionary mit Migrationsstatus
        """
        current_version = 0
        if self.applied_migrations:
            current_version = max(m["version"] for m in self.applied_migrations)
        
        latest_version = 0
        if self.available_migrations:
            latest_version = max(m.version for m in self.available_migrations)
        
        return {
            "current_version": current_version,
            "latest_version": latest_version,
            "is_up_to_date": current_version == latest_version,
            "applied_migrations": self.applied_migrations,
            "available_migrations": [
                {
                    "version": m.version,
                    "name": m.name,
                    "description": m.description,
                    "applied": any(am["version"] == m.version for am in self.applied_migrations)
                }
                for m in self.available_migrations
            ]
        }
    
    def validate_migrations(self) -> bool:
        """
        Validiert die Migrationen.
        
        Returns:
            True, wenn alle Migrationen gültig sind
        """
        try:
            # Prüfe auf Inkonsistenzen
            for migration_info in self.applied_migrations:
                # Prüfe, ob die Migration noch verfügbar ist
                available_migration = next(
                    (m for m in self.available_migrations if m.version == migration_info["version"]),
                    None
                )
                
                if not available_migration:
                    logger.warning(f"Angewandte Migration {migration_info['version']} ist nicht mehr verfügbar")
                    continue
                
                # Prüfe den Hash
                if migration_info["hash"] != available_migration.get_hash():
                    logger.error(f"Hash-Inkonsistenz bei Migration {migration_info['version']}")
                    return False
            
            logger.info("Migrationen validiert")
            return True
            
        except Exception as e:
            logger.error(f"Fehler bei der Validierung der Migrationen: {e}")
            return False


# Globale Instanz des MigrationManagers
_migration_manager: Optional[MigrationManager] = None


def get_migration_manager() -> MigrationManager:
    """
    Gibt die globale Instanz des MigrationManagers zurück.
    
    Returns:
        MigrationManager-Instanz
    """
    global _migration_manager
    if _migration_manager is None:
        _migration_manager = MigrationManager()
    return _migration_manager


def run_migrations(target_version: Optional[int] = None) -> bool:
    """
    Führt Datenbankmigrationen aus.
    
    Args:
        target_version: Zielversionsnummer (None für neueste Version)
        
    Returns:
        True, wenn die Migration erfolgreich war
    """
    try:
        manager = get_migration_manager()
        return manager.migrate(target_version)
    except Exception as e:
        logger.error(f"Fehler beim Ausführen der Migrationen: {e}")
        return False


def get_migration_status() -> Dict[str, any]:
    """
    Gibt den Status der Migrationen zurück.
    
    Returns:
        Dictionary mit Migrationsstatus
    """
    try:
        manager = get_migration_manager()
        return manager.get_migration_status()
    except Exception as e:
        logger.error(f"Fehler beim Abrufen des Migrationsstatus: {e}")
        return {}


def validate_migrations() -> bool:
    """
    Validiert die Migrationen.
    
    Returns:
        True, wenn alle Migrationen gültig sind
    """
    try:
        manager = get_migration_manager()
        return manager.validate_migrations()
    except Exception as e:
        logger.error(f"Fehler bei der Validierung der Migrationen: {e}")
        return False