"""
Zentrale Konfigurationsverwaltung für den Telegram Audio Downloader.
"""

import os
import json
import yaml
import configparser
from pathlib import Path
from typing import Any, Dict, Optional, Union
from dataclasses import dataclass, field

from .error_handling import ConfigurationError, handle_error


@dataclass
class Config:
    """Konfigurationsklasse für den Telegram Audio Downloader."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialisiert die Konfiguration.
        
        Args:
            config_path: Optionaler Pfad zur Konfigurationsdatei
        """
        self.config = configparser.ConfigParser()
        
        # Lade die Konfiguration
        if config_path and os.path.exists(config_path):
            self.config.read(config_path)
        else:
            # Lade die Standardkonfiguration
            self._load_default_config()
    
    def _load_default_config(self) -> None:
        """Lädt die Standardkonfiguration."""
        # Telegram-Einstellungen
        self.config['telegram'] = {
            'api_id': '',
            'api_hash': '',
            'phone_number': ''
        }
        
        # Download-Einstellungen
        self.config['download'] = {
            'download_dir': 'downloads',
            'max_concurrent_downloads': '5',
            'max_file_size': '100000000',
            'allowed_extensions': '.mp3,.m4a,.flac,.ogg,.wav',
            # Neue Einstellungen für die fortgeschrittene Download-Wiederaufnahme
            'max_retries': '3',
            'retry_delay': '5',
            'checksum_algorithm': 'sha256'
        }
    
    def get_api_id(self) -> str:
        """Gibt die API-ID zurück."""
        return self.config.get('telegram', 'api_id', fallback='')
    
    def get_api_hash(self) -> str:
        """Gibt die API-Hash zurück."""
        return self.config.get('telegram', 'api_hash', fallback='')
    
    def get_phone_number(self) -> str:
        """Gibt die Telefonnummer zurück."""
        return self.config.get('telegram', 'phone_number', fallback='')
    
    @property
    def download_dir(self) -> str:
        """Verzeichnis für die Downloads."""
        return self.config.get('download', 'download_dir', fallback='downloads')
    
    @property
    def max_concurrent_downloads(self) -> int:
        """Maximale Anzahl der gleichzeitigen Downloads."""
        return self.config.getint('download', 'max_concurrent_downloads', fallback=5)
    
    @property
    def max_file_size(self) -> int:
        """Maximale Größe der zu ladenden Dateien in Bytes."""
        return self.config.getint('download', 'max_file_size', fallback=100000000)
    
    @property
    def allowed_extensions(self) -> str:
        """Erlaubte Dateierweiterungen für Downloads."""
        return self.config.get('download', 'allowed_extensions', fallback='.mp3,.m4a,.flac,.ogg,.wav')
    
    @property
    def max_retries(self) -> int:
        """Maximale Anzahl von Wiederholungsversuchen."""
        return self.config.getint('download', 'max_retries', fallback=3)
    
    @property
    def retry_delay(self) -> int:
        """Wartezeit zwischen Wiederholungsversuchen in Sekunden."""
        return self.config.getint('download', 'retry_delay', fallback=5)
    
    @property
    def checksum_algorithm(self) -> str:
        """Algorithmus für die Prüfsummenberechnung."""
        return self.config.get('download', 'checksum_algorithm', fallback='sha256')
    
    def validate_required_fields(self) -> None:
        """
        Validiert, dass alle erforderlichen Felder gesetzt sind.
        
        Raises:
            ConfigurationError: Wenn erforderliche Felder fehlen
        """
        required_fields = ['api_id', 'api_hash', 'phone_number']
        missing_fields = [field for field in required_fields if not self.config.get('telegram', field)]
        
        if missing_fields:
            raise ConfigurationError(
                f"Fehlende erforderliche Configurationsfelder: {', '.join(missing_fields)}. "
                "Bitte setzen Sie diese über Umgebungsvariablen oder Konfigurationsdatei."
            )
