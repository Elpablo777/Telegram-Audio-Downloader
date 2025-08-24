"""
Intelligente Warteschlange für den Telegram Audio Downloader.
"""

import asyncio
import heapq
import time
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from collections import defaultdict

from .models import DownloadStatus
from .logging_config import get_logger
from .error_handling import handle_error, DownloadError

logger = get_logger(__name__)

class Priority(Enum):
    """Prioritätsstufen für Download-Aufträge."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

class DependencyType(Enum):
    """Arten von Abhängigkeiten zwischen Aufträgen."""
    BEFORE = "before"  # Dieser Auftrag muss vor dem anderen ausgeführt werden
    AFTER = "after"    # Dieser Auftrag muss nach dem anderen ausgeführt werden
    PARENT = "parent"  # Dieser Auftrag ist ein Elternteil des anderen
    CHILD = "child"    # Dieser Auftrag ist ein Kind des anderen

@dataclass
class QueueItem:
    """Ein Element in der Download-Warteschlange."""
    id: str
    group_name: str
    priority: Priority
    created_at: datetime
    dependencies: Set[str] = field(default_factory=set)
    dependent_items: Set[str] = field(default_factory=set)
    status: DownloadStatus = DownloadStatus.PENDING
    limit: Optional[int] = None
    output_dir: Optional[str] = None
    parallel_downloads: Optional[int] = None
    # Für die Heap-Queue benötigen wir eine Methode zum Vergleichen
    # Wir verwenden eine Kombination aus Priorität, Erstellungszeit und ID
    sort_key: tuple = field(init=False)
    
    def __post_init__(self):
        # Sortierschlüssel: höhere Priorität, frühere Erstellungszeit, niedrigere ID
        # heapq ist ein Min-Heap, daher invertieren wir die Priorität
        self.sort_key = (-self.priority.value, self.created_at.timestamp(), self.id)
    
    def __lt__(self, other):
        """Vergleichsmethode für die Heap-Queue."""
        return self.sort_key < other.sort_key

class IntelligentQueue:
    """Intelligente Warteschlange mit Priorisierung und Abhängigkeitsverwaltung."""
    
    def __init__(self, max_concurrent_items: int = 3):
        """
        Initialisiert die intelligente Warteschlange.
        
        Args:
            max_concurrent_items: Maximale Anzahl gleichzeitiger Download-Aufträge
        """
        self.max_concurrent_items = max_concurrent_items
        self.pending_queue: List[QueueItem] = []  # Heap-basierte Warteschlange
        self.active_items: Dict[str, QueueItem] = {}  # Aktive Download-Aufträge
        self.completed_items: Dict[str, QueueItem] = {}  # Abgeschlossene Aufträge
        self.failed_items: Dict[str, QueueItem] = {}  # Fehlgeschlagene Aufträge
        self.dependencies: Dict[str, Set[str]] = defaultdict(set)  # Abhängigkeiten
        self.dependents: Dict[str, Set[str]] = defaultdict(set)  # Abhängige Elemente
        self.resource_usage: Dict[str, int] = {}  # Ressourcennutzung pro Auftrag
        self.semaphore = asyncio.Semaphore(max_concurrent_items)
        self._stop_processing = False
        heapq.heapify(self.pending_queue)
    
    def add_item(self, item: QueueItem) -> None:
        """
        Fügt einen Download-Auftrag zur Warteschlange hinzu.
        
        Args:
            item: Der hinzuzufügende Download-Auftrag
        """
        try:
            # Füge das Element zur Warteschlange hinzu
            heapq.heappush(self.pending_queue, item)
            
            # Aktualisiere die Abhängigkeiten
            for dep_id in item.dependencies:
                self.dependencies[item.id].add(dep_id)
                self.dependents[dep_id].add(item.id)
            
            logger.info(f"Download-Auftrag {item.id} zur Warteschlange hinzugefügt (Priorität: {item.priority.name})")
        except Exception as e:
            error = DownloadError(f"Fehler beim Hinzufügen des Download-Auftrags {item.id}: {e}")
            handle_error(error, "intelligent_queue_add_item")
            raise
    
    def remove_item(self, item_id: str) -> bool:
        """
        Entfernt einen Download-Auftrag aus der Warteschlange.
        
        Args:
            item_id: ID des zu entfernenden Auftrags
            
        Returns:
            True, wenn der Auftrag entfernt wurde, False sonst
        """
        try:
            # Prüfe, ob der Auftrag in der Warteschlange ist
            for i, item in enumerate(self.pending_queue):
                if item.id == item_id:
                    # Entferne den Auftrag aus der Warteschlange
                    self.pending_queue.pop(i)
                    heapq.heapify(self.pending_queue)  # Neuordnung des Heaps
                    
                    # Entferne Abhängigkeiten
                    self._remove_dependencies(item_id)
                    
                    logger.info(f"Download-Auftrag {item_id} aus der Warteschlange entfernt")
                    return True
            
            # Prüfe, ob der Auftrag aktiv ist
            if item_id in self.active_items:
                # Wir können aktive Aufträge nicht direkt entfernen
                logger.warning(f"Download-Auftrag {item_id} ist aktiv und kann nicht entfernt werden")
                return False
            
            # Prüfe, ob der Auftrag bereits abgeschlossen oder fehlgeschlagen ist
            if item_id in self.completed_items or item_id in self.failed_items:
                logger.warning(f"Download-Auftrag {item_id} ist bereits abgeschlossen")
                return False
            
            logger.warning(f"Download-Auftrag {item_id} nicht in der Warteschlange gefunden")
            return False
        except Exception as e:
            error = DownloadError(f"Fehler beim Entfernen des Download-Auftrags {item_id}: {e}")
            handle_error(error, "intelligent_queue_remove_item")
            return False
    
    def _remove_dependencies(self, item_id: str) -> None:
        """
        Entfernt alle Abhängigkeiten für einen Auftrag.
        
        Args:
            item_id: ID des Auftrags
        """
        # Entferne Abhängigkeiten dieses Auftrags
        if item_id in self.dependencies:
            for dep_id in self.dependencies[item_id]:
                self.dependents[dep_id].discard(item_id)
            del self.dependencies[item_id]
        
        # Entferne abhängige Aufträge von diesem Auftrag
        if item_id in self.dependents:
            for dep_id in self.dependents[item_id]:
                self.dependencies[dep_id].discard(item_id)
            del self.dependents[item_id]
    
    def get_next_item(self) -> Optional[QueueItem]:
        """
        Holt den nächsten verfügbaren Download-Auftrag aus der Warteschlange.
        
        Returns:
            Der nächste Download-Auftrag oder None, wenn keiner verfügbar ist
        """
        try:
            # Prüfe, ob die maximale Anzahl aktiver Aufträge erreicht ist
            if len(self.active_items) >= self.max_concurrent_items:
                return None
            
            # Suche nach einem Auftrag, der bereit ist (keine unerfüllten Abhängigkeiten)
            temp_queue = []
            next_item = None
            
            while self.pending_queue:
                # Hole das Element mit der höchsten Priorität
                item = heapq.heappop(self.pending_queue)
                
                # Prüfe, ob alle Abhängigkeiten erfüllt sind
                if self._are_dependencies_met(item):
                    next_item = item
                    break
                else:
                    # Lege das Element vorübergehend beiseite
                    temp_queue.append(item)
            
            # Lege die nicht verarbeiteten Elemente zurück in die Warteschlange
            for item in temp_queue:
                heapq.heappush(self.pending_queue, item)
            
            if next_item:
                # Markiere den Auftrag als aktiv
                next_item.status = DownloadStatus.DOWNLOADING
                self.active_items[next_item.id] = next_item
                logger.info(f"Download-Auftrag {next_item.id} als nächstes bereit für Download")
            
            return next_item
        except Exception as e:
            error = DownloadError(f"Fehler beim Holen des nächsten Download-Auftrags: {e}")
            handle_error(error, "intelligent_queue_get_next_item")
            return None
    
    def _are_dependencies_met(self, item: QueueItem) -> bool:
        """
        Prüft, ob alle Abhängigkeiten eines Auftrags erfüllt sind.
        
        Args:
            item: Der zu prüfende Auftrag
            
        Returns:
            True, wenn alle Abhängigkeiten erfüllt sind, False sonst
        """
        for dep_id in item.dependencies:
            # Prüfe, ob die Abhängigkeit abgeschlossen ist
            if dep_id not in self.completed_items:
                return False
        return True
    
    def mark_item_completed(self, item_id: str) -> None:
        """
        Markiert einen Download-Auftrag als abgeschlossen.
        
        Args:
            item_id: ID des abgeschlossenen Auftrags
        """
        try:
            if item_id in self.active_items:
                item = self.active_items.pop(item_id)
                item.status = DownloadStatus.COMPLETED
                item.completed_at = datetime.now()
                self.completed_items[item_id] = item
                
                # Entferne Ressourcennutzung
                if item_id in self.resource_usage:
                    del self.resource_usage[item_id]
                
                logger.info(f"Download-Auftrag {item_id} als abgeschlossen markiert")
            else:
                logger.warning(f"Download-Auftrag {item_id} nicht in aktiven Aufträgen gefunden")
        except Exception as e:
            error = DownloadError(f"Fehler beim Markieren des Download-Auftrags {item_id} als abgeschlossen: {e}")
            handle_error(error, "intelligent_queue_mark_completed")
    
    def mark_item_failed(self, item_id: str, error_message: Optional[str] = None) -> None:
        """
        Markiert einen Download-Auftrag als fehlgeschlagen.
        
        Args:
            item_id: ID des fehlgeschlagenen Auftrags
            error_message: Optionale Fehlermeldung
        """
        try:
            if item_id in self.active_items:
                item = self.active_items.pop(item_id)
                item.status = DownloadStatus.FAILED
                item.error_message = error_message
                item.completed_at = datetime.now()
                self.failed_items[item_id] = item
                
                # Entferne Ressourcennutzung
                if item_id in self.resource_usage:
                    del self.resource_usage[item_id]
                
                logger.error(f"Download-Auftrag {item_id} als fehlgeschlagen markiert: {error_message}")
            else:
                logger.warning(f"Download-Auftrag {item_id} nicht in aktiven Aufträgen gefunden")
        except Exception as e:
            error = DownloadError(f"Fehler beim Markieren des Download-Auftrags {item_id} als fehlgeschlagen: {e}")
            handle_error(error, "intelligent_queue_mark_failed")
    
    def get_queue_status(self) -> Dict[str, Any]:
        """
        Gibt den Status der Warteschlange zurück.
        
        Returns:
            Dictionary mit Statusinformationen
        """
        return {
            "pending_items": len(self.pending_queue),
            "active_items": len(self.active_items),
            "completed_items": len(self.completed_items),
            "failed_items": len(self.failed_items),
            "max_concurrent_items": self.max_concurrent_items,
            "current_concurrent_items": len(self.active_items)
        }
    
    def update_item_priority(self, item_id: str, new_priority: Priority) -> bool:
        """
        Aktualisiert die Priorität eines Download-Auftrags.
        
        Args:
            item_id: ID des Auftrags
            new_priority: Neue Priorität
            
        Returns:
            True, wenn die Priorität aktualisiert wurde, False sonst
        """
        return self.update_priority(item_id, new_priority)

    def update_priority(self, item_id: str, new_priority: Priority) -> bool:
        """
        Aktualisiert die Priorität eines Download-Auftrags.
        
        Args:
            item_id: ID des Auftrags
            new_priority: Neue Priorität
            
        Returns:
            True, wenn die Priorität aktualisiert wurde, False sonst
        """
        try:
            # Prüfe, ob der Auftrag in der Warteschlange ist
            for i, item in enumerate(self.pending_queue):
                if item.id == item_id:
                    # Entferne das Element aus der Warteschlange
                    self.pending_queue.pop(i)
                    
                    # Aktualisiere die Priorität
                    item.priority = new_priority
                    item.sort_key = (-item.priority.value, item.created_at.timestamp(), item.id)
                    
                    # Füge das Element wieder zur Warteschlange hinzu
                    heapq.heappush(self.pending_queue, item)
                    heapq.heapify(self.pending_queue)  # Neuordnung des Heaps
                    
                    logger.info(f"Priorität des Download-Auftrags {item_id} auf {new_priority.name} aktualisiert")
                    return True
            
            # Prüfe, ob der Auftrag aktiv ist
            if item_id in self.active_items:
                # Aktive Aufträge können ihre Priorität nicht ändern
                logger.warning(f"Download-Auftrag {item_id} ist aktiv und kann die Priorität nicht ändern")
                return False
            
            logger.warning(f"Download-Auftrag {item_id} nicht in der Warteschlange gefunden")
            return False
        except Exception as e:
            error = DownloadError(f"Fehler beim Aktualisieren der Priorität des Download-Auftrags {item_id}: {e}")
            handle_error(error, "intelligent_queue_update_priority")
            return False
    
    def add_dependency(self, item_id: str, dependency_id: str, dependency_type: DependencyType = DependencyType.BEFORE) -> bool:
        """
        Fügt eine Abhängigkeit zwischen zwei Download-Aufträgen hinzu.
        
        Args:
            item_id: ID des abhängigen Auftrags
            dependency_id: ID des Auftrags, von dem abhängig ist
            dependency_type: Art der Abhängigkeit
            
        Returns:
            True, wenn die Abhängigkeit hinzugefügt wurde, False sonst
        """
        try:
            # Prüfe, ob beide Aufträge existieren
            item_exists = (item_id in self.active_items or 
                          item_id in self.completed_items or 
                          item_id in self.failed_items or
                          any(item.id == item_id for item in self.pending_queue))
            
            dependency_exists = (dependency_id in self.active_items or 
                               dependency_id in self.completed_items or 
                               dependency_id in self.failed_items or
                               any(item.id == dependency_id for item in self.pending_queue))
            
            if not item_exists or not dependency_exists:
                logger.warning(f"Ein oder beide Aufträge ({item_id}, {dependency_id}) existieren nicht")
                return False
            
            # Füge die Abhängigkeit hinzu
            self.dependencies[item_id].add(dependency_id)
            self.dependents[dependency_id].add(item_id)
            
            # Aktualisiere das Abhängigkeitsfeld im Auftrag
            for item in self.pending_queue:
                if item.id == item_id:
                    item.dependencies.add(dependency_id)
                    break
            
            if item_id in self.active_items:
                self.active_items[item_id].dependencies.add(dependency_id)
            
            logger.info(f"Abhängigkeit hinzugefügt: {item_id} -> {dependency_id} ({dependency_type.value})")
            return True
        except Exception as e:
            error = DownloadError(f"Fehler beim Hinzufügen der Abhängigkeit zwischen {item_id} und {dependency_id}: {e}")
            handle_error(error, "intelligent_queue_add_dependency")
            return False
    
    def get_dependent_items(self, item_id: str) -> Set[str]:
        """
        Gibt alle Aufträge zurück, die von einem bestimmten Auftrag abhängen.
        
        Args:
            item_id: ID des Auftrags
            
        Returns:
            Menge der abhängigen Aufträge
        """
        return self.dependents.get(item_id, set())
    
    def get_dependencies(self, item_id: str) -> Set[str]:
        """
        Gibt alle Aufträge zurück, von denen ein bestimmter Auftrag abhängt.
        
        Args:
            item_id: ID des Auftrags
            
        Returns:
            Menge der Abhängigkeiten
        """
        return self.dependencies.get(item_id, set())
    
    def stop_processing(self) -> None:
        """Stoppt die Verarbeitung neuer Aufträge."""
        self._stop_processing = True
        logger.info("Verarbeitung neuer Download-Aufträge gestoppt")
    
    def resume_processing(self) -> None:
        """Setzt die Verarbeitung neuer Aufträge fort."""
        self._stop_processing = False
        logger.info("Verarbeitung neuer Download-Aufträge fortgesetzt")
    
    def is_processing_stopped(self) -> bool:
        """
        Prüft, ob die Verarbeitung neuer Aufträge gestoppt ist.
        
        Returns:
            True, wenn die Verarbeitung gestoppt ist, False sonst
        """
        return self._stop_processing