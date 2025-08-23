"""
Performance-Optimierungen und Resource-Management für den Telegram Audio Downloader.
"""
import asyncio
import time
import psutil
import gc
from typing import Dict, Optional, List
from dataclasses import dataclass
from pathlib import Path

from .logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class PerformanceMetrics:
    """Sammelt Performance-Metriken."""
    downloads_completed: int = 0
    downloads_failed: int = 0
    total_bytes_downloaded: int = 0
    total_download_time: float = 0.0
    average_speed_mbps: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    disk_usage_gb: float = 0.0
    active_connections: int = 0


class RateLimiter:
    """Intelligenter Rate-Limiter für Telegram-API-Aufrufe."""
    
    def __init__(self, max_requests_per_second: float = 1.0, burst_size: int = 5):
        self.max_requests_per_second = max_requests_per_second
        self.burst_size = burst_size
        self.tokens = burst_size
        self.last_update = time.time()
        self.request_history: List[float] = []
        self._lock = asyncio.Lock()
    
    async def acquire(self, weight: float = 1.0) -> None:
        """
        Erwirbt Tokens für eine API-Anfrage.
        
        Args:
            weight: Gewicht der Anfrage (größere Dateien = höheres Gewicht)
        """
        async with self._lock:
            now = time.time()
            
            # Token-Bucket auffüllen
            time_passed = now - self.last_update
            tokens_to_add = time_passed * self.max_requests_per_second
            self.tokens = min(self.burst_size, self.tokens + tokens_to_add)
            self.last_update = now
            
            # Adaptive Rate-Limiting basierend auf Historie
            if len(self.request_history) >= 10:
                recent_requests = [r for r in self.request_history if now - r < 60]  # Letzte Minute
                if len(recent_requests) > 30:  # Zu viele Anfragen
                    weight *= 1.5  # Erhöhe Gewicht
            
            # Warten, falls nicht genug Tokens
            if self.tokens < weight:
                wait_time = (weight - self.tokens) / self.max_requests_per_second
                logger.debug(f"Rate-Limiting: Warte {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
                self.tokens = 0
            else:
                self.tokens -= weight
            
            # Historie aktualisieren
            self.request_history.append(now)
            if len(self.request_history) > 100:
                self.request_history = self.request_history[-50:]  # Behalte nur die letzten 50
    
    def adjust_rate(self, flood_wait_seconds: int) -> None:
        """Passt die Rate basierend auf FloodWait-Fehlern an."""
        if flood_wait_seconds > 0:
            # Reduziere Rate dramatisch nach FloodWait
            self.max_requests_per_second = max(0.1, self.max_requests_per_second * 0.5)
            logger.warning(f"Rate-Limiting angepasst auf {self.max_requests_per_second:.2f} req/s nach FloodWait")
        else:
            # Erhöhe Rate langsam, wenn keine Probleme
            self.max_requests_per_second = min(2.0, self.max_requests_per_second * 1.1)


class MemoryManager:
    """Überwacht und optimiert Speicherverbrauch."""
    
    def __init__(self, max_memory_mb: int = 1024):
        self.max_memory_mb = max_memory_mb
        self.process = psutil.Process()
        self.gc_threshold = max_memory_mb * 0.8  # GC bei 80% der Grenze
        
    def get_memory_usage(self) -> float:
        """Gibt aktuellen Speicherverbrauch in MB zurück."""
        try:
            memory_info = self.process.memory_info()
            return memory_info.rss / (1024 * 1024)  # RSS in MB
        except Exception:
            return 0.0
    
    def check_memory_pressure(self) -> bool:
        """Prüft, ob Speicherdruck vorliegt."""
        current_mb = self.get_memory_usage()
        
        if current_mb > self.gc_threshold:
            logger.warning(f"Hoher Speicherverbrauch: {current_mb:.1f}MB (Grenze: {self.max_memory_mb}MB)")
            self.force_garbage_collection()
            return True
        
        return False
    
    def force_garbage_collection(self) -> int:
        """Erzwingt Garbage Collection und gibt freigegebenen Speicher zurück."""
        before = self.get_memory_usage()
        
        # Mehrere GC-Zyklen für bessere Bereinigung
        collected = 0
        for _ in range(3):
            collected += gc.collect()
        
        after = self.get_memory_usage()
        freed_mb = before - after
        
        if freed_mb > 1:  # Nur loggen wenn signifikant
            logger.info(f"Garbage Collection: {freed_mb:.1f}MB freigegeben")
        
        return collected
    
    def get_system_memory_info(self) -> Dict[str, float]:
        """Gibt System-Speicher-Informationen zurück."""
        virtual_memory = psutil.virtual_memory()
        return {
            "total_gb": virtual_memory.total / (1024**3),
            "available_gb": virtual_memory.available / (1024**3),
            "used_percent": virtual_memory.percent,
            "process_mb": self.get_memory_usage()
        }


class DiskSpaceManager:
    """Überwacht verfügbaren Festplattenspeicher."""
    
    def __init__(self, download_dir: Path, min_free_gb: float = 1.0):
        self.download_dir = Path(download_dir)
        self.min_free_gb = min_free_gb
    
    def get_disk_usage(self) -> Dict[str, float]:
        """Gibt Festplattennutzung zurück."""
        try:
            usage = psutil.disk_usage(str(self.download_dir))
            return {
                "total_gb": usage.total / (1024**3),
                "free_gb": usage.free / (1024**3),
                "used_gb": usage.used / (1024**3),
                "used_percent": (usage.used / usage.total) * 100
            }
        except Exception as e:
            logger.error(f"Fehler beim Ermitteln der Festplattennutzung: {e}")
            return {"total_gb": 0, "free_gb": 0, "used_gb": 0, "used_percent": 0}
    
    def check_disk_space(self, required_mb: float = 0) -> bool:
        """
        Prüft, ob genug Festplattenspeicher verfügbar ist.
        
        Args:
            required_mb: Benötigter Speicher in MB
            
        Returns:
            True wenn genug Speicher verfügbar
        """
        disk_info = self.get_disk_usage()
        free_gb = disk_info["free_gb"]
        required_gb = required_mb / 1024
        
        if free_gb < (self.min_free_gb + required_gb):
            logger.error(
                f"Nicht genug Festplattenspeicher: {free_gb:.1f}GB frei, "
                f"benötigt: {required_gb:.1f}GB + {self.min_free_gb}GB Puffer"
            )
            return False
        
        return True
    
    def cleanup_temp_files(self) -> int:
        """Bereinigt temporäre Dateien und gibt Anzahl zurück."""
        cleaned = 0
        try:
            # .partial Dateien bereinigen
            for partial_file in self.download_dir.glob("*.partial"):
                if partial_file.is_file():
                    partial_file.unlink()
                    cleaned += 1
            
            # Alte Temp-Dateien bereinigen
            for temp_file in self.download_dir.glob("*.tmp"):
                if temp_file.is_file():
                    temp_file.unlink()
                    cleaned += 1
                    
            if cleaned > 0:
                logger.info(f"Temp-Dateien bereinigt: {cleaned} Dateien")
                
        except Exception as e:
            logger.error(f"Fehler beim Bereinigen von Temp-Dateien: {e}")
        
        return cleaned


class PerformanceMonitor:
    """Zentraler Performance-Monitor."""
    
    def __init__(self, download_dir: Path, max_memory_mb: int = 1024):
        self.download_dir = download_dir
        self.rate_limiter = RateLimiter()
        self.memory_manager = MemoryManager(max_memory_mb)
        self.disk_manager = DiskSpaceManager(download_dir)
        self.metrics = PerformanceMetrics()
        
        self.start_time = time.time()
        self.last_check = time.time()
        
    async def before_download(self, file_size_mb: float) -> bool:
        """
        Prüfungen vor einem Download.
        
        Args:
            file_size_mb: Größe der zu downloadenden Datei in MB
            
        Returns:
            True wenn Download fortgesetzt werden kann
        """
        # Rate-Limiting
        weight = max(1.0, file_size_mb / 10)  # Größere Dateien = höheres Gewicht
        await self.rate_limiter.acquire(weight)
        
        # Speicher-Check
        if self.memory_manager.check_memory_pressure():
            await asyncio.sleep(1)  # Kurze Pause nach GC
        
        # Festplatten-Check
        if not self.disk_manager.check_disk_space(file_size_mb):
            return False
        
        return True
    
    def after_download(self, success: bool, file_size_mb: float, duration: float):
        """Aktualisiert Metriken nach einem Download."""
        if success:
            self.metrics.downloads_completed += 1
            self.metrics.total_bytes_downloaded += int(file_size_mb * 1024 * 1024)
            self.metrics.total_download_time += duration
            
            # Durchschnittliche Geschwindigkeit berechnen
            if duration > 0:
                speed_mbps = file_size_mb / duration
                self.metrics.average_speed_mbps = (
                    (self.metrics.average_speed_mbps * (self.metrics.downloads_completed - 1) + speed_mbps)
                    / self.metrics.downloads_completed
                )
        else:
            self.metrics.downloads_failed += 1
    
    def handle_flood_wait(self, wait_seconds: int):
        """Behandelt FloodWait-Fehler."""
        self.rate_limiter.adjust_rate(wait_seconds)
    
    def get_performance_report(self) -> Dict:
        """Gibt einen Performance-Bericht zurück."""
        now = time.time()
        uptime = now - self.start_time
        
        # System-Metriken aktualisieren
        self.metrics.memory_usage_mb = self.memory_manager.get_memory_usage()
        self.metrics.cpu_usage_percent = psutil.cpu_percent(interval=0.1)
        
        disk_info = self.disk_manager.get_disk_usage()
        self.metrics.disk_usage_gb = disk_info["used_gb"]
        
        return {
            "uptime_seconds": uptime,
            "downloads": {
                "completed": self.metrics.downloads_completed,
                "failed": self.metrics.downloads_failed,
                "success_rate": (
                    self.metrics.downloads_completed / 
                    max(1, self.metrics.downloads_completed + self.metrics.downloads_failed) * 100
                )
            },
            "performance": {
                "total_gb_downloaded": self.metrics.total_bytes_downloaded / (1024**3),
                "average_speed_mbps": self.metrics.average_speed_mbps,
                "downloads_per_minute": (
                    self.metrics.downloads_completed / max(1, uptime / 60)
                )
            },
            "resources": {
                "memory_mb": self.metrics.memory_usage_mb,
                "cpu_percent": self.metrics.cpu_usage_percent,
                "disk_used_gb": self.metrics.disk_usage_gb,
                "disk_free_gb": disk_info["free_gb"]
            },
            "rate_limiting": {
                "current_rate": self.rate_limiter.max_requests_per_second,
                "tokens_available": self.rate_limiter.tokens
            }
        }
    
    async def periodic_maintenance(self):
        """Führt periodische Wartungsaufgaben durch."""
        # Alle 5 Minuten
        if time.time() - self.last_check > 300:
            self.last_check = time.time()
            
            # Memory-Check
            self.memory_manager.check_memory_pressure()
            
            # Temp-Dateien bereinigen
            self.disk_manager.cleanup_temp_files()
            
            # Performance-Report loggen
            report = self.get_performance_report()
            logger.info(
                f"PERFORMANCE: {report['downloads']['completed']} Downloads, "
                f"{report['performance']['average_speed_mbps']:.1f} MB/s avg, "
                f"{report['resources']['memory_mb']:.0f}MB RAM"
            )


# Globale Performance-Monitor-Instanz
_performance_monitor = None

def get_performance_monitor(download_dir: Optional[Path] = None, max_memory_mb: int = 1024) -> Optional[PerformanceMonitor]:
    """Gibt den globalen Performance-Monitor zurück."""
    global _performance_monitor
    if _performance_monitor is None and download_dir:
        _performance_monitor = PerformanceMonitor(download_dir, max_memory_mb)
    return _performance_monitor