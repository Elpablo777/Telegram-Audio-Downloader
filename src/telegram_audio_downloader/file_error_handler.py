"""
Dateisystem-Fehlerbehandlung für den Telegram Audio Downloader.
"""

import errno
import logging
import os
from pathlib import Path
from typing import Union

from .enhanced_error_handling import FilesystemError, handle_error
from .logging_config import get_logger

logger = get_logger(__name__)


def handle_file_error(error: Exception, context: str = "", filepath: Union[str, Path] = "") -> None:
    """
    Behandelt Dateisystemfehler zentral.
    
    Args:
        error: Der aufgetretene Dateisystemfehler
        context: Kontext, in dem der Fehler aufgetreten ist
        filepath: Pfad zur Datei, bei der der Fehler aufgetreten ist
    """
    # Spezifische OSError-Fehler in unsere eigenen Fehlerklassen übersetzen
    if isinstance(error, OSError):
        if error.errno == errno.EACCES:
            file_error = FilesystemError(
                f"Zugriff verweigert: {filepath if filepath else 'Datei'} - {str(error)}",
                context={"error_code": "FILE_ACCESS_DENIED"}
            )
        elif error.errno == errno.ENOENT:
            file_error = FilesystemError(
                f"Datei nicht gefunden: {filepath if filepath else 'Datei'} - {str(error)}",
                context={"error_code": "FILE_NOT_FOUND"}
            )
        elif error.errno == errno.EEXIST:
            file_error = FilesystemError(
                f"Datei existiert bereits: {filepath if filepath else 'Datei'} - {str(error)}",
                context={"error_code": "FILE_ALREADY_EXISTS"}
            )
        elif error.errno == errno.ENOSPC:
            file_error = FilesystemError(
                f"Kein Speicherplatz verfügbar: {str(error)}",
                context={"error_code": "FILE_NO_SPACE"}
            )
        elif error.errno == errno.EROFS:
            file_error = FilesystemError(
                f"Schreibvorgang auf schreibgeschütztem Dateisystem: {str(error)}",
                context={"error_code": "FILE_READ_ONLY"}
            )
        else:
            file_error = FilesystemError(
                f"Dateioperation fehlgeschlagen: {str(error)}",
                context={"error_code": "FILE_GENERAL_ERROR"}
            )
    else:
        file_error = FilesystemError(
            f"Unerwarteter Dateifehler: {str(error)}",
            context={"error_code": "FILE_UNEXPECTED_ERROR"}
        )
    
    # Fehler behandeln
    handle_error(file_error, context)
    
    
def with_file_error_handling(filepath: Union[str, Path] = ""):
    """
    Dekorator zum Einhüllen von Funktionen mit Dateifehlerbehandlung.
    
    Args:
        filepath: Optionaler Pfad zur Datei, bei der der Fehler aufgetreten ist
        
    Returns:
        Der Dekorator
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except (OSError, FilesystemError) as e:
                # Kontext aus dem Funktionsnamen ableiten
                context = f"file_{func.__name__}"
                handle_file_error(e, context, filepath)
                raise
            except Exception as e:
                # Unerwartete Fehler ebenfalls als Dateifehler behandeln
                context = f"file_{func.__name__}_unexpected"
                file_error = FilesystemError(
                    f"Unerwarteter Fehler in Dateioperation: {str(e)}",
                    context={"error_code": "FILE_UNEXPECTED_ERROR"}
                )
                handle_error(file_error, context)
                raise
                
        return wrapper
    return decorator