"""
Audit-Logging für den Telegram Audio Downloader.
"""

import json
import hashlib
from datetime import datetime
from typing import Any, Dict, Optional, List
from pathlib import Path
import logging.handlers


class AuditLogger:
    """Logger für Audit-Events mit Sicherheitsrelevanz."""

    def __init__(self, log_file: str = "logs/audit.log"):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """Richtet den Audit-Logger ein."""
        logger = logging.getLogger("audit")
        logger.setLevel(logging.INFO)
        logger.handlers.clear()

        # File Handler mit Rotation
        handler = logging.handlers.RotatingFileHandler(
            filename=self.log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8"
        )

        # JSON Formatter
        formatter = AuditJSONFormatter()
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        # Verhindere das Propagieren zu anderen Loggern
        logger.propagate = False

        return logger

    def log_user_login(self, user_id: str, ip_address: Optional[str] = None) -> None:
        """
        Loggt eine Benutzeranmeldung.

        Args:
            user_id: ID des Benutzers
            ip_address: IP-Adresse des Benutzers (optional)
        """
        self._log_event(
            event_type="user_login",
            user_id=user_id,
            ip_address=ip_address
        )

    def log_user_logout(self, user_id: str) -> None:
        """
        Loggt eine Benutzerabmeldung.

        Args:
            user_id: ID des Benutzers
        """
        self._log_event(
            event_type="user_logout",
            user_id=user_id
        )

    def log_configuration_change(
        self, 
        user_id: str, 
        config_key: str, 
        old_value: Any, 
        new_value: Any,
        reason: Optional[str] = None
    ) -> None:
        """
        Loggt eine Konfigurationsänderung.

        Args:
            user_id: ID des Benutzers
            config_key: Name der Konfigurationseinstellung
            old_value: Alter Wert
            new_value: Neuer Wert
            reason: Grund für die Änderung (optional)
        """
        # Maskiere sensible Daten
        masked_old_value = self._mask_sensitive_data(config_key, old_value)
        masked_new_value = self._mask_sensitive_data(config_key, new_value)

        self._log_event(
            event_type="configuration_change",
            user_id=user_id,
            config_key=config_key,
            old_value=masked_old_value,
            new_value=masked_new_value,
            reason=reason
        )

    def log_data_change(
        self,
        user_id: str,
        table: str,
        record_id: Any,
        action: str,
        old_data: Optional[Dict[str, Any]] = None,
        new_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Loggt eine Datenänderung.

        Args:
            user_id: ID des Benutzers
            table: Name der Tabelle
            record_id: ID des Datensatzes
            action: Aktion (create, update, delete)
            old_data: Alte Daten (optional)
            new_data: Neue Daten (optional)
        """
        # Maskiere sensible Daten
        masked_old_data = self._mask_sensitive_dict(old_data) if old_data else None
        masked_new_data = self._mask_sensitive_dict(new_data) if new_data else None

        self._log_event(
            event_type="data_change",
            user_id=user_id,
            table=table,
            record_id=record_id,
            action=action,
            old_data=masked_old_data,
            new_data=masked_new_data
        )

    def log_system_event(
        self,
        event_type: str,
        description: str,
        severity: str = "INFO",
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Loggt ein Systemereignis.

        Args:
            event_type: Typ des Ereignisses
            description: Beschreibung des Ereignisses
            severity: Schweregrad (INFO, WARNING, ERROR)
            details: Zusätzliche Details (optional)
        """
        self._log_event(
            event_type=event_type,
            description=description,
            severity=severity,
            details=details
        )

    def log_security_event(
        self,
        event_type: str,
        description: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Loggt ein sicherheitsrelevantes Ereignis.

        Args:
            event_type: Typ des Ereignisses
            description: Beschreibung des Ereignisses
            user_id: ID des Benutzers (optional)
            ip_address: IP-Adresse (optional)
            details: Zusätzliche Details (optional)
        """
        self._log_event(
            event_type=event_type,
            description=description,
            user_id=user_id,
            ip_address=ip_address,
            details=details,
            security_relevant=True
        )

    def _log_event(self, event_type: str, **kwargs: Any) -> None:
        """
        Loggt ein Audit-Event.

        Args:
            event_type: Typ des Ereignisses
            **kwargs: Zusätzliche Ereignisdaten
        """
        event_data = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            **kwargs
        }

        # Erstelle einen Hash des Ereignisses für Integritätsprüfung
        event_hash = self._create_event_hash(event_data)
        event_data["event_hash"] = event_hash

        self.logger.info(json.dumps(event_data, ensure_ascii=False))

    def _mask_sensitive_data(self, key: str, value: Any) -> Any:
        """
        Maskiert sensible Daten.

        Args:
            key: Schlüssel des Datenfelds
            value: Wert des Datenfelds

        Returns:
            Maskierter Wert oder Originalwert
        """
        sensitive_keywords = [
            "password", "passwd", "pwd", "secret", "token", "key", 
            "api", "hash", "credential", "auth", "session"
        ]

        key_lower = key.lower()
        if any(keyword in key_lower for keyword in sensitive_keywords):
            if isinstance(value, str) and len(value) > 0:
                return "*" * min(len(value), 8)  # Maskiere mit Sternchen
            elif value is not None:
                return "***"  # Generische Maskierung
        return value

    def _mask_sensitive_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Maskiert sensible Daten in einem Dictionary.

        Args:
            data: Dictionary mit Daten

        Returns:
            Dictionary mit maskierten Daten
        """
        masked_data = {}
        for key, value in data.items():
            masked_data[key] = self._mask_sensitive_data(key, value)
        return masked_data

    def _create_event_hash(self, event_data: Dict[str, Any]) -> str:
        """
        Erstellt einen Hash des Ereignisses für Integritätsprüfung.

        Args:
            event_data: Ereignisdaten

        Returns:
            Hash des Ereignisses
        """
        # Entferne den Hash selbst aus den Daten, um eine Rekursion zu vermeiden
        data_copy = event_data.copy()
        data_copy.pop("event_hash", None)

        # Erstelle einen String aus den sortierten Daten
        data_string = json.dumps(data_copy, sort_keys=True, ensure_ascii=False)

        # Erstelle SHA256-Hash
        return hashlib.sha256(data_string.encode('utf-8')).hexdigest()

    def get_audit_events(
        self, 
        event_type: Optional[str] = None, 
        user_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Ruft Audit-Events aus der Log-Datei ab.

        Args:
            event_type: Filter nach Ereignistyp (optional)
            user_id: Filter nach Benutzer-ID (optional)
            start_time: Startzeit für den Zeitraum (optional)
            end_time: Endzeit für den Zeitraum (optional)

        Returns:
            Liste der Audit-Events
        """
        events = []
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        event = json.loads(line.strip())
                        
                        # Filter anwenden
                        if event_type and event.get("event_type") != event_type:
                            continue
                        if user_id and event.get("user_id") != user_id:
                            continue
                        if start_time or end_time:
                            event_time = datetime.fromisoformat(event.get("timestamp", ""))
                            if start_time and event_time < start_time:
                                continue
                            if end_time and event_time > end_time:
                                continue
                        
                        events.append(event)
                    except json.JSONDecodeError:
                        # Überspringe ungültige Zeilen
                        continue
        except FileNotFoundError:
            # Log-Datei existiert noch nicht
            pass

        return events


class AuditJSONFormatter(logging.Formatter):
    """JSON-Formatter für Audit-Logs."""

    def format(self, record: logging.LogRecord) -> str:
        """Formatiert den Log-Eintrag als JSON."""
        # Wenn die Nachricht bereits JSON ist, geben wir sie direkt zurück
        if isinstance(record.msg, str) and record.msg.startswith('{'):
            try:
                # Prüfe ob es gültiges JSON ist
                json.loads(record.msg)
                return record.msg
            except json.JSONDecodeError:
                pass
        
        # Andernfalls formatieren wir es als normale Log-Nachricht
        return super().format(record)


# Globale Instanz des AuditLoggers
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """
    Gibt die globale Instanz des AuditLoggers zurück.

    Returns:
        Die AuditLogger-Instanz
    """
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


def log_user_login(user_id: str, ip_address: Optional[str] = None) -> None:
    """
    Loggt eine Benutzeranmeldung.

    Args:
        user_id: ID des Benutzers
        ip_address: IP-Adresse des Benutzers (optional)
    """
    logger = get_audit_logger()
    logger.log_user_login(user_id, ip_address)


def log_user_logout(user_id: str) -> None:
    """
    Loggt eine Benutzerabmeldung.

    Args:
        user_id: ID des Benutzers
    """
    logger = get_audit_logger()
    logger.log_user_logout(user_id)


def log_configuration_change(
    user_id: str, 
    config_key: str, 
    old_value: Any, 
    new_value: Any,
    reason: Optional[str] = None
) -> None:
    """
    Loggt eine Konfigurationsänderung.

    Args:
        user_id: ID des Benutzers
        config_key: Name der Konfigurationseinstellung
        old_value: Alter Wert
        new_value: Neuer Wert
        reason: Grund für die Änderung (optional)
    """
    logger = get_audit_logger()
    logger.log_configuration_change(user_id, config_key, old_value, new_value, reason)


def log_data_change(
    user_id: str,
    table: str,
    record_id: Any,
    action: str,
    old_data: Optional[Dict[str, Any]] = None,
    new_data: Optional[Dict[str, Any]] = None
) -> None:
    """
    Loggt eine Datenänderung.

    Args:
        user_id: ID des Benutzers
        table: Name der Tabelle
        record_id: ID des Datensatzes
        action: Aktion (create, update, delete)
        old_data: Alte Daten (optional)
        new_data: Neue Daten (optional)
    """
    logger = get_audit_logger()
    logger.log_data_change(user_id, table, record_id, action, old_data, new_data)


def log_system_event(
    event_type: str,
    description: str,
    severity: str = "INFO",
    details: Optional[Dict[str, Any]] = None
) -> None:
    """
    Loggt ein Systemereignis.

    Args:
        event_type: Typ des Ereignisses
        description: Beschreibung des Ereignisses
        severity: Schweregrad (INFO, WARNING, ERROR)
        details: Zusätzliche Details (optional)
    """
    logger = get_audit_logger()
    logger.log_system_event(event_type, description, severity, details)


def log_security_event(
    event_type: str,
    description: str,
    user_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> None:
    """
    Loggt ein sicherheitsrelevantes Ereignis.

    Args:
        event_type: Typ des Ereignisses
        description: Beschreibung des Ereignisses
        user_id: ID des Benutzers (optional)
        ip_address: IP-Adresse (optional)
        details: Zusätzliche Details (optional)
    """
    logger = get_audit_logger()
    logger.log_security_event(event_type, description, user_id, ip_address, details)


def log_audit_event(event_type: str, description: str, details: Optional[Dict[str, Any]] = None) -> None:
    """
    Loggt ein Audit-Event.
    
    Args:
        event_type: Typ des Ereignisses
        description: Beschreibung des Ereignisses
        details: Zusätzliche Details (optional)
    """
    logger = get_audit_logger()
    logger.log_system_event(event_type, description, "INFO", details)