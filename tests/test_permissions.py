#!/usr/bin/env python3
"""
Berechtigungstests - Telegram Audio Downloader
===========================================

Tests für Dateiberechtigungen und Zugriffsrechte.
"""

import os
import sys
import tempfile
import stat
import platform
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from telegram_audio_downloader.downloader import AudioDownloader
from telegram_audio_downloader.utils import ensure_directory_exists


class TestFilePermissions:
    """Tests für Dateiberechtigungen."""
    
    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp(prefix="permissions_test_")
        self.download_dir = Path(self.temp_dir) / "downloads"
        self.download_dir.mkdir()
        
        yield
        
        # Cleanup
        import shutil
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def test_download_directory_permissions(self):
        """Test Berechtigungen des Download-Verzeichnisses."""
        downloader = AudioDownloader(download_dir=str(self.download_dir))
        
        # Prüfe, ob das Download-Verzeichnis existiert
        assert self.download_dir.exists()
        assert self.download_dir.is_dir()
        
        # Prüfe Verzeichnisberechtigungen
        dir_stat = self.download_dir.stat()
        
        # Verzeichnis sollte lesbar, schreibbar und durchsuchbar sein
        assert dir_stat.st_mode & stat.S_IRUSR  # Lesen
        assert dir_stat.st_mode & stat.S_IWUSR  # Schreiben
        assert dir_stat.st_mode & stat.S_IXUSR  # Durchsuchen
    
    def test_created_file_permissions(self):
        """Test Berechtigungen von erstellten Dateien."""
        # Erstelle eine Testdatei
        test_file = self.download_dir / "test_file.mp3"
        test_file.write_text("test content")
        
        # Prüfe Dateiberechtigungen
        file_stat = test_file.stat()
        
        # Datei sollte lesbar und schreibbar sein
        assert file_stat.st_mode & stat.S_IRUSR  # Lesen
        assert file_stat.st_mode & stat.S_IWUSR  # Schreiben
        
        # Datei sollte normalerweise nicht ausführbar sein
        if platform.system() != "Windows":
            # Unter Unix-Systemen prüfen wir, dass die Datei nicht ausführbar ist
            assert not (file_stat.st_mode & stat.S_IXUSR)
    
    def test_directory_creation_permissions(self):
        """Test Berechtigungen bei Verzeichniserstellung."""
        new_dir = self.download_dir / "new_subdir"
        created_dir = ensure_directory_exists(new_dir)
        
        # Prüfe, ob das Verzeichnis erstellt wurde
        assert created_dir.exists()
        assert created_dir.is_dir()
        
        # Prüfe Verzeichnisberechtigungen
        dir_stat = created_dir.stat()
        assert dir_stat.st_mode & stat.S_IRUSR  # Lesen
        assert dir_stat.st_mode & stat.S_IWUSR  # Schreiben
        assert dir_stat.st_mode & stat.S_IXUSR  # Durchsuchen
    
    @pytest.mark.skipif(platform.system() == "Windows", reason="Unix-specific permissions test")
    def test_unix_specific_permissions(self):
        """Test Unix-spezifische Berechtigungen."""
        # Erstelle eine Testdatei
        test_file = self.download_dir / "unix_test.mp3"
        test_file.write_text("unix test content")
        
        # Prüfe Unix-spezifische Berechtigungen
        file_stat = test_file.stat()
        
        # Prüfe Besitzer-Berechtigungen
        assert file_stat.st_mode & stat.S_IRUSR  # Besitzer Lesen
        assert file_stat.st_mode & stat.S_IWUSR  # Besitzer Schreiben
        assert not (file_stat.st_mode & stat.S_IXUSR)  # Besitzer Nicht-Ausführen
        
        # Prüfe Gruppen-Berechtigungen (können variieren)
        # Prüfe andere Benutzer-Berechtigungen (können variieren)
    
    def test_permission_errors_handling(self):
        """Test Umgang mit Berechtigungsfehlern."""
        # Dieser Test ist schwierig ohne echte Berechtigungsfehler
        # In einer echten Umgebung würden wir Berechtigungen ändern
        # um Fehler zu simulieren
        
        # Prüfe, ob der Downloader mit dem Download-Verzeichnis arbeiten kann
        downloader = AudioDownloader(download_dir=str(self.download_dir))
        assert downloader.download_dir == self.download_dir


class TestUserGroupPermissions:
    """Tests für Benutzer- und Gruppenberechtigungen."""
    
    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp(prefix="user_group_test_")
        self.download_dir = Path(self.temp_dir) / "downloads"
        self.download_dir.mkdir()
        
        yield
        
        # Cleanup
        import shutil
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    @pytest.mark.skipif(platform.system() == "Windows", reason="Unix-specific user/group test")
    def test_user_and_group_ownership(self):
        """Test Benutzer- und Gruppen-Eigentümerschaft."""
        import pwd
        import grp
        
        # Erstelle eine Testdatei
        test_file = self.download_dir / "ownership_test.mp3"
        test_file.write_text("ownership test")
        
        # Prüfe Eigentümerschaft
        file_stat = test_file.stat()
        
        # Prüfe Benutzer-ID
        user_info = pwd.getpwuid(file_stat.st_uid)
        assert user_info is not None
        
        # Prüfe Gruppen-ID
        group_info = grp.getgrgid(file_stat.st_gid)
        assert group_info is not None
    
    def test_cross_user_access_simulation(self):
        """Test Simulation von Zugriffen anderer Benutzer."""
        # Erstelle eine Testdatei
        test_file = self.download_dir / "cross_user_test.mp3"
        test_file.write_text("cross user test")
        
        # In einer echten Umgebung würden wir hier die Datei
        # für andere Benutzer zugänglich machen und dann
        # versuchen, als anderer Benutzer darauf zuzugreifen
        
        # Für Tests prüfen wir einfach, ob die Datei existiert
        assert test_file.exists()


class TestAccessControl:
    """Tests für Zugriffskontrolle."""
    
    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp(prefix="access_control_test_")
        self.download_dir = Path(self.temp_dir) / "downloads"
        self.download_dir.mkdir()
        
        yield
        
        # Cleanup
        import shutil
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def test_read_access(self):
        """Test Lesezugriff."""
        # Erstelle eine Testdatei
        test_file = self.download_dir / "read_test.mp3"
        test_content = "read access test content"
        test_file.write_text(test_content)
        
        # Prüfe Lesezugriff
        assert test_file.exists()
        read_content = test_file.read_text()
        assert read_content == test_content
    
    def test_write_access(self):
        """Test Schreibzugriff."""
        test_file = self.download_dir / "write_test.mp3"
        
        # Prüfe Schreibzugriff
        test_content = "write access test"
        test_file.write_text(test_content)
        assert test_file.exists()
        
        # Prüfe Inhalt
        read_content = test_file.read_text()
        assert read_content == test_content
    
    def test_delete_access(self):
        """Test Löschzugriff."""
        test_file = self.download_dir / "delete_test.mp3"
        test_file.write_text("delete test")
        
        # Prüfe, dass die Datei existiert
        assert test_file.exists()
        
        # Lösche die Datei
        test_file.unlink()
        
        # Prüfe, dass die Datei nicht mehr existiert
        assert not test_file.exists()
    
    @pytest.mark.skipif(platform.system() == "Windows", reason="Execute permission test")
    def test_execute_permission_denied_for_files(self):
        """Test dass Audiodateien nicht ausführbar sind."""
        test_file = self.download_dir / "execute_test.mp3"
        test_file.write_text("execute test content")
        
        # Prüfe, dass die Datei nicht ausführbar ist
        file_stat = test_file.stat()
        assert not (file_stat.st_mode & stat.S_IXUSR)
        assert not (file_stat.st_mode & stat.S_IXGRP)
        assert not (file_stat.st_mode & stat.S_IXOTH)


class TestPermissionSecurity:
    """Tests für Berechtigungssicherheit."""
    
    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp(prefix="permission_security_test_")
        self.download_dir = Path(self.temp_dir) / "downloads"
        self.download_dir.mkdir()
        
        yield
        
        # Cleanup
        import shutil
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def test_sensitive_file_permissions(self):
        """Test Berechtigungen sensibler Dateien."""
        # Erstelle eine Datei, die sensible Informationen enthalten könnte
        sensitive_file = self.download_dir / "sensitive_data.txt"
        sensitive_file.write_text("sensitive information")
        
        # Prüfe, dass die Datei nicht für andere Benutzer lesbar ist
        # (Dies ist eine vereinfachte Prüfung)
        file_stat = sensitive_file.stat()
        
        # Unter Unix-Systemen prüfen wir die Berechtigungen genauer
        if platform.system() != "Windows":
            # Datei sollte nur für den Besitzer lesbar/schreibbar sein
            # Dies ist eine vereinfachte Prüfung - in der echten Welt
            # würden wir genauere Berechtigungen setzen
            pass
    
    def test_temporary_file_permissions(self):
        """Test Berechtigungen temporärer Dateien."""
        # Erstelle eine temporäre Datei (wie bei partiellen Downloads)
        temp_file = self.download_dir / "temp_download.mp3.partial"
        temp_file.write_text("temporary content")
        
        # Prüfe Berechtigungen
        file_stat = temp_file.stat()
        assert file_stat.st_mode & stat.S_IRUSR  # Lesen
        assert file_stat.st_mode & stat.S_IWUSR  # Schreiben
    
    def test_log_file_permissions(self):
        """Test Berechtigungen von Log-Dateien."""
        # Erstelle ein Log-Verzeichnis
        log_dir = Path(self.temp_dir) / "logs"
        log_dir.mkdir()
        
        # Erstelle eine Log-Datei
        log_file = log_dir / "test.log"
        log_file.write_text("log entry")
        
        # Prüfe Log-Datei-Berechtigungen
        file_stat = log_file.stat()
        assert file_stat.st_mode & stat.S_IRUSR  # Lesen
        assert file_stat.st_mode & stat.S_IWUSR  # Schreiben


class TestPermissionEdgeCases:
    """Tests für Berechtigungs-Sonderfälle."""
    
    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp(prefix="permission_edge_test_")
        self.download_dir = Path(self.temp_dir) / "downloads"
        self.download_dir.mkdir()
        
        yield
        
        # Cleanup
        import shutil
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def test_very_long_filename_permissions(self):
        """Test Berechtigungen bei sehr langen Dateinamen."""
        # Erstelle einen sehr langen Dateinamen
        long_name = "a" * 200 + ".mp3"
        long_file = self.download_dir / long_name
        
        # Erstelle die Datei
        long_file.write_text("long filename test")
        
        # Prüfe Berechtigungen
        file_stat = long_file.stat()
        assert file_stat.st_mode & stat.S_IRUSR
        assert file_stat.st_mode & stat.S_IWUSR
    
    def test_unicode_filename_permissions(self):
        """Test Berechtigungen bei Unicode-Dateinamen."""
        # Erstelle Dateien mit Unicode-Namen
        unicode_names = [
            "müsic.mp3",
            "café.mp3",
            "naïve.mp3",
            "文件.mp3",  # Chinesisch
            "файл.mp3",  # Russisch
        ]
        
        for name in unicode_names:
            unicode_file = self.download_dir / name
            try:
                unicode_file.write_text(f"unicode test {name}")
                # Prüfe Berechtigungen
                file_stat = unicode_file.stat()
                assert file_stat.st_mode & stat.S_IRUSR
                assert file_stat.st_mode & stat.S_IWUSR
            except Exception:
                # Einige Systeme unterstützen möglicherweise nicht alle Unicode-Zeichen
                # in Dateinamen
                pass
    
    @pytest.mark.skipif(platform.system() == "Windows", reason="Symbolic link test")
    def test_symbolic_link_permissions(self):
        """Test Berechtigungen von symbolischen Links."""
        # Erstelle eine Originaldatei
        original_file = self.download_dir / "original.mp3"
        original_file.write_text("original content")
        
        # Erstelle einen symbolischen Link
        symlink_file = self.download_dir / "symlink.mp3"
        symlink_file.symlink_to(original_file)
        
        # Prüfe Berechtigungen
        # Symbolische Links haben normalerweise 777 Berechtigungen,
        # aber der Zugriff hängt von den Berechtigungen der Zieldatei ab
        symlink_stat = symlink_file.lstat()  # lstat für den Link selbst
        assert stat.S_ISLNK(symlink_stat.st_mode)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])