"""
Strukturiertes Logging für den Telegram Audio Downloader.
"""

import json
import logging
import logging.handlers
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union
from contextvars import ContextVar

from rich.console import Console
from rich.logging import RichHandler


# Kontextvariable für Korrelations-IDs
correlation_id: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)


class JSONFormatter(logging.Formatter):
    """JSON-Formatter für strukturierte Logs."""

    def format(self, record: logging.LogRecord) -> str:
        """Formatiert den Log-Eintrag als JSON."""
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
            "correlation_id": correlation_id.get(),
        }

        # Füge Exception-Informationen hinzu, falls vorhanden
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Füge benutzerdefinierte Felder hinzu
        for key, value in record.__dict__.items():
            if key not in log_entry and not key.startswith('_'):
                log_entry[key] = value

        return json.dumps(log_entry, ensure_ascii=False)


class StructuredLogger:
    """Erweiterte Logging-Klasse mit strukturiertem JSON-Logging."""

    def __init__(self, name: str = "telegram_audio_downloader"):
        self.name: str = name
        self.logger: logging.Logger = logging.getLogger(name)
        self.console: Console = Console()
        self._configured: bool = False

    def configure(
        self,
        level: str = "INFO",
        log_file: Optional[str] = None,
        json_log_file: Optional[str] = None,
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5,
        enable_rich: bool = True,
    ) -> None:
        """
        Konfiguriert das strukturierte Logging-System.

        Args:
            level: Log-Level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Pfad zur traditionellen Log-Datei (optional)
            json_log_file: Pfad zur JSON-Log-Datei (optional)
            max_file_size: Maximale Größe der Log-Datei in Bytes
            backup_count: Anzahl der Backup-Log-Dateien
            enable_rich: Rich-Handler für Terminal-Ausgabe aktivieren
        """
        if self._configured:
            return

        # Logger konfigurieren
        self.logger.setLevel(getattr(logging, level.upper(), logging.INFO))
        self.logger.handlers.clear()

        # Formatter definieren
        json_formatter = JSONFormatter()
        standard_formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Console Handler (Rich oder Standard)
        if enable_rich:
            console_handler: logging.Handler = RichHandler(
                console=self.console,
                show_time=True,
                show_path=True,
                rich_tracebacks=True,
                tracebacks_show_locals=True,
            )
            console_handler.setFormatter(logging.Formatter("%(message)s"))
        else:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(standard_formatter)

        console_handler.setLevel(logging.INFO)
        self.logger.addHandler(console_handler)

        # Traditioneller File Handler (mit Rotation)
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.handlers.RotatingFileHandler(
                filename=log_file,
                maxBytes=max_file_size,
                backupCount=backup_count,
                encoding="utf-8",
            )
            file_handler.setFormatter(standard_formatter)
            file_handler.setLevel(logging.DEBUG)
            self.logger.addHandler(file_handler)

        # JSON File Handler (mit Rotation)
        if json_log_file:
            json_path = Path(json_log_file)
            json_path.parent.mkdir(parents=True, exist_ok=True)

            json_handler = logging.handlers.RotatingFileHandler(
                filename=json_log_file,
                maxBytes=max_file_size,
                backupCount=backup_count,
                encoding="utf-8",
            )
            json_handler.setFormatter(json_formatter)
            json_handler.setLevel(logging.DEBUG)
            self.logger.addHandler(json_handler)

        # Error Handler (separate Datei für Fehler)
        if log_file:
            error_log = log_path.parent / f"{log_path.stem}_errors{log_path.suffix}"
            error_handler = logging.handlers.RotatingFileHandler(
                filename=error_log,
                maxBytes=max_file_size,
                backupCount=backup_count,
                encoding="utf-8",
            )
            error_handler.setFormatter(standard_formatter)
            error_handler.setLevel(logging.ERROR)
            self.logger.addHandler(error_handler)

        # JSON Error Handler
        if json_log_file:
            json_error_log = json_path.parent / f"{json_path.stem}_errors.json"
            json_error_handler = logging.handlers.RotatingFileHandler(
                filename=json_error_log,
                maxBytes=max_file_size,
                backupCount=backup_count,
                encoding="utf-8",
            )
            json_error_handler.setFormatter(json_formatter)
            json_error_handler.setLevel(logging.ERROR)
            self.logger.addHandler(json_error_handler)

        self._configured = True
        self.logger.info(f"Strukturiertes Logging konfiguriert - Level: {level}")

    def get_logger(self) -> logging.Logger:
        """Gibt den konfigurierten Logger zurück."""
        if not self._configured:
            self.configure()
        return self.logger

    def set_correlation_id(self, cid: Optional[str] = None) -> str:
        """
        Setzt eine Korrelations-ID für den aktuellen Kontext.

        Args:
            cid: Optionale Korrelations-ID. Wenn nicht angegeben, wird eine neue generiert.

        Returns:
            Die gesetzte Korrelations-ID
        """
        if cid is None:
            cid = str(uuid.uuid4())
        correlation_id.set(cid)
        return cid

    def get_correlation_id(self) -> Optional[str]:
        """Gibt die aktuelle Korrelations-ID zurück."""
        return correlation_id.get()

    def log_structured(self, level: str, message: str, **kwargs: Any) -> None:
        """
        Loggt eine strukturierte Nachricht mit zusätzlichen Feldern.

        Args:
            level: Log-Level
            message: Nachrichtentext
            **kwargs: Zusätzliche strukturierte Daten
        """
        # Füge zusätzliche Felder zum Log-Record hinzu
        extra = {"structured_data": kwargs}
        log_method = getattr(self.logger, level.lower(), self.logger.info)
        log_method(message, extra=extra)

    def log_performance(
        self, operation: str, duration: float, details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Loggt Performance-Metriken im strukturierten Format."""
        self.log_structured(
            "INFO",
            f"PERFORMANCE: {operation} dauerte {duration:.2f}s",
            operation=operation,
            duration=duration,
            details=details,
            event_type="performance"
        )

    def log_download_progress(
        self, file_name: str, progress: float, speed: Optional[float] = None
    ) -> None:
        """Loggt Download-Fortschritt im strukturierten Format."""
        self.log_structured(
            "DEBUG",
            f"DOWNLOAD: {file_name} - {progress:.1f}%",
            file_name=file_name,
            progress=progress,
            speed=speed,
            event_type="download_progress"
        )

    def log_api_error(self, operation: str, error: Exception, retry_count: int = 0) -> None:
        """Loggt API-spezifische Fehler im strukturierten Format."""
        self.log_structured(
            "ERROR",
            f"API_ERROR: {operation} fehlgeschlagen",
            operation=operation,
            error_type=type(error).__name__,
            error_message=str(error),
            retry_count=retry_count,
            event_type="api_error"
        )

    def log_system_info(self) -> None:
        """Loggt System-Informationen beim Start im strukturierten Format."""
        import platform
        import psutil

        info = {
            "system": platform.system(),
            "version": platform.version(),
            "python_version": platform.python_version(),
            "cpu_cores": psutil.cpu_count(),
            "ram_gb": round(psutil.virtual_memory().total / (1024**3), 1),
            "free_space_gb": round(psutil.disk_usage('.').free / (1024**3), 1),
            "event_type": "system_info"
        }

        self.log_structured("INFO", "SYSTEM_INFO", **info)


# Globale Instanz des StructuredLoggers
_structured_logger: Optional[StructuredLogger] = None


def get_structured_logger(name: Optional[str] = None) -> StructuredLogger:
    """
    Gibt die globale Instanz des StructuredLoggers zurück.

    Args:
        name: Optionaler Name für den Logger

    Returns:
        Die StructuredLogger-Instanz
    """
    global _structured_logger
    if _structured_logger is None:
        _structured_logger = StructuredLogger(name or __name__)
    return _structured_logger


def setup_structured_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    json_log_file: Optional[str] = None,
    max_file_size: int = 10 * 1024 * 1024,
    backup_count: int = 5,
    enable_rich: bool = True,
) -> StructuredLogger:
    """
    Konfiguriert das strukturierte Logging-System.

    Args:
        level: Log-Level
        log_file: Pfad zur traditionellen Log-Datei
        json_log_file: Pfad zur JSON-Log-Datei
        max_file_size: Maximale Dateigröße für Rotation
        backup_count: Anzahl der Backup-Dateien
        enable_rich: Rich-Handler aktivieren

    Returns:
        Die konfigurierte StructuredLogger-Instanz
    """
    logger = get_structured_logger()
    logger.configure(
        level=level,
        log_file=log_file,
        json_log_file=json_log_file,
        max_file_size=max_file_size,
        backup_count=backup_count,
        enable_rich=enable_rich,
    )
    return logger