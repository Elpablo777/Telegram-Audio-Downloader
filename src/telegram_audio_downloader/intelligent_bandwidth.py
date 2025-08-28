"""
Intelligente Bandbreitensteuerung für den Telegram Audio Downloader.

Dynamische Anpassung basierend auf:
- Netzwerklatenz
- Serverlast
- Systemressourcen
- Benutzeraktivität
"""

import asyncio
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import psutil
import statistics

from .logging_config import get_logger
from .models import AudioFile
from .config import Config

logger = get_logger(__name__)


@dataclass
class BandwidthMetrics:
    """Metriken für die Bandbreitenmessung."""
    timestamp: datetime = field(default_factory=datetime.now)
    download_speed_kbps: float = 0.0
    latency_ms: float = 0.0
    packet_loss_percent: float = 0.0
    concurrent_downloads: int = 0
    system_cpu_percent: float = 0.0
    system_memory_percent: float = 0.0
    system_disk_io: float = 0.0


@dataclass
class AdaptiveSettings:
    """Adaptive Einstellungen für die Bandbreitensteuerung."""
    max_concurrent_downloads: int = 5
    chunk_size: int = 8192
    timeout_seconds: int = 30
    retry_delay: int = 5
    max_retries: int = 3
    bandwidth_limit_kbps: Optional[int] = None  # Kein Limit wenn None


class IntelligentBandwidthController:
    """Verwaltet die intelligente Bandbreitensteuerung."""
    
    def __init__(self, config: Config):
        """
        Initialisiert den IntelligentBandwidthController.
        
        Args:
            config: Konfigurationsobjekt
        """
        self.config = config
        self.metrics_history: List[BandwidthMetrics] = []
        self.adaptive_settings = AdaptiveSettings()
        self.active_downloads: Dict[str, datetime] = {}
        self.performance_baselines: Dict[str, float] = {}
        self.last_adjustment_time = datetime.now()
        self.adjustment_interval = timedelta(seconds=30)  # Alle 30 Sekunden anpassen
        
        # Initialisiere mit den Konfigurationswerten
        self.adaptive_settings.max_concurrent_downloads = config.max_concurrent_downloads
        self.adaptive_settings.timeout_seconds = 30  # Standardwert
        self.adaptive_settings.retry_delay = config.retry_delay
        self.adaptive_settings.max_retries = config.max_retries
        
        logger.info("IntelligentBandwidthController initialisiert")
    
    def collect_metrics(self) -> BandwidthMetrics:
        """
        Sammelt aktuelle System- und Netzwerkmetriken.
        
        Returns:
            BandwidthMetrics-Objekt mit aktuellen Metriken
        """
        try:
            # Systemmetriken sammeln
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            disk_io = psutil.disk_io_counters()
            disk_io_rate = disk_io.read_bytes + disk_io.write_bytes if disk_io else 0
            
            # Netzwerkmetriken (vereinfacht)
            # In einer echten Implementierung würden wir hier
            # Ping-Zeiten und Paketverlust messen
            latency_ms = self._estimate_network_latency()
            packet_loss_percent = self._estimate_packet_loss()
            
            # Download-Metriken
            concurrent_downloads = len(self.active_downloads)
            download_speed_kbps = self._calculate_current_download_speed()
            
            metrics = BandwidthMetrics(
                download_speed_kbps=download_speed_kbps,
                latency_ms=latency_ms,
                packet_loss_percent=packet_loss_percent,
                concurrent_downloads=concurrent_downloads,
                system_cpu_percent=cpu_percent,
                system_memory_percent=memory_percent,
                system_disk_io=disk_io_rate
            )
            
            # Füge zu Historie hinzu (max. 100 Einträge)
            self.metrics_history.append(metrics)
            if len(self.metrics_history) > 100:
                self.metrics_history.pop(0)
            
            logger.debug(f"Metriken gesammelt: {metrics}")
            return metrics
            
        except Exception as e:
            logger.error(f"Fehler beim Sammeln von Metriken: {e}")
            # Rückfall auf Standardmetriken
            return BandwidthMetrics()
    
    def _estimate_network_latency(self) -> float:
        """
        Schätzt die Netzwerklatenz (vereinfachte Implementierung).
        
        Returns:
            Geschätzte Latenz in Millisekunden
        """
        # In einer echten Implementierung würden wir hier
        # echte Ping-Messungen durchführen
        # Für dieses Beispiel verwenden wir einen simulierten Wert
        if self.metrics_history:
            # Basierend auf der Download-Geschwindigkeit schätzen
            recent_speeds = [m.download_speed_kbps for m in self.metrics_history[-10:]]
            if recent_speeds:
                avg_speed = sum(recent_speeds) / len(recent_speeds)
                # Höhere Geschwindigkeit = niedrigere Latenz (vereinfacht)
                return max(10.0, 200.0 - (avg_speed / 100.0))
        
        return 50.0  # Standardwert
    
    def _estimate_packet_loss(self) -> float:
        """
        Schätzt den Paketverlust (vereinfachte Implementierung).
        
        Returns:
            Geschätzter Paketverlust in Prozent
        """
        # In einer echten Implementierung würden wir hier
        # echte Paketverlustmessungen durchführen
        if self.metrics_history:
            # Basierend auf der Systemauslastung schätzen
            recent_cpu = [m.system_cpu_percent for m in self.metrics_history[-10:]]
            if recent_cpu:
                avg_cpu = sum(recent_cpu) / len(recent_cpu)
                # Höhere CPU-Auslastung = höherer Paketverlust (vereinfacht)
                return min(5.0, avg_cpu / 20.0)
        
        return 0.1  # Standardwert
    
    def _calculate_current_download_speed(self) -> float:
        """
        Berechnet die aktuelle Download-Geschwindigkeit.
        
        Returns:
            Download-Geschwindigkeit in KB/s
        """
        if len(self.metrics_history) < 2:
            return 0.0
        
        # Berechne Durchschnittsgeschwindigkeit der letzten 10 Messungen
        recent_metrics = self.metrics_history[-10:]
        speeds = [m.download_speed_kbps for m in recent_metrics if m.download_speed_kbps > 0]
        
        if speeds:
            return sum(speeds) / len(speeds)
        
        return 0.0
    
    def should_adjust_settings(self) -> bool:
        """
        Prüft, ob eine Anpassung der Einstellungen erforderlich ist.
        
        Returns:
            True, wenn eine Anpassung erforderlich ist
        """
        now = datetime.now()
        time_since_last_adjustment = now - self.last_adjustment_time
        
        # Anpassung alle 30 Sekunden oder bei hoher Systemauslastung
        if time_since_last_adjustment >= self.adjustment_interval:
            return True
        
        # Sofortige Anpassung bei kritischer Auslastung
        if self.metrics_history:
            latest = self.metrics_history[-1]
            if (latest.system_cpu_percent > 90.0 or 
                latest.system_memory_percent > 90.0):
                return True
        
        return False
    
    def adjust_settings(self) -> None:
        """
        Passt die Einstellungen basierend auf den aktuellen Metriken an.
        """
        if not self.should_adjust_settings():
            return
        
        try:
            metrics = self.collect_metrics()
            
            # Speichere die aktuelle Zeit der Anpassung
            self.last_adjustment_time = datetime.now()
            
            # Anpassung der maximalen gleichzeitigen Downloads
            self._adjust_concurrent_downloads(metrics)
            
            # Anpassung der Chunk-Größe
            self._adjust_chunk_size(metrics)
            
            # Anpassung der Timeouts
            self._adjust_timeouts(metrics)
            
            # Anpassung der Wiederholungsversuche
            self._adjust_retry_settings(metrics)
            
            # Anpassung des Bandbreitenlimits
            self._adjust_bandwidth_limit(metrics)
            
            logger.info(f"Einstellungen angepasst: {self.adaptive_settings}")
            
        except Exception as e:
            logger.error(f"Fehler bei der Anpassung der Einstellungen: {e}")
    
    def _adjust_concurrent_downloads(self, metrics: BandwidthMetrics) -> None:
        """
        Passt die maximale Anzahl gleichzeitiger Downloads an.
        
        Args:
            metrics: Aktuelle Metriken
        """
        current = self.adaptive_settings.max_concurrent_downloads
        config_max = self.config.max_concurrent_downloads
        
        # Reduziere bei hoher Systemauslastung
        if metrics.system_cpu_percent > 80.0 or metrics.system_memory_percent > 80.0:
            new_concurrent = max(1, current - 1)
        # Erhöhe bei niedriger Auslastung und guter Netzwerkleistung
        elif (metrics.system_cpu_percent < 50.0 and metrics.system_memory_percent < 50.0 and
              metrics.latency_ms < 100.0 and metrics.packet_loss_percent < 1.0):
            new_concurrent = min(config_max, current + 1)
        else:
            # Keine Änderung
            return
        
        # Stelle sicher, dass der Wert im gültigen Bereich bleibt
        new_concurrent = max(1, min(config_max, new_concurrent))
        
        if new_concurrent != current:
            self.adaptive_settings.max_concurrent_downloads = new_concurrent
            logger.info(f"Max. gleichzeitige Downloads angepasst: {new_concurrent}")
    
    def _adjust_chunk_size(self, metrics: BandwidthMetrics) -> None:
        """
        Passt die Chunk-Größe an.
        
        Args:
            metrics: Aktuelle Metriken
        """
        current = self.adaptive_settings.chunk_size
        config_chunk = self.config.chunk_size
        
        # Reduziere bei hoher Latenz
        if metrics.latency_ms > 200.0:
            new_chunk = max(1024, current // 2)
        # Erhöhe bei niedriger Latenz und guter Bandbreite
        elif metrics.latency_ms < 50.0 and metrics.download_speed_kbps > 1000.0:
            new_chunk = min(config_chunk * 2, current * 2)
        else:
            # Keine Änderung
            return
        
        # Stelle sicher, dass der Wert im gültigen Bereich bleibt
        new_chunk = max(1024, min(config_chunk * 4, new_chunk))
        
        if new_chunk != current:
            self.adaptive_settings.chunk_size = new_chunk
            logger.info(f"Chunk-Größe angepasst: {new_chunk}")
    
    def _adjust_timeouts(self, metrics: BandwidthMetrics) -> None:
        """
        Passt die Timeout-Einstellungen an.
        
        Args:
            metrics: Aktuelle Metriken
        """
        current = self.adaptive_settings.timeout_seconds
        config_timeout = self.config.timeout
        
        # Erhöhe bei hoher Latenz
        if metrics.latency_ms > 200.0:
            new_timeout = min(config_timeout * 2, current + 10)
        # Reduziere bei niedriger Latenz
        elif metrics.latency_ms < 50.0:
            new_timeout = max(10, current - 5)
        else:
            # Keine Änderung
            return
        
        if new_timeout != current:
            self.adaptive_settings.timeout_seconds = new_timeout
            logger.info(f"Timeout angepasst: {new_timeout}s")
    
    def _adjust_retry_settings(self, metrics: BandwidthMetrics) -> None:
        """
        Passt die Wiederholungseinstellungen an.
        
        Args:
            metrics: Aktuelle Metriken
        """
        current_delay = self.adaptive_settings.retry_delay
        current_max = self.adaptive_settings.max_retries
        config_delay = self.config.retry_delay
        config_max = self.config.max_retries
        
        # Anpassung des Wiederholungsverzögerung
        if metrics.latency_ms > 200.0 or metrics.packet_loss_percent > 2.0:
            # Erhöhe die Wartezeit bei schlechten Netzwerkbedingungen
            new_delay = min(config_delay * 3, current_delay + 5)
        elif metrics.latency_ms < 50.0 and metrics.packet_loss_percent < 0.5:
            # Reduziere die Wartezeit bei guten Bedingungen
            new_delay = max(1, current_delay - 1)
        else:
            # Keine Änderung
            new_delay = current_delay
        
        # Anpassung der maximalen Wiederholungen
        if metrics.packet_loss_percent > 3.0:
            # Erhöhe maximale Wiederholungen bei hohem Paketverlust
            new_max = min(config_max + 2, current_max + 1)
        elif metrics.packet_loss_percent < 1.0:
            # Reduziere maximale Wiederholungen bei niedrigem Paketverlust
            new_max = max(1, current_max - 1)
        else:
            # Keine Änderung
            new_max = current_max
        
        if new_delay != current_delay or new_max != current_max:
            self.adaptive_settings.retry_delay = new_delay
            self.adaptive_settings.max_retries = new_max
            logger.info(f"Wiederholungseinstellungen angepasst: Verzögerung={new_delay}s, Max={new_max}")
    
    def _adjust_bandwidth_limit(self, metrics: BandwidthMetrics) -> None:
        """
        Passt das Bandbreitenlimit an.
        
        Args:
            metrics: Aktuelle Metriken
        """
        # In einer erweiterten Implementierung würden wir hier
        # ein dynamisches Bandbreitenlimit berechnen
        # Für dieses Beispiel lassen wir das Limit unverändert
        pass
    
    def get_current_settings(self) -> AdaptiveSettings:
        """
        Gibt die aktuellen adaptiven Einstellungen zurück.
        
        Returns:
            AdaptiveSettings-Objekt mit aktuellen Einstellungen
        """
        return self.adaptive_settings
    
    def register_download_start(self, file_id: str) -> None:
        """
        Registriert den Start eines Downloads.
        
        Args:
            file_id: Telegram-Datei-ID
        """
        self.active_downloads[file_id] = datetime.now()
        logger.debug(f"Download gestartet: {file_id}")
    
    def register_download_end(self, file_id: str) -> None:
        """
        Registriert das Ende eines Downloads.
        
        Args:
            file_id: Telegram-Datei-ID
        """
        if file_id in self.active_downloads:
            del self.active_downloads[file_id]
            logger.debug(f"Download beendet: {file_id}")
    
    def get_active_download_count(self) -> int:
        """
        Gibt die Anzahl aktiver Downloads zurück.
        
        Returns:
            Anzahl aktiver Downloads
        """
        return len(self.active_downloads)
    
    def can_start_new_download(self) -> bool:
        """
        Prüft, ob ein neuer Download gestartet werden kann.
        
        Returns:
            True, wenn ein neuer Download gestartet werden kann
        """
        return len(self.active_downloads) < self.adaptive_settings.max_concurrent_downloads
    
    def update_download_speed(self, file_id: str, bytes_downloaded: int, time_elapsed: float) -> None:
        """
        Aktualisiert die Download-Geschwindigkeit für eine Datei.
        
        Args:
            file_id: Telegram-Datei-ID
            bytes_downloaded: Anzahl heruntergeladener Bytes
            time_elapsed: Verstrichene Zeit in Sekunden
        """
        if time_elapsed > 0:
            speed_kbps = (bytes_downloaded / 1024) / time_elapsed
            logger.debug(f"Download-Geschwindigkeit für {file_id}: {speed_kbps:.2f} KB/s")
            
            # Aktualisiere die Metriken
            if self.metrics_history:
                self.metrics_history[-1].download_speed_kbps = speed_kbps


# Globale Instanz des BandwidthControllers
_bandwidth_controller: Optional[IntelligentBandwidthController] = None


def get_bandwidth_controller(config: Config = None) -> IntelligentBandwidthController:
    """
    Gibt die globale Instanz des IntelligentBandwidthController zurück.
    
    Args:
        config: Konfigurationsobjekt (nur für die erste Initialisierung)
        
    Returns:
        IntelligentBandwidthController-Instanz
    """
    global _bandwidth_controller
    if _bandwidth_controller is None:
        if config is None:
            raise ValueError("Konfiguration erforderlich für die erste Initialisierung")
        _bandwidth_controller = IntelligentBandwidthController(config)
    return _bandwidth_controller


def initialize_bandwidth_controller(config: Config) -> None:
    """
    Initialisiert den Bandwidth-Controller.
    
    Args:
        config: Konfigurationsobjekt
    """
    try:
        global _bandwidth_controller
        _bandwidth_controller = IntelligentBandwidthController(config)
        logger.info("Bandwidth-Controller initialisiert")
    except Exception as e:
        logger.error(f"Fehler bei der Initialisierung des Bandwidth-Controllers: {e}")
        raise


def adjust_bandwidth_settings() -> None:
    """
    Passt die Bandbreiteneinstellungen an.
    """
    try:
        controller = get_bandwidth_controller()
        controller.adjust_settings()
    except Exception as e:
        logger.error(f"Fehler bei der Anpassung der Bandbreiteneinstellungen: {e}")


def get_current_bandwidth_settings() -> AdaptiveSettings:
    """
    Gibt die aktuellen Bandbreiteneinstellungen zurück.
    
    Returns:
        AdaptiveSettings-Objekt mit aktuellen Einstellungen
    """
    try:
        controller = get_bandwidth_controller()
        return controller.get_current_settings()
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Bandbreiteneinstellungen: {e}")
        # Rückfall auf Standardwerte
        return AdaptiveSettings()


def register_download_start(file_id: str) -> None:
    """
    Registriert den Start eines Downloads.
    
    Args:
        file_id: Telegram-Datei-ID
    """
    try:
        controller = get_bandwidth_controller()
        controller.register_download_start(file_id)
    except Exception as e:
        logger.error(f"Fehler beim Registrieren des Download-Starts: {e}")


def register_download_end(file_id: str) -> None:
    """
    Registriert das Ende eines Downloads.
    
    Args:
        file_id: Telegram-Datei-ID
    """
    try:
        controller = get_bandwidth_controller()
        controller.register_download_end(file_id)
    except Exception as e:
        logger.error(f"Fehler beim Registrieren des Download-Endes: {e}")


def can_start_new_download() -> bool:
    """
    Prüft, ob ein neuer Download gestartet werden kann.
    
    Returns:
        True, wenn ein neuer Download gestartet werden kann
    """
    try:
        controller = get_bandwidth_controller()
        return controller.can_start_new_download()
    except Exception as e:
        logger.error(f"Fehler bei der Prüfung, ob neuer Download gestartet werden kann: {e}")
        return True  # Rückfall: Erlaube Download


def update_download_speed(file_id: str, bytes_downloaded: int, time_elapsed: float) -> None:
    """
    Aktualisiert die Download-Geschwindigkeit.
    
    Args:
        file_id: Telegram-Datei-ID
        bytes_downloaded: Anzahl heruntergeladener Bytes
        time_elapsed: Verstrichene Zeit in Sekunden
    """
    try:
        controller = get_bandwidth_controller()
        controller.update_download_speed(file_id, bytes_downloaded, time_elapsed)
    except Exception as e:
        logger.error(f"Fehler beim Aktualisieren der Download-Geschwindigkeit: {e}")