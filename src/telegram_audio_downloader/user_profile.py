"""
Benutzerprofilierung für den Telegram Audio Downloader.
"""

import json
import hashlib
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from pathlib import Path
from datetime import datetime

from .logging_config import get_logger
from .config import Config

logger = get_logger(__name__)


@dataclass
class UserProfile:
    """Datenklasse für ein Benutzerprofil."""
    user_id: str
    username: Optional[str] = None
    email: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    last_login: Optional[datetime] = None
    preferences: Dict[str, Any] = field(default_factory=dict)
    download_history: List[Dict[str, Any]] = field(default_factory=list)
    favorite_groups: List[str] = field(default_factory=list)
    custom_categories: Dict[str, List[str]] = field(default_factory=dict)
    accessibility_settings: Dict[str, Any] = field(default_factory=dict)
    keyboard_shortcuts: Dict[str, str] = field(default_factory=dict)
    language: str = "en"
    theme: str = "default"
    download_path: Optional[str] = None
    max_concurrent_downloads: int = 3
    download_quality: str = "high"
    auto_categorize: bool = True
    notifications_enabled: bool = True
    notification_methods: List[str] = field(default_factory=lambda: ["system"])
    privacy_settings: Dict[str, Any] = field(default_factory=dict)
    statistics: Dict[str, Any] = field(default_factory=dict)


class UserProfileManager:
    """Klasse zur Verwaltung von Benutzerprofilen."""
    
    def __init__(self, profiles_dir: Optional[str] = None):
        """
        Initialisiert den UserProfileManager.
        
        Args:
            profiles_dir: Verzeichnis für Profildateien
        """
        self.config = Config()
        self.profiles_dir = profiles_dir or str(Path(self.config.CONFIG_PATH) / "profiles")
        self.current_profile: Optional[UserProfile] = None
        self._ensure_profiles_dir()
    
    def _ensure_profiles_dir(self):
        """Stellt sicher, dass das Profilverzeichnis existiert."""
        Path(self.profiles_dir).mkdir(parents=True, exist_ok=True)
        logger.debug(f"Profilverzeichnis sichergestellt: {self.profiles_dir}")
    
    def _hash_user_id(self, user_id: str) -> str:
        """
        Erstellt einen Hash des Benutzer-IDs für die Dateinamen.
        
        Args:
            user_id: Benutzer-ID
            
        Returns:
            Gehashte Benutzer-ID
        """
        return hashlib.sha256(user_id.encode()).hexdigest()[:16]
    
    def _get_profile_path(self, user_id: str) -> Path:
        """
        Gibt den Pfad zur Profildatei zurück.
        
        Args:
            user_id: Benutzer-ID
            
        Returns:
            Pfad zur Profildatei
        """
        hashed_id = self._hash_user_id(user_id)
        return Path(self.profiles_dir) / f"{hashed_id}.json"
    
    def create_profile(self, user_id: str, username: Optional[str] = None, 
                      email: Optional[str] = None, **kwargs) -> UserProfile:
        """
        Erstellt ein neues Benutzerprofil.
        
        Args:
            user_id: Eindeutige Benutzer-ID
            username: Benutzername
            email: E-Mail-Adresse
            **kwargs: Zusätzliche Profilparameter
            
        Returns:
            Neues UserProfile-Objekt
        """
        # Erstelle das Profil
        profile = UserProfile(
            user_id=user_id,
            username=username,
            email=email,
            **kwargs
        )
        
        # Speichere das Profil
        self.save_profile(profile)
        logger.info(f"Neues Profil erstellt für Benutzer: {user_id}")
        
        return profile
    
    def load_profile(self, user_id: str) -> Optional[UserProfile]:
        """
        Lädt ein Benutzerprofil.
        
        Args:
            user_id: Benutzer-ID
            
        Returns:
            UserProfile-Objekt oder None, wenn nicht gefunden
        """
        profile_path = self._get_profile_path(user_id)
        
        if not profile_path.exists():
            logger.debug(f"Profil für Benutzer {user_id} nicht gefunden")
            return None
        
        try:
            with open(profile_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Konvertiere Datumsangaben
            if 'created_at' in data:
                data['created_at'] = datetime.fromisoformat(data['created_at'])
            if 'last_login' in data and data['last_login']:
                data['last_login'] = datetime.fromisoformat(data['last_login'])
            
            # Erstelle das Profil-Objekt
            profile = UserProfile(**data)
            
            logger.debug(f"Profil geladen für Benutzer: {user_id}")
            return profile
            
        except Exception as e:
            logger.error(f"Fehler beim Laden des Profils für {user_id}: {e}")
            return None
    
    def save_profile(self, profile: UserProfile):
        """
        Speichert ein Benutzerprofil.
        
        Args:
            profile: Zu speicherndes UserProfile-Objekt
        """
        profile_path = self._get_profile_path(profile.user_id)
        
        try:
            # Konvertiere Datumsangaben für die Serialisierung
            profile_dict = asdict(profile)
            profile_dict['created_at'] = profile_dict['created_at'].isoformat()
            if profile_dict['last_login']:
                profile_dict['last_login'] = profile_dict['last_login'].isoformat()
            
            # Speichere das Profil
            with open(profile_path, 'w', encoding='utf-8') as f:
                json.dump(profile_dict, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"Profil gespeichert für Benutzer: {profile.user_id}")
            
        except Exception as e:
            logger.error(f"Fehler beim Speichern des Profils für {profile.user_id}: {e}")
    
    def delete_profile(self, user_id: str) -> bool:
        """
        Löscht ein Benutzerprofil.
        
        Args:
            user_id: Benutzer-ID
            
        Returns:
            True, wenn erfolgreich gelöscht, False sonst
        """
        profile_path = self._get_profile_path(user_id)
        
        try:
            if profile_path.exists():
                profile_path.unlink()
                logger.info(f"Profil gelöscht für Benutzer: {user_id}")
                return True
            else:
                logger.debug(f"Profil zum Löschen nicht gefunden für Benutzer: {user_id}")
                return False
                
        except Exception as e:
            logger.error(f"Fehler beim Löschen des Profils für {user_id}: {e}")
            return False
    
    def list_profiles(self) -> List[str]:
        """
        Listet alle vorhandenen Benutzerprofile auf.
        
        Returns:
            Liste von Benutzer-IDs
        """
        try:
            profile_files = Path(self.profiles_dir).glob("*.json")
            user_ids = []
            
            for profile_file in profile_files:
                # Extrahiere die gehashte ID aus dem Dateinamen
                hashed_id = profile_file.stem
                user_ids.append(hashed_id)
            
            logger.debug(f"{len(user_ids)} Profile gefunden")
            return user_ids
            
        except Exception as e:
            logger.error(f"Fehler beim Auflisten der Profile: {e}")
            return []
    
    def set_current_profile(self, profile: UserProfile):
        """
        Setzt das aktuelle Benutzerprofil.
        
        Args:
            profile: UserProfile-Objekt
        """
        self.current_profile = profile
        # Aktualisiere das letzte Login-Datum
        profile.last_login = datetime.now()
        self.save_profile(profile)
        logger.debug(f"Aktuelles Profil gesetzt: {profile.user_id}")
    
    def get_current_profile(self) -> Optional[UserProfile]:
        """
        Gibt das aktuelle Benutzerprofil zurück.
        
        Returns:
            Aktuelles UserProfile-Objekt oder None
        """
        return self.current_profile
    
    def update_preference(self, user_id: str, key: str, value: Any) -> bool:
        """
        Aktualisiert eine Benutzereinstellung.
        
        Args:
            user_id: Benutzer-ID
            key: Einstellungsschlüssel
            value: Einstellungswert
            
        Returns:
            True, wenn erfolgreich aktualisiert, False sonst
        """
        profile = self.load_profile(user_id)
        if not profile:
            return False
        
        profile.preferences[key] = value
        self.save_profile(profile)
        logger.debug(f"Einstellung aktualisiert für {user_id}: {key} = {value}")
        return True
    
    def get_preference(self, user_id: str, key: str, default: Any = None) -> Any:
        """
        Gibt eine Benutzereinstellung zurück.
        
        Args:
            user_id: Benutzer-ID
            key: Einstellungsschlüssel
            default: Standardwert
            
        Returns:
            Einstellungswert oder Standardwert
        """
        profile = self.load_profile(user_id)
        if not profile:
            return default
        
        return profile.preferences.get(key, default)
    
    def add_to_download_history(self, user_id: str, download_info: Dict[str, Any]) -> bool:
        """
        Fügt einen Download zur Download-Historie hinzu.
        
        Args:
            user_id: Benutzer-ID
            download_info: Download-Informationen
            
        Returns:
            True, wenn erfolgreich hinzugefügt, False sonst
        """
        profile = self.load_profile(user_id)
        if not profile:
            return False
        
        # Füge Zeitstempel hinzu
        download_info['timestamp'] = datetime.now().isoformat()
        profile.download_history.append(download_info)
        
        # Begrenze die Historie auf 1000 Einträge
        if len(profile.download_history) > 1000:
            profile.download_history = profile.download_history[-1000:]
        
        self.save_profile(profile)
        logger.debug(f"Download zur Historie hinzugefügt für {user_id}")
        return True
    
    def get_download_history(self, user_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Gibt die Download-Historie eines Benutzers zurück.
        
        Args:
            user_id: Benutzer-ID
            limit: Maximale Anzahl von Einträgen
            
        Returns:
            Liste von Download-Informationen
        """
        profile = self.load_profile(user_id)
        if not profile:
            return []
        
        history = profile.download_history
        if limit:
            history = history[-limit:]  # Letzte N Einträge
        
        return history
    
    def add_favorite_group(self, user_id: str, group_id: str) -> bool:
        """
        Fügt eine Telegram-Gruppe zu den Favoriten hinzu.
        
        Args:
            user_id: Benutzer-ID
            group_id: Gruppen-ID
            
        Returns:
            True, wenn erfolgreich hinzugefügt, False sonst
        """
        profile = self.load_profile(user_id)
        if not profile:
            return False
        
        if group_id not in profile.favorite_groups:
            profile.favorite_groups.append(group_id)
            self.save_profile(profile)
            logger.debug(f"Gruppe zu Favoriten hinzugefügt für {user_id}: {group_id}")
            return True
        
        return False
    
    def remove_favorite_group(self, user_id: str, group_id: str) -> bool:
        """
        Entfernt eine Telegram-Gruppe aus den Favoriten.
        
        Args:
            user_id: Benutzer-ID
            group_id: Gruppen-ID
            
        Returns:
            True, wenn erfolgreich entfernt, False sonst
        """
        profile = self.load_profile(user_id)
        if not profile:
            return False
        
        if group_id in profile.favorite_groups:
            profile.favorite_groups.remove(group_id)
            self.save_profile(profile)
            logger.debug(f"Gruppe aus Favoriten entfernt für {user_id}: {group_id}")
            return True
        
        return False
    
    def get_favorite_groups(self, user_id: str) -> List[str]:
        """
        Gibt die favorisierten Telegram-Gruppen eines Benutzers zurück.
        
        Args:
            user_id: Benutzer-ID
            
        Returns:
            Liste von Gruppen-IDs
        """
        profile = self.load_profile(user_id)
        if not profile:
            return []
        
        return profile.favorite_groups
    
    def update_statistics(self, user_id: str, stat_key: str, value: Any) -> bool:
        """
        Aktualisiert eine Benutzerstatistik.
        
        Args:
            user_id: Benutzer-ID
            stat_key: Statistikschlüssel
            value: Statistikwert
            
        Returns:
            True, wenn erfolgreich aktualisiert, False sonst
        """
        profile = self.load_profile(user_id)
        if not profile:
            return False
        
        profile.statistics[stat_key] = value
        self.save_profile(profile)
        logger.debug(f"Statistik aktualisiert für {user_id}: {stat_key} = {value}")
        return True
    
    def get_statistics(self, user_id: str) -> Dict[str, Any]:
        """
        Gibt die Statistiken eines Benutzers zurück.
        
        Args:
            user_id: Benutzer-ID
            
        Returns:
            Dictionary mit Statistiken
        """
        profile = self.load_profile(user_id)
        if not profile:
            return {}
        
        return profile.statistics


# Globale Instanz
_profile_manager: Optional[UserProfileManager] = None

def get_profile_manager() -> UserProfileManager:
    """
    Gibt die globale Instanz des UserProfileManagers zurück.
    
    Returns:
        Instanz von UserProfileManager
    """
    global _profile_manager
    if _profile_manager is None:
        _profile_manager = UserProfileManager()
    return _profile_manager

def create_user_profile(user_id: str, username: Optional[str] = None, 
                       email: Optional[str] = None, **kwargs) -> UserProfile:
    """
    Erstellt ein neues Benutzerprofil.
    
    Args:
        user_id: Eindeutige Benutzer-ID
        username: Benutzername
        email: E-Mail-Adresse
        **kwargs: Zusätzliche Profilparameter
        
    Returns:
        Neues UserProfile-Objekt
    """
    manager = get_profile_manager()
    return manager.create_profile(user_id, username, email, **kwargs)

def load_user_profile(user_id: str) -> Optional[UserProfile]:
    """
    Lädt ein Benutzerprofil.
    
    Args:
        user_id: Benutzer-ID
        
    Returns:
        UserProfile-Objekt oder None, wenn nicht gefunden
    """
    manager = get_profile_manager()
    return manager.load_profile(user_id)

def save_user_profile(profile: UserProfile):
    """
    Speichert ein Benutzerprofil.
    
    Args:
        profile: Zu speicherndes UserProfile-Objekt
    """
    manager = get_profile_manager()
    manager.save_profile(profile)

def set_current_user_profile(profile: UserProfile):
    """
    Setzt das aktuelle Benutzerprofil.
    
    Args:
        profile: UserProfile-Objekt
    """
    manager = get_profile_manager()
    manager.set_current_profile(profile)

def get_current_user_profile() -> Optional[UserProfile]:
    """
    Gibt das aktuelle Benutzerprofil zurück.
    
    Returns:
        Aktuelles UserProfile-Objekt oder None
    """
    manager = get_profile_manager()
    return manager.get_current_profile()

def update_user_preference(user_id: str, key: str, value: Any) -> bool:
    """
    Aktualisiert eine Benutzereinstellung.
    
    Args:
        user_id: Benutzer-ID
        key: Einstellungsschlüssel
        value: Einstellungswert
        
    Returns:
        True, wenn erfolgreich aktualisiert, False sonst
    """
    manager = get_profile_manager()
    return manager.update_preference(user_id, key, value)

def get_user_preference(user_id: str, key: str, default: Any = None) -> Any:
    """
    Gibt eine Benutzereinstellung zurück.
    
    Args:
        user_id: Benutzer-ID
        key: Einstellungsschlüssel
        default: Standardwert
        
    Returns:
        Einstellungswert oder Standardwert
    """
    manager = get_profile_manager()
    return manager.get_preference(user_id, key, default)