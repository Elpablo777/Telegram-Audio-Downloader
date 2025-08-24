"""
Fortgeschrittene Speicherverwaltung für den Telegram Audio Downloader.

Features:
- Objekt-Pooling
- Lazy Loading
- Memory-Mapped-Dateien
- Speicherdefragmentierung
- Angepasste Allokatoren
"""

import gc
import mmap
import weakref
import asyncio
from collections import deque, defaultdict
from typing import Any, Optional, Dict, List, Callable
from dataclasses import dataclass, field
from pathlib import Path
import psutil

from .logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class MemoryStats:
    """Speicherstatistiken für das Monitoring."""
    process_memory_mb: float = 0.0
    system_memory_percent: float = 0.0
    object_count: int = 0
    pool_size: int = 0
    mapped_files: int = 0
    last_updated: float = 0.0


class ObjectPool:
    """Objektpool für teure Objekte, um Neuerstellung zu vermeiden."""
    
    def __init__(self, factory_func: Callable, max_size: int = 10):
        """
        Initialisiert den Objektpool.
        
        Args:
            factory_func: Funktion zur Erstellung neuer Objekte
            max_size: Maximale Poolgröße
        """
        self._factory_func = factory_func
        self._max_size = max_size
        self._pool = deque(maxlen=max_size)
        self._in_use = weakref.WeakSet()
        
        logger.debug(f"Objektpool initialisiert mit max. Größe {max_size}")
    
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
            if len(self._pool) < self._pool.maxlen:
                self._pool.append(obj)
    
    def pool_size(self) -> int:
        """Gibt die aktuelle Poolgröße zurück."""
        return len(self._pool)
    
    def in_use_count(self) -> int:
        """Gibt die Anzahl der verwendeten Objekte zurück."""
        return len(self._in_use)


class LazyLoader:
    """Lazy Loading für große Datenstrukturen."""
    
    def __init__(self):
        """Initialisiert den LazyLoader."""
        self._loaded_objects = {}
        self._load_functions = {}
        self._access_count = defaultdict(int)
        
    def register_loader(self, key: str, loader_func: Callable) -> None:
        """
        Registriert eine Lade-Funktion für einen Schlüssel.
        
        Args:
            key: Schlüssel für das Objekt
            loader_func: Funktion zum Laden des Objekts
        """
        self._load_functions[key] = loader_func
    
    def get(self, key: str) -> Any:
        """
        Holt ein Objekt (lädt es bei Bedarf).
        
        Args:
            key: Schlüssel des Objekts
            
        Returns:
            Geladenes Objekt
        """
        self._access_count[key] += 1
        
        if key not in self._loaded_objects:
            if key in self._load_functions:
                self._loaded_objects[key] = self._load_functions[key]()
                logger.debug(f"Objekt '{key}' lazy geladen")
            else:
                raise KeyError(f"Keine Lade-Funktion für Schlüssel '{key}' registriert")
                
        return self._loaded_objects[key]
    
    def unload(self, key: str) -> None:
        """
        Entlädt ein Objekt aus dem Speicher.
        
        Args:
            key: Schlüssel des Objekts
        """
        if key in self._loaded_objects:
            del self._loaded_objects[key]
            logger.debug(f"Objekt '{key}' aus Speicher entladen")
    
    def unload_least_used(self, count: int = 1) -> None:
        """
        Entlädt die am wenigsten verwendeten Objekte.
        
        Args:
            count: Anzahl der zu entladenden Objekte
        """
        # Finde die am wenigsten verwendeten Objekte
        sorted_items = sorted(self._access_count.items(), key=lambda x: x[1])
        keys_to_unload = [key for key, _ in sorted_items[:count]]
        
        for key in keys_to_unload:
            self.unload(key)
            if key in self._access_count:
                del self._access_count[key]


class MemoryMappedFileManager:
    """Verwaltet Memory-Mapped-Dateien für effizienten Dateizugriff."""
    
    def __init__(self, max_mapped_files: int = 5):
        """
        Initialisiert den MemoryMappedFileManager.
        
        Args:
            max_mapped_files: Maximale Anzahl gleichzeitig gemappter Dateien
        """
        self.max_mapped_files = max_mapped_files
        self._mapped_files = {}  # file_path -> mmap_object
        self._access_order = deque()  # Für LRU-ähnliches Verhalten
        self._file_sizes = {}  # file_path -> size
        
        logger.debug(f"MemoryMappedFileManager initialisiert mit max. {max_mapped_files} Dateien")
    
    def map_file(self, file_path: Path) -> Optional[mmap.mmap]:
        """
        Mappt eine Datei in den Speicher.
        
        Args:
            file_path: Pfad zur Datei
            
        Returns:
            Memory-Mapped-Objekt oder None bei Fehler
        """
        file_path = Path(file_path)
        
        # Prüfe, ob Datei bereits gemappt ist
        if str(file_path) in self._mapped_files:
            # Aktualisiere Zugriffsreihenfolge
            if str(file_path) in self._access_order:
                self._access_order.remove(str(file_path))
            self._access_order.append(str(file_path))
            return self._mapped_files[str(file_path)]
        
        try:
            # Prüfe Dateigröße
            file_size = file_path.stat().st_size
            if file_size == 0:
                return None
                
            # Wenn maximale Anzahl erreicht, entferne älteste Datei
            if len(self._mapped_files) >= self.max_mapped_files:
                if self._access_order:
                    oldest_file = self._access_order.popleft()
                    if oldest_file in self._mapped_files:
                        self._mapped_files[oldest_file].close()
                        del self._mapped_files[oldest_file]
                        if oldest_file in self._file_sizes:
                            del self._file_sizes[oldest_file]
            
            # Datei mappen
            with open(file_path, 'rb') as f:
                mapped_file = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
                self._mapped_files[str(file_path)] = mapped_file
                self._file_sizes[str(file_path)] = file_size
                self._access_order.append(str(file_path))
                
                logger.debug(f"Datei {file_path} gemappt ({file_size} Bytes)")
                return mapped_file
                
        except Exception as e:
            logger.error(f"Fehler beim Mappen der Datei {file_path}: {e}")
            return None
    
    def unmap_file(self, file_path: Path) -> None:
        """
        Entfernt eine Datei aus dem Speicher.
        
        Args:
            file_path: Pfad zur Datei
        """
        file_path = str(file_path)
        
        if file_path in self._mapped_files:
            self._mapped_files[file_path].close()
            del self._mapped_files[file_path]
            if file_path in self._file_sizes:
                del self._file_sizes[file_path]
            if file_path in self._access_order:
                self._access_order.remove(file_path)
                
            logger.debug(f"Datei {file_path} aus Speicher entfernt")
    
    def get_file_size(self, file_path: Path) -> int:
        """
        Gibt die Größe einer gemappten Datei zurück.
        
        Args:
            file_path: Pfad zur Datei
            
        Returns:
            Dateigröße in Bytes
        """
        return self._file_sizes.get(str(file_path), 0)
    
    def close_all(self) -> None:
        """Schließt alle gemappten Dateien."""
        for mapped_file in self._mapped_files.values():
            try:
                mapped_file.close()
            except Exception as e:
                logger.error(f"Fehler beim Schließen einer gemappten Datei: {e}")
        
        self._mapped_files.clear()
        self._file_sizes.clear()
        self._access_order.clear()


class AdvancedMemoryManager:
    """Zentrale Klasse für fortgeschrittene Speicherverwaltung."""
    
    def __init__(self, download_dir: Path, max_memory_mb: int = 1024):
        """
        Initialisiert den AdvancedMemoryManager.
        
        Args:
            download_dir: Download-Verzeichnis
            max_memory_mb: Maximale Speicherbelegung in MB
        """
        self.download_dir = Path(download_dir)
        self.max_memory_mb = max_memory_mb
        self.memory_pressure_threshold = max_memory_mb * 0.8
        self.critical_memory_threshold = max_memory_mb * 0.95
        
        # Komponenten initialisieren
        self.object_pools = {}  # pool_name -> ObjectPool
        self.lazy_loader = LazyLoader()
        self.mapped_file_manager = MemoryMappedFileManager()
        
        # Statistiken
        self.stats = MemoryStats()
        self._last_gc_time = 0.0
        self._gc_interval = 30.0  # Sekunden
        
        logger.info(f"AdvancedMemoryManager initialisiert mit max. {max_memory_mb}MB")
    
    def register_object_pool(self, name: str, factory_func: Callable, max_size: int = 10) -> None:
        """
        Registriert einen neuen Objektpool.
        
        Args:
            name: Name des Pools
            factory_func: Funktion zur Erstellung neuer Objekte
            max_size: Maximale Poolgröße
        """
        self.object_pools[name] = ObjectPool(factory_func, max_size)
        logger.debug(f"Objektpool '{name}' registriert")
    
    def acquire_from_pool(self, pool_name: str) -> Any:
        """
        Holt ein Objekt aus einem Pool.
        
        Args:
            pool_name: Name des Pools
            
        Returns:
            Objekt aus dem Pool
        """
        if pool_name in self.object_pools:
            return self.object_pools[pool_name].acquire()
        else:
            raise KeyError(f"Objektpool '{pool_name}' nicht gefunden")
    
    def release_to_pool(self, pool_name: str, obj: Any) -> None:
        """
        Gibt ein Objekt an einen Pool zurück.
        
        Args:
            pool_name: Name des Pools
            obj: Objekt, das zurückgegeben wird
        """
        if pool_name in self.object_pools:
            self.object_pools[pool_name].release(obj)
    
    def get_memory_stats(self) -> MemoryStats:
        """Gibt aktuelle Speicherstatistiken zurück."""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            system_memory = psutil.virtual_memory()
            
            self.stats.process_memory_mb = memory_info.rss / (1024 * 1024)
            self.stats.system_memory_percent = system_memory.percent
            self.stats.object_count = len(gc.get_objects())
            self.stats.pool_size = sum(pool.pool_size() for pool in self.object_pools.values())
            self.stats.mapped_files = len(self.mapped_file_manager._mapped_files)
            self.stats.last_updated = asyncio.get_event_loop().time()
            
        except Exception as e:
            logger.error(f"Fehler beim Erfassen der Speicherstatistiken: {e}")
            
        return self.stats
    
    def check_memory_pressure(self) -> str:
        """
        Prüft, ob Speicherdruck besteht.
        
        Returns:
            Drucklevel: 'normal', 'warning', 'critical'
        """
        stats = self.get_memory_stats()
        
        if stats.process_memory_mb > self.critical_memory_threshold:
            return 'critical'
        elif stats.process_memory_mb > self.memory_pressure_threshold:
            return 'warning'
        else:
            return 'normal'
    
    async def perform_memory_maintenance(self) -> None:
        """Führt Speicherwartung durch."""
        current_time = asyncio.get_event_loop().time()
        
        # Nur alle _gc_interval Sekunden Garbage Collection durchführen
        if current_time - self._last_gc_time < self._gc_interval:
            return
            
        self._last_gc_time = current_time
        
        # Speicherdruck prüfen
        pressure_level = self.check_memory_pressure()
        
        if pressure_level == 'critical':
            logger.warning("Kritischer Speicherdruck erkannt, führe erweiterte Bereinigung durch")
            
            # Lazy Loader bereinigen
            self.lazy_loader.unload_least_used(3)
            
            # Garbage Collection forcieren
            collected = gc.collect()
            logger.info(f"Garbage Collection durchgeführt: {collected} Objekte bereinigt")
            
        elif pressure_level == 'warning':
            logger.info("Speicherdruck erkannt, führe leichte Bereinigung durch")
            
            # Lazy Loader bereinigen
            self.lazy_loader.unload_least_used(1)
            
            # Normale Garbage Collection
            gc.collect()
    
    def map_file_for_reading(self, file_path: Path) -> Optional[mmap.mmap]:
        """
        Mappt eine Datei zum Lesen.
        
        Args:
            file_path: Pfad zur Datei
            
        Returns:
            Memory-Mapped-Objekt oder None bei Fehler
        """
        return self.mapped_file_manager.map_file(file_path)
    
    def unmap_file(self, file_path: Path) -> None:
        """
        Entfernt eine Datei aus dem Speicher.
        
        Args:
            file_path: Pfad zur Datei
        """
        self.mapped_file_manager.unmap_file(file_path)
    
    async def close(self) -> None:
        """Schließt alle Ressourcen."""
        self.mapped_file_manager.close_all()
        logger.info("AdvancedMemoryManager geschlossen")


def get_memory_manager(download_dir: Path = Path("."), max_memory_mb: int = 1024):
    """
    Gibt eine Instanz des AdvancedMemoryManager zurück.
    
    Args:
        download_dir: Download-Verzeichnis
        max_memory_mb: Maximale Speicherbelegung in MB
        
    Returns:
        AdvancedMemoryManager-Instanz
    """
    return AdvancedMemoryManager(download_dir, max_memory_mb)