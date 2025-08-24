"""
Tests für die Tastaturkürzel im Telegram Audio Downloader.
"""

import pytest
from unittest.mock import Mock, patch
import sys

from src.telegram_audio_downloader.keyboard_shortcuts import (
    Shortcut,
    KeyboardShortcutManager,
    get_keyboard_shortcut_manager,
    register_shortcut,
    unregister_shortcut,
    handle_keypress,
    set_shortcut_context,
    show_shortcut_help
)


class TestShortcut:
    """Testfälle für die Shortcut-Datenklasse."""
    
    def test_shortcut_initialization(self):
        """Testet die Initialisierung der Shortcut-Klasse."""
        # Erstelle eine Mock-Funktion für die Aktion
        mock_action = Mock()
        
        shortcut = Shortcut(
            key="ctrl+s",
            description="Speichern",
            action=mock_action,
            context="editor",
            enabled=True
        )
        
        assert shortcut.key == "ctrl+s"
        assert shortcut.description == "Speichern"
        assert shortcut.action == mock_action
        assert shortcut.context == "editor"
        assert shortcut.enabled == True


class TestKeyboardShortcutManager:
    """Testfälle für die KeyboardShortcutManager-Klasse."""
    
    def test_initialization(self):
        """Testet die Initialisierung des KeyboardShortcutManagers."""
        manager = KeyboardShortcutManager()
        
        assert manager is not None
        assert hasattr(manager, 'shortcuts')
        assert hasattr(manager, 'context')
        assert manager.context == "global"
        # Überprüfe, ob Standardkürzel registriert wurden
        assert len(manager.shortcuts) > 0
    
    def test_register_shortcut(self):
        """Testet das Registrieren eines Tastaturkürzels."""
        manager = KeyboardShortcutManager()
        initial_count = len(manager.shortcuts)
        
        # Erstelle eine Mock-Funktion für die Aktion
        mock_action = Mock()
        
        # Registriere ein neues Tastaturkürzel
        manager.register_shortcut(
            key="ctrl+t",
            description="Test",
            action=mock_action
        )
        
        # Überprüfe, ob das Kürzel hinzugefügt wurde
        assert len(manager.shortcuts) == initial_count + 1
        assert "ctrl+t" in manager.shortcuts
        
        shortcut = manager.shortcuts["ctrl+t"]
        assert shortcut.key == "ctrl+t"
        assert shortcut.description == "Test"
        assert shortcut.action == mock_action
        assert shortcut.context == "global"
        assert shortcut.enabled == True
    
    def test_unregister_shortcut(self):
        """Testet das Entfernen eines Tastaturkürzels."""
        manager = KeyboardShortcutManager()
        
        # Registriere ein Tastaturkürzel
        mock_action = Mock()
        manager.register_shortcut("ctrl+u", "Unregister Test", mock_action)
        assert "ctrl+u" in manager.shortcuts
        
        # Entferne das Tastaturkürzel
        manager.unregister_shortcut("ctrl+u")
        assert "ctrl+u" not in manager.shortcuts
    
    def test_enable_disable_shortcut(self):
        """Testet das Aktivieren und Deaktivieren von Tastaturkürzeln."""
        manager = KeyboardShortcutManager()
        
        # Registriere ein Tastaturkürzel
        mock_action = Mock()
        manager.register_shortcut("ctrl+e", "Enable/Disable Test", mock_action)
        
        # Deaktiviere das Tastaturkürzel
        manager.disable_shortcut("ctrl+e")
        assert manager.shortcuts["ctrl+e"].enabled == False
        
        # Aktiviere das Tastaturkürzel
        manager.enable_shortcut("ctrl+e")
        assert manager.shortcuts["ctrl+e"].enabled == True
    
    def test_set_context(self):
        """Testet das Setzen des Kontexts."""
        manager = KeyboardShortcutManager()
        
        # Setze den Kontext
        manager.set_context("search")
        assert manager.context == "search"
    
    def test_get_shortcuts_for_context(self):
        """Testet das Abrufen von Tastaturkürzeln für einen Kontext."""
        manager = KeyboardShortcutManager()
        
        # Registriere Tastaturkürzel für verschiedene Kontexte
        mock_action = Mock()
        manager.register_shortcut("ctrl+a", "Global Action", mock_action, "global")
        manager.register_shortcut("ctrl+b", "Search Action", mock_action, "search")
        manager.register_shortcut("ctrl+c", "Download Action", mock_action, "download")
        
        # Hole Tastaturkürzel für den globalen Kontext
        global_shortcuts = manager.get_shortcuts_for_context("global")
        assert "ctrl+a" in global_shortcuts
        assert "ctrl+b" not in global_shortcuts  # Nur globale Kürzel
        
        # Hole Tastaturkürzel für den Suchkontext
        search_shortcuts = manager.get_shortcuts_for_context("search")
        assert "ctrl+a" in search_shortcuts  # Globale Kürzel sind immer enthalten
        assert "ctrl+b" in search_shortcuts
        assert "ctrl+c" not in search_shortcuts
    
    def test_handle_keypress(self):
        """Testet die Behandlung eines Tastendrucks."""
        manager = KeyboardShortcutManager()
        
        # Erstelle eine Mock-Funktion für die Aktion
        mock_action = Mock()
        
        # Registriere ein Tastaturkürzel
        manager.register_shortcut("ctrl+h", "Handle Test", mock_action)
        
        # Behandle einen Tastendruck
        result = manager.handle_keypress("ctrl+h")
        
        # Überprüfe, ob die Aktion ausgeführt wurde
        assert result == True
        mock_action.assert_called_once()
    
    def test_handle_keypress_disabled(self):
        """Testet die Behandlung eines deaktivierten Tastaturkürzels."""
        manager = KeyboardShortcutManager()
        
        # Erstelle eine Mock-Funktion für die Aktion
        mock_action = Mock()
        
        # Registriere und deaktiviere ein Tastaturkürzel
        manager.register_shortcut("ctrl+d", "Disabled Test", mock_action)
        manager.disable_shortcut("ctrl+d")
        
        # Behandle einen Tastendruck
        result = manager.handle_keypress("ctrl+d")
        
        # Überprüfe, ob die Aktion nicht ausgeführt wurde
        assert result == False
        mock_action.assert_not_called()
    
    def test_handle_keypress_wrong_context(self):
        """Testet die Behandlung eines Tastaturkürzels im falschen Kontext."""
        manager = KeyboardShortcutManager()
        manager.set_context("search")
        
        # Erstelle eine Mock-Funktion für die Aktion
        mock_action = Mock()
        
        # Registriere ein Tastaturkürzel für einen anderen Kontext
        manager.register_shortcut("ctrl+w", "Wrong Context Test", mock_action, "download")
        
        # Behandle einen Tastendruck
        result = manager.handle_keypress("ctrl+w")
        
        # Überprüfe, ob die Aktion nicht ausgeführt wurde
        assert result == False
        mock_action.assert_not_called()
    
    def test_show_help(self):
        """Testet die Anzeige der Hilfe."""
        manager = KeyboardShortcutManager()
        
        # Füge einige Tastaturkürzel hinzu
        mock_action = Mock()
        manager.register_shortcut("ctrl+t", "Test Action", mock_action, "test")
        
        # Teste, ob die Hilfe angezeigt werden kann (ohne Exception)
        try:
            manager.show_help()
            # Wenn keine Exception geworfen wird, ist der Test erfolgreich
            assert True
        except Exception as e:
            pytest.fail(f"Fehler beim Anzeigen der Hilfe: {e}")


class TestGlobalFunctions:
    """Testfälle für die globalen Funktionen."""
    
    def test_get_keyboard_shortcut_manager_singleton(self):
        """Testet, dass der KeyboardShortcutManager als Singleton funktioniert."""
        manager1 = get_keyboard_shortcut_manager()
        manager2 = get_keyboard_shortcut_manager()
        
        assert manager1 is manager2
    
    def test_register_shortcut_global(self):
        """Testet das Registrieren eines Tastaturkürzels über die globale Funktion."""
        # Registriere ein Tastaturkürzel
        mock_action = Mock()
        register_shortcut("ctrl+g", "Global Register Test", mock_action)
        
        # Überprüfe, ob das Kürzel registriert wurde
        manager = get_keyboard_shortcut_manager()
        assert "ctrl+g" in manager.shortcuts
    
    def test_unregister_shortcut_global(self):
        """Testet das Entfernen eines Tastaturkürzels über die globale Funktion."""
        # Registriere ein Tastaturkürzel
        mock_action = Mock()
        register_shortcut("ctrl+r", "Global Unregister Test", mock_action)
        
        # Entferne das Tastaturkürzel
        unregister_shortcut("ctrl+r")
        
        # Überprüfe, ob das Kürzel entfernt wurde
        manager = get_keyboard_shortcut_manager()
        assert "ctrl+r" not in manager.shortcuts
    
    def test_handle_keypress_global(self):
        """Testet die Behandlung eines Tastendrucks über die globale Funktion."""
        # Registriere ein Tastaturkürzel
        mock_action = Mock()
        register_shortcut("ctrl+k", "Global Handle Test", mock_action)
        
        # Behandle einen Tastendruck
        result = handle_keypress("ctrl+k")
        
        # Überprüfe, ob die Aktion ausgeführt wurde
        assert result == True
        mock_action.assert_called_once()
    
    def test_set_shortcut_context_global(self):
        """Testet das Setzen des Kontexts über die globale Funktion."""
        # Setze den Kontext
        set_shortcut_context("global_test")
        
        # Überprüfe, ob der Kontext gesetzt wurde
        manager = get_keyboard_shortcut_manager()
        assert manager.context == "global_test"
    
    def test_show_shortcut_help_global(self):
        """Testet die Anzeige der Hilfe über die globale Funktion."""
        # Teste, ob die Hilfe angezeigt werden kann (ohne Exception)
        try:
            show_shortcut_help()
            # Wenn keine Exception geworfen wird, ist der Test erfolgreich
            assert True
        except Exception as e:
            pytest.fail(f"Fehler beim Anzeigen der Hilfe: {e}")


if __name__ == "__main__":
    pytest.main([__file__])