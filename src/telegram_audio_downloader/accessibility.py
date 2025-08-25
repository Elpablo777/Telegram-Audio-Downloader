"""
Barrierefreiheit für den Telegram Audio Downloader.
"""

from typing import Optional, Dict, Any, Callable
from enum import Enum
from dataclasses import dataclass, field
import time

from rich.console import Console
from rich.text import Text
from rich.style import Style

from .logging_config import get_logger
from .i18n import _, Language

logger = get_logger(__name__)
console = Console()


class AccessibilityFeature(Enum):
    """Enumeration der verfügbaren Barrierefreiheitsfunktionen."""
    SCREEN_READER = "screen_reader"
    HIGH_CONTRAST = "high_contrast"
    LARGE_TEXT = "large_text"
    KEYBOARD_NAVIGATION = "keyboard_navigation"
    AUDIO_FEEDBACK = "audio_feedback"
    BRAILLE_SUPPORT = "braille_support"
    CUSTOM_COLORS = "custom_colors"
    REDUCED_MOTION = "reduced_motion"


class ScreenReaderMode(Enum):
    """Enumeration der Screenreader-Modi."""
    OFF = "off"
    VERBOSE = "verbose"
    CONCISE = "concise"
    SUMMARY = "summary"


@dataclass
class AccessibilitySettings:
    """Datenklasse für Barrierefreiheitseinstellungen."""
    screen_reader_mode: ScreenReaderMode = ScreenReaderMode.OFF
    high_contrast: bool = False
    large_text: bool = False
    keyboard_navigation: bool = True
    audio_feedback: bool = False
    braille_support: bool = False
    custom_colors: bool = False
    reduced_motion: bool = False
    custom_color_scheme: Dict[str, str] = field(default_factory=dict)
    focus_indicators: bool = True
    keyboard_shortcuts: bool = True
    text_to_speech_enabled: bool = False
    text_to_speech_rate: float = 1.0  # 0.5 bis 2.0
    text_to_speech_volume: float = 1.0  # 0.0 bis 1.0


class AccessibilityManager:
    """Klasse zur Verwaltung von Barrierefreiheitsfunktionen."""
    
    def __init__(self):
        """Initialisiert den AccessibilityManager."""
        self.console = console
        self.settings = AccessibilitySettings()
        self.screen_reader_buffer = []
        self.last_spoken = ""
        self.focus_elements = []
        self.current_focus_index = 0
    
    def enable_feature(self, feature: AccessibilityFeature):
        """
        Aktiviert eine Barrierefreiheitsfunktion.
        
        Args:
            feature: Zu aktivierende Funktion
        """
        if feature == AccessibilityFeature.SCREEN_READER:
            self.settings.screen_reader_mode = ScreenReaderMode.VERBOSE
            self._speak(_("screen_reader_enabled"))
        elif feature == AccessibilityFeature.HIGH_CONTRAST:
            self.settings.high_contrast = True
            self._speak(_("high_contrast_enabled"))
        elif feature == AccessibilityFeature.LARGE_TEXT:
            self.settings.large_text = True
            self._speak(_("large_text_enabled"))
        elif feature == AccessibilityFeature.AUDIO_FEEDBACK:
            self.settings.audio_feedback = True
            self._speak(_("audio_feedback_enabled"))
        elif feature == AccessibilityFeature.BRAILLE_SUPPORT:
            self.settings.braille_support = True
            self._speak(_("braille_support_enabled"))
        elif feature == AccessibilityFeature.CUSTOM_COLORS:
            self.settings.custom_colors = True
            self._speak(_("custom_colors_enabled"))
        elif feature == AccessibilityFeature.REDUCED_MOTION:
            self.settings.reduced_motion = True
            self._speak(_("reduced_motion_enabled"))
        
        logger.debug(f"Barrierefreiheitsfunktion aktiviert: {feature.value}")
    
    def disable_feature(self, feature: AccessibilityFeature):
        """
        Deaktiviert eine Barrierefreiheitsfunktion.
        
        Args:
            feature: Zu deaktivierende Funktion
        """
        if feature == AccessibilityFeature.SCREEN_READER:
            self.settings.screen_reader_mode = ScreenReaderMode.OFF
            self._speak(_("screen_reader_disabled"))
        elif feature == AccessibilityFeature.HIGH_CONTRAST:
            self.settings.high_contrast = False
            self._speak(_("high_contrast_disabled"))
        elif feature == AccessibilityFeature.LARGE_TEXT:
            self.settings.large_text = False
            self._speak(_("large_text_disabled"))
        elif feature == AccessibilityFeature.AUDIO_FEEDBACK:
            self.settings.audio_feedback = False
            self._speak(_("audio_feedback_disabled"))
        elif feature == AccessibilityFeature.BRAILLE_SUPPORT:
            self.settings.braille_support = False
            self._speak(_("braille_support_disabled"))
        elif feature == AccessibilityFeature.CUSTOM_COLORS:
            self.settings.custom_colors = False
            self._speak(_("custom_colors_disabled"))
        elif feature == AccessibilityFeature.REDUCED_MOTION:
            self.settings.reduced_motion = False
            self._speak(_("reduced_motion_disabled"))
        
        logger.debug(f"Barrierefreiheitsfunktion deaktiviert: {feature.value}")
    
    def set_screen_reader_mode(self, mode: ScreenReaderMode):
        """
        Setzt den Screenreader-Modus.
        
        Args:
            mode: Screenreader-Modus
        """
        self.settings.screen_reader_mode = mode
        mode_names = {
            ScreenReaderMode.OFF: _("screen_reader_off"),
            ScreenReaderMode.VERBOSE: _("screen_reader_verbose"),
            ScreenReaderMode.CONCISE: _("screen_reader_concise"),
            ScreenReaderMode.SUMMARY: _("screen_reader_summary")
        }
        self._speak(_("screen_reader_mode_set").format(mode=mode_names.get(mode, mode.value)))
        logger.debug(f"Screenreader-Modus gesetzt: {mode.value}")
    
    def set_text_to_speech_settings(self, rate: Optional[float] = None, volume: Optional[float] = None):
        """
        Setzt die Text-to-Speech-Einstellungen.
        
        Args:
            rate: Sprechgeschwindigkeit (0.5 bis 2.0)
            volume: Lautstärke (0.0 bis 1.0)
        """
        if rate is not None:
            self.settings.text_to_speech_rate = max(0.5, min(2.0, rate))
        if volume is not None:
            self.settings.text_to_speech_volume = max(0.0, min(1.0, volume))
        
        self._speak(_("tts_settings_updated"))
        logger.debug(f"Text-to-Speech-Einstellungen aktualisiert: rate={self.settings.text_to_speech_rate}, volume={self.settings.text_to_speech_volume}")
    
    def speak(self, text: str, interrupt: bool = True):
        """
        Spricht einen Text mit dem Screenreader.
        
        Args:
            text: Zu sprechender Text
            interrupt: Ob vorherige Ausgaben unterbrochen werden sollen
        """
        if self.settings.screen_reader_mode == ScreenReaderMode.OFF:
            return
        
        self._speak(text, interrupt)
    
    def _speak(self, text: str, interrupt: bool = True):
        """
        Interne Methode zum Sprechen von Text.
        
        Args:
            text: Zu sprechender Text
            interrupt: Ob vorherige Ausgaben unterbrochen werden sollen
        """
        # Vermeide das mehrfache Sprechen desselben Textes
        if text == self.last_spoken and not interrupt:
            return
        
        self.last_spoken = text
        
        # Add text to screen reader buffer
        if interrupt:
            self.screen_reader_buffer = [text]
        else:
            self.screen_reader_buffer.append(text)
        
        # In a real implementation, the text-to-speech API would be called here
        # For this example, we simply print the text to the console
        if self.settings.screen_reader_mode != ScreenReaderMode.OFF:
            mode_prefix = {
                ScreenReaderMode.VERBOSE: "[SR-V]",
                ScreenReaderMode.CONCISE: "[SR-C]",
                ScreenReaderMode.SUMMARY: "[SR-S]"
            }.get(self.settings.screen_reader_mode, "[SR]")
            
            print(f"{mode_prefix} {text}")
    
    def describe_element(self, element_type: str, element_name: str, state: str = "", additional_info: str = ""):
        """
        Describes a UI element for screen readers.
        
        Args:
            element_type: Type of element (button, link, input, etc.)
            element_name: Name of element
            state: State of element (selected, disabled, etc.)
            additional_info: Additional information
        """
        if self.settings.screen_reader_mode == ScreenReaderMode.OFF:
            return
        
        # Erstelle eine Beschreibung basierend auf dem Modus
        if self.settings.screen_reader_mode == ScreenReaderMode.VERBOSE:
            description = f"{element_type} {element_name}"
            if state:
                description += f" {state}"
            if additional_info:
                description += f" {additional_info}"
        elif self.settings.screen_reader_mode == ScreenReaderMode.CONCISE:
            description = f"{element_name}"
            if state:
                description += f" {state}"
        else:  # SUMMARY
            description = f"{element_name}"
        
        self._speak(description)
    
    def announce_state_change(self, state: str):
        """
        Announces a state change.
        
        Args:
            state: New state
        """
        if self.settings.screen_reader_mode != ScreenReaderMode.OFF:
            self._speak(state, interrupt=True)
    
    def add_focus_element(self, element: str, callback: Optional[Callable] = None):
        """
        Adds an element to keyboard navigation.
        
        Args:
            element: Name of element
            callback: Function called when activated
        """
        self.focus_elements.append((element, callback))
        logger.debug(f"Fokuselement hinzugefügt: {element}")
    
    def clear_focus_elements(self):
        """Löscht alle Fokuselemente."""
        self.focus_elements.clear()
        self.current_focus_index = 0
        logger.debug("Fokuselemente gelöscht")
    
    def move_focus_next(self):
        """Bewegt den Fokus zum nächsten Element."""
        if not self.focus_elements:
            return
        
        self.current_focus_index = (self.current_focus_index + 1) % len(self.focus_elements)
        element_name, _ = self.focus_elements[self.current_focus_index]
        
        if self.settings.screen_reader_mode != ScreenReaderMode.OFF:
            self._speak(_("focus_moved_to").format(element=element_name))
        
        logger.debug(f"Fokus bewegt zu: {element_name}")
    
    def move_focus_previous(self):
        """Bewegt den Fokus zum vorherigen Element."""
        if not self.focus_elements:
            return
        
        self.current_focus_index = (self.current_focus_index - 1) % len(self.focus_elements)
        element_name, _ = self.focus_elements[self.current_focus_index]
        
        if self.settings.screen_reader_mode != ScreenReaderMode.OFF:
            self._speak(_("focus_moved_to").format(element=element_name))
        
        logger.debug(f"Fokus bewegt zu: {element_name}")
    
    def activate_focused_element(self):
        """Aktiviert das aktuell fokussierte Element."""
        if not self.focus_elements:
            return
        
        element_name, callback = self.focus_elements[self.current_focus_index]
        
        if self.settings.screen_reader_mode != ScreenReaderMode.OFF:
            self._speak(_("element_activated").format(element=element_name))
        
        if callback:
            callback()
        
        logger.debug(f"Element aktiviert: {element_name}")
    
    def get_accessible_style(self) -> Style:
        """
        Returns an accessible style.
        
        Returns:
            Rich Style object
        """
        if self.settings.high_contrast:
            # Use high contrast colors
            return Style(color="white", bgcolor="black", bold=True)
        elif self.settings.custom_colors and self.settings.custom_color_scheme:
            # Use custom colors
            primary_color = self.settings.custom_color_scheme.get("primary", "blue")
            return Style(color=primary_color)
        else:
            # Default style
            return Style()
    
    def get_accessible_text(self, text: str) -> Text:
        """
        Returns accessible text.
        
        Args:
            text: Input text
            
        Returns:
            Rich Text object
        """
        accessible_text = Text(text)
        style = self.get_accessible_style()
        accessible_text.stylize(style)
        
        # Enlarge when large text is enabled
        if self.settings.large_text:
            # In a real implementation, we would change the font size
            # For Rich text, we can use bold font
            accessible_text.stylize("bold")
        
        return accessible_text
    
    def provide_audio_feedback(self, event_type: str):
        """
        Provides audio feedback for an event.
        
        Args:
            event_type: Type of event (success, error, warning, navigation, etc.)
        """
        if not self.settings.audio_feedback:
            return
        
        # In a real implementation, we would play sounds here
        # For this example, we output a description
        feedback_sounds = {
            "success": _("sound_success"),
            "error": _("sound_error"),
            "warning": _("sound_warning"),
            "navigation": _("sound_navigation"),
            "selection": _("sound_selection")
        }
        
        sound_description = feedback_sounds.get(event_type, _("sound_generic"))
        print(f"[AUDIO] {sound_description}")
        logger.debug(f"Akustisches Feedback: {event_type}")


# Globale Instanz
_accessibility_manager: Optional[AccessibilityManager] = None

def get_accessibility_manager() -> AccessibilityManager:
    """
    Returns the global instance of AccessibilityManager.
    
    Returns:
        Instance of AccessibilityManager
    """
    global _accessibility_manager
    if _accessibility_manager is None:
        _accessibility_manager = AccessibilityManager()
    return _accessibility_manager

def enable_accessibility_feature(feature: AccessibilityFeature):
    """
    Enables an accessibility feature.
    
    Args:
        feature: Feature to enable
    """
    manager = get_accessibility_manager()
    manager.enable_feature(feature)

def disable_accessibility_feature(feature: AccessibilityFeature):
    """
    Disables an accessibility feature.
    
    Args:
        feature: Feature to disable
    """
    manager = get_accessibility_manager()
    manager.disable_feature(feature)

def speak(text: str, interrupt: bool = True):
    """
    Speaks text with the screen reader.
    
    Args:
        text: Text to speak
        interrupt: Whether to interrupt previous outputs
    """
    manager = get_accessibility_manager()
    manager.speak(text, interrupt)

def describe_element(element_type: str, element_name: str, state: str = "", additional_info: str = ""):
    """
    Describes a UI element for screen readers.
    
    Args:
        element_type: Type of element
        element_name: Name of element
        state: State of element
        additional_info: Additional information
    """
    manager = get_accessibility_manager()
    manager.describe_element(element_type, element_name, state, additional_info)

def announce_state_change(state: str):
    """
    Announces a state change.
    
    Args:
        state: New state
    """
    manager = get_accessibility_manager()
    manager.announce_state_change(state)

# Initialize translations for accessibility
def init_accessibility_translations():
    """Initializes translations for accessibility features."""
    # This function would load the appropriate translations
    # for accessibility features in a real implementation
    pass


# Deutsche Übersetzungen für Barrierefreiheit
ACCESSIBILITY_TRANSLATIONS_DE = {
    "screen_reader_enabled": "Screenreader aktiviert",
    "high_contrast_enabled": "Hoher Kontrast aktiviert",
    "large_text_enabled": "Große Schrift aktiviert",
    "audio_feedback_enabled": "Akustisches Feedback aktiviert",
    "braille_support_enabled": "Braille-Unterstützung aktiviert",
    "custom_colors_enabled": "Benutzerdefinierte Farben aktiviert",
    "reduced_motion_enabled": "Reduzierte Bewegung aktiviert",
    "screen_reader_disabled": "Screenreader deaktiviert",
    "high_contrast_disabled": "Hoher Kontrast deaktiviert",
    "large_text_disabled": "Große Schrift deaktiviert",
    "audio_feedback_disabled": "Akustisches Feedback deaktiviert",
    "braille_support_disabled": "Braille-Unterstützung deaktiviert",
    "custom_colors_disabled": "Benutzerdefinierte Farben deaktiviert",
    "reduced_motion_disabled": "Reduzierte Bewegung deaktiviert",
    "screen_reader_off": "Aus",
    "screen_reader_verbose": "Ausführlich",
    "screen_reader_concise": "Kurz",
    "screen_reader_summary": "Zusammenfassung",
    "screen_reader_mode_set": "Screenreader-Modus auf {mode} gesetzt",
    "tts_settings_updated": "Text-to-Speech-Einstellungen aktualisiert",
    "focus_moved_to": "Fokus bewegt zu {element}",
    "element_activated": "Element {element} aktiviert",
    "sound_success": "Erfolgston",
    "sound_error": "Fehlerklang",
    "sound_warning": "Warnklang",
    "sound_navigation": "Navigationston",
    "sound_selection": "Auswahlsound",
    "sound_generic": "Allgemeiner Sound"
}