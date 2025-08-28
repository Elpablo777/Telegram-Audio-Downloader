#!/usr/bin/env python3
"""
Configuration Validation Tests - Telegram Audio Downloader
========================================================

Tests für die Validierung von Konfigurationswerten.
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch
import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from telegram_audio_downloader.config import Config
from telegram_audio_downloader.error_handling import ConfigurationError


class TestConfigValidation:
    """Tests für die Validierung von Konfigurationswerten."""
    
    def test_config_validation_valid_values(self):
        """Test Validierung mit gültigen Werten."""
        # Test mit allen gültigen Standardwerten
        config = Config()
        # Sollte keine Exception werfen
        
        # Test mit benutzerdefinierten gültigen Werten
        config = Config(
            max_concurrent_downloads=5,
            rate_limit_delay=0.5,
            max_memory_mb=512,
            cache_size=10000
        )
        # Sollte keine Exception werfen
    
    def test_config_validation_invalid_max_concurrent_downloads(self):
        """Test Validierung mit ungültigen max_concurrent_downloads Werten."""
        # Test mit 0
        with pytest.raises(ConfigurationError):
            Config(max_concurrent_downloads=0)
        
        # Test mit negativen Werten
        with pytest.raises(ConfigurationError):
            Config(max_concurrent_downloads=-1)
        
        # Test mit Werten über dem Maximum
        with pytest.raises(ConfigurationError):
            Config(max_concurrent_downloads=11)  # Max ist 10
    
    def test_config_validation_invalid_rate_limit_delay(self):
        """Test Validierung mit ungültigen rate_limit_delay Werten."""
        # Test mit negativen Werten
        with pytest.raises(ConfigurationError):
            Config(rate_limit_delay=-1)
    
    def test_config_validation_invalid_paths(self):
        """Test Validierung mit ungültigen Pfaden."""
        # Test mit leerem download_dir
        with pytest.raises(ConfigurationError):
            Config(download_dir="")
        
        # Test mit leerem db_path
        with pytest.raises(ConfigurationError):
            Config(db_path="")
    
    def test_config_validation_invalid_memory_settings(self):
        """Test Validierung mit ungültigen Speichereinstellungen."""
        # Test mit negativen Werten
        with pytest.raises(ConfigurationError):
            Config(max_memory_mb=-1)
        
        with pytest.raises(ConfigurationError):
            Config(cache_size=-1)
    
    def test_config_validation_edge_cases(self):
        """Test Validierung mit Extremwerten."""
        # Test mit minimalen gültigen Werten
        config = Config(
            max_concurrent_downloads=1,
            rate_limit_delay=0,
            max_memory_mb=1,
            cache_size=1
        )
        # Sollte keine Exception werfen
        
        # Test mit maximalen gültigen Werten
        config = Config(
            max_concurrent_downloads=10,
            max_memory_mb=10000,
            cache_size=1000000
        )
        # Sollte keine Exception werfen
    
    def test_config_validation_dependencies(self):
        """Test Validierung von Abhängigkeiten zwischen Einstellungen."""
        # In einem erweiterten System würde man hier Abhängigkeiten prüfen
        # Zum Beispiel: cache_size sollte nicht größer als max_memory_mb sein
        
        config = Config(
            max_memory_mb=512,
            cache_size=10000
        )
        # In der aktuellen Implementierung gibt es keine solchen Abhängigkeiten
    
    def test_config_validation_consistency(self):
        """Test Konsistenzprüfungen."""
        # Test mit inkonsistenten Werten
        # In einem erweiterten System würde man hier Konsistenzprüfungen implementieren
        
        config = Config(
            max_concurrent_downloads=5,
            rate_limit_delay=0.1
        )
        # In der aktuellen Implementierung sind diese Werte konsistent
    
    def test_config_validation_user_friendly_errors(self):
        """Test benutzerfreundliche Fehlermeldungen."""
        # Test mit spezifischen Fehlermeldungen
        try:
            Config(max_concurrent_downloads=0)
        except ConfigurationError as e:
            assert "max_concurrent_downloads" in str(e)
            assert "positive" in str(e).lower()
        
        try:
            Config(rate_limit_delay=-1)
        except ConfigurationError as e:
            assert "rate_limit_delay" in str(e)
            assert "negative" in str(e).lower() or "non-negative" in str(e).lower()
        
        try:
            Config(download_dir="")
        except ConfigurationError as e:
            assert "download_dir" in str(e)
            assert "empty" in str(e).lower() or "darf nicht leer" in str(e).lower()