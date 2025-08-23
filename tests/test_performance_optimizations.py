"""
Tests für die Performance-Optimierungen des Telegram Audio Downloaders.
"""

import pytest
import time
import asyncio
from unittest.mock import patch, MagicMock

from src.telegram_audio_downloader.performance import (
    PerformanceMonitor, RateLimiter, DownloadStatistics, 
    get_performance_monitor, format_bytes, format_duration
)
from src.telegram_audio_downloader.memory_utils import (
    MemoryEfficientSet, StreamingDataProcessor, MemoryMonitor, 
    ObjectPool, perform_memory_cleanup
)
from src.telegram_audio_downloader.downloader import LRUCache


class TestPerformanceMonitor:
    """Tests für den Performance-Monitor."""

    def test_performance_monitor_basic_operations(self):
        """Test grundlegende Operationen des Performance-Monitors."""
        monitor = PerformanceMonitor()
        
        # Teste das Starten und Beenden eines Downloads
        download_id = monitor.start_download("test_file.mp3", 1024000)  # 1MB
        assert download_id is not None
        
        # Simuliere etwas Download-Zeit
        time.sleep(0.01)
        
        # Beende den Download
        monitor.end_download(download_id, success=True)
        
        # Überprüfe die Statistiken
        stats = monitor.get_statistics()
        assert stats["completed_downloads"] == 1
        assert stats["failed_downloads"] == 0
        assert stats["total_bytes_downloaded"] == 1024000

    def test_performance_monitor_failed_download(self):
        """Test fehlgeschlagener Download im Performance-Monitor."""
        monitor = PerformanceMonitor()
        
        # Teste einen fehlgeschlagenen Download
        download_id = monitor.start_download("failed_file.mp3", 512000)  # 512KB
        time.sleep(0.01)
        monitor.end_download(download_id, success=False)
        
        # Überprüfe die Statistiken
        stats = monitor.get_statistics()
        assert stats["completed_downloads"] == 0
        assert stats["failed_downloads"] == 1
        assert stats["total_bytes_downloaded"] == 0

    def test_performance_monitor_concurrent_downloads(self):
        """Test gleichzeitige Downloads im Performance-Monitor."""
        monitor = PerformanceMonitor()
        
        # Starte mehrere Downloads
        download_ids = []
        for i in range(5):
            download_id = monitor.start_download(f"file_{i}.mp3", 102400 * (i + 1))
            download_ids.append(download_id)
        
        # Überprüfe aktive Downloads
        active_downloads = monitor.get_active_downloads()
        assert len(active_downloads) == 5
        
        # Beende einige Downloads
        for i, download_id in enumerate(download_ids[:3]):
            monitor.end_download(download_id, success=True)
        
        # Überprüfe aktive Downloads erneut
        active_downloads = monitor.get_active_downloads()
        assert len(active_downloads) == 2

    def test_performance_monitor_get_report(self):
        """Test Performance-Report des Monitors."""
        monitor = PerformanceMonitor()
        
        # Führe einige Operationen durch
        download_id = monitor.start_download("test_file.mp3", 2048000)  # 2MB
        time.sleep(0.01)
        monitor.end_download(download_id, success=True)
        
        # Hole den Report
        report = monitor.get_performance_report()
        
        # Überprüfe die Report-Struktur
        assert "uptime_seconds" in report
        assert "downloads" in report
        assert "performance" in report
        assert "resources" in report
        assert "rate_limiting" in report
        
        # Überprüfe spezifische Werte
        assert report["downloads"]["completed"] == 1
        assert report["downloads"]["failed"] == 0
        assert report["performance"]["total_gb_downloaded"] >= 0


class TestRateLimiter:
    """Tests für den Rate-Limiter."""

    def test_rate_limiter_basic_operation(self):
        """Test grundlegende Operationen des Rate-Limiters."""
        limiter = RateLimiter(max_rate=10.0)  # 10 requests pro Sekunde
        
        # Teste, dass wir initially Tokens haben
        assert limiter.get_available_tokens() > 0
        
        # Teste das Verbrauchen von Tokens
        initial_tokens = limiter.get_available_tokens()
        limiter.consume_tokens(1)
        assert limiter.get_available_tokens() == initial_tokens - 1

    def test_rate_limiter_refill(self):
        """Test Auffüllen des Rate-Limiters."""
        limiter = RateLimiter(max_rate=10.0, refill_interval=0.1)  # Schnelleres Auffüllen für Tests
        
        # Verbrauche alle Tokens
        initial_tokens = limiter.get_available_tokens()
        limiter.consume_tokens(initial_tokens)
        assert limiter.get_available_tokens() == 0
        
        # Warte auf Auffüllung
        time.sleep(0.15)  # Warte etwas länger als das Auffüllintervall
        
        # Überprüfe, dass Tokens aufgefüllt wurden
        assert limiter.get_available_tokens() > 0

    def test_rate_limiter_wait_time(self):
        """Test Wartezeit-Berechnung des Rate-Limiters."""
        limiter = RateLimiter(max_rate=5.0)  # 5 requests pro Sekunde
        
        # Verbrauche alle Tokens
        tokens = limiter.get_available_tokens()
        limiter.consume_tokens(tokens)
        
        # Berechne die benötigte Wartezeit für 1 Token
        wait_time = limiter.get_wait_time(1)
        assert wait_time > 0
        
        # Die Wartezeit für 0 Tokens sollte 0 sein
        assert limiter.get_wait_time(0) == 0


class TestDownloadStatistics:
    """Tests für die Download-Statistiken."""

    def test_download_statistics_basic_operations(self):
        """Test grundlegende Operationen der Download-Statistiken."""
        stats = DownloadStatistics()
        
        # Teste das Hinzufügen von abgeschlossenen Downloads
        stats.add_completed_download(1024000, 0.5)  # 1MB in 0.5 Sekunden
        stats.add_completed_download(2048000, 1.0)  # 2MB in 1.0 Sekunden
        
        # Überprüfe die Statistiken
        summary = stats.get_summary()
        assert summary["completed"] == 2
        assert summary["total_bytes"] == 3072000  # 1MB + 2MB
        
        # Teste das Hinzufügen von fehlgeschlagenen Downloads
        stats.add_failed_download()
        stats.add_failed_download()
        
        summary = stats.get_summary()
        assert summary["failed"] == 2

    def test_download_statistics_performance_metrics(self):
        """Test Performance-Metriken der Download-Statistiken."""
        stats = DownloadStatistics()
        
        # Füge einige Downloads hinzu
        stats.add_completed_download(1048576, 1.0)  # 1MB in 1 Sekunde = 1 MB/s
        stats.add_completed_download(2097152, 1.0)  # 2MB in 1 Sekunde = 2 MB/s
        stats.add_completed_download(1572864, 1.0)  # 1.5MB in 1 Sekunde = 1.5 MB/s
        
        summary = stats.get_summary()
        
        # Überprüfe die berechneten Metriken
        assert summary["total_megabytes"] == 4.5  # 1 + 2 + 1.5
        assert summary["average_speed_mbps"] == 1.5  # (1 + 2 + 1.5) / 3


class TestUtilityFunctions:
    """Tests für Hilfsfunktionen."""

    def test_format_bytes(self):
        """Test Byte-Formatierung."""
        from src.telegram_audio_downloader.performance import format_bytes
        
        # Test verschiedene Größen
        assert format_bytes(0) == "0 B"
        assert format_bytes(1023) == "1023 B"
        assert format_bytes(1024) == "1.0 KB"
        assert format_bytes(1048576) == "1.0 MB"
        assert format_bytes(1073741824) == "1.0 GB"
        assert format_bytes(1099511627776) == "1.0 TB"

    def test_format_duration(self):
        """Test Zeitdauer-Formatierung."""
        from src.telegram_audio_downloader.performance import format_duration
        
        # Test verschiedene Zeiten
        assert format_duration(0) == "0s"
        assert format_duration(30) == "30s"
        assert format_duration(90) == "1m 30s"
        assert format_duration(3661) == "1h 1m 1s"
        assert format_duration(90061) == "1d 1h 1m 1s"


class TestGlobalPerformanceFunctions:
    """Tests für globale Performance-Funktionen."""

    def test_get_performance_monitor(self):
        """Test Abruf des globalen Performance-Monitors."""
        monitor1 = get_performance_monitor()
        monitor2 = get_performance_monitor()
        
        # Es sollte immer dieselbe Instanz zurückgegeben werden
        assert monitor1 is monitor2
        assert isinstance(monitor1, PerformanceMonitor)


class TestIntegrationPerformance:
    """Integrationstests für Performance-Komponenten."""

    def test_lru_cache_performance(self):
        """Test Performance des LRU-Caches."""
        cache = LRUCache(max_size=1000)
        
        # Fülle den Cache
        start_time = time.time()
        for i in range(1000):
            cache.put(f"key_{i}", f"value_{i}")
        
        fill_time = time.time() - start_time
        
        # Greife auf Einträge zu
        start_time = time.time()
        for i in range(1000):
            value = cache.get(f"key_{i}")
            assert value == f"value_{i}"
        
        access_time = time.time() - start_time
        
        # Die Zeiten sollten vernünftig sein (dies ist ein einfacher Check)
        assert fill_time < 1.0  # Sollte weniger als 1 Sekunde dauern
        assert access_time < 1.0  # Sollte weniger als 1 Sekunde dauern

    def test_memory_efficient_set_performance(self):
        """Test Performance des speichereffizienten Sets."""
        efficient_set = MemoryEfficientSet(max_size=10000)
        
        # Füge viele Elemente hinzu
        start_time = time.time()
        for i in range(5000):
            efficient_set.add(f"item_{i}")
        
        add_time = time.time() - start_time
        
        # Prüfe auf Elemente
        start_time = time.time()
        for i in range(5000):
            assert f"item_{i}" in efficient_set
        
        check_time = time.time() - start_time
        
        # Die Zeiten sollten vernünftig sein
        assert add_time < 1.0
        assert check_time < 1.0

    def test_streaming_data_processor_performance(self):
        """Test Performance des Streaming-Data-Processors."""
        processor = StreamingDataProcessor(chunk_size=1000)
        
        # Erstelle Testdaten
        test_data = list(range(10000))
        
        # Verarbeite die Daten
        start_time = time.time()
        chunks = list(processor.process_in_chunks(iter(test_data)))
        process_time = time.time() - start_time
        
        # Überprüfe die Ergebnisse
        assert len(chunks) == 10  # 10000 Elemente / 1000 pro Chunk
        assert len(chunks[0]) == 1000
        
        # Die Verarbeitung sollte schnell sein
        assert process_time < 1.0


if __name__ == '__main__':
    pytest.main([__file__])