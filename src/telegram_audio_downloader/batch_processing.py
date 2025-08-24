"""
Batch-Verarbeitung für den Telegram Audio Downloader.
"""

import asyncio
import logging
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

from .error_handling import handle_error
from .file_error_handler import handle_file_error, with_file_error_handling
from .utils import sanitize_filename

logger = logging.getLogger(__name__)

class Priority(Enum):
    """Prioritätsstufen für Download-Aufträge."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class BatchItem:
    """Ein einzelner Download-Auftrag in einer Batch-Verarbeitung."""
    id: str
    group_name: str
    limit: Optional[int] = None
    priority: Priority = Priority.NORMAL
    output_dir: Optional[Path] = None
    parallel_downloads: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: str = "pending"  # pending, running, completed, failed
    progress: float = 0.0  # 0.0 - 1.0
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class ProgressCallback(ABC):
    """Abstrakte Basisklasse für Fortschrittsrückmeldungen."""
    
    @abstractmethod
    async def on_item_start(self, item: BatchItem) -> None:
        """Wird aufgerufen, wenn ein Batch-Item gestartet wird."""
        pass
    
    @abstractmethod
    async def on_item_progress(self, item: BatchItem, progress: float) -> None:
        """Wird aufgerufen, wenn der Fortschritt eines Items aktualisiert wird."""
        pass
    
    @abstractmethod
    async def on_item_complete(self, item: BatchItem) -> None:
        """Wird aufgerufen, wenn ein Batch-Item abgeschlossen ist."""
        pass
    
    @abstractmethod
    async def on_item_error(self, item: BatchItem, error: Exception) -> None:
        """Wird aufgerufen, wenn ein Batch-Item fehlschlägt."""
        pass

class ConsoleProgressCallback(ProgressCallback):
    """Konsolenbasierte Fortschrittsrückmeldung."""
    
    async def on_item_start(self, item: BatchItem) -> None:
        """Zeigt den Start eines Items an."""
        logger.info(f"Starte Batch-Item {item.id}: {item.group_name}")
    
    async def on_item_progress(self, item: BatchItem, progress: float) -> None:
        """Aktualisiert den Fortschritt eines Items."""
        logger.debug(f"Batch-Item {item.id} Fortschritt: {progress:.2%}")
    
    async def on_item_complete(self, item: BatchItem) -> None:
        """Zeigt den Abschluss eines Items an."""
        logger.info(f"Batch-Item {item.id} abgeschlossen")
    
    async def on_item_error(self, item: BatchItem, error: Exception) -> None:
        """Zeigt einen Fehler eines Items an."""
        logger.error(f"Batch-Item {item.id} fehlgeschlagen: {error}")

class BatchProcessor:
    """Batch-Prozessor für die Sammelverarbeitung von Download-Aufträgen."""
    
    def __init__(self, max_concurrent_batches: int = 3, progress_callback: Optional[ProgressCallback] = None):
        """
        Initialisiert den Batch-Prozessor.
        
        Args:
            max_concurrent_batches: Maximale Anzahl gleichzeitiger Batch-Verarbeitungen
            progress_callback: Callback für Fortschrittsmeldungen
        """
        self.max_concurrent_batches = max_concurrent_batches
        self.progress_callback = progress_callback or ConsoleProgressCallback()
        self.batch_queue: List[BatchItem] = []
        self.active_batches: Dict[str, BatchItem] = {}
        self.completed_batches: Dict[str, BatchItem] = {}
        self.failed_batches: Dict[str, BatchItem] = {}
        self.semaphore = asyncio.Semaphore(max_concurrent_batches)
        self._stop_processing = False
        
    def add_batch_item(self, item: BatchItem) -> None:
        """
        Fügt einen Download-Auftrag zur Warteschlange hinzu.
        
        Args:
            item: Der hinzuzufügende Batch-Item
        """
        # Füge das Item an der richtigen Position basierend auf der Priorität hinzu
        inserted = False
        for i, existing_item in enumerate(self.batch_queue):
            if item.priority.value > existing_item.priority.value:
                self.batch_queue.insert(i, item)
                inserted = True
                break
        
        if not inserted:
            self.batch_queue.append(item)
            
        logger.info(f"Batch-Item {item.id} zur Warteschlange hinzugefügt (Priorität: {item.priority.name})")
    
    async def process_batches(self, download_function: Callable) -> None:
        """
        Verarbeitet alle Batch-Aufträge in der Warteschlange.
        
        Args:
            download_function: Funktion zum Ausführen der Downloads
        """
        logger.info(f"Starte Batch-Verarbeitung mit {len(self.batch_queue)} Aufträgen")
        
        # Erstelle Tasks für alle Batch-Items
        tasks = []
        while self.batch_queue and not self._stop_processing:
            # Hole das nächstes Item aus der Warteschlange
            item = self.batch_queue.pop(0)
            self.active_batches[item.id] = item
            
            # Erstelle einen Task für das Item
            task = asyncio.create_task(self._process_item(item, download_function))
            tasks.append(task)
        
        # Warte auf Abschluss aller Tasks
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        logger.info("Batch-Verarbeitung abgeschlossen")
        self._log_summary()
    
    async def _process_item(self, item: BatchItem, download_function: Callable) -> None:
        """
        Verarbeitet ein einzelnes Batch-Item.
        
        Args:
            item: Das zu verarbeitende Item
            download_function: Funktion zum Ausführen der Downloads
        """
        async with self.semaphore:
            try:
                item.status = "running"
                item.started_at = datetime.now()
                await self.progress_callback.on_item_start(item)
                
                # Führe den Download aus
                await download_function(
                    group=item.group_name,
                    limit=item.limit,
                    output=str(item.output_dir) if item.output_dir else None,
                    parallel=item.parallel_downloads
                )
                
                item.status = "completed"
                item.completed_at = datetime.now()
                item.progress = 1.0
                await self.progress_callback.on_item_complete(item)
                
                # Verschiebe das Item in die abgeschlossenen Items
                self.completed_batches[item.id] = self.active_batches.pop(item.id)
                
            except Exception as e:
                item.status = "failed"
                item.error = str(e)
                item.completed_at = datetime.now()
                await self.progress_callback.on_item_error(item, e)
                
                # Verschiebe das Item in die fehlgeschlagenen Items
                self.failed_batches[item.id] = self.active_batches.pop(item.id)
                
                logger.error(f"Fehler bei der Verarbeitung von Batch-Item {item.id}: {e}")
    
    def stop_processing(self) -> None:
        """Stoppt die Batch-Verarbeitung."""
        self._stop_processing = True
        logger.info("Batch-Verarbeitung wird gestoppt")
    
    def get_progress(self) -> Dict[str, Any]:
        """
        Gibt den aktuellen Fortschritt der Batch-Verarbeitung zurück.
        
        Returns:
            Dictionary mit Fortschrittsinformationen
        """
        total_items = len(self.batch_queue) + len(self.active_batches) + len(self.completed_batches) + len(self.failed_batches)
        completed_items = len(self.completed_batches)
        failed_items = len(self.failed_batches)
        
        if total_items > 0:
            overall_progress = (completed_items + failed_items) / total_items
        else:
            overall_progress = 0.0
            
        return {
            "total_items": total_items,
            "pending_items": len(self.batch_queue),
            "active_items": len(self.active_batches),
            "completed_items": completed_items,
            "failed_items": failed_items,
            "overall_progress": overall_progress
        }
    
    def _log_summary(self) -> None:
        """Protokolliert eine Zusammenfassung der Batch-Verarbeitung."""
        progress = self.get_progress()
        logger.info(f"Batch-Verarbeitung Zusammenfassung:")
        logger.info(f"  Gesamt: {progress['total_items']}")
        logger.info(f"  Ausstehend: {progress['pending_items']}")
        logger.info(f"  Aktiv: {progress['active_items']}")
        logger.info(f"  Abgeschlossen: {progress['completed_items']}")
        logger.info(f"  Fehlgeschlagen: {progress['failed_items']}")
        logger.info(f"  Gesamtfortschritt: {progress['overall_progress']:.2%}")