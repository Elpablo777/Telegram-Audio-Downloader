"""
Benutzerdefinierte Tastenkombinationen für den Telegram Audio Downloader.
"""

import json
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field, asdict
from pathlib import Path
from enum import Enum

from .logging_config import get_logger
from .config import Config
from .i18n import _

logger = get_logger(__name__)


class KeyModifier(Enum):
    """Enumeration der Tastenmodifikatoren."""
    CTRL = "ctrl"
    ALT = "alt"
    SHIFT = "shift"
    META = "meta"  # Cmd auf macOS, Windows-Taste auf Windows


class KeyContext(Enum):
    """Enumeration der Tastenkontexte."""
    GLOBAL = "global"
    SEARCH = "search"
    DOWNLOAD = "download"
    SETTINGS = "settings"
    INTERACTIVE = "interactive"
    PROGRESS = "progress"
    HELP = "help"


@dataclass
class KeyBinding:
    """Datenklasse für eine Tastenbelegung."""
    key: str
    modifiers: List[KeyModifier] = field(default_factory=list)
    action: str = ""  # Name der Aktion
    context: KeyContext = KeyContext.GLOBAL
    enabled: bool = True
    description: str = ""
    custom_action: Optional[Callable] = None


class CustomKeybindingManager:
    """Klasse zur Verwaltung von benutzerdefinierten Tastenkombinationen."""
    
    def __init__(self, keybindings_file: Optional[str] = None):
        """
        Initialisiert den CustomKeybindingManager.
        
        Args:
            keybindings_file: Pfad zur Datei mit benutzerdefinierten Tastenkombinationen
        """
        self.config = Config()
        self.keybindings_file = keybindings_file or str(Path(self.config.CONFIG_PATH) / "keybindings.json")
        self.keybindings: Dict[str, KeyBinding] = {}
        self.action_callbacks: Dict[str, Callable] = {}
        self.context = KeyContext.GLOBAL
        self._load_default_keybindings()
        self._load_custom_keybindings()
    
    def _load_default_keybindings(self):
        """Lädt die standardmäßigen Tastenkombinationen."""
        default_bindings = [
            # Globale Tastenkombinationen
            KeyBinding(key="q", action="quit", context=KeyContext.GLOBAL, 
                      description=_("shortcut_quit")),
            KeyBinding(key="h", action="help", context=KeyContext.GLOBAL, 
                      description=_("shortcut_help")),
            KeyBinding(key="s", action="search", context=KeyContext.GLOBAL, 
                      description=_("shortcut_search")),
            KeyBinding(key="d", action="download", context=KeyContext.GLOBAL, 
                      description=_("shortcut_download")),
            KeyBinding(key="p", action="pause", context=KeyContext.GLOBAL, 
                      description=_("shortcut_pause")),
            KeyBinding(key="c", action="config", context=KeyContext.GLOBAL, 
                      description=_("shortcut_config")),
            
            # Interaktiver Modus
            KeyBinding(key="enter", action="confirm", context=KeyContext.INTERACTIVE, 
                      description=_("confirm")),
            KeyBinding(key="esc", action="cancel", context=KeyContext.INTERACTIVE, 
                      description=_("cancel")),
            KeyBinding(key=" ", action="toggle", context=KeyContext.INTERACTIVE, 
                      description=_("toggle_selection")),
            
            # Navigations-Tasten
            KeyBinding(key="up", action="navigate_up", context=KeyContext.INTERACTIVE, 
                      description=_("navigate_up")),
            KeyBinding(key="down", action="navigate_down", context=KeyContext.INTERACTIVE, 
                      description=_("navigate_down")),
            KeyBinding(key="left", action="navigate_left", context=KeyContext.INTERACTIVE, 
                      description=_("navigate_left")),
            KeyBinding(key="right", action="navigate_right", context=KeyContext.INTERACTIVE, 
                      description=_("navigate_right")),
            
            # Suchmodus
            KeyBinding(key="f", action="filter", context=KeyContext.SEARCH, 
                      description=_("filter_results")),
            KeyBinding(key="r", action="refresh", context=KeyContext.SEARCH, 
                      description=_("refresh_search")),
            
            # Download-Modus
            KeyBinding(key="a", action="select_all", context=KeyContext.DOWNLOAD, 
                      description=_("select_all")),
            KeyBinding(key="n", action="select_none", context=KeyContext.DOWNLOAD, 
                      description=_("select_none")),
            KeyBinding(key="i", action="invert_selection", context=KeyContext.DOWNLOAD, 
                      description=_("invert_selection")),
        ]
        
        # Registriere die Standard-Tastenkombinationen
        for binding in default_bindings:
            self.register_keybinding(binding)
        
        logger.debug("Standard-Tastenkombinationen geladen")
    
    def _load_custom_keybindings(self):
        """Lädt benutzerdefinierte Tastenkombinationen aus der Datei."""
        try:
            if Path(self.keybindings_file).exists():
                with open(self.keybindings_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Konvertiere die Daten in KeyBinding-Objekte
                for binding_data in data:
                    # Konvertiere Modifikatoren
                    modifiers = [KeyModifier(mod) for mod in binding_data.get("modifiers", [])]
                    
                    # Konvertiere Kontext
                    context = KeyContext(binding_data.get("context", "global"))
                    
                    # Erstelle das KeyBinding-Objekt
                    binding = KeyBinding(
                        key=binding_data["key"],
                        modifiers=modifiers,
                        action=binding_data["action"],
                        context=context,
                        enabled=binding_data.get("enabled", True),
                        description=binding_data.get("description", "")
                    )
                    
                    self.register_keybinding(binding)
                
                logger.debug(f"Benutzerdefinierte Tastenkombinationen geladen: {self.keybindings_file}")
            
        except Exception as e:
            logger.error(f"Fehler beim Laden der benutzerdefinierten Tastenkombinationen: {e}")
    
    def _save_custom_keybindings(self):
        """Speichert benutzerdefinierte Tastenkombinationen in der Datei."""
        try:
            # Konvertiere KeyBinding-Objekte in serialisierbare Daten
            bindings_data = []
            for binding in self.keybindings.values():
                if not binding.action.startswith("default_"):  # Speichere nur benutzerdefinierte Bindings
                    binding_data = {
                        "key": binding.key,
                        "modifiers": [mod.value for mod in binding.modifiers],
                        "action": binding.action,
                        "context": binding.context.value,
                        "enabled": binding.enabled,
                        "description": binding.description
                    }
                    bindings_data.append(binding_data)
            
            # Speichere die Daten
            Path(self.keybindings_file).parent.mkdir(parents=True, exist_ok=True)
            with open(self.keybindings_file, 'w', encoding='utf-8') as f:
                json.dump(bindings_data, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"Benutzerdefinierte Tastenkombinationen gespeichert: {self.keybindings_file}")
            
        except Exception as e:
            logger.error(f"Fehler beim Speichern der benutzerdefinierten Tastenkombinationen: {e}")
    
    def register_keybinding(self, binding: KeyBinding):
        """
        Registriert eine neue Tastenkombination.
        
        Args:
            binding: KeyBinding-Objekt
        """
        # Erstelle einen eindeutigen Schlüssel für die Tastenkombination
        binding_key = self._generate_binding_key(binding)
        
        # Registriere die Tastenkombination
        self.keybindings[binding_key] = binding
        logger.debug(f"Tastenkombination registriert: {binding_key}")
    
    def unregister_keybinding(self, binding: KeyBinding) -> bool:
        """
        Entfernt eine Tastenkombination.
        
        Args:
            binding: KeyBinding-Objekt
            
        Returns:
            True, wenn erfolgreich entfernt, False sonst
        """
        binding_key = self._generate_binding_key(binding)
        
        if binding_key in self.keybindings:
            del self.keybindings[binding_key]
            self._save_custom_keybindings()
            logger.debug(f"Tastenkombination entfernt: {binding_key}")
            return True
        
        return False
    
    def _generate_binding_key(self, binding: KeyBinding) -> str:
        """
        Generiert einen eindeutigen Schlüssel für eine Tastenkombination.
        
        Args:
            binding: KeyBinding-Objekt
            
        Returns:
            Eindeutiger Schlüssel
        """
        # Sortiere die Modifikatoren für eine konsistente Darstellung
        modifiers = sorted([mod.value for mod in binding.modifiers])
        modifier_str = "+".join(modifiers) if modifiers else ""
        
        # Erstelle den Schlüssel
        if modifier_str:
            return f"{modifier_str}+{binding.key}+{binding.context.value}"
        else:
            return f"{binding.key}+{binding.context.value}"
    
    def bind_action(self, action_name: str, callback: Callable):
        """
        Bindet eine Aktion an eine Callback-Funktion.
        
        Args:
            action_name: Name der Aktion
            callback: Callback-Funktion
        """
        self.action_callbacks[action_name] = callback
        logger.debug(f"Aktion gebunden: {action_name}")
    
    def unbind_action(self, action_name: str) -> bool:
        """
        Entfernt die Bindung einer Aktion.
        
        Args:
            action_name: Name der Aktion
            
        Returns:
            True, wenn erfolgreich entfernt, False sonst
        """
        if action_name in self.action_callbacks:
            del self.action_callbacks[action_name]
            logger.debug(f"Aktion entfernt: {action_name}")
            return True
        
        return False
    
    def handle_keypress(self, key: str, modifiers: Optional[List[KeyModifier]] = None, 
                       context: Optional[KeyContext] = None) -> bool:
        """
        Behandelt einen Tastendruck.
        
        Args:
            key: Gedrückte Taste
            modifiers: Liste von Modifikatoren
            context: Aktueller Kontext
            
        Returns:
            True, wenn die Tastenkombination verarbeitet wurde, False sonst
        """
        if modifiers is None:
            modifiers = []
        if context is None:
            context = self.context
        
        # Erstelle ein temporäres KeyBinding-Objekt für die Suche
        temp_binding = KeyBinding(key=key, modifiers=modifiers, context=context)
        binding_key = self._generate_binding_key(temp_binding)
        
        # Suche nach der Tastenkombination
        binding = self.keybindings.get(binding_key)
        
        # Wenn nicht gefunden, suche auch im globalen Kontext
        if not binding and context != KeyContext.GLOBAL:
            temp_binding.context = KeyContext.GLOBAL
            global_binding_key = self._generate_binding_key(temp_binding)
            binding = self.keybindings.get(global_binding_key)
        
        # Wenn eine Tastenkombination gefunden wurde und aktiv ist
        if binding and binding.enabled:
            return self._execute_binding(binding)
        
        return False
    
    def _execute_binding(self, binding: KeyBinding) -> bool:
        """
        Führt eine Tastenkombination aus.
        
        Args:
            binding: KeyBinding-Objekt
            
        Returns:
            True, wenn erfolgreich ausgeführt, False sonst
        """
        try:
            # Überprüfe, ob eine benutzerdefinierte Aktion vorhanden ist
            if binding.custom_action:
                binding.custom_action()
                logger.debug(f"Benutzerdefinierte Aktion ausgeführt: {binding.action}")
                return True
            
            # Überprüfe, ob eine registrierte Aktion vorhanden ist
            if binding.action in self.action_callbacks:
                callback = self.action_callbacks[binding.action]
                callback()
                logger.debug(f"Aktion ausgeführt: {binding.action}")
                return True
            
            # Wenn keine Aktion gefunden wurde, gib False zurück
            logger.debug(f"Keine Aktion für Tastenkombination gefunden: {binding.action}")
            return False
            
        except Exception as e:
            logger.error(f"Fehler beim Ausführen der Tastenkombination {binding.action}: {e}")
            return False
    
    def set_context(self, context: KeyContext):
        """
        Setzt den aktuellen Kontext.
        
        Args:
            context: Neuer Kontext
        """
        self.context = context
        logger.debug(f"Kontext geändert: {context.value}")
    
    def get_keybindings_for_context(self, context: Optional[KeyContext] = None) -> List[KeyBinding]:
        """
        Gibt die Tastenkombinationen für einen bestimmten Kontext zurück.
        
        Args:
            context: Kontext (standardmäßig der aktuelle Kontext)
            
        Returns:
            Liste von KeyBinding-Objekten
        """
        if context is None:
            context = self.context
        
        bindings = [
            binding for binding in self.keybindings.values()
            if binding.context == context or binding.context == KeyContext.GLOBAL
        ]
        
        return bindings
    
    def customize_keybinding(self, action: str, new_key: str, 
                           new_modifiers: Optional[List[KeyModifier]] = None,
                           context: Optional[KeyContext] = None) -> bool:
        """
        Passt eine Tastenkombination an.
        
        Args:
            action: Name der Aktion
            new_key: Neue Taste
            new_modifiers: Neue Modifikatoren
            context: Kontext
            
        Returns:
            True, wenn erfolgreich angepasst, False sonst
        """
        if new_modifiers is None:
            new_modifiers = []
        if context is None:
            context = self.context
        
        # Suche nach der vorhandenen Tastenkombination
        existing_binding = None
        existing_binding_key = None
        
        for key, binding in self.keybindings.items():
            if binding.action == action and binding.context == context:
                existing_binding = binding
                existing_binding_key = key
                break
        
        if not existing_binding:
            logger.warning(f"Tastenkombination für Aktion {action} nicht gefunden")
            return False
        
        # Erstelle eine neue Tastenkombination
        new_binding = KeyBinding(
            key=new_key,
            modifiers=new_modifiers,
            action=action,
            context=context,
            enabled=existing_binding.enabled,
            description=existing_binding.description,
            custom_action=existing_binding.custom_action
        )
        
        # Entferne die alte Tastenkombination
        if existing_binding_key:
            del self.keybindings[existing_binding_key]
        
        # Registriere die neue Tastenkombination
        self.register_keybinding(new_binding)
        
        # Speichere die benutzerdefinierten Tastenkombinationen
        self._save_custom_keybindings()
        
        logger.info(f"Tastenkombination angepasst: {action} -> {new_key}")
        return True
    
    def reset_to_default(self, action: str, context: Optional[KeyContext] = None) -> bool:
        """
        Setzt eine Tastenkombination auf den Standardwert zurück.
        
        Args:
            action: Name der Aktion
            context: Kontext
            
        Returns:
            True, wenn erfolgreich zurückgesetzt, False sonst
        """
        if context is None:
            context = self.context
        
        # Suche nach der benutzerdefinierten Tastenkombination
        custom_binding_key = None
        for key, binding in self.keybindings.items():
            if binding.action == action and binding.context == context and not binding.action.startswith("default_"):
                custom_binding_key = key
                break
        
        # Entferne die benutzerdefinierte Tastenkombination
        if custom_binding_key:
            del self.keybindings[custom_binding_key]
        
        # Speichere die benutzerdefinierten Tastenkombinationen
        self._save_custom_keybindings()
        
        logger.info(f"Tastenkombination auf Standard zurückgesetzt: {action}")
        return True
    
    def list_all_keybindings(self) -> Dict[str, List[KeyBinding]]:
        """
        Listet alle Tastenkombinationen gruppiert nach Kontext auf.
        
        Returns:
            Dictionary mit Kontexten als Schlüssel und Listen von KeyBinding-Objekten als Werte
        """
        grouped_bindings = {}
        
        for binding in self.keybindings.values():
            context = binding.context.value
            if context not in grouped_bindings:
                grouped_bindings[context] = []
            grouped_bindings[context].append(binding)
        
        return grouped_bindings


# Globale Instanz
_keybinding_manager: Optional[CustomKeybindingManager] = None

def get_keybinding_manager() -> CustomKeybindingManager:
    """
    Gibt die globale Instanz des CustomKeybindingManagers zurück.
    
    Returns:
        Instanz von CustomKeybindingManager
    """
    global _keybinding_manager
    if _keybinding_manager is None:
        _keybinding_manager = CustomKeybindingManager()
    return _keybinding_manager

def register_keybinding(binding: KeyBinding):
    """
    Registriert eine neue Tastenkombination.
    
    Args:
        binding: KeyBinding-Objekt
    """
    manager = get_keybinding_manager()
    manager.register_keybinding(binding)

def handle_keypress(key: str, modifiers: Optional[List[KeyModifier]] = None, 
                   context: Optional[KeyContext] = None) -> bool:
    """
    Behandelt einen Tastendruck.
    
    Args:
        key: Gedrückte Taste
        modifiers: Liste von Modifikatoren
        context: Aktueller Kontext
        
    Returns:
        True, wenn die Tastenkombination verarbeitet wurde, False sonst
    """
    manager = get_keybinding_manager()
    return manager.handle_keypress(key, modifiers, context)

def bind_action(action_name: str, callback: Callable):
    """
    Bindet eine Aktion an eine Callback-Funktion.
    
    Args:
        action_name: Name der Aktion
        callback: Callback-Funktion
    """
    manager = get_keybinding_manager()
    manager.bind_action(action_name, callback)

def customize_keybinding(action: str, new_key: str, 
                        new_modifiers: Optional[List[KeyModifier]] = None,
                        context: Optional[KeyContext] = None) -> bool:
    """
    Passt eine Tastenkombination an.
    
    Args:
        action: Name der Aktion
        new_key: Neue Taste
        new_modifiers: Neue Modifikatoren
        context: Kontext
        
    Returns:
        True, wenn erfolgreich angepasst, False sonst
    """
    manager = get_keybinding_manager()
    return manager.customize_keybinding(action, new_key, new_modifiers, context)

def reset_keybinding_to_default(action: str, context: Optional[KeyContext] = None) -> bool:
    """
    Setzt eine Tastenkombination auf den Standardwert zurück.
    
    Args:
        action: Name der Aktion
        context: Kontext
        
    Returns:
        True, wenn erfolgreich zurückgesetzt, False sonst
    """
    manager = get_keybinding_manager()
    return manager.reset_to_default(action, context)

# Deutsche Übersetzungen für Tastenkombinationen
CUSTOM_KEYBINDINGS_TRANSLATIONS_DE = {
    "shortcut_quit": "Programm beenden",
    "shortcut_help": "Hilfe anzeigen",
    "shortcut_search": "Suche starten",
    "shortcut_download": "Download starten",
    "shortcut_pause": "Downloads pausieren/fortsetzen",
    "shortcut_config": "Einstellungen anzeigen",
    "confirm": "Bestätigen",
    "cancel": "Abbrechen",
    "toggle_selection": "Auswahl umschalten",
    "navigate_up": "Nach oben navigieren",
    "navigate_down": "Nach unten navigieren",
    "navigate_left": "Nach links navigieren",
    "navigate_right": "Nach rechts navigieren",
    "filter_results": "Ergebnisse filtern",
    "refresh_search": "Suche aktualisieren",
    "select_all": "Alle auswählen",
    "select_none": "Keine auswählen",
    "invert_selection": "Auswahl umkehren"
}