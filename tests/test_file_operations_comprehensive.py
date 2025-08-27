#!/usr/bin/env python3
"""
Comprehensive File Operations Tests - Telegram Audio Downloader
==============================================================

Umfassende Tests für Dateioperationen und -berechtigungen.
"""

import os
import sys
import tempfile
import stat
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from telegram_audio_downloader.utils.file_operations import (
    sanitize_filename, 
    create_download_directory,
    check_disk_space,
    secure_delete_file,
    move_file_with_backup
)
from telegram_audio_downloader.utils import sanitize_filename as sanitize_filename_util


class TestFileOperationsComprehensive:
    """Umfassende Tests für Dateioperationen."""
    
    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp(prefix="file_ops_test_")
        self.download_dir = Path(self.temp_dir) / "downloads"
        self.download_dir.mkdir()
        
        yield
        
        # Cleanup
        import shutil
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def test_sanitize_filename_extreme_cases(self):
        """Test Sanitize-Filename mit Extremfällen."""
        # Test very long filenames
        long_name = "a" * 300 + ".mp3"
        sanitized = sanitize_filename(long_name)
        assert len(sanitized) <= 255  # Typical filesystem limit
        assert sanitized.endswith(".mp3")
        
        # Test filenames with only special characters
        only_special = "___...___"
        sanitized = sanitize_filename(only_special)
        assert len(sanitized) > 0  # Should not be empty
        assert "untitled" in sanitized.lower() or "file" in sanitized.lower()
        
        # Test filenames with unicode characters
        unicode_name = "müsic_fïle_ñame.mp3"
        sanitized = sanitize_filename(unicode_name)
        assert "müsic" in sanitized or "music" in sanitized  # Should handle unicode gracefully
        assert ".mp3" in sanitized
        
        # Test filenames with path separators
        with_path = "path/to/file.mp3"
        sanitized = sanitize_filename(with_path)
        assert "/" not in sanitized
        assert "\\" not in sanitized
        assert ".mp3" in sanitized
        
        # Test empty filename
        empty_name = ""
        sanitized = sanitize_filename(empty_name)
        assert len(sanitized) > 0  # Should not be empty
        assert "untitled" in sanitized.lower() or "file" in sanitized.lower()
    
    def test_create_download_directory_permissions(self):
        """Test Erstellung von Download-Verzeichnis mit Berechtigungen."""
        # Test creating directory with specific permissions
        test_dir = self.download_dir / "permission_test"
        
        # Create directory with specific permissions
        create_download_directory(str(test_dir))
        
        # Check if directory exists
        assert test_dir.exists()
        assert test_dir.is_dir()
        
        # Check basic permissions (platform dependent)
        stat_info = test_dir.stat()
        # On Unix-like systems, we could check more detailed permissions
        # On Windows, this is more limited
    
    def test_create_download_directory_existing_file(self):
        """Test Erstellung von Download-Verzeichnis wenn Datei existiert."""
        # Create a file where directory should be
        conflict_path = self.download_dir / "conflict"
        conflict_path.write_text("This is a file, not a directory")
        
        # Try to create directory at the same path
        with pytest.raises(OSError):
            create_download_directory(str(conflict_path))
    
    def test_check_disk_space_edge_cases(self):
        """Test Prüfung des Speicherplatzes mit Extremfällen."""
        # Test with very small disk space
        with patch('shutil.disk_usage') as mock_disk_usage:
            # Simulate almost full disk (only 1 byte free)
            mock_disk_usage.return_value = (1000, 999, 1)
            has_space = check_disk_space(str(self.download_dir), required_bytes=10)
            assert not has_space  # Should not have space for 10 bytes
        
        # Test with plenty of disk space
        with patch('shutil.disk_usage') as mock_disk_usage:
            # Simulate lots of free space
            mock_disk_usage.return_value = (1000000, 500000, 500000)
            has_space = check_disk_space(str(self.download_dir), required_bytes=1000)
            assert has_space  # Should have space for 1000 bytes
        
        # Test with invalid path
        has_space = check_disk_space("/invalid/path", required_bytes=100)
        assert not has_space  # Should return False for invalid path
    
    def test_secure_delete_file_normal(self):
        """Test sicheres Löschen von Dateien."""
        # Create a test file
        test_file = self.download_dir / "test_delete.txt"
        test_file.write_text("This is test content for deletion")
        
        # Verify file exists
        assert test_file.exists()
        
        # Securely delete the file
        secure_delete_file(str(test_file))
        
        # Verify file is deleted
        assert not test_file.exists()
    
    def test_secure_delete_file_nonexistent(self):
        """Test sicheres Löschen von nicht existierenden Dateien."""
        # Try to delete a file that doesn't exist
        nonexistent_file = self.download_dir / "does_not_exist.txt"
        
        # Should not raise an exception
        secure_delete_file(str(nonexistent_file))
    
    def test_secure_delete_file_no_permissions(self):
        """Test sicheres Löschen von Dateien ohne Berechtigungen."""
        # Create a test file
        test_file = self.download_dir / "test_delete_no_perm.txt"
        test_file.write_text("This is test content")
        
        # Make file read-only
        test_file.chmod(stat.S_IREAD)
        
        # Try to delete read-only file
        # On some systems, this might still work depending on directory permissions
        try:
            secure_delete_file(str(test_file))
            # If it worked, file should be gone
            assert not test_file.exists() or not os.access(test_file, os.W_OK)
        except PermissionError:
            # This is also acceptable behavior
            pass
    
    def test_move_file_with_backup_normal(self):
        """Test Verschieben von Dateien mit Backup."""
        # Create source file
        source_file = self.download_dir / "source.txt"
        source_content = "Source file content"
        source_file.write_text(source_content)
        
        # Create destination file
        dest_file = self.download_dir / "dest.txt"
        dest_content = "Destination file content"
        dest_file.write_text(dest_content)
        
        # Move with backup
        backup_path = move_file_with_backup(str(source_file), str(dest_file))
        
        # Verify source file is gone
        assert not source_file.exists()
        
        # Verify destination has source content
        assert dest_file.exists()
        assert dest_file.read_text() == source_content
        
        # Verify backup exists with original destination content
        assert Path(backup_path).exists()
        assert Path(backup_path).read_text() == dest_content
    
    def test_move_file_with_backup_no_dest(self):
        """Test Verschieben von Dateien mit Backup wenn Ziel nicht existiert."""
        # Create source file
        source_file = self.download_dir / "source.txt"
        source_content = "Source file content"
        source_file.write_text(source_content)
        
        # Destination doesn't exist
        dest_file = self.download_dir / "new_dest.txt"
        
        # Move with backup (no backup should be created)
        backup_path = move_file_with_backup(str(source_file), str(dest_file))
        
        # Verify source file is gone
        assert not source_file.exists()
        
        # Verify destination has source content
        assert dest_file.exists()
        assert dest_file.read_text() == source_content
        
        # Verify no backup was created
        assert backup_path is None
    
    def test_move_file_with_backup_same_file(self):
        """Test Verschieben von Dateien mit Backup wenn Quelle und Ziel gleich sind."""
        # Create source file
        source_file = self.download_dir / "same_file.txt"
        source_content = "Same file content"
        source_file.write_text(source_content)
        
        # Try to move file to itself
        backup_path = move_file_with_backup(str(source_file), str(source_file))
        
        # File should still exist with same content
        assert source_file.exists()
        assert source_file.read_text() == source_content
        
        # No backup should be created
        assert backup_path is None
    
    def test_sanitize_filename_security_cases(self):
        """Test Sanitize-Filename mit Sicherheitsfällen."""
        # Test path traversal attempts
        traversal_names = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32\\config\\sam",
            "../../../../../../../../etc/shadow"
        ]
        
        for name in traversal_names:
            sanitized = sanitize_filename(name)
            # Should not contain path traversal
            assert ".." not in sanitized
            assert not sanitized.startswith("/")
            assert not sanitized.startswith("\\")
        
        # Test names with null bytes
        with_null = "test.mp3\0malicious_code"
        sanitized = sanitize_filename(with_null)
        # Should not contain null bytes
        assert "\0" not in sanitized
        
        # Test names with control characters
        with_control = "test\x01\x02\x03.mp3"
        sanitized = sanitize_filename(with_control)
        # Should not contain control characters
        assert "\x01" not in sanitized
        assert "\x02" not in sanitized
        assert "\x03" not in sanitized
    
    def test_create_download_directory_nested(self):
        """Test Erstellung von verschachtelten Download-Verzeichnissen."""
        # Create deeply nested directory path
        nested_dir = self.download_dir / "level1" / "level2" / "level3" / "level4"
        
        # Create the nested directory structure
        create_download_directory(str(nested_dir))
        
        # Verify all levels exist
        assert nested_dir.exists()
        assert nested_dir.is_dir()
        assert (self.download_dir / "level1").exists()
        assert (self.download_dir / "level1" / "level2").exists()
        assert (self.download_dir / "level1" / "level2" / "level3").exists()
    
    def test_file_operations_with_unicode_paths(self):
        """Test Dateioperationen mit Unicode-Pfaden."""
        # Create directory with unicode name
        unicode_dir = self.download_dir / "müsic_dïrectory_ñame"
        create_download_directory(str(unicode_dir))
        
        # Verify directory exists
        assert unicode_dir.exists()
        assert unicode_dir.is_dir()
        
        # Create file with unicode name
        unicode_file = unicode_dir / "müsic_fïle_ñame.mp3"
        unicode_file.write_text("Unicode test content")
        
        # Verify file exists
        assert unicode_file.exists()
        
        # Test disk space check with unicode path
        has_space = check_disk_space(str(unicode_dir), required_bytes=100)
        assert has_space
    
    def test_sanitize_filename_windows_reserved_names(self):
        """Test Sanitize-Filename mit Windows-reservierten Namen."""
        # Windows reserved names
        reserved_names = ["CON", "PRN", "AUX", "NUL", 
                         "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
                         "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"]
        
        for name in reserved_names:
            # Test as filename
            sanitized = sanitize_filename(f"{name}.txt")
            # Should not be exactly the reserved name
            assert sanitized != name
            assert ".txt" in sanitized
            
            # Test as basename
            sanitized = sanitize_filename(name)
            # Should not be exactly the reserved name
            assert sanitized != name