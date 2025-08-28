"""
Tests für die automatische Vervollständigung im Telegram Audio Downloader.
"""

import pytest
from unittest.mock import Mock, patch

from src.telegram_audio_downloader.auto_completion import (
    CompletionType,
    CompletionItem,
    CompletionContext,
    AutoCompletionManager,
    get_completion_manager,
    get_completions,
    add_completion_source,
    register_custom_provider,
    add_to_completion_history,
    clear_completion_history
)


class TestCompletionType:
    """Testfälle für die CompletionType-Enumeration."""
    
    def test_completion_type_values(self):
        """Testet die Werte der CompletionType-Enumeration."""
        assert CompletionType.COMMAND.value == "command"
        assert CompletionType.FILE_NAME.value == "file_name"
        assert CompletionType.GROUP_NAME.value == "group_name"
        assert CompletionType.ARTIST.value == "artist"
        assert CompletionType.GENRE.value == "genre"
        assert CompletionType.TAG.value == "tag"
        assert CompletionType.SEARCH_HISTORY.value == "search_history"
        assert CompletionType.CUSTOM.value == "custom"


class TestCompletionItem:
    """Testfälle für die CompletionItem-Datenklasse."""
    
    def test_initialization(self):
        """Testet die Initialisierung der CompletionItem-Klasse."""
        item = CompletionItem(
            text="test",
            display_text="Test Item",
            description="A test completion item",
            type=CompletionType.COMMAND,
            priority=5,
            icon="🧪"
        )
        
        assert item.text == "test"
        assert item.display_text == "Test Item"
        assert item.description == "A test completion item"
        assert item.type == CompletionType.COMMAND
        assert item.priority == 5
        assert item.icon == "🧪"
        assert item.metadata == {}


class TestCompletionContext:
    """Testfälle für die CompletionContext-Datenklasse."""
    
    def test_initialization(self):
        """Testet die Initialisierung der CompletionContext-Klasse."""
        context = CompletionContext(
            current_input="test",
            cursor_position=4,
            context_type="search",
            available_types=[CompletionType.COMMAND, CompletionType.GENRE],
            max_suggestions=5,
            case_sensitive=True,
            fuzzy_matching=False
        )
        
        assert context.current_input == "test"
        assert context.cursor_position == 4
        assert context.context_type == "search"
        assert context.available_types == [CompletionType.COMMAND, CompletionType.GENRE]
        assert context.max_suggestions == 5
        assert context.case_sensitive == True
        assert context.fuzzy_matching == False


class TestAutoCompletionManager:
    """Testfälle für die AutoCompletionManager-Klasse."""
    
    def test_initialization(self):
        """Testet die Initialisierung des AutoCompletionManagers."""
        manager = AutoCompletionManager()
        
        assert manager is not None
        assert hasattr(manager, 'console')
        assert isinstance(manager.completion_sources, dict)
        assert isinstance(manager.custom_providers, dict)
        assert isinstance(manager.history, list)
        
        # Überprüfe, ob Standardvervollständigungen initialisiert wurden
        assert CompletionType.COMMAND in manager.completion_sources
        assert CompletionType.GENRE in manager.completion_sources
    
    def test_add_completion_source(self):
        """Testet das Hinzufügen einer Vervollständigungsquelle."""
        manager = AutoCompletionManager()
        
        items = [
            CompletionItem(text="test1", type=CompletionType.CUSTOM),
            CompletionItem(text="test2", type=CompletionType.CUSTOM)
        ]
        
        manager.add_completion_source(CompletionType.CUSTOM, items)
        
        assert CompletionType.CUSTOM in manager.completion_sources
        assert len(manager.completion_sources[CompletionType.CUSTOM]) >= 2
    
    def test_register_custom_provider(self):
        """Testet das Registrieren eines benutzerdefinierten Anbieters."""
        manager = AutoCompletionManager()
        
        def test_provider(context):
            return [CompletionItem(text="custom", type=CompletionType.CUSTOM)]
        
        manager.register_custom_provider("test_provider", test_provider)
        
        assert "test_provider" in manager.custom_providers
        assert manager.custom_providers["test_provider"] is test_provider
    
    def test_get_completions(self):
        """Testet das Abrufen von Vervollständigungen."""
        manager = AutoCompletionManager()
        
        context = CompletionContext(
            current_input="d",
            cursor_position=1,
            available_types=[CompletionType.COMMAND]
        )
        
        completions = manager.get_completions(context)
        
        # Es sollten einige Befehle gefunden werden, die mit "d" beginnen
        assert len(completions) > 0
        
        # Überprüfe, ob alle zurückgegebenen Elemente CompletionItem-Instanzen sind
        for completion in completions:
            assert isinstance(completion, CompletionItem)
    
    def test_match_completions_exact(self):
        """Testet das exakte Matching von Vervollständigungen."""
        manager = AutoCompletionManager()
        
        context = CompletionContext(
            current_input="down",
            cursor_position=4,
            case_sensitive=False,
            fuzzy_matching=False
        )
        
        completions = manager.get_completions(context)
        
        # Es sollte mindestens das "download"-Kommando gefunden werden
        assert len(completions) > 0
        assert any("down" in (c.text.lower() or c.display_text.lower()) for c in completions)
    
    def test_match_completions_fuzzy(self):
        """Testet das Fuzzy-Matching von Vervollständigungen."""
        manager = AutoCompletionManager()
        
        context = CompletionContext(
            current_input="dwn",
            cursor_position=3,
            case_sensitive=False,
            fuzzy_matching=True
        )
        
        completions = manager.get_completions(context)
        
        # Es sollte mindestens das "download"-Kommando gefunden werden
        assert len(completions) > 0
    
    def test_add_to_history(self):
        """Testet das Hinzufügen zu der Vervollständigungshistorie."""
        manager = AutoCompletionManager()
        
        manager.add_to_history("test_search")
        manager.add_to_history("another_search")
        
        assert len(manager.history) == 2
        assert manager.history[0] == "another_search"
        assert manager.history[1] == "test_search"
    
    def test_get_history_completions(self):
        """Testet das Abrufen von Historien-Vervollständigungen."""
        manager = AutoCompletionManager()
        
        manager.add_to_history("test_search")
        manager.add_to_history("another_search")
        
        context = CompletionContext(
            current_input="test",
            cursor_position=4
        )
        
        history_completions = manager.get_history_completions(context)
        
        assert len(history_completions) > 0
        assert any(c.text == "test_search" for c in history_completions)
    
    def test_clear_history(self):
        """Testet das Löschen der Vervollständigungshistorie."""
        manager = AutoCompletionManager()
        
        manager.add_to_history("test_search")
        assert len(manager.history) == 1
        
        manager.clear_history()
        assert len(manager.history) == 0
    
    def test_custom_provider_integration(self):
        """Testet die Integration von benutzerdefinierten Anbietern."""
        manager = AutoCompletionManager()
        
        def custom_provider(context):
            return [CompletionItem(text="custom_item", type=CompletionType.CUSTOM)]
        
        manager.register_custom_provider("test_provider", custom_provider)
        
        context = CompletionContext(
            current_input="custom",
            cursor_position=6
        )
        
        completions = manager.get_completions(context)
        
        # Es sollte das benutzerdefinierte Element gefunden werden
        assert any(c.text == "custom_item" for c in completions)
    
    def test_custom_provider_error_handling(self):
        """Testet die Fehlerbehandlung bei benutzerdefinierten Anbietern."""
        manager = AutoCompletionManager()
        
        def faulty_provider(context):
            raise Exception("Test error")
        
        manager.register_custom_provider("faulty_provider", faulty_provider)
        
        context = CompletionContext(
            current_input="test",
            cursor_position=4
        )
        
        # Dies sollte keine Exception werfen, auch wenn der Anbieter fehlschlägt
        completions = manager.get_completions(context)
        
        # Die anderen Vervollständigungen sollten trotzdem funktionieren
        assert isinstance(completions, list)
    
    def test_get_completion_stats(self):
        """Testet das Abrufen von Vervollständigungsstatistiken."""
        manager = AutoCompletionManager()
        
        stats = manager.get_completion_stats()
        
        # Es sollten Statistiken für verschiedene Typen vorhanden sein
        assert isinstance(stats, dict)
        assert "total" in stats
        assert "history_items" in stats
        assert stats["history_items"] == 0


class TestGlobalFunctions:
    """Testfälle für die globalen Funktionen."""
    
    def test_get_completion_manager_singleton(self):
        """Testet, dass der AutoCompletionManager als Singleton funktioniert."""
        manager1 = get_completion_manager()
        manager2 = get_completion_manager()
        
        assert manager1 is manager2
    
    def test_get_completions_global(self):
        """Testet das Abrufen von Vervollständigungen über die globale Funktion."""
        context = CompletionContext(
            current_input="d",
            cursor_position=1
        )
        
        completions = get_completions(context)
        
        assert isinstance(completions, list)
        assert len(completions) > 0
    
    def test_add_completion_source_global(self):
        """Testet das Hinzufügen einer Vervollständigungsquelle über die globale Funktion."""
        items = [
            CompletionItem(text="global_test", type=CompletionType.CUSTOM)
        ]
        
        # Füge eine Quelle hinzu
        add_completion_source(CompletionType.CUSTOM, items)
        
        # Überprüfe, ob sie hinzugefügt wurde
        manager = get_completion_manager()
        assert CompletionType.CUSTOM in manager.completion_sources
        assert any(c.text == "global_test" for c in manager.completion_sources[CompletionType.CUSTOM])
    
    def test_register_custom_provider_global(self):
        """Testet das Registrieren eines benutzerdefinierten Anbieters über die globale Funktion."""
        def test_provider(context):
            return [CompletionItem(text="global_custom", type=CompletionType.CUSTOM)]
        
        register_custom_provider("global_test_provider", test_provider)
        
        manager = get_completion_manager()
        assert "global_test_provider" in manager.custom_providers
    
    def test_add_to_completion_history_global(self):
        """Testet das Hinzufügen zu der Vervollständigungshistorie über die globale Funktion."""
        # Lösche zuerst die Historie
        clear_completion_history()
        
        # Füge etwas zur Historie hinzu
        add_to_completion_history("global_test_search")
        
        manager = get_completion_manager()
        assert len(manager.history) == 1
        assert manager.history[0] == "global_test_search"
    
    def test_clear_completion_history_global(self):
        """Testet das Löschen der Vervollständigungshistorie über die globale Funktion."""
        # Füge etwas zur Historie hinzu
        add_to_completion_history("test_item_1")
        add_to_completion_history("test_item_2")
        
        manager = get_completion_manager()
        assert len(manager.history) == 2
        
        # Lösche die Historie
        clear_completion_history()
        
        assert len(manager.history) == 0


if __name__ == "__main__":
    pytest.main([__file__])