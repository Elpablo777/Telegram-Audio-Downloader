"""
Tests für die Batch-Verarbeitung.
"""

import unittest
import asyncio
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

from src.telegram_audio_downloader.batch_processing import (
    BatchItem, BatchProcessor, Priority, ProgressCallback, ConsoleProgressCallback
)

class TestBatchItem(unittest.TestCase):
    """Tests für die BatchItem-Klasse."""
    
    def test_batch_item_creation(self):
        """Testet die Erstellung eines BatchItems."""
        item = BatchItem(
            id="test_001",
            group_name="Test Group",
            limit=10,
            priority=Priority.HIGH
        )
        
        self.assertEqual(item.id, "test_001")
        self.assertEqual(item.group_name, "Test Group")
        self.assertEqual(item.limit, 10)
        self.assertEqual(item.priority, Priority.HIGH)
        self.assertEqual(item.status, "pending")
        self.assertEqual(item.progress, 0.0)
        self.assertIsNone(item.error)
        self.assertEqual(item.metadata, {})
        self.assertIsNotNone(item.created_at)

class TestConsoleProgressCallback(unittest.TestCase):
    """Tests für die ConsoleProgressCallback-Klasse."""
    
    def setUp(self):
        """Erstellt eine Instanz der ConsoleProgressCallback-Klasse."""
        self.callback = ConsoleProgressCallback()
    
    def test_on_item_start(self):
        """Testet die on_item_start Methode."""
        item = BatchItem(id="test_001", group_name="Test Group")
        # Diese Methode ist async, daher müssen wir sie entsprechend testen
        async def run_test():
            await self.callback.on_item_start(item)
        asyncio.run(run_test())
        # Der Test ist erfolgreich, wenn keine Exception auftritt
    
    def test_on_item_progress(self):
        """Testet die on_item_progress Methode."""
        item = BatchItem(id="test_001", group_name="Test Group")
        # Diese Methode ist async, daher müssen wir sie entsprechend testen
        async def run_test():
            await self.callback.on_item_progress(item, 0.5)
        asyncio.run(run_test())
        # Der Test ist erfolgreich, wenn keine Exception auftritt
    
    def test_on_item_complete(self):
        """Testet die on_item_complete Methode."""
        item = BatchItem(id="test_001", group_name="Test Group")
        # Diese Methode ist async, daher müssen wir sie entsprechend testen
        async def run_test():
            await self.callback.on_item_complete(item)
        asyncio.run(run_test())
        # Der Test ist erfolgreich, wenn keine Exception auftritt
    
    def test_on_item_error(self):
        """Testet die on_item_error Methode."""
        item = BatchItem(id="test_001", group_name="Test Group")
        error = Exception("Test error")
        # Diese Methode ist async, daher müssen wir sie entsprechend testen
        async def run_test():
            await self.callback.on_item_error(item, error)
        asyncio.run(run_test())
        # Der Test ist erfolgreich, wenn keine Exception auftritt

class TestBatchProcessor(unittest.TestCase):
    """Tests für die BatchProcessor-Klasse."""
    
    def setUp(self):
        """Erstellt eine Instanz der BatchProcessor-Klasse."""
        self.processor = BatchProcessor(max_concurrent_batches=2)
    
    def test_add_batch_item(self):
        """Testet das Hinzufügen von Batch-Items."""
        item1 = BatchItem(id="test_001", group_name="Group 1", priority=Priority.NORMAL)
        item2 = BatchItem(id="test_002", group_name="Group 2", priority=Priority.HIGH)
        item3 = BatchItem(id="test_003", group_name="Group 3", priority=Priority.LOW)
        
        self.processor.add_batch_item(item1)
        self.processor.add_batch_item(item2)
        self.processor.add_batch_item(item3)
        
        # Prüfen, dass die Items in der richtigen Reihenfolge hinzugefügt wurden (Priorität)
        self.assertEqual(len(self.processor.batch_queue), 3)
        self.assertEqual(self.processor.batch_queue[0].id, "test_002")  # HIGH priority
        self.assertEqual(self.processor.batch_queue[1].id, "test_001")  # NORMAL priority
        self.assertEqual(self.processor.batch_queue[2].id, "test_003")  # LOW priority
    
    def test_get_progress(self):
        """Testet die Fortschrittsabfrage."""
        # Füge einige Items hinzu
        item1 = BatchItem(id="test_001", group_name="Group 1")
        item2 = BatchItem(id="test_002", group_name="Group 2")
        item3 = BatchItem(id="test_003", group_name="Group 3")
        
        self.processor.add_batch_item(item1)
        self.processor.add_batch_item(item2)
        self.processor.add_batch_item(item3)
        
        # Prüfe den initialen Fortschritt
        progress = self.processor.get_progress()
        self.assertEqual(progress["total_items"], 3)
        self.assertEqual(progress["pending_items"], 3)
        self.assertEqual(progress["active_items"], 0)
        self.assertEqual(progress["completed_items"], 0)
        self.assertEqual(progress["failed_items"], 0)
        self.assertEqual(progress["overall_progress"], 0.0)
    
    def test_process_batches(self):
        """Testet die Batch-Verarbeitung."""
        # Erstelle Mocks
        mock_download_function = AsyncMock()
        
        # Erstelle einen Prozessor
        processor = BatchProcessor(max_concurrent_batches=2)
        
        # Füge einige Items hinzu
        item1 = BatchItem(id="test_001", group_name="Group 1")
        item2 = BatchItem(id="test_002", group_name="Group 2")
        
        processor.add_batch_item(item1)
        processor.add_batch_item(item2)
        
        # Verarbeite die Batches
        asyncio.run(processor.process_batches(mock_download_function))
        
        # Prüfe, dass die Warteschlange leer ist und die Items verarbeitet wurden
        self.assertEqual(len(processor.batch_queue), 0)
        self.assertEqual(len(processor.completed_batches) + len(processor.failed_batches), 2)

if __name__ == "__main__":
    unittest.main()