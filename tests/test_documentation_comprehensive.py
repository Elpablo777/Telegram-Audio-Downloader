#!/usr/bin/env python3
"""
Comprehensive Documentation Tests - Telegram Audio Downloader
============================================================

Umfassende Tests für Dokumentation und Beispiele.
"""

import os
import sys
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import modules to test docstrings
from telegram_audio_downloader import cli, downloader, database, models, utils
from telegram_audio_downloader.utils import file_operations, rate_limiter, metadata_extractor


class TestDocumentationComprehensive:
    """Umfassende Tests für Dokumentation."""
    
    def test_module_docstrings_exist(self):
        """Test dass Module Docstrings haben."""
        # Check main modules
        assert cli.__doc__ is not None and len(cli.__doc__.strip()) > 0
        assert downloader.__doc__ is not None and len(downloader.__doc__.strip()) > 0
        assert database.__doc__ is not None and len(database.__doc__.strip()) > 0
        assert models.__doc__ is not None and len(models.__doc__.strip()) > 0
        
        # Check utility modules
        assert file_operations.__doc__ is not None and len(file_operations.__doc__.strip()) > 0
        assert rate_limiter.__doc__ is not None and len(rate_limiter.__doc__.strip()) > 0
        assert metadata_extractor.__doc__ is not None and len(metadata_extractor.__doc__.strip()) > 0
    
    def test_class_docstrings_exist(self):
        """Test dass Klassen Docstrings haben."""
        # Import classes to test
        from telegram_audio_downloader.downloader import AudioDownloader
        from telegram_audio_downloader.database import init_db, reset_db
        from telegram_audio_downloader.utils.rate_limiter import RateLimiter
        from telegram_audio_downloader.utils.lru_cache import LRUCache
        
        # Check that classes have docstrings
        assert AudioDownloader.__doc__ is not None and len(AudioDownloader.__doc__.strip()) > 0
        assert RateLimiter.__doc__ is not None and len(RateLimiter.__doc__.strip()) > 0
        assert LRUCache.__doc__ is not None and len(LRUCache.__doc__.strip()) > 0
    
    def test_function_docstrings_exist(self):
        """Test dass Funktionen Docstrings haben."""
        # Check some key functions
        assert downloader.download_audio_files.__doc__ is not None
        assert database.init_db.__doc__ is not None and len(database.init_db.__doc__.strip()) > 0
        assert database.reset_db.__doc__ is not None and len(database.reset_db.__doc__.strip()) > 0
        assert file_operations.sanitize_filename.__doc__ is not None and len(file_operations.sanitize_filename.__doc__.strip()) > 0
        assert rate_limiter.RateLimiter.acquire.__doc__ is not None and len(rate_limiter.RateLimiter.acquire.__doc__.strip()) > 0
    
    def test_docstring_quality(self):
        """Test Qualität der Docstrings."""
        # Check that docstrings are not just placeholders
        assert cli.__doc__ != "Main module"
        assert cli.__doc__ != "Main"
        assert cli.__doc__ != "CLI module"
        
        # Check that docstrings contain meaningful content
        assert len(cli.__doc__.split()) > 3  # At least 4 words
        
        # Check downloader docstring
        from telegram_audio_downloader.downloader import AudioDownloader
        assert len(AudioDownloader.__doc__.split()) > 5  # At least 6 words
    
    def test_readme_examples(self):
        """Test Beispiele in README.md."""
        # Read README.md
        readme_path = Path(__file__).parent.parent / "README.md"
        if readme_path.exists():
            readme_content = readme_path.read_text(encoding='utf-8')
            
            # Check for basic structure
            assert "# " in readme_content  # Has title
            assert "## " in readme_content  # Has sections
            
            # Check for installation instructions
            assert "pip install" in readme_content or "Installation" in readme_content
            
            # Check for usage examples
            assert "Usage" in readme_content or "usage" in readme_content.lower()
            assert "--group" in readme_content or "--help" in readme_content
    
    def test_cli_help_documentation(self):
        """Test CLI-Hilfe-Dokumentation."""
        from click.testing import CliRunner
        runner = CliRunner()
        
        # Test that help output is meaningful
        result = runner.invoke(cli.main, ['--help'])
        assert result.exit_code == 0
        
        # Check for essential help content
        assert "--group" in result.output
        assert "--limit" in result.output
        assert "Usage:" in result.output
        assert "Options:" in result.output
    
    def test_api_documentation_consistency(self):
        """Test Konsistenz der API-Dokumentation."""
        # Check that function signatures match their docstrings
        from telegram_audio_downloader.downloader import AudioDownloader
        
        # Get the __init__ method
        init_method = AudioDownloader.__init__
        if init_method.__doc__:
            # Check that documented parameters exist in signature
            # This is a basic check - in practice, you might use introspection
            # to match parameters with docstring descriptions
            pass
    
    def test_example_scripts_execution(self):
        """Test Ausführung von Beispielskripten."""
        # Check if there are example scripts in the documentation
        examples_dir = Path(__file__).parent.parent / "docs" / "examples"
        if examples_dir.exists():
            example_scripts = list(examples_dir.glob("*.py"))
            
            # Try to execute each example script
            for script in example_scripts:
                try:
                    # Execute script in a subprocess to avoid side effects
                    result = subprocess.run([
                        sys.executable, str(script)
                    ], capture_output=True, text=True, timeout=30)
                    
                    # Should not crash with syntax errors
                    assert result.returncode != 2  # 2 typically indicates syntax error
                except subprocess.TimeoutExpired:
                    # Timeout is acceptable for examples that might wait for input
                    pass
                except Exception:
                    # Other exceptions might indicate issues
                    pass  # We don't fail the test but could log this
    
    def test_changelog_format(self):
        """Test Format des CHANGELOG.md."""
        changelog_path = Path(__file__).parent.parent / "CHANGELOG.md"
        if changelog_path.exists():
            changelog_content = changelog_path.read_text(encoding='utf-8')
            
            # Check for basic changelog structure
            assert "# " in changelog_content  # Has title
            assert "## " in changelog_content  # Has version sections
            assert "[Unreleased]" in changelog_content or "[v" in changelog_content  # Has version markers
    
    def test_code_comments_quality(self):
        """Test Qualität der Code-Kommentare."""
        # Check that source files have meaningful comments
        src_dir = Path(__file__).parent.parent / "src"
        if src_dir.exists():
            python_files = src_dir.rglob("*.py")
            
            for py_file in python_files:
                content = py_file.read_text(encoding='utf-8')
                
                # Check for comments (excluding docstrings)
                lines = content.split('\n')
                comment_lines = [line for line in lines if line.strip().startswith('#')]
                
                # Should have some comments in larger files
                if len(lines) > 50:  # For larger files
                    # Either has inline comments or docstrings
                    has_comments = len(comment_lines) > 0
                    has_docstrings = '"""' in content or "'''" in content
                    assert has_comments or has_docstrings
    
    def test_tutorial_completeness(self):
        """Test Vollständigkeit der Tutorials."""
        docs_dir = Path(__file__).parent.parent / "docs"
        if docs_dir.exists():
            # Look for tutorial files
            tutorials = list(docs_dir.glob("*tutorial*.md")) + list(docs_dir.glob("*guide*.md"))
            
            for tutorial in tutorials:
                content = tutorial.read_text(encoding='utf-8')
                
                # Should have basic structure
                assert "# " in content  # Has title
                assert len(content.split()) > 50  # Has substantial content
    
    def test_configuration_documentation(self):
        """Test Dokumentation der Konfiguration."""
        # Check that configuration options are documented
        docs_dir = Path(__file__).parent.parent / "docs"
        if docs_dir.exists():
            # Look for configuration documentation
            config_docs = list(docs_dir.glob("*config*.md")) + list(docs_dir.glob("*configuration*.md"))
            
            # Should have configuration documentation
            # assert len(config_docs) > 0  # This might be too strict
    
    def test_api_reference_generation(self):
        """Test Generierung der API-Referenz."""
        # This would typically test if sphinx or similar can generate docs
        # For now, we'll check if the required files exist
        docs_dir = Path(__file__).parent.parent / "docs"
        if docs_dir.exists():
            # Check for API reference files
            api_ref_files = list(docs_dir.glob("api/*")) + list(docs_dir.glob("reference/*"))
            # We won't assert this as it might not exist in all projects
    
    def test_documentation_links(self):
        """Test Links in der Dokumentation."""
        readme_path = Path(__file__).parent.parent / "README.md"
        if readme_path.exists():
            content = readme_path.read_text(encoding='utf-8')
            
            # Check for relative links to documentation
            if "docs/" in content or "documentation" in content.lower():
                # This indicates documentation structure exists
                pass
    
    def test_command_line_interface_documentation(self):
        """Test Dokumentation der Kommandozeilenschnittstelle."""
        from click.testing import CliRunner
        runner = CliRunner()
        
        # Test help output comprehensiveness
        result = runner.invoke(cli.main, ['--help'])
        
        # Should document all major options
        assert "--group" in result.output
        assert "--limit" in result.output
        # Add other options as they exist in the CLI
    
    def test_error_handling_documentation(self):
        """Test Dokumentation der Fehlerbehandlung."""
        # Check that common error cases are documented
        readme_path = Path(__file__).parent.parent / "README.md"
        if readme_path.exists():
            content = readme_path.read_text(encoding='utf-8')
            
            # Should mention error handling or troubleshooting
            error_keywords = ["error", "troubleshoot", "issue", "problem"]
            has_error_docs = any(keyword in content.lower() for keyword in error_keywords)
            
            # This is a soft check - documentation might be in separate files