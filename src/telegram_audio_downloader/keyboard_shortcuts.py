"""
Tastaturkürzel für den Telegram Audio Downloader.
"""

from typing import Dict, Callable, Optional, Any
from dataclasses import dataclass, field
import sys

from .logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class Shortcut:
    """Datenklasse für ein Tastaturkürzel."""
    key: str
    description: str
    action: Callable
    context: str = "global"  # global, download, search, etc.
    enabled: bool = True


class KeyboardShortcutManager:
    """Klasse zur Verwaltung von Tastaturkürzeln."""
    
    def __init__(self):
        """Initialisiert den KeyboardShortcutManager."""
        self.shortcuts: Dict[str, Shortcut] = {}
        self.context = "global"
        self._initialize_default_shortcuts()
    
    def _initialize_default_shortcuts(self):
        """Initialisiert die Standard-Tastaturkürzel."""
        # Globale Tastaturkürzel
        self.register_shortcut(
            key="q",
            description="Programm beenden",
            action=self._quit_action,
            context="global"
        )
        
        self.register_shortcut(
            key="h",
            description="Hilfe anzeigen",
            action=self._help_action,
            context="global"
        )
        
        self.register_shortcut(
            key="s",
            description="Suchen",
            action=self._search_action,
            context="global"
        )
        
        self.register_shortcut(
            key="d",
            description="Download starten",
            action=self._download_action,
            context="global"
        )
        
        self.register_shortcut(
            key="p",
            description="Downloads pausieren/fortsetzen",
            action=self._pause_action,
            context="global"
        )
        
        self.register_shortcut(
            key="c",
            description="Einstellungen anzeigen",
            action=self._config_action,
            context="global"
        )
        
        # Kontextspezifische Tastaturkürzel
        self.register_shortcut(
            key="enter",
            description="Auswahl bestätigen",
            action=self._confirm_action,
            context="selection"
        )
        
        self.register_shortcut(
            key="esc",
            description="Abbrechen/zurück",
            action=self._cancel_action,
            context="selection"
        )
        
        self.register_shortcut(
            key="space",
            description="Auswahl umschalten",
            action=self._toggle_action,
            context="selection"
        )
    
    def register_shortcut(self, key: str, description: str, action: Callable, context: str = "global", enabled: bool = True):
        """
        Registriert ein neues Tastaturkürzel.
        
        Args:
            key: Tastenkürzel (z.B. "ctrl+s", "q", "f1")
            description: Beschreibung der Aktion
            action: Funktion, die bei Drücken der Taste ausgeführt wird
            context: Kontext, in dem das Kürzel aktiv ist
            enabled: Ob das Kürzel aktiviert ist
        """
        shortcut = Shortcut(
            key=key.lower(),
            description=description,
            action=action,
            context=context,
            enabled=enabled
        )
        self.shortcuts[key.lower()] = shortcut
        logger.debug(f"Tastaturkürzel registriert: {key} - {description}")
    
    def unregister_shortcut(self, key: str):
        """
        Entfernt ein Tastaturkürzel.
        
        Args:
            key: Tastenkürzel zum Entfernen
        """
        key = key.lower()
        if key in self.shortcuts:
            del self.shortcuts[key]
            logger.debug(f"Tastaturkürzel entfernt: {key}")
    
    def enable_shortcut(self, key: str):
        """
        Aktiviert ein Tastaturkürzel.
        
        Args:
            key: Tastenkürzel zum Aktivieren
        """
        key = key.lower()
        if key in self.shortcuts:
            self.shortcuts[key].enabled = True
            logger.debug(f"Tastaturkürzel aktiviert: {key}")
    
    def disable_shortcut(self, key: str):
        """
        Deaktiviert ein Tastaturkürzel.
        
        Args:
            key: Tastenkürzel zum Deaktivieren
        """
        key = key.lower()
        if key in self.shortcuts:
            self.shortcuts[key].enabled = False
            logger.debug(f"Tastaturkürzel deaktiviert: {key}")
    
    def set_context(self, context: str):
        """
        Setzt den aktuellen Kontext.
        
        Args:
            context: Neuer Kontext
        """
        self.context = context
        logger.debug(f"Kontext geändert: {context}")
    
    def get_shortcuts_for_context(self, context: Optional[str] = None) -> Dict[str, Shortcut]:
        """
        Gibt die Tastaturkürzel für einen bestimmten Kontext zurück.
        
        Args:
            context: Kontext (standardmäßig der aktuelle Kontext)
            
        Returns:
            Dictionary mit Tastaturkürzeln
        """
        if context is None:
            context = self.context
        
        return {
            key: shortcut for key, shortcut in self.shortcuts.items()
            if shortcut.context in [context, "global"] and shortcut.enabled
        }
    
    def handle_keypress(self, key: str) -> bool:
        """
        Behandelt einen Tastendruck.
        
        Args:
            key: Gedrückte Taste
            
        Returns:
            True, wenn das Tastaturkürzel verarbeitet wurde, False sonst
        """
        key = key.lower()
        
        # Prüfe, ob das Tastaturkürzel im aktuellen Kontext existiert und aktiviert ist
        if key in self.shortcuts:
            shortcut = self.shortcuts[key]
            if shortcut.enabled and shortcut.context in [self.context, "global"]:
                try:
                    shortcut.action()
                    logger.debug(f"Tastaturkürzel ausgeführt: {key}")
                    return True
                except Exception as e:
                    logger.error(f"Fehler beim Ausführen des Tastaturkürzels {key}: {e}")
                    return False
        
        return False
    
    def show_help(self):
        """Zeigt eine Hilfe zu den verfügbaren Tastaturkürzeln an."""
        print("\nVerfügbare Tastaturkürzel:")
        print("-" * 40)
        
        # Gruppiere nach Kontext
        contexts = {}
        for shortcut in self.shortcuts.values():
            if shortcut.enabled:
                if shortcut.context not in contexts:
                    contexts[shortcut.context] = []
                contexts[shortcut.context].append(shortcut)
        
        # Zeige globale Tastaturkürzel
        if "global" in contexts:
            print("\nGlobale Tastaturkürzel:")
            for shortcut in contexts["global"]:
                print(f"  {shortcut.key:10} - {shortcut.description}")
        
        # Zeige kontextspezifische Tastaturkürzel
        for context, shortcuts in contexts.items():
            if context != "global":
                print(f"\n{context.title()}-Tastaturkürzel:")
                for shortcut in shortcuts:
                    if shortcut.context == context:
                        print(f"  {shortcut.key:10} - {shortcut.description}")
    
    # Standard-Aktionen
    def _quit_action(self):
        """Standardaktion zum Beenden des Programms."""
        print("Programm wird beendet...")
        sys.exit(0)
    
    def _help_action(self):
        """Standardaktion zum Anzeigen der Hilfe."""
        self.show_help()
    
    def _search_action(self):
        """Standardaktion zum Starten einer Suche."""
        print("Suchfunktion wird aufgerufen...")
        # Hier würde die Suchfunktion aufgerufen werden
    
    def _download_action(self):
        """Standardaktion zum Starten eines Downloads."""
        print("Download wird gestartet...")
        # Hier würde der Download gestartet werden
    
    def _pause_action(self):
        """Standardaktion zum Pausieren/Fortsetzen von Downloads."""
        print("Downloads werden pausiert/fortgesetzt...")
        # Hier würde die Pausenfunktion aufgerufen werden
    
    def _config_action(self):
        """Standardaktion zum Anzeigen der Einstellungen."""
        print("Einstellungen werden angezeigt...")
        # Hier würden die Einstellungen angezeigt werden
    
    def _confirm_action(self):
        """Standardaktion zur Bestätigung einer Auswahl."""
        print("Auswahl bestätigt.")
        # Hier würde die Bestätigungslogik implementiert werden
    
    def _cancel_action(self):
        """Standardaktion zum Abbrechen."""
        print("Aktion abgebrochen.")
        # Hier würde die Abbruchlogik implementiert werden
    
    def _toggle_action(self):
        """Standardaktion zum Umschalten einer Auswahl."""
        print("Auswahl umgeschaltet.")
        # Hier würde die Umschaltlogik implementiert werden


# Globale Instanz
_keyboard_shortcut_manager: Optional[KeyboardShortcutManager] = None

def get_keyboard_shortcut_manager() -> KeyboardShortcutManager:
    """
    Gibt die globale Instanz des KeyboardShortcutManagers zurück.
    
    Returns:
        Instanz von KeyboardShortcutManager
    """
    global _keyboard_shortcut_manager
    if _keyboard_shortcut_manager is None:
        _keyboard_shortcut_manager = KeyboardShortcutManager()
    return _keyboard_shortcut_manager

def register_shortcut(key: str, description: str, action: Callable, context: str = "global", enabled: bool = True):
    """
    Registriert ein neues Tastaturkürzel.
    
    Args:
        key: Tastenkürzel
        description: Beschreibung der Aktion
        action: Funktion, die bei Drücken der Taste ausgeführt wird
        context: Kontext, in dem das Kürzel aktiv ist
        enabled: Ob das Kürzel aktiviert ist
    """
    manager = get_keyboard_shortcut_manager()
    manager.register_shortcut(key, description, action, context, enabled)

def unregister_shortcut(key: str):
    """
    Entfernt ein Tastaturkürzel.
    
    Args:
        key: Tastenkürzel zum Entfernen
    """
    manager = get_keyboard_shortcut_manager()
    manager.unregister_shortcut(key)

def handle_keypress(key: str) -> bool:
    """
    Behandelt einen Tastendruck.
    
    Args:
        key: Gedrückte Taste
        
    Returns:
        True, wenn das Tastaturkürzel verarbeitet wurde, False sonst
    """
    manager = get_keyboard_shortcut_manager()
    return manager.handle_keypress(key)

def set_shortcut_context(context: str):
    """
    Setzt den aktuellen Kontext für Tastaturkürzel.
    
    Args:
        context: Neuer Kontext
    """
    manager = get_keyboard_shortcut_manager()
    manager.set_context(context)

def show_shortcut_help():
    """Zeigt eine Hilfe zu den verfügbaren Tastaturkürzeln an."""
    manager = get_keyboard_shortcut_manager()
    manager.show_help()