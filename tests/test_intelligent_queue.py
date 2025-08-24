#!/usr/bin/env python3
"""
Tests für die intelligente Warteschlange - Telegram Audio Downloader
====================================================================

Tests für die intelligente Warteschlange mit Priorisierung und 
Abhängigkeitsverwaltung.
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from telegram_audio_downloader.intelligent_queue import (
    IntelligentQueue, QueueItem, Priority, DependencyType, DownloadStatus
)

class TestIntelligentQueue:
    """Tests für die intelligente Warteschlange."""
    
    def test_queue_initialization(self):
        """Test initialisiert die intelligente Warteschlange."""
        queue = IntelligentQueue(max_concurrent_items=5)
        
        assert queue.max_concurrent_items == 5
        assert len(queue.pending_queue) == 0
        assert len(queue.active_items) == 0
        assert len(queue.completed_items) == 0
        assert len(queue.failed_items) == 0
    
    def test_add_item(self):
        """Test fügt ein Element zur Warteschlange hinzu."""
        queue = IntelligentQueue()
        
        item = QueueItem(
            id="test1",
            group_name="Test Group",
            priority=Priority.NORMAL,
            created_at=datetime.now()
        )
        
        queue.add_item(item)
        
        assert len(queue.pending_queue) == 1
        # Überprüfe, ob das Element in der Warteschlange ist
        pending_item = queue.pending_queue[0]
        assert pending_item.id == "test1"
        assert pending_item.group_name == "Test Group"
        assert pending_item.priority == Priority.NORMAL
    
    def test_remove_item(self):
        """Test entfernt ein Element aus der Warteschlange."""
        queue = IntelligentQueue()
        
        item = QueueItem(
            id="test1",
            group_name="Test Group",
            priority=Priority.NORMAL,
            created_at=datetime.now()
        )
        
        queue.add_item(item)
        assert len(queue.pending_queue) == 1
        
        result = queue.remove_item("test1")
        assert result is True
        assert len(queue.pending_queue) == 0
    
    def test_remove_nonexistent_item(self):
        """Test entfernt ein nicht existierendes Element."""
        queue = IntelligentQueue()
        
        result = queue.remove_item("nonexistent")
        assert result is False
    
    def test_get_next_item_no_dependencies(self):
        """Test holt das nächste Element ohne Abhängigkeiten."""
        queue = IntelligentQueue()
        
        item1 = QueueItem(
            id="test1",
            group_name="Test Group 1",
            priority=Priority.NORMAL,
            created_at=datetime.now()
        )
        
        item2 = QueueItem(
            id="test2",
            group_name="Test Group 2",
            priority=Priority.HIGH,
            created_at=datetime.now()
        )
        
        queue.add_item(item1)
        queue.add_item(item2)
        
        # Das Element mit hoher Priorität sollte zuerst kommen
        next_item = queue.get_next_item()
        assert next_item is not None
        assert next_item.id == "test2"
        assert next_item.status == DownloadStatus.DOWNLOADING
        assert next_item.id in queue.active_items
    
    def test_get_next_item_with_dependencies(self):
        """Test holt das nächste Element mit Abhängigkeiten."""
        queue = IntelligentQueue()
        
        # Abhängigkeit: test2 muss vor test1 ausgeführt werden
        item1 = QueueItem(
            id="test1",
            group_name="Test Group 1",
            priority=Priority.NORMAL,
            created_at=datetime.now(),
            dependencies={"test2"}
        )
        
        item2 = QueueItem(
            id="test2",
            group_name="Test Group 2",
            priority=Priority.NORMAL,
            created_at=datetime.now()
        )
        
        queue.add_item(item1)
        queue.add_item(item2)
        
        # Zuerst sollte item2 kommen, da item1 von item2 abhängt
        next_item = queue.get_next_item()
        assert next_item is not None
        assert next_item.id == "test2"
        
        # Nach Abschluss von item2 sollte item1 kommen
        queue.mark_item_completed("test2")
        next_item = queue.get_next_item()
        assert next_item is not None
        assert next_item.id == "test1"
    
    def test_mark_item_completed(self):
        """Test markiert ein Element als abgeschlossen."""
        queue = IntelligentQueue()
        
        item = QueueItem(
            id="test1",
            group_name="Test Group",
            priority=Priority.NORMAL,
            created_at=datetime.now()
        )
        
        queue.add_item(item)
        next_item = queue.get_next_item()
        assert next_item is not None
        assert next_item.id == "test1"
        assert len(queue.active_items) == 1
        
        queue.mark_item_completed("test1")
        assert len(queue.active_items) == 0
        assert len(queue.completed_items) == 1
        assert "test1" in queue.completed_items
    
    def test_mark_item_failed(self):
        """Test markiert ein Element als fehlgeschlagen."""
        queue = IntelligentQueue()
        
        item = QueueItem(
            id="test1",
            group_name="Test Group",
            priority=Priority.NORMAL,
            created_at=datetime.now()
        )
        
        queue.add_item(item)
        next_item = queue.get_next_item()
        assert next_item is not None
        assert next_item.id == "test1"
        assert len(queue.active_items) == 1
        
        queue.mark_item_failed("test1", "Test error")
        assert len(queue.active_items) == 0
        assert len(queue.failed_items) == 1
        assert "test1" in queue.failed_items
        assert queue.failed_items["test1"].error_message == "Test error"
    
    def test_dynamic_prioritization(self):
        """Test ändert die Priorität eines Elements dynamisch."""
        queue = IntelligentQueue()
        
        item = QueueItem(
            id="test1",
            group_name="Test Group",
            priority=Priority.NORMAL,
            created_at=datetime.now()
        )
        
        queue.add_item(item)
        assert queue.pending_queue[0].priority == Priority.NORMAL
        
        queue.update_item_priority("test1", Priority.HIGH)
        # Das Element sollte neu sortiert worden sein
        queue.pending_queue.sort()
        assert queue.pending_queue[0].priority == Priority.HIGH
    
    def test_resource_control(self):
        """Test begrenzt die Anzahl gleichzeitiger Downloads."""
        queue = IntelligentQueue(max_concurrent_items=2)
        
        # Füge 3 Elemente hinzu
        for i in range(3):
            item = QueueItem(
                id=f"test{i}",
                group_name=f"Test Group {i}",
                priority=Priority.NORMAL,
                created_at=datetime.now()
            )
            queue.add_item(item)
        
        # Hole die ersten beiden Elemente
        item1 = queue.get_next_item()
        item2 = queue.get_next_item()
        assert item1 is not None
        assert item2 is not None
        
        # Das dritte Element sollte nicht verfügbar sein, da das Limit erreicht ist
        item3 = queue.get_next_item()
        assert item3 is None
        
        # Nach Abschluss eines Elements sollte das dritte verfügbar werden
        queue.mark_item_completed(item1.id)
        item3 = queue.get_next_item()
        assert item3 is not None
        assert item3.id == "test2"