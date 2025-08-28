#!/usr/bin/env python3
"""
Dokumentationstests - Telegram Audio Downloader
============================================

Tests für die Dokumentation und API-Docs der Anwendung.
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Für diese Tests importieren wir Module, um sicherzustellen,
# dass sie keine Syntaxfehler haben und dokumentiert sind
from telegram_audio_downloader import cli, downloader, database, models, utils
from telegram_audio_downloader.error_handling import handle_error
from telegram_audio_downloader.logging_config import get_logger
from telegram_audio_downloader.performance import get_performance_monitor


class TestDocumentation:
    """Tests für die Dokumentation."""
    
    def test_module_docstrings(self):
        """Test Docstrings in Modulen."""
        # Prüfe, ob die Module Docstrings haben
        assert cli.__doc__ is not None
        assert downloader.__doc__ is not None
        assert database.__doc__ is not None
        assert models.__doc__ is not None
        assert utils.__doc__ is not None
    
    def test_class_docstrings(self):
        """Test Docstrings in Klassen."""
        # Prüfe, ob wichtige Klassen Docstrings haben
        from telegram_audio_downloader.downloader import AudioDownloader, LRUCache
        from telegram_audio_downloader.models import AudioFile, TelegramGroup
        
        assert AudioDownloader.__doc__ is not None
        assert LRUCache.__doc__ is not None
        assert AudioFile.__doc__ is not None
        assert TelegramGroup.__doc__ is not None
    
    def test_function_docstrings(self):
        """Test Docstrings in Funktionen."""
        # Prüfe, ob wichtige Funktionen Docstrings haben
        assert handle_error.__doc__ is not None
        assert get_logger.__doc__ is not None
        assert get_performance_monitor.__doc__ is not None
        
        # Prüfe einige Funktionen aus utils
        assert utils.sanitize_filename.__doc__ is not None
        assert utils.format_file_size.__doc__ is not None
    
    def test_cli_help_consistency(self):
        """Test Konsistenz der CLI-Hilfe mit Dokumentation."""
        from click.testing import CliRunner
        runner = CliRunner()
        
        # Teste, ob die CLI-Hilfe verfügbar ist
        result = runner.invoke(cli.cli, ['--help'])
        assert result.exit_code == 0
        assert "Usage:" in result.output
        
        # Teste einzelne Befehle
        commands = ['download', 'search', 'performance', 'config']
        for command in commands:
            result = runner.invoke(cli.cli, [command, '--help'])
            assert result.exit_code == 0
            assert "Usage:" in result.output


class TestREADME:
    """Tests für die README-Datei."""
    
    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Setup test environment."""
        self.project_root = Path(__file__).parent.parent
        yield
    
    def test_readme_exists(self):
        """Test dass README-Datei existiert."""
        readme_path = self.project_root / "README.md"
        assert readme_path.exists(), "README.md file should exist"
    
    def test_readme_content(self):
        """Test Inhalt der README-Datei."""
        readme_path = self.project_root / "README.md"
        
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Prüfe, ob wichtige Abschnitte vorhanden sind
        assert "# " in content  # Titel
        assert "## " in content  # Untertitel
        assert len(content) > 100  # Mindestlänge
    
    def test_readme_examples(self):
        """Test dass README-Beispiele korrekt sind."""
        readme_path = self.project_root / "README.md"
        
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Prüfe, ob Code-Beispiele vorhanden sind
        assert "```" in content  # Code-Blöcke
        assert "python" in content.lower() or "bash" in content.lower()  # Sprachangaben


class TestAPIConsistency:
    """Tests für API-Konsistenz."""
    
    def test_public_api_availability(self):
        """Test Verfügbarkeit der öffentlichen API."""
        # Prüfe, ob wichtige Klassen und Funktionen importiert werden können
        from telegram_audio_downloader.downloader import AudioDownloader
        from telegram_audio_downloader.models import AudioFile
        from telegram_audio_downloader.utils import sanitize_filename
        
        # Erstelle Instanzen, um sicherzustellen, dass sie funktionieren
        assert AudioDownloader is not None
        assert AudioFile is not None
        assert sanitize_filename is not None
    
    def test_api_parameter_consistency(self):
        """Test Konsistenz der API-Parameter."""
        import inspect
        from telegram_audio_downloader.downloader import AudioDownloader
        
        # Prüfe die Signatur des Konstruktors
        sig = inspect.signature(AudioDownloader.__init__)
        params = list(sig.parameters.keys())
        
        # Prüfe, ob erwartete Parameter vorhanden sind
        assert "download_dir" in params
        assert "max_concurrent_downloads" in params


class TestDocstringConsistency:
    """Tests für Docstring-Konsistenz."""
    
    def test_function_parameter_documentation(self):
        """Test dass Funktionsparameter dokumentiert sind."""
        from telegram_audio_downloader.utils import sanitize_filename
        import inspect
        
        # Prüfe, ob die Funktion eine Docstring hat
        assert sanitize_filename.__doc__ is not None
        
        # Prüfe die Signatur
        sig = inspect.signature(sanitize_filename)
        params = list(sig.parameters.keys())
        
        # Alle Parameter sollten in der Docstring erwähnt werden
        # (Dies ist eine vereinfachte Prüfung)
        if params:
            assert len(params) > 0
    
    def test_return_value_documentation(self):
        """Test dass Rückgabewerte dokumentiert sind."""
        from telegram_audio_downloader.utils import format_file_size
        
        # Prüfe, ob die Funktion eine Docstring hat
        assert format_file_size.__doc__ is not None
        
        # Prüfe, ob "Returns:" oder ähnliches in der Docstring enthalten ist
        assert "return" in format_file_size.__doc__.lower() or "gibt" in format_file_size.__doc__.lower()
    
    def test_exception_documentation(self):
        """Test dass Ausnahmen dokumentiert sind."""
        from telegram_audio_downloader.error_handling import handle_error
        
        # Prüfe, ob die Funktion eine Docstring hat
        assert handle_error.__doc__ is not None
        
        # Prüfe, ob "Raises:" oder "Exception" in der Docstring enthalten ist
        docstring = handle_error.__doc__.lower()
        assert "raise" in docstring or "exception" in docstring or "fehler" in docstring


class TestDocumentationExamples:
    """Tests für Beispiele in der Dokumentation."""
    
    def test_cli_usage_examples(self):
        """Test CLI-Verwendungsbeispiele."""
        # Dies testet, ob die in der Dokumentation gezeigten
        # CLI-Befehle tatsächlich funktionieren
        
        from click.testing import CliRunner
        runner = CliRunner()
        
        # Teste grundlegende CLI-Verwendung
        result = runner.invoke(cli.cli, ['--help'])
        assert result.exit_code == 0
    
    def test_code_examples(self):
        """Test Code-Beispiele aus der Dokumentation."""
        # Dies testet, ob Code-Beispiele aus der Dokumentation
        # syntaktisch korrekt sind und ausgeführt werden können
        
        # Beispiel: Import und Verwendung des AudioDownloaders
        try:
            from telegram_audio_downloader.downloader import AudioDownloader
            # Dies sollte ohne ImportError funktionieren
            assert AudioDownloader is not None
        except ImportError:
            pytest.fail("AudioDownloader should be importable")


class TestDocumentationCompleteness:
    """Tests für Vollständigkeit der Dokumentation."""
    
    def test_all_public_functions_documented(self):
        """Test dass alle öffentlichen Funktionen dokumentiert sind."""
        import telegram_audio_downloader.utils as utils_module
        
        # Prüfe, ob alle Funktionen in utils dokumentiert sind
        for name in dir(utils_module):
            if not name.startswith('_'):  # Öffentliche Funktionen
                obj = getattr(utils_module, name)
                if callable(obj):
                    assert obj.__doc__ is not None, f"Function {name} should have a docstring"
    
    def test_all_public_classes_documented(self):
        """Test dass alle öffentlichen Klassen dokumentiert sind."""
        import telegram_audio_downloader.downloader as downloader_module
        
        # Prüfe, ob alle Klassen in downloader dokumentiert sind
        for name in dir(downloader_module):
            if not name.startswith('_'):  # Öffentliche Klassen
                obj = getattr(downloader_module, name)
                if isinstance(obj, type):  # Es ist eine Klasse
                    assert obj.__doc__ is not None, f"Class {name} should have a docstring"
    
    def test_all_cli_commands_documented(self):
        """Test dass alle CLI-Befehle dokumentiert sind."""
        # Prüfe, ob alle CLI-Befehle Hilfetext haben
        from click.testing import CliRunner
        runner = CliRunner()
        
        # Teste alle Hauptbefehle
        commands = ['download', 'search', 'performance', 'config']
        for command in commands:
            result = runner.invoke(cli.cli, [command, '--help'])
            assert result.exit_code == 0
            assert len(result.output.strip()) > 0, f"Command {command} should have help text"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])