"""
Intelligentes Caching für den Telegram Audio Downloader.
"""

import asyncio
import hashlib
import json
import logging
import os
import pickle
import time
from abc import ABC, abstractmethod
from collections import OrderedDict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional, Union

import aiofiles
from .error_handling import handle_error
from .file_error_handler import handle_file_error, with_file_error_handling

logger = logging.getLogger(__name__)

# Standard-Cache-Größen
DEFAULT_MEMORY_CACHE_SIZE = 1000
DEFAULT_DISK_CACHE_SIZE = 10000
DEFAULT_CDN_CACHE_SIZE = 100000

# Standard-TTL (Time-To-Live) in Sekunden
DEFAULT_MEMORY_TTL = 300  # 5 Minuten
DEFAULT_DISK_TTL = 3600   # 1 Stunde
DEFAULT_CDN_TTL = 86400   # 24 Stunden

class CacheEntry:
    """Repräsentiert einen Cache-Eintrag mit Metadaten."""
    
    def __init__(self, key: str, value: Any, ttl: int = DEFAULT_MEMORY_TTL):
        """
        Initialisiert einen Cache-Eintrag.
        
        Args:
            key: Schlüssel des Eintrags
            value: Wert des Eintrags
            ttl: Time-To-Live in Sekunden
        """
        self.key = key
        self.value = value
        self.created_at = time.time()
        self.expires_at = self.created_at + ttl if ttl is not None else None
        self.access_count = 0
        self.last_accessed = self.created_at
        
    def is_expired(self) -> bool:
        """
        Prüft, ob der Eintrag abgelaufen ist.
        
        Returns:
            True, wenn der Eintrag abgelaufen ist
        """
        if self.expires_at is None:
            return False
        return time.time() >= self.expires_at
        
    def access(self) -> None:
        """Markiert den Eintrag als zugegriffen."""
        self.access_count += 1
        self.last_accessed = time.time()
        
    def get_ttl(self) -> Optional[int]:
        """
        Berechnet die verbleibende TTL.
        
        Returns:
            Verbleibende TTL in Sekunden oder None, wenn kein Ablauf
        """
        if self.expires_at is None:
            return None
        remaining = int(self.expires_at - time.time())
        return max(0, remaining) if remaining >= 0 else 0


class BaseCache(ABC):
    """Abstrakte Basisklasse für alle Cache-Implementierungen."""
    
    def __init__(self, max_size: int = DEFAULT_MEMORY_CACHE_SIZE, default_ttl: int = DEFAULT_MEMORY_TTL):
        """
        Initialisiert den Basis-Cache.
        
        Args:
            max_size: Maximale Anzahl von Einträgen
            default_ttl: Standard-TTL für Einträge in Sekunden
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "errors": 0
        }
        
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """
        Ruft einen Wert aus dem Cache ab.
        
        Args:
            key: Schlüssel des abzurufenden Werts
            
        Returns:
            Wert oder None, wenn nicht gefunden
        """
        pass
        
    @abstractmethod
    async def put(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Fügt einen Wert zum Cache hinzu.
        
        Args:
            key: Schlüssel des Werts
            value: Wert zum Cachen
            ttl: Time-To-Live in Sekunden (optional)
            
        Returns:
            True, wenn erfolgreich
        """
        pass
        
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """
        Löscht einen Eintrag aus dem Cache.
        
        Args:
            key: Schlüssel des zu löschenden Eintrags
            
        Returns:
            True, wenn erfolgreich
        """
        pass
        
    @abstractmethod
    async def clear(self) -> None:
        """Leert den gesamten Cache."""
        pass
        
    @abstractmethod
    async def size(self) -> int:
        """
        Gibt die aktuelle Größe des Caches zurück.
        
        Returns:
            Anzahl der Einträge im Cache
        """
        pass
        
    def get_stats(self) -> Dict[str, Any]:
        """
        Gibt Cache-Statistiken zurück.
        
        Returns:
            Dictionary mit Statistiken
        """
        return self.stats.copy()


class MemoryCache(BaseCache):
    """In-Memory-Cache mit LRU-Eviction-Policy."""
    
    def __init__(self, max_size: int = DEFAULT_MEMORY_CACHE_SIZE, default_ttl: int = DEFAULT_MEMORY_TTL):
        """
        Initialisiert den Memory-Cache.
        
        Args:
            max_size: Maximale Anzahl von Einträgen
            default_ttl: Standard-TTL für Einträge in Sekunden
        """
        super().__init__(max_size, default_ttl)
        self.cache = OrderedDict()
        
    async def get(self, key: str) -> Optional[Any]:
        """
        Ruft einen Wert aus dem Memory-Cache ab.
        
        Args:
            key: Schlüssel des abzurufenden Werts
            
        Returns:
            Wert oder None, wenn nicht gefunden
        """
        try:
            if key in self.cache:
                entry = self.cache[key]
                if not entry.is_expired():
                    # Markiere als zugegriffen und verschiebe ans Ende (LRU)
                    entry.access()
                    self.cache.move_to_end(key)
                    self.stats["hits"] += 1
                    return entry.value
                else:
                    # Entferne abgelaufene Einträge
                    del self.cache[key]
                    
            self.stats["misses"] += 1
            return None
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Fehler beim Abrufen aus Memory-Cache: {e}")
            return None
            
    async def put(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Fügt einen Wert zum Memory-Cache hinzu.
        
        Args:
            key: Schlüssel des Werts
            value: Wert zum Cachen
            ttl: Time-To-Live in Sekunden (optional)
            
        Returns:
            True, wenn erfolgreich
        """
        try:
            # Wenn der Schlüssel bereits existiert, entferne ihn
            if key in self.cache:
                del self.cache[key]
                
            # Erstelle neuen Eintrag
            effective_ttl = ttl if ttl is not None else self.default_ttl
            entry = CacheEntry(key, value, effective_ttl)
            self.cache[key] = entry
            
            # Prüfe auf Größenbegrenzung und entferne älteste Einträge
            while len(self.cache) > self.max_size:
                # Entferne den ältesten Eintrag (LRU)
                oldest_key, _ = self.cache.popitem(last=False)
                self.stats["evictions"] += 1
                
            return True
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Fehler beim Einfügen in Memory-Cache: {e}")
            return False
            
    async def delete(self, key: str) -> bool:
        """
        Löscht einen Eintrag aus dem Memory-Cache.
        
        Args:
            key: Schlüssel des zu löschenden Eintrags
            
        Returns:
            True, wenn erfolgreich
        """
        try:
            if key in self.cache:
                del self.cache[key]
                return True
            return False
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Fehler beim Löschen aus Memory-Cache: {e}")
            return False
            
    async def clear(self) -> None:
        """Leert den gesamten Memory-Cache."""
        try:
            self.cache.clear()
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Fehler beim Leeren des Memory-Cache: {e}")
            
    async def size(self) -> int:
        """
        Gibt die aktuelle Größe des Memory-Cache zurück.
        
        Returns:
            Anzahl der Einträge im Cache
        """
        return len(self.cache)


class DiskCache(BaseCache):
    """Festplatten-Cache mit Dateisystem-basiertem Speicher."""
    
    def __init__(self, cache_dir: Union[str, Path], max_size: int = DEFAULT_DISK_CACHE_SIZE, 
                 default_ttl: int = DEFAULT_DISK_TTL):
        """
        Initialisiert den Disk-Cache.
        
        Args:
            cache_dir: Verzeichnis für den Cache
            max_size: Maximale Anzahl von Einträgen
            default_ttl: Standard-TTL für Einträge in Sekunden
        """
        super().__init__(max_size, default_ttl)
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._lock = asyncio.Lock()
        
    def _get_cache_file_path(self, key: str) -> Path:
        """
        Berechnet den Dateipfad für einen Cache-Schlüssel.
        
        Args:
            key: Cache-Schlüssel
            
        Returns:
            Pfad zur Cache-Datei
        """
        # Erstelle einen sicheren Dateinamen aus dem Schlüssel
        key_hash = hashlib.sha256(key.encode('utf-8')).hexdigest()
        return self.cache_dir / f"{key_hash}.cache"
        
    async def get(self, key: str) -> Optional[Any]:
        """
        Ruft einen Wert aus dem Disk-Cache ab.
        
        Args:
            key: Schlüssel des abzurufenden Werts
            
        Returns:
            Wert oder None, wenn nicht gefunden
        """
        try:
            async with self._lock:
                cache_file = self._get_cache_file_path(key)
                if cache_file.exists():
                    try:
                        async with aiofiles.open(cache_file, 'rb') as f:
                            data = await f.read()
                            entry = pickle.loads(data)
                            
                            if not entry.is_expired():
                                entry.access()
                                # Aktualisiere die Datei mit den neuen Zugriffsdaten
                                async with aiofiles.open(cache_file, 'wb') as f:
                                    await f.write(pickle.dumps(entry))
                                self.stats["hits"] += 1
                                return entry.value
                            else:
                                # Entferne abgelaufene Datei
                                cache_file.unlink()
                    except Exception:
                        # Bei Fehler entferne die beschädigte Datei
                        if cache_file.exists():
                            cache_file.unlink()
                            
            self.stats["misses"] += 1
            return None
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Fehler beim Abrufen aus Disk-Cache: {e}")
            return None
            
    async def put(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Fügt einen Wert zum Disk-Cache hinzu.
        
        Args:
            key: Schlüssel des Werts
            value: Wert zum Cachen
            ttl: Time-To-Live in Sekunden (optional)
            
        Returns:
            True, wenn erfolgreich
        """
        try:
            async with self._lock:
                # Prüfe aktuelle Größe und entferne älteste Dateien bei Bedarf
                cache_files = list(self.cache_dir.glob("*.cache"))
                if len(cache_files) >= self.max_size:
                    # Sortiere nach Änderungsdatum (älteste zuerst)
                    cache_files.sort(key=lambda f: f.stat().st_mtime)
                    # Entferne älteste Dateien
                    for i in range(len(cache_files) - self.max_size + 1):
                        cache_files[i].unlink()
                        self.stats["evictions"] += 1
                
                # Erstelle neuen Eintrag
                effective_ttl = ttl if ttl is not None else self.default_ttl
                entry = CacheEntry(key, value, effective_ttl)
                
                # Speichere in Datei
                cache_file = self._get_cache_file_path(key)
                async with aiofiles.open(cache_file, 'wb') as f:
                    await f.write(pickle.dumps(entry))
                    
                return True
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Fehler beim Einfügen in Disk-Cache: {e}")
            return False
            
    async def delete(self, key: str) -> bool:
        """
        Löscht einen Eintrag aus dem Disk-Cache.
        
        Args:
            key: Schlüssel des zu löschenden Eintrags
            
        Returns:
            True, wenn erfolgreich
        """
        try:
            async with self._lock:
                cache_file = self._get_cache_file_path(key)
                if cache_file.exists():
                    cache_file.unlink()
                    return True
                return False
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Fehler beim Löschen aus Disk-Cache: {e}")
            return False
            
    async def clear(self) -> None:
        """Leert den gesamten Disk-Cache."""
        try:
            async with self._lock:
                for cache_file in self.cache_dir.glob("*.cache"):
                    cache_file.unlink()
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Fehler beim Leeren des Disk-Cache: {e}")
            
    async def size(self) -> int:
        """
        Gibt die aktuelle Größe des Disk-Cache zurück.
        
        Returns:
            Anzahl der Einträge im Cache
        """
        try:
            return len(list(self.cache_dir.glob("*.cache")))
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Fehler beim Ermitteln der Disk-Cache-Größe: {e}")
            return 0


class CDNCache(BaseCache):
    """CDN-Cache für vorgeladene Vorschauen und häufig verwendete Daten."""
    
    def __init__(self, cache_dir: Union[str, Path], max_size: int = DEFAULT_CDN_CACHE_SIZE, 
                 default_ttl: int = DEFAULT_CDN_TTL):
        """
        Initialisiert den CDN-Cache.
        
        Args:
            cache_dir: Verzeichnis für den Cache
            max_size: Maximale Anzahl von Einträgen
            default_ttl: Standard-TTL für Einträge in Sekunden
        """
        super().__init__(max_size, default_ttl)
        self.cache_dir = Path(cache_dir) / "cdn"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.cache_dir / "metadata.json"
        self._lock = asyncio.Lock()
        self._load_metadata()
        
    def _load_metadata(self) -> None:
        """Lädt die Cache-Metadaten."""
        try:
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r') as f:
                    self.metadata = json.load(f)
            else:
                self.metadata = {}
        except Exception as e:
            logger.warning(f"Fehler beim Laden der CDN-Cache-Metadaten: {e}")
            self.metadata = {}
            
    def _save_metadata(self) -> None:
        """Speichert die Cache-Metadaten."""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Fehler beim Speichern der CDN-Cache-Metadaten: {e}")
            
    def _get_cache_file_path(self, key: str) -> Path:
        """
        Berechnet den Dateipfad für einen Cache-Schlüssel.
        
        Args:
            key: Cache-Schlüssel
            
        Returns:
            Pfad zur Cache-Datei
        """
        # Erstelle einen sicheren Dateinamen aus dem Schlüssel
        key_hash = hashlib.sha256(key.encode('utf-8')).hexdigest()
        return self.cache_dir / f"{key_hash}.cdn"
        
    async def get(self, key: str) -> Optional[Any]:
        """
        Ruft einen Wert aus dem CDN-Cache ab.
        
        Args:
            key: Schlüssel des abzurufenden Werts
            
        Returns:
            Wert oder None, wenn nicht gefunden
        """
        try:
            async with self._lock:
                if key in self.metadata:
                    entry_info = self.metadata[key]
                    cache_file = Path(entry_info["file_path"])
                    
                    if cache_file.exists():
                        # Prüfe auf Ablauf
                        if entry_info["expires_at"] is None or time.time() <= entry_info["expires_at"]:
                            try:
                                async with aiofiles.open(cache_file, 'rb') as f:
                                    data = await f.read()
                                    value = pickle.loads(data)
                                    
                                    # Aktualisiere Zugriffsstatistik
                                    entry_info["access_count"] += 1
                                    entry_info["last_accessed"] = time.time()
                                    self._save_metadata()
                                    
                                    self.stats["hits"] += 1
                                    return value
                            except Exception:
                                # Bei Fehler entferne die beschädigte Datei
                                if cache_file.exists():
                                    cache_file.unlink()
                                # Und die Metadaten
                                del self.metadata[key]
                                self._save_metadata()
                        else:
                            # Entferne abgelaufene Datei und Metadaten
                            if cache_file.exists():
                                cache_file.unlink()
                            del self.metadata[key]
                            self._save_metadata()
                            
            self.stats["misses"] += 1
            return None
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Fehler beim Abrufen aus CDN-Cache: {e}")
            return None
            
    async def put(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Fügt einen Wert zum CDN-Cache hinzu.
        
        Args:
            key: Schlüssel des Werts
            value: Wert zum Cachen
            ttl: Time-To-Live in Sekunden (optional)
            
        Returns:
            True, wenn erfolgreich
        """
        try:
            async with self._lock:
                # Prüfe aktuelle Größe und entferne älteste Dateien bei Bedarf
                if len(self.metadata) >= self.max_size:
                    # Sortiere nach letztem Zugriff (älteste zuerst)
                    sorted_entries = sorted(
                        self.metadata.items(), 
                        key=lambda x: x[1]["last_accessed"]
                    )
                    # Entferne älteste Einträge
                    for i in range(len(sorted_entries) - self.max_size + 1):
                        old_key, old_info = sorted_entries[i]
                        old_file = Path(old_info["file_path"])
                        if old_file.exists():
                            old_file.unlink()
                        del self.metadata[old_key]
                        self.stats["evictions"] += 1
                    self._save_metadata()
                
                # Erstelle neuen Eintrag
                effective_ttl = ttl if ttl is not None else self.default_ttl
                expires_at = time.time() + effective_ttl if effective_ttl > 0 else None
                
                # Speichere in Datei
                cache_file = self._get_cache_file_path(key)
                async with aiofiles.open(cache_file, 'wb') as f:
                    await f.write(pickle.dumps(value))
                
                # Speichere Metadaten
                self.metadata[key] = {
                    "file_path": str(cache_file),
                    "created_at": time.time(),
                    "expires_at": expires_at,
                    "access_count": 0,
                    "last_accessed": time.time()
                }
                self._save_metadata()
                
                return True
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Fehler beim Einfügen in CDN-Cache: {e}")
            return False
            
    async def delete(self, key: str) -> bool:
        """
        Löscht einen Eintrag aus dem CDN-Cache.
        
        Args:
            key: Schlüssel des zu löschenden Eintrags
            
        Returns:
            True, wenn erfolgreich
        """
        try:
            async with self._lock:
                if key in self.metadata:
                    entry_info = self.metadata[key]
                    cache_file = Path(entry_info["file_path"])
                    if cache_file.exists():
                        cache_file.unlink()
                    del self.metadata[key]
                    self._save_metadata()
                    return True
                return False
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Fehler beim Löschen aus CDN-Cache: {e}")
            return False
            
    async def clear(self) -> None:
        """Leert den gesamten CDN-Cache."""
        try:
            async with self._lock:
                for entry_info in self.metadata.values():
                    cache_file = Path(entry_info["file_path"])
                    if cache_file.exists():
                        cache_file.unlink()
                self.metadata.clear()
                self._save_metadata()
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Fehler beim Leeren des CDN-Cache: {e}")
            
    async def size(self) -> int:
        """
        Gibt die aktuelle Größe des CDN-Cache zurück.
        
        Returns:
            Anzahl der Einträge im Cache
        """
        try:
            return len(self.metadata)
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Fehler beim Ermitteln der CDN-Cache-Größe: {e}")
            return 0


class IntelligentCachingSystem:
    """Intelligentes Caching-System mit mehrstufigem Caching."""
    
    def __init__(self, cache_dir: Union[str, Path]):
        """
        Initialisiert das intelligente Caching-System.
        
        Args:
            cache_dir: Basis-Verzeichnis für alle Caches
        """
        self.cache_dir = Path(cache_dir)
        self.memory_cache = MemoryCache()
        self.disk_cache = DiskCache(self.cache_dir / "disk")
        self.cdn_cache = CDNCache(self.cache_dir / "cdn")
        
    async def get(self, key: str, cache_level: str = "all") -> Optional[Any]:
        """
        Ruft einen Wert aus dem Cache ab (mit mehrstufigem Fallback).
        
        Args:
            key: Schlüssel des abzurufenden Werts
            cache_level: Cache-Ebene ("memory", "disk", "cdn", "all")
            
        Returns:
            Wert oder None, wenn nicht gefunden
        """
        # 1. Prüfe Memory-Cache
        if cache_level in ["memory", "all"]:
            value = await self.memory_cache.get(key)
            if value is not None:
                return value
                
        # 2. Prüfe Disk-Cache
        if cache_level in ["disk", "all"]:
            value = await self.disk_cache.get(key)
            if value is not None:
                # Promote to memory cache
                await self.memory_cache.put(key, value)
                return value
                
        # 3. Prüfe CDN-Cache
        if cache_level in ["cdn", "all"]:
            value = await self.cdn_cache.get(key)
            if value is not None:
                # Promote to memory and disk cache
                await self.memory_cache.put(key, value)
                await self.disk_cache.put(key, value)
                return value
                
        return None
        
    async def put(self, key: str, value: Any, cache_levels: list = None, 
                  ttl: Optional[Dict[str, int]] = None) -> bool:
        """
        Fügt einen Wert zu den Caches hinzu.
        
        Args:
            key: Schlüssel des Werts
            value: Wert zum Cachen
            cache_levels: Liste der Cache-Ebenen ("memory", "disk", "cdn")
            ttl: TTL für jede Ebene
            
        Returns:
            True, wenn erfolgreich
        """
        if cache_levels is None:
            cache_levels = ["memory", "disk", "cdn"]
            
        if ttl is None:
            ttl = {}
            
        success = True
        
        # Füge zu den angegebenen Ebenen hinzu
        if "memory" in cache_levels:
            mem_ttl = ttl.get("memory", DEFAULT_MEMORY_TTL)
            success &= await self.memory_cache.put(key, value, mem_ttl)
            
        if "disk" in cache_levels:
            disk_ttl = ttl.get("disk", DEFAULT_DISK_TTL)
            success &= await self.disk_cache.put(key, value, disk_ttl)
            
        if "cdn" in cache_levels:
            cdn_ttl = ttl.get("cdn", DEFAULT_CDN_TTL)
            success &= await self.cdn_cache.put(key, value, cdn_ttl)
            
        return success
        
    async def delete(self, key: str) -> bool:
        """
        Löscht einen Eintrag aus allen Caches.
        
        Args:
            key: Schlüssel des zu löschenden Eintrags
            
        Returns:
            True, wenn erfolgreich
        """
        success = True
        success &= await self.memory_cache.delete(key)
        success &= await self.disk_cache.delete(key)
        success &= await self.cdn_cache.delete(key)
        return success
        
    async def clear(self, cache_level: str = "all") -> None:
        """
        Leert die Caches.
        
        Args:
            cache_level: Zu leerende Ebene ("memory", "disk", "cdn", "all")
        """
        if cache_level in ["memory", "all"]:
            await self.memory_cache.clear()
        if cache_level in ["disk", "all"]:
            await self.disk_cache.clear()
        if cache_level in ["cdn", "all"]:
            await self.cdn_cache.clear()
            
    async def get_stats(self) -> Dict[str, Any]:
        """
        Gibt Statistiken für alle Cache-Ebenen zurück.
        
        Returns:
            Dictionary mit Statistiken
        """
        return {
            "memory": await self.memory_cache.get_stats(),
            "disk": await self.disk_cache.get_stats(),
            "cdn": await self.cdn_cache.get_stats(),
            "memory_size": await self.memory_cache.size(),
            "disk_size": await self.disk_cache.size(),
            "cdn_size": await self.cdn_cache.size()
        }


# Globale Instanz des intelligenten Caching-Systems
_intelligent_cache: Optional[IntelligentCachingSystem] = None


def get_intelligent_cache(cache_dir: Union[str, Path] = "cache") -> IntelligentCachingSystem:
    """
    Gibt die globale Instanz des intelligenten Caching-Systems zurück.
    
    Args:
        cache_dir: Basis-Verzeichnis für alle Caches
        
    Returns:
        Instanz des IntelligentCachingSystem
    """
    global _intelligent_cache
    if _intelligent_cache is None:
        _intelligent_cache = IntelligentCachingSystem(cache_dir)
    return _intelligent_cache