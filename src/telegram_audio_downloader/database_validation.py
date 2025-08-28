"""
Datenbank-Validierung für den Telegram Audio Downloader.

Erweiterte Validierung für:
- Datenintegrität
- Geschäftsregeln
- Konsistenzprüfungen
- Benutzerdefinierte Constraints
"""

import re
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from pathlib import Path

from .models import AudioFile, TelegramGroup, db
from .logging_config import get_logger
from peewee import fn

logger = get_logger(__name__)


class DatabaseValidator:
    """Verwaltet die Datenbank-Validierung."""
    
    def __init__(self):
        """Initialisiert den DatabaseValidator."""
        self.validation_rules = {}
        self.custom_constraints = {}
        self.business_rules = {}
        self._register_default_validations()
        
        logger.info("DatabaseValidator initialisiert")
    
    def _register_default_validations(self) -> None:
        """Registriert Standard-Validierungsregeln."""
        # AudioFile Validierungen
        self.add_validation_rule("audio_files", "file_id", self._validate_file_id)
        self.add_validation_rule("audio_files", "status", self._validate_status)
        self.add_validation_rule("audio_files", "duration", self._validate_duration)
        self.add_validation_rule("audio_files", "file_size", self._validate_file_size)
        self.add_validation_rule("audio_files", "title", self._validate_title)
        self.add_validation_rule("audio_files", "performer", self._validate_performer)
        
        # TelegramGroup Validierungen
        self.add_validation_rule("telegram_groups", "group_id", self._validate_group_id)
        self.add_validation_rule("telegram_groups", "title", self._validate_group_title)
        
        logger.debug("Standard-Validierungsregeln registriert")
    
    def add_validation_rule(self, table_name: str, column_name: str, 
                           validation_func: Callable[[Any], bool]) -> None:
        """
        Fügt eine Validierungsregel hinzu.
        
        Args:
            table_name: Name der Tabelle
            column_name: Name der Spalte
            validation_func: Validierungsfunktion
        """
        if table_name not in self.validation_rules:
            self.validation_rules[table_name] = {}
        
        self.validation_rules[table_name][column_name] = validation_func
        logger.debug(f"Validierungsregel für {table_name}.{column_name} hinzugefügt")
    
    def add_custom_constraint(self, constraint_name: str, 
                             constraint_func: Callable[[], bool]) -> None:
        """
        Fügt eine benutzerdefinierte Constraint hinzu.
        
        Args:
            constraint_name: Name der Constraint
            constraint_func: Constraint-Funktion
        """
        self.custom_constraints[constraint_name] = constraint_func
        logger.debug(f"Benutzerdefinierte Constraint '{constraint_name}' hinzugefügt")
    
    def add_business_rule(self, rule_name: str, 
                         rule_func: Callable[[], bool]) -> None:
        """
        Fügt eine Geschäftsregel hinzu.
        
        Args:
            rule_name: Name der Regel
            rule_func: Regel-Funktion
        """
        self.business_rules[rule_name] = rule_func
        logger.debug(f"Geschäftsregel '{rule_name}' hinzugefügt")
    
    def validate_record(self, table_name: str, record_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Validiert einen Datensatz.
        
        Args:
            table_name: Name der Tabelle
            record_data: Zu validierende Daten
            
        Returns:
            Dictionary mit Validierungsfehlern
        """
        errors = {}
        
        # Spaltenweise Validierung
        if table_name in self.validation_rules:
            for column_name, value in record_data.items():
                if column_name in self.validation_rules[table_name]:
                    validation_func = self.validation_rules[table_name][column_name]
                    if not validation_func(value):
                        if column_name not in errors:
                            errors[column_name] = []
                        errors[column_name].append(f"Ungültiger Wert: {value}")
        
        return errors
    
    def validate_integrity(self) -> Dict[str, List[str]]:
        """
        Führt Datenintegritätsprüfungen durch.
        
        Returns:
            Dictionary mit Integritätsfehlern
        """
        errors = {}
        
        try:
            # Prüfe auf doppelte file_id in AudioFile
            duplicate_files = AudioFile.select(AudioFile.file_id).group_by(AudioFile.file_id).having(
                fn.COUNT(AudioFile.file_id) > 1
            )
            
            if duplicate_files.count() > 0:
                errors["audio_files"] = [f"Doppelte file_id gefunden: {[f.file_id for f in duplicate_files]}"]
            
            # Prüfe auf ungültige Fremdschlüssel
            invalid_groups = AudioFile.select().where(
                AudioFile.group.is_null() & (AudioFile.group_id.is_null(False))
            )
            
            if invalid_groups.count() > 0:
                errors["audio_files_foreign_keys"] = [
                    f"Ungültige group_id Referenzen: {invalid_groups.count()} Datensätze"
                ]
                
        except Exception as e:
            logger.error(f"Fehler bei der Integritätsprüfung: {e}")
            if "integrity_check" not in errors:
                errors["integrity_check"] = []
            errors["integrity_check"].append(str(e))
        
        return errors
    
    def validate_business_rules(self) -> Dict[str, List[str]]:
        """
        Validiert Geschäftsregeln.
        
        Returns:
            Dictionary mit Geschäftsregel-Fehlern
        """
        errors = {}
        
        try:
            for rule_name, rule_func in self.business_rules.items():
                try:
                    if not rule_func():
                        if rule_name not in errors:
                            errors[rule_name] = []
                        errors[rule_name].append("Geschäftsregel nicht erfüllt")
                except Exception as e:
                    logger.error(f"Fehler bei der Validierung der Geschäftsregel '{rule_name}': {e}")
                    if rule_name not in errors:
                        errors[rule_name] = []
                    errors[rule_name].append(f"Fehler bei der Validierung: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Fehler bei der Geschäftsregel-Validierung: {e}")
            if "business_rules" not in errors:
                errors["business_rules"] = []
            errors["business_rules"].append(str(e))
        
        return errors
    
    def validate_custom_constraints(self) -> Dict[str, List[str]]:
        """
        Validiert benutzerdefinierte Constraints.
        
        Returns:
            Dictionary mit Constraint-Fehlern
        """
        errors = {}
        
        try:
            for constraint_name, constraint_func in self.custom_constraints.items():
                try:
                    if not constraint_func():
                        if constraint_name not in errors:
                            errors[constraint_name] = []
                        errors[constraint_name].append("Constraint nicht erfüllt")
                except Exception as e:
                    logger.error(f"Fehler bei der Validierung der Constraint '{constraint_name}': {e}")
                    if constraint_name not in errors:
                        errors[constraint_name] = []
                    errors[constraint_name].append(f"Fehler bei der Validierung: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Fehler bei der Constraint-Validierung: {e}")
            if "custom_constraints" not in errors:
                errors["custom_constraints"] = []
            errors["custom_constraints"].append(str(e))
        
        return errors
    
    def run_full_validation(self) -> Dict[str, Any]:
        """
        Führt eine vollständige Datenbank-Validierung durch.
        
        Returns:
            Dictionary mit Validierungsergebnissen
        """
        logger.info("Starte vollständige Datenbank-Validierung")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "record_validation": {},
            "integrity_validation": {},
            "business_rules_validation": {},
            "custom_constraints_validation": {},
            "summary": {}
        }
        
        try:
            # Datenintegrität prüfen
            results["integrity_validation"] = self.validate_integrity()
            
            # Geschäftsregeln validieren
            results["business_rules_validation"] = self.validate_business_rules()
            
            # Benutzerdefinierte Constraints validieren
            results["custom_constraints_validation"] = self.validate_custom_constraints()
            
            # Zusammenfassung erstellen
            error_count = 0
            for validation_type in ["integrity_validation", "business_rules_validation", 
                                  "custom_constraints_validation"]:
                error_count += sum(len(errors) for errors in results[validation_type].values())
            
            results["summary"] = {
                "total_errors": error_count,
                "validation_passed": error_count == 0,
                "validation_types_checked": 3
            }
            
            if error_count == 0:
                logger.info("Datenbank-Validierung erfolgreich abgeschlossen - keine Fehler gefunden")
            else:
                logger.warning(f"Datenbank-Validierung abgeschlossen - {error_count} Fehler gefunden")
                
        except Exception as e:
            logger.error(f"Schwerwiegender Fehler bei der Datenbank-Validierung: {e}")
            results["summary"] = {
                "total_errors": 1,
                "validation_passed": False,
                "error": str(e)
            }
        
        return results
    
    # Validierungsfunktionen für AudioFile
    def _validate_file_id(self, value: str) -> bool:
        """Validiert die file_id."""
        if not value:
            return False
        # Prüfe auf gültige Zeichen (angenommen: alphanumerisch und Unterstriche)
        return bool(re.match(r'^[a-zA-Z0-9_]+$', value)) and len(value) <= 255
    
    def _validate_status(self, value: str) -> bool:
        """Validiert den Status."""
        from .models import DownloadStatus
        valid_statuses = [status.value for status in DownloadStatus]
        return value in valid_statuses
    
    def _validate_duration(self, value: int) -> bool:
        """Validiert die Dauer."""
        return isinstance(value, int) and value >= 0
    
    def _validate_file_size(self, value: int) -> bool:
        """Validiert die Dateigröße."""
        return isinstance(value, int) and value >= 0
    
    def _validate_title(self, value: str) -> bool:
        """Validiert den Titel."""
        return isinstance(value, str) and len(value) <= 255
    
    def _validate_performer(self, value: str) -> bool:
        """Validiert den Interpret."""
        return value is None or (isinstance(value, str) and len(value) <= 255)
    
    # Validierungsfunktionen für TelegramGroup
    def _validate_group_id(self, value: int) -> bool:
        """Validiert die group_id."""
        return isinstance(value, int) and value > 0
    
    def _validate_group_title(self, value: str) -> bool:
        """Validiert den Gruppentitel."""
        return isinstance(value, str) and 1 <= len(value) <= 255


# Globale Instanz des Validators
_validator: Optional[DatabaseValidator] = None


def get_database_validator() -> DatabaseValidator:
    """
    Gibt die globale Instanz des DatabaseValidator zurück.
    
    Returns:
        DatabaseValidator-Instanz
    """
    global _validator
    if _validator is None:
        _validator = DatabaseValidator()
    return _validator


def validate_database() -> Dict[str, Any]:
    """
    Führt eine vollständige Datenbank-Validierung durch.
    
    Returns:
        Dictionary mit Validierungsergebnissen
    """
    try:
        validator = get_database_validator()
        return validator.run_full_validation()
    except Exception as e:
        logger.error(f"Fehler bei der Datenbank-Validierung: {e}")
        return {
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "summary": {
                "total_errors": 1,
                "validation_passed": False
            }
        }


def add_custom_validation_rule(table_name: str, column_name: str, 
                              validation_func: Callable[[Any], bool]) -> None:
    """
    Fügt eine benutzerdefinierte Validierungsregel hinzu.
    
    Args:
        table_name: Name der Tabelle
        column_name: Name der Spalte
        validation_func: Validierungsfunktion
    """
    try:
        validator = get_database_validator()
        validator.add_validation_rule(table_name, column_name, validation_func)
    except Exception as e:
        logger.error(f"Fehler beim Hinzufügen der Validierungsregel: {e}")


def add_business_rule(rule_name: str, rule_func: Callable[[], bool]) -> None:
    """
    Fügt eine Geschäftsregel hinzu.
    
    Args:
        rule_name: Name der Regel
        rule_func: Regel-Funktion
    """
    try:
        validator = get_database_validator()
        validator.add_business_rule(rule_name, rule_func)
    except Exception as e:
        logger.error(f"Fehler beim Hinzufügen der Geschäftsregel: {e}")


def add_custom_constraint(constraint_name: str, 
                         constraint_func: Callable[[], bool]) -> None:
    """
    Fügt eine benutzerdefinierte Constraint hinzu.
    
    Args:
        constraint_name: Name der Constraint
        constraint_func: Constraint-Funktion
    """
    try:
        validator = get_database_validator()
        validator.add_custom_constraint(constraint_name, constraint_func)
    except Exception as e:
        logger.error(f"Fehler beim Hinzufügen der Constraint: {e}")