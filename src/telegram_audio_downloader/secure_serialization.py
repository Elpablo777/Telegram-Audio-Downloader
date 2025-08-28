"""
Sichere Serialisierung für den Telegram Audio Downloader.

Bietet sichere Alternativen zu pickle für die Serialisierung von Daten,
insbesondere für das Caching-System.
"""

import json
import base64
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union
from dataclasses import asdict, is_dataclass

from .error_handling import SecurityError, handle_error
from .logging_config import get_logger

logger = get_logger(__name__)


class SecureSerializationError(SecurityError):
    """Fehler bei der sicheren Serialisierung."""
    pass


def secure_dumps(obj: Any) -> bytes:
    """
    Serialisiert ein Objekt sicher zu Bytes.
    
    Args:
        obj: Zu serialisierendes Objekt
        
    Returns:
        Serialisierte Daten als Bytes
        
    Raises:
        SecureSerializationError: Bei Serialisierungsfehlern
    """
    try:
        # Konvertiere das Objekt in ein JSON-serialisierbares Format
        json_obj = _convert_to_json_serializable(obj)
        
        # Serialisiere zu JSON und kodiere als Base64
        json_str = json.dumps(json_obj, ensure_ascii=False, separators=(',', ':'))
        return base64.b64encode(json_str.encode('utf-8'))
    except Exception as e:
        logger.error(f"Fehler bei der sicheren Serialisierung: {e}")
        raise SecureSerializationError(f"Serialisierung fehlgeschlagen: {e}") from e


def secure_loads(data: bytes) -> Any:
    """
    Deserialisiert Daten sicher aus Bytes.
    
    Args:
        data: Zu deserialisierende Daten als Bytes
        
    Returns:
        Deserialisiertes Objekt
        
    Raises:
        SecureSerializationError: Bei Deserialisierungsfehlern
    """
    try:
        # Dekodiere von Base64 und deserialisiere von JSON
        json_str = base64.b64decode(data).decode('utf-8')
        json_obj = json.loads(json_str)
        
        # Konvertiere zurück zum ursprünglichen Objektformat
        return _convert_from_json_serializable(json_obj)
    except Exception as e:
        logger.error(f"Fehler bei der sicheren Deserialisierung: {e}")
        raise SecureSerializationError(f"Deserialisierung fehlgeschlagen: {e}") from e


def _convert_to_json_serializable(obj: Any) -> Any:
    """
    Konvertiert ein Objekt in ein JSON-serialisierbares Format.
    
    Args:
        obj: Zu konvertierendes Objekt
        
    Returns:
        JSON-serialisierbares Objekt
    """
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    elif isinstance(obj, (list, tuple)):
        return [_convert_to_json_serializable(item) for item in obj]
    elif isinstance(obj, dict):
        return {str(key): _convert_to_json_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, (datetime, timedelta)):
        # Spezielle Behandlung für Datums- und Zeitobjekte
        return {
            "__type__": "datetime" if isinstance(obj, datetime) else "timedelta",
            "__value__": obj.isoformat() if isinstance(obj, datetime) else str(obj.total_seconds())
        }
    elif is_dataclass(obj):
        # Behandlung für dataclass-Objekte
        return {
            "__type__": "dataclass",
            "__class__": f"{obj.__class__.__module__}.{obj.__class__.__name__}",
            "__value__": _convert_to_json_serializable(asdict(obj))
        }
    elif hasattr(obj, '__dict__'):
        # Allgemeine Objekte mit __dict__
        return {
            "__type__": "object",
            "__class__": f"{obj.__class__.__module__}.{obj.__class__.__name__}",
            "__value__": _convert_to_json_serializable(obj.__dict__)
        }
    else:
        # Für alle anderen Typen verwenden wir die String-Repräsentation
        return {
            "__type__": "other",
            "__class__": f"{obj.__class__.__module__}.{obj.__class__.__name__}",
            "__value__": str(obj)
        }


def _convert_from_json_serializable(obj: Any) -> Any:
    """
    Konvertiert ein JSON-serialisierbares Objekt zurück zum ursprünglichen Format.
    
    Args:
        obj: JSON-serialisierbares Objekt
        
    Returns:
        Ursprüngliches Objektformat
    """
    if not isinstance(obj, dict):
        return obj
    elif "__type__" in obj:
        obj_type = obj["__type__"]
        obj_value = obj["__value__"]
        
        if obj_type == "datetime":
            return datetime.fromisoformat(obj_value)
        elif obj_type == "timedelta":
            return timedelta(seconds=float(obj_value))
        elif obj_type == "dataclass":
            # Für dataclass-Objekte würden wir hier die Rekonstruktion implementieren
            # Da wir die konkreten Klassen nicht kennen, geben wir das dict zurück
            return _convert_from_json_serializable(obj_value)
        elif obj_type == "object":
            # Für allgemeine Objekte geben wir das dict zurück
            return _convert_from_json_serializable(obj_value)
        elif obj_type == "other":
            # Für andere Typen geben wir den String-Wert zurück
            return obj_value
        else:
            return _convert_from_json_serializable(obj_value)
    else:
        return {key: _convert_from_json_serializable(value) for key, value in obj.items()}