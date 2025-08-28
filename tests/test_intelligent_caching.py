"""
Tests für das intelligente Caching-System.
"""

import asyncio
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.telegram_audio_downloader.intelligent_caching import (
    CacheEntry,
    BaseCache,
    MemoryCache,
    DiskCache,
    CDNCache,
    IntelligentCachingSystem,
    get_intelligent_cache
)


class TestCacheEntry(unittest.TestCase):
    """Tests für den CacheEntry."""
    
    def test_cache_entry_creation(self):
        """Test der CacheEntry-Erstellung."""
        entry = CacheEntry("test_key", "test_value", 100)
        
        self.assertEqual(entry.key, "test_key")
        self.assertEqual(entry.value, "test_value")
        self.assertFalse(entry.is_expired())
        self.assertEqual(entry.access_count, 0)
        
    def test_cache_entry_expiration(self):
        """Test der CacheEntry-Ablaufprüfung."""
        # Eintrag mit negativer TTL sollte sofort ablaufen
        entry = CacheEntry("test_key", "test_value", -1)
        self.assertTrue(entry.is_expired())
        
        # Eintrag ohne Ablauf (ttl=None) sollte nie ablaufen
        entry = CacheEntry("test_key", "test_value", None)
        self.assertFalse(entry.is_expired())
        
    def test_cache_entry_access(self):
        """Test der CacheEntry-Zugriffsmethoden."""
        entry = CacheEntry("test_key", "test_value", 100)
        
        # Prüfe initiale Werte
        self.assertEqual(entry.access_count, 0)
        
        # Markiere als zugegriffen
        entry.access()
        
        # Prüfe aktualisierte Werte
        self.assertEqual(entry.access_count, 1)
        
    def test_cache_entry_ttl(self):
        """Test der CacheEntry-TTL-Berechnung."""
        entry = CacheEntry("test_key", "test_value", 100)
        
        # TTL sollte positiv sein
        ttl = entry.get_ttl()
        self.assertIsNotNone(ttl)
        if ttl is not None:
            self.assertGreaterEqual(ttl, 0)
            self.assertLessEqual(ttl, 100)
        
        # Eintrag ohne Ablauf sollte None zurückgeben
        entry_no_expiry = CacheEntry("test_key", "test_value", None)
        self.assertIsNone(entry_no_expiry.get_ttl())


class TestMemoryCache(unittest.TestCase):
    """Tests für den MemoryCache."""
    
    def setUp(self):
        """Test-Setup."""
        self.cache = MemoryCache(max_size=3, default_ttl=100)
        
    def test_memory_cache_creation(self):
        """Test der MemoryCache-Erstellung."""
        self.assertEqual(self.cache.max_size, 3)
        self.assertEqual(self.cache.default_ttl, 100)
        self.assertEqual(self.cache.stats["hits"], 0)
        self.assertEqual(self.cache.stats["misses"], 0)
        
    async def test_memory_cache_put_and_get(self):
        """Test des Einfügens und Abrufens von Werten."""
        # Füge Werte hinzu
        await self.cache.put("key1", "value1")
        await self.cache.put("key2", "value2")
        
        # Rufe Werte ab
        value1 = await self.cache.get("key1")
        value2 = await self.cache.get("key2")
        value3 = await self.cache.get("key3")  # Nicht existent
        
        self.assertEqual(value1, "value1")
        self.assertEqual(value2, "value2")
        self.assertIsNone(value3)
        
        # Prüfe Statistiken
        self.assertEqual(self.cache.stats["hits"], 2)
        self.assertEqual(self.cache.stats["misses"], 1)
        
    async def test_memory_cache_lru_behavior(self):
        """Test des LRU-Verhaltens."""
        # Fülle den Cache
        await self.cache.put("key1", "value1")
        await self.cache.put("key2", "value2")
        await self.cache.put("key3", "value3")
        
        # Greife auf key1 zu, um es zum zuletzt verwendeten zu machen
        value = await self.cache.get("key1")
        self.assertEqual(value, "value1")
        
        # Füge einen neuen Eintrag hinzu - key2 sollte entfernt werden
        await self.cache.put("key4", "value4")
        
        # Prüfe, dass key2 entfernt wurde und die anderen noch da sind
        self.assertIsNone(await self.cache.get("key2"))
        self.assertEqual(await self.cache.get("key1"), "value1")
        self.assertEqual(await self.cache.get("key3"), "value3")
        self.assertEqual(await self.cache.get("key4"), "value4")
        
    async def test_memory_cache_expiration(self):
        """Test der Ablaufprüfung."""
        # Erstelle einen Eintrag mit 0 TTL (sofort abgelaufen)
        await self.cache.put("key1", "value1", ttl=0)
        
        # Der Eintrag sollte nicht abrufbar sein
        value = await self.cache.get("key1")
        self.assertIsNone(value)
        
    async def test_memory_cache_delete(self):
        """Test des Löschens von Einträgen."""
        # Füge einen Eintrag hinzu
        await self.cache.put("key1", "value1")
        
        # Prüfe, dass er existiert
        self.assertEqual(await self.cache.get("key1"), "value1")
        
        # Lösche den Eintrag
        result = await self.cache.delete("key1")
        self.assertTrue(result)
        
        # Prüfe, dass er nicht mehr existiert
        self.assertIsNone(await self.cache.get("key1"))
        
        # Versuche, einen nicht existierenden Eintrag zu löschen
        result = await self.cache.delete("key2")
        self.assertFalse(result)
        
    async def test_memory_cache_clear(self):
        """Test des Leerens des Caches."""
        # Füge einige Einträge hinzu
        await self.cache.put("key1", "value1")
        await self.cache.put("key2", "value2")
        
        # Prüfe, dass sie existieren
        self.assertEqual(await self.cache.size(), 2)
        
        # Leere den Cache
        await self.cache.clear()
        
        # Prüfe, dass er leer ist
        self.assertEqual(await self.cache.size(), 0)
        self.assertIsNone(await self.cache.get("key1"))
        self.assertIsNone(await self.cache.get("key2"))


class TestDiskCache(unittest.TestCase):
    """Tests für den DiskCache."""
    
    def setUp(self):
        """Test-Setup."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.cache = DiskCache(self.test_dir, max_size=3, default_ttl=100)
        
    def tearDown(self):
        """Test-Cleanup."""
        # Entferne das Testverzeichnis
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
        
    async def test_disk_cache_creation(self):
        """Test der DiskCache-Erstellung."""
        self.assertEqual(self.cache.max_size, 3)
        self.assertEqual(self.cache.default_ttl, 100)
        self.assertTrue(self.cache.cache_dir.exists())
        
    async def test_disk_cache_put_and_get(self):
        """Test des Einfügens und Abrufens von Werten."""
        # Füge Werte hinzu
        await self.cache.put("key1", "value1")
        await self.cache.put("key2", "value2")
        
        # Rufe Werte ab
        value1 = await self.cache.get("key1")
        value2 = await self.cache.get("key2")
        value3 = await self.cache.get("key3")  # Nicht existent
        
        self.assertEqual(value1, "value1")
        self.assertEqual(value2, "value2")
        self.assertIsNone(value3)
        
    async def test_disk_cache_delete(self):
        """Test des Löschens von Einträgen."""
        # Füge einen Eintrag hinzu
        await self.cache.put("key1", "value1")
        
        # Prüfe, dass er existiert
        self.assertEqual(await self.cache.get("key1"), "value1")
        
        # Lösche den Eintrag
        result = await self.cache.delete("key1")
        self.assertTrue(result)
        
        # Prüfe, dass er nicht mehr existiert
        self.assertIsNone(await self.cache.get("key1"))
        
    async def test_disk_cache_clear(self):
        """Test des Leerens des Caches."""
        # Füge einige Einträge hinzu
        await self.cache.put("key1", "value1")
        await self.cache.put("key2", "value2")
        
        # Prüfe, dass Cache-Dateien existieren
        cache_files = list(self.cache.cache_dir.glob("*.cache"))
        self.assertGreater(len(cache_files), 0)
        
        # Leere den Cache
        await self.cache.clear()
        
        # Prüfe, dass keine Cache-Dateien mehr existieren
        cache_files = list(self.cache.cache_dir.glob("*.cache"))
        self.assertEqual(len(cache_files), 0)


class TestCDNCache(unittest.TestCase):
    """Tests für den CDNCache."""
    
    def setUp(self):
        """Test-Setup."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.cache = CDNCache(self.test_dir, max_size=3, default_ttl=100)
        
    def tearDown(self):
        """Test-Cleanup."""
        # Entferne das Testverzeichnis
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
        
    async def test_cdn_cache_creation(self):
        """Test der CDNCache-Erstellung."""
        self.assertEqual(self.cache.max_size, 3)
        self.assertEqual(self.cache.default_ttl, 100)
        self.assertTrue(self.cache.cache_dir.exists())
        
    async def test_cdn_cache_put_and_get(self):
        """Test des Einfügens und Abrufens von Werten."""
        # Füge Werte hinzu
        await self.cache.put("key1", "value1")
        await self.cache.put("key2", "value2")
        
        # Rufe Werte ab
        value1 = await self.cache.get("key1")
        value2 = await self.cache.get("key2")
        value3 = await self.cache.get("key3")  # Nicht existent
        
        self.assertEqual(value1, "value1")
        self.assertEqual(value2, "value2")
        self.assertIsNone(value3)
        
    async def test_cdn_cache_delete(self):
        """Test des Löschens von Einträgen."""
        # Füge einen Eintrag hinzu
        await self.cache.put("key1", "value1")
        
        # Prüfe, dass er existiert
        self.assertEqual(await self.cache.get("key1"), "value1")
        
        # Lösche den Eintrag
        result = await self.cache.delete("key1")
        self.assertTrue(result)
        
        # Prüfe, dass er nicht mehr existiert
        self.assertIsNone(await self.cache.get("key1"))
        
    async def test_cdn_cache_clear(self):
        """Test des Leerens des Caches."""
        # Füge einige Einträge hinzu
        await self.cache.put("key1", "value1")
        await self.cache.put("key2", "value2")
        
        # Prüfe, dass Cache-Dateien existieren
        cache_files = list(self.cache.cache_dir.glob("*.cdn"))
        self.assertGreater(len(cache_files), 0)
        
        # Leere den Cache
        await self.cache.clear()
        
        # Prüfe, dass keine Cache-Dateien mehr existieren
        cache_files = list(self.cache.cache_dir.glob("*.cdn"))
        self.assertEqual(len(cache_files), 0)


class TestIntelligentCachingSystem(unittest.TestCase):
    """Tests für das IntelligentCachingSystem."""
    
    def setUp(self):
        """Test-Setup."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.cache_system = IntelligentCachingSystem(self.test_dir)
        
    def tearDown(self):
        """Test-Cleanup."""
        # Entferne das Testverzeichnis
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
        
    async def test_cache_system_creation(self):
        """Test der Cache-System-Erstellung."""
        self.assertIsInstance(self.cache_system.memory_cache, MemoryCache)
        self.assertIsInstance(self.cache_system.disk_cache, DiskCache)
        self.assertIsInstance(self.cache_system.cdn_cache, CDNCache)
        
    async def test_cache_system_put_and_get(self):
        """Test des Einfügens und Abrufens von Werten."""
        # Füge einen Wert hinzu
        await self.cache_system.put("key1", "value1")
        
        # Rufe den Wert ab
        value = await self.cache_system.get("key1")
        self.assertEqual(value, "value1")
        
    async def test_cache_system_multi_level_get(self):
        """Test des mehrstufigen Abrufens."""
        # Füge einen Wert nur zum CDN-Cache hinzu
        await self.cache_system.cdn_cache.put("key1", "value1")
        
        # Rufe den Wert über das System ab
        value = await self.cache_system.get("key1")
        self.assertEqual(value, "value1")
        
        # Prüfe, dass der Wert auch in den anderen Caches ist (Promotion)
        mem_value = await self.cache_system.memory_cache.get("key1")
        disk_value = await self.cache_system.disk_cache.get("key1")
        self.assertEqual(mem_value, "value1")
        self.assertEqual(disk_value, "value1")
        
    async def test_cache_system_delete(self):
        """Test des Löschens von Einträgen."""
        # Füge einen Wert hinzu
        await self.cache_system.put("key1", "value1")
        
        # Prüfe, dass er in allen Caches existiert
        self.assertEqual(await self.cache_system.get("key1"), "value1")
        
        # Lösche den Eintrag
        result = await self.cache_system.delete("key1")
        self.assertTrue(result)
        
        # Prüfe, dass er in keinem Cache mehr existiert
        self.assertIsNone(await self.cache_system.get("key1"))
        self.assertIsNone(await self.cache_system.memory_cache.get("key1"))
        self.assertIsNone(await self.cache_system.disk_cache.get("key1"))
        self.assertIsNone(await self.cache_system.cdn_cache.get("key1"))
        
    async def test_cache_system_clear(self):
        """Test des Leerens des Caches."""
        # Füge einige Einträge hinzu
        await self.cache_system.put("key1", "value1")
        await self.cache_system.put("key2", "value2")
        
        # Prüfe, dass sie existieren
        self.assertEqual(await self.cache_system.get("key1"), "value1")
        self.assertEqual(await self.cache_system.get("key2"), "value2")
        
        # Leere alle Caches
        await self.cache_system.clear()
        
        # Prüfe, dass sie nicht mehr existieren
        self.assertIsNone(await self.cache_system.get("key1"))
        self.assertIsNone(await self.cache_system.get("key2"))
        
    async def test_cache_system_stats(self):
        """Test der Statistik."""
        # Füge einige Einträge hinzu und rufe sie ab
        await self.cache_system.put("key1", "value1")
        await self.cache_system.get("key1")
        await self.cache_system.get("key2")  # Nicht existent
        
        # Hole die Statistiken
        stats = await self.cache_system.get_stats()
        
        # Prüfe, dass die Statistiken vorhanden sind
        self.assertIn("memory", stats)
        self.assertIn("disk", stats)
        self.assertIn("cdn", stats)
        self.assertIn("hits", stats["memory"])
        self.assertIn("misses", stats["memory"])
        self.assertGreaterEqual(stats["memory_size"], 0)
        self.assertGreaterEqual(stats["disk_size"], 0)
        self.assertGreaterEqual(stats["cdn_size"], 0)


class TestGlobalCacheFunction(unittest.TestCase):
    """Tests für die globale Cache-Funktion."""
    
    def setUp(self):
        """Test-Setup."""
        # Setze den globalen Cache zurück
        from src.telegram_audio_downloader.intelligent_caching import _intelligent_cache
        if _intelligent_cache is not None:
            # Leere den Cache
            asyncio.run(_intelligent_cache.clear())
            
    def tearDown(self):
        """Test-Cleanup."""
        # Setze den globalen Cache zurück
        from src.telegram_audio_downloader.intelligent_caching import _intelligent_cache
        if _intelligent_cache is not None:
            # Entferne das Cache-Verzeichnis
            import shutil
            cache_dir = _intelligent_cache.cache_dir
            asyncio.run(_intelligent_cache.clear())
            shutil.rmtree(cache_dir, ignore_errors=True)
            
    def test_get_intelligent_cache(self):
        """Test der globalen Cache-Funktion."""
        # Hole die Cache-Instanz
        cache1 = get_intelligent_cache()
        cache2 = get_intelligent_cache()
        
        # Es sollte immer dieselbe Instanz zurückgegeben werden
        self.assertIs(cache1, cache2)
        
        # Es sollte eine IntelligentCachingSystem-Instanz sein
        self.assertIsInstance(cache1, IntelligentCachingSystem)


if __name__ == "__main__":
    unittest.main()