"""
Tests für die Tastaturkürzel-Verwaltung.
"""

import unittest
from unittest.mock import patch, MagicMock

from src.telegram_audio_downloader.keyboard_shortcuts import (
    KeyboardShortcuts, Shortcut
)

class TestKeyboardShortcuts(unittest.TestCase):
    """Tests für die KeyboardShortcuts-Klasse."""
    
    def setUp(self):
        """Erstellt eine Instanz der KeyboardShortcuts-Klasse."""
        self.keyboard = KeyboardShortcuts()
    
    def test_initialization(self):
        """Testet die Initialisierung der KeyboardShortcuts-Klasse."""
        self.assertIsInstance(self.keyboard, KeyboardShortcuts)
        # Wir testen nicht den is_paused-Status, da er durch Signal-Handler beeinflusst werden kann
        self.assertEqual(len(self.keyboard.shortcuts), 0)
    
    def test_register_shortcut(self):
        """Testet das Registrieren eines Tastaturkürzels."""
        action = MagicMock()
        self.keyboard.register_shortcut(Shortcut.CANCEL, action)
        self.assertIn(Shortcut.CANCEL, self.keyboard.shortcuts)
        self.assertEqual(self.keyboard.shortcuts[Shortcut.CANCEL], action)
    
    def test_unregister_shortcut(self):
        """Testet das Entfernen eines Tastaturkürzels."""
        action = MagicMock()
        self.keyboard.register_shortcut(Shortcut.CANCEL, action)
        self.assertIn(Shortcut.CANCEL, self.keyboard.shortcuts)
        
        self.keyboard.unregister_shortcut(Shortcut.CANCEL)
        self.assertNotIn(Shortcut.CANCEL, self.keyboard.shortcuts)
    
    def test_handle_keypress_quit(self):
        """Testet die Verarbeitung des Beenden-Tastaturkürzels."""
        with patch('sys.exit') as mock_exit:
            self.keyboard.handle_keypress('q')
            mock_exit.assert_called_once_with(0)

if __name__ == "__main__":
    unittest.main()