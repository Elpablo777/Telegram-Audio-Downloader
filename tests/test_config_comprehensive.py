#!/usr/bin/env python3
"""
Comprehensive Configuration Tests - Telegram Audio Downloader
============================================================

Umfassende Tests für die Konfigurationsverwaltung.
"""

import os
import sys
import json
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch
import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from telegram_audio_downloader.config import Config
from telegram_audio_downloader.error_handling import ConfigurationError


class TestConfigComprehensive:
    """Umfassende Tests für die Konfigurationsklasse."""
    
    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp(prefix="config_test_")
        self.config_dir = Path(self.temp_dir) / "config"
        self.config_dir.mkdir()
        
        yield
        
        # Cleanup
        import shutil
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def test_config_initialization_with_defaults(self):
        """Test Konfigurationsinitialisierung mit Standardwerten."""
        config = Config()
        
        # Prüfe Standardwerte
        assert config.session_name == "telegram_audio_downloader"
        assert config.download_dir == "downloads"
        assert config.max_concurrent_downloads == 3
        assert config.rate_limit_delay == 0.1
        assert config.db_path == "data/downloads.db"
        assert config.log_dir == "logs"
        assert config.log_level == "INFO"
        assert config.max_memory_mb == 1024
        assert config.cache_size == 50000
        assert config.api_id is None
        assert config.api_hash is None
        assert config.encryption_key is None
    
    def test_config_initialization_with_custom_values(self):
        """Test Konfigurationsinitialisierung mit benutzerdefinierten Werten."""
        config = Config(
            api_id="123456",
            api_hash="test_hash",
            session_name="test_session",
            download_dir="/tmp/test_downloads",
            max_concurrent_downloads=5,
            rate_limit_delay=0.5,
            db_path="/tmp/test.db",
            log_dir="/tmp/logs",
            log_level="DEBUG",
            max_memory_mb=512,
            cache_size=10000,
            encryption_key=os.getenv("TEST_ENCRYPTION_KEY", "fake_test_key_for_testing")
        )
        
        # Prüfe benutzerdefinierte Werte
        assert config.api_id == "123456"
        assert config.api_hash == "test_hash"
        assert config.session_name == "test_session"
        assert config.download_dir == "/tmp/test_downloads"
        assert config.max_concurrent_downloads == 5
        assert config.rate_limit_delay == 0.5
        assert config.db_path == "/tmp/test.db"
        assert config.log_dir == "/tmp/logs"
        assert config.log_level == "DEBUG"
        assert config.max_memory_mb == 512
        assert config.cache_size == 10000
        assert config.encryption_key == "test_key"
    
    def test_config_from_env(self):
        """Test Konfiguration aus Umgebungsvariablen."""
        # Setze Umgebungsvariablen
        env_vars = {
            "API_ID": "789012",
            "API_HASH": "env_hash",
            "SESSION_NAME": "env_session",
            "DOWNLOAD_DIR": "/tmp/env_downloads",
            "MAX_CONCURRENT_DOWNLOADS": "7",
            "RATE_LIMIT_DELAY": "0.3",
            "DB_PATH": "/tmp/env.db",
            "LOG_DIR": "/tmp/env_logs",
            "LOG_LEVEL": "WARNING",
            "MAX_MEMORY_MB": "2048",
            "CACHE_SIZE": "20000",
            "ENCRYPTION_KEY": "env_key"
        }
        
        with patch.dict(os.environ, env_vars):
            config = Config.from_env()
            
            # Prüfe Werte aus Umgebungsvariablen
            assert config.api_id == "789012"
            assert config.api_hash == "env_hash"
            assert config.session_name == "env_session"
            assert config.download_dir == "/tmp/env_downloads"
            assert config.max_concurrent_downloads == 7
            assert config.rate_limit_delay == 0.3
            assert config.db_path == "/tmp/env.db"
            assert config.log_dir == "/tmp/env_logs"
            assert config.log_level == "WARNING"
            assert config.max_memory_mb == 2048
            assert config.cache_size == 20000
            assert config.encryption_key == "env_key"
    
    def test_config_from_json_file(self):
        """Test Konfiguration aus JSON-Datei."""
        # Erstelle JSON-Konfigurationsdatei
        config_data = {
            "api_id": "345678",
            "api_hash": "json_hash",
            "session_name": "json_session",
            "download_dir": "/tmp/json_downloads",
            "max_concurrent_downloads": 4,
            "rate_limit_delay": 0.2,
            "db_path": "/tmp/json.db",
            "log_dir": "/tmp/json_logs",
            "log_level": "ERROR",
            "max_memory_mb": 1024,
            "cache_size": 15000,
            "encryption_key": "json_key"
        }
        
        config_file = self.config_dir / "config.json"
        with open(config_file, 'w') as f:
            json.dump(config_data, f)
        
        # Lade Konfiguration aus Datei
        config = Config.from_file(config_file)
        
        # Prüfe Werte aus JSON-Datei
        assert config.api_id == "345678"
        assert config.api_hash == "json_hash"
        assert config.session_name == "json_session"
        assert config.download_dir == "/tmp/json_downloads"
        assert config.max_concurrent_downloads == 4
        assert config.rate_limit_delay == 0.2
        assert config.db_path == "/tmp/json.db"
        assert config.log_dir == "/tmp/json_logs"
        assert config.log_level == "ERROR"
        assert config.max_memory_mb == 1024
        assert config.cache_size == 15000
        assert config.encryption_key == "json_key"
    
    def test_config_from_yaml_file(self):
        """Test Konfiguration aus YAML-Datei."""
        # Erstelle YAML-Konfigurationsdatei
        config_data = {
            "api_id": "901234",
            "api_hash": "yaml_hash",
            "session_name": "yaml_session",
            "download_dir": "/tmp/yaml_downloads",
            "max_concurrent_downloads": 6,
            "rate_limit_delay": 0.4,
            "db_path": "/tmp/yaml.db",
            "log_dir": "/tmp/yaml_logs",
            "log_level": "CRITICAL",
            "max_memory_mb": 768,
            "cache_size": 25000,
            "encryption_key": "yaml_key"
        }
        
        config_file = self.config_dir / "config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        # Lade Konfiguration aus Datei
        config = Config.from_file(config_file)
        
        # Prüfe Werte aus YAML-Datei
        assert config.api_id == "901234"
        assert config.api_hash == "yaml_hash"
        assert config.session_name == "yaml_session"
        assert config.download_dir == "/tmp/yaml_downloads"
        assert config.max_concurrent_downloads == 6
        assert config.rate_limit_delay == 0.4
        assert config.db_path == "/tmp/yaml.db"
        assert config.log_dir == "/tmp/yaml_logs"
        assert config.log_level == "CRITICAL"
        assert config.max_memory_mb == 768
        assert config.cache_size == 25000
        assert config.encryption_key == "yaml_key"
    
    def test_config_from_ini_file(self):
        """Test Konfiguration aus INI-Datei."""
        # Erstelle INI-Konfigurationsdatei
        config_content = """
[DEFAULT]
api_id = 567890
api_hash = ini_hash
session_name = ini_session
download_dir = /tmp/ini_downloads
max_concurrent_downloads = 2
rate_limit_delay = 0.1
db_path = /tmp/ini.db
log_dir = /tmp/ini_logs
log_level = INFO
max_memory_mb = 256
cache_size = 5000
encryption_key = ini_key
"""
        
        config_file = self.config_dir / "config.ini"
        with open(config_file, 'w') as f:
            f.write(config_content)
        
        # Lade Konfiguration aus Datei
        config = Config.from_file(config_file)
        
        # Prüfe Werte aus INI-Datei
        assert config.api_id == "567890"
        assert config.api_hash == "ini_hash"
        assert config.session_name == "ini_session"
        assert config.download_dir == "/tmp/ini_downloads"
        assert config.max_concurrent_downloads == 2
        assert config.rate_limit_delay == 0.1
        assert config.db_path == "/tmp/ini.db"
        assert config.log_dir == "/tmp/ini_logs"
        assert config.log_level == "INFO"
        assert config.max_memory_mb == 256
        assert config.cache_size == 5000
        assert config.encryption_key == "ini_key"
    
    def test_config_priority_order(self):
        """Test Prioritätsreihenfolge der Konfigurationsquellen."""
        # 4. Standardwerte
        default_config = Config()
        
        # 3. Konfigurationsdatei
        config_data = {
            "api_id": "111111",
            "api_hash": "file_hash",
            "session_name": "file_session",
            "max_concurrent_downloads": 4
        }
        
        config_file = self.config_dir / "config.json"
        with open(config_file, 'w') as f:
            json.dump(config_data, f)
        
        # 2. Umgebungsvariablen
        env_vars = {
            "API_ID": "222222",
            "API_HASH": "env_hash",
            "max_concurrent_downloads": "6"
        }
        
        # 1. Befehlszeilenargumente
        cli_args = {
            "api_id": "333333",
            "max_concurrent_downloads": 8
        }
        
        with patch.dict(os.environ, env_vars):
            config = Config.load(config_path=config_file, cli_args=cli_args)
            
            # Prüfe Prioritätsreihenfolge (CLI > ENV > FILE > DEFAULT)
            assert config.api_id == "333333"  # CLI
            assert config.api_hash == "env_hash"  # ENV
            assert config.session_name == "file_session"  # FILE
            assert config.max_concurrent_downloads == 8  # CLI
            assert config.rate_limit_delay == 0.1  # DEFAULT
    
    def test_config_validation(self):
        """Test Konfigurationsvalidierung."""
        # Test gültige Konfiguration
        valid_config = Config(max_concurrent_downloads=5, rate_limit_delay=0.5)
        # Sollte keine Exception werfen
        
        # Test ungültige max_concurrent_downloads
        with pytest.raises(ConfigurationError):
            Config(max_concurrent_downloads=0)
        
        with pytest.raises(ConfigurationError):
            Config(max_concurrent_downloads=-1)
        
        with pytest.raises(ConfigurationError):
            Config(max_concurrent_downloads=11)  # Max ist 10
        
        # Test ungültige rate_limit_delay
        with pytest.raises(ConfigurationError):
            Config(rate_limit_delay=-1)
        
        # Test ungültige Pfade
        with pytest.raises(ConfigurationError):
            Config(download_dir="")
        
        with pytest.raises(ConfigurationError):
            Config(db_path="")
    
    def test_config_required_fields_validation(self):
        """Test Validierung erforderlicher Felder."""
        config = Config()
        
        # Ohne API-ID und API-Hash sollte die Validierung fehlschlagen
        with pytest.raises(ConfigurationError):
            config.validate_required_fields()
        
        # Mit API-ID und API-Hash sollte die Validierung erfolgreich sein
        config.api_id = "123456"
        config.api_hash = "test_hash"
        
        # Sollte keine Exception werfen
        config.validate_required_fields()
    
    def test_config_to_dict(self):
        """Test Konvertierung der Konfiguration in ein Dictionary."""
        config = Config(
            api_id="123456",
            api_hash="test_hash",
            session_name="test_session",
            download_dir="/tmp/test_downloads",
            max_concurrent_downloads=5
        )
        
        config_dict = config.to_dict()
        
        # Prüfe, dass alle Felder im Dictionary enthalten sind
        assert config_dict["api_id"] == "123456"
        assert config_dict["api_hash"] == "test_hash"
        assert config_dict["session_name"] == "test_session"
        assert config_dict["download_dir"] == "/tmp/test_downloads"
        assert config_dict["max_concurrent_downloads"] == 5
    
    def test_config_save_to_file(self):
        """Test Speichern der Konfiguration in Datei."""
        config = Config(
            api_id="123456",
            api_hash="test_hash",
            session_name="test_session",
            download_dir="/tmp/test_downloads",
            max_concurrent_downloads=5
        )
        
        # Test JSON-Speicherung
        json_file = self.config_dir / "test_config.json"
        config.save_to_file(json_file, format='json')
        assert json_file.exists()
        
        # Test YAML-Speicherung
        yaml_file = self.config_dir / "test_config.yaml"
        config.save_to_file(yaml_file, format='yaml')
        assert yaml_file.exists()
        
        # Test INI-Speicherung
        ini_file = self.config_dir / "test_config.ini"
        config.save_to_file(ini_file, format='ini')
        assert ini_file.exists()
        
        # Test ungültiges Format
        with pytest.raises(ConfigurationError):
            config.save_to_file("test.txt", format='txt')
    
    def test_config_merge_configs(self):
        """Test Zusammenführung von Konfigurationen."""
        base_config = Config(
            api_id="base_id",
            api_hash="base_hash",
            session_name="base_session",
            download_dir="/tmp/base"
        )
        
        override_config = Config(
            api_id="override_id",
            session_name="override_session"
            # download_dir ist nicht gesetzt, sollte vom base_config übernommen werden
        )
        
        merged_config = Config._merge_configs(base_config, override_config)
        
        # Prüfe übernommene Werte
        assert merged_config.api_id == "override_id"  # Überschrieben
        assert merged_config.api_hash == "base_hash"  # Beibehalten
        assert merged_config.session_name == "override_session"  # Überschrieben
        assert merged_config.download_dir == "/tmp/base"  # Beibehalten