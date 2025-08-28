"""
Tests für die erweiterte Suche im Telegram Audio Downloader.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from typing import List

from src.telegram_audio_downloader.advanced_search import (
    SearchType,
    SearchOperator,
    SearchFilter,
    SearchQuery,
    SearchResult,
    AdvancedSearchEngine,
    get_search_engine,
    perform_search,
    get_search_suggestions
)
from src.telegram_audio_downloader.models import AudioFile, TelegramGroup


class TestSearchType:
    """Testfälle für die SearchType-Enumeration."""
    
    def test_search_type_values(self):
        """Testet die Werte der SearchType-Enumeration."""
        assert SearchType.AUDIO_FILES.value == "audio_files"
        assert SearchType.DOWNLOADED_FILES.value == "downloaded_files"
        assert SearchType.TELEGRAM_GROUPS.value == "telegram_groups"
        assert SearchType.ALL.value == "all"


class TestSearchOperator:
    """Testfälle für die SearchOperator-Enumeration."""
    
    def test_search_operator_values(self):
        """Testet die Werte der SearchOperator-Enumeration."""
        assert SearchOperator.AND.value == "and"
        assert SearchOperator.OR.value == "or"
        assert SearchOperator.NOT.value == "not"


class TestSearchFilter:
    """Testfälle für die SearchFilter-Datenklasse."""
    
    def test_initialization(self):
        """Testet die Initialisierung der SearchFilter-Klasse."""
        filter_obj = SearchFilter(
            field="title",
            operator="contains",
            value="test"
        )
        
        assert filter_obj.field == "title"
        assert filter_obj.operator == "contains"
        assert filter_obj.value == "test"
        assert filter_obj.search_type == SearchOperator.AND


class TestSearchQuery:
    """Testfälle für die SearchQuery-Datenklasse."""
    
    def test_initialization(self):
        """Testet die Initialisierung der SearchQuery-Klasse."""
        query = SearchQuery(
            terms=["test", "search"],
            search_type=SearchType.ALL,
            case_sensitive=True,
            fuzzy_search=True,
            limit=50
        )
        
        assert query.terms == ["test", "search"]
        assert query.search_type == SearchType.ALL
        assert query.case_sensitive == True
        assert query.fuzzy_search == True
        assert query.limit == 50
        assert query.offset == 0
        assert query.sort_by is None
        assert query.sort_order == "asc"


class TestSearchResult:
    """Testfälle für die SearchResult-Datenklasse."""
    
    def test_initialization(self):
        """Testet die Initialisierung der SearchResult-Klasse."""
        result = SearchResult(
            items=["item1", "item2"],
            total_count=2,
            query_time=0.5,
            search_type=SearchType.ALL
        )
        
        assert result.items == ["item1", "item2"]
        assert result.total_count == 2
        assert result.query_time == 0.5
        assert result.search_type == SearchType.ALL
        assert result.highlighted_terms == []


class TestAdvancedSearchEngine:
    """Testfälle für die AdvancedSearchEngine-Klasse."""
    
    def test_initialization(self):
        """Testet die Initialisierung der AdvancedSearchEngine."""
        engine = AdvancedSearchEngine()
        
        assert engine is not None
        assert hasattr(engine, 'logger')
        assert hasattr(engine, 'search_history')
        assert engine.search_history == []
    
    def test_search_empty_query(self):
        """Testet die Suche mit einer leeren Anfrage."""
        engine = AdvancedSearchEngine()
        
        # Erstelle eine leere Suchanfrage
        query = SearchQuery()
        
        # Führe die Suche durch
        result = engine.search(query)
        
        assert isinstance(result, SearchResult)
        assert result.items == []
        assert result.total_count == 0
        assert result.query_time >= 0
        assert result.search_type == SearchType.ALL
    
    def test_search_with_terms(self):
        """Testet die Suche mit Suchbegriffen."""
        engine = AdvancedSearchEngine()
        
        # Erstelle eine Suchanfrage mit Begriffen
        query = SearchQuery(
            terms=["test", "search"],
            search_type=SearchType.DOWNLOADED_FILES
        )
        
        # Mock die _search_downloaded_files Methode
        with patch.object(engine, '_search_downloaded_files', return_value=[Mock(), Mock()]) as mock_search:
            # Führe die Suche durch
            result = engine.search(query)
            
            # Überprüfe die Ergebnisse
            assert isinstance(result, SearchResult)
            assert len(result.items) == 2
            assert result.total_count == 2
            assert result.search_type == SearchType.DOWNLOADED_FILES
            mock_search.assert_called_once_with(query)
    
    @patch('src.telegram_audio_downloader.advanced_search.AudioFile')
    def test_search_downloaded_files(self, mock_audio_file):
        """Testet die Suche in heruntergeladenen Dateien."""
        engine = AdvancedSearchEngine()
        
        # Erstelle eine Suchanfrage
        query = SearchQuery(
            terms=["test"],
            search_type=SearchType.DOWNLOADED_FILES
        )
        
        # Mock die Datenbankabfrage
        mock_select = Mock()
        mock_select.where.return_value = mock_select
        mock_select.__iter__ = Mock(return_value=iter([Mock(), Mock()]))
        mock_audio_file.select.return_value = mock_select
        
        # Führe die Suche durch
        results = engine._search_downloaded_files(query)
        
        assert len(results) == 2
        mock_audio_file.select.assert_called_once()
    
    @patch('src.telegram_audio_downloader.advanced_search.TelegramGroup')
    def test_search_telegram_groups(self, mock_telegram_group):
        """Testet die Suche in Telegram-Gruppen."""
        engine = AdvancedSearchEngine()
        
        # Erstelle eine Suchanfrage
        query = SearchQuery(
            terms=["test"],
            search_type=SearchType.TELEGRAM_GROUPS
        )
        
        # Mock die Datenbankabfrage
        mock_select = Mock()
        mock_select.where.return_value = mock_select
        mock_select.__iter__ = Mock(return_value=iter([Mock(), Mock()]))
        mock_telegram_group.select.return_value = mock_select
        
        # Führe die Suche durch
        results = engine._search_telegram_groups(query)
        
        assert len(results) == 2
        mock_telegram_group.select.assert_called_once()
    
    def test_sort_results(self):
        """Testet das Sortieren von Suchergebnissen."""
        engine = AdvancedSearchEngine()
        
        # Erstelle Testdaten
        item1 = Mock()
        item1.title = "Zebra"
        item2 = Mock()
        item2.title = "Apple"
        item3 = Mock()
        item3.title = "Banana"
        
        results = [item1, item2, item3]
        
        # Sortiere aufsteigend
        sorted_results = engine._sort_results(results, "title", "asc")
        assert sorted_results[0].title == "Apple"
        assert sorted_results[1].title == "Banana"
        assert sorted_results[2].title == "Zebra"
        
        # Sortiere absteigend
        sorted_results = engine._sort_results(results, "title", "desc")
        assert sorted_results[0].title == "Zebra"
        assert sorted_results[1].title == "Banana"
        assert sorted_results[2].title == "Apple"
    
    def test_get_search_suggestions(self):
        """Testet das Abrufen von Suchvorschlägen."""
        engine = AdvancedSearchEngine()
        
        # Mock die AudioFile-Abfragen
        with patch('src.telegram_audio_downloader.advanced_search.AudioFile') as mock_audio_file:
            # Mock die select-Methoden
            mock_title_select = Mock()
            mock_title_select.distinct.return_value = mock_title_select
            mock_title_select.__iter__ = Mock(return_value=iter([
                Mock(title="Rock"), Mock(title="Jazz"), Mock(title="Classical")
            ]))
            
            mock_performer_select = Mock()
            mock_performer_select.distinct.return_value = mock_performer_select
            mock_performer_select.__iter__ = Mock(return_value=iter([
                Mock(performer="Queen"), Mock(performer="Miles Davis"), Mock(performer="Beethoven")
            ]))
            
            mock_filename_select = Mock()
            mock_filename_select.distinct.return_value = mock_filename_select
            mock_filename_select.__iter__ = Mock(return_value=iter([
                Mock(file_name="song1.mp3"), Mock(file_name="song2.mp3"), Mock(file_name="song3.mp3")
            ]))
            
            mock_audio_file.select.side_effect = [
                mock_title_select,
                mock_performer_select,
                mock_filename_select
            ]
            
            # Hole Suchvorschläge
            suggestions = engine.get_search_suggestions("Ro", max_suggestions=5)
            
            assert isinstance(suggestions, list)
            # Die genauen Vorschläge hängen von der fuzzy matching Implementierung ab
    
    def test_get_search_history(self):
        """Testet das Abrufen der Suchhistorie."""
        engine = AdvancedSearchEngine()
        
        # Füge einige Einträge zur Historie hinzu
        engine.search_history.append({"query": "test1", "result": "result1"})
        engine.search_history.append({"query": "test2", "result": "result2"})
        
        # Hole die gesamte Historie
        history = engine.get_search_history()
        assert len(history) == 2
        
        # Hole nur die letzten Einträge
        limited_history = engine.get_search_history(limit=1)
        assert len(limited_history) == 1
    
    def test_clear_search_history(self):
        """Testet das Löschen der Suchhistorie."""
        engine = AdvancedSearchEngine()
        
        # Füge einige Einträge zur Historie hinzu
        engine.search_history.append({"query": "test1", "result": "result1"})
        assert len(engine.search_history) == 1
        
        # Lösche die Historie
        engine.clear_search_history()
        assert len(engine.search_history) == 0
    
    def test_get_faceted_search_results(self):
        """Testet das Abrufen von facettierten Suchergebnissen."""
        engine = AdvancedSearchEngine()
        
        # Erstelle eine Suchanfrage
        query = SearchQuery(terms=["test"])
        
        # Mock die search Methode
        mock_result = SearchResult(
            items=[
                Mock(category="rock", mime_type="audio/mp3", file_size=5000000),
                Mock(category="jazz", mime_type="audio/flac", file_size=15000000)
            ]
        )
        
        with patch.object(engine, 'search', return_value=mock_result):
            # Hole die facettierten Ergebnisse
            facets = engine.get_faceted_search_results(query)
            
            assert isinstance(facets, dict)
            assert "categories" in facets
            assert "file_types" in facets
            assert "size_ranges" in facets


class TestGlobalFunctions:
    """Testfälle für die globalen Funktionen."""
    
    def test_get_search_engine_singleton(self):
        """Testet, dass die AdvancedSearchEngine als Singleton funktioniert."""
        engine1 = get_search_engine()
        engine2 = get_search_engine()
        
        assert engine1 is engine2
    
    def test_perform_search_global(self):
        """Testet die Durchführung einer Suche über die globale Funktion."""
        # Erstelle eine Suchanfrage
        query = SearchQuery(terms=["test"])
        
        # Mock die AdvancedSearchEngine
        with patch('src.telegram_audio_downloader.advanced_search.AdvancedSearchEngine') as mock_engine_class:
            mock_engine = Mock()
            mock_engine_class.return_value = mock_engine
            mock_engine.search.return_value = SearchResult(items=[], total_count=0, query_time=0.1)
            
            # Führe die Suche durch
            result = perform_search(query)
            
            assert isinstance(result, SearchResult)
            mock_engine.search.assert_called_once_with(query)
    
    def test_get_search_suggestions_global(self):
        """Testet das Abrufen von Suchvorschlägen über die globale Funktion."""
        # Mock die AdvancedSearchEngine
        with patch('src.telegram_audio_downloader.advanced_search.AdvancedSearchEngine') as mock_engine_class:
            mock_engine = Mock()
            mock_engine_class.return_value = mock_engine
            mock_engine.get_search_suggestions.return_value = ["suggestion1", "suggestion2"]
            
            # Hole Suchvorschläge
            suggestions = get_search_suggestions("test")
            
            assert suggestions == ["suggestion1", "suggestion2"]
            mock_engine.get_search_suggestions.assert_called_once_with("test", 10)


if __name__ == "__main__":
    pytest.main([__file__])