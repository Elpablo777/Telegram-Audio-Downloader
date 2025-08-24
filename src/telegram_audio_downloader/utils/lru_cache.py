"""
LRU-Cache-Implementierung für den Telegram Audio Downloader.
"""

from collections import OrderedDict
from typing import Any, Callable, Optional, TypeVar, Generic, Union
from threading import RLock
import time

T = TypeVar('T')
K = TypeVar('K')
V = TypeVar('V')

class LRUCache(Generic[K, V]):
    """
    Least Recently Used (LRU) Cache Implementierung.
    """

    def __init__(self, maxsize: int = 128, ttl: Optional[float] = None):
        """
        Initialisiert den LRU-Cache.

        Args:
            maxsize: Maximale Anzahl von Einträgen im Cache
            ttl: Zeit bis zum Ablauf eines Eintrags in Sekunden (optional)
        """
        if maxsize <= 0:
            raise ValueError("maxsize muss größer als 0 sein")
        
        self.maxsize = maxsize
        self.ttl = ttl
        self.cache: OrderedDict[K, tuple[V, float]] = OrderedDict()
        self.lock = RLock()

    def get(self, key: K, default: Optional[V] = None) -> Union[V, None]:
        """
        Gibt den Wert für einen Schlüssel zurück und markiert ihn als zuletzt verwendet.

        Args:
            key: Der Schlüssel
            default: Standardwert, falls der Schlüssel nicht gefunden wird

        Returns:
            Der Wert oder der Standardwert
        """
        with self.lock:
            if key in self.cache:
                value, timestamp = self.cache[key]
                
                # Prüfe TTL
                if self.ttl is not None and time.time() - timestamp > self.ttl:
                    del self.cache[key]
                    return default
                
                # Markiere als zuletzt verwendet
                self.cache.move_to_end(key)
                return value
            return default

    def put(self, key: K, value: V) -> None:
        """
        Fügt einen Wert zum Cache hinzu.

        Args:
            key: Der Schlüssel
            value: Der Wert
        """
        with self.lock:
            if key in self.cache:
                # Aktualisiere den Wert und markiere als zuletzt verwendet
                self.cache[key] = (value, time.time())
                self.cache.move_to_end(key)
            else:
                # Prüfe ob der Cache voll ist
                if len(self.cache) >= self.maxsize:
                    # Entferne den am längsten nicht verwendeten Eintrag
                    self.cache.popitem(last=False)
                
                # Füge den neuen Eintrag hinzu
                self.cache[key] = (value, time.time())

    def delete(self, key: K) -> bool:
        """
        Entfernt einen Eintrag aus dem Cache.

        Args:
            key: Der Schlüssel

        Returns:
            True, wenn der Eintrag entfernt wurde, False sonst
        """
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False

    def clear(self) -> None:
        """Leert den gesamten Cache."""
        with self.lock:
            self.cache.clear()

    def size(self) -> int:
        """
        Gibt die aktuelle Anzahl von Einträgen im Cache zurück.

        Returns:
            Anzahl der Einträge
        """
        with self.lock:
            # Bereinige abgelaufene Einträge
            if self.ttl is not None:
                current_time = time.time()
                expired_keys = [
                    key for key, (_, timestamp) in self.cache.items()
                    if current_time - timestamp > self.ttl
                ]
                for key in expired_keys:
                    del self.cache[key]
            
            return len(self.cache)

    def contains(self, key: K) -> bool:
        """
        Prüft, ob ein Schlüssel im Cache enthalten ist.

        Args:
            key: Der Schlüssel

        Returns:
            True, wenn der Schlüssel enthalten ist, False sonst
        """
        return self.get(key, None) is not None

    def keys(self):
        """
        Gibt alle Schlüssel im Cache zurück.

        Returns:
            Liste der Schlüssel
        """
        with self.lock:
            return list(self.cache.keys())

    def values(self):
        """
        Gibt alle Werte im Cache zurück.

        Returns:
            Liste der Werte
        """
        with self.lock:
            return [value for value, _ in self.cache.values()]

    def items(self):
        """
        Gibt alle Schlüssel-Wert-Paare im Cache zurück.

        Returns:
            Liste der Schlüssel-Wert-Paare
        """
        with self.lock:
            return [(key, value) for key, (value, _) in self.cache.items()]


# Globale Instanzen für verschiedene Cache-Typen
_filename_cache: Optional[LRUCache[str, str]] = None
_metadata_cache: Optional[LRUCache[str, dict]] = None
_download_cache: Optional[LRUCache[str, str]] = None


def get_filename_cache() -> LRUCache[str, str]:
    """
    Gibt den globalen Dateinamen-Cache zurück.

    Returns:
        LRUCache-Instanz für Dateinamen
    """
    global _filename_cache
    if _filename_cache is None:
        _filename_cache = LRUCache(maxsize=1000, ttl=3600)  # 1 Stunde TTL
    return _filename_cache


def get_metadata_cache() -> LRUCache[str, dict]:
    """
    Gibt den globalen Metadaten-Cache zurück.

    Returns:
        LRUCache-Instanz für Metadaten
    """
    global _metadata_cache
    if _metadata_cache is None:
        _metadata_cache = LRUCache(maxsize=500, ttl=1800)  # 30 Minuten TTL
    return _metadata_cache


def get_download_cache() -> LRUCache[str, str]:
    """
    Gibt den globalen Download-Cache zurück.

    Returns:
        LRUCache-Instanz für Downloads
    """
    global _download_cache
    if _download_cache is None:
        _download_cache = LRUCache(maxsize=200, ttl=7200)  # 2 Stunden TTL
    return _download_cache


def cached_function(maxsize: int = 128, ttl: Optional[float] = None):
    """
    Dekorator für das Cachen von Funktionsaufrufen.

    Args:
        maxsize: Maximale Anzahl von Einträgen im Cache
        ttl: Zeit bis zum Ablauf eines Eintrags in Sekunden (optional)

    Returns:
        Dekorator-Funktion
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        cache = LRUCache[str, T](maxsize=maxsize, ttl=ttl)
        
        def wrapper(*args, **kwargs) -> T:
            # Erstelle einen Schlüssel aus den Argumenten
            key = str(args) + str(sorted(kwargs.items()))
            
            # Prüfe ob der Wert im Cache ist
            result = cache.get(key)
            if result is not None:
                return result
            
            # Berechne den Wert und speichere ihn im Cache
            result = func(*args, **kwargs)
            cache.put(key, result)
            return result
        
        return wrapper
    return decorator