"""
Logging-Konfiguration für den Telegram Audio Downloader.
"""

import logging
import logging.handlers
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

from rich.console import Console
from rich.logging import RichHandler


class TelegramAudioLogger:
    """Erweiterte Logging-Klasse für das Telegram Audio Downloader Tool."""

    def __init__(self, name: str = "telegram_audio_downloader"):
        self.name: str = name
        self.logger: logging.Logger = logging.getLogger(name)
        self.console: Console = Console()
        self._configured: bool = False

    def configure(
        self,
        level: str = "INFO",
        log_file: Optional[str] = None,
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 3,
        enable_rich: bool = True,
    ) -> None:
        """
        Konfiguriert das Logging-System.

        Args:
            level: Log-Level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Pfad zur Log-Datei (optional)
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
        file_formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        console_formatter = logging.Formatter(fmt="%(levelname)s - %(message)s")

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
            console_handler.setFormatter(console_formatter)

        console_handler.setLevel(logging.INFO)
        self.logger.addHandler(console_handler)

        # File Handler (mit Rotation)
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.handlers.RotatingFileHandler(
                filename=log_file,
                maxBytes=max_file_size,
                backupCount=backup_count,
                encoding="utf-8",
            )
            file_handler.setFormatter(file_formatter)
            file_handler.setLevel(logging.DEBUG)
            self.logger.addHandler(file_handler)

        # Error Handler (separate Datei für Fehler)
        if log_file:
            error_log = log_path.parent / f"{log_path.stem}_errors{log_path.suffix}"
            error_handler = logging.handlers.RotatingFileHandler(
                filename=error_log,
                maxBytes=max_file_size,
                backupCount=backup_count,
                encoding="utf-8",
            )
            error_handler.setFormatter(file_formatter)
            error_handler.setLevel(logging.ERROR)
            self.logger.addHandler(error_handler)

        self._configured = True
        self.logger.info(f"Logging konfiguriert - Level: {level}, Datei: {log_file}")

    def get_logger(self) -> logging.Logger:
        """Gibt den konfigurierten Logger zurück."""
        if not self._configured:
            self.configure()
        return self.logger

    def log_performance(
        self, operation: str, duration: float, details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Loggt Performance-Metriken."""
        message = f"PERFORMANCE: {operation} dauerte {duration:.2f}s"
        if details:
            message += f" - Details: {details}"
        self.logger.info(message)

    def log_download_progress(
        self, file_name: str, progress: float, speed: Optional[float] = None
    ) -> None:
        """Loggt Download-Fortschritt."""
        message = f"DOWNLOAD: {file_name} - {progress:.1f}%"
        if speed:
            message += f" ({speed:.1f} KB/s)"
        self.logger.debug(message)

    def log_api_error(self, operation: str, error: Exception, retry_count: int = 0) -> None:
        """Loggt API-spezifische Fehler."""
        message = f"API_ERROR: {operation} fehlgeschlagen"
        if retry_count > 0:
            message += f" (Versuch {retry_count})"
        message += f" - {type(error).__name__}: {error}"
        self.logger.error(message, exc_info=True)

    def log_system_info(self) -> None:
        """Loggt System-Informationen beim Start."""
        import platform

        import psutil

        info = {
            "System": platform.system(),
            "Version": platform.version(),
            "Python": platform.python_version(),
            "CPU Cores": psutil.cpu_count(),
            "RAM": f"{psutil.virtual_memory().total / (1024**3):.1f} GB",
            "Free Space": f"{psutil.disk_usage('.').free / (1024**3):.1f} GB",
        }

        self.logger.info(
            "SYSTEM_INFO: " + " | ".join([f"{k}: {v}" for k, v in info.items()])
        )


class ErrorTracker:
    """Verfolgt und kategorisiert Fehler für bessere Diagnostik."""

    def __init__(self):
        self.errors: List[Dict[str, Any]] = []
        self.error_counts: Dict[str, int] = {}
        self.logger: logging.Logger = TelegramAudioLogger().get_logger()

    def track_error(self, error: Exception, context: str, severity: str = "ERROR") -> None:
        """Verfolgt einen Fehler mit Kontext."""
        error_info = {
            "timestamp": datetime.now(),
            "type": type(error).__name__,
            "message": str(error),
            "context": context,
            "severity": severity,
        }

        self.errors.append(error_info)

        # Fehler-Zählung
        error_key = f"{error_info['type']}:{context}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1

        # Loggen basierend auf Schweregrad
        log_method = getattr(self.logger, severity.lower(), self.logger.error)
        log_method(
            f"TRACKED_ERROR [{context}]: {error_info['type']} - {error_info['message']}"
        )

    def get_error_summary(self) -> Dict[str, Any]:
        """Gibt eine Zusammenfassung der Fehler zurück."""
        if not self.errors:
            return {"total": 0, "by_type": {}, "recent": []}

        by_type: Dict[str, int] = {}
        for error in self.errors:
            error_type = error["type"]
            by_type[error_type] = by_type.get(error_type, 0) + 1

        recent_errors = sorted(self.errors, key=lambda x: x["timestamp"], reverse=True)[
            :5
        ]

        return {
            "total": len(self.errors),
            "by_type": by_type,
            "most_common": sorted(
                self.error_counts.items(), key=lambda x: x[1], reverse=True
            )[:3],
            "recent": [
                {
                    "type": e["type"],
                    "context": e["context"],
                    "time": e["timestamp"].strftime("%H:%M:%S"),
                }
                for e in recent_errors
            ],
        }

    def should_retry(
        self, error: Exception, context: str, max_retries: int = 3
    ) -> bool:
        """Entscheidet, ob ein Fehler einen Retry-Versuch wert ist."""
        error_key = f"{type(error).__name__}:{context}"
        current_count = self.error_counts.get(error_key, 0)

        # Telegram-spezifische Retry-Logik
        from telethon.errors import FloodWaitError

        if isinstance(error, FloodWaitError):
            return True  # Immer retry bei FloodWait

        if isinstance(error, (ConnectionError, TimeoutError)):
            return current_count < max_retries

        if isinstance(error, (ConnectionError, TimeoutError)):
            return current_count < max_retries

        return False


# Globale Logger-Instanz
_global_logger: Optional[TelegramAudioLogger] = None
_error_tracker = ErrorTracker()


def get_logger(name: str = "telegram_audio_downloader") -> logging.Logger:
    """Gibt den globalen Logger zurück."""
    global _global_logger
    if _global_logger is None:
        _global_logger = TelegramAudioLogger(name)
        # Standard-Konfiguration laden
        config_path = Path("config/default.ini")
        if config_path.exists():
            import configparser

            config = configparser.ConfigParser()
            config.read(config_path)

            log_config = config["logging"] if "logging" in config else {}
            _global_logger.configure(
                level=log_config.get("level", "INFO"),
                log_file=log_config.get("file", "data/telegram_audio_downloader.log"),
                max_file_size=int(log_config.get("max_file_size_mb", 10)) * 1024 * 1024,
                backup_count=int(log_config.get("backup_count", 3)),
            )
        else:
            _global_logger.configure()

    return _global_logger.get_logger()


def get_error_tracker() -> ErrorTracker:
    """Gibt den globalen Error-Tracker zurück."""
    return _error_tracker


def setup_logging(debug: bool = False) -> logging.Logger:
    """Konfiguriert das Logging-System für die gesamte Anwendung."""
    level = "DEBUG" if debug else "INFO"
    logger_instance = TelegramAudioLogger()
    logger_instance.configure(
        level=level, log_file="data/telegram_audio_downloader.log", enable_rich=True
    )

    # System-Info beim Start loggen
    logger_instance.log_system_info()

    return logger_instance.get_logger()