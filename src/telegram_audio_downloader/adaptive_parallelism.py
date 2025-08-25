"""
Adaptive Parallelisierung für den Telegram Audio Downloader.

Dynamische Anpassung der parallelen Downloads basierend auf Systemressourcen:
- CPU-Auslastung
- Verfügbarer Arbeitsspeicher
- Netzwerklatenz
- Server-Antwortzeiten
- Aktive Systemlast
"""

import asyncio
import time
import psutil
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from pathlib import Path

from .logging_config import get_logger
from .performance import get_performance_monitor

logger = get_logger(__name__)


@dataclass
class SystemResources:
    """Aktuelle Systemressourcen-Metriken."""
    cpu_percent: float = 0.0
    memory_available_mb: float = 0.0
    memory_percent: float = 0.0
    disk_io_read_mb: float = 0.0
    disk_io_write_mb: float = 0.0
    network_bytes_sent: float = 0.0
    network_bytes_recv: float = 0.0
    timestamp: float = field(default_factory=time.time)


class AdaptiveParallelismController:
    """Steuert die adaptive Parallelisierung basierend auf Systemressourcen."""
    
    def __init__(
        self,
        download_dir: Path,
        initial_concurrent_downloads: int = 3,
        min_concurrent_downloads: int = 1,
        max_concurrent_downloads: int = 10,
        cpu_threshold_high: float = 80.0,
        cpu_threshold_low: float = 50.0,
        memory_threshold_high: float = 85.0,
        memory_threshold_low: float = 70.0,
        network_latency_threshold_ms: float = 200.0
    ):
        """
        Initialisiert den AdaptiveParallelismController.
        
        Args:
            download_dir: Download-Verzeichnis
            initial_concurrent_downloads: Initiale Anzahl paralleler Downloads
            min_concurrent_downloads: Minimale Anzahl paralleler Downloads
            max_concurrent_downloads: Maximale Anzahl paralleler Downloads
            cpu_threshold_high: CPU-Schwellenwert für Reduzierung (%)
            cpu_threshold_low: CPU-Schwellenwert für Erhöhung (%)
            memory_threshold_high: Speicher-Schwellenwert für Reduzierung (%)
            memory_threshold_low: Speicher-Schwellenwert für Erhöhung (%)
            network_latency_threshold_ms: Netzwerk-Latenz-Schwellenwert (ms)
        """
        self.download_dir = Path(download_dir)
        self.current_concurrent_downloads = initial_concurrent_downloads
        self.min_concurrent_downloads = min_concurrent_downloads
        self.max_concurrent_downloads = max_concurrent_downloads
        self.cpu_threshold_high = cpu_threshold_high
        self.cpu_threshold_low = cpu_threshold_low
        self.memory_threshold_high = memory_threshold_high
        self.memory_threshold_low = memory_threshold_low
        self.network_latency_threshold_ms = network_latency_threshold_ms
        
        # Semaphore for current number of parallel downloads
        self.semaphore = asyncio.Semaphore(initial_concurrent_downloads)
        
        # Systemressourcen-Monitoring
        self.last_resources: Optional[SystemResources] = None
        self.last_check_time = 0.0
        self.check_interval = 5.0  # Sekunden
        
        # Performance-Monitor
        self.performance_monitor = get_performance_monitor(download_dir)
        
        # Historical data for intelligent adaptation
        self.download_speed_history = []
        self.resource_history = []
        self.max_history_size = 100
        
        logger.info(
            f"AdaptiveParallelismController initialisiert: "
            f"Downloads={initial_concurrent_downloads}, "
            f"Min={min_concurrent_downloads}, Max={max_concurrent_downloads}"
        )
    
    def _get_system_resources(self) -> SystemResources:
        """Erfasst aktuelle Systemressourcen."""
        try:
            # CPU-Auslastung
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # Speicherinformationen
            memory = psutil.virtual_memory()
            memory_available_mb = memory.available / (1024 * 1024)
            memory_percent = memory.percent
            
            # Festplatten-I/O
            disk_io = psutil.disk_io_counters()
            disk_io_read_mb = disk_io.read_bytes / (1024 * 1024) if disk_io else 0.0
            disk_io_write_mb = disk_io.write_bytes / (1024 * 1024) if disk_io else 0.0
            
            # Netzwerk-I/O
            net_io = psutil.net_io_counters()
            network_bytes_sent = net_io.bytes_sent if net_io else 0.0
            network_bytes_recv = net_io.bytes_recv if net_io else 0.0
            
            return SystemResources(
                cpu_percent=cpu_percent,
                memory_available_mb=memory_available_mb,
                memory_percent=memory_percent,
                disk_io_read_mb=disk_io_read_mb,
                disk_io_write_mb=disk_io_write_mb,
                network_bytes_sent=network_bytes_sent,
                network_bytes_recv=network_bytes_recv
            )
        except Exception as e:
            logger.error(f"Fehler beim Erfassen der Systemressourcen: {e}")
            # Fall back to default values
            return SystemResources()
    
    def _calculate_optimal_concurrent_downloads(self, resources: SystemResources) -> int:
        """
        Calculates the optimal number of parallel downloads based on system resources.
        
        Args:
            resources: Current system resources
            
        Returns:
            Optimal number of parallel downloads
        """
        optimal_count = self.current_concurrent_downloads
        
        # CPU-basierte Anpassung
        if resources.cpu_percent > self.cpu_threshold_high:
            # CPU usage high - reduce
            optimal_count = max(self.min_concurrent_downloads, optimal_count - 1)
            logger.debug(f"CPU-Auslastung hoch ({resources.cpu_percent:.1f}%): Reduziere auf {optimal_count}")
        elif resources.cpu_percent < self.cpu_threshold_low and optimal_count < self.max_concurrent_downloads:
            # CPU usage low - increase
            optimal_count = min(self.max_concurrent_downloads, optimal_count + 1)
            logger.debug(f"CPU-Auslastung niedrig ({resources.cpu_percent:.1f}%): Erhöhe auf {optimal_count}")
        
        # Speicher-basierte Anpassung
        if resources.memory_percent > self.memory_threshold_high:
            # Memory usage high - reduce
            optimal_count = max(self.min_concurrent_downloads, optimal_count - 1)
            logger.debug(f"Speicherauslastung hoch ({resources.memory_percent:.1f}%): Reduziere auf {optimal_count}")
        elif resources.memory_percent < self.memory_threshold_low and optimal_count < self.max_concurrent_downloads:
            # Memory usage low - increase
            optimal_count = min(self.max_concurrent_downloads, optimal_count + 1)
            logger.debug(f"Speicherauslastung niedrig ({resources.memory_percent:.1f}%): Erhöhe auf {optimal_count}")
        
        # Netzwerk-basierte Anpassung (vereinfacht)
        # In a real implementation, we would measure ping times here
        # For now, we use a simplified assumption
        
        return optimal_count
    
    async def update_parallelism(self) -> None:
        """Updates parallelism based on system resources."""
        current_time = time.time()
        
        # Only update every check_interval seconds
        if current_time - self.last_check_time < self.check_interval:
            return
        
        self.last_check_time = current_time
        
        # Capture system resources
        resources = self._get_system_resources()
        
        # Save historical data
        self.resource_history.append(resources)
        if len(self.resource_history) > self.max_history_size:
            self.resource_history.pop(0)
        
        # Calculate optimal number of parallel downloads
        optimal_count = self._calculate_optimal_concurrent_downloads(resources)
        
        # Update semaphore when count changes
        if optimal_count != self.current_concurrent_downloads:
            logger.info(
                f"Changing parallel downloads from {self.current_concurrent_downloads} to {optimal_count} "
                f"(CPU: {resources.cpu_percent:.1f}%, RAM: {resources.memory_percent:.1f}%)"
            )
            
            # Create new semaphore
            self.semaphore = asyncio.Semaphore(optimal_count)
            self.current_concurrent_downloads = optimal_count
            
            # Update performance monitor
            if self.performance_monitor:
                # Here we could send additional metrics to the performance monitor
                pass
    
    def get_semaphore(self) -> asyncio.Semaphore:
        """
        Returns the current semaphore.
        
        Returns:
            asyncio.Semaphore for download control
        """
        return self.semaphore
    
    def get_current_concurrent_downloads(self) -> int:
        """
        Returns the current number of parallel downloads.
        
        Returns:
            Current number of parallel downloads
        """
        return self.current_concurrent_downloads
    
    def record_download_speed(self, speed_mbps: float) -> None:
        """
        Records a download speed.
        
        Args:
            speed_mbps: Download speed in MB/s
        """
        self.download_speed_history.append(speed_mbps)
        if len(self.download_speed_history) > self.max_history_size:
            self.download_speed_history.pop(0)
    
    def get_average_download_speed(self) -> float:
        """
        Calculates the average download speed.
        
        Returns:
            Average download speed in MB/s
        """
        if not self.download_speed_history:
            return 0.0
        return sum(self.download_speed_history) / len(self.download_speed_history)


def get_parallelism_manager(download_dir: Path = Path(".")):
    """
    Returns an instance of AdaptiveParallelismController.
    
    Args:
        download_dir: Download directory
        
    Returns:
        AdaptiveParallelismController instance
    """
    return AdaptiveParallelismController(download_dir)