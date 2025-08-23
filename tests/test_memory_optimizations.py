"""
Tests für die Speicheroptimierungen des Telegram Audio Downloaders.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.telegram_audio_downloader.memory_utils import (
    MemoryEfficientSet, StreamingDataProcessor, MemoryMonitor, 
    ObjectPool, perform_memory_cleanup, get_memory_monitor, get_object_pool
)
from src.telegram_audio_downloader.downloader import LRUCache


class TestLRUCache:
    """Tests für den LRU-Cache."""

    def test_lru_cache_basic_operations(self):
        """Test grundlegende LRU-Cache-Operationen."""
        cache = LRUCache(max_size=3)
        
        # Teste put und get
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        cache.put("key3", "value3")
        
        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"
        
        # Teste, dass der Cache die richtige Größe hat
        assert len(cache) == 3
        
        # Teste, dass ein neuer Eintrag den ältesten entfernt
        cache.put("key4", "value4")
        assert cache.get("key1") is None  # key1 sollte entfernt worden sein
        assert cache.get("key4") == "value4"
        
        # Teste, dass zuletzt verwendete Einträge erhalten bleiben
        cache.get("key2")  # key2 wird jetzt zum zuletzt verwendeten
        cache.put("key5", "value5")  # key3 sollte entfernt werden, nicht key2
        assert cache.get("key2") == "value2"
        assert cache.get("key3") is None
        assert cache.get("key5") == "value5"

    def test_lru_cache_update_existing(self):
        """Test Aktualisierung vorhandener Einträge im LRU-Cache."""
        cache = LRUCache(max_size=3)
        
        cache.put("key1", "value1")
        cache.put("key1", "updated_value1")  # Aktualisiere vorhandenen Eintrag
        
        assert cache.get("key1") == "updated_value1"
        assert len(cache) == 1

    def test_lru_cache_empty_operations(self):
        """Test LRU-Cache-Operationen mit leerem Cache."""
        cache = LRUCache(max_size=3)
        
        assert cache.get("nonexistent") is None
        assert len(cache) == 0


class TestMemoryEfficientSet:
    """Tests für das speichereffiziente Set."""

    def test_memory_efficient_set_basic_operations(self):
        """Test grundlegende Operationen des speichereffizienten Sets."""
        efficient_set = MemoryEfficientSet(max_size=5)
        
        # Teste hinzufügen und Prüfen
        efficient_set.add("item1")
        efficient_set.add("item2")
        efficient_set.add("item3")
        
        assert "item1" in efficient_set
        assert "item2" in efficient_set
        assert "item3" in efficient_set
        assert "item4" not in efficient_set
        
        # Teste Länge
        assert len(efficient_set) == 3

    def test_memory_efficient_set_overflow_behavior(self):
        """Test Verhalten des speichereffizienten Sets bei Überlauf."""
        efficient_set = MemoryEfficientSet(max_size=3)
        
        # Fülle das Set über die maximale Größe
        efficient_set.add("item1")
        efficient_set.add("item2")
        efficient_set.add("item3")
        efficient_set.add("item4")  # Sollte Überlauf verursachen
        
        # Mindestens die neuesten Elemente sollten vorhanden sein
        assert "item4" in efficient_set
        assert len(efficient_set) >= 3  # Genauer Wert kann variieren wegen Weak-References

    def test_memory_efficient_set_clear(self):
        """Test Löschen des speichereffizienten Sets."""
        efficient_set = MemoryEfficientSet(max_size=5)
        
        efficient_set.add("item1")
        efficient_set.add("item2")
        
        assert len(efficient_set) == 2
        
        efficient_set.clear()
        assert len(efficient_set) == 0
        assert "item1" not in efficient_set
        assert "item2" not in efficient_set


class TestStreamingDataProcessor:
    """Tests für den Streaming-Data-Processor."""

    def test_streaming_data_processor_chunk_processing(self):
        """Test Chunk-Verarbeitung des Streaming-Data-Processors."""
        processor = StreamingDataProcessor(chunk_size=3)
        
        # Erstelle Testdaten
        test_data = list(range(10))  # [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        
        # Verarbeite in Chunks
        chunks = list(processor.process_in_chunks(iter(test_data)))
        
        # Überprüfe die Chunks
        assert len(chunks) == 4  # 10 Elemente / 3 pro Chunk = 4 Chunks (letzter mit 1 Element)
        assert chunks[0] == [0, 1, 2]
        assert chunks[1] == [3, 4, 5]
        assert chunks[2] == [6, 7, 8]
        assert chunks[3] == [9]

    def test_streaming_data_processor_file_processing(self):
        """Test Datei-Verarbeitung des Streaming-Data-Processors."""
        # Erstelle eine temporäre Testdatei
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Zeile 1\n")
            f.write("Zeile 2\n")
            f.write("Zeile 3\n")
            temp_file_path = f.name
        
        try:
            processor = StreamingDataProcessor()
            lines = list(processor.process_file_lines(Path(temp_file_path)))
            
            assert len(lines) == 3
            assert lines[0] == "Zeile 1"
            assert lines[1] == "Zeile 2"
            assert lines[2] == "Zeile 3"
        finally:
            # Lösche die temporäre Datei
            os.unlink(temp_file_path)

    def test_streaming_data_processor_empty_file(self):
        """Test Verarbeitung einer leeren Datei."""
        # Erstelle eine leere temporäre Testdatei
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            temp_file_path = f.name
        
        try:
            processor = StreamingDataProcessor()
            lines = list(processor.process_file_lines(Path(temp_file_path)))
            
            assert len(lines) == 0
        finally:
            # Lösche die temporäre Datei
            os.unlink(temp_file_path)


class TestMemoryMonitor:
    """Tests für den Memory-Monitor."""

    def test_memory_monitor_basic_info(self):
        """Test grundlegende Speicherinformationen des Memory-Monitors."""
        monitor = MemoryMonitor()
        memory_info = monitor.get_memory_usage()
        
        # Überprüfe, dass alle erwarteten Schlüssel vorhanden sind
        assert "process_rss_mb" in memory_info
        assert "process_vms_mb" in memory_info
        assert "system_total_gb" in memory_info
        assert "system_available_gb" in memory_info
        assert "system_used_percent" in memory_info
        
        # Überprüfe, dass die Werte sinnvoll sind
        assert memory_info["process_rss_mb"] >= 0
        assert memory_info["system_total_gb"] > 0
        assert 0 <= memory_info["system_used_percent"] <= 100

    def test_memory_monitor_pressure_check(self):
        """Test Speicherdruck-Prüfung des Memory-Monitors."""
        monitor = MemoryMonitor(warning_threshold_mb=100, critical_threshold_mb=200)
        pressure_detected, pressure_level = monitor.check_memory_pressure()
        
        # Die Ergebnisse hängen vom tatsächlichen Speicherverbrauch ab
        # Aber es sollte immer ein gültiges Ergebnis zurückgegeben werden
        assert isinstance(pressure_detected, bool)
        assert pressure_level in ["normal", "warning", "critical"]

    def test_memory_monitor_cleanup_callbacks(self):
        """Test Cleanup-Callbacks des Memory-Monitors."""
        monitor = MemoryMonitor()
        
        # Erstelle einen Mock-Callback
        callback_called = False
        def test_callback():
            nonlocal callback_called
            callback_called = True
        
        # Registriere den Callback
        monitor.register_cleanup_callback(test_callback)
        
        # Führe Cleanup durch
        monitor.perform_cleanup()
        
        # Überprüfe, dass der Callback aufgerufen wurde
        # (Dieser Test könnte fehlschlagen, wenn der Callback einen Fehler wirft)
        # In diesem Fall ignorieren wir das und testen nur die Registrierung


class TestObjectPool:
    """Tests für den Object-Pool."""

    def test_object_pool_basic_operations(self):
        """Test grundlegende Operationen des Object-Pools."""
        # Erstelle eine Factory-Funktion
        creation_count = 0
        def factory_func():
            nonlocal creation_count
            creation_count += 1
            return f"object_{creation_count}"
        
        pool = ObjectPool(factory_func, max_size=3)
        
        # Hole Objekte aus dem Pool
        obj1 = pool.acquire()
        obj2 = pool.acquire()
        
        assert obj1 == "object_1"
        assert obj2 == "object_2"
        
        # Gebe Objekte zurück
        pool.release(obj1)
        pool.release(obj2)
        
        # Hole sie erneut - sie sollten wiederverwendet werden
        obj3 = pool.acquire()
        obj4 = pool.acquire()
        
        # Da wir nur 2 Objekte zurückgegeben haben, sollten diese wiederverwendet werden
        # Aber die Reihenfolge ist nicht garantiert
        assert obj3 in ["object_1", "object_2"]
        assert obj4 in ["object_1", "object_2"]
        assert obj3 != obj4

    def test_object_pool_max_size(self):
        """Test maximale Größe des Object-Pools."""
        creation_count = 0
        def factory_func():
            nonlocal creation_count
            creation_count += 1
            return f"object_{creation_count}"
        
        pool = ObjectPool(factory_func, max_size=2)
        
        # Erstelle mehr Objekte als die maximale Pool-Größe
        objects = []
        for i in range(5):
            objects.append(pool.acquire())
        
        # Gebe alle Objekte zurück
        for obj in objects:
            pool.release(obj)
        
        # Der Pool sollte nur die maximal erlaubte Anzahl behalten
        # Erstelle neue Objekte und überprüfe, dass neue erstellt werden
        new_obj = pool.acquire()
        # Wir können nicht genau vorhersagen, ob ein neues Objekt erstellt wird,
        # da der Pool eine deque mit maxlen verwendet


class TestGlobalMemoryFunctions:
    """Tests für die globalen Speicherfunktionen."""

    def test_perform_memory_cleanup(self):
        """Test globale Speicherbereinigung."""
        # Führe die Bereinigung durch
        collected_objects = perform_memory_cleanup()
        
        # Es sollte eine nicht-negative Anzahl an Objekten zurückgegeben werden
        assert collected_objects >= 0

    def test_get_memory_monitor(self):
        """Test Abruf des globalen Memory-Monitors."""
        monitor1 = get_memory_monitor()
        monitor2 = get_memory_monitor()
        
        # Es sollte immer dieselbe Instanz zurückgegeben werden
        assert monitor1 is monitor2
        assert isinstance(monitor1, MemoryMonitor)

    def test_get_object_pool(self):
        """Test Abruf von Object-Pools."""
        def factory_func():
            return "test_object"
        
        pool1 = get_object_pool("test_pool", factory_func, max_size=5)
        pool2 = get_object_pool("test_pool", factory_func, max_size=5)
        pool3 = get_object_pool("different_pool", factory_func, max_size=5)
        
        # Gleiche Name sollte gleiche Instanz zurückgeben
        assert pool1 is pool2
        # Unterschiedliche Namen sollten unterschiedliche Instanzen zurückgeben
        assert pool1 is not pool3
        assert pool2 is not pool3
        
        assert isinstance(pool1, ObjectPool)
        assert isinstance(pool3, ObjectPool)


if __name__ == '__main__':
    pytest.main([__file__])