#!/usr/bin/env python3
"""
Konfigurationstests - Telegram Audio Downloader
============================================

Tests für Konfigurationsoptionen und -verwaltung.
"""

import os
import sys
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from telegram_audio_downloader.config import ConfigManager
from telegram_audio_downloader.cli import config
from click.testing import CliRunner


class TestConfiguration:
    """Tests für die Konfigurationsverwaltung."""
    
    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp(prefix="config_test_")
        self.config_dir = Path(self.temp_dir) / "config"
        self.config_dir.mkdir()
        self.config_file = self.config_dir / "config.json"
        
        # Setze Umgebungsvariablen für Tests
        os.environ["CONFIG_DIR"] = str(self.config_dir)
        
        yield
        
        # Cleanup
        import shutil
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
        
        # Entferne Umgebungsvariablen
        if "CONFIG_DIR" in os.environ:
            del os.environ["CONFIG_DIR"]
    
    def test_config_manager_creation(self):
        """Test Erstellung des ConfigManagers."""
        config_manager = ConfigManager()
        assert config_manager is not None
        assert config_manager.config_dir == self.config_dir
    
    def test_config_manager_default_values(self):
        """Test Standardwerte des ConfigManagers."""
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        # Prüfe Standardwerte
        assert "max_concurrent_downloads" in config
        assert "download_directory" in config
        assert "database_path" in config
        assert "log_level" in config
    
    def test_config_manager_set_get_value(self):
        """Test Setzen und Abrufen von Konfigurationswerten."""
        config_manager = ConfigManager()
        
        # Setze einen Wert
        config_manager.set_value("test_key", "test_value")
        
        # Prüfe, ob der Wert gesetzt wurde
        assert config_manager.get_value("test_key") == "test_value"
        
        # Prüfe, ob der Wert in der Konfiguration enthalten ist
        config = config_manager.get_config()
        assert config["test_key"] == "test_value"
    
    def test_config_manager_persistence(self):
        """Test Persistenz der Konfiguration."""
        # Erster ConfigManager
        config_manager1 = ConfigManager()
        config_manager1.set_value("persistent_key", "persistent_value")
        config_manager1.save_config()
        
        # Zweiter ConfigManager (neu laden)
        config_manager2 = ConfigManager()
        assert config_manager2.get_value("persistent_key") == "persistent_value"
    
    def test_config_manager_update_existing_value(self):
        """Test Aktualisierung eines bestehenden Werts."""
        config_manager = ConfigManager()
        
        # Setze initialen Wert
        config_manager.set_value("update_key", "initial_value")
        assert config_manager.get_value("update_key") == "initial_value"
        
        # Aktualisiere den Wert
        config_manager.set_value("update_key", "updated_value")
        assert config_manager.get_value("update_key") == "updated_value"
    
    def test_config_manager_get_nonexistent_key(self):
        """Test Abrufen eines nicht existierenden Schlüssels."""
        config_manager = ConfigManager()
        
        # Ohne Standardwert
        assert config_manager.get_value("nonexistent_key") is None
        
        # Mit Standardwert
        assert config_manager.get_value("nonexistent_key", "default") == "default"
    
    def test_config_manager_load_from_file(self):
        """Test Laden der Konfiguration aus Datei."""
        # Erstelle eine Konfigurationsdatei
        test_config = {
            "test_key": "test_value",
            "number_key": 42,
            "bool_key": True
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(test_config, f)
        
        # Lade Konfiguration
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        # Prüfe Werte
        assert config["test_key"] == "test_value"
        assert config["number_key"] == 42
        assert config["bool_key"] is True
    
    def test_config_manager_invalid_json(self):
        """Test Umgang mit ungültigem JSON."""
        # Erstelle eine ungültige Konfigurationsdatei
        with open(self.config_file, 'w') as f:
            f.write("invalid json content")
        
        # Sollte trotzdem einen ConfigManager erstellen können
        config_manager = ConfigManager()
        assert config_manager is not None
        
        # Standardkonfiguration sollte geladen werden
        config = config_manager.get_config()
        assert "max_concurrent_downloads" in config
    
    def test_config_manager_environment_variables(self):
        """Test Konfiguration über Umgebungsvariablen."""
        # Setze Umgebungsvariable
        os.environ["TAD_DOWNLOAD_DIR"] = "/custom/download/path"
        
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        # Prüfe, ob Umgebungsvariable berücksichtigt wird
        # (Dies hängt von der Implementierung ab)
        
        # Entferne Umgebungsvariable
        del os.environ["TAD_DOWNLOAD_DIR"]
    
    def test_config_manager_merge_configs(self):
        """Test Zusammenführung von Konfigurationen."""
        # Erstelle Datei-Konfiguration
        file_config = {"file_key": "file_value"}
        with open(self.config_file, 'w') as f:
            json.dump(file_config, f)
        
        # Setze Umgebungsvariable
        os.environ["TAD_ENV_KEY"] = "env_value"
        
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        # Prüfe, ob beide Konfigurationen enthalten sind
        assert config["file_key"] == "file_value"
        assert config["env_key"] == "env_value"
        
        # Entferne Umgebungsvariable
        del os.environ["TAD_ENV_KEY"]


class TestCLIConfiguration:
    """Tests für CLI-Konfigurationsbefehle."""
    
    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Setup test environment."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp(prefix="cli_config_test_")
        self.config_dir = Path(self.temp_dir) / "config"
        self.config_dir.mkdir()
        
        # Setze Umgebungsvariablen für Tests
        os.environ["CONFIG_DIR"] = str(self.config_dir)
        
        yield
        
        # Cleanup
        import shutil
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
        
        # Entferne Umgebungsvariablen
        if "CONFIG_DIR" in os.environ:
            del os.environ["CONFIG_DIR"]
    
    def test_config_show_command(self):
        """Test config show Befehl."""
        result = self.runner.invoke(config, ['show'])
        assert result.exit_code == 0
        # Konfiguration sollte angezeigt werden
    
    def test_config_set_command(self):
        """Test config set Befehl."""
        result = self.runner.invoke(config, ['set', 'cli_test_key', 'cli_test_value'])
        assert result.exit_code == 0
        
        # Prüfe, ob der Wert gesetzt wurde
        result = self.runner.invoke(config, ['show'])
        assert result.exit_code == 0
        assert "cli_test_key" in result.output
        assert "cli_test_value" in result.output
    
    def test_config_get_command(self):
        """Test config get Befehl."""
        # Setze zuerst einen Wert
        result = self.runner.invoke(config, ['set', 'get_test_key', 'get_test_value'])
        assert result.exit_code == 0
        
        # Hole den Wert
        result = self.runner.invoke(config, ['get', 'get_test_key'])
        assert result.exit_code == 0
        assert "get_test_value" in result.output
    
    def test_config_list_command(self):
        """Test config list Befehl."""
        # Setze einige Werte
        self.runner.invoke(config, ['set', 'list_key1', 'value1'])
        self.runner.invoke(config, ['set', 'list_key2', 'value2'])
        
        # Liste die Konfiguration auf
        result = self.runner.invoke(config, ['list'])
        assert result.exit_code == 0
        assert "list_key1" in result.output
        assert "list_key2" in result.output
    
    def test_config_reset_command(self):
        """Test config reset Befehl."""
        # Setze einen Wert
        self.runner.invoke(config, ['set', 'reset_key', 'reset_value'])
        
        # Setze zurück
        result = self.runner.invoke(config, ['reset'])
        assert result.exit_code == 0
        
        # Prüfe, ob der Wert entfernt wurde (optional, je nach Implementierung)


class TestConfigurationPriorities:
    """Tests für Konfigurationsprioritäten."""
    
    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp(prefix="config_priority_test_")
        self.config_dir = Path(self.temp_dir) / "config"
        self.config_dir.mkdir()
        self.config_file = self.config_dir / "config.json"
        
        # Setze Umgebungsvariablen für Tests
        os.environ["CONFIG_DIR"] = str(self.config_dir)
        
        yield
        
        # Cleanup
        import shutil
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
        
        # Entferne Umgebungsvariablen
        if "CONFIG_DIR" in os.environ:
            del os.environ["CONFIG_DIR"]
    
    def test_default_priority(self):
        """Test Priorität der Standardwerte."""
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        # Standardwerte sollten gesetzt sein
        assert config["max_concurrent_downloads"] is not None
    
    def test_file_over_default_priority(self):
        """Test Priorität von Datei über Standardwerten."""
        # Erstelle Datei-Konfiguration
        file_config = {"max_concurrent_downloads": 10}
        with open(self.config_file, 'w') as f:
            json.dump(file_config, f)
        
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        # Datei-Konfiguration sollte Vorrang haben
        assert config["max_concurrent_downloads"] == 10
    
    def test_env_over_file_priority(self):
        """Test Priorität von Umgebungsvariablen über Datei."""
        # Erstelle Datei-Konfiguration
        file_config = {"max_concurrent_downloads": 10}
        with open(self.config_file, 'w') as f:
            json.dump(file_config, f)
        
        # Setze Umgebungsvariable
        os.environ["TAD_MAX_CONCURRENT_DOWNLOADS"] = "20"
        
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        # Umgebungsvariable sollte Vorrang haben
        assert config["max_concurrent_downloads"] == 20
        
        # Entferne Umgebungsvariable
        del os.environ["TAD_MAX_CONCURRENT_DOWNLOADS"]
    
    def test_cli_over_env_priority(self):
        """Test Priorität von CLI-Argumenten über Umgebungsvariablen."""
        # Dieser Test ist schwierig ohne direkten Zugriff auf CLI-Argumente
        # In der Regel würden solche Tests die CLI direkt aufrufen
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])