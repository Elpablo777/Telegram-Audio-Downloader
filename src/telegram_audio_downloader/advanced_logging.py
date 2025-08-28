"""
Erweiterte Protokollierung für den Telegram Audio Downloader.
"""

import logging
import json
import traceback
from datetime import datetime
from typing import Any, Dict, Optional, Union
from pathlib import Path
import asyncio
from dataclasses import dataclass, asdict
from enum import Enum

from .error_handling import TelegramAudioError

logger = logging.getLogger(__name__)

class LogLevel(Enum):
    """Protokollstufen für verschiedene Ereignistypen."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

@dataclass
class LogEntry:
    """Ein einzelner Protokolleintrag mit erweiterten Informationen."""
    timestamp: datetime
    level: LogLevel
    module: str
    message: str
    user_action: Optional[str] = None
    performance_metrics: Optional[Dict[str, Any]] = None
    system_info: Optional[Dict[str, Any]] = None
    error_details: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None
    trace_id: Optional[str] = None

class AdvancedLogger:
    """Erweitertes Protokollierungssystem mit detaillierten Berichten."""
    
    def __init__(self, log_dir: Union[str, Path] = "logs"):
        """
        Initialisiert das erweiterte Protokollierungssystem.
        
        Args:
            log_dir: Verzeichnis für Protokolldateien
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True, parents=True)  # Stelle sicher, dass alle Elternverzeichnisse existieren
        
        # Erstelle separate Logger für verschiedene Ereignistypen
        self.error_logger = self._setup_logger("errors", "errors.log")
        self.performance_logger = self._setup_logger("performance", "performance.log")
        self.user_logger = self._setup_logger("user_actions", "user_actions.log")
        self.system_logger = self._setup_logger("system_events", "system_events.log")
        self.audit_logger = self._setup_logger("audit", "audit.log")
        
    def _setup_logger(self, name: str, filename: str) -> logging.Logger:
        """
        Erstellt und konfiguriert einen benannten Logger.
        
        Args:
            name: Name des Loggers
            filename: Name der Protokolldatei
            
        Returns:
            Konfigurierter Logger
        """
        logger_instance = logging.getLogger(f"telegram_audio_downloader.{name}")
        logger_instance.setLevel(logging.DEBUG)
        
        # Vermeide doppelte Handler
        if not logger_instance.handlers:
            # Stelle sicher, dass das Verzeichnis existiert
            log_file_path = self.log_dir / filename
            log_file_path.parent.mkdir(exist_ok=True, parents=True)
            
            handler = logging.FileHandler(log_file_path, encoding='utf-8')
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger_instance.addHandler(handler)
        
        return logger_instance
    
    def log_error(self, error: Exception, module: str, user_action: Optional[str] = None, 
                  context: Optional[Dict[str, Any]] = None, trace_id: Optional[str] = None) -> None:
        """
        Protokolliert einen Fehler mit detaillierten Informationen.
        
        Args:
            error: Aufgetretener Fehler
            module: Modul, in dem der Fehler auftrat
            user_action: Vom Benutzer ausgeführte Aktion
            context: Kontextinformationen
            trace_id: Trace-ID für die Fehlerverfolgung
        """
        error_details = {
            "type": type(error).__name__,
            "message": str(error),
            "traceback": traceback.format_exc()
        }
        
        if isinstance(error, TelegramAudioError):
            error_details.update({
                "error_code": getattr(error, 'error_code', None),
                "context": getattr(error, 'context', {}),
                "timestamp": getattr(error, 'timestamp', None)
            })
        
        log_entry = LogEntry(
            timestamp=datetime.now(),
            level=LogLevel.ERROR,
            module=module,
            message=str(error),
            user_action=user_action,
            error_details=error_details,
            context=context,
            trace_id=trace_id
        )
        
        self.error_logger.error(self._format_log_entry(log_entry))
    
    def log_performance(self, metrics: Dict[str, Any], module: str, 
                       user_action: Optional[str] = None, context: Optional[Dict[str, Any]] = None,
                       trace_id: Optional[str] = None) -> None:
        """
        Protokolliert Performance-Metriken.
        
        Args:
            metrics: Performance-Metriken
            module: Modul, das die Metriken erzeugte
            user_action: Vom Benutzer ausgeführte Aktion
            context: Kontextinformationen
            trace_id: Trace-ID für die Fehlerverfolgung
        """
        log_entry = LogEntry(
            timestamp=datetime.now(),
            level=LogLevel.INFO,
            module=module,
            message="Performance metrics recorded",
            user_action=user_action,
            performance_metrics=metrics,
            context=context,
            trace_id=trace_id
        )
        
        self.performance_logger.info(self._format_log_entry(log_entry))
    
    def log_user_action(self, action: str, module: str, details: Optional[Dict[str, Any]] = None,
                       context: Optional[Dict[str, Any]] = None, trace_id: Optional[str] = None) -> None:
        """
        Protokolliert eine Benutzeraktion.
        
        Args:
            action: Ausgeführte Aktion
            module: Modul, in dem die Aktion ausgeführt wurde
            details: Detaillierte Informationen zur Aktion
            context: Kontextinformationen
            trace_id: Trace-ID für die Fehlerverfolgung
        """
        log_entry = LogEntry(
            timestamp=datetime.now(),
            level=LogLevel.INFO,
            module=module,
            message=f"User action: {action}",
            user_action=action,
            context={**(context or {}), **(details or {})},
            trace_id=trace_id
        )
        
        self.user_logger.info(self._format_log_entry(log_entry))
    
    def log_system_event(self, event: str, module: str, details: Optional[Dict[str, Any]] = None,
                        level: LogLevel = LogLevel.INFO, context: Optional[Dict[str, Any]] = None,
                        trace_id: Optional[str] = None) -> None:
        """
        Protokolliert ein Systemereignis.
        
        Args:
            event: Beschreibung des Ereignisses
            module: Modul, in dem das Ereignis auftrat
            details: Detaillierte Informationen zum Ereignis
            level: Protokollstufe
            context: Kontextinformationen
            trace_id: Trace-ID für die Fehlerverfolgung
        """
        log_entry = LogEntry(
            timestamp=datetime.now(),
            level=level,
            module=module,
            message=f"System event: {event}",
            system_info=details,
            context=context,
            trace_id=trace_id
        )
        
        log_func = getattr(self.system_logger, level.value.lower())
        log_func(self._format_log_entry(log_entry))
    
    def log_audit_event(self, event: str, module: str, user: Optional[str] = None,
                       details: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None,
                       trace_id: Optional[str] = None) -> None:
        """
        Protokolliert ein Audit-Ereignis.
        
        Args:
            event: Beschreibung des Audit-Ereignisses
            module: Modul, in dem das Ereignis auftrat
            user: Benutzer, der die Aktion ausgeführt hat
            details: Detaillierte Informationen zum Ereignis
            context: Kontextinformationen
            trace_id: Trace-ID für die Fehlerverfolgung
        """
        audit_info = {
            "event": event,
            "user": user,
            "timestamp": datetime.now().isoformat()
        }
        
        log_entry = LogEntry(
            timestamp=datetime.now(),
            level=LogLevel.INFO,
            module=module,
            message=f"Audit event: {event}",
            system_info=audit_info,
            context={**(context or {}), **(details or {})},
            trace_id=trace_id
        )
        
        self.audit_logger.info(self._format_log_entry(log_entry))
    
    def _format_log_entry(self, entry: LogEntry) -> str:
        """
        Formatiert einen Protokolleintrag als JSON-String.
        
        Args:
            entry: Zu formatierender Protokolleintrag
            
        Returns:
            JSON-formatierter Protokolleintrag
        """
        # Konvertiere das Datenklasse-Objekt in ein Dictionary
        entry_dict = asdict(entry)
        
        # Konvertiere den Timestamp in einen String
        entry_dict['timestamp'] = entry_dict['timestamp'].isoformat()
        
        # Konvertiere das LogLevel-Enum in einen String
        entry_dict['level'] = entry_dict['level'].value
        
        # Entferne None-Werte
        entry_dict = {k: v for k, v in entry_dict.items() if v is not None}
        
        return json.dumps(entry_dict, ensure_ascii=False)
    
    async def flush_logs(self) -> None:
        """
        Leert alle Protokollpuffer.
        """
        # In einer echten Implementierung würden wir hier sicherstellen,
        # dass alle Protokolleinträge geschrieben wurden
        await asyncio.sleep(0)  # Yield control to event loop

# Globale Instanz des erweiterten Loggers
_advanced_logger: Optional[AdvancedLogger] = None

def get_advanced_logger(log_dir: Union[str, Path] = "logs") -> AdvancedLogger:
    """
    Gibt die globale Instanz des erweiterten Loggers zurück.
    
    Args:
        log_dir: Verzeichnis für Protokolldateien
        
    Returns:
        Instanz des AdvancedLogger
    """
    global _advanced_logger
    if _advanced_logger is None:
        _advanced_logger = AdvancedLogger(log_dir)
    return _advanced_logger

# Hilfsfunktionen für die Verwendung außerhalb der Klasse
def log_error(error: Exception, module: str, user_action: Optional[str] = None, 
              context: Optional[Dict[str, Any]] = None, trace_id: Optional[str] = None) -> None:
    """
    Protokolliert einen Fehler mit detaillierten Informationen.
    
    Args:
        error: Aufgetretener Fehler
        module: Modul, in dem der Fehler auftrat
        user_action: Vom Benutzer ausgeführte Aktion
        context: Kontextinformationen
        trace_id: Trace-ID für die Fehlerverfolgung
    """
    logger = get_advanced_logger()
    logger.log_error(error, module, user_action, context, trace_id)

def log_performance(metrics: Dict[str, Any], module: str, 
                   user_action: Optional[str] = None, context: Optional[Dict[str, Any]] = None,
                   trace_id: Optional[str] = None) -> None:
    """
    Protokolliert Performance-Metriken.
    
    Args:
        metrics: Performance-Metriken
        module: Modul, das die Metriken erzeugte
        user_action: Vom Benutzer ausgeführte Aktion
        context: Kontextinformationen
        trace_id: Trace-ID für die Fehlerverfolgung
    """
    logger = get_advanced_logger()
    logger.log_performance(metrics, module, user_action, context, trace_id)

def log_user_action(action: str, module: str, details: Optional[Dict[str, Any]] = None,
                   context: Optional[Dict[str, Any]] = None, trace_id: Optional[str] = None) -> None:
    """
    Protokolliert eine Benutzeraktion.
    
    Args:
        action: Ausgeführte Aktion
        module: Modul, in dem die Aktion ausgeführt wurde
        details: Detaillierte Informationen zur Aktion
        context: Kontextinformationen
        trace_id: Trace-ID für die Fehlerverfolgung
    """
    logger = get_advanced_logger()
    logger.log_user_action(action, module, details, context, trace_id)

def log_system_event(event: str, module: str, details: Optional[Dict[str, Any]] = None,
                    level: LogLevel = LogLevel.INFO, context: Optional[Dict[str, Any]] = None,
                    trace_id: Optional[str] = None) -> None:
    """
    Protokolliert ein Systemereignis.
    
    Args:
        event: Beschreibung des Ereignisses
        module: Modul, in dem das Ereignis auftrat
        details: Detaillierte Informationen zum Ereignis
        level: Protokollstufe
        context: Kontextinformationen
        trace_id: Trace-ID für die Fehlerverfolgung
    """
    logger = get_advanced_logger()
    logger.log_system_event(event, module, details, level, context, trace_id)

def log_audit_event(event: str, module: str, user: Optional[str] = None,
                   details: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None,
                   trace_id: Optional[str] = None) -> None:
    """
    Protokolliert ein Audit-Ereignis.
    
    Args:
        event: Beschreibung des Audit-Ereignisses
        module: Modul, in dem das Ereignis auftrat
        user: Benutzer, der die Aktion ausgeführt hat
        details: Detaillierte Informationen zum Ereignis
        context: Kontextinformationen
        trace_id: Trace-ID für die Fehlerverfolgung
    """
    logger = get_advanced_logger()
    logger.log_audit_event(event, module, user, details, context, trace_id)