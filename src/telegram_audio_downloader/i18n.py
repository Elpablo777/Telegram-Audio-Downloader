"""
Mehrsprachige Unterstützung (i18n) für den Telegram Audio Downloader.
"""

import json
import os
from typing import Dict, Optional, Any
from pathlib import Path
from enum import Enum

from .logging_config import get_logger

logger = get_logger(__name__)


class Language(Enum):
    """Enumeration der unterstützten Sprachen."""
    ENGLISH = "en"
    GERMAN = "de"
    SPANISH = "es"
    FRENCH = "fr"
    ITALIAN = "it"
    PORTUGUESE = "pt"
    RUSSIAN = "ru"
    CHINESE = "zh"
    JAPANESE = "ja"
    KOREAN = "ko"


# Standardübersetzungen (Englisch)
DEFAULT_TRANSLATIONS = {
    # Allgemeine Begriffe
    "welcome": "Welcome to Telegram Audio Downloader",
    "quit": "Quit",
    "help": "Help",
    "search": "Search",
    "download": "Download",
    "settings": "Settings",
    "cancel": "Cancel",
    "confirm": "Confirm",
    "error": "Error",
    "success": "Success",
    "warning": "Warning",
    "info": "Information",
    
    # Hauptmenü
    "main_menu": "Main Menu",
    "search_and_download": "Search and Download",
    "manage_downloads": "Manage Downloads",
    "view_downloaded_files": "View Downloaded Files",
    "search_downloaded_files": "Search Downloaded Files",
    "manage_groups": "Manage Telegram Groups",
    "view_settings": "View Settings",
    "advanced_options": "Advanced Options",
    
    # Suchfunktion
    "search_prompt": "Enter search term",
    "search_results": "Search Results",
    "no_results": "No results found",
    "files_found": "{} files found",
    
    # Download-Funktion
    "download_progress": "Download Progress",
    "download_complete": "Download complete",
    "download_failed": "Download failed",
    "downloading": "Downloading",
    "pending": "Pending",
    "completed": "Completed",
    "failed": "Failed",
    
    # Einstellungen
    "download_path": "Download Path",
    "max_concurrent_downloads": "Max Concurrent Downloads",
    "download_retries": "Download Retries",
    "timeout": "Timeout (seconds)",
    "quality": "Quality",
    
    # Fehlermeldungen
    "error_occurred": "An error occurred: {}",
    "file_not_found": "File not found",
    "connection_error": "Connection error",
    "authentication_error": "Authentication error",
    "download_error": "Download error",
    
    # Bestätigungen
    "confirm_quit": "Do you really want to quit?",
    "confirm_download": "Do you want to download {} files?",
    "confirm_delete": "Do you really want to delete this file?",
    
    # Statusmeldungen
    "initializing": "Initializing...",
    "connecting": "Connecting...",
    "processing": "Processing...",
    "saving": "Saving...",
    "done": "Done",
    
    # Kategorien
    "category_classical": "Classical",
    "category_jazz": "Jazz",
    "category_rock": "Rock",
    "category_pop": "Pop",
    "category_electronic": "Electronic",
    "category_hiphop": "Hip Hop",
    "category_country": "Country",
    "category_reggae": "Reggae",
    "category_latin": "Latin",
    "category_world": "World",
    "category_unclassified": "Unclassified",
    
    # Dateitypen
    "file_type_mp3": "MP3 Audio",
    "file_type_flac": "FLAC Audio",
    "file_type_m4a": "M4A Audio",
    "file_type_wav": "WAV Audio",
    "file_type_ogg": "OGG Audio",
    
    # Tastaturkürzel
    "shortcut_quit": "Quit program",
    "shortcut_help": "Show help",
    "shortcut_search": "Start search",
    "shortcut_download": "Start download",
    "shortcut_pause": "Pause/resume downloads",
    "shortcut_config": "Show settings",
    
    # Interaktiver Modus
    "interactive_mode": "Interactive Mode",
    "choose_option": "Choose an option",
    "enter_choice": "Enter your choice",
    "invalid_choice": "Invalid choice",
    
    # Fortschrittsanzeige
    "progress_eta": "ETA",
    "progress_speed": "Speed",
    "progress_downloaded": "Downloaded",
    "progress_total": "Total",
    
    # Gruppenverwaltung
    "manage_groups_title": "Manage Telegram Groups",
    "add_group": "Add Group",
    "remove_group": "Remove Group",
    "list_groups": "List Groups",
    
    # Hilfetexte
    "help_welcome": "Welcome to the Telegram Audio Downloader help system",
    "help_navigation": "Use arrow keys or shortcuts to navigate",
    "help_search": "Enter terms to search for audio files in Telegram groups",
    "help_download": "Select files and start downloading",
    "help_settings": "Configure downloader behavior",
}


class TranslationManager:
    """Klasse zur Verwaltung von Übersetzungen."""
    
    def __init__(self, language: Language = Language.ENGLISH, translations_dir: Optional[str] = None):
        """
        Initialisiert den TranslationManager.
        
        Args:
            language: Zu verwendende Sprache
            translations_dir: Verzeichnis mit Übersetzungsdateien
        """
        self.language = language
        self.translations_dir = translations_dir or str(Path(__file__).parent / "translations")
        self.translations = DEFAULT_TRANSLATIONS.copy()
        self._load_translations()
    
    def _load_translations(self):
        """Lädt die Übersetzungen für die aktuelle Sprache."""
        if self.language == Language.ENGLISH:
            # Englisch ist die Standardsprache
            return
        
        # Erstelle das Übersetzungsverzeichnis, falls es nicht existiert
        Path(self.translations_dir).mkdir(parents=True, exist_ok=True)
        
        # Pfad zur Übersetzungsdatei
        translation_file = Path(self.translations_dir) / f"{self.language.value}.json"
        
        try:
            if translation_file.exists():
                with open(translation_file, 'r', encoding='utf-8') as f:
                    loaded_translations = json.load(f)
                    # Kombiniere mit Standardübersetzungen
                    self.translations.update(loaded_translations)
                    logger.debug(f"Übersetzungen für {self.language.value} geladen")
            else:
                # Erstelle eine leere Übersetzungsdatei basierend auf den Standardübersetzungen
                self._create_translation_file(translation_file)
                logger.debug(f"Leere Übersetzungsdatei für {self.language.value} erstellt")
        except Exception as e:
            logger.error(f"Fehler beim Laden der Übersetzungen für {self.language.value}: {e}")
    
    def _create_translation_file(self, translation_file: Path):
        """
        Erstellt eine leere Übersetzungsdatei.
        
        Args:
            translation_file: Pfad zur Übersetzungsdatei
        """
        try:
            # Erstelle ein Dictionary mit leeren Werten für alle Schlüssel
            empty_translations = {key: "" for key in DEFAULT_TRANSLATIONS.keys()}
            
            with open(translation_file, 'w', encoding='utf-8') as f:
                json.dump(empty_translations, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Fehler beim Erstellen der Übersetzungsdatei {translation_file}: {e}")
    
    def set_language(self, language: Language):
        """
        Setzt die aktuelle Sprache.
        
        Args:
            language: Neue Sprache
        """
        self.language = language
        self._load_translations()
        logger.debug(f"Sprache geändert zu {language.value}")
    
    def get_translation(self, key: str, **kwargs) -> str:
        """
        Gibt die Übersetzung für einen Schlüssel zurück.
        
        Args:
            key: Übersetzungsschlüssel
            **kwargs: Platzhalterwerte für die Übersetzung
            
        Returns:
            Übersetzter Text
        """
        translation = self.translations.get(key, key)  # Fallback auf den Schlüssel selbst
        
        # Ersetze Platzhalter
        if kwargs:
            try:
                translation = translation.format(**kwargs)
            except (KeyError, IndexError) as e:
                logger.warning(f"Fehler beim Formatieren der Übersetzung '{key}': {e}")
        
        return translation
    
    def add_translation(self, key: str, translation: str):
        """
        Fügt eine neue Übersetzung hinzu.
        
        Args:
            key: Übersetzungsschlüssel
            translation: Übersetzter Text
        """
        self.translations[key] = translation
        logger.debug(f"Übersetzung hinzugefügt: {key} -> {translation}")
    
    def save_translations(self):
        """Speichert die aktuellen Übersetzungen in der Datei."""
        if self.language == Language.ENGLISH:
            return  # Keine Speicherung für die Standardsprache
        
        translation_file = Path(self.translations_dir) / f"{self.language.value}.json"
        
        try:
            with open(translation_file, 'w', encoding='utf-8') as f:
                json.dump(self.translations, f, ensure_ascii=False, indent=2)
            logger.debug(f"Übersetzungen für {self.language.value} gespeichert")
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Übersetzungen für {self.language.value}: {e}")


# Globale Instanz
_translation_manager: Optional[TranslationManager] = None

def get_translation_manager() -> TranslationManager:
    """
    Gibt die globale Instanz des TranslationManagers zurück.
    
    Returns:
        Instanz von TranslationManager
    """
    global _translation_manager
    if _translation_manager is None:
        _translation_manager = TranslationManager()
    return _translation_manager

def set_language(language: Language):
    """
    Setzt die aktuelle Sprache.
    
    Args:
        language: Neue Sprache
    """
    manager = get_translation_manager()
    manager.set_language(language)

def _(key: str, **kwargs) -> str:
    """
    Gibt die Übersetzung für einen Schlüssel zurück.
    
    Args:
        key: Übersetzungsschlüssel
        **kwargs: Platzhalterwerte für die Übersetzung
        
    Returns:
        Übersetzter Text
    """
    manager = get_translation_manager()
    return manager.get_translation(key, **kwargs)

def add_translation(key: str, translation: str):
    """
    Fügt eine neue Übersetzung hinzu.
    
    Args:
        key: Übersetzungsschlüssel
        translation: Übersetzter Text
    """
    manager = get_translation_manager()
    manager.add_translation(key, translation)

# Erstelle deutsche Übersetzungen
GERMAN_TRANSLATIONS = {
    # Allgemeine Begriffe
    "welcome": "Willkommen beim Telegram Audio Downloader",
    "quit": "Beenden",
    "help": "Hilfe",
    "search": "Suchen",
    "download": "Herunterladen",
    "settings": "Einstellungen",
    "cancel": "Abbrechen",
    "confirm": "Bestätigen",
    "error": "Fehler",
    "success": "Erfolg",
    "warning": "Warnung",
    "info": "Information",
    
    # Hauptmenü
    "main_menu": "Hauptmenü",
    "search_and_download": "Suchen und Herunterladen",
    "manage_downloads": "Downloads verwalten",
    "view_downloaded_files": "Heruntergeladene Dateien anzeigen",
    "search_downloaded_files": "In heruntergeladenen Dateien suchen",
    "manage_groups": "Telegram-Gruppen verwalten",
    "view_settings": "Einstellungen anzeigen",
    "advanced_options": "Erweiterte Optionen",
    
    # Suchfunktion
    "search_prompt": "Suchbegriff eingeben",
    "search_results": "Suchergebnisse",
    "no_results": "Keine Ergebnisse gefunden",
    "files_found": "{} Dateien gefunden",
    
    # Download-Funktion
    "download_progress": "Download-Fortschritt",
    "download_complete": "Download abgeschlossen",
    "download_failed": "Download fehlgeschlagen",
    "downloading": "Wird heruntergeladen",
    "pending": "Ausstehend",
    "completed": "Abgeschlossen",
    "failed": "Fehlgeschlagen",
    
    # Einstellungen
    "download_path": "Download-Pfad",
    "max_concurrent_downloads": "Max. gleichzeitige Downloads",
    "download_retries": "Download-Wiederholungen",
    "timeout": "Timeout (Sekunden)",
    "quality": "Qualität",
    
    # Fehlermeldungen
    "error_occurred": "Ein Fehler ist aufgetreten: {}",
    "file_not_found": "Datei nicht gefunden",
    "connection_error": "Verbindungsfehler",
    "authentication_error": "Authentifizierungsfehler",
    "download_error": "Download-Fehler",
    
    # Bestätigungen
    "confirm_quit": "Möchten Sie das Programm wirklich beenden?",
    "confirm_download": "Möchten Sie {} Dateien herunterladen?",
    "confirm_delete": "Möchten Sie diese Datei wirklich löschen?",
    
    # Statusmeldungen
    "initializing": "Initialisierung...",
    "connecting": "Verbindung wird hergestellt...",
    "processing": "Verarbeitung...",
    "saving": "Speichern...",
    "done": "Fertig",
    
    # Kategorien
    "category_classical": "Klassik",
    "category_jazz": "Jazz",
    "category_rock": "Rock",
    "category_pop": "Pop",
    "category_electronic": "Elektronisch",
    "category_hiphop": "Hip Hop",
    "category_country": "Country",
    "category_reggae": "Reggae",
    "category_latin": "Latein",
    "category_world": "Weltmusik",
    "category_unclassified": "Nicht klassifiziert",
    
    # Dateitypen
    "file_type_mp3": "MP3-Audio",
    "file_type_flac": "FLAC-Audio",
    "file_type_m4a": "M4A-Audio",
    "file_type_wav": "WAV-Audio",
    "file_type_ogg": "OGG-Audio",
    
    # Tastaturkürzel
    "shortcut_quit": "Programm beenden",
    "shortcut_help": "Hilfe anzeigen",
    "shortcut_search": "Suche starten",
    "shortcut_download": "Download starten",
    "shortcut_pause": "Downloads pausieren/fortsetzen",
    "shortcut_config": "Einstellungen anzeigen",
    
    # Interaktiver Modus
    "interactive_mode": "Interaktiver Modus",
    "choose_option": "Wählen Sie eine Option",
    "enter_choice": "Geben Sie Ihre Auswahl ein",
    "invalid_choice": "Ungültige Auswahl",
    
    # Fortschrittsanzeige
    "progress_eta": "Verbleibend",
    "progress_speed": "Geschwindigkeit",
    "progress_downloaded": "Heruntergeladen",
    "progress_total": "Gesamt",
    
    # Gruppenverwaltung
    "manage_groups_title": "Telegram-Gruppen verwalten",
    "add_group": "Gruppe hinzufügen",
    "remove_group": "Gruppe entfernen",
    "list_groups": "Gruppen auflisten",
    
    # Hilfetexte
    "help_welcome": "Willkommen im Hilfe-System des Telegram Audio Downloaders",
    "help_navigation": "Verwenden Sie die Pfeiltasten oder Tastaturkürzel zur Navigation",
    "help_search": "Geben Sie Begriffe ein, um nach Audiodateien in Telegram-Gruppen zu suchen",
    "help_download": "Wählen Sie Dateien aus und starten Sie den Download",
    "help_settings": "Konfigurieren Sie das Verhalten des Downloaders",
}

# Initialisiere den TranslationManager mit deutschen Übersetzungen, falls gewünscht
def init_translations(language: Language = Language.ENGLISH):
    """
    Initialisiert die Übersetzungen.
    
    Args:
        language: Zu verwendende Sprache
    """
    global _translation_manager
    _translation_manager = TranslationManager(language)
    
    # Wenn Deutsch ausgewählt ist, füge die deutschen Übersetzungen hinzu
    if language == Language.GERMAN:
        for key, translation in GERMAN_TRANSLATIONS.items():
            _translation_manager.add_translation(key, translation)
        _translation_manager.save_translations()