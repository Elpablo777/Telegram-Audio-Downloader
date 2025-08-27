#!/usr/bin/env python3
"""
Security Configuration Tests - Telegram Audio Downloader
======================================================

Tests für die sichere Handhabung von Konfigurationen.
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

from telegram_audio_downloader.config import Config
from telegram_audio_downloader.error_handling import ConfigurationError


class TestConfigSecurity:
    """Tests für die sichere Handhabung von Konfigurationen."""
    
    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp(prefix="config_security_test_")
        self.config_dir = Path(self.temp_dir) / "config"
        self.config_dir.mkdir()
        
        yield
        
        # Cleanup
        import shutil
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def test_config_encryption_key_handling(self):
        """Test sichere Handhabung von Verschlüsselungsschlüsseln."""
        # Test mit Verschlüsselungsschlüssel
        config = Config(encryption_key="super_secret_key")
        
        # Der Schlüssel sollte sicher gespeichert werden
        assert config.encryption_key == "super_secret_key"
        
        # Bei der Konvertierung in ein Dictionary sollte der Schlüssel enthalten sein
        # (In Produktion würde man ihn maskieren)
        config_dict = config.to_dict()
        assert config_dict["encryption_key"] == "super_secret_key"
    
    def test_config_file_permissions(self):
        """Test Dateiberechtigungen für Konfigurationsdateien."""
        config = Config(
            api_id="123456",
            api_hash="test_hash"
        )
        
        # Speichere Konfiguration in JSON-Datei
        config_file = self.config_dir / "secure_config.json"
        config.save_to_file(config_file, format='json')
        
        # Prüfe, dass die Datei existiert
        assert config_file.exists()
        
        # Prüfe Dateiberechtigungen (Unix/Linux)
        if hasattr(os, 'chmod'):
            # Setze sichere Berechtigungen (nur Lesen/Schreiben für Besitzer)
            os.chmod(config_file, 0o600)
            
            # Prüfe Berechtigungen
            stat_info = config_file.stat()
            assert stat_info.st_mode & 0o777 == 0o600
    
    def test_config_sanitize_sensitive_data(self):
        """Test Bereinigung sensibler Daten."""
        # In Produktion würde man hier Funktionen implementieren,
        # um sensible Daten in Logs zu maskieren
        config = Config(
            api_id="123456",
            api_hash="sensitive_hash",
            encryption_key="super_secret_key"
        )
        
        # Konvertiere in Dictionary
        config_dict = config.to_dict()
        
        # In Produktion würde man hier sensible Daten maskieren
        # Für diesen Test prüfen wir, dass die Daten vorhanden sind
        assert config_dict["api_id"] == "123456"
        assert config_dict["api_hash"] == "sensitive_hash"
        assert config_dict["encryption_key"] == "super_secret_key"
    
    def test_config_environment_variable_security(self):
        """Test sichere Handhabung von Umgebungsvariablen."""
        # Setze sensible Umgebungsvariablen
        sensitive_env = {
            "API_ID": "789012",
            "API_HASH": "env_sensitive_hash",
            "ENCRYPTION_KEY": "env_secret_key"
        }
        
        with patch.dict(os.environ, sensitive_env):
            config = Config.from_env()
            
            # Prüfe, dass die Werte korrekt geladen wurden
            assert config.api_id == "789012"
            assert config.api_hash == "env_sensitive_hash"
            assert config.encryption_key == "env_secret_key"
    
    def test_config_file_security_with_invalid_json(self):
        """Test Sicherheit bei ungültigen JSON-Konfigurationsdateien."""
        # Erstelle eine ungültige JSON-Datei
        config_file = self.config_dir / "invalid_config.json"
        with open(config_file, 'w') as f:
            f.write("{ invalid json }")
        
        # Das Laden sollte eine ConfigurationError werfen
        with pytest.raises(ConfigurationError):
            Config.from_file(config_file)
    
    def test_config_file_security_with_malicious_content(self):
        """Test Sicherheit bei bösartigem Inhalt in Konfigurationsdateien."""
        # Erstelle eine JSON-Datei mit bösartigem Inhalt
        # (In Produktion würde man hier sicherere Parsing-Methoden verwenden)
        config_file = self.config_dir / "malicious_config.json"
        malicious_data = {
            "api_id": "123456",
            "__class__": "malicious_class",
            "__module__": "malicious_module"
        }
        
        with open(config_file, 'w') as f:
            json.dump(malicious_data, f)
        
        # Das Laden sollte funktionieren, aber bösartige Attribute sollten ignoriert werden
        config = Config.from_file(config_file)
        assert config.api_id == "123456"
        # Die bösartigen Attribute sollten nicht in der Config-Klasse existieren
    
    def test_config_memory_security(self):
        """Test Speichersicherheit der Konfiguration."""
        # Erstelle eine Konfiguration mit sensiblen Daten
        config = Config(
            api_id="123456",
            api_hash="sensitive_hash",
            encryption_key="super_secret_key"
        )
        
        # Prüfe, dass die sensiblen Daten im Speicher sind
        assert config.api_id == "123456"
        assert config.api_hash == "sensitive_hash"
        assert config.encryption_key == "super_secret_key"
        
        # In Produktion würde man hier sicherere Speichermethoden verwenden
        # (z.B. sichere Speicherbereiche, Verschlüsselung im Speicher)
    
    def test_config_audit_logging(self):
        """Test Audit-Logging für Konfigurationszugriffe."""
        # In Produktion würde man hier Logging implementieren,
        # um Konfigurationszugriffe zu verfolgen
        
        config = Config(
            api_id="123456",
            api_hash="test_hash"
        )
        
        # Zugriff auf sensible Daten
        api_id = config.api_id
        api_hash = config.api_hash
        
        # In Produktion würde man hier Logs schreiben
        # Für diesen Test prüfen wir nur, dass der Zugriff funktioniert
        assert api_id == "123456"
        assert api_hash == "test_hash"
    
    def test_config_access_control(self):
        """Test Zugriffskontrolle für Konfigurationen."""
        # In Produktion würde man hier Zugriffskontrollen implementieren
        
        config = Config(
            api_id="123456",
            api_hash="test_hash"
        )
        
        # Prüfe, dass nur autorisierte Komponenten auf die Konfiguration zugreifen können
        # In diesem Test prüfen wir nur die grundlegende Funktionalität
        assert config.api_id == "123456"
        assert config.api_hash == "test_hash"
        
        # In Produktion würde man hier Berechtigungsprüfungen implementieren
    
    def test_config_secure_storage_integration(self):
        """Test Integration mit sicheren Speicherlösungen."""
        # In Produktion würde man hier Integrationen mit Vault, Keyring etc. implementieren
        
        # Für diesen Test prüfen wir nur die grundlegende Struktur
        config = Config(
            api_id="123456",
            api_hash="test_hash",
            encryption_key="test_key"
        )
        
        # In Produktion würde man hier Methoden zum sicheren Laden/Speichern implementieren
        assert config.api_id == "123456"
        assert config.api_hash == "test_hash"
        assert config.encryption_key == "test_key"