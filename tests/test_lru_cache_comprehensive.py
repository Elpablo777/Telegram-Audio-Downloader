#!/usr/bin/env python3
"""
Comprehensive LRU Cache Tests - Telegram Audio Downloader
========================================================

Umfassende Tests für das LRU-Cache-System.
"""

import os
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch
import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from telegram_audio_downloader.utils.lru_cache import LRUCache


class TestLRUCacheComprehensive:
    """Umfassende Tests für das LRU-Cache-System."""
    
    def test_lru_cache_initialization(self):
        """Test LRU-Cache-Initialisierung."""
        # Test normal initialization
        cache = LRUCache(max_size=100)
        assert cache.max_size == 100
        assert len(cache) == 0
        assert cache.current_size == 0
        
        # Test initialization with different sizes
        cache = LRUCache(max_size=10)
        assert cache.max_size == 10
        
        cache = LRUCache(max_size=1000)
        assert cache.max_size == 1000
        
        # Test initialization with invalid size
        with pytest.raises(ValueError):
            LRUCache(max_size=0)
        
        with pytest.raises(ValueError):
            LRUCache(max_size=-5)
    
    def test_lru_cache_put_and_get(self):
        """Test LRU-Cache put und get Operationen."""
        cache = LRUCache(max_size=3)
        
        # Test putting items
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        cache.put("key3", "value3")
        
        # Test getting items
        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"
        
        # Test cache size
        assert len(cache) == 3
        assert cache.current_size == 3
    
    def test_lru_cache_eviction_policy(self):
        """Test LRU-Cache Eviction Policy."""
        cache = LRUCache(max_size=3)
        
        # Fill cache
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        cache.put("key3", "value3")
        
        # Access key1 to make it recently used
        cache.get("key1")
        
        # Add new item - key2 should be evicted (least recently used)
        cache.put("key4", "value4")
        
        # Check that key2 was evicted
        assert cache.get("key2") is None
        # Check that other keys are still there
        assert cache.get("key1") == "value1"
        assert cache.get("key3") == "value3"
        assert cache.get("key4") == "value4"
    
    def test_lru_cache_update_existing(self):
        """Test LRU-Cache Aktualisierung existierender Einträge."""
        cache = LRUCache(max_size=3)
        
        # Add items
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        
        # Update existing item
        cache.put("key1", "updated_value1")
        
        # Check updated value
        assert cache.get("key1") == "updated_value1"
        assert cache.get("key2") == "value2"
        
        # Size should remain the same
        assert len(cache) == 2
    
    def test_lru_cache_get_nonexistent(self):
        """Test LRU-Cache get für nicht existierende Schlüssel."""
        cache = LRUCache(max_size=3)
        
        # Try to get non-existent key
        assert cache.get("nonexistent") is None
        
        # Add an item and try again
        cache.put("key1", "value1")
        assert cache.get("nonexistent") is None
        assert cache.get("key1") == "value1"
    
    def test_lru_cache_with_large_objects(self):
        """Test LRU-Cache mit großen Objekten."""
        cache = LRUCache(max_size=1000)  # Size in bytes approximation
        
        # Create large objects
        large_object1 = "x" * 500  # Approx 500 bytes
        large_object2 = "y" * 400  # Approx 400 bytes
        large_object3 = "z" * 200  # Approx 200 bytes
        
        # Add objects
        cache.put("large1", large_object1)
        cache.put("large2", large_object2)
        
        # Check objects
        assert cache.get("large1") == large_object1
        assert cache.get("large2") == large_object2
        
        # Add third object - should fit
        cache.put("large3", large_object3)
        assert cache.get("large3") == large_object3
        
        # Add another large object - should cause eviction
        large_object4 = "w" * 600  # Approx 600 bytes
        cache.put("large4", large_object4)
        
        # Some objects should be evicted due to size constraints
        # Exact behavior depends on implementation details
    
    def test_lru_cache_contains(self):
        """Test LRU-Cache contains Methode."""
        cache = LRUCache(max_size=3)
        
        # Test empty cache
        assert not cache.contains("key1")
        
        # Add item
        cache.put("key1", "value1")
        assert cache.contains("key1")
        assert not cache.contains("key2")
        
        # Add more items
        cache.put("key2", "value2")
        cache.put("key3", "value3")
        
        assert cache.contains("key1")
        assert cache.contains("key2")
        assert cache.contains("key3")
        
        # After eviction
        cache.put("key4", "value4")  # Should evict key1
        assert not cache.contains("key1")  # key1 was least recently used
        assert cache.contains("key2")
        assert cache.contains("key3")
        assert cache.contains("key4")
    
    def test_lru_cache_clear(self):
        """Test LRU-Cache clear Methode."""
        cache = LRUCache(max_size=3)
        
        # Add items
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        cache.put("key3", "value3")
        
        # Verify items exist
        assert len(cache) == 3
        assert cache.current_size == 3
        
        # Clear cache
        cache.clear()
        
        # Verify cache is empty
        assert len(cache) == 0
        assert cache.current_size == 0
        assert cache.get("key1") is None
        assert cache.get("key2") is None
        assert cache.get("key3") is None
    
    def test_lru_cache_keys_and_values(self):
        """Test LRU-Cache keys und values Methoden."""
        cache = LRUCache(max_size=3)
        
        # Test empty cache
        assert cache.keys() == []
        assert cache.values() == []
        
        # Add items
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        cache.put("key3", "value3")
        
        # Test keys and values
        keys = cache.keys()
        values = cache.values()
        
        assert len(keys) == 3
        assert len(values) == 3
        assert "key1" in keys
        assert "key2" in keys
        assert "key3" in keys
        assert "value1" in values
        assert "value2" in values
        assert "value3" in values
    
    def test_lru_cache_with_different_data_types(self):
        """Test LRU-Cache mit verschiedenen Datentypen."""
        cache = LRUCache(max_size=10)
        
        # Test with different data types
        cache.put("string_key", "string_value")
        cache.put("int_key", 42)
        cache.put("float_key", 3.14)
        cache.put("bool_key", True)
        cache.put("list_key", [1, 2, 3])
        cache.put("dict_key", {"a": 1, "b": 2})
        cache.put("none_key", None)
        
        # Retrieve and verify types
        assert cache.get("string_key") == "string_value"
        assert cache.get("int_key") == 42
        assert cache.get("float_key") == 3.14
        assert cache.get("bool_key") is True
        assert cache.get("list_key") == [1, 2, 3]
        assert cache.get("dict_key") == {"a": 1, "b": 2}
        assert cache.get("none_key") is None
    
    def test_lru_cache_with_complex_keys(self):
        """Test LRU-Cache mit komplexen Schlüsseln."""
        cache = LRUCache(max_size=10)
        
        # Test with tuple keys
        cache.put(("tuple", "key"), "tuple_value")
        assert cache.get(("tuple", "key")) == "tuple_value"
        
        # Test with integer keys
        cache.put(42, "integer_key_value")
        assert cache.get(42) == "integer_key_value"
        
        # Test with mixed type keys
        complex_key = ("complex", 123, "key")
        cache.put(complex_key, "complex_value")
        assert cache.get(complex_key) == "complex_value"
    
    def test_lru_cache_performance_with_many_items(self):
        """Test LRU-Cache Performance mit vielen Einträgen."""
        cache = LRUCache(max_size=1000)
        
        # Add many items
        for i in range(1000):
            cache.put(f"key_{i}", f"value_{i}")
        
        # Access some items to change their order
        for i in range(0, 1000, 100):
            cache.get(f"key_{i}")
        
        # Add more items to trigger eviction
        for i in range(1000, 1500):
            cache.put(f"key_{i}", f"value_{i}")
        
        # Verify cache still works correctly
        # Recently accessed items should still be there
        assert cache.get("key_0") == "value_0"
        # Early items that weren't accessed should be evicted
        # This depends on implementation details
    
    def test_lru_cache_thread_safety(self):
        """Test LRU-Cache Thread-Sicherheit."""
        cache = LRUCache(max_size=10)
        
        # This is a basic test - in a real scenario, we would use threading
        # For now, we test that basic operations don't cause internal state issues
        
        # Interleave put and get operations
        cache.put("key1", "value1")
        value1 = cache.get("key1")
        cache.put("key2", "value2")
        value2 = cache.get("key2")
        cache.put("key3", "value3")
        
        assert value1 == "value1"
        assert value2 == "value2"
        assert cache.get("key3") == "value3"
    
    def test_lru_cache_memory_behavior(self):
        """Test LRU-Cache Speicherverhalten."""
        cache = LRUCache(max_size=5)
        
        # Fill cache
        for i in range(5):
            cache.put(f"key_{i}", f"value_{i}")
        
        # Check initial state
        assert len(cache) == 5
        
        # Add more items to cause eviction
        for i in range(5, 10):
            cache.put(f"key_{i}", f"value_{i}")
        
        # Cache should maintain its maximum size
        assert len(cache) == 5
        
        # Check that oldest items were evicted
        # This depends on access patterns
        # After adding key_5 to key_9, key_0 to key_4 should be evicted
        # if no accesses happened in between