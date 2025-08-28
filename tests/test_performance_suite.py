#!/usr/bin/env python3
"""
Performance Test Suite - Telegram Audio Downloader
=================================================

Performance-Tests für Download-Geschwindigkeit, Speichernutzung und CPU-Auslastung.
"""

import os
import sys
import asyncio
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from telegram_audio_downloader.downloader import AudioDownloader
from telegram_audio_downloader.models import AudioFile, DownloadStatus


class PerformanceMetrics:
    """Klasse zur Erfassung von Performance-Metriken."""
    
    def __init__(self):
        self.metrics = {}
    
    def start_timing(self, operation_name):
        """Startet die Zeitmessung für eine Operation."""
        self.metrics[operation_name] = {
            "start_time": time.time(),
            "end_time": None,
            "duration": None
        }
    
    def stop_timing(self, operation_name):
        """Stoppt die Zeitmessung für eine Operation."""
        if operation_name in self.metrics:
            self.metrics[operation_name]["end_time"] = time.time()
            self.metrics[operation_name]["duration"] = (
                self.metrics[operation_name]["end_time"] - 
                self.metrics[operation_name]["start_time"]
            )
    
    def record_memory_usage(self, operation_name, memory_mb):
        """Erfasst den Speicherverbrauch."""
        if operation_name not in self.metrics:
            self.metrics[operation_name] = {}
        self.metrics[operation_name]["memory_mb"] = memory_mb
    
    def record_cpu_usage(self, operation_name, cpu_percent):
        """Erfasst die CPU-Auslastung."""
        if operation_name not in self.metrics:
            self.metrics[operation_name] = {}
        self.metrics[operation_name]["cpu_percent"] = cpu_percent
    
    def record_download_speed(self, operation_name, speed_mbps):
        """Erfasst die Download-Geschwindigkeit."""
        if operation_name not in self.metrics:
            self.metrics[operation_name] = {}
        self.metrics[operation_name]["download_speed_mbps"] = speed_mbps
    
    def get_metrics(self):
        """Gibt die erfassten Metriken zurück."""
        return self.metrics


class PerformanceTestSuite:
    """Performance-Test-Suite."""
    
    def __init__(self):
        self.metrics = PerformanceMetrics()
        self.temp_dir = None
        self.download_dir = None
    
    def setup_test_environment(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp(prefix="perf_test_")
        self.download_dir = Path(self.temp_dir) / "downloads"
        self.download_dir.mkdir()
        
        # Setup test database
        test_db_path = Path(self.temp_dir) / "test.db"
        os.environ["DB_PATH"] = str(test_db_path)
        
        return self.temp_dir
    
    def teardown_test_environment(self):
        """Cleanup test environment."""
        import shutil
        if self.temp_dir and Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def create_test_messages(self, count):
        """Erstellt Test-Nachrichten."""
        messages = []
        for i in range(count):
            mock_msg = Mock()
            mock_msg.id = i + 1
            mock_msg.date = "2024-01-20T10:00:00Z"
            mock_msg.text = f"Test Audio File {i+1}"
            
            mock_audio = Mock()
            mock_audio.file_id = f"test_file_id_{i}"
            mock_audio.duration = 180
            mock_audio.title = f"Test Song {i+1}"
            mock_audio.performer = "Test Artist"
            mock_audio.file_size = 5242880  # 5MB
            
            mock_msg.audio = mock_audio
            messages.append(mock_msg)
        return messages


class TestPerformanceSuite:
    """Tests für die Performance-Test-Suite."""
    
    @pytest.fixture(autouse=True)
    def setup_performance_test(self):
        """Setup Performance-Test."""
        self.perf_suite = PerformanceTestSuite()
        self.temp_dir = self.perf_suite.setup_test_environment()
        yield
        self.perf_suite.teardown_test_environment()
    
    @pytest.mark.asyncio
    async def test_download_speed(self):
        """Test Download-Geschwindigkeit."""
        # Initialize downloader
        downloader = AudioDownloader(
            download_dir=str(self.perf_suite.download_dir),
            max_concurrent_downloads=3
        )
        
        # Create test messages
        test_messages = self.perf_suite.create_test_messages(10)
        
        # Mock Telegram client
        mock_client = AsyncMock()
        mock_client.get_entity.return_value = Mock(
            id=-1001234567890,
            title="Test Music Group",
            username="test_music_group"
        )
        mock_client.iter_messages.return_value = test_messages
        
        # Mock file download with timing
        test_file_content = b"ID3\x03\x00\x00\x00" + b"\x00" * 5242870  # 5MB
        
        with patch('telegram_audio_downloader.downloader.TelegramClient') as mock_client_class:
            mock_client_class.return_value = mock_client
            
            # Initialize client
            await downloader.initialize_client()
            
            # Measure download speed
            start_time = time.time()
            result = await downloader.download_audio_files(
                group_name="@test_music_group",
                limit=10
            )
            end_time = time.time()
            
            # Calculate download speed (MB/s)
            total_size_mb = result["total_size"] / (1024 * 1024)
            duration = end_time - start_time
            download_speed = total_size_mb / duration if duration > 0 else 0
            
            # Record metrics
            self.perf_suite.metrics.record_download_speed("download_speed_test", download_speed)
            self.perf_suite.metrics.start_timing("download_speed_test")
            self.perf_suite.metrics.stop_timing("download_speed_test")
            
            print(f"Downloaded {total_size_mb:.2f} MB in {duration:.2f} seconds")
            print(f"Download speed: {download_speed:.2f} MB/s")
            
            # Assert reasonable performance
            assert download_speed > 0.1  # Minimum 0.1 MB/s
            assert result["completed"] == 10
    
    @pytest.mark.asyncio
    async def test_memory_usage(self):
        """Test Speichernutzung."""
        try:
            import psutil
            process = psutil.Process()
        except ImportError:
            pytest.skip("psutil not available")
            return
        
        # Measure initial memory
        initial_memory = process.memory_info().rss / (1024 * 1024)  # MB
        
        # Initialize downloader
        downloader = AudioDownloader(
            download_dir=str(self.perf_suite.download_dir),
            max_concurrent_downloads=5
        )
        
        # Measure memory after initialization
        init_memory = process.memory_info().rss / (1024 * 1024)  # MB
        memory_delta_init = init_memory - initial_memory
        
        # Record metrics
        self.perf_suite.metrics.record_memory_usage("initialization", init_memory)
        
        # Create test messages
        test_messages = self.perf_suite.create_test_messages(20)
        
        # Mock Telegram client
        mock_client = AsyncMock()
        mock_client.get_entity.return_value = Mock(
            id=-1001234567890,
            title="Test Music Group",
            username="test_music_group"
        )
        mock_client.iter_messages.return_value = test_messages
        
        # Mock file download
        test_file_content = b"ID3\x03\x00\x00\x00" + b"\x00" * 5242870  # 5MB
        
        with patch('telegram_audio_downloader.downloader.TelegramClient') as mock_client_class:
            mock_client_class.return_value = mock_client
            
            # Initialize client
            await downloader.initialize_client()
            
            # Measure memory before download
            before_download_memory = process.memory_info().rss / (1024 * 1024)  # MB
            
            # Perform downloads
            result = await downloader.download_audio_files(
                group_name="@test_music_group",
                limit=20
            )
            
            # Measure memory after download
            after_download_memory = process.memory_info().rss / (1024 * 1024)  # MB
            memory_delta_download = after_download_memory - before_download_memory
            
            # Record metrics
            self.perf_suite.metrics.record_memory_usage("before_download", before_download_memory)
            self.perf_suite.metrics.record_memory_usage("after_download", after_download_memory)
            
            print(f"Initial memory: {initial_memory:.2f} MB")
            print(f"Memory after initialization: {init_memory:.2f} MB (+{memory_delta_init:.2f} MB)")
            print(f"Memory before download: {before_download_memory:.2f} MB")
            print(f"Memory after download: {after_download_memory:.2f} MB (+{memory_delta_download:.2f} MB)")
            
            # Assert reasonable memory usage
            assert memory_delta_init < 50  # Initialization should use less than 50MB
            assert memory_delta_download < 100  # Download should use less than 100MB additional memory
    
    @pytest.mark.asyncio
    async def test_cpu_usage(self):
        """Test CPU-Auslastung."""
        try:
            import psutil
            process = psutil.Process()
        except ImportError:
            pytest.skip("psutil not available")
            return
        
        # Initialize downloader
        downloader = AudioDownloader(
            download_dir=str(self.perf_suite.download_dir),
            max_concurrent_downloads=3
        )
        
        # Create test messages
        test_messages = self.perf_suite.create_test_messages(15)
        
        # Mock Telegram client
        mock_client = AsyncMock()
        mock_client.get_entity.return_value = Mock(
            id=-1001234567890,
            title="Test Music Group",
            username="test_music_group"
        )
        mock_client.iter_messages.return_value = test_messages
        
        # Mock file download
        test_file_content = b"ID3\x03\x00\x00\x00" + b"\x00" * 5242870  # 5MB
        
        with patch('telegram_audio_downloader.downloader.TelegramClient') as mock_client_class:
            mock_client_class.return_value = mock_client
            
            # Initialize client
            await downloader.initialize_client()
            
            # Measure CPU before download
            cpu_before = process.cpu_percent()
            
            # Perform downloads
            result = await downloader.download_audio_files(
                group_name="@test_music_group",
                limit=15
            )
            
            # Measure CPU after download
            cpu_after = process.cpu_percent()
            cpu_delta = cpu_after - cpu_before
            
            # Record metrics
            self.perf_suite.metrics.record_cpu_usage("cpu_usage_test", cpu_after)
            
            print(f"CPU before download: {cpu_before:.2f}%")
            print(f"CPU after download: {cpu_after:.2f}%")
            print(f"CPU delta: {cpu_delta:.2f}%")
            
            # Assert reasonable CPU usage
            assert cpu_after < 90  # CPU usage should stay below 90%
    
    @pytest.mark.asyncio
    async def test_concurrent_downloads(self):
        """Test gleichzeitige Downloads."""
        # Initialize downloader with high concurrency
        downloader = AudioDownloader(
            download_dir=str(self.perf_suite.download_dir),
            max_concurrent_downloads=10
        )
        
        # Create test messages
        test_messages = self.perf_suite.create_test_messages(30)
        
        # Mock Telegram client
        mock_client = AsyncMock()
        mock_client.get_entity.return_value = Mock(
            id=-1001234567890,
            title="Test Music Group",
            username="test_music_group"
        )
        mock_client.iter_messages.return_value = test_messages
        
        # Mock file download
        test_file_content = b"ID3\x03\x00\x00\x00" + b"\x00" * 5242870  # 5MB
        
        with patch('telegram_audio_downloader.downloader.TelegramClient') as mock_client_class:
            mock_client_class.return_value = mock_client
            
            # Initialize client
            await downloader.initialize_client()
            
            # Measure time for concurrent downloads
            start_time = time.time()
            result = await downloader.download_audio_files(
                group_name="@test_music_group",
                limit=30
            )
            end_time = time.time()
            
            duration = end_time - start_time
            
            # Record metrics
            self.perf_suite.metrics.start_timing("concurrent_downloads")
            self.perf_suite.metrics.stop_timing("concurrent_downloads")
            self.perf_suite.metrics.record_download_speed(
                "concurrent_downloads", 
                (result["total_size"] / (1024 * 1024)) / duration if duration > 0 else 0
            )
            
            print(f"Downloaded {result['completed']} files in {duration:.2f} seconds with 10 concurrent downloads")
            
            # Assert all files were downloaded
            assert result["completed"] == 30
            # Assert reasonable time (should be faster than sequential)
            assert duration < 60  # Should complete within 60 seconds


if __name__ == "__main__":
    pytest.main([__file__, "-v"])