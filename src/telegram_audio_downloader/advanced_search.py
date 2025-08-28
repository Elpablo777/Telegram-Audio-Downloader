"""
Erweiterte Suche für den Telegram Audio Downloader.
"""

from typing import List, Optional, Dict, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import re
from fuzzywuzzy import fuzz, process

from telethon.tl.types import Document, DocumentAttributeAudio, Message

from .models import AudioFile, TelegramGroup
from .logging_config import get_logger
from .i18n import _

logger = get_logger(__name__)


class SearchType(Enum):
    """Enumeration der Suchtypen."""
    AUDIO_FILES = "audio_files"
    DOWNLOADED_FILES = "downloaded_files"
    TELEGRAM_GROUPS = "telegram_groups"
    ALL = "all"


class SearchOperator(Enum):
    """Enumeration der Suchoperatoren."""
    AND = "and"
    OR = "or"
    NOT = "not"


@dataclass
class SearchFilter:
    """Datenklasse für Suchfilter."""
    field: str
    operator: str
    value: Any
    search_type: SearchOperator = SearchOperator.AND


@dataclass
class SearchQuery:
    """Datenklasse für eine Suchanfrage."""
    terms: List[str] = field(default_factory=list)
    filters: List[SearchFilter] = field(default_factory=list)
    search_type: SearchType = SearchType.ALL
    case_sensitive: bool = False
    fuzzy_search: bool = False
    fuzzy_threshold: int = 80
    limit: Optional[int] = None
    offset: int = 0
    sort_by: Optional[str] = None
    sort_order: str = "asc"  # asc oder desc


@dataclass
class SearchResult:
    """Datenklasse für ein Suchergebnis."""
    items: List[Any] = field(default_factory=list)
    total_count: int = 0
    query_time: float = 0.0
    search_type: SearchType = SearchType.ALL
    highlighted_terms: List[str] = field(default_factory=list)


class AdvancedSearchEngine:
    """Klasse für die erweiterte Suche."""
    
    def __init__(self):
        """Initialisiert die AdvancedSearchEngine."""
        self.logger = get_logger(__name__ + ".AdvancedSearchEngine")
        self.search_history = []
    
    def search(self, query: SearchQuery) -> SearchResult:
        """
        Führt eine erweiterte Suche durch.
        
        Args:
            query: SearchQuery-Objekt
            
        Returns:
            SearchResult-Objekt
        """
        import time
        start_time = time.time()
        
        results = []
        highlighted_terms = []
        
        try:
            # Führe die Suche basierend auf dem Suchtyp durch
            if query.search_type in [SearchType.AUDIO_FILES, SearchType.ALL]:
                audio_results = self._search_audio_files(query)
                results.extend(audio_results)
                highlighted_terms.extend(self._extract_highlighted_terms(audio_results, query.terms))
            
            if query.search_type in [SearchType.DOWNLOADED_FILES, SearchType.ALL]:
                downloaded_results = self._search_downloaded_files(query)
                results.extend(downloaded_results)
                highlighted_terms.extend(self._extract_highlighted_terms(downloaded_results, query.terms))
            
            if query.search_type in [SearchType.TELEGRAM_GROUPS, SearchType.ALL]:
                group_results = self._search_telegram_groups(query)
                results.extend(group_results)
                highlighted_terms.extend(self._extract_highlighted_terms(group_results, query.terms))
            
            # Sortiere die Ergebnisse
            if query.sort_by:
                results = self._sort_results(results, query.sort_by, query.sort_order)
            
            # Wende Limit und Offset an
            if query.limit:
                results = results[query.offset:query.offset + query.limit]
            
            # Erstelle das Suchergebnis
            search_result = SearchResult(
                items=results,
                total_count=len(results),
                query_time=time.time() - start_time,
                search_type=query.search_type,
                highlighted_terms=list(set(highlighted_terms))  # Entferne Duplikate
            )
            
            # Füge zur Suchhistorie hinzu
            self.search_history.append({
                "query": query,
                "result": search_result,
                "timestamp": datetime.now()
            })
            
            self.logger.info(f"Suche abgeschlossen: {len(results)} Ergebnisse in {search_result.query_time:.2f}s")
            return search_result
            
        except Exception as e:
            self.logger.error(f"Fehler bei der Suche: {e}")
            return SearchResult(
                items=[],
                total_count=0,
                query_time=time.time() - start_time,
                search_type=query.search_type
            )
    
    def _search_audio_files(self, query: SearchQuery) -> List[Dict[str, Any]]:
        """
        Sucht nach Audiodateien in Telegram-Gruppen.
        
        Args:
            query: SearchQuery-Objekt
            
        Returns:
            Liste von Audiodatei-Informationen
        """
        # Diese Methode würde in einer echten Implementierung mit der Telegram-API interagieren
        # Für dieses Beispiel geben wir eine leere Liste zurück
        self.logger.debug("Suche nach Audiodateien in Telegram-Gruppen")
        return []
    
    def _search_downloaded_files(self, query: SearchQuery) -> List[AudioFile]:
        """
        Sucht in heruntergeladenen Dateien.
        
        Args:
            query: SearchQuery-Objekt
            
        Returns:
            Liste von AudioFile-Objekten
        """
        try:
            # Erstelle die Basisabfrage
            base_query = AudioFile.select()
            
            # Wende Textsuche an
            if query.terms:
                text_conditions = []
                for term in query.terms:
                    if query.fuzzy_search:
                        # Bei Fuzzy-Suche verwenden wir eine einfachere Bedingung
                        text_conditions.append(
                            (AudioFile.title.contains(term)) |
                            (AudioFile.performer.contains(term)) |
                            (AudioFile.file_name.contains(term))
                        )
                    else:
                        # Exakte Textsuche
                        if query.case_sensitive:
                            text_conditions.append(
                                (AudioFile.title.contains(term)) |
                                (AudioFile.performer.contains(term)) |
                                (AudioFile.file_name.contains(term))
                            )
                        else:
                            text_conditions.append(
                                (AudioFile.title.contains(term)) |
                                (AudioFile.performer.contains(term)) |
                                (AudioFile.file_name.contains(term))
                            )
                
                # Kombiniere die Textbedingungen
                if text_conditions:
                    combined_condition = text_conditions[0]
                    for condition in text_conditions[1:]:
                        if query.filters and any(f.operator == "or" for f in query.filters):
                            combined_condition |= condition
                        else:
                            combined_condition &= condition
                    base_query = base_query.where(combined_condition)
            
            # Wende Filter an
            for filter_obj in query.filters:
                if filter_obj.search_type == SearchOperator.AND:
                    base_query = self._apply_filter(base_query, filter_obj, AudioFile)
                # OR-Filter würden separat behandelt werden
            
            # Führe die Abfrage aus
            results = list(base_query)
            
            self.logger.debug(f"Suche in heruntergeladenen Dateien: {len(results)} Ergebnisse")
            return results
            
        except Exception as e:
            self.logger.error(f"Fehler bei der Suche in heruntergeladenen Dateien: {e}")
            return []
    
    def _search_telegram_groups(self, query: SearchQuery) -> List[TelegramGroup]:
        """
        Sucht in Telegram-Gruppen.
        
        Args:
            query: SearchQuery-Objekt
            
        Returns:
            Liste von TelegramGroup-Objekten
        """
        try:
            # Erstelle die Basisabfrage
            base_query = TelegramGroup.select()
            
            # Wende Textsuche an
            if query.terms:
                for term in query.terms:
                    base_query = base_query.where(
                        (TelegramGroup.title.contains(term)) |
                        (TelegramGroup.username.contains(term))
                    )
            
            # Wende Filter an
            for filter_obj in query.filters:
                if filter_obj.search_type == SearchOperator.AND:
                    base_query = self._apply_filter(base_query, filter_obj, TelegramGroup)
            
            # Führe die Abfrage aus
            results = list(base_query)
            
            self.logger.debug(f"Suche in Telegram-Gruppen: {len(results)} Ergebnisse")
            return results
            
        except Exception as e:
            self.logger.error(f"Fehler bei der Suche in Telegram-Gruppen: {e}")
            return []
    
    def _apply_filter(self, query, filter_obj: SearchFilter, model_class):
        """
        Wendet einen Filter auf eine Datenbankabfrage an.
        
        Args:
            query: Datenbankabfrage
            filter_obj: SearchFilter-Objekt
            model_class: Modellklasse
            
        Returns:
            Angepasste Datenbankabfrage
        """
        try:
            # Hole das Feld aus dem Modell
            if hasattr(model_class, filter_obj.field):
                field = getattr(model_class, filter_obj.field)
            else:
                self.logger.warning(f"Feld {filter_obj.field} nicht im Modell {model_class.__name__} gefunden")
                return query
            
            # Wende den Operator an
            if filter_obj.operator == "=":
                query = query.where(field == filter_obj.value)
            elif filter_obj.operator == "!=":
                query = query.where(field != filter_obj.value)
            elif filter_obj.operator == ">":
                query = query.where(field > filter_obj.value)
            elif filter_obj.operator == "<":
                query = query.where(field < filter_obj.value)
            elif filter_obj.operator == ">=":
                query = query.where(field >= filter_obj.value)
            elif filter_obj.operator == "<=":
                query = query.where(field <= filter_obj.value)
            elif filter_obj.operator == "contains":
                query = query.where(field.contains(filter_obj.value))
            elif filter_obj.operator == "in":
                if isinstance(filter_obj.value, list):
                    query = query.where(field.in_(filter_obj.value))
            elif filter_obj.operator == "not_in":
                if isinstance(filter_obj.value, list):
                    query = query.where(field.not_in(filter_obj.value))
            
            return query
            
        except Exception as e:
            self.logger.error(f"Fehler beim Anwenden des Filters: {e}")
            return query
    
    def _sort_results(self, results: List[Any], sort_by: str, sort_order: str) -> List[Any]:
        """
        Sortiert die Suchergebnisse.
        
        Args:
            results: Liste von Ergebnissen
            sort_by: Sortierfeld
            sort_order: Sortierreihenfolge (asc oder desc)
            
        Returns:
            Sortierte Liste von Ergebnissen
        """
        try:
            # Sortiere die Ergebnisse
            reverse = sort_order.lower() == "desc"
            
            # Verwende getattr mit einem Standardwert für die Sortierung
            sorted_results = sorted(
                results,
                key=lambda x: getattr(x, sort_by, ""),
                reverse=reverse
            )
            
            return sorted_results
            
        except Exception as e:
            self.logger.error(f"Fehler beim Sortieren der Ergebnisse: {e}")
            return results
    
    def _extract_highlighted_terms(self, results: List[Any], search_terms: List[str]) -> List[str]:
        """
        Extrahiert hervorgehobene Begriffe aus den Suchergebnissen.
        
        Args:
            results: Liste von Suchergebnissen
            search_terms: Suchbegriffe
            
        Returns:
            Liste von hervorgehobenen Begriffen
        """
        highlighted = []
        
        # In einer echten Implementierung würden wir hier die tatsächlich
        # gefundenen Begriffe aus den Ergebnissen extrahieren
        # Für dieses Beispiel verwenden wir die Suchbegriffe selbst
        highlighted.extend(search_terms)
        
        return highlighted
    
    def get_search_suggestions(self, partial_query: str, max_suggestions: int = 10) -> List[str]:
        """
        Gibt Suchvorschläge basierend auf einer partiellen Anfrage zurück.
        
        Args:
            partial_query: Partielle Suchanfrage
            max_suggestions: Maximale Anzahl von Vorschlägen
            
        Returns:
            Liste von Suchvorschlägen
        """
        try:
            suggestions = []
            
            # Hole Titel und Künstler aus der Datenbank für Vorschläge
            titles = [af.title for af in AudioFile.select(AudioFile.title).distinct() if af.title]
            performers = [af.performer for af in AudioFile.select(AudioFile.performer).distinct() if af.performer]
            filenames = [af.file_name for af in AudioFile.select(AudioFile.file_name).distinct() if af.file_name]
            
            # Kombiniere alle Begriffe
            all_terms = titles + performers + filenames
            
            if partial_query:
                # Verwende fuzzy matching für Vorschläge
                matches = process.extract(partial_query, all_terms, limit=max_suggestions)
                suggestions = [match[0] for match in matches if match[1] >= 60]  # Mindestübereinstimmung 60%
            else:
                # Gib die häufigsten Begriffe zurück
                suggestions = list(set(all_terms))[:max_suggestions]
            
            self.logger.debug(f"Suchvorschläge generiert: {len(suggestions)} Vorschläge")
            return suggestions
            
        except Exception as e:
            self.logger.error(f"Fehler beim Generieren von Suchvorschlägen: {e}")
            return []
    
    def get_search_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Gibt die Suchhistorie zurück.
        
        Args:
            limit: Maximale Anzahl von Einträgen
            
        Returns:
            Liste von Suchhistorien-Einträgen
        """
        history = self.search_history
        if limit:
            history = history[-limit:]
        return history
    
    def clear_search_history(self):
        """Löscht die Suchhistorie."""
        self.search_history.clear()
        self.logger.debug("Suchhistorie gelöscht")
    
    def get_faceted_search_results(self, query: SearchQuery) -> Dict[str, Any]:
        """
        Gibt facettierte Suchergebnisse zurück.
        
        Args:
            query: SearchQuery-Objekt
            
        Returns:
            Dictionary mit facettierten Ergebnissen
        """
        try:
            facets = {
                "categories": {},
                "file_types": {},
                "date_ranges": {},
                "size_ranges": {}
            }
            
            # Hole alle Ergebnisse für die Facettierung
            all_results = self.search(SearchQuery(
                terms=query.terms,
                search_type=query.search_type,
                fuzzy_search=query.fuzzy_search
            ))
            
            # Erstelle Facetten
            for item in all_results.items:
                if isinstance(item, AudioFile):
                    # Kategorien
                    category = getattr(item, 'category', 'unclassified')
                    facets["categories"][category] = facets["categories"].get(category, 0) + 1
                    
                    # Dateitypen
                    file_type = getattr(item, 'mime_type', 'unknown')
                    facets["file_types"][file_type] = facets["file_types"].get(file_type, 0) + 1
                    
                    # Größenbereiche (vereinfacht)
                    size = getattr(item, 'file_size', 0)
                    if size < 1024 * 1024:  # < 1MB
                        size_range = "< 1MB"
                    elif size < 10 * 1024 * 1024:  # < 10MB
                        size_range = "1-10MB"
                    else:
                        size_range = "> 10MB"
                    facets["size_ranges"][size_range] = facets["size_ranges"].get(size_range, 0) + 1
            
            self.logger.debug(f"Facettierte Suche abgeschlossen: {len(facets)} Facetten")
            return facets
            
        except Exception as e:
            self.logger.error(f"Fehler bei der facettierten Suche: {e}")
            return {}


# Globale Instanz
_search_engine: Optional[AdvancedSearchEngine] = None

def get_search_engine() -> AdvancedSearchEngine:
    """
    Gibt die globale Instanz der AdvancedSearchEngine zurück.
    
    Returns:
        Instanz von AdvancedSearchEngine
    """
    global _search_engine
    if _search_engine is None:
        _search_engine = AdvancedSearchEngine()
    return _search_engine

def perform_search(query: SearchQuery) -> SearchResult:
    """
    Führt eine erweiterte Suche durch.
    
    Args:
        query: SearchQuery-Objekt
        
    Returns:
        SearchResult-Objekt
    """
    engine = get_search_engine()
    return engine.search(query)

def get_search_suggestions(partial_query: str, max_suggestions: int = 10) -> List[str]:
    """
    Gibt Suchvorschläge zurück.
    
    Args:
        partial_query: Partielle Suchanfrage
        max_suggestions: Maximale Anzahl von Vorschlägen
        
    Returns:
        Liste von Suchvorschlägen
    """
    engine = get_search_engine()
    return engine.get_search_suggestions(partial_query, max_suggestions)