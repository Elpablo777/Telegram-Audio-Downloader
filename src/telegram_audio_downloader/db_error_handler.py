"""
Datenbank-Fehlerbehandlung für den Telegram Audio Downloader.
"""

import logging
from typing import Optional

from peewee import DatabaseError as PeeweeDatabaseError
from peewee import OperationalError, IntegrityError

from .enhanced_error_handling import DatabaseError, handle_error
from .logging_config import get_logger

logger = get_logger(__name__)


def handle_database_error(error: Exception, context: str = "") -> None:
    """
    Behandelt Datenbankfehler zentral.
    
    Args:
        error: Der aufgetretene Datenbankfehler
        context: Kontext, in dem der Fehler aufgetreten ist
    """
    # Spezifische Peewee-Fehler in unsere eigenen Fehlerklassen übersetzen
    if isinstance(error, IntegrityError):
        db_error = DatabaseError(
            f"Datenbank-Integritätsfehler: {str(error)}",
            context={"error_code": "DB_INTEGRITY_ERROR"}
        )
    elif isinstance(error, OperationalError):
        db_error = DatabaseError(
            f"Datenbank-Betriebsfehler: {str(error)}",
            context={"error_code": "DB_OPERATIONAL_ERROR"}
        )
    elif isinstance(error, PeeweeDatabaseError):
        db_error = DatabaseError(
            f"Allgemeiner Datenbankfehler: {str(error)}",
            context={"error_code": "DB_GENERAL_ERROR"}
        )
    else:
        db_error = DatabaseError(
            f"Unerwarteter Datenbankfehler: {str(error)}",
            context={"error_code": "DB_UNEXPECTED_ERROR"}
        )
    
    # Fehler behandeln
    handle_error(db_error, context)
    
    
def with_database_error_handling(func):
    """
    Dekorator zum Einhüllen von Funktionen mit Datenbankfehlerbehandlung.
    
    Args:
        func: Die zu wrappende Funktion
        
    Returns:
        Die gewrappte Funktion mit Datenbankfehlerbehandlung
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (PeeweeDatabaseError, DatabaseError) as e:
            # Kontext aus dem Funktionsnamen ableiten
            context = f"db_{func.__name__}"
            handle_database_error(e, context)
            raise
        except Exception as e:
            # Unerwartete Fehler ebenfalls als Datenbankfehler behandeln
            context = f"db_{func.__name__}_unexpected"
            db_error = DatabaseError(
                f"Unerwarteter Fehler in Datenbankoperation: {str(e)}",
                context={"error_code": "DB_UNEXPECTED_ERROR"}
            )
            handle_error(db_error, context)
            raise
            
    return wrapper