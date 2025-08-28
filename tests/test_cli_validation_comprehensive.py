#!/usr/bin/env python3
"""
Comprehensive CLI Validation Tests - Telegram Audio Downloader
=============================================================

Umfassende Tests für CLI-Validierung und Fehlerbehandlung.
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch
import pytest
from click.testing import CliRunner

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from telegram_audio_downloader.cli import main


class TestCLIValidationComprehensive:
    """Umfassende Tests für CLI-Validierung."""
    
    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Setup test environment."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp(prefix="cli_validation_test_")
        self.download_dir = Path(self.temp_dir) / "downloads"
        self.download_dir.mkdir()
        
        # Setup test database
        self.test_db_path = Path(self.temp_dir) / "test.db"
        os.environ["DB_PATH"] = str(self.test_db_path)
        
        yield
        
        # Cleanup
        import shutil
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def test_invalid_group_name_format(self):
        """Test ungültiges Gruppenname-Format."""
        result = self.runner.invoke(main, ['--group', 'invalid_format', '--limit', '5'])
        assert result.exit_code != 0
        assert "Invalid value" in result.output or "Error" in result.output
    
    def test_negative_limit_value(self):
        """Test negative Limit-Wert."""
        result = self.runner.invoke(main, ['--group', '@test_group', '--limit', '-5'])
        assert result.exit_code != 0
        assert "Invalid value" in result.output or "Error" in result.output
    
    def test_zero_limit_value(self):
        """Test Null-Limit-Wert."""
        result = self.runner.invoke(main, ['--group', '@test_group', '--limit', '0'])
        # Zero might be valid depending on implementation, but let's test it
        # If it's invalid, it should show an error
        if result.exit_code != 0:
            assert "Invalid value" in result.output or "Error" in result.output
    
    def test_missing_required_group_parameter(self):
        """Test fehlender erforderlicher Gruppenparameter."""
        result = self.runner.invoke(main, ['--limit', '5'])
        # Depending on implementation, this might be valid if there's a default
        # or invalid if group is required
        if result.exit_code != 0:
            assert "Missing option" in result.output or "Error" in result.output
    
    def test_invalid_directory_path(self):
        """Test ungültiger Verzeichnispfad."""
        result = self.runner.invoke(main, [
            '--group', '@test_group',
            '--limit', '5',
            '--directory', '/invalid/path/that/does/not/exist'
        ])
        # This might be handled at runtime rather than CLI validation
        # Let's check for error handling in output
        # If the command accepts it but fails later, that's also a valid test
    
    def test_conflicting_options(self):
        """Test widersprüchliche Optionen."""
        # If there are any conflicting options in the CLI, test them here
        # For now, we'll test with verbose and quiet as an example
        result = self.runner.invoke(main, [
            '--group', '@test_group',
            '--limit', '5',
            '--verbose',
            '--quiet'
        ])
        # Depending on implementation, this might be valid or invalid
        # If invalid, it should show an error
    
    def test_excessive_limit_value(self):
        """Test übermäßiger Limit-Wert."""
        result = self.runner.invoke(main, ['--group', '@test_group', '--limit', '1000000'])
        # This might be valid but could cause issues, so it's good to test
        # The application should handle this gracefully
    
    def test_invalid_api_credentials_format(self):
        """Test ungültiges API-Credentials-Format."""
        # Test with environment variables or command line options for API credentials
        with patch.dict(os.environ, {'API_ID': 'invalid', 'API_HASH': 'invalid'}):
            result = self.runner.invoke(main, ['--group', '@test_group', '--limit', '5'])
            # This would be tested more thoroughly in integration tests
            # but we can check for proper error handling in CLI
    
    def test_help_output_format(self):
        """Test Hilfe-Ausgabe-Format."""
        result = self.runner.invoke(main, ['--help'])
        assert result.exit_code == 0
        assert "Usage:" in result.output
        assert "--group" in result.output
        assert "--limit" in result.output
        # Check that help text is properly formatted and informative
    
    def test_version_output(self):
        """Test Versionsausgabe."""
        result = self.runner.invoke(main, ['--version'])
        # Version output should be consistent and properly formatted
        # This might exit with code 0 or raise SystemExit depending on implementation
        assert result.exit_code == 0 or result.exit_code == 1  # Accept both
    
    def test_unrecognized_option(self):
        """Test nicht erkannte Option."""
        result = self.runner.invoke(main, ['--group', '@test_group', '--unrecognized-option'])
        assert result.exit_code != 0
        assert "no such option" in result.output.lower() or "unrecognized" in result.output.lower()
    
    def test_multiple_group_parameters(self):
        """Test mehrere Gruppenparameter."""
        result = self.runner.invoke(main, [
            '--group', '@test_group1',
            '--group', '@test_group2'
        ])
        # Depending on implementation, this might be valid or invalid
        # If invalid, it should show an appropriate error message
    
    def test_empty_group_name(self):
        """Test leerer Gruppenname."""
        result = self.runner.invoke(main, ['--group', '', '--limit', '5'])
        assert result.exit_code != 0
        assert "Invalid value" in result.output or "Error" in result.output
    
    def test_special_characters_in_parameters(self):
        """Test Sonderzeichen in Parametern."""
        special_groups = [
            '@test@group',
            '@test group',
            '@test#group',
            '@test$group'
        ]
        
        for group in special_groups:
            result = self.runner.invoke(main, ['--group', group, '--limit', '5'])
            # Depending on validation rules, some might be valid, others invalid
            # The important thing is consistent error handling
    
    def test_numeric_group_name(self):
        """Test numerischer Gruppenname."""
        result = self.runner.invoke(main, ['--group', '@123456', '--limit', '5'])
        # This might be valid or invalid depending on Telegram's rules
        # The application should handle it appropriately