#!/usr/bin/env python3
"""
LRU Cache Test - Telegram Audio Downloader
=========================================

Test für die LRU-Cache-Funktionalität.
"""

import sys
from pathlib import Path
import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from telegram_audio_downloader.downloader import LRUCache


class TestLRUCache:
    """Tests für den LRU-Cache."""
    
    def test_cache_creation(self):
        """Test der Cache-Erstellung."""
        cache = LRUCache(max_size=100)
        assert cache.max_size == 100
        assert len(cache) == 0
    
    def test_cache_put_and_get(self):
        """Test des Einfügens und Abrufens von Werten."""
        cache = LRUCache(max_size=100)
        
        # Put values
        cache.put("key1", True)
        cache.put("key2", False)
        
        # Get values
        assert cache.get("key1") is True
        assert cache.get("key2") is False
        assert cache.get("nonexistent") is None
        
        # Check cache size
        assert len(cache) == 2
    
    def test_cache_lru_behavior(self):
        """Test des LRU-Verhaltens."""
        cache = LRUCache(max_size=3)
        
        # Fill cache
        cache.put("key1", True)
        cache.put("key2", True)
        cache.put("key3", True)
        
        # Access key1 to make it most recently used
        assert cache.get("key1") is True
        
        # Add key4, which should evict key2 (least recently used)
        cache.put("key4", True)
        
        # Verify key2 was evicted and key4 was added
        assert cache.get("key1") is True  # Still there (recently used)
        assert cache.get("key2") is None  # Evicted
        assert cache.get("key3") is True  # Still there
        assert cache.get("key4") is True  # Newly added
        
        # Check cache size
        assert len(cache) == 3
    
    def test_cache_max_size_limit(self):
        """Test der maximalen Cache-Größe."""
        cache = LRUCache(max_size=2)
        
        # Add more items than max_size
        cache.put("key1", True)
        cache.put("key2", True)
        cache.put("key3", True)  # This should evict key1
        
        # Verify only the last two items remain
        assert cache.get("key1") is None  # Evicted
        assert cache.get("key2") is True  # Still there
        assert cache.get("key3") is True  # Most recent
        
        # Check cache size
        assert len(cache) == 2
    
    def test_cache_contains(self):
        """Test des 'in'-Operators."""
        cache = LRUCache(max_size=100)
        
        cache.put("key1", True)
        cache.put("key2", False)
        
        # Test contains
        assert "key1" in cache
        assert "key2" in cache
        assert "nonexistent" not in cache
    
    def test_cache_update_existing_key(self):
        """Test der Aktualisierung eines vorhandenen Schlüssels."""
        cache = LRUCache(max_size=100)
        
        # Add key with initial value
        cache.put("key1", True)
        assert cache.get("key1") is True
        
        # Update key with new value
        cache.put("key1", False)
        assert cache.get("key1") is False
        
        # Check cache size (should still be 1)
        assert len(cache) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])