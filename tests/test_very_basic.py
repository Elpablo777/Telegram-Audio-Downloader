#!/usr/bin/env python3
"""
Very Basic Test - Telegram Audio Downloader
==========================================

Sehr einfacher Test für grundlegende Funktionen.
"""

import os
import sys
import tempfile
from pathlib import Path
import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from telegram_audio_downloader.downloader import AudioDownloader
from telegram_audio_downloader.models import DownloadStatus


class TestVeryBasic:
    """Sehr grundlegende Tests."""
    
    def test_downloader_creation(self):
        """Test der Downloader-Erstellung."""
        # Create temporary directory
        temp_dir = tempfile.mkdtemp(prefix="very_basic_test_")
        download_dir = Path(temp_dir) / "downloads"
        download_dir.mkdir()
        
        try:
            # Initialize downloader
            downloader = AudioDownloader(download_dir=str(download_dir))
            
            # Verify downloader was initialized correctly
            assert downloader.download_dir == download_dir
            assert downloader.download_dir.exists()
            assert downloader.max_concurrent_downloads == 3  # Default value
            
            # Verify LRU cache is initialized (it may already contain entries from the database)
            assert downloader._downloaded_files_cache is not None
            # The cache may already contain entries from previous tests, so we just check it's initialized
        finally:
            # Cleanup
            import shutil
            if Path(temp_dir).exists():
                shutil.rmtree(temp_dir)
    
    def test_download_status_enum(self):
        """Test des DownloadStatus-Enums."""
        # Verify all expected status values exist
        expected_statuses = ["pending", "downloading", "completed", "failed", "skipped"]
        actual_statuses = [status.value for status in DownloadStatus]
        
        for status in expected_statuses:
            assert status in actual_statuses
    
    def test_audio_file_properties(self):
        """Test der AudioFile-Eigenschaften."""
        # This test doesn't create actual database records, just tests the model structure
        assert hasattr(DownloadStatus, "PENDING")
        assert hasattr(DownloadStatus, "DOWNLOADING")
        assert hasattr(DownloadStatus, "COMPLETED")
        assert hasattr(DownloadStatus, "FAILED")
        assert hasattr(DownloadStatus, "SKIPPED")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])