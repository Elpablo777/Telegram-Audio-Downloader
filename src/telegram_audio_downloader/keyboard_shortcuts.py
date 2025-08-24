"""
Tastaturkürzel-Verwaltung für den Telegram Audio Downloader.
"""

import logging
import signal
import sys
from typing import Dict, Callable, Optional
from enum import Enum

logger = logging.getLogger(__name__)

class Shortcut(Enum):
    """Verfügbare Tastaturkürzel."""
    CANCEL = "ctrl+c"
    PAUSE = "space"
    HELP = "f1"
    COMPLETE = "ctrl+d"
    RESTART = "ctrl+r"
    QUIT = "q"

class KeyboardShortcuts:
    """Klasse zur Verwaltung von Tastaturkürzeln."""
    
    def __init__(self):
        """Initialisiert die Tastaturkürzel-Verwaltung."""
        self.shortcuts: Dict[Shortcut, Callable] = {}
        self.is_paused = False
        self.setup_signal_handlers()
        
    def setup_signal_handlers(self) -> None:
        """Richtet die Signal-Handler für Systemkürzel ein."""
        # SIGINT (Ctrl+C) für Abbruch
        signal.signal(signal.SIGINT, self._handle_sigint)
        
        # SIGTERM für ordnungsgemäßen Shutdown
        signal.signal(signal.SIGTERM, self._handle_sigterm)
        
    def _handle_sigint(self, signum, frame) -> None:
        """Behandelt SIGINT (Ctrl+C)."""
        logger.info("SIGINT empfangen (Ctrl+C)")
        if Shortcut.CANCEL in self.shortcuts:
            try:
                self.shortcuts[Shortcut.CANCEL]()
            except Exception as e:
                logger.error(f"Fehler beim Ausführen der Abbruch-Aktion: {e}")
        else:
            # Standardverhalten: Programm beenden
            print("\nProgramm durch Benutzer abgebrochen.")
            sys.exit(0)
            
    def _handle_sigterm(self, signum, frame) -> None:
        """Behandelt SIGTERM."""
        logger.info("SIGTERM empfangen")
        if Shortcut.QUIT in self.shortcuts:
            try:
                self.shortcuts[Shortcut.QUIT]()
            except Exception as e:
                logger.error(f"Fehler beim Ausführen der Quit-Aktion: {e}")
        else:
            # Standardverhalten: Programm beenden
            sys.exit(0)
    
    def register_shortcut(self, shortcut: Shortcut, action: Callable) -> None:
        """
        Registriert eine Aktion für ein Tastaturkürzel.
        
        Args:
            shortcut: Das Tastaturkürzel
            action: Die auszuführende Aktion
        """
        self.shortcuts[shortcut] = action
        logger.debug(f"Tastaturkürzel {shortcut.value} registriert")
        
    def unregister_shortcut(self, shortcut: Shortcut) -> None:
        """
        Entfernt ein Tastaturkürzel.
        
        Args:
            shortcut: Das zu entfernende Tastaturkürzel
        """
        if shortcut in self.shortcuts:
            del self.shortcuts[shortcut]
            logger.debug(f"Tastaturkürzel {shortcut.value} entfernt")
            
    def handle_keypress(self, key: str) -> None:
        """
        Verarbeitet einen Tastendruck.
        
        Args:
            key: Der gedrückte Schlüssel
        """
        # Mapping von Tasten zu Shortcuts
        key_mapping = {
            ' ': Shortcut.PAUSE,
            '\x03': Shortcut.CANCEL,  # Ctrl+C
            '\x04': Shortcut.COMPLETE,  # Ctrl+D
            '\x12': Shortcut.RESTART,  # Ctrl+R
            'q': Shortcut.QUIT,
            'Q': Shortcut.QUIT,
        }
        
        # Spezielle Behandlung für F1
        if key == '\x00' or key == '\xe0':  # Windows: \x00 oder \xe0 für Spezialtasten
            # Wir müssen auf das nächste Zeichen warten, um die tatsächliche Taste zu erkennen
            # In einer echten Implementierung würden wir hier eine Bibliothek wie keyboard verwenden
            pass
        elif key in key_mapping:
            shortcut = key_mapping[key]
            if shortcut in self.shortcuts:
                try:
                    self.shortcuts[shortcut]()
                except Exception as e:
                    logger.error(f"Fehler beim Ausführen der Aktion für {shortcut.value}: {e}")
            else:
                # Standardverhalten für einige Shortcuts
                if shortcut == Shortcut.PAUSE:
                    self._toggle_pause()
                elif shortcut == Shortcut.QUIT:
                    self._quit()
                    
    def _toggle_pause(self) -> None:
        """Schaltet den Pausenstatus um."""
        self.is_paused = not self.is_paused
        status = "pausiert" if self.is_paused else "fortgesetzt"
        logger.info(f"Download {status}")
        print(f"\nDownload {status}. Drücken Sie die Leertaste erneut zum Fortsetzen.")
        
    def _quit(self) -> None:
        """Beendet das Programm."""
        logger.info("Programm wird beendet")
        print("\nProgramm wird beendet...")
        sys.exit(0)
        
    def is_download_paused(self) -> bool:
        """
        Prüft, ob der Download pausiert ist.
        
        Returns:
            True, wenn pausiert, False sonst
        """
        return self.is_paused

# Globale Instanz
_keyboard_shortcuts: Optional[KeyboardShortcuts] = None

def get_keyboard_shortcuts() -> KeyboardShortcuts:
    """
    Gibt die globale Instanz der Tastaturkürzel-Verwaltung zurück.
    
    Returns:
        Instanz von KeyboardShortcuts
    """
    global _keyboard_shortcuts
    if _keyboard_shortcuts is None:
        _keyboard_shortcuts = KeyboardShortcuts()
    return _keyboard_shortcuts

# Hilfsfunktionen für die Verwendung außerhalb der Klasse
def register_shortcut(shortcut: Shortcut, action: Callable) -> None:
    """
    Registriert eine Aktion für ein Tastaturkürzel.
    
    Args:
        shortcut: Das Tastaturkürzel
        action: Die auszuführende Aktion
    """
    keyboard = get_keyboard_shortcuts()
    keyboard.register_shortcut(shortcut, action)

def unregister_shortcut(shortcut: Shortcut) -> None:
    """
    Entfernt ein Tastaturkürzel.
    
    Args:
        shortcut: Das zu entfernende Tastaturkürzel
    """
    keyboard = get_keyboard_shortcuts()
    keyboard.unregister_shortcut(shortcut)

def handle_keypress(key: str) -> None:
    """
    Verarbeitet einen Tastendruck.
    
    Args:
        key: Der gedrückte Schlüssel
    """
    keyboard = get_keyboard_shortcuts()
    keyboard.handle_keypress(key)

def is_download_paused() -> bool:
    """
    Prüft, ob der Download pausiert ist.
    
    Returns:
        True, wenn pausiert, False sonst
    """
    keyboard = get_keyboard_shortcuts()
    return keyboard.is_download_paused()