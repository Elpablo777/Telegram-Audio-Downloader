"""
Logger-Modul für den Telegram Audio Downloader.
Bietet eine zentrale Schnittstelle für das Logging-System.
"""

import functools
import logging
from typing import Optional

from .logging_config import TelegramAudioLogger
from .structured_logging import StructuredLogger

# Globale Logger-Instanz
_logger_instance: Optional[TelegramAudioLogger] = None
_structured_logger_instance: Optional[StructuredLogger] = None


def get_logger(debug: bool = False) -> logging.Logger:
    """
    Gibt eine konfigurierte Logger-Instanz zurück.
    
    Args:
        debug: Wenn True, wird der Debug-Modus aktiviert
        
    Returns:
        Konfigurierter Logger
    """
    global _logger_instance
    
    if _logger_instance is None:
        _logger_instance = TelegramAudioLogger()
        level = "DEBUG" if debug else "INFO"
        _logger_instance.configure(level=level)
    
    return _logger_instance.get_logger()


def get_structured_logger() -> logging.Logger:
    """
    Gibt eine strukturierte Logger-Instanz zurück.
    
    Returns:
        Strukturierter Logger
    """
    global _structured_logger_instance
    
    if _structured_logger_instance is None:
        _structured_logger_instance = StructuredLogger()
        _structured_logger_instance.configure()
    
    return _structured_logger_instance.get_logger()


def log_function_call(func):
    """
    Dekorator zum Protokollieren von Funktionsaufrufen.
    
    Args:
        func: Zu protokollierende Funktion
        
    Returns:
        Dekorierte Funktion
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger()
        logger.debug(f"Aufruf von Funktion: {func.__name__}")
        
        try:
            result = func(*args, **kwargs)
            logger.debug(f"Funktion {func.__name__} erfolgreich abgeschlossen")
            return result
        except Exception as e:
            logger.error(f"Fehler in Funktion {func.__name__}: {e}")
            raise
            
    return wrapper