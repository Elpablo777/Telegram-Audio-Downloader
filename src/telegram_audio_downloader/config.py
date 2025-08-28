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
        # Telegram-Einstellungen - Werte werden aus Umgebungsvariablen geladen
        self.config['telegram'] = {
            'api_id': os.getenv('API_ID', ''),
            'api_hash': os.getenv('API_HASH', ''),
            'phone_number': os.getenv('PHONE_NUMBER', '')
        }
        
        # Proxy-Einstellungen
        self.config['proxy'] = {
            'type': '',  # socks5, http, etc.
            'host': '',
            'port': '',
            'username': '',
            'password': ''
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
        
        # Performance-Einstellungen
        self.config['performance'] = {
            'chunk_size': '8192',
            'timeout': '30',
            'connection_pool_size': '10'
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
    
    @property
    def proxy_type(self) -> str:
        """Typ des Proxys (socks5, http, etc.)."""
        return self.config.get('proxy', 'type', fallback='')
    
    @property
    def proxy_host(self) -> str:
        """Host des Proxys."""
        return self.config.get('proxy', 'host', fallback='')
    
    @property
    def proxy_port(self) -> int:
        """Port des Proxys."""
        return self.config.getint('proxy', 'port', fallback=0)
    
    @property
    def proxy_username(self) -> str:
        """Benutzername für den Proxy."""
        return self.config.get('proxy', 'username', fallback='')
    
    @property
    def proxy_password(self) -> str:
        """Passwort für den Proxy."""
        return self.config.get('proxy', 'password', fallback='')
    
    @property
    def chunk_size(self) -> int:
        """Größe der Download-Chunks in Bytes."""
        return self.config.getint('performance', 'chunk_size', fallback=8192)
    
    @property
    def timeout(self) -> int:
        """Timeout für Netzwerkoperationen in Sekunden."""
        return self.config.getint('performance', 'timeout', fallback=30)
    
    @property
    def connection_pool_size(self) -> int:
        """Größe des Verbindungspools."""
        return self.config.getint('performance', 'connection_pool_size', fallback=10)
    
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
    
    def export_to_yaml(self, output_path: str) -> None:
        """
        Exportiert die Konfiguration in eine YAML-Datei.
        
        Args:
            output_path: Pfad zur Ausgabedatei
        """
        # Konvertiere die ConfigParser-Daten in ein Dictionary
        config_dict = {}
        for section_name in self.config.sections():
            config_dict[section_name] = {}
            for key, value in self.config.items(section_name):
                # Entferne sensible Daten aus dem Export
                if key not in ['api_id', 'api_hash', 'phone_number', 'password']:
                    config_dict[section_name][key] = value
        
        # Schreibe das Dictionary in eine YAML-Datei
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True, indent=2)