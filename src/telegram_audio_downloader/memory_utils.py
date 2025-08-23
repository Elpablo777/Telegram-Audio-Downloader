"""
Speichereffiziente Hilfsfunktionen für den Telegram Audio Downloader.
"""

import gc
import weakref
from collections import deque
from typing import Any, Generator, Iterator, Optional, Set, Dict, Tuple
from pathlib import Path

import psutil

from .logging_config import get_logger

logger = get_logger(__name__)


class MemoryEfficientSet:
    """
    Speichereffiziente Set-Implementierung mit Größenbegrenzung und automatischer Bereinigung.
    Verwendet eine Kombination aus In-Memory-Set und Weak-References für große Datenmengen.
    """
    
    def __init__(self, max_size: int = 50000):
        self.max_size = max_size
        self._primary_set: Set[str] = set()
        self._overflow_cache = weakref.WeakValueDictionary()
        self._access_order = deque(maxlen=max_size // 10)  # Für LRU-ähnliches Verhalten
        
    def add(self, item: str) -> None:
        """Fügt ein Element zum Set hinzu."""
        if len(self._primary_set) < self.max_size:
            self._primary_set.add(item)
            self._access_order.append(item)
        else:
            # Wenn das primäre Set voll ist, in Weak-Reference-Cache verschieben
            if self._access_order:
                # Ältestes Element entfernen
                oldest = self._access_order.popleft()
                if oldest in self._primary_set:
                    self._primary_set.remove(oldest)
                    # In Weak-Reference-Cache verschieben
                    self._overflow_cache[oldest] = True
            
            # Neues Element hinzufügen
            self._primary_set.add(item)
            self._access_order.append(item)
    
    def __contains__(self, item: str) -> bool:
        """Prüft, ob ein Element im Set enthalten ist."""
        return item in self._primary_set or item in self._overflow_cache
    
    def __len__(self) -> int:
        """Gibt die Anzahl der Elemente im Set zurück."""
        return len(self._primary_set) + len(self._overflow_cache)
    
    def clear(self) -> None:
        """Leert das Set."""
        self._primary_set.clear()
        self._overflow_cache.clear()
        self._access_order.clear()


class StreamingDataProcessor:
    """
    Verarbeitet große Datenmengen stream-basiert, um Speicher zu schonen.
    """
    
    def __init__(self, chunk_size: int = 1000):
        self.chunk_size = chunk_size
    
    def process_in_chunks(self, data_source: Iterator[Any]) -> Generator[list, None, None]:
        """
        Verarbeitet Daten in Chunks, um Speicher zu schonen.
        
        Args:
            data_source: Iterator über die zu verarbeitenden Daten
            
        Yields:
            Liste von Datenobjekten mit maximal chunk_size Elementen
        """
        chunk = []
        for item in data_source:
            chunk.append(item)
            if len(chunk) >= self.chunk_size:
                yield chunk
                chunk = []
        
        # Letzten Chunk ausgeben, falls nicht leer
        if chunk:
            yield chunk
    
    def process_file_lines(self, file_path: Path) -> Generator[str, None, None]:
        """
        Liest eine Datei zeilenweise, um Speicher zu schonen.
        
        Args:
            file_path: Pfad zur Datei
            
        Yields:
            Einzelne Zeilen der Datei
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    yield line.rstrip('\n')
        except Exception as e:
            logger.error(f"Fehler beim Lesen der Datei {file_path}: {e}")
            raise


class MemoryMonitor:
    """
    Überwacht den Speicherverbrauch und führt automatische Bereinigung durch.
    """
    
    def __init__(self, warning_threshold_mb: float = 800, critical_threshold_mb: float = 1000):
        self.warning_threshold_mb = warning_threshold_mb
        self.critical_threshold_mb = critical_threshold_mb
        self._cleanup_callbacks = []
    
    def get_memory_usage(self) -> Dict[str, float]:
        """
        Gibt detaillierte Speicherinformationen zurück.
        
        Returns:
            Dictionary mit Speicherinformationen
        """
        process = psutil.Process()
        memory_info = process.memory_info()
        system_memory = psutil.virtual_memory()
        
        return {
            "process_rss_mb": memory_info.rss / (1024 * 1024),
            "process_vms_mb": memory_info.vms / (1024 * 1024),
            "system_total_gb": system_memory.total / (1024**3),
            "system_available_gb": system_memory.available / (1024**3),
            "system_used_percent": system_memory.percent,
        }
    
    def check_memory_pressure(self) -> Tuple[bool, str]:
        """
        Prüft, ob Speicherdruck besteht.
        
        Returns:
            Tuple aus (pressure_detected, pressure_level)
        """
        memory_info = self.get_memory_usage()
        usage_mb = memory_info["process_rss_mb"]
        
        if usage_mb > self.critical_threshold_mb:
            return True, "critical"
        elif usage_mb > self.warning_threshold_mb:
            return True, "warning"
        else:
            return False, "normal"
    
    def perform_cleanup(self) -> int:
        """
        Führt Speicherbereinigung durch.
        
        Returns:
            Anzahl der bereinigten Objekte
        """
        # Garbage Collection durchführen
        collected = gc.collect()
        cyclic_refs = gc.collect()
        total_collected = collected + cyclic_refs
        
        # Registrierte Cleanup-Callbacks aufrufen
        for callback in self._cleanup_callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"Fehler beim Ausführen von Cleanup-Callback: {e}")
        
        logger.info(f"Speicherbereinigung durchgeführt: {total_collected} Objekte")
        return total_collected
    
    def register_cleanup_callback(self, callback) -> None:
        """
        Registriert eine Funktion, die bei Speicherbereinigung aufgerufen wird.
        
        Args:
            callback: Funktion, die aufgerufen werden soll
        """
        self._cleanup_callbacks.append(callback)


class ObjectPool:
    """
    Object Pool für teure Objekte, um Neuerstellung zu vermeiden.
    """
    
    def __init__(self, factory_func, max_size: int = 10):
        self._factory_func = factory_func
        self._max_size = max_size
        self._pool = deque(maxlen=max_size)
        self._in_use = weakref.WeakSet()
    
    def acquire(self) -> Any:
        """
        Holt ein Objekt aus dem Pool oder erstellt ein neues.
        
        Returns:
            Objekt aus dem Pool
        """
        if self._pool:
            obj = self._pool.popleft()
        else:
            obj = self._factory_func()
        
        self._in_use.add(obj)
        return obj
    
    def release(self, obj: Any) -> None:
        """
        Gibt ein Objekt an den Pool zurück.
        
        Args:
            obj: Objekt, das zurückgegeben wird
        """
        if obj in self._in_use:
            self._in_use.remove(obj)
            if len(self._pool) < self._max_size:
                self._pool.append(obj)
    
    def cleanup(self) -> None:
        """Leert den Pool."""
        self._pool.clear()
        self._in_use.clear()


# Globale Instanzen
_memory_monitor: Optional[MemoryMonitor] = None
_object_pools: Dict[str, ObjectPool] = {}


def get_memory_monitor() -> MemoryMonitor:
    """Gibt den globalen Memory-Monitor zurück."""
    global _memory_monitor
    if _memory_monitor is None:
        _memory_monitor = MemoryMonitor()
    return _memory_monitor


def get_object_pool(pool_name: str, factory_func, max_size: int = 10) -> ObjectPool:
    """
    Gibt einen benannten Object-Pool zurück.
    
    Args:
        pool_name: Name des Pools
        factory_func: Funktion zur Erstellung neuer Objekte
        max_size: Maximale Größe des Pools
        
    Returns:
        ObjectPool-Instanz
    """
    global _object_pools
    if pool_name not in _object_pools:
        _object_pools[pool_name] = ObjectPool(factory_func, max_size)
    return _object_pools[pool_name]


def perform_memory_cleanup() -> int:
    """
    Führt eine globale Speicherbereinigung durch.
    
    Returns:
        Anzahl der bereinigten Objekte
    """
    monitor = get_memory_monitor()
    return monitor.perform_cleanup()