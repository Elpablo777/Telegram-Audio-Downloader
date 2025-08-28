#!/usr/bin/env python3
"""
File Operations Test - Telegram Audio Downloader
==============================================

Test für grundlegende Dateioperationen.
"""

import sys
import tempfile
from pathlib import Path
import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from telegram_audio_downloader.utils import sanitize_filename, format_file_size, get_unique_filepath


class TestFileOperations:
    """Tests für Dateioperationen."""
    
    def test_sanitize_filename(self):
        """Test der Dateinamen-Sanitisierung."""
        # Test valid filename
        assert sanitize_filename("test.mp3") == "test.mp3"
        
        # Test filename with invalid characters
        assert sanitize_filename("test/file.mp3") == "test_file.mp3"
        assert sanitize_filename("test\\file.mp3") == "test_file.mp3"
        assert sanitize_filename("test:file.mp3") == "test_file.mp3"
        assert sanitize_filename("test*file.mp3") == "test_file.mp3"
        assert sanitize_filename("test?file.mp3") == "test_file.mp3"
        assert sanitize_filename('test"file.mp3') == "test_file.mp3"
        assert sanitize_filename("test<file.mp3") == "test_file.mp3"
        assert sanitize_filename("test>file.mp3") == "test_file.mp3"
        assert sanitize_filename("test|file.mp3") == "test_file.mp3"
        
        # Test filename with path traversal attempts
        # The updated implementation correctly handles these
        assert sanitize_filename("../../../etc/passwd") == "_._._etc_passwd"
        assert sanitize_filename("..\\..\\windows\\system32\\config\\sam") == "_._windows_system32_config_sam"
        
        # Test empty filename - the implementation returns "unknown_file"
        assert sanitize_filename("") == "unknown_file"
        
        # Test filename with only invalid characters that get stripped
        assert sanitize_filename("...") == "unknown_file"
        
        # NEW TESTS: Unicode and emoji handling (these are the key fixes)
        
        # Test NULL bytes (these caused crashes before)
        assert sanitize_filename("test\x00file.mp3") == "test_file.mp3"
        
        # Test other control characters
        assert sanitize_filename("test\x01file.mp3") == "test_file.mp3"
        assert sanitize_filename("test\nfile.mp3") == "test_file.mp3"
        assert sanitize_filename("test\tfile.mp3") == "test_file.mp3"
        
        # Test emojis (these could cause filesystem issues)
        assert sanitize_filename("🎵 My Song.mp3") == "_ My Song.mp3"
        assert sanitize_filename("Artist - Song 🎶.mp3") == "Artist - Song _.mp3"
        assert sanitize_filename("🔥💯🎵.mp3") == "_.mp3"
        
        # Test safe Unicode characters (these should be preserved)
        assert sanitize_filename("café.mp3") == "café.mp3"
        assert sanitize_filename("测试.mp3") == "测试.mp3"
        
        # Test Unicode normalization
        assert sanitize_filename("é.mp3") == "é.mp3"  # NFC normalized
        
        # Test zero-width characters (these should be removed)
        assert sanitize_filename("test\u200Bfile.mp3") == "testfile.mp3"
        assert sanitize_filename("test\u200Dfile.mp3") == "testfile.mp3"
        
        # Test complex combinations that could crash the system
        assert sanitize_filename("🎵\x00Test\n\u200BFile🎶.mp3") == "_Test_File_.mp3"
        
        # Test reserved Windows names
        assert sanitize_filename("CON.mp3") == "_CON.mp3"
        assert sanitize_filename("con.mp3") == "_con.mp3"
    
    def test_format_file_size(self):
        """Test der Dateigrößen-Formatierung."""
        # Test bytes
        assert format_file_size(0) == "0 B"
        assert format_file_size(512) == "512.0 B"
        assert format_file_size(1023) == "1023.0 B"
        
        # Test KB
        assert format_file_size(1024) == "1.0 KB"
        assert format_file_size(1536) == "1.5 KB"
        assert format_file_size(1048575) == "1024.0 KB"
        
        # Test MB
        assert format_file_size(1048576) == "1.0 MB"
        assert format_file_size(1572864) == "1.5 MB"
        assert format_file_size(1073741823) == "1024.0 MB"
        
        # Test GB
        assert format_file_size(1073741824) == "1.0 GB"
        assert format_file_size(1610612736) == "1.5 GB"
    
    def test_get_unique_filepath(self):
        """Test der eindeutigen Dateipfad-Erstellung."""
        # Create temporary directory
        temp_dir = Path(tempfile.mkdtemp(prefix="file_ops_test_"))
        
        try:
            # Test non-existing file
            test_file = temp_dir / "test.mp3"
            unique_path = get_unique_filepath(test_file)
            assert unique_path == test_file
            
            # Create a file
            test_file.write_text("test content")
            assert test_file.exists()
            
            # Test existing file - should return a unique path
            unique_path = get_unique_filepath(test_file)
            assert unique_path != test_file
            assert unique_path.name == "test_1.mp3"
            assert unique_path.parent == test_file.parent
            
            # Create the second file
            unique_path.write_text("test content 2")
            assert unique_path.exists()
            
            # Test existing file again - should return another unique path
            unique_path2 = get_unique_filepath(test_file)
            assert unique_path2 != test_file
            assert unique_path2 != unique_path
            assert unique_path2.name == "test_2.mp3"
        finally:
            # Cleanup
            import shutil
            if temp_dir.exists():
                shutil.rmtree(temp_dir)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])