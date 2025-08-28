"""
Tests für die kontextbezogene Hilfe im Telegram Audio Downloader.
"""

import pytest
from unittest.mock import Mock, patch

from src.telegram_audio_downloader.contextual_help import (
    HelpContext,
    HelpEntry,
    ContextualHelpManager,
    get_help_manager,
    show_help,
    search_help,
    add_help_entry
)


class TestHelpContext:
    """Testfälle für die HelpContext-Enumeration."""
    
    def test_help_context_values(self):
        """Testet die Werte der HelpContext-Enumeration."""
        assert HelpContext.GLOBAL.value == "global"
        assert HelpContext.SEARCH.value == "search"
        assert HelpContext.DOWNLOAD.value == "download"
        assert HelpContext.SETTINGS.value == "settings"
        assert HelpContext.INTERACTIVE.value == "interactive"
        assert HelpContext.PROGRESS.value == "progress"
        assert HelpContext.CATEGORIES.value == "categories"


class TestHelpEntry:
    """Testfälle für die HelpEntry-Datenklasse."""
    
    def test_help_entry_initialization(self):
        """Testet die Initialisierung der HelpEntry-Klasse."""
        entry = HelpEntry(
            title="Test Entry",
            description="This is a test entry",
            usage="Use this for testing",
            examples=["example 1", "example 2"],
            related_commands=["cmd1", "cmd2"],
            context=HelpContext.GLOBAL
        )
        
        assert entry.title == "Test Entry"
        assert entry.description == "This is a test entry"
        assert entry.usage == "Use this for testing"
        assert entry.examples == ["example 1", "example 2"]
        assert entry.related_commands == ["cmd1", "cmd2"]
        assert entry.context == HelpContext.GLOBAL


class TestContextualHelpManager:
    """Testfälle für die ContextualHelpManager-Klasse."""
    
    def test_initialization(self):
        """Testet die Initialisierung des ContextualHelpManagers."""
        manager = ContextualHelpManager()
        
        assert manager is not None
        assert hasattr(manager, 'console')
        assert hasattr(manager, 'help_entries')
        # Überprüfe, ob Standardhilfeeinträge registriert wurden
        assert len(manager.help_entries) > 0
    
    def test_add_help_entry(self):
        """Testet das Hinzufügen eines Hilfeeintrags."""
        manager = ContextualHelpManager()
        initial_count = len(manager.help_entries)
        
        # Füge einen neuen Hilfeeintrag hinzu
        manager.add_help_entry(
            key="test_entry",
            title="Test Entry",
            description="This is a test entry"
        )
        
        # Überprüfe, ob der Eintrag hinzugefügt wurde
        assert len(manager.help_entries) == initial_count + 1
        assert "test_entry" in manager.help_entries
        
        entry = manager.help_entries["test_entry"]
        assert entry.title == "Test Entry"
        assert entry.description == "This is a test entry"
        assert entry.context == HelpContext.GLOBAL
    
    def test_remove_help_entry(self):
        """Testet das Entfernen eines Hilfeeintrags."""
        manager = ContextualHelpManager()
        
        # Füge einen Hilfeeintrag hinzu
        manager.add_help_entry("remove_test", "Remove Test", "This is a remove test")
        assert "remove_test" in manager.help_entries
        
        # Entferne den Hilfeeintrag
        manager.remove_help_entry("remove_test")
        assert "remove_test" not in manager.help_entries
    
    def test_get_help_entry(self):
        """Testet das Abrufen eines Hilfeeintrags."""
        manager = ContextualHelpManager()
        
        # Füge einen Hilfeeintrag hinzu
        manager.add_help_entry("get_test", "Get Test", "This is a get test")
        
        # Hole den Hilfeeintrag
        entry = manager.get_help_entry("get_test")
        assert entry is not None
        assert entry.title == "Get Test"
        
        # Versuche, einen nicht existierenden Eintrag zu holen
        non_existent = manager.get_help_entry("non_existent")
        assert non_existent is None
    
    def test_get_help_for_context(self):
        """Testet das Abrufen von Hilfeeinträgen für einen Kontext."""
        manager = ContextualHelpManager()
        
        # Füge Hilfeeinträge für verschiedene Kontexte hinzu
        manager.add_help_entry("global_test", "Global Test", "Global test entry", context=HelpContext.GLOBAL)
        manager.add_help_entry("search_test", "Search Test", "Search test entry", context=HelpContext.SEARCH)
        manager.add_help_entry("download_test", "Download Test", "Download test entry", context=HelpContext.DOWNLOAD)
        
        # Hole Hilfeeinträge für den Suchkontext
        search_entries = manager.get_help_for_context(HelpContext.SEARCH)
        # Sollte den globalen Eintrag und den Such-Eintrag enthalten
        assert len(search_entries) >= 2
        assert any(entry.title == "Global Test" for entry in search_entries)
        assert any(entry.title == "Search Test" for entry in search_entries)
    
    def test_search_help(self):
        """Testet die Suche nach Hilfeeinträgen."""
        manager = ContextualHelpManager()
        
        # Füge einige Hilfeeinträge hinzu
        manager.add_help_entry(
            "search_test_1",
            "Search Test Entry 1",
            "This entry contains the word testing",
            examples=["test example 1", "another test"]
        )
        
        manager.add_help_entry(
            "search_test_2",
            "Another Entry",
            "This entry does not contain the search word"
        )
        
        # Suche nach "test"
        results = manager.search_help("test")
        assert len(results) >= 1
        assert any("search_test_1" in str(result) for result in results)
    
    def test_show_help_general(self):
        """Testet die Anzeige der allgemeinen Hilfe."""
        manager = ContextualHelpManager()
        
        # Teste, ob die allgemeine Hilfe angezeigt werden kann (ohne Exception)
        try:
            manager.show_help()
            # Wenn keine Exception geworfen wird, ist der Test erfolgreich
            assert True
        except Exception as e:
            pytest.fail(f"Fehler beim Anzeigen der allgemeinen Hilfe: {e}")
    
    def test_show_help_for_context(self):
        """Testet die Anzeige von Hilfe für einen Kontext."""
        manager = ContextualHelpManager()
        
        # Teste, ob die Hilfe für einen Kontext angezeigt werden kann (ohne Exception)
        try:
            manager.show_help(context=HelpContext.SEARCH)
            # Wenn keine Exception geworfen wird, ist der Test erfolgreich
            assert True
        except Exception as e:
            pytest.fail(f"Fehler beim Anzeigen der Hilfe für einen Kontext: {e}")
    
    def test_show_help_for_key(self):
        """Testet die Anzeige von Hilfe für einen spezifischen Schlüssel."""
        manager = ContextualHelpManager()
        
        # Teste, ob die Hilfe für einen spezifischen Schlüssel angezeigt werden kann (ohne Exception)
        try:
            manager.show_help(key="welcome")
            # Wenn keine Exception geworfen wird, ist der Test erfolgreich
            assert True
        except Exception as e:
            pytest.fail(f"Fehler beim Anzeigen der Hilfe für einen Schlüssel: {e}")
    
    def test_show_help_non_existent_key(self):
        """Testet die Anzeige von Hilfe für einen nicht existierenden Schlüssel."""
        manager = ContextualHelpManager()
        
        # Teste, ob die Hilfe für einen nicht existierenden Schlüssel angezeigt werden kann (ohne Exception)
        try:
            manager.show_help(key="non_existent")
            # Wenn keine Exception geworfen wird, ist der Test erfolgreich
            assert True
        except Exception as e:
            pytest.fail(f"Fehler beim Anzeigen der Hilfe für einen nicht existierenden Schlüssel: {e}")


class TestGlobalFunctions:
    """Testfälle für die globalen Funktionen."""
    
    def test_get_help_manager_singleton(self):
        """Testet, dass der ContextualHelpManager als Singleton funktioniert."""
        manager1 = get_help_manager()
        manager2 = get_help_manager()
        
        assert manager1 is manager2
    
    def test_show_help_global(self):
        """Testet die Anzeige von Hilfe über die globale Funktion."""
        # Teste, ob die Hilfe angezeigt werden kann (ohne Exception)
        try:
            show_help()
            # Wenn keine Exception geworfen wird, ist der Test erfolgreich
            assert True
        except Exception as e:
            pytest.fail(f"Fehler beim Anzeigen der Hilfe: {e}")
    
    def test_search_help_global(self):
        """Testet die Suche nach Hilfe über die globale Funktion."""
        # Füge einen Hilfeeintrag hinzu
        add_help_entry("global_search_test", "Global Search Test", "This is for global search testing")
        
        # Suche nach dem Eintrag
        results = search_help("global search")
        assert len(results) >= 1
    
    def test_add_help_entry_global(self):
        """Testet das Hinzufügen eines Hilfeeintrags über die globale Funktion."""
        # Füge einen Hilfeeintrag hinzu
        add_help_entry("global_add_test", "Global Add Test", "This is for global add testing")
        
        # Überprüfe, ob der Eintrag hinzugefügt wurde
        manager = get_help_manager()
        assert "global_add_test" in manager.help_entries


if __name__ == "__main__":
    pytest.main([__file__])