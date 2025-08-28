#!/usr/bin/env python3
"""
Configuration Edge Cases Tests - Telegram Audio Downloader
========================================================

Tests für Konfigurationseckfälle und Prioritäten.
"""

import os
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import patch
import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from telegram_audio_downloader.config import ConfigManager


class TestConfigEdgeCases:
    """Tests für Konfigurationseckfälle."""
    
    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp(prefix="config_edge_test_")
        self.config_dir = Path(self.temp_dir) / "config"
        self.config_dir.mkdir()
        self.config_file = self.config_dir / "config.json"
        
        # Set environment variables for tests
        os.environ["CONFIG_DIR"] = str(self.config_dir)
        
        yield
        
        # Cleanup
        import shutil
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def test_empty_config_file(self):
        """Test leere Konfigurationsdatei."""
        # Create empty config file
        self.config_file.write_text("")
        
        config_manager = ConfigManager()
        # Should handle empty config gracefully and use defaults
        config = config_manager.get_config()
        assert isinstance(config, dict)
        # Should have default values
        assert "max_concurrent_downloads" in config
    
    def test_malformed_json_config(self):
        """Test fehlerhafte JSON-Konfiguration."""
        # Create malformed JSON config
        self.config_file.write_text("{ invalid json }")
        
        config_manager = ConfigManager()
        # Should handle malformed JSON gracefully and use defaults
        config = config_manager.get_config()
        assert isinstance(config, dict)
        # Should have default values despite malformed JSON
        assert "max_concurrent_downloads" in config
    
    def test_config_with_extra_fields(self):
        """Test Konfiguration mit zusätzlichen Feldern."""
        # Create config with extra fields
        config_data = {
            "max_concurrent_downloads": 3,
            "rate_limit_delay": 0.5,
            "extra_field_1": "should_be_ignored",
            "extra_field_2": 123,
            "nested": {
                "field": "also_ignored"
            }
        }
        
        self.config_file.write_text(json.dumps(config_data))
        
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        # Should only contain expected fields
        assert config["max_concurrent_downloads"] == 3
        assert config["rate_limit_delay"] == 0.5
        # Extra fields should not be in the final config
        assert "extra_field_1" not in config
        assert "extra_field_2" not in config
        assert "nested" not in config
    
    def test_config_with_missing_fields(self):
        """Test Konfiguration mit fehlenden Feldern."""
        # Create config with missing fields
        config_data = {
            "max_concurrent_downloads": 5
            # rate_limit_delay is missing
        }
        
        self.config_file.write_text(json.dumps(config_data))
        
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        # Should have the provided value
        assert config["max_concurrent_downloads"] == 5
        # Should have default value for missing field
        assert "rate_limit_delay" in config
        assert isinstance(config["rate_limit_delay"], (int, float))
    
    def test_config_type_mismatches(self):
        """Test Typfehler in Konfiguration."""
        # Create config with wrong types
        config_data = {
            "max_concurrent_downloads": "three",  # Should be int
            "rate_limit_delay": "half",  # Should be float
            "download_dir": 123  # Should be string
        }
        
        self.config_file.write_text(json.dumps(config_data))
        
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        # Should use defaults for invalid types
        assert isinstance(config["max_concurrent_downloads"], int)
        assert isinstance(config["rate_limit_delay"], (int, float))
        assert isinstance(config["download_dir"], str)
    
    def test_config_priority_env_over_file(self):
        """Test Priorität von Umgebungsvariablen über Datei."""
        # Create config file
        config_data = {
            "max_concurrent_downloads": 2
        }
        self.config_file.write_text(json.dumps(config_data))
        
        # Set environment variable with higher priority
        os.environ["MAX_CONCURRENT_DOWNLOADS"] = "5"
        
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        # Environment variable should take precedence
        assert config["max_concurrent_downloads"] == 5
    
    def test_config_priority_cli_over_env(self):
        """Test Priorität von CLI-Argumenten über Umgebungsvariablen."""
        # Set environment variable
        os.environ["MAX_CONCURRENT_DOWNLOADS"] = "3"
        
        config_manager = ConfigManager()
        
        # Pass CLI argument with highest priority
        config = config_manager.get_config(cli_args={"max_concurrent_downloads": 7})
        
        # CLI argument should take precedence
        assert config["max_concurrent_downloads"] == 7
    
    def test_config_file_permissions_error(self):
        """Test Konfigurationsdatei mit Berechtigungsfehler."""
        # Create config file
        config_data = {
            "max_concurrent_downloads": 4
        }
        self.config_file.write_text(json.dumps(config_data))
        
        # Make file unreadable
        self.config_file.chmod(0o000)
        
        config_manager = ConfigManager()
        # Should handle permission errors gracefully
        config = config_manager.get_config()
        
        # Should use defaults
        assert isinstance(config["max_concurrent_downloads"], int)
        
        # Restore permissions for cleanup
        self.config_file.chmod(0o644)
    
    def test_nonexistent_config_directory(self):
        """Test nicht existierendes Konfigurationsverzeichnis."""
        # Set config directory to non-existent path
        nonexistent_dir = Path(self.temp_dir) / "nonexistent"
        os.environ["CONFIG_DIR"] = str(nonexistent_dir)
        
        config_manager = ConfigManager()
        # Should handle non-existent directory gracefully
        config = config_manager.get_config()
        
        # Should use defaults
        assert isinstance(config, dict)
        assert "max_concurrent_downloads" in config
    
    def test_config_with_null_values(self):
        """Test Konfiguration mit Null-Werten."""
        # Create config with null values
        config_data = {
            "max_concurrent_downloads": None,
            "rate_limit_delay": None
        }
        
        self.config_file.write_text(json.dumps(config_data))
        
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        # Should use defaults for null values
        assert isinstance(config["max_concurrent_downloads"], int)
        assert isinstance(config["rate_limit_delay"], (int, float))
    
    def test_config_with_negative_values(self):
        """Test Konfiguration mit negativen Werten."""
        # Create config with negative values
        config_data = {
            "max_concurrent_downloads": -5,  # Should be positive
            "rate_limit_delay": -1.0  # Should be non-negative
        }
        
        self.config_file.write_text(json.dumps(config_data))
        
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        # Should use defaults for invalid negative values
        assert config["max_concurrent_downloads"] > 0
        assert config["rate_limit_delay"] >= 0
    
    def test_config_with_extreme_values(self):
        """Test Konfiguration mit extremen Werten."""
        # Create config with extreme values
        config_data = {
            "max_concurrent_downloads": 1000000,  # Very large
            "rate_limit_delay": 1000000.0  # Very large
        }
        
        self.config_file.write_text(json.dumps(config_data))
        
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        # Should accept extreme values (validation might happen elsewhere)
        assert config["max_concurrent_downloads"] == 1000000
        assert config["rate_limit_delay"] == 1000000.0
    
    def test_config_case_sensitivity(self):
        """Test Groß-/Kleinschreibung in Konfiguration."""
        # Create config with mixed case keys
        config_data = {
            "Max_Concurrent_Downloads": 3,  # Wrong case
            "RATE_LIMIT_DELAY": 0.5  # Wrong case
        }
        
        self.config_file.write_text(json.dumps(config_data))
        
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        # Should not recognize wrong case keys and use defaults
        assert "Max_Concurrent_Downloads" not in config
        assert "RATE_LIMIT_DELAY" not in config
        # Should have default values
        assert isinstance(config["max_concurrent_downloads"], int)
        assert isinstance(config["rate_limit_delay"], (int, float))
    
    def test_config_with_unicode_characters(self):
        """Test Konfiguration mit Unicode-Zeichen."""
        # Create config with unicode values
        config_data = {
            "download_dir": "/path/with/üñíçödé",
            "user_agent": "Télégram Downloader v1.0"
        }
        
        self.config_file.write_text(json.dumps(config_data, ensure_ascii=False))
        
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        # Should handle unicode properly
        assert "download_dir" in config
        assert "user_agent" in config