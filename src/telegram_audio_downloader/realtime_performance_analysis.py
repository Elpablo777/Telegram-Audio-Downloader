"""
Echtzeit-Performance-Analyse für den Telegram Audio Downloader.

Umfasst:
- Download-Geschwindigkeit
- Fehlerraten
- Systemressourcen
- Netzwerklatenz
- Anwendungsmetriken
"""

import time
import asyncio
import psutil
from collections import deque, defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import json

from .logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance-Metriken in Echtzeit."""
    timestamp: float = field(default_factory=time.time)
    download_speed_mbps: float = 0.0
    error_rate_percent: float = 0.0
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    network_latency_ms: float = 0.0
    disk_io_read_mb: float = 0.0
    disk_io_write_mb: float = 0.0
    active_downloads: int = 0
    queue_length: int = 0


class RealtimePerformanceAnalyzer:
    """Analysiert die Performance in Echtzeit."""
    
    def __init__(self, download_dir: Path, history_size: int = 1000):
        """
        Initialisiert den RealtimePerformanceAnalyzer.
        
        Args:
            download_dir: Download-Verzeichnis
            history_size: Maximale Größe der Metrik-Historie
        """
        self.download_dir = Path(download_dir)
        self.history_size = history_size
        
        # Metrik-Historie
        self.metrics_history = deque(maxlen=history_size)
        self.error_history = deque(maxlen=history_size)
        self.speed_history = deque(maxlen=history_size)
        
        # Aktuelle Metriken
        self.current_metrics = PerformanceMetrics()
        
        # Zähler für Statistiken
        self.total_downloads = 0
        self.successful_downloads = 0
        self.failed_downloads = 0
        self.total_errors = 0
        
        # Zeitstempel für letzte Aktualisierung
        self.last_update = 0.0
        self.update_interval = 1.0  # Sekunden
        
        # Alarm-Schwellenwerte
        self.speed_threshold_low = 1.0  # MB/s
        self.error_rate_threshold_high = 5.0  # Prozent
        self.cpu_threshold_high = 85.0  # Prozent
        self.memory_threshold_high = 800.0  # MB
        
        logger.info("RealtimePerformanceAnalyzer initialisiert")
    
    def record_download_start(self) -> None:
        """Zeichnet den Start eines Downloads auf."""
        self.total_downloads += 1
        self.current_metrics.active_downloads += 1
    
    def record_download_completion(self, success: bool, file_size_mb: float, duration: float) -> None:
        """
        Zeichnet den Abschluss eines Downloads auf.
        
        Args:
            success: Ob der Download erfolgreich war
            file_size_mb: Dateigröße in MB
            duration: Download-Dauer in Sekunden
        """
        self.current_metrics.active_downloads -= 1
        
        if success:
            self.successful_downloads += 1
            if duration > 0:
                speed_mbps = file_size_mb / duration
                self.speed_history.append(speed_mbps)
                self.current_metrics.download_speed_mbps = speed_mbps
        else:
            self.failed_downloads += 1
            
        # Aktualisiere Fehlerrate
        total_completed = self.successful_downloads + self.failed_downloads
        if total_completed > 0:
            self.current_metrics.error_rate_percent = (self.failed_downloads / total_completed) * 100
    
    def record_error(self, error_type: str, context: str) -> None:
        """
        Zeichnet einen Fehler auf.
        
        Args:
            error_type: Typ des Fehlers
            context: Kontext des Fehlers
        """
        self.total_errors += 1
        self.error_history.append({
            'timestamp': time.time(),
            'type': error_type,
            'context': context
        })
        
        # Aktualisiere Fehlerrate
        total_completed = self.successful_downloads + self.failed_downloads
        if total_completed > 0:
            self.current_metrics.error_rate_percent = (self.failed_downloads / total_completed) * 100
    
    async def update_system_metrics(self) -> None:
        """Aktualisiert die System-Metriken."""
        current_time = time.time()
        
        # Nur alle update_interval Sekunden aktualisieren
        if current_time - self.last_update < self.update_interval:
            return
            
        self.last_update = current_time
        
        try:
            # CPU-Auslastung
            self.current_metrics.cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # Speicherauslastung
            memory = psutil.virtual_memory()
            self.current_metrics.memory_mb = memory.rss / (1024 * 1024) if hasattr(memory, 'rss') else memory.used / (1024 * 1024)
            
            # Festplatten-I/O
            disk_io = psutil.disk_io_counters()
            if disk_io:
                self.current_metrics.disk_io_read_mb = disk_io.read_bytes / (1024 * 1024)
                self.current_metrics.disk_io_write_mb = disk_io.write_bytes / (1024 * 1024)
            
            # Netzwerk-I/O (vereinfacht)
            net_io = psutil.net_io_counters()
            if net_io:
                self.current_metrics.network_latency_ms = 0.0  # In einer echten Implementierung würden wir Ping messen
            
            # Historie aktualisieren
            self.metrics_history.append(self.current_metrics)
            
        except Exception as e:
            logger.error(f"Fehler beim Aktualisieren der System-Metriken: {e}")
    
    def get_current_metrics(self) -> PerformanceMetrics:
        """
        Gibt die aktuellen Performance-Metriken zurück.
        
        Returns:
            Aktuelle Performance-Metriken
        """
        return self.current_metrics
    
    def get_average_speed(self) -> float:
        """
        Berechnet die durchschnittliche Download-Geschwindigkeit.
        
        Returns:
            Durchschnittliche Geschwindigkeit in MB/s
        """
        if not self.speed_history:
            return 0.0
        return sum(self.speed_history) / len(self.speed_history)
    
    def get_error_statistics(self) -> Dict[str, int]:
        """
        Gibt Fehlerstatistiken zurück.
        
        Returns:
            Dictionary mit Fehlerstatistiken
        """
        error_counts = defaultdict(int)
        for error in self.error_history:
            error_counts[error['type']] += 1
        return dict(error_counts)
    
    def check_performance_alerts(self) -> List[str]:
        """
        Prüft auf Performance-Probleme und gibt Warnungen zurück.
        
        Returns:
            Liste von Warnmeldungen
        """
        alerts = []
        
        # Geschwindigkeitswarnung
        if self.current_metrics.download_speed_mbps < self.speed_threshold_low:
            alerts.append(f"Niedrige Download-Geschwindigkeit: {self.current_metrics.download_speed_mbps:.2f} MB/s")
        
        # Fehlerwarnung
        if self.current_metrics.error_rate_percent > self.error_rate_threshold_high:
            alerts.append(f"Hohe Fehlerrate: {self.current_metrics.error_rate_percent:.2f}%")
        
        # CPU-Warnung
        if self.current_metrics.cpu_percent > self.cpu_threshold_high:
            alerts.append(f"Hohe CPU-Auslastung: {self.current_metrics.cpu_percent:.1f}%")
        
        # Speicherwarnung
        if self.current_metrics.memory_mb > self.memory_threshold_high:
            alerts.append(f"Hohe Speicherauslastung: {self.current_metrics.memory_mb:.0f} MB")
        
        return alerts
    
    def get_performance_report(self) -> Dict[str, any]:
        """
        Erstellt einen detaillierten Performance-Bericht.
        
        Returns:
            Dictionary mit Performance-Daten
        """
        return {
            'timestamp': time.time(),
            'current_metrics': {
                'download_speed_mbps': self.current_metrics.download_speed_mbps,
                'error_rate_percent': self.current_metrics.error_rate_percent,
                'cpu_percent': self.current_metrics.cpu_percent,
                'memory_mb': self.current_metrics.memory_mb,
                'network_latency_ms': self.current_metrics.network_latency_ms,
                'active_downloads': self.current_metrics.active_downloads,
                'queue_length': self.current_metrics.queue_length
            },
            'statistics': {
                'total_downloads': self.total_downloads,
                'successful_downloads': self.successful_downloads,
                'failed_downloads': self.failed_downloads,
                'total_errors': self.total_errors,
                'average_speed_mbps': self.get_average_speed()
            },
            'error_distribution': self.get_error_statistics(),
            'alerts': self.check_performance_alerts()
        }
    
    def export_metrics_to_file(self, file_path: Path) -> None:
        """
        Exportiert die Metriken in eine JSON-Datei.
        
        Args:
            file_path: Pfad zur Exportdatei
        """
        try:
            report = self.get_performance_report()
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            logger.info(f"Performance-Metriken exportiert nach {file_path}")
        except Exception as e:
            logger.error(f"Fehler beim Exportieren der Metriken: {e}")
    
    async def start_monitoring(self) -> None:
        """Startet das kontinuierliche Monitoring."""
        logger.info("Performance-Monitoring gestartet")
        
        while True:
            try:
                await self.update_system_metrics()
                
                # Prüfe auf Warnungen
                alerts = self.check_performance_alerts()
                if alerts:
                    for alert in alerts:
                        logger.warning(f"PERFORMANCE ALERT: {alert}")
                
                # Warte bis zur nächsten Aktualisierung
                await asyncio.sleep(self.update_interval)
                
            except asyncio.CancelledError:
                logger.info("Performance-Monitoring abgebrochen")
                break
            except Exception as e:
                logger.error(f"Fehler im Performance-Monitoring: {e}")
                await asyncio.sleep(self.update_interval)
    
    def get_trend_analysis(self, window_size: int = 10) -> Dict[str, str]:
        """
        Führt eine Trendanalyse durch.
        
        Args:
            window_size: Anzahl der Datenpunkte für die Analyse
            
        Returns:
            Dictionary mit Trend-Informationen
        """
        if len(self.metrics_history) < window_size:
            return {'status': 'insufficient_data'}
        
        # Hole die letzten window_size Datenpunkte
        recent_metrics = list(self.metrics_history)[-window_size:]
        
        # Geschwindigkeitstrend analysieren
        speeds = [m.download_speed_mbps for m in recent_metrics]
        if len(speeds) >= 2:
            speed_trend = 'improving' if speeds[-1] > speeds[0] else 'degrading' if speeds[-1] < speeds[0] else 'stable'
        else:
            speed_trend = 'unknown'
        
        # Fehlerquotentrend analysieren
        error_rates = [m.error_rate_percent for m in recent_metrics]
        if len(error_rates) >= 2:
            error_trend = 'improving' if error_rates[-1] < error_rates[0] else 'degrading' if error_rates[-1] > error_rates[0] else 'stable'
        else:
            error_trend = 'unknown'
        
        return {
            'speed_trend': speed_trend,
            'error_trend': error_trend,
            'data_points': len(recent_metrics)
        }