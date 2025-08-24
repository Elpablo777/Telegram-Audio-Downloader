"""
Zentrale Fehlerbehandlung für den Telegram Audio Downloader.
"""

import asyncio
import logging
import sys
import traceback
from typing import Any, Callable, Optional, Type, TypeVar

from rich.console import Console

from .logging_config import get_logger

# Rich-Konsole für formatierte Ausgabe
console = Console()

# Logger initialisieren
logger = get_logger(__name__)

# Typvariable für generische Funktionen
T = TypeVar('T')

class TelegramAudioError(Exception):
    """Basisklasse für alle spezifischen Fehler des Telegram Audio Downloaders."""
    def __init__(self, message: str, error_code: Optional[str] = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

class ConfigurationError(TelegramAudioError):
    """Fehler bei der Konfiguration des Downloaders."""
    pass

class AuthenticationError(TelegramAudioError):
    """Fehler bei der Authentifizierung mit der Telegram-API."""
    pass

class NetworkError(TelegramAudioError):
    """Netzwerk-bezogene Fehler."""
    pass

class DownloadError(TelegramAudioError):
    """Fehler beim Herunterladen von Dateien."""
    pass

class DatabaseError(TelegramAudioError):
    """Fehler bei Datenbankoperationen."""
    pass

class FileOperationError(TelegramAudioError):
    """Fehler bei Dateioperationen."""
    pass

class SecurityError(TelegramAudioError):
    """Sicherheits-bezogene Fehler."""
    pass

class TelegramAPIError(TelegramAudioError):
    """Fehler bei der Interaktion mit der Telegram-API."""
    def __init__(self, message: str, telegram_error: Optional[Exception] = None):
        super().__init__(message)
        self.telegram_error = telegram_error

class ErrorHandler:
    """Zentrale Klasse zur Fehlerbehandlung im Telegram Audio Downloader."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        
    def handle_error(self, error: Exception, context: str = "", exit_on_error: bool = False) -> None:
        """
        Behandelt einen Fehler zentral und gibt eine formatierte Meldung aus.
        
        Args:
            error: Der aufgetretene Fehler
            context: Kontext, in dem der Fehler aufgetreten ist
            exit_on_error: Ob das Programm bei diesem Fehler beendet werden soll
        """
        error_type = type(error).__name__
        
        # Spezifische Fehlerbehandlung
        if isinstance(error, ConfigurationError):
            self._handle_configuration_error(error, context)
        elif isinstance(error, AuthenticationError):
            self._handle_authentication_error(error, context)
        elif isinstance(error, NetworkError):
            self._handle_network_error(error, context)
        elif isinstance(error, DownloadError):
            self._handle_download_error(error, context)
        elif isinstance(error, DatabaseError):
            self._handle_database_error(error, context)
        elif isinstance(error, FileOperationError):
            self._handle_file_operation_error(error, context)
        elif isinstance(error, SecurityError):
            self._handle_security_error(error, context)
        elif isinstance(error, TelegramAPIError):
            self._handle_telegram_api_error(error, context)
        else:
            # Allgemeine Fehlerbehandlung
            self._handle_generic_error(error, context)
            
        # Logge den vollständigen Stacktrace für Debugging-Zwecke
        self.logger.debug(f"Vollständiger Stacktrace für {error_type}:", exc_info=True)
        
        # Programm beenden, wenn erforderlich
        if exit_on_error:
            sys.exit(1)
            
    def _handle_configuration_error(self, error: ConfigurationError, context: str) -> None:
        """Behandelt Konfigurationsfehler."""
        console.print(f"[red]Konfigurationsfehler[/red] in {context}: {error.message}")
        self.logger.error(f"Konfigurationsfehler in {context}: {error.message}")
        
    def _handle_authentication_error(self, error: AuthenticationError, context: str) -> None:
        """Behandelt Authentifizierungsfehler."""
        console.print(f"[red]Authentifizierungsfehler[/red] in {context}: {error.message}")
        console.print("[yellow]Bitte überprüfen Sie Ihre API-Zugangsdaten in der .env-Datei[/yellow]")
        self.logger.error(f"Authentifizierungsfehler in {context}: {error.message}")
        
    def _handle_network_error(self, error: NetworkError, context: str) -> None:
        """Behandelt Netzwerkfehler."""
        console.print(f"[red]Netzwerkfehler[/red] in {context}: {error.message}")
        console.print("[yellow]Bitte überprüfen Sie Ihre Internetverbindung[/yellow]")
        self.logger.error(f"Netzwerkfehler in {context}: {error.message}")
        
    def _handle_download_error(self, error: DownloadError, context: str) -> None:
        """Behandelt Download-Fehler."""
        console.print(f"[red]Download-Fehler[/red] in {context}: {error.message}")
        self.logger.error(f"Download-Fehler in {context}: {error.message}")
        
    def _handle_database_error(self, error: DatabaseError, context: str) -> None:
        """Behandelt Datenbankfehler."""
        console.print(f"[red]Datenbankfehler[/red] in {context}: {error.message}")
        self.logger.error(f"Datenbankfehler in {context}: {error.message}")
        
    def _handle_file_operation_error(self, error: FileOperationError, context: str) -> None:
        """Behandelt Dateioperations-Fehler."""
        console.print(f"[red]Dateioperations-Fehler[/red] in {context}: {error.message}")
        self.logger.error(f"Dateioperations-Fehler in {context}: {error.message}")
        
    def _handle_security_error(self, error: SecurityError, context: str) -> None:
        """Behandelt Sicherheitsfehler."""
        console.print(f"[red]Sicherheitsfehler[/red] in {context}: {error.message}")
        self.logger.error(f"Sicherheitsfehler in {context}: {error.message}")
        
    def _handle_telegram_api_error(self, error: TelegramAPIError, context: str) -> None:
        """Behandelt Telegram-API-Fehler."""
        console.print(f"[red]Telegram-API-Fehler[/red] in {context}: {error.message}")
        if error.telegram_error:
            self.logger.error(f"Telegram-API-Fehler in {context}: {error.message} (Ursache: {error.telegram_error})")
        else:
            self.logger.error(f"Telegram-API-Fehler in {context}: {error.message}")
        
    def _handle_generic_error(self, error: Exception, context: str) -> None:
        """Behandelt generische Fehler."""
        error_type = type(error).__name__
        console.print(f"[red]{error_type}[/red] in {context}: {str(error)}")
        self.logger.error(f"{error_type} in {context}: {str(error)}")
        
    async def handle_async_error(self, error: Exception, context: str = "", exit_on_error: bool = False) -> None:
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
            except Exception as e:
                self.handle_error(e, func.__name__)
                raise
                
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
            except Exception as e:
                self.handle_error(e, func.__name__)
                raise
                
        return wrapper

# Globale Instanz des ErrorHandlers
_error_handler: Optional[ErrorHandler] = None

def get_error_handler() -> ErrorHandler:
    """
    Gibt die globale Instanz des ErrorHandlers zurück.
    
    Returns:
        ErrorHandler: Globale Instanz des ErrorHandlers
    """
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler

def handle_error(error: Exception, context: str = "", exit_on_error: bool = False) -> None:
    """
    Behandelt einen Fehler zentral und gibt eine formatierte Meldung aus.
    
    Args:
        error: Der aufgetretene Fehler
        context: Kontext, in dem der Fehler aufgetreten ist
        exit_on_error: Ob das Programm bei diesem Fehler beendet werden soll
    """
    error_handler = get_error_handler()
    error_handler.handle_error(error, context, exit_on_error)
