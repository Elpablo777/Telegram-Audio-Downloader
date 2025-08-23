#!/usr/bin/env python3
"""
Pytest Configuration for Tests
==============================

Minimal pytest configuration.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
import asyncio

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def temp_workspace(tmp_path):
    """Create temporary workspace for tests."""
    workspace = tmp_path / "test_workspace"
    workspace.mkdir()
    
    # Create subdirectories
    (workspace / "downloads").mkdir()
    (workspace / "data").mkdir()
    (workspace / "logs").mkdir()
    
    return workspace

@pytest.fixture
def mock_telegram_client():
    """Mock Telegram client for testing."""
    from unittest.mock import AsyncMock, Mock
    
    mock_client = AsyncMock()
    
    # Mock entity
    mock_entity = Mock()
    mock_entity.id = -1001234567890
    mock_entity.title = "Test Group"
    mock_entity.username = "test_group"
    mock_client.get_entity.return_value = mock_entity
    
    # Mock message
    mock_message = Mock()
    mock_message.id = 1
    mock_message.audio = Mock(
        file_id="test_file_id",
        duration=180,
        title="Test Song",
        performer="Test Artist",
        file_size=5242880
    )
    
    mock_client.iter_messages.return_value = [mock_message]
    mock_client.download_media.return_value = "test_audio.mp3"
    
    return mock_client

@pytest.fixture
def sample_audio_file(tmp_path):
    """Create sample audio file for testing."""
    audio_file = tmp_path / "sample.mp3"
    
    # Create minimal MP3 file
    mp3_header = b"ID3\x03\x00\x00\x00\x00\x00\x00\x00"
    audio_content = mp3_header + b"\x00" * 1000
    audio_file.write_bytes(audio_content)
    
    return audio_file

@pytest.fixture
async def test_database(tmp_path):
    """Create test database."""
    from telegram_audio_downloader.database import Database
    
    db_path = tmp_path / "test.db"
    db = Database(database_url=f"sqlite:///{db_path}")
    await db.init()
    
    yield db
    
    await db.close()

@pytest.fixture
def performance_benchmark():
    """Performance benchmark fixture."""
    import time
    import psutil
    
    class PerformanceBenchmark:
        def __init__(self):
            self.start_time = None
            self.start_memory = None
            self.process = psutil.Process()
        
        def start(self):
            self.start_time = time.time()
            self.start_memory = self.process.memory_info().rss
        
        def stop(self):
            if self.start_time is None:
                raise ValueError("Benchmark not started")
            
            end_time = time.time()
            end_memory = self.process.memory_info().rss
            
            return {
                "duration": end_time - self.start_time,
                "memory_delta": end_memory - self.start_memory,
                "peak_memory": end_memory
            }
    
    return PerformanceBenchmark()

# Test collection configuration
def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names."""
    for item in items:
        # Add markers based on test file/name patterns
        if "e2e" in item.nodeid:
            item.add_marker(pytest.mark.e2e)
        
        if "performance" in item.nodeid or "benchmark" in item.nodeid:
            item.add_marker(pytest.mark.performance)
            item.add_marker(pytest.mark.slow)
        
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        
        if "security" in item.nodeid:
            item.add_marker(pytest.mark.security)
        
        if "network" in item.nodeid or "download" in item.nodeid:
            item.add_marker(pytest.mark.network)

# Skip markers for CI/local development
def pytest_runtest_setup(item):
    """Skip tests based on markers and environment."""
    import os
    
    # Skip network tests if SKIP_NETWORK_TESTS is set
    if "network" in [mark.name for mark in item.iter_markers()]:
        if os.environ.get("SKIP_NETWORK_TESTS"):
            pytest.skip("Network tests disabled")
    
    # Skip slow tests if SKIP_SLOW_TESTS is set
    if "slow" in [mark.name for mark in item.iter_markers()]:
        if os.environ.get("SKIP_SLOW_TESTS"):
            pytest.skip("Slow tests disabled")

# Reporting configuration
@pytest.hookimpl(tryfirst=True)
def pytest_configure_node(node):
    """Configure test node for parallel execution."""
    node.slaveinput["custom_data"] = "e2e_tests"

def pytest_html_report_title(report):
    """Customize HTML report title."""
    report.title = "Telegram Audio Downloader - E2E Test Report"

# Custom test result reporting
class E2ETestReporter:
    """Custom test reporter for E2E results."""
    
    def __init__(self):
        self.results = []
    
    def pytest_runtest_logreport(self, report):
        """Log test report."""
        if report.when == "call":
            self.results.append({
                "test": report.nodeid,
                "outcome": report.outcome,
                "duration": getattr(report, "duration", 0),
                "details": getattr(report, "details", {})
            })
    
    def pytest_sessionfinish(self, session):
        """Generate final report."""
        passed = len([r for r in self.results if r["outcome"] == "passed"])
        failed = len([r for r in self.results if r["outcome"] == "failed"])
        skipped = len([r for r in self.results if r["outcome"] == "skipped"])
        
        print(f"\n🧪 E2E Test Summary:")
        print(f"   ✅ Passed: {passed}")
        print(f"   ❌ Failed: {failed}")
        print(f"   ⏭️ Skipped: {skipped}")
        print(f"   📊 Total: {len(self.results)}")

@pytest.fixture(autouse=True)
def e2e_reporter():
    """Auto-use E2E reporter."""
    return E2ETestReporter()

# Performance test utilities
@pytest.fixture
def memory_monitor():
    """Memory monitoring fixture."""
    import psutil
    
    class MemoryMonitor:
        def __init__(self):
            self.process = psutil.Process()
            self.initial_memory = self.process.memory_info().rss
        
        def get_memory_usage(self):
            current = self.process.memory_info().rss
            return {
                "current_mb": current / (1024 * 1024),
                "delta_mb": (current - self.initial_memory) / (1024 * 1024),
                "percent": self.process.memory_percent()
            }
    
    return MemoryMonitor()

# Test data fixtures
@pytest.fixture
def sample_telegram_data():
    """Sample Telegram data for testing."""
    return {
        "groups": [
            {
                "id": -1001234567890,
                "title": "Test Music Group",
                "username": "test_music_group"
            }
        ],
        "messages": [
            {
                "id": 1,
                "text": "Test Audio 1",
                "audio": {
                    "file_id": "audio_file_1",
                    "duration": 180,
                    "title": "Song 1",
                    "performer": "Artist 1",
                    "file_size": 5242880
                }
            },
            {
                "id": 2,
                "text": "Test Audio 2",
                "audio": {
                    "file_id": "audio_file_2",
                    "duration": 240,
                    "title": "Song 2",
                    "performer": "Artist 2",
                    "file_size": 7340032
                }
            }
        ]
    }

# Environment setup/teardown
@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment."""
    import os
    import tempfile
    
    # Set test environment variables
    os.environ["TESTING"] = "true"
    os.environ["LOG_LEVEL"] = "DEBUG"
    
    # Create test data directory
    test_data_dir = Path("data/tests")
    test_data_dir.mkdir(parents=True, exist_ok=True)
    
    yield
    
    # Cleanup (if needed)
    print("\n🧹 Test environment cleanup completed")

# Async helper utilities
@pytest.fixture
def async_timeout():
    """Async timeout helper."""
    import asyncio
    
    async def timeout_after(seconds, coro):
        try:
            return await asyncio.wait_for(coro, timeout=seconds)
        except asyncio.TimeoutError:
            pytest.fail(f"Test timed out after {seconds} seconds")
    
    return timeout_after

# Mock data generators
@pytest.fixture
def generate_mock_audio_files():
    """Generate mock audio files."""
    def _generate(count=5, base_path=None):
        if base_path is None:
            base_path = Path("/tmp")
        
        files = []
        for i in range(count):
            file_path = base_path / f"mock_audio_{i}.mp3"
            content = b"ID3\x03\x00\x00\x00" + b"\x00" * (1024 * 1024)  # 1MB
            file_path.write_bytes(content)
            files.append(file_path)
        
        return files
    
    return _generate

# Test configuration based on pytest.ini
def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--run-slow", action="store_true", default=False,
        help="Run slow tests"
    )
    parser.addoption(
        "--run-network", action="store_true", default=False,
        help="Run network-dependent tests"
    )
    parser.addoption(
        "--run-e2e", action="store_true", default=False,
        help="Run end-to-end tests"
    )
    parser.addoption(
        "--performance-only", action="store_true", default=False,
        help="Run only performance tests"
    )

def pytest_configure_markers(config):
    """Configure test markers based on command line options."""
    if config.getoption("--performance-only"):
        # Only run performance tests
        config.option.markexpr = "performance"
    elif not config.getoption("--run-slow"):
        # Skip slow tests by default
        config.option.markexpr = "not slow"
