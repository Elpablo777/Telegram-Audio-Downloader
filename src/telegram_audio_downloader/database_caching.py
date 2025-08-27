"""
Datenbank-Caching für den Telegram Audio Downloader.

Ebenen:
- In-Memory-Cache
- Redis/Memcached
- Abfrage-Ergebnis-Cache
- Objekt-Cache
"""

import time
import hashlib
import json
import threading
from typing import Optional, Dict, Any, List, Callable
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timedelta

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from .models import db
from .logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class CacheEntry:
    """Repräsentiert einen Cache-Eintrag."""
    key: str
    value: Any
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)


class InMemoryCache:
    """In-Memory-Cache mit LRU-Eviction."""
    
    def __init__(self, max_size: int = 1000, default_ttl_seconds: int = 300):
        """
        Initialisiert den InMemoryCache.
        
        Args:
            max_size: Maximale Anzahl von Einträgen
            default_ttl_seconds: Standard-TTL in Sekunden
        """
        self.max_size = max_size
        self.default_ttl_seconds = default_ttl_seconds
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.hits = 0
        self.misses = 0
        self._lock = threading.RLock()
        
        logger.info(f"InMemoryCache initialisiert mit max. {max_size} Einträgen")
    
    def get(self, key: str) -> Optional[Any]:
        """
        Holt einen Wert aus dem Cache.
        
        Args:
            key: Schlüssel
            
        Returns:
            Wert oder None, wenn nicht gefunden
        """
        with self._lock:
            if key in self.cache:
                entry = self.cache[key]
                
                # Prüfe, ob der Eintrag abgelaufen ist
                if entry.expires_at and entry.expires_at < datetime.now():
                    del self.cache[key]
                    self.misses += 1
                    return None
                
                # Aktualisiere Zugriffsstatistiken
                entry.access_count += 1
                entry.last_accessed = datetime.now()
                self.cache.move_to_end(key)  # Markiere als zuletzt verwendet
                self.hits += 1
                return entry.value
            else:
                self.misses += 1
                return None
    
    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """
        Speichert einen Wert im Cache.
        
        Args:
            key: Schlüssel
            value: Wert
            ttl_seconds: TTL in Sekunden (None für Standard-TTL)
        """
        with self._lock:
            # Entferne den Eintrag, falls er bereits existiert
            if key in self.cache:
                del self.cache[key]
            
            # Prüfe die maximale Größe und entferne älteste Einträge
            while len(self.cache) >= self.max_size:
                self.cache.popitem(last=False)  # Entferne ältesten Eintrag
            
            # Berechne Ablaufzeit
            expires_at = None
            if ttl_seconds is not None:
                expires_at = datetime.now() + timedelta(seconds=ttl_seconds)
            elif self.default_ttl_seconds > 0:
                expires_at = datetime.now() + timedelta(seconds=self.default_ttl_seconds)
            
            # Erstelle und speichere den Eintrag
            entry = CacheEntry(
                key=key,
                value=value,
                expires_at=expires_at
            )
            self.cache[key] = entry
            self.cache.move_to_end(key)  # Markiere als zuletzt verwendet
    
    def delete(self, key: str) -> bool:
        """
        Löscht einen Eintrag aus dem Cache.
        
        Args:
            key: Schlüssel
            
        Returns:
            True, wenn der Eintrag gelöscht wurde
        """
        with self._lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False
    
    def clear(self) -> None:
        """Leert den Cache."""
        with self._lock:
            self.cache.clear()
            self.hits = 0
            self.misses = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Gibt Cache-Statistiken zurück.
        
        Returns:
            Dictionary mit Cache-Statistiken
        """
        with self._lock:
            total_requests = self.hits + self.misses
            hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
            
            return {
                "size": len(self.cache),
                "max_size": self.max_size,
                "hits": self.hits,
                "misses": self.misses,
                "total_requests": total_requests,
                "hit_rate_percent": round(hit_rate, 2),
                "default_ttl_seconds": self.default_ttl_seconds
            }
    
    def cleanup_expired(self) -> int:
        """
        Bereinigt abgelaufene Einträge.
        
        Returns:
            Anzahl der bereinigten Einträge
        """
        with self._lock:
            current_time = datetime.now()
            expired_keys = [
                key for key, entry in self.cache.items()
                if entry.expires_at and entry.expires_at < current_time
            ]
            
            for key in expired_keys:
                del self.cache[key]
            
            if expired_keys:
                logger.debug(f"{len(expired_keys)} abgelaufene Einträge bereinigt")
            
            return len(expired_keys)


class RedisCache:
    """Redis-basierter Cache."""
    
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0,
                 password: Optional[str] = None, default_ttl_seconds: int = 300):
        """
        Initialisiert den RedisCache.
        
        Args:
            host: Redis-Host
            port: Redis-Port
            db: Redis-Datenbanknummer
            password: Redis-Passwort
            default_ttl_seconds: Standard-TTL in Sekunden
        """
        if not REDIS_AVAILABLE:
            raise ImportError("Redis ist nicht verfügbar. Installiere 'redis' mit pip.")
        
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.default_ttl_seconds = default_ttl_seconds
        self.client: Optional[redis.Redis] = None
        self.hits = 0
        self.misses = 0
        
        # Verbinde mit Redis
        self._connect()
        
        logger.info(f"RedisCache initialisiert für {host}:{port}/{db}")
    
    def _connect(self) -> None:
        """Stellt die Verbindung zu Redis her."""
        try:
            self.client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Teste die Verbindung
            self.client.ping()
            logger.debug("Redis-Verbindung erfolgreich")
        except Exception as e:
            logger.error(f"Fehler beim Verbinden mit Redis: {e}")
            self.client = None
    
    def get(self, key: str) -> Optional[Any]:
        """
        Holt einen Wert aus Redis.
        
        Args:
            key: Schlüssel
            
        Returns:
            Wert oder None, wenn nicht gefunden
        """
        if not self.client:
            return None
        
        try:
            value = self.client.get(key)
            if value is not None:
                self.hits += 1
                # Deserialisiere den Wert
                return json.loads(value)
            else:
                self.misses += 1
                return None
        except Exception as e:
            logger.error(f"Fehler beim Lesen aus Redis: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> bool:
        """
        Speichert einen Wert in Redis.
        
        Args:
            key: Schlüssel
            value: Wert
            ttl_seconds: TTL in Sekunden (None für Standard-TTL)
            
        Returns:
            True, wenn der Wert gespeichert wurde
        """
        if not self.client:
            return False
        
        try:
            # Serialisiere den Wert
            serialized_value = json.dumps(value, default=str)
            
            # Setze TTL
            ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl_seconds
            
            # Speichere den Wert
            result = self.client.setex(key, ttl, serialized_value)
            return result
        except Exception as e:
            logger.error(f"Fehler beim Speichern in Redis: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Löscht einen Eintrag aus Redis.
        
        Args:
            key: Schlüssel
            
        Returns:
            True, wenn der Eintrag gelöscht wurde
        """
        if not self.client:
            return False
        
        try:
            result = self.client.delete(key)
            return result > 0
        except Exception as e:
            logger.error(f"Fehler beim Löschen aus Redis: {e}")
            return False
    
    def clear(self) -> None:
        """Leert den Redis-Cache."""
        if not self.client:
            return
        
        try:
            self.client.flushdb()
            self.hits = 0
            self.misses = 0
        except Exception as e:
            logger.error(f"Fehler beim Leeren von Redis: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Gibt Redis-Statistiken zurück.
        
        Returns:
            Dictionary mit Redis-Statistiken
        """
        if not self.client:
            return {}
        
        try:
            info = self.client.info()
            total_requests = self.hits + self.misses
            hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
            
            return {
                "hits": self.hits,
                "misses": self.misses,
                "total_requests": total_requests,
                "hit_rate_percent": round(hit_rate, 2),
                "redis_info": {
                    "used_memory": info.get("used_memory_human", "N/A"),
                    "connected_clients": info.get("connected_clients", "N/A"),
                    "total_commands_processed": info.get("total_commands_processed", "N/A"),
                    "keyspace_hits": info.get("keyspace_hits", "N/A"),
                    "keyspace_misses": info.get("keyspace_misses", "N/A")
                }
            }
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Redis-Statistiken: {e}")
            return {}


class QueryResultCache:
    """Cache für Abfrageergebnisse."""
    
    def __init__(self, memory_cache: InMemoryCache, redis_cache: Optional[RedisCache] = None):
        """
        Initialisiert den QueryResultCache.
        
        Args:
            memory_cache: In-Memory-Cache
            redis_cache: Optionaler Redis-Cache
        """
        self.memory_cache = memory_cache
        self.redis_cache = redis_cache
        self.query_cache_prefix = "query:"
        
        logger.info("QueryResultCache initialisiert")
    
    def _generate_cache_key(self, query: str, params: tuple) -> str:
        """
        Generiert einen Cache-Schlüssel für eine Abfrage.
        
        Args:
            query: SQL-Abfrage
            params: Abfrageparameter
            
        Returns:
            Cache-Schlüssel
        """
        # Kombiniere Abfrage und Parameter
        key_data = f"{query}:{params}"
        # Erstelle SHA-256-Hash als Schlüssel (sicherer als MD5)
        return self.query_cache_prefix + hashlib.sha256(key_data.encode()).hexdigest()
    
    def get_query_result(self, query: str, params: tuple = ()) -> Optional[Any]:
        """
        Holt ein Abfrageergebnis aus dem Cache.
        
        Args:
            query: SQL-Abfrage
            params: Abfrageparameter
            
        Returns:
            Abfrageergebnis oder None, wenn nicht im Cache
        """
        cache_key = self._generate_cache_key(query, params)
        
        # Prüfe zuerst den Memory-Cache
        result = self.memory_cache.get(cache_key)
        if result is not None:
            logger.debug(f"Abfrageergebnis aus Memory-Cache geholt: {cache_key}")
            return result
        
        # Prüfe dann den Redis-Cache
        if self.redis_cache:
            result = self.redis_cache.get(cache_key)
            if result is not None:
                # Speichere das Ergebnis auch im Memory-Cache
                self.memory_cache.set(cache_key, result)
                logger.debug(f"Abfrageergebnis aus Redis-Cache geholt: {cache_key}")
                return result
        
        logger.debug(f"Abfrageergebnis nicht im Cache gefunden: {cache_key}")
        return None
    
    def set_query_result(self, query: str, params: tuple, result: Any,
                        ttl_seconds: Optional[int] = None) -> None:
        """
        Speichert ein Abfrageergebnis im Cache.
        
        Args:
            query: SQL-Abfrage
            params: Abfrageparameter
            result: Abfrageergebnis
            ttl_seconds: TTL in Sekunden
        """
        cache_key = self._generate_cache_key(query, params)
        
        # Speichere im Memory-Cache
        self.memory_cache.set(cache_key, result, ttl_seconds)
        
        # Speichere im Redis-Cache, falls verfügbar
        if self.redis_cache:
            self.redis_cache.set(cache_key, result, ttl_seconds)
        
        logger.debug(f"Abfrageergebnis im Cache gespeichert: {cache_key}")
    
    def invalidate_query(self, query: str, params: tuple = ()) -> None:
        """
        Invalidiert ein Abfrageergebnis im Cache.
        
        Args:
            query: SQL-Abfrage
            params: Abfrageparameter
        """
        cache_key = self._generate_cache_key(query, params)
        
        # Lösche aus dem Memory-Cache
        self.memory_cache.delete(cache_key)
        
        # Lösche aus dem Redis-Cache, falls verfügbar
        if self.redis_cache:
            self.redis_cache.delete(cache_key)
        
        logger.debug(f"Abfrageergebnis aus Cache entfernt: {cache_key}")
    
    def clear_all_queries(self) -> None:
        """Leert alle Abfrageergebnisse aus dem Cache."""
        # In einer echten Implementierung würden wir hier alle
        # Schlüssel mit dem Präfix "query:" entfernen
        self.memory_cache.clear()
        if self.redis_cache:
            self.redis_cache.clear()
        
        logger.info("Alle Abfrageergebnisse aus Cache entfernt")


class ObjectCache:
    """Cache für Objekte."""
    
    def __init__(self, memory_cache: InMemoryCache, redis_cache: Optional[RedisCache] = None):
        """
        Initialisiert den ObjectCache.
        
        Args:
            memory_cache: In-Memory-Cache
            redis_cache: Optionaler Redis-Cache
        """
        self.memory_cache = memory_cache
        self.redis_cache = redis_cache
        self.object_cache_prefix = "object:"
        
        logger.info("ObjectCache initialisiert")
    
    def get_object(self, object_type: str, object_id: str) -> Optional[Any]:
        """
        Holt ein Objekt aus dem Cache.
        
        Args:
            object_type: Typ des Objekts
            object_id: ID des Objekts
            
        Returns:
            Objekt oder None, wenn nicht im Cache
        """
        cache_key = f"{self.object_cache_prefix}{object_type}:{object_id}"
        
        # Prüfe zuerst den Memory-Cache
        result = self.memory_cache.get(cache_key)
        if result is not None:
            logger.debug(f"Objekt aus Memory-Cache geholt: {cache_key}")
            return result
        
        # Prüfe dann den Redis-Cache
        if self.redis_cache:
            result = self.redis_cache.get(cache_key)
            if result is not None:
                # Speichere das Objekt auch im Memory-Cache
                self.memory_cache.set(cache_key, result)
                logger.debug(f"Objekt aus Redis-Cache geholt: {cache_key}")
                return result
        
        logger.debug(f"Objekt nicht im Cache gefunden: {cache_key}")
        return None
    
    def set_object(self, object_type: str, object_id: str, obj: Any,
                  ttl_seconds: Optional[int] = None) -> None:
        """
        Speichert ein Objekt im Cache.
        
        Args:
            object_type: Typ des Objekts
            object_id: ID des Objekts
            obj: Objekt
            ttl_seconds: TTL in Sekunden
        """
        cache_key = f"{self.object_cache_prefix}{object_type}:{object_id}"
        
        # Speichere im Memory-Cache
        self.memory_cache.set(cache_key, obj, ttl_seconds)
        
        # Speichere im Redis-Cache, falls verfügbar
        if self.redis_cache:
            self.redis_cache.set(cache_key, obj, ttl_seconds)
        
        logger.debug(f"Objekt im Cache gespeichert: {cache_key}")
    
    def invalidate_object(self, object_type: str, object_id: str) -> None:
        """
        Invalidiert ein Objekt im Cache.
        
        Args:
            object_type: Typ des Objekts
            object_id: ID des Objekts
        """
        cache_key = f"{self.object_cache_prefix}{object_type}:{object_id}"
        
        # Lösche aus dem Memory-Cache
        self.memory_cache.delete(cache_key)
        
        # Lösche aus dem Redis-Cache, falls verfügbar
        if self.redis_cache:
            self.redis_cache.delete(cache_key)
        
        logger.debug(f"Objekt aus Cache entfernt: {cache_key}")
    
    def clear_all_objects(self) -> None:
        """Leert alle Objekte aus dem Cache."""
        # In einer echten Implementierung würden wir hier alle
        # Schlüssel mit dem Präfix "object:" entfernen
        self.memory_cache.clear()
        if self.redis_cache:
            self.redis_cache.clear()
        
        logger.info("Alle Objekte aus Cache entfernt")


class DatabaseCacheManager:
    """Zentrale Verwaltung aller Datenbank-Caches."""
    
    def __init__(self, redis_config: Optional[Dict[str, Any]] = None):
        """
        Initialisiert den DatabaseCacheManager.
        
        Args:
            redis_config: Konfiguration für Redis (None, wenn nicht verwendet)
        """
        # Initialisiere die Caches
        self.memory_cache = InMemoryCache(max_size=1000, default_ttl_seconds=300)
        
        self.redis_cache = None
        if redis_config and REDIS_AVAILABLE:
            try:
                self.redis_cache = RedisCache(**redis_config)
            except Exception as e:
                logger.warning(f"Redis-Cache konnte nicht initialisiert werden: {e}")
        
        # Initialisiere spezialisierte Caches
        self.query_cache = QueryResultCache(self.memory_cache, self.redis_cache)
        self.object_cache = ObjectCache(self.memory_cache, self.redis_cache)
        
        # Hintergrund-Task für Cache-Bereinigung
        self.cleanup_thread = None
        self.cleanup_interval = 60  # Sekunden
        self._start_cleanup_thread()
        
        logger.info("DatabaseCacheManager initialisiert")
    
    def _start_cleanup_thread(self) -> None:
        """Startet den Hintergrund-Task für Cache-Bereinigung."""
        def cleanup_loop():
            while True:
                try:
                    time.sleep(self.cleanup_interval)
                    self.memory_cache.cleanup_expired()
                except Exception as e:
                    logger.error(f"Fehler im Cache-Cleanup-Thread: {e}")
        
        self.cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
        self.cleanup_thread.start()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Gibt Statistiken für alle Caches zurück.
        
        Returns:
            Dictionary mit Cache-Statistiken
        """
        stats = {
            "memory_cache": self.memory_cache.get_stats(),
            "query_cache": {
                "enabled": True
            },
            "object_cache": {
                "enabled": True
            }
        }
        
        if self.redis_cache:
            stats["redis_cache"] = self.redis_cache.get_stats()
        else:
            stats["redis_cache"] = {
                "enabled": False,
                "reason": "Redis nicht konfiguriert oder nicht verfügbar"
            }
        
        return stats
    
    def clear_all_caches(self) -> None:
        """Leert alle Caches."""
        self.memory_cache.clear()
        if self.redis_cache:
            self.redis_cache.clear()
        logger.info("Alle Caches geleert")


# Globale Instanz des CacheManagers
_cache_manager: Optional[DatabaseCacheManager] = None


def get_cache_manager() -> DatabaseCacheManager:
    """
    Gibt die globale Instanz des DatabaseCacheManager zurück.
    
    Returns:
        DatabaseCacheManager-Instanz
    """
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = DatabaseCacheManager()
    return _cache_manager


def cache_database_query(ttl_seconds: Optional[int] = None):
    """
    Dekorator zum Cachen von Datenbankabfragen.
    
    Args:
        ttl_seconds: TTL in Sekunden (None für Standard-TTL)
    """
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            # Erstelle Cache-Schlüssel aus Funktionsname und Argumenten
            key_data = f"{func.__name__}:{args}:{kwargs}"
            cache_key = hashlib.sha256(key_data.encode()).hexdigest()
            
            # Hole Cache-Manager
            cache_manager = get_cache_manager()
            
            # Prüfe, ob Ergebnis im Cache ist
            cached_result = cache_manager.memory_cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Ergebnis aus Cache geholt für {func.__name__}")
                return cached_result
            
            # Führe Funktion aus
            result = func(*args, **kwargs)
            
            # Speichere Ergebnis im Cache
            cache_manager.memory_cache.set(cache_key, result, ttl_seconds)
            logger.debug(f"Ergebnis im Cache gespeichert für {func.__name__}")
            
            return result
        return wrapper
    return decorator


def get_cache_statistics() -> Dict[str, Any]:
    """
    Gibt Cache-Statistiken zurück.
    
    Returns:
        Dictionary mit Cache-Statistiken
    """
    try:
        cache_manager = get_cache_manager()
        return cache_manager.get_cache_stats()
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Cache-Statistiken: {e}")
        return {}


def clear_all_database_caches() -> None:
    """Leert alle Datenbank-Caches."""
    try:
        cache_manager = get_cache_manager()
        cache_manager.clear_all_caches()
    except Exception as e:
        logger.error(f"Fehler beim Leeren der Caches: {e}")