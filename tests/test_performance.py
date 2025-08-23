#!/usr/bin/env python3
"""
Performance Tests - Telegram Audio Downloader
=============================================

Comprehensive performance testing for enterprise-level monitoring.
"""

import pytest
import asyncio
import time
import sys
import psutil
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from telegram_audio_downloader.core.downloader import AudioDownloader
from telegram_audio_downloader.utils.rate_limiter import RateLimiter
from telegram_audio_downloader.utils.memory_manager import MemoryManager
from telegram_audio_downloader.monitoring.performance_monitor import PerformanceMonitor


class TestPerformanceMonitor:
    """Test performance monitoring system."""
    
    @pytest.fixture
    def performance_monitor(self):
        return PerformanceMonitor()
    
    @pytest.mark.performance
    async def test_monitor_initialization(self, performance_monitor):
        """Test performance monitor initialization."""
        assert performance_monitor is not None
        assert hasattr(performance_monitor, 'start_monitoring')
        assert hasattr(performance_monitor, 'get_metrics')
    
    @pytest.mark.performance
    async def test_memory_tracking(self, performance_monitor):
        """Test memory usage tracking."""
        initial_memory = performance_monitor.get_memory_usage()
        assert isinstance(initial_memory, dict)
        assert 'rss_mb' in initial_memory
        assert 'vms_mb' in initial_memory
        assert 'percent' in initial_memory
        
        # Allocate some memory
        large_data = [0] * 1000000  # 1M integers
        
        new_memory = performance_monitor.get_memory_usage()
        assert new_memory['rss_mb'] >= initial_memory['rss_mb']
        
        del large_data
    
    @pytest.mark.performance
    async def test_cpu_monitoring(self, performance_monitor):
        """Test CPU usage monitoring."""
        cpu_usage = performance_monitor.get_cpu_usage()
        assert isinstance(cpu_usage, float)
        assert 0 <= cpu_usage <= 100
    
    @pytest.mark.performance
    async def test_execution_time_tracking(self, performance_monitor):
        """Test execution time tracking."""
        with performance_monitor.track_execution("test_operation"):
            await asyncio.sleep(0.1)
        
        metrics = performance_monitor.get_metrics()
        assert "test_operation" in metrics
        assert metrics["test_operation"]["duration"] >= 0.1


class TestRateLimiter:
    """Test rate limiting functionality."""
    
    @pytest.fixture
    def rate_limiter(self):
        return RateLimiter(max_requests=10, time_window=1.0)
    
    @pytest.mark.performance
    async def test_rate_limiter_initialization(self, rate_limiter):
        """Test rate limiter initialization."""
        assert rate_limiter.max_requests == 10
        assert rate_limiter.time_window == 1.0
        assert rate_limiter.request_count == 0
    
    @pytest.mark.performance
    async def test_request_allowance(self, rate_limiter):
        """Test request allowance within limits."""
        for i in range(10):
            assert await rate_limiter.acquire()
        
        # 11th request should be rate limited
        assert not await rate_limiter.acquire()
    
    @pytest.mark.performance
    async def test_rate_limit_reset(self, rate_limiter):
        """Test rate limit reset after time window."""
        # Fill up the rate limiter
        for i in range(10):
            await rate_limiter.acquire()
        
        # Should be rate limited
        assert not await rate_limiter.acquire()
        
        # Wait for reset
        await asyncio.sleep(1.1)
        
        # Should allow requests again
        assert await rate_limiter.acquire()
    
    @pytest.mark.performance
    @pytest.mark.slow
    async def test_concurrent_rate_limiting(self, rate_limiter):
        """Test rate limiting with concurrent requests."""
        async def make_request():
            return await rate_limiter.acquire()
        
        # Make 20 concurrent requests
        tasks = [make_request() for _ in range(20)]
        results = await asyncio.gather(*tasks)
        
        # Only 10 should be allowed
        allowed = sum(results)
        assert allowed <= 10


class TestMemoryManager:
    """Test memory management functionality."""
    
    @pytest.fixture
    def memory_manager(self):
        return MemoryManager(max_memory_mb=100)
    
    @pytest.mark.performance
    async def test_memory_manager_initialization(self, memory_manager):
        """Test memory manager initialization."""
        assert memory_manager.max_memory_mb == 100
        assert hasattr(memory_manager, 'check_memory_usage')
        assert hasattr(memory_manager, 'cleanup_if_needed')
    
    @pytest.mark.performance
    async def test_memory_monitoring(self, memory_manager):
        """Test memory usage monitoring."""
        usage = memory_manager.get_current_usage()
        assert isinstance(usage, dict)
        assert 'current_mb' in usage
        assert 'max_mb' in usage
        assert 'percentage' in usage
    
    @pytest.mark.performance
    async def test_memory_cleanup_trigger(self, memory_manager):
        """Test memory cleanup trigger."""
        # Mock high memory usage
        with patch.object(memory_manager, 'get_current_usage') as mock_usage:
            mock_usage.return_value = {
                'current_mb': 95,
                'max_mb': 100,
                'percentage': 95.0
            }
            
            cleanup_needed = memory_manager.check_memory_usage()
            assert cleanup_needed
    
    @pytest.mark.performance
    async def test_memory_within_limits(self, memory_manager):
        """Test memory within acceptable limits."""
        # Mock normal memory usage
        with patch.object(memory_manager, 'get_current_usage') as mock_usage:
            mock_usage.return_value = {
                'current_mb': 50,
                'max_mb': 100,
                'percentage': 50.0
            }
            
            cleanup_needed = memory_manager.check_memory_usage()
            assert not cleanup_needed


class TestDownloaderPerformance:
    """Test AudioDownloader performance."""
    
    @pytest.fixture
    async def downloader(self, tmp_path):
        """Create downloader instance for testing."""
        download_dir = tmp_path / "downloads"
        download_dir.mkdir()
        
        downloader = AudioDownloader(
            download_dir=str(download_dir),
            max_concurrent_downloads=3,
            rate_limit_delay=0.1
        )
        
        # Mock the telegram client
        mock_client = AsyncMock()
        downloader._client = mock_client
        
        return downloader
    
    @pytest.mark.performance
    async def test_download_initialization_time(self, downloader):
        """Test downloader initialization performance."""
        start_time = time.time()
        
        # Initialize components
        await downloader._initialize_components()
        
        init_time = time.time() - start_time
        assert init_time < 1.0  # Should initialize in under 1 second
    
    @pytest.mark.performance
    @pytest.mark.slow
    async def test_concurrent_download_performance(self, downloader):
        """Test concurrent download performance."""
        # Mock multiple audio files
        mock_files = [
            Mock(id=i, audio=Mock(file_id=f"file_{i}", title=f"Song {i}"))
            for i in range(10)
        ]
        
        downloader._client.iter_messages.return_value = mock_files
        downloader._client.download_media.return_value = "test_file.mp3"
        
        start_time = time.time()
        
        # Start downloads
        with patch.object(downloader, '_download_single_file') as mock_download:
            mock_download.return_value = {"status": "success", "file_path": "test.mp3"}
            
            results = await downloader.download_audio_files(
                group_identifier="test_group",
                limit=10
            )
        
        total_time = time.time() - start_time
        
        # With 3 concurrent downloads, should be faster than sequential
        assert total_time < 5.0
        assert len(results) == 10
    
    @pytest.mark.performance
    async def test_memory_usage_during_downloads(self, downloader, memory_monitor):
        """Test memory usage during download operations."""
        initial_memory = memory_monitor.get_memory_usage()
        
        # Mock download with large file
        mock_file = Mock(id=1, audio=Mock(file_id="large_file", title="Large Song"))
        downloader._client.iter_messages.return_value = [mock_file]
        
        # Simulate download
        with patch.object(downloader, '_download_single_file') as mock_download:
            mock_download.return_value = {"status": "success", "file_path": "large.mp3"}
            
            await downloader.download_audio_files(
                group_identifier="test_group",
                limit=1
            )
        
        final_memory = memory_monitor.get_memory_usage()
        
        # Memory increase should be reasonable
        memory_increase = final_memory['current_mb'] - initial_memory['current_mb']
        assert memory_increase < 50  # Less than 50MB increase


class TestPerformanceBenchmarks:
    """Performance benchmarks for the entire system."""
    
    @pytest.mark.performance
    @pytest.mark.slow
    async def test_system_startup_time(self, tmp_path):
        """Benchmark system startup time."""
        start_time = time.time()
        
        # Initialize complete system
        downloader = AudioDownloader(
            download_dir=str(tmp_path / "downloads"),
            max_concurrent_downloads=5
        )
        
        # Mock client initialization
        with patch.object(downloader, '_create_client'):
            await downloader._initialize_components()
        
        startup_time = time.time() - start_time
        
        # System should start in under 2 seconds
        assert startup_time < 2.0
        print(f"System startup time: {startup_time:.3f}s")
    
    @pytest.mark.performance
    async def test_database_query_performance(self, test_database):
        """Benchmark database query performance."""
        # Insert test data
        for i in range(100):
            await test_database.execute(
                "INSERT INTO downloads (file_id, title, file_path) VALUES (?, ?, ?)",
                (f"file_{i}", f"Song {i}", f"/path/to/song_{i}.mp3")
            )
        
        start_time = time.time()
        
        # Query data
        results = await test_database.fetch_all(
            "SELECT * FROM downloads WHERE title LIKE ?",
            ("%Song%",)
        )
        
        query_time = time.time() - start_time
        
        # Query should complete in under 100ms
        assert query_time < 0.1
        assert len(results) == 100
        print(f"Database query time: {query_time:.3f}s")
    
    @pytest.mark.performance
    async def test_file_processing_performance(self, tmp_path, sample_audio_file):
        """Benchmark file processing performance."""
        # Create multiple test files
        test_files = []
        for i in range(10):
            test_file = tmp_path / f"test_{i}.mp3"
            test_file.write_bytes(sample_audio_file.read_bytes())
            test_files.append(test_file)
        
        start_time = time.time()
        
        # Process files
        from telegram_audio_downloader.utils.metadata import extract_metadata
        
        for file_path in test_files:
            metadata = extract_metadata(str(file_path))
            assert metadata is not None
        
        processing_time = time.time() - start_time
        
        # Should process 10 files in under 1 second
        assert processing_time < 1.0
        print(f"File processing time: {processing_time:.3f}s")


class TestResourceUsage:
    """Test resource usage patterns."""
    
    @pytest.mark.performance
    async def test_cpu_usage_under_load(self, tmp_path):
        """Test CPU usage under high load."""
        process = psutil.Process()
        initial_cpu = process.cpu_percent(interval=0.1)
        
        # Simulate high load
        downloader = AudioDownloader(
            download_dir=str(tmp_path / "downloads"),
            max_concurrent_downloads=10
        )
        
        # Mock heavy processing
        async def cpu_intensive_task():
            for _ in range(1000000):
                pass
        
        start_time = time.time()
        await asyncio.gather(*[cpu_intensive_task() for _ in range(5)])
        
        final_cpu = process.cpu_percent(interval=0.1)
        duration = time.time() - start_time
        
        print(f"CPU usage: {initial_cpu:.1f}% -> {final_cpu:.1f}%")
        print(f"Processing duration: {duration:.3f}s")
        
        # CPU usage should be reasonable
        assert final_cpu < 90.0
    
    @pytest.mark.performance
    async def test_disk_io_performance(self, tmp_path):
        """Test disk I/O performance."""
        test_data = b"0" * (1024 * 1024)  # 1MB of data
        
        start_time = time.time()
        
        # Write multiple files
        for i in range(10):
            test_file = tmp_path / f"io_test_{i}.dat"
            test_file.write_bytes(test_data)
        
        write_time = time.time() - start_time
        
        start_time = time.time()
        
        # Read files back
        total_read = 0
        for i in range(10):
            test_file = tmp_path / f"io_test_{i}.dat"
            data = test_file.read_bytes()
            total_read += len(data)
        
        read_time = time.time() - start_time
        
        print(f"Write time: {write_time:.3f}s")
        print(f"Read time: {read_time:.3f}s")
        print(f"Total data: {total_read / (1024*1024):.1f}MB")
        
        # I/O should be reasonably fast
        assert write_time < 2.0
        assert read_time < 1.0
        assert total_read == 10 * 1024 * 1024


@pytest.mark.performance
class TestPerformanceRegression:
    """Performance regression tests."""
    
    async def test_no_memory_leaks(self, tmp_path):
        """Test for memory leaks during repeated operations."""
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        # Repeat operations
        for iteration in range(10):
            downloader = AudioDownloader(
                download_dir=str(tmp_path / f"downloads_{iteration}"),
                max_concurrent_downloads=1
            )
            
            # Mock download
            with patch.object(downloader, '_create_client'):
                await downloader._initialize_components()
            
            # Force cleanup
            del downloader
            
            # Check memory after each iteration
            current_memory = process.memory_info().rss
            memory_increase = (current_memory - initial_memory) / (1024 * 1024)
            
            print(f"Iteration {iteration}: Memory increase: {memory_increase:.1f}MB")
            
            # Memory should not grow significantly
            assert memory_increase < 50  # Less than 50MB increase
    
    async def test_performance_stability(self, tmp_path):
        """Test performance stability over multiple runs."""
        execution_times = []
        
        for run in range(5):
            start_time = time.time()
            
            # Standard operation
            downloader = AudioDownloader(
                download_dir=str(tmp_path / f"run_{run}"),
                max_concurrent_downloads=3
            )
            
            with patch.object(downloader, '_create_client'):
                await downloader._initialize_components()
            
            execution_time = time.time() - start_time
            execution_times.append(execution_time)
            
            print(f"Run {run + 1}: {execution_time:.3f}s")
        
        # Performance should be stable (low variance)
        import statistics
        avg_time = statistics.mean(execution_times)
        stdev_time = statistics.stdev(execution_times)
        
        print(f"Average: {avg_time:.3f}s, StdDev: {stdev_time:.3f}s")
        
        # Standard deviation should be low (< 20% of average)
        assert stdev_time < avg_time * 0.2


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])