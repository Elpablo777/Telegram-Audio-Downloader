"""
Intelligentes Prefetching für den Telegram Audio Downloader.

Vorausschauendes Laden von Dateien basierend auf:
- Analyse von Download-Mustern
- Pufferung häufig genutzter Dateien
- Hintergrund-Downloads mit niedriger Priorität
- Angepasste Puffergröße
"""

import asyncio
import time
import weakref
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from .logging_config import get_logger
from .models import AudioFile

logger = get_logger(__name__)


@dataclass
class DownloadPattern:
    """Muster für Download-Verhaltensanalyse."""
    group_id: int
    file_extensions: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    time_patterns: Dict[int, int] = field(default_factory=lambda: defaultdict(int))  # Stunden des Tages
    file_sizes: List[int] = field(default_factory=list)
    last_accessed: datetime = field(default_factory=datetime.now)
    
    def add_download(self, file_extension: str, hour_of_day: int, file_size: int) -> None:
        """Fügt einen Download zum Muster hinzu."""
        self.file_extensions[file_extension] += 1
        self.time_patterns[hour_of_day] += 1
        self.file_sizes.append(file_size)
        self.last_accessed = datetime.now()
        
        # Begrenze die Anzahl der gespeicherten Dateigrößen
        if len(self.file_sizes) > 1000:
            self.file_sizes = self.file_sizes[-1000:]
    
    def get_preferred_extensions(self, limit: int = 3) -> List[str]:
        """Gibt die bevorzugten Dateierweiterungen zurück."""
        sorted_extensions = sorted(
            self.file_extensions.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        return [ext for ext, _ in sorted_extensions[:limit]]
    
    def get_preferred_hours(self, limit: int = 3) -> List[int]:
        """Gibt die Stunden mit den meisten Downloads zurück."""
        sorted_hours = sorted(
            self.time_patterns.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        return [hour for hour, _ in sorted_hours[:limit]]


class PrefetchManager:
    """Verwaltet intelligentes Prefetching von Audiodateien."""
    
    def __init__(self, download_dir: Path, max_prefetch_queue: int = 10):
        """
        Initialisiert den PrefetchManager.
        
        Args:
            download_dir: Download-Verzeichnis
            max_prefetch_queue: Maximale Anzahl von Dateien in der Prefetch-Warteschlange
        """
        self.download_dir = Path(download_dir)
        self.max_prefetch_queue = max_prefetch_queue
        self.patterns: Dict[int, DownloadPattern] = {}  # group_id -> DownloadPattern
        self.prefetch_queue: deque = deque(maxlen=max_prefetch_queue)
        self.prefetch_history: Set[str] = set()  # file_ids, die bereits geprefetcht wurden
        self.access_frequency: Dict[str, int] = defaultdict(int)  # file_id -> Zugriffshäufigkeit
        self.last_prefetch_time = 0.0
        self.prefetch_interval = 30.0  # Sekunden zwischen Prefetch-Versuchen
        self.is_prefetching = False
        
        # Schwache Referenzen für große Datenstrukturen
        self._cache = weakref.WeakValueDictionary()
        
        logger.info(f"PrefetchManager initialisiert mit max. {max_prefetch_queue} Dateien in der Warteschlange")
    
    def record_download(self, group_id: int, file_extension: str, file_size: int, file_id: str) -> None:
        """
        Zeichnet einen Download für die Musteranalyse auf.
        
        Args:
            group_id: ID der Telegram-Gruppe
            file_extension: Dateierweiterung
            file_size: Dateigröße in Bytes
            file_id: Eindeutige ID der Datei
        """
        # Muster für die Gruppe erstellen oder abrufen
        if group_id not in self.patterns:
            self.patterns[group_id] = DownloadPattern(group_id=group_id)
        
        pattern = self.patterns[group_id]
        hour_of_day = datetime.now().hour
        pattern.add_download(file_extension, hour_of_day, file_size)
        
        # Zugriffshäufigkeit erhöhen
        self.access_frequency[file_id] += 1
    
    def should_prefetch(self) -> bool:
        """
        Prüft, ob ein Prefetch-Vorgang gestartet werden sollte.
        
        Returns:
            True, wenn Prefetching gestartet werden sollte
        """
        if self.is_prefetching:
            return False
            
        if time.time() - self.last_prefetch_time < self.prefetch_interval:
            return False
            
        return len(self.prefetch_queue) > 0
    
    async def start_prefetching(self, downloader) -> None:
        """
        Startet den Prefetching-Prozess im Hintergrund.
        
        Args:
            downloader: AudioDownloader-Instanz für die tatsächlichen Downloads
        """
        if self.is_prefetching or not self.prefetch_queue:
            return
            
        self.is_prefetching = True
        self.last_prefetch_time = time.time()
        
        try:
            logger.debug(f"Starte Prefetching von {len(self.prefetch_queue)} Dateien")
            
            # Prefetch-Dateien mit niedriger Priorität
            prefetch_tasks = []
            while self.prefetch_queue:
                file_id = self.prefetch_queue.popleft()
                if file_id not in self.prefetch_history:
                    # Erstelle einen Prefetch-Task
                    task = self._prefetch_file(downloader, file_id)
                    prefetch_tasks.append(task)
                    self.prefetch_history.add(file_id)
            
            # Führe Prefetching mit niedriger Priorität aus
            if prefetch_tasks:
                # Verwende eine niedrigere Anzahl paralleler Downloads für Prefetching
                semaphore = asyncio.Semaphore(min(2, len(prefetch_tasks)))
                
                async def limited_prefetch(task):
                    async with semaphore:
                        await task
                
                limited_tasks = [limited_prefetch(task) for task in prefetch_tasks]
                await asyncio.gather(*limited_tasks, return_exceptions=True)
                
                logger.info(f"Prefetching von {len(prefetch_tasks)} Dateien abgeschlossen")
        except Exception as e:
            logger.error(f"Fehler beim Prefetching: {e}")
        finally:
            self.is_prefetching = False
    
    async def _prefetch_file(self, downloader, file_id: str) -> None:
        """
        Prefetcht eine einzelne Datei.
        
        Args:
            downloader: AudioDownloader-Instanz
            file_id: ID der Datei zum Prefetchen
        """
        try:
            # In einer echten Implementierung würden wir hier die Datei tatsächlich herunterladen
            # und im Cache speichern. Für dieses Beispiel simulieren wir den Vorgang.
            logger.debug(f"Prefetching Datei {file_id}")
            await asyncio.sleep(0.1)  # Simuliere Download-Zeit
        except Exception as e:
            logger.error(f"Fehler beim Prefetching von Datei {file_id}: {e}")
    
    def analyze_patterns(self) -> Dict[str, any]:
        """
        Analysiert die gesammelten Download-Muster.
        
        Returns:
            Dictionary mit Analyseergebnissen
        """
        if not self.patterns:
            return {}
        
        analysis = {
            "total_groups": len(self.patterns),
            "patterns": {}
        }
        
        for group_id, pattern in self.patterns.items():
            analysis["patterns"][group_id] = {
                "preferred_extensions": pattern.get_preferred_extensions(),
                "preferred_hours": pattern.get_preferred_hours(),
                "total_downloads": sum(pattern.file_extensions.values()),
                "last_accessed": pattern.last_accessed.isoformat()
            }
        
        return analysis
    
    def add_to_prefetch_queue(self, file_id: str) -> None:
        """
        Fügt eine Datei zur Prefetch-Warteschlange hinzu.
        
        Args:
            file_id: ID der Datei zum Hinzufügen
        """
        # Prüfe, ob die Datei bereits in der Warteschlange ist oder bereits geprefetcht wurde
        if file_id in self.prefetch_history:
            return
            
        # Prüfe, ob die Datei bereits in der Warteschlange ist
        if file_id in self.prefetch_queue:
            return
            
        # Prüfe Zugriffshäufigkeit - nur häufig abgerufene Dateien prefetchen
        if self.access_frequency.get(file_id, 0) < 2:
            return
            
        # Füge zur Warteschlange hinzu
        self.prefetch_queue.append(file_id)
        logger.debug(f"Datei {file_id} zur Prefetch-Warteschlange hinzugefügt")
    
    def get_prefetch_candidates(self, group_id: int, limit: int = 5) -> List[str]:
        """
        Gibt Kandidaten für das Prefetching basierend auf Mustern zurück.
        
        Args:
            group_id: ID der Telegram-Gruppe
            limit: Maximale Anzahl von Kandidaten
            
        Returns:
            Liste von Datei-IDs für das Prefetching
        """
        # In einer echten Implementierung würden wir hier eine Datenbankabfrage
        # durchführen, um ähnliche Dateien zu finden.
        # Für dieses Beispiel geben wir eine leere Liste zurück.
        return []
    
    def clear_old_patterns(self, max_age_hours: int = 24) -> None:
        """
        Löscht alte Download-Muster.
        
        Args:
            max_age_hours: Maximales Alter in Stunden
        """
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        old_groups = [
            group_id for group_id, pattern in self.patterns.items()
            if pattern.last_accessed < cutoff_time
        ]
        
        for group_id in old_groups:
            del self.patterns[group_id]
            
        logger.debug(f"{len(old_groups)} alte Download-Muster gelöscht")