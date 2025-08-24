"""
Performance-Optimierung und Monitoring für den Telegram Audio Downloader.
"""

import asyncio
import gc
import time
import weakref
from collections import deque, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Deque, Dict, Optional, Tuple, Any

import psutil
from telethon.errors import FloodWaitError

from .logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance-Metriken für das Monitoring mit speichereffizienten Strukturen."""

    downloads_completed: int = 0
    downloads_failed: int = 0
    total_bytes_downloaded: int = 0
    total_download_time: float = 0.0
    # Verwende deque für gleitende Durchschnittsberechnung mit begrenzter Größe
    download_times: Deque[float] = field(default_factory=lambda: deque(maxlen=1000))
    download_speeds: Deque[float] = field(default_factory=lambda: deque(maxlen=1000))
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    disk_usage_gb: float = 0.0

    @property
    def average_speed_mbps(self) -> float:
        """Berechnet die durchschnittliche Download-Geschwindigkeit."""
        if not self.download_speeds:
            return 0.0
        return sum(self.download_speeds) / len(self.download_speeds)

    @property
    def downloads_per_minute(self) -> float:
        """Berechnet die Anzahl der Downloads pro Minute."""
        if not self.download_times:
            return 0.0
        # Nur die letzten 60 Sekunden berücksichtigen
        recent_downloads = [t for t in self.download_times if time.time() - t < 60]
        return len(recent_downloads)


@dataclass
class DownloadStatistics:
    """Statistiken für Download-Vorgänge."""
    
    files_downloaded: int = 0
    files_failed: int = 0
    total_bytes: int = 0
    total_time: float = 0.0
    average_speed: float = 0.0
    success_rate: float = 0.0
    
    def update(self, bytes_downloaded: int, time_taken: float, success: bool) -> None:
        """
        Aktualisiert die Download-Statistiken.
        
        Args:
            bytes_downloaded: Anzahl der heruntergeladenen Bytes
            time_taken: Dauer des Downloads in Sekunden
            success: Ob der Download erfolgreich war
        """
        if success:
            self.files_downloaded += 1
        else:
            self.files_failed += 1
            
        self.total_bytes += bytes_downloaded
        self.total_time += time_taken
        
        # Berechne Durchschnittsgeschwindigkeit
        if time_taken > 0:
            self.average_speed = bytes_downloaded / time_taken / (1024 * 1024)  # MB/s
            
        # Berechne Erfolgsrate
        total_files = self.files_downloaded + self.files_failed
        if total_files > 0:
            self.success_rate = (self.files_downloaded / total_files) * 100

    def get_summary(self) -> Dict[str, Any]:
        """
        Gibt eine Zusammenfassung der Statistiken zurück.
        
        Returns:
            Dictionary mit Statistikdaten
        """
        return {
            "files_downloaded": self.files_downloaded,
            "files_failed": self.files_failed,
            "total_bytes": self.total_bytes,
            "total_time": self.total_time,
            "average_speed_mbps": self.average_speed,
            "success_rate_percent": self.success_rate,
            "total_files": self.files_downloaded + self.files_failed
        }


class RateLimiter:
    """Token-Bucket Rate-Limiter für die Telegram-API."""

    def __init__(self, max_requests_per_second: float = 2.0, burst_size: int = 5):
        self.max_requests_per_second = max_requests_per_second
        self.burst_size = burst_size
        self.tokens: float = burst_size
        self.last_refill = time.time()
        self._lock = asyncio.Lock()

    async def acquire(self, weight: float = 1.0) -> None:
        """Erhält ein Token vom Bucket (blockierend)."""
        async with self._lock:
            now = time.time()
            # Tokens nachfüllen
            time_passed = now - self.last_refill
            new_tokens = time_passed * self.max_requests_per_second
            self.tokens = min(self.burst_size, self.tokens + new_tokens)
            self.last_refill = now

            # Wenn nicht genug Tokens, warten
            if self.tokens < weight:
                needed_tokens = weight - self.tokens
                wait_time = needed_tokens / self.max_requests_per_second
                logger.debug(f"Rate-Limiting: Warte {wait_time:.2f}s")
                await asyncio.sleep(wait_time)

                # Nach Wartezeit Tokens aktualisieren
                now = time.time()
                time_passed = now - self.last_refill
                new_tokens = time_passed * self.max_requests_per_second
                self.tokens = min(self.burst_size, self.tokens + new_tokens)
                self.last_refill = now

            self.tokens -= weight

    def adjust_rate(self, wait_seconds: int) -> None:
        """Passt die Rate basierend auf einem FloodWaitError an."""
        # Reduziere die Rate basierend auf der Wartezeit
        new_rate = max(0.1, 1.0 / wait_seconds)
        self.max_requests_per_second = new_rate
        logger.info(
            f"Rate-Limiter angepasst: {self.max_requests_per_second:.2f} req/s"
        )


class MemoryManager:
    """Verwaltet den Speicherverbrauch und führt Garbage Collection durch."""

    def __init__(self, max_memory_mb: int = 1024):
        self.max_memory_mb = max_memory_mb
        self.pressure_threshold_mb = max_memory_mb * 0.8
        self.gc_threshold_mb = max_memory_mb * 0.9
        # Weak-Reference-Cache für große Objekte
        self._weak_cache = weakref.WeakValueDictionary()

    def get_memory_usage(self) -> float:
        """Gibt den aktuellen Speicherverbrauch in MB zurück."""
        process = psutil.Process()
        return process.memory_info().rss / (1024 * 1024)

    def get_system_memory_info(self) -> Dict[str, float]:
        """Gibt System-Speicherinformationen zurück."""
        memory = psutil.virtual_memory()
        return {
            "total_gb": memory.total / (1024**3),
            "available_gb": memory.available / (1024**3),
            "used_percent": memory.percent,
        }

    def check_memory_pressure(self) -> bool:
        """Prüft, ob Speicherdruck besteht und führt ggf. GC durch."""
        usage_mb = self.get_memory_usage()
        system_memory = self.get_system_memory_info()

        # Warnung bei hoher Speicherbelastung
        if usage_mb > self.pressure_threshold_mb:
            logger.warning(
                f"Hoher Speicherverbrauch: {usage_mb:.1f}MB / {self.max_memory_mb}MB, "
                f"System: {system_memory['used_percent']:.1f}%"
            )

        # Aggressive GC bei sehr hohem Verbrauch
        if usage_mb > self.gc_threshold_mb:
            logger.info("Führe aggressive Garbage Collection durch...")
            return self.force_garbage_collection()

        return False

    def force_garbage_collection(self) -> int:
        """Führt eine erzwungene Garbage Collection durch."""
        # Speicher bereinigen
        collected = gc.collect()

        # Zyklische Referenzen auflösen
        cyclic_refs = gc.collect()
        total_collected = collected + cyclic_refs

        logger.info(f"Garbage Collection: {total_collected} Objekte bereinigt")
        return total_collected


def format_bytes(bytes_value: int) -> str:
    """
    Formatiert Bytes in ein lesbares Format.
    
    Args:
        bytes_value: Anzahl der Bytes
        
    Returns:
        Formatierte String-Repräsentation
    """
    if bytes_value == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size = float(bytes_value)
    
    while size >= 1024.0 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1
    
    return f"{size:.1f} {size_names[i]}"


class DiskSpaceManager:
    """Verwaltet den Festplattenspeicher und bereinigt temporäre Dateien."""

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
                "used_percent": (usage.used / usage.total) * 100,
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
    """Zentraler Performance-Monitor mit speichereffizienten Datenstrukturen."""

    def __init__(self, download_dir: Path, max_memory_mb: int = 1024):
        self.download_dir = download_dir
        self.rate_limiter = RateLimiter()
        self.memory_manager = MemoryManager(max_memory_mb)
        self.disk_manager = DiskSpaceManager(download_dir)
        self.metrics = PerformanceMetrics()

        self.start_time = time.time()
        self.last_check = time.time()
        # Begrenzte Historie für Performance-Daten
        self._performance_history = deque(maxlen=100)

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

    def after_download(self, success: bool, file_size_mb: float, duration: float) -> None:
        """Aktualisiert Metriken nach einem Download."""
        # Zeitstempel für Downloads pro Minute speichern
        self.metrics.download_times.append(time.time())
        
        if success:
            self.metrics.downloads_completed += 1
            self.metrics.total_bytes_downloaded += int(file_size_mb * 1024 * 1024)
            self.metrics.total_download_time += duration

            # Durchschnittliche Geschwindigkeit berechnen und speichern
            if duration > 0:
                speed_mbps = file_size_mb / duration
                self.metrics.download_speeds.append(speed_mbps)
        else:
            self.metrics.downloads_failed += 1

    def handle_flood_wait(self, wait_seconds: int) -> None:
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
                    self.metrics.downloads_completed
                    / max(
                        1,
                        self.metrics.downloads_completed
                        + self.metrics.downloads_failed,
                    )
                    * 100
                ),
            },
            "performance": {
                "total_gb_downloaded": self.metrics.total_bytes_downloaded / (1024**3),
                "average_speed_mbps": self.metrics.average_speed_mbps,
                "downloads_per_minute": self.metrics.downloads_per_minute,
            },
            "resources": {
                "memory_mb": self.metrics.memory_usage_mb,
                "cpu_percent": self.metrics.cpu_usage_percent,
                "disk_used_gb": self.metrics.disk_usage_gb,
                "disk_free_gb": disk_info["free_gb"],
            },
            "rate_limiting": {
                "current_rate": self.rate_limiter.max_requests_per_second,
                "tokens_available": self.rate_limiter.tokens,
            },
        }

    async def periodic_maintenance(self) -> None:
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
_performance_monitor: Optional[PerformanceMonitor] = None


def get_performance_monitor(
    download_dir: Optional[Path] = None, max_memory_mb: int = 1024
) -> Optional[PerformanceMonitor]:
    """Gibt den globalen Performance-Monitor zurück."""
    global _performance_monitor
    if _performance_monitor is None and download_dir:
        _performance_monitor = PerformanceMonitor(download_dir, max_memory_mb)
    return _performance_monitor