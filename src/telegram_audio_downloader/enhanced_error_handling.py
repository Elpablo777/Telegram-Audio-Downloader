"""
Erweiterte Fehlerbehandlung für den Telegram Audio Downloader.
"""

import asyncio
import logging
import smtplib
import sys
import traceback
from abc import ABC, abstractmethod
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar
from contextvars import ContextVar

from rich.console import Console

from .structured_logging import get_structured_logger, StructuredLogger

# Rich-Konsole für formatierte Ausgabe
console = Console()

# Logger initialisieren
logger = get_structured_logger(__name__)

# Kontextvariable für Fehlerkontext
error_context: ContextVar[Dict[str, Any]] = ContextVar('error_context', default={})

# Typvariable für generische Funktionen
T = TypeVar('T')


class ErrorCategory:
    """Fehlerkategorien für detaillierte Fehlerhierarchie."""
    NETWORK = "network"
    FILESYSTEM = "filesystem"
    API = "api"
    VALIDATION = "validation"
    CONFIGURATION = "configuration"
    AUTHENTICATION = "authentication"
    DATABASE = "database"
    DOWNLOAD = "download"
    UNKNOWN = "unknown"


class BaseError(Exception):
    """Basisklasse für alle spezifischen Fehler des Telegram Audio Downloaders."""
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[str] = None,
        category: str = ErrorCategory.UNKNOWN,
        context: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None
    ):
        self.message = message
        self.error_code = error_code
        self.category = category
        self.context = context or {}
        self.correlation_id = correlation_id
        self.timestamp = datetime.now()
        super().__init__(self.message)


class NetworkError(BaseError):
    """Netzwerk-bezogene Fehler."""
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            category=ErrorCategory.NETWORK,
            context=context
        )


class FilesystemError(BaseError):
    """Dateisystem-bezogene Fehler."""
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            category=ErrorCategory.FILESYSTEM,
            context=context
        )


class APIError(BaseError):
    """API-bezogene Fehler."""
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            category=ErrorCategory.API,
            context=context
        )


class ValidationError(BaseError):
    """Validierungsfehler."""
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            category=ErrorCategory.VALIDATION,
            context=context
        )


class ConfigurationError(BaseError):
    """Fehler bei der Konfiguration des Downloaders."""
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            category=ErrorCategory.CONFIGURATION,
            context=context
        )


class AuthenticationError(BaseError):
    """Fehler bei der Authentifizierung mit der Telegram-API."""
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            category=ErrorCategory.AUTHENTICATION,
            context=context
        )


class DatabaseError(BaseError):
    """Fehler bei Datenbankoperationen."""
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            category=ErrorCategory.DATABASE,
            context=context
        )


class DownloadError(BaseError):
    """Fehler beim Herunterladen von Dateien."""
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            category=ErrorCategory.DOWNLOAD,
            context=context
        )


class NotificationHandler(ABC):
    """Abstrakte Basisklasse für Benachrichtigungshandler."""

    @abstractmethod
    async def send_notification(self, error: BaseError) -> bool:
        """
        Sendet eine Benachrichtigung über einen Fehler.

        Args:
            error: Der aufgetretene Fehler

        Returns:
            True, wenn die Benachrichtigung erfolgreich gesendet wurde, sonst False
        """
        pass


class EmailNotificationHandler(NotificationHandler):
    """E-Mail-Benachrichtigungshandler."""

    def __init__(
        self,
        smtp_server: str,
        smtp_port: int,
        username: str,
        password: str,
        recipients: List[str],
        sender: str
    ):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.recipients = recipients
        self.sender = sender

    async def send_notification(self, error: BaseError) -> bool:
        """Sendet eine E-Mail-Benachrichtigung über einen Fehler."""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.sender
            msg['To'] = ', '.join(self.recipients)
            msg['Subject'] = f"Telegram Audio Downloader Fehler: {error.category}"

            body = f"""
Ein Fehler ist im Telegram Audio Downloader aufgetreten:

Kategorie: {error.category}
Nachricht: {error.message}
Zeitstempel: {error.timestamp}
Fehlercode: {error.error_code}
Korrelations-ID: {error.correlation_id}

Kontext:
{error.context}

Stacktrace:
{traceback.format_exc()}
            """

            msg.attach(MIMEText(body, 'plain', 'utf-8'))

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)

            logger.log_structured(
                "INFO",
                "E-Mail-Benachrichtigung gesendet",
                category=error.category,
                recipients=self.recipients
            )
            return True
        except Exception as e:
            logger.log_structured(
                "ERROR",
                "Fehler beim Senden der E-Mail-Benachrichtigung",
                error=str(e)
            )
            return False


class ErrorHandler:
    """Erweiterte Klasse zur Fehlerbehandlung im Telegram Audio Downloader."""

    def __init__(self):
        self.logger = get_structured_logger(__name__)
        self.notification_handlers: List[NotificationHandler] = []
        self.auto_recovery_strategies: Dict[str, Callable] = {}

    def add_notification_handler(self, handler: NotificationHandler) -> None:
        """
        Fügt einen Benachrichtigungshandler hinzu.

        Args:
            handler: Der hinzuzufügende Benachrichtigungshandler
        """
        self.notification_handlers.append(handler)

    def add_auto_recovery_strategy(self, category: str, strategy: Callable) -> None:
        """
        Fügt eine automatische Wiederherstellungsstrategie hinzu.

        Args:
            category: Die Fehlerkategorie
            strategy: Die Wiederherstellungsstrategie
        """
        self.auto_recovery_strategies[category] = strategy

    def handle_error(self, error: BaseError, context: str = "", exit_on_error: bool = False) -> None:
        """
        Behandelt einen Fehler erweitert und gibt eine formatierte Meldung aus.

        Args:
            error: Der aufgetretene Fehler
            context: Kontext, in dem der Fehler aufgetreten ist
            exit_on_error: Ob das Programm bei diesem Fehler beendet werden soll
        """
        # Füge Kontextinformationen hinzu
        error_context_data = error_context.get()
        if context:
            error_context_data["user_action"] = context
        error.context.update(error_context_data)

        # Logge den Fehler strukturiert
        self._log_error(error)

        # Spezifische Fehlerbehandlung
        self._handle_specific_error(error)

        # Sende Benachrichtigungen
        asyncio.create_task(self._send_notifications(error))

        # Versuche automatische Wiederherstellung
        asyncio.create_task(self._attempt_auto_recovery(error))

        # Logge den vollständigen Stacktrace für Debugging-Zwecke
        self.logger.log_structured(
            "DEBUG",
            f"Vollständiger Stacktrace für {type(error).__name__}:",
            stacktrace=traceback.format_exc(),
            event_type="stacktrace"
        )

        # Programm beenden, wenn erforderlich
        if exit_on_error:
            sys.exit(1)

    def _log_error(self, error: BaseError) -> None:
        """Loggt einen Fehler strukturiert."""
        self.logger.log_structured(
            "ERROR",
            f"FEHLER [{error.category}]: {error.message}",
            category=error.category,
            error_code=error.error_code,
            context=error.context,
            correlation_id=error.correlation_id,
            timestamp=error.timestamp.isoformat(),
            event_type="error"
        )

    def _handle_specific_error(self, error: BaseError) -> None:
        """Behandelt spezifische Fehlerkategorien."""
        if isinstance(error, ConfigurationError):
            self._handle_configuration_error(error)
        elif isinstance(error, AuthenticationError):
            self._handle_authentication_error(error)
        elif isinstance(error, NetworkError):
            self._handle_network_error(error)
        elif isinstance(error, DownloadError):
            self._handle_download_error(error)
        elif isinstance(error, DatabaseError):
            self._handle_database_error(error)
        elif isinstance(error, FilesystemError):
            self._handle_filesystem_error(error)
        elif isinstance(error, APIError):
            self._handle_api_error(error)
        elif isinstance(error, ValidationError):
            self._handle_validation_error(error)
        else:
            # Allgemeine Fehlerbehandlung
            self._handle_generic_error(error)

    def _handle_configuration_error(self, error: ConfigurationError) -> None:
        """Behandelt Konfigurationsfehler."""
        console.print(f"[red]Konfigurationsfehler[/red] [{error.category}]: {error.message}")
        console.print("[yellow]Bitte überprüfen Sie Ihre Konfiguration[/yellow]")
        self.logger.log_structured(
            "ERROR",
            f"Konfigurationsfehler: {error.message}",
            category=error.category
        )

    def _handle_authentication_error(self, error: AuthenticationError) -> None:
        """Behandelt Authentifizierungsfehler."""
        console.print(f"[red]Authentifizierungsfehler[/red] [{error.category}]: {error.message}")
        console.print("[yellow]Bitte überprüfen Sie Ihre API-Zugangsdaten[/yellow]")
        self.logger.log_structured(
            "ERROR",
            f"Authentifizierungsfehler: {error.message}",
            category=error.category
        )

    def _handle_network_error(self, error: NetworkError) -> None:
        """Behandelt Netzwerkfehler."""
        console.print(f"[red]Netzwerkfehler[/red] [{error.category}]: {error.message}")
        console.print("[yellow]Bitte überprüfen Sie Ihre Internetverbindung[/yellow]")
        self.logger.log_structured(
            "ERROR",
            f"Netzwerkfehler: {error.message}",
            category=error.category
        )

    def _handle_download_error(self, error: DownloadError) -> None:
        """Behandelt Download-Fehler."""
        console.print(f"[red]Download-Fehler[/red] [{error.category}]: {error.message}")
        self.logger.log_structured(
            "ERROR",
            f"Download-Fehler: {error.message}",
            category=error.category
        )

    def _handle_database_error(self, error: DatabaseError) -> None:
        """Behandelt Datenbankfehler."""
        console.print(f"[red]Datenbankfehler[/red] [{error.category}]: {error.message}")
        self.logger.log_structured(
            "ERROR",
            f"Datenbankfehler: {error.message}",
            category=error.category
        )

    def _handle_filesystem_error(self, error: FilesystemError) -> None:
        """Behandelt Dateisystem-Fehler."""
        console.print(f"[red]Dateisystem-Fehler[/red] [{error.category}]: {error.message}")
        self.logger.log_structured(
            "ERROR",
            f"Dateisystem-Fehler: {error.message}",
            category=error.category
        )

    def _handle_api_error(self, error: APIError) -> None:
        """Behandelt API-Fehler."""
        console.print(f"[red]API-Fehler[/red] [{error.category}]: {error.message}")
        self.logger.log_structured(
            "ERROR",
            f"API-Fehler: {error.message}",
            category=error.category
        )

    def _handle_validation_error(self, error: ValidationError) -> None:
        """Behandelt Validierungsfehler."""
        console.print(f"[red]Validierungsfehler[/red] [{error.category}]: {error.message}")
        self.logger.log_structured(
            "ERROR",
            f"Validierungsfehler: {error.message}",
            category=error.category
        )

    def _handle_generic_error(self, error: BaseError) -> None:
        """Behandelt generische Fehler."""
        console.print(f"[red]{type(error).__name__}[/red] [{error.category}]: {error.message}")
        self.logger.log_structured(
            "ERROR",
            f"{type(error).__name__}: {error.message}",
            category=error.category
        )

    async def _send_notifications(self, error: BaseError) -> None:
        """Sendet Benachrichtigungen über einen Fehler."""
        for handler in self.notification_handlers:
            try:
                await handler.send_notification(error)
            except Exception as e:
                self.logger.log_structured(
                    "ERROR",
                    "Fehler beim Senden einer Benachrichtigung",
                    error=str(e),
                    handler_type=type(handler).__name__
                )

    async def _attempt_auto_recovery(self, error: BaseError) -> None:
        """Versucht eine automatische Wiederherstellung."""
        if error.category in self.auto_recovery_strategies:
            try:
                strategy = self.auto_recovery_strategies[error.category]
                await strategy(error)
                self.logger.log_structured(
                    "INFO",
                    "Automatische Wiederherstellung erfolgreich",
                    category=error.category
                )
            except Exception as e:
                self.logger.log_structured(
                    "ERROR",
                    "Fehler bei der automatischen Wiederherstellung",
                    error=str(e),
                    category=error.category
                )

    async def handle_async_error(self, error: BaseError, context: str = "", exit_on_error: bool = False) -> None:
        """
        Behandelt einen Fehler asynchron.

        Args:
            error: Der aufgetretene Fehler
            context: Kontext, in dem der Fehler aufgetreten ist
            exit_on_error: Ob das Programm bei diesem Fehler beendet werden soll
        """
        self.handle_error(error, context, exit_on_error)

    def wrap_async_function(self, func: Callable[..., T]) -> Callable[..., T]:
        """
        Dekorator zum Einhüllen asynchroner Funktionen mit Fehlerbehandlung.

        Args:
            func: Die zu wrappende Funktion

        Returns:
            Die gewrappte Funktion mit Fehlerbehandlung
        """
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return await func(*args, **kwargs)
            except BaseError:
                raise
            except Exception as e:
                # Konvertiere allgemeine Exceptions in spezifische Fehler
                error = self._convert_exception(e, func.__name__)
                self.handle_error(error)
                raise error

        return wrapper

    def wrap_sync_function(self, func: Callable[..., T]) -> Callable[..., T]:
        """
        Dekorator zum Einhüllen synchroner Funktionen mit Fehlerbehandlung.

        Args:
            func: Die zu wrappende Funktion

        Returns:
            Die gewrappte Funktion mit Fehlerbehandlung
        """
        def wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return func(*args, **kwargs)
            except BaseError:
                raise
            except Exception as e:
                # Konvertiere allgemeine Exceptions in spezifische Fehler
                error = self._convert_exception(e, func.__name__)
                self.handle_error(error)
                raise error

        return wrapper

    def _convert_exception(self, exception: Exception, context: str) -> BaseError:
        """
        Konvertiert eine allgemeine Exception in einen spezifischen Fehler.

        Args:
            exception: Die zu konvertierende Exception
            context: Der Kontext der Exception

        Returns:
            Der konvertierte spezifische Fehler
        """
        # Mapping von Exception-Typen zu spezifischen Fehlern
        exception_mapping = {
            FileNotFoundError: FilesystemError,
            PermissionError: FilesystemError,
            ConnectionError: NetworkError,
            TimeoutError: NetworkError,
            ValueError: ValidationError,
            KeyError: ValidationError,
        }

        error_class = exception_mapping.get(type(exception), BaseError)
        return error_class(
            message=str(exception),
            context={"original_exception": type(exception).__name__}
        )

    def set_error_context(self, **kwargs: Any) -> None:
        """
        Setzt Kontextinformationen für Fehler.

        Args:
            **kwargs: Kontextinformationen
        """
        ctx = error_context.get()
        ctx.update(kwargs)
        error_context.set(ctx)

    def get_error_context(self) -> Dict[str, Any]:
        """Gibt die aktuellen Fehlerkontextinformationen zurück."""
        return error_context.get()


# Globale Instanz des ErrorHandlers
_error_handler: Optional[ErrorHandler] = None


def get_error_handler() -> ErrorHandler:
    """
    Gibt die globale Instanz des ErrorHandlers zurück.

    Returns:
        Die ErrorHandler-Instanz
    """
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler


def handle_error(error: BaseError, context: str = "", exit_on_error: bool = False) -> None:
    """
    Behandelt einen Fehler global.

    Args:
        error: Der aufgetretene Fehler
        context: Kontext, in dem der Fehler aufgetreten ist
        exit_on_error: Ob das Programm bei diesem Fehler beendet werden soll
    """
    handler = get_error_handler()
    handler.handle_error(error, context, exit_on_error)