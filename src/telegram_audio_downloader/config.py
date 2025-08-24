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
    """
    Zentrale Konfigurationsklasse für den Telegram Audio Downloader.
    
    Diese Klasse verwaltet alle Konfigurationseinstellungen mit folgender Priorität:
    1. Befehlszeilenargumente
    2. Umgebungsvariablen
    3. Konfigurationsdatei
    4. Standardwerte
    """
    
    # Telegram API Einstellungen
    api_id: Optional[str] = None
    api_hash: Optional[str] = None
    session_name: str = "telegram_audio_downloader"
    
    # Download Einstellungen
    download_dir: str = "downloads"
    max_concurrent_downloads: int = 3
    rate_limit_delay: float = 0.1
    
    # Datenbank Einstellungen
    db_path: str = "data/downloads.db"
    
    # Logging Einstellungen
    log_dir: str = "logs"
    log_level: str = "INFO"
    
    # Performance Einstellungen
    max_memory_mb: int = 1024
    cache_size: int = 50000
    
    # Sicherheitseinstellungen
    encryption_key: Optional[str] = None
    
    def __post_init__(self):
        """Validiert die Konfiguration nach der Initialisierung."""
        self._validate_config()
    
    def _validate_config(self) -> None:
        """Validiert die Konfigurationswerte."""
        # Validiere max_concurrent_downloads
        if not isinstance(self.max_concurrent_downloads, int) or self.max_concurrent_downloads <= 0:
            raise ConfigurationError("max_concurrent_downloads muss eine positive ganze Zahl sein")
        
        if self.max_concurrent_downloads > 10:
            raise ConfigurationError("max_concurrent_downloads darf maximal 10 sein")
        
        # Validiere rate_limit_delay
        if not isinstance(self.rate_limit_delay, (int, float)) or self.rate_limit_delay < 0:
            raise ConfigurationError("rate_limit_delay muss eine nicht-negative Zahl sein")
        
        # Validiere Pfade
        if not isinstance(self.download_dir, str) or not self.download_dir:
            raise ConfigurationError("download_dir darf nicht leer sein")
        
        if not isinstance(self.db_path, str) or not self.db_path:
            raise ConfigurationError("db_path darf nicht leer sein")
    
    @classmethod
    def from_env(cls) -> 'Config':
        """
        Erstellt eine Konfiguration aus Umgebungsvariablen.
        
        Returns:
            Config: Neue Konfigurationsinstanz
        """
        return cls(
            api_id=os.getenv("API_ID"),
            api_hash=os.getenv("API_HASH"),
            session_name=os.getenv("SESSION_NAME", "telegram_audio_downloader"),
            download_dir=os.getenv("DOWNLOAD_DIR", "downloads"),
            max_concurrent_downloads=int(os.getenv("MAX_CONCURRENT_DOWNLOADS", 3)),
            rate_limit_delay=float(os.getenv("RATE_LIMIT_DELAY", 0.1)),
            db_path=os.getenv("DB_PATH", "data/downloads.db"),
            log_dir=os.getenv("LOG_DIR", "logs"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            max_memory_mb=int(os.getenv("MAX_MEMORY_MB", 1024)),
            cache_size=int(os.getenv("CACHE_SIZE", 50000)),
            encryption_key=os.getenv("ENCRYPTION_KEY")
        )
    
    @classmethod
    def from_file(cls, config_path: Union[str, Path]) -> 'Config':
        """
        Erstellt eine Konfiguration aus einer Datei.
        
        Args:
            config_path: Pfad zur Konfigurationsdatei
            
        Returns:
            Config: Neue Konfigurationsinstanz
        """
        config_path = Path(config_path)
        
        if not config_path.exists():
            raise ConfigurationError(f"Konfigurationsdatei nicht gefunden: {config_path}")
        
        if config_path.suffix.lower() == '.json':
            return cls._from_json(config_path)
        elif config_path.suffix.lower() in ['.yml', '.yaml']:
            return cls._from_yaml(config_path)
        elif config_path.suffix.lower() == '.ini':
            return cls._from_ini(config_path)
        elif config_path.suffix.lower() == '.toml':
            return cls._from_toml(config_path)
        else:
            raise ConfigurationError(f"Nicht unterstütztes Konfigurationsformat: {config_path.suffix}")
    
    @classmethod
    def _from_json(cls, config_path: Path) -> 'Config':
        """Lädt Konfiguration aus JSON-Datei."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return cls(**data)
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Ungültiges JSON in Konfigurationsdatei: {e}")
        except Exception as e:
            raise ConfigurationError(f"Fehler beim Lesen der JSON-Konfiguration: {e}")
    
    @classmethod
    def _from_yaml(cls, config_path: Path) -> 'Config':
        """Lädt Konfiguration aus YAML-Datei."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            return cls(**data)
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Ungültiges YAML in Konfigurationsdatei: {e}")
        except Exception as e:
            raise ConfigurationError(f"Fehler beim Lesen der YAML-Konfiguration: {e}")
    
    @classmethod
    def _from_ini(cls, config_path: Path) -> 'Config':
        """Lädt Konfiguration aus INI-Datei."""
        try:
            config = configparser.ConfigParser()
            config.read(config_path, encoding='utf-8')
            
            # Konvertiere INI-Daten in flaches Dictionary
            data = {}
            for section in config.sections():
                for key, value in config.items(section):
                    # Konvertiere Werte in passende Typen
                    if key in ['max_concurrent_downloads', 'max_memory_mb', 'cache_size']:
                        data[key] = int(value)
                    elif key in ['rate_limit_delay']:
                        data[key] = float(value)
                    else:
                        data[key] = value
            
            return cls(**data)
        except Exception as e:
            raise ConfigurationError(f"Fehler beim Lesen der INI-Konfiguration: {e}")
    
    @classmethod
    def _from_toml(cls, config_path: Path) -> 'Config':
        """Lädt Konfiguration aus TOML-Datei."""
        try:
            import tomli  # Python < 3.11
        except ImportError:
            try:
                import tomllib as tomli  # Python >= 3.11
            except ImportError:
                raise ConfigurationError("TOML-Unterstützung nicht verfügbar. Installiere tomli oder verwende Python >= 3.11")
        
        try:
            with open(config_path, 'rb') as f:
                data = tomli.load(f)
            
            # Flache das verschachtelte Dictionary
            flat_data = {}
            for section, values in data.items():
                if isinstance(values, dict):
                    flat_data.update(values)
                else:
                    flat_data[section] = values
            
            return cls(**flat_data)
        except Exception as e:
            raise ConfigurationError(f"Fehler beim Lesen der TOML-Konfiguration: {e}")
    
    @classmethod
    def load(cls, 
             config_path: Optional[Union[str, Path]] = None,
             cli_args: Optional[Dict[str, Any]] = None) -> 'Config':
        """
        Lädt die Konfiguration mit Priorisierung:
        1. Befehlszeilenargumente
        2. Umgebungsvariablen
        3. Konfigurationsdatei
        4. Standardwerte
        
        Args:
            config_path: Optionaler Pfad zur Konfigurationsdatei
            cli_args: Optionale Befehlszeilenargumente
            
        Returns:
            Config: Neue Konfigurationsinstanz
        """
        # 4. Standardwerte
        config = cls()
        
        # 3. Konfigurationsdatei
        if config_path:
            try:
                file_config = cls.from_file(config_path)
                config = cls._merge_configs(config, file_config)
            except ConfigurationError:
                # Wenn die Datei nicht existiert oder ungültig ist, weiter mit anderen Quellen
                pass
        
        # 2. Umgebungsvariablen
        env_config = cls.from_env()
        config = cls._merge_configs(config, env_config)
        
        # 1. Befehlszeilenargumente
        if cli_args:
            # Filtere nur die Argumente, die in der Config-Klasse existieren
            valid_args = {k: v for k, v in cli_args.items() if hasattr(config, k)}
            cli_config = cls(**valid_args)
            config = cls._merge_configs(config, cli_config)
        
        # Validiere die finale Konfiguration
        config._validate_config()
        
        return config
    
    @staticmethod
    def _merge_configs(base_config: 'Config', override_config: 'Config') -> 'Config':
        """
        Führt zwei Konfigurationen zusammen, wobei die zweite Vorrang hat.
        
        Args:
            base_config: Basis-Konfiguration
            override_config: Überschreibende Konfiguration
            
        Returns:
            Config: Zusammengeführte Konfiguration
        """
        merged_data = {}
        
        # Hole alle Felder der Config-Klasse
        for field_name in base_config.__dataclass_fields__:
            base_value = getattr(base_config, field_name)
            override_value = getattr(override_config, field_name, None)
            
            # Verwende den überschreibenden Wert, wenn er nicht None ist
            merged_data[field_name] = override_value if override_value is not None else base_value
        
        return Config(**merged_data)
    
    def validate_required_fields(self) -> None:
        """
        Validiert, dass alle erforderlichen Felder gesetzt sind.
        
        Raises:
            ConfigurationError: Wenn erforderliche Felder fehlen
        """
        required_fields = ['api_id', 'api_hash']
        missing_fields = [field for field in required_fields if not getattr(self, field)]
        
        if missing_fields:
            raise ConfigurationError(
                f"Fehlende erforderliche Konfigurationsfelder: {', '.join(missing_fields)}. "
                "Bitte setzen Sie diese über Umgebungsvariablen oder Konfigurationsdatei."
            )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Konvertiert die Konfiguration in ein Dictionary.
        
        Returns:
            Dict[str, Any]: Konfigurationsdaten als Dictionary
        """
        return {field_name: getattr(self, field_name) for field_name in self.__dataclass_fields__}
    
    def save_to_file(self, config_path: Union[str, Path], format: str = 'json') -> None:
        """
        Speichert die Konfiguration in einer Datei.
        
        Args:
            config_path: Pfad zur Konfigurationsdatei
            format: Format der Konfigurationsdatei ('json', 'yaml', 'ini')
        """
        config_path = Path(config_path)
        data = self.to_dict()
        
        if format.lower() == 'json':
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        elif format.lower() in ['yml', 'yaml']:
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
        elif format.lower() == 'ini':
            config = configparser.ConfigParser()
            config['DEFAULT'] = data
            with open(config_path, 'w', encoding='utf-8') as f:
                config.write(f)
        else:
            raise ConfigurationError(f"Nicht unterstütztes Ausgabeformat: {format}")