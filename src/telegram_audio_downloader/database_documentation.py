"""
Datenbank-Dokumentation für den Telegram Audio Downloader.

Automatische Dokumentation für:
- Schema-Dokumentation
- Beziehungsdiagramme
- Datenflussdiagramme
- API-Dokumentation
"""

import json
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime

from .models import AudioFile, TelegramGroup, db
from .logging_config import get_logger

logger = get_logger(__name__)


class DatabaseDocumentation:
    """Verwaltet die automatische Datenbank-Dokumentation."""
    
    def __init__(self, docs_dir: Path = None):
        """
        Initialisiert die Datenbank-Dokumentation.
        
        Args:
            docs_dir: Verzeichnis für die Dokumentation
        """
        self.docs_dir = docs_dir or Path("docs/database")
        self.docs_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"DatabaseDocumentation initialisiert mit Dokumentationsverzeichnis {self.docs_dir}")
    
    def generate_schema_documentation(self) -> Dict[str, Any]:
        """
        Generiert die Schema-Dokumentation.
        
        Returns:
            Dictionary mit Schema-Informationen
        """
        logger.info("Generiere Schema-Dokumentation")
        
        schema_info = {
            "generated_at": datetime.now().isoformat(),
            "tables": {}
        }
        
        try:
            # Informationen über AudioFile-Tabelle
            schema_info["tables"]["audio_files"] = {
                "name": "audio_files",
                "description": "Speichert Informationen zu heruntergeladenen Audiodateien",
                "columns": [
                    {
                        "name": "id",
                        "type": "INTEGER",
                        "primary_key": True,
                        "nullable": False,
                        "description": "Eindeutige ID des Datensatzes"
                    },
                    {
                        "name": "file_id",
                        "type": "VARCHAR(255)",
                        "unique": True,
                        "nullable": False,
                        "description": "Eindeutige Telegram-Datei-ID"
                    },
                    {
                        "name": "file_name",
                        "type": "VARCHAR(255)",
                        "nullable": False,
                        "description": "Name der Datei"
                    },
                    {
                        "name": "file_size",
                        "type": "INTEGER",
                        "nullable": True,
                        "description": "Größe der Datei in Bytes"
                    },
                    {
                        "name": "duration",
                        "type": "INTEGER",
                        "nullable": True,
                        "description": "Dauer der Audiodatei in Sekunden"
                    },
                    {
                        "name": "title",
                        "type": "VARCHAR(255)",
                        "nullable": True,
                        "description": "Titel der Audiodatei"
                    },
                    {
                        "name": "performer",
                        "type": "VARCHAR(255)",
                        "nullable": True,
                        "description": "Interpret der Audiodatei"
                    },
                    {
                        "name": "group_id",
                        "type": "INTEGER",
                        "foreign_key": "telegram_groups.id",
                        "nullable": False,
                        "description": "Referenz zur Telegram-Gruppe"
                    },
                    {
                        "name": "downloaded_at",
                        "type": "DATETIME",
                        "nullable": True,
                        "description": "Zeitpunkt des Downloads"
                    },
                    {
                        "name": "status",
                        "type": "VARCHAR(50)",
                        "nullable": False,
                        "description": "Download-Status"
                    },
                    {
                        "name": "error_message",
                        "type": "TEXT",
                        "nullable": True,
                        "description": "Fehlermeldung bei fehlgeschlagenem Download"
                    },
                    {
                        "name": "download_attempts",
                        "type": "INTEGER",
                        "default": 0,
                        "description": "Anzahl der Download-Versuche"
                    }
                ],
                "indexes": [
                    {
                        "name": "idx_audio_files_file_id",
                        "columns": ["file_id"],
                        "unique": True,
                        "description": "Eindeutiger Index auf file_id"
                    },
                    {
                        "name": "idx_audio_files_status",
                        "columns": ["status"],
                        "unique": False,
                        "description": "Index für Status-Abfragen"
                    },
                    {
                        "name": "idx_audio_files_group_id",
                        "columns": ["group_id"],
                        "unique": False,
                        "description": "Index für Gruppen-Abfragen"
                    },
                    {
                        "name": "idx_audio_files_downloaded_at",
                        "columns": ["downloaded_at"],
                        "unique": False,
                        "description": "Index für Sortierung nach Download-Zeit"
                    }
                ]
            }
            
            # Informationen über TelegramGroup-Tabelle
            schema_info["tables"]["telegram_groups"] = {
                "name": "telegram_groups",
                "description": "Speichert Informationen zu Telegram-Gruppen",
                "columns": [
                    {
                        "name": "id",
                        "type": "INTEGER",
                        "primary_key": True,
                        "nullable": False,
                        "description": "Eindeutige ID des Datensatzes"
                    },
                    {
                        "name": "group_id",
                        "type": "BIGINT",
                        "unique": True,
                        "nullable": False,
                        "description": "Eindeutige Telegram-Gruppen-ID"
                    },
                    {
                        "name": "title",
                        "type": "VARCHAR(255)",
                        "nullable": False,
                        "description": "Titel der Telegram-Gruppe"
                    },
                    {
                        "name": "username",
                        "type": "VARCHAR(255)",
                        "nullable": True,
                        "description": "Benutzername der Telegram-Gruppe"
                    }
                ],
                "indexes": [
                    {
                        "name": "idx_telegram_groups_group_id",
                        "columns": ["group_id"],
                        "unique": True,
                        "description": "Eindeutiger Index auf group_id"
                    }
                ]
            }
            
        except Exception as e:
            logger.error(f"Fehler bei der Schema-Dokumentation: {e}")
            schema_info["error"] = str(e)
        
        return schema_info
    
    def generate_relationship_diagram(self) -> str:
        """
        Generiert ein Beziehungsdiagramm im Mermaid-Format.
        
        Returns:
            Mermaid-Diagramm als String
        """
        logger.info("Generiere Beziehungsdiagramm")
        
        diagram = """erDiagram
    TELEGRAM_GROUPS ||--o{ AUDIO_FILES : contains
    
    TELEGRAM_GROUPS {
        int id PK
        bigint group_id UK
        string title
        string username
    }
    
    AUDIO_FILES {
        int id PK
        string file_id UK
        string file_name
        int file_size
        int duration
        string title
        string performer
        int group_id FK
        datetime downloaded_at
        string status
        text error_message
        int download_attempts
    }"""
        
        return diagram
    
    def generate_data_flow_diagram(self) -> str:
        """
        Generiert ein Datenflussdiagramm im Mermaid-Format.
        
        Returns:
            Mermaid-Diagramm als String
        """
        logger.info("Generiere Datenflussdiagramm")
        
        diagram = """graph TD
    A[Telegram API] --> B(Downloader)
    B --> C[(SQLite Database)]
    C --> D[Query Interface]
    D --> E[Application]
    C --> F[Backup System]
    C --> G[Replication System]"""
        
        return diagram
    
    def generate_api_documentation(self) -> Dict[str, Any]:
        """
        Generiert die API-Dokumentation.
        
        Returns:
            Dictionary mit API-Dokumentation
        """
        logger.info("Generiere API-Dokumentation")
        
        api_docs = {
            "generated_at": datetime.now().isoformat(),
            "models": {
                "AudioFile": {
                    "description": "Repräsentiert eine heruntergeladene Audiodatei",
                    "fields": {
                        "id": "Eindeutige ID des Datensatzes",
                        "file_id": "Eindeutige Telegram-Datei-ID",
                        "file_name": "Name der Datei",
                        "file_size": "Größe der Datei in Bytes",
                        "duration": "Dauer der Audiodatei in Sekunden",
                        "title": "Titel der Audiodatei",
                        "performer": "Interpret der Audiodatei",
                        "group": "Referenz zur Telegram-Gruppe",
                        "downloaded_at": "Zeitpunkt des Downloads",
                        "status": "Download-Status",
                        "error_message": "Fehlermeldung bei fehlgeschlagenem Download",
                        "download_attempts": "Anzahl der Download-Versuche"
                    },
                    "methods": {
                        "save": "Speichert den Datensatz in der Datenbank",
                        "delete_instance": "Löscht den Datensatz aus der Datenbank",
                        "get_by_file_id": "Findet einen Datensatz anhand der file_id"
                    }
                },
                "TelegramGroup": {
                    "description": "Repräsentiert eine Telegram-Gruppe",
                    "fields": {
                        "id": "Eindeutige ID des Datensatzes",
                        "group_id": "Eindeutige Telegram-Gruppen-ID",
                        "title": "Titel der Telegram-Gruppe",
                        "username": "Benutzername der Telegram-Gruppe"
                    },
                    "methods": {
                        "save": "Speichert den Datensatz in der Datenbank",
                        "delete_instance": "Löscht den Datensatz aus der Datenbank",
                        "get_by_group_id": "Findet einen Datensatz anhand der group_id"
                    }
                }
            },
            "database_functions": {
                "init_db": "Initialisiert die Datenbank und erstellt Tabellen",
                "optimize_database_indexes": "Optimiert die Datenbankindizes",
                "run_migrations": "Führt Datenbankmigrationen aus",
                "create_extended_tables": "Erstellt erweiterte Tabellen"
            }
        }
        
        return api_docs
    
    def generate_full_documentation(self) -> Dict[str, Any]:
        """
        Generiert die vollständige Datenbank-Dokumentation.
        
        Returns:
            Dictionary mit vollständiger Dokumentation
        """
        logger.info("Generiere vollständige Datenbank-Dokumentation")
        
        documentation = {
            "generated_at": datetime.now().isoformat(),
            "schema": self.generate_schema_documentation(),
            "relationship_diagram": self.generate_relationship_diagram(),
            "data_flow_diagram": self.generate_data_flow_diagram(),
            "api_documentation": self.generate_api_documentation()
        }
        
        return documentation
    
    def save_documentation(self, format: str = "json") -> Optional[Path]:
        """
        Speichert die Dokumentation in einem bestimmten Format.
        
        Args:
            format: Ausgabeformat ('json', 'md')
            
        Returns:
            Pfad zur erstellten Dokumentationsdatei
        """
        try:
            documentation = self.generate_full_documentation()
            
            if format.lower() == "json":
                doc_file = self.docs_dir / "database_documentation.json"
                with open(doc_file, "w", encoding="utf-8") as f:
                    json.dump(documentation, f, indent=2, ensure_ascii=False)
                logger.info(f"Datenbank-Dokumentation als JSON gespeichert: {doc_file}")
                return doc_file
                
            elif format.lower() == "md":
                doc_file = self.docs_dir / "database_documentation.md"
                with open(doc_file, "w", encoding="utf-8") as f:
                    # Schema-Dokumentation
                    f.write("# Datenbank-Dokumentation\n\n")
                    f.write(f"Generiert am: {documentation['generated_at']}\n\n")
                    
                    # Tabellen
                    f.write("## Tabellen\n\n")
                    for table_name, table_info in documentation["schema"]["tables"].items():
                        f.write(f"### {table_info['name']}\n\n")
                        f.write(f"{table_info['description']}\n\n")
                        
                        f.write("#### Spalten\n\n")
                        f.write("| Name | Typ | Nullable | Beschreibung |\n")
                        f.write("|------|-----|----------|--------------|\n")
                        for column in table_info["columns"]:
                            nullable = "Ja" if column.get("nullable", True) else "Nein"
                            f.write(f"| {column['name']} | {column['type']} | {nullable} | {column['description']} |\n")
                        f.write("\n")
                    
                    # Beziehungsdiagramm
                    f.write("## Beziehungsdiagramm\n\n")
                    f.write("```mermaid\n")
                    f.write(documentation["relationship_diagram"])
                    f.write("\n```\n\n")
                    
                    # Datenflussdiagramm
                    f.write("## Datenflussdiagramm\n\n")
                    f.write("```mermaid\n")
                    f.write(documentation["data_flow_diagram"])
                    f.write("\n```\n\n")
                
                logger.info(f"Datenbank-Dokumentation als Markdown gespeichert: {doc_file}")
                return doc_file
                
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Dokumentation: {e}")
            return None


# Globale Instanz der Dokumentation
_documentation: Optional[DatabaseDocumentation] = None


def get_database_documentation() -> DatabaseDocumentation:
    """
    Gibt die globale Instanz der DatabaseDocumentation zurück.
    
    Returns:
        DatabaseDocumentation-Instanz
    """
    global _documentation
    if _documentation is None:
        _documentation = DatabaseDocumentation()
    return _documentation


def generate_database_documentation(format: str = "json") -> Optional[Path]:
    """
    Generiert und speichert die Datenbank-Dokumentation.
    
    Args:
        format: Ausgabeformat ('json', 'md')
        
    Returns:
        Pfad zur erstellten Dokumentationsdatei
    """
    try:
        documentation = get_database_documentation()
        return documentation.save_documentation(format)
    except Exception as e:
        logger.error(f"Fehler bei der Generierung der Datenbank-Dokumentation: {e}")
        return None


def get_schema_documentation() -> Dict[str, Any]:
    """
    Gibt die Schema-Dokumentation zurück.
    
    Returns:
        Dictionary mit Schema-Informationen
    """
    try:
        documentation = get_database_documentation()
        return documentation.generate_schema_documentation()
    except Exception as e:
        logger.error(f"Fehler bei der Schema-Dokumentation: {e}")
        return {}


def get_relationship_diagram() -> str:
    """
    Gibt das Beziehungsdiagramm zurück.
    
    Returns:
        Mermaid-Diagramm als String
    """
    try:
        documentation = get_database_documentation()
        return documentation.generate_relationship_diagram()
    except Exception as e:
        logger.error(f"Fehler beim Beziehungsdiagramm: {e}")
        return ""


def get_data_flow_diagram() -> str:
    """
    Gibt das Datenflussdiagramm zurück.
    
    Returns:
        Mermaid-Diagramm als String
    """
    try:
        documentation = get_database_documentation()
        return documentation.generate_data_flow_diagram()
    except Exception as e:
        logger.error(f"Fehler beim Datenflussdiagramm: {e}")
        return ""


def get_api_documentation() -> Dict[str, Any]:
    """
    Gibt die API-Dokumentation zurück.
    
    Returns:
        Dictionary mit API-Dokumentation
    """
    try:
        documentation = get_database_documentation()
        return documentation.generate_api_documentation()
    except Exception as e:
        logger.error(f"Fehler bei der API-Dokumentation: {e}")
        return {}