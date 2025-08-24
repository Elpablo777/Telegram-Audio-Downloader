#!/usr/bin/env python3
"""
Plattformtests - Telegram Audio Downloader
========================================

Tests für plattformübergreifende Kompatibilität.
"""

import os
import sys
import tempfile
import platform
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from telegram_audio_downloader.downloader import AudioDownloader
from telegram_audio_downloader.utils import sanitize_filename, get_unique_filepath


class TestPlatformCompatibility:
    """Tests für plattformübergreifende Kompatibilität."""
    
    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp(prefix="platform_test_")
        self.download_dir = Path(self.temp_dir) / "downloads"
        self.download_dir.mkdir()
        
        yield
        
        # Cleanup
        import shutil
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def test_platform_detection(self):
        """Test Erkennung der Plattform."""
        current_platform = platform.system()
        assert current_platform in ["Windows", "Linux", "Darwin"]  # macOS ist Darwin
    
    def test_path_handling_windows(self):
        """Test Pfadverarbeitung unter Windows."""
        if platform.system() == "Windows":
            # Teste Windows-spezifische Pfade
            windows_path = Path("C:\\Users\\Test\\Downloads")
            assert str(windows_path).startswith("C:\\")
    
    def test_path_handling_unix(self):
        """Test Pfadverarbeitung unter Unix-Systemen."""
        if platform.system() in ["Linux", "Darwin"]:
            # Teste Unix-spezifische Pfade
            unix_path = Path("/home/test/downloads")
            assert str(unix_path).startswith("/")
    
    def test_filename_sanitization_cross_platform(self):
        """Test Dateinamen-Sanitisierung plattformübergreifend."""
        # Teste verschiedene plattformspezifische Problemfälle
        problematic_names = [
            "test<file>.mp3",      # < und > sind unter Windows problematisch
            "test:file.mp3",       # : ist unter Windows problematisch
            "test|file.mp3",       # | ist unter Windows problematisch
            "test*file.mp3",       # * ist unter Windows problematisch
            "test?file.mp3",       # ? ist unter Windows problematisch
            "test\"file.mp3",      # " ist unter Windows problematisch
            "test/file.mp3",       # / ist überall problematisch
            "test\\file.mp3",      # \ ist unter Windows problematisch
            "CON.mp3",             # Reservierte Namen unter Windows
            "PRN.mp3",             # Reservierte Namen unter Windows
            "AUX.mp3",             # Reservierte Namen unter Windows
            "NUL.mp3",             # Reservierte Namen unter Windows
        ]
        
        for name in problematic_names:
            sanitized = sanitize_filename(name)
            # Der sanierte Name sollte nicht die problematischen Zeichen enthalten
            assert "<" not in sanitized
            assert ">" not in sanitized
            assert ":" not in sanitized
            assert "|" not in sanitized
            assert "*" not in sanitized
            assert "?" not in sanitized
            assert "\"" not in sanitized
            # Bei reservierten Namen sollte ein Prefix hinzugefügt werden
            if name.upper() in ["CON", "PRN", "AUX", "NUL"]:
                assert sanitized.startswith("_")
    
    def test_file_operations_cross_platform(self):
        """Test Dateioperationen plattformübergreifend."""
        # Erstelle eine Testdatei
        test_file = self.download_dir / "test_file.mp3"
        test_file.write_text("test content")
        
        # Prüfe, ob die Datei existiert
        assert test_file.exists()
        
        # Prüfe Dateiberechtigungen (plattformspezifisch)
        if platform.system() != "Windows":
            # Unter Unix-Systemen prüfe Berechtigungen
            import stat
            file_stat = test_file.stat()
            # Datei sollte lesbar sein
            assert file_stat.st_mode & stat.S_IRUSR
    
    def test_downloader_cross_platform(self):
        """Test Downloader plattformübergreifend."""
        downloader = AudioDownloader(
            download_dir=str(self.download_dir),
            max_concurrent_downloads=2
        )
        
        # Prüfe, ob der Downloader korrekt initialisiert wurde
        assert downloader.download_dir == self.download_dir
        assert downloader.max_concurrent_downloads == 2


class TestPythonVersionCompatibility:
    """Tests für Kompatibilität mit verschiedenen Python-Versionen."""
    
    def test_python_version_detection(self):
        """Test Erkennung der Python-Version."""
        major, minor, patch = platform.python_version_tuple()
        assert int(major) >= 3  # Mindestens Python 3
        assert int(minor) >= 7  # Mindestens Python 3.7
    
    def test_supported_python_versions(self):
        """Test Unterstützung der Python-Versionen."""
        python_version = platform.python_version()
        # Die Anwendung sollte mit Python 3.7+ funktionieren
        assert python_version.startswith("3.")
    
    def test_async_await_compatibility(self):
        """Test Async/Await-Kompatibilität."""
        # Prüfe, ob async/await verfügbar ist (Python 3.5+)
        import asyncio
        
        async def test_async_function():
            return "async result"
        
        # Dies sollte ohne Syntaxfehler funktionieren
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(test_async_function())
        loop.close()
        
        assert result == "async result"


class TestFilesystemCompatibility:
    """Tests für Dateisystem-Kompatibilität."""
    
    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp(prefix="filesystem_test_")
        self.download_dir = Path(self.temp_dir) / "downloads"
        self.download_dir.mkdir()
        
        yield
        
        # Cleanup
        import shutil
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def test_long_filename_handling(self):
        """Test Umgang mit langen Dateinamen."""
        # Erstelle einen sehr langen Dateinamen
        long_name = "a" * 300 + ".mp3"
        sanitized = sanitize_filename(long_name, max_length=255)
        
        # Der sanierte Name sollte die maximale Länge nicht überschreiten
        assert len(sanitized) <= 255
    
    def test_unicode_filename_handling(self):
        """Test Umgang mit Unicode-Dateinamen."""
        # Teste verschiedene Unicode-Zeichen
        unicode_names = [
            "müsic.mp3",           # Umlaute
            "café.mp3",            # Akzente
            "naïve.mp3",           # Tilde
            "résumé.mp3",          # Akzente
            "文件.mp3",             # Chinesische Zeichen
            "файл.mp3",            # Kyrillische Zeichen
            "archivo.mp3",         # Spanische Zeichen
        ]
        
        for name in unicode_names:
            sanitized = sanitize_filename(name)
            # Der sanierte Name sollte nicht leer sein
            assert len(sanitized) > 0
            # Unicode-Zeichen sollten erhalten bleiben (oder ersetzt werden)
            assert isinstance(sanitized, str)
    
    def test_case_sensitivity(self):
        """Test Groß-/Kleinschreibung."""
        # Unter Windows sind Dateisysteme normalerweise nicht case-sensitiv
        # Unter Unix-Systemen schon
        
        test_file1 = self.download_dir / "test.mp3"
        test_file2 = self.download_dir / "TEST.mp3"
        
        # Erstelle die erste Datei
        test_file1.write_text("content1")
        
        if platform.system() == "Windows":
            # Unter Windows sind beide Pfade gleich
            assert test_file1.exists()
        else:
            # Unter Unix-Systemen sind sie unterschiedlich
            assert test_file1.exists()
            # test_file2 existiert noch nicht, es sei denn es ist das gleiche Dateisystem


class TestEnvironmentCompatibility:
    """Tests für Umgebungs-Kompatibilität."""
    
    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Setup test environment."""
        self.original_env = os.environ.copy()
        yield
        # Stelle die ursprüngliche Umgebung wieder her
        os.environ.clear()
        os.environ.update(self.original_env)
    
    def test_environment_variable_handling(self):
        """Test Umgang mit Umgebungsvariablen."""
        # Setze Test-Umgebungsvariablen
        os.environ["TEST_VAR"] = "test_value"
        
        # Prüfe, ob sie korrekt gelesen werden
        assert os.environ.get("TEST_VAR") == "test_value"
        
        # Prüfe, ob nicht existierende Variablen None zurückgeben
        assert os.environ.get("NONEXISTENT_VAR") is None
    
    def test_path_environment_variables(self):
        """Test Pfad-Umgebungsvariablen."""
        # Prüfe wichtige Pfad-Variablen
        path_vars = ["PATH", "HOME"]
        if platform.system() == "Windows":
            path_vars = ["PATH", "USERPROFILE"]
        
        for var in path_vars:
            if var in os.environ:
                path_value = os.environ[var]
                assert isinstance(path_value, str)
                assert len(path_value) > 0


class TestLibraryCompatibility:
    """Tests für Bibliotheks-Kompatibilität."""
    
    def test_required_libraries_import(self):
        """Test Import der erforderlichen Bibliotheken."""
        # Prüfe, ob alle erforderlichen Bibliotheken importiert werden können
        try:
            import telethon
            import peewee
            import click
            import tqdm
            import mutagen
        except ImportError as e:
            pytest.fail(f"Required library import failed: {e}")
    
    def test_library_versions(self):
        """Test Bibliotheksversionen."""
        import telethon
        import peewee
        
        # Prüfe, ob die Bibliotheken minimale Versionen haben
        # Dies sind nur Beispiele - die tatsächlichen Anforderungen können anders sein
        assert telethon.__version__ is not None
        assert peewee.__version__ is not None


class TestCharacterEncoding:
    """Tests für Zeichencodierung."""
    
    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp(prefix="encoding_test_")
        self.download_dir = Path(self.temp_dir) / "downloads"
        self.download_dir.mkdir()
        
        yield
        
        # Cleanup
        import shutil
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def test_utf8_encoding(self):
        """Test UTF-8 Codierung."""
        # Erstelle eine Datei mit UTF-8 Inhalt
        test_content = "Test with üñíçødé characters"
        test_file = self.download_dir / "utf8_test.txt"
        test_file.write_text(test_content, encoding='utf-8')
        
        # Lese den Inhalt zurück
        read_content = test_file.read_text(encoding='utf-8')
        assert read_content == test_content
    
    def test_file_encoding_consistency(self):
        """Test Datei-Codierungskonsistenz."""
        # Erstelle mehrere Dateien mit verschiedenen Inhalten
        test_strings = [
            "ASCII content",
            "Ümläüts",      # Latin-1
            "中文内容",      # Chinese
            "Русский",      # Russian
            "العربية",      # Arabic (rechts nach links)
        ]
        
        for i, content in enumerate(test_strings):
            test_file = self.download_dir / f"encoding_test_{i}.txt"
            test_file.write_text(content, encoding='utf-8')
            
            # Lese zurück und prüfe
            read_content = test_file.read_text(encoding='utf-8')
            assert read_content == content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])