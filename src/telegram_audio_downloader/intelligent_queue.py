"""
Intelligente Warteschlange für den Telegram Audio Downloader.
====================================================================

Die intelligente Warteschlange ist ein zentrales Element des Telegram Audio Downloaders,
das die Verwaltung und Priorisierung von Download-Aufträgen übernimmt. Sie bietet
folgende Funktionen:

- Prioritäten-basiertes Queue-Management mit vier Prioritätsstufen (LOW, NORMAL, HIGH, CRITICAL)
- Abhängigkeitsverwaltung zwischen Aufträgen
- Batch-Verarbeitung für Gruppen von Aufträgen
- Dynamische Queue-Optimierung basierend auf Leistungsdaten
- Ressourcenkontrolle zur Begrenzung gleichzeitiger Downloads
- Fortschrittsverfolgung für einzelne Aufträge und Batches

Die Warteschlange verwendet eine Heap-basierte Datenstruktur für effiziente Sortierung
und Abruf von Aufträgen mit einer Zeitkomplexität von O(log n) für Einfüge- und 
Löschvorgänge. Die Implementierung verwendet asyncio.Semaphore zur Begrenzung der
Anzahl gleichzeitiger Downloads, was eine effiziente Ressourcennutzung gewährleistet.

Example:
    queue = IntelligentQueue(max_concurrent_items=3)
    
    # Einfacher Auftrag
    item = QueueItem(
        id="download_1",
        group_name="Music Group",
        priority=Priority.NORMAL,
        created_at=datetime.now()
    )
    queue.add_item(item)
    
    # Batch-Auftrag
    items = [QueueItem(...) for _ in range(5)]
    queue.add_batch("batch_1", items)
    
    # Verarbeitung
    while True:
        item = queue.get_next_item()
        if item is None:
            break
        # Verarbeite den Auftrag
        queue.mark_item_completed(item.id)
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
    """Ein Element in der Download-Warteschlange.
    
    Attributes:
        id: Eindeutige ID des Auftrags
        group_name: Name der Telegram-Gruppe
        priority: Priorität des Auftrags (LOW, NORMAL, HIGH, CRITICAL)
        created_at: Erstellungszeitpunkt des Auftrags
        dependencies: Menge von IDs, von denen dieser Auftrag abhängt
        dependent_items: Menge von IDs, die von diesem Auftrag abhängen
        status: Aktueller Status des Auftrags (PENDING, DOWNLOADING, COMPLETED, FAILED)
        limit: Maximale Anzahl herunterzuladender Dateien
        output_dir: Ausgabeverzeichnis für Downloads
        parallel_downloads: Anzahl paralleler Downloads
        batch_id: ID des Batches, zu dem dieser Auftrag gehört (optional)
        batch_priority: Priorität des Batches (optional)
        progress: Fortschritt des Auftrags (0-100)
        total_items: Gesamtanzahl der Aufträge im Batch
        sort_key: Schlüssel für die Sortierung in der Heap-basierten Warteschlange
    """
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
    # Neue Felder für Batch-Verarbeitung
    batch_id: Optional[str] = None
    batch_priority: Optional[Priority] = None
    progress: int = 0
    total_items: int = 1
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
    """Intelligente Warteschlange mit Priorisierung und Abhängigkeitsverwaltung.
    
    Die intelligente Warteschlange verwaltet Download-Aufträge mit folgenden Funktionen:
    
    - Prioritäten-basierte Verarbeitung mit vier Stufen
    - Abhängigkeitsmanagement zwischen Aufträgen
    - Batch-Verarbeitung für Gruppen von Aufträgen
    - Dynamische Optimierung basierend auf Leistungsdaten
    - Ressourcenkontrolle zur Begrenzung gleichzeitiger Downloads
    - Fortschrittsverfolgung
    
    Example:
        queue = IntelligentQueue(max_concurrent_items=3)
        
        # Einfügen eines Auftrags
        item = QueueItem(
            id="download_1",
            group_name="Music Group",
            priority=Priority.HIGH,
            created_at=datetime.now()
        )
        queue.add_item(item)
        
        # Verarbeiten der Warteschlange
        while True:
            item = queue.get_next_item()
            if item is None:
                break
            # Verarbeite den Auftrag
            queue.mark_item_completed(item.id)
    """
    
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
        # Neue Strukturen für Batch-Verarbeitung
        self.batches: Dict[str, List[QueueItem]] = defaultdict(list)
        self.batch_progress: Dict[str, int] = defaultdict(int)
        # Neue Attribute für dynamische Optimierung
        self.performance_history: List[Dict[str, Any]] = []
        self.resource_utilization: Dict[str, float] = defaultdict(float)
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
                
                # Aktualisiere Batch-Fortschritt, wenn das Element zu einem Batch gehört
                if item.batch_id:
                    self.update_batch_progress(item.batch_id, item_id)
                
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
    
    def add_batch(self, batch_id: str, items: List[QueueItem], batch_priority: Priority = Priority.NORMAL) -> None:
        """
        Fügt eine Gruppe von Download-Aufträgen als Batch zur Warteschlange hinzu.
        
        Args:
            batch_id: Eindeutige ID für den Batch
            items: Liste von QueueItem-Objekten
            batch_priority: Priorität für den gesamten Batch
        """
        try:
            # Setze Batch-Informationen für alle Elemente
            for item in items:
                item.batch_id = batch_id
                item.batch_priority = batch_priority
                item.total_items = len(items)
                self.add_item(item)
            
            # Speichere den Batch
            self.batches[batch_id] = items
            self.batch_progress[batch_id] = 0
            
            logger.info(f"Batch {batch_id} mit {len(items)} Aufträgen zur Warteschlange hinzugefügt")
        except Exception as e:
            error = DownloadError(f"Fehler beim Hinzufügen des Batches {batch_id}: {e}")
            handle_error(error, "intelligent_queue_add_batch")
            raise
    
    def get_batch_progress(self, batch_id: str) -> float:
        """
        Gibt den Fortschritt eines Batches als Prozentsatz zurück.
        
        Args:
            batch_id: ID des Batches
            
        Returns:
            Fortschritt als Prozentsatz (0-100)
        """
        if batch_id not in self.batches:
            return 0.0
        
        total_items = len(self.batches[batch_id])
        if total_items == 0:
            return 0.0
            
        completed = self.batch_progress.get(batch_id, 0)
        return (completed / total_items) * 100
    
    def update_batch_progress(self, batch_id: str, item_id: str) -> None:
        """
        Aktualisiert den Fortschritt eines Batches, wenn ein Element abgeschlossen wird.
        
        Args:
            batch_id: ID des Batches
            item_id: ID des abgeschlossenen Elements
        """
        if batch_id in self.batches:
            self.batch_progress[batch_id] = self.batch_progress.get(batch_id, 0) + 1
            logger.info(f"Batch {batch_id} Fortschritt: {self.batch_progress[batch_id]}/{len(self.batches[batch_id])}")
    
    def optimize_queue(self) -> None:
        """
        Optimiert die Warteschlange basierend auf Leistungsdaten und Ressourcennutzung.
        """
        try:
            # Sammle aktuelle Leistungsdaten
            performance_data = self._collect_performance_data()
            self.performance_history.append(performance_data)
            
            # Behalte nur die letzten 100 Einträge
            if len(self.performance_history) > 100:
                self.performance_history.pop(0)
            
            # Analysiere die Leistungsdaten
            if len(self.performance_history) >= 10:
                self._analyze_performance_trends()
            
            # Optimiere Prioritäten basierend auf Ressourcennutzung
            self._optimize_priorities()
            
            logger.info("Warteschlange optimiert")
        except Exception as e:
            error = DownloadError(f"Fehler bei der Warteschlangen-Optimierung: {e}")
            handle_error(error, "intelligent_queue_optimize")
    
    def _collect_performance_data(self) -> Dict[str, Any]:
        """
        Sammelt aktuelle Leistungsdaten der Warteschlange.
        
        Returns:
            Dictionary mit Leistungsdaten
        """
        return {
            "timestamp": datetime.now(),
            "pending_items": len(self.pending_queue),
            "active_items": len(self.active_items),
            "completed_items": len(self.completed_items),
            "failed_items": len(self.failed_items),
            "resource_utilization": dict(self.resource_utilization),
            "batch_progress": dict(self.batch_progress)
        }
    
    def _analyze_performance_trends(self) -> None:
        """
        Analysiert Leistungstrends basierend auf der Historie.
        """
        # Berechne Durchschnittswerte der letzten 10 Messungen
        recent_data = self.performance_history[-10:]
        
        avg_pending = sum(data["pending_items"] for data in recent_data) / len(recent_data)
        avg_active = sum(data["active_items"] for data in recent_data) / len(recent_data)
        avg_completion_rate = sum(data["completed_items"] for data in recent_data) / len(recent_data)
        
        # Einfache Anpassung der maximalen gleichzeitigen Downloads
        if avg_active < self.max_concurrent_items * 0.5:
            # Wenn weniger als 50% der Kapazität genutzt wird, reduziere die Anzahl
            self.max_concurrent_items = max(1, self.max_concurrent_items - 1)
        elif avg_active > self.max_concurrent_items * 0.8 and len(self.pending_queue) > 5:
            # Wenn mehr als 80% der Kapazität genutzt wird und viele ausstehende Aufträge vorhanden sind, erhöhe die Anzahl
            self.max_concurrent_items += 1
        
        logger.info(f"Leistungstrends analysiert: Durchschnittlich {avg_active} aktive Aufträge")
    
    def _optimize_priorities(self) -> None:
        """
        Optimiert Prioritäten basierend auf Ressourcennutzung und Wartezeiten.
        """
        current_time = datetime.now()
        
        # Aktualisiere Ressourcennutzung für aktive Aufträge
        for item_id, item in self.active_items.items():
            # Berechne Wartezeit
            wait_time = (current_time - item.created_at).total_seconds()
            
            # Aktualisiere Ressourcennutzung (einfache Formel)
            self.resource_utilization[item_id] = min(1.0, wait_time / 3600)  # Normalisiert auf Stunden
        
        # Prüfe ausstehende Aufträge auf Prioritätsanpassungen
        for item in self.pending_queue:
            # Wenn ein Auftrag lange wartet, erhöhe die Priorität
            wait_time = (current_time - item.created_at).total_seconds()
            
            if wait_time > 7200:  # 2 Stunden
                if item.priority != Priority.CRITICAL:
                    old_priority = item.priority
                    item.priority = Priority.HIGH if item.priority == Priority.NORMAL else Priority.CRITICAL
                    item.sort_key = (-item.priority.value, item.created_at.timestamp(), item.id)
                    logger.info(f"Priorität von Auftrag {item.id} von {old_priority.name} auf {item.priority.name} erhöht")
        
        # Neuordnung des Heaps nach Prioritätsänderungen
        heapq.heapify(self.pending_queue)