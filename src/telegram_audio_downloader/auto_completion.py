"""
Automatische Vervollständigung für den Telegram Audio Downloader.
"""

from typing import List, Dict, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
import re

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from .logging_config import get_logger
from .i18n import _
from .models import AudioFile, TelegramGroup

logger = get_logger(__name__)
console = Console()


class CompletionType(Enum):
    """Enumeration der Vervollständigungstypen."""
    COMMAND = "command"
    FILE_NAME = "file_name"
    GROUP_NAME = "group_name"
    ARTIST = "artist"
    GENRE = "genre"
    TAG = "tag"
    SEARCH_HISTORY = "search_history"
    CUSTOM = "custom"


@dataclass
class CompletionItem:
    """Datenklasse für ein Vervollständigungselement."""
    text: str
    display_text: str = ""
    description: str = ""
    type: CompletionType = CompletionType.CUSTOM
    priority: int = 0  # Höhere Werte = höhere Priorität
    metadata: Dict[str, Any] = field(default_factory=dict)
    icon: str = "🔹"


@dataclass
class CompletionContext:
    """Datenklasse für den Vervollständigungskontext."""
    current_input: str
    cursor_position: int
    context_type: str = "global"  # global, search, download, settings, etc.
    available_types: List[CompletionType] = field(default_factory=list)
    max_suggestions: int = 10
    case_sensitive: bool = False
    fuzzy_matching: bool = True


class AutoCompletionManager:
    """Klasse zur Verwaltung der automatischen Vervollständigung."""
    
    def __init__(self):
        """Initialisiert den AutoCompletionManager."""
        self.console = console
        self.completion_sources: Dict[CompletionType, List[CompletionItem]] = {}
        self.custom_providers: Dict[str, Callable] = {}
        self.history: List[str] = []
        self.max_history_items = 100
        self._initialize_default_completions()
    
    def _initialize_default_completions(self):
        """Initialisiert die standardmäßigen Vervollständigungselemente."""
        # Standardbefehle
        commands = [
            ("download", _("download_command"), _("Download audio files from Telegram"), "📥"),
            ("search", _("search_command"), _("Search for audio files"), "🔍"),
            ("list", _("list_command"), _("List available audio files"), "📋"),
            ("info", _("info_command"), _("Show information about a file"), "ℹ️"),
            ("config", _("config_command"), _("Configure application settings"), "⚙️"),
            ("help", _("help_command"), _("Show help information"), "❓"),
            ("quit", _("quit_command"), _("Exit the application"), "🚪"),
            ("history", _("history_command"), _("Show download history"), "📜"),
            ("favorites", _("favorites_command"), _("Show favorite groups"), "⭐"),
            ("stats", _("stats_command"), _("Show download statistics"), "📊"),
        ]
        
        command_items = [
            CompletionItem(
                text=cmd[0],
                display_text=cmd[1],
                description=cmd[2],
                type=CompletionType.COMMAND,
                icon=cmd[3]
            )
            for cmd in commands
        ]
        
        self.completion_sources[CompletionType.COMMAND] = command_items
        
        # Standardkategorien
        categories = [
            ("rock", _("rock_genre"), _("Rock music"), "🎸"),
            ("pop", _("pop_genre"), _("Pop music"), "🎤"),
            ("jazz", _("jazz_genre"), _("Jazz music"), "🎷"),
            ("classical", _("classical_genre"), _("Classical music"), "🎼"),
            ("electronic", _("electronic_genre"), _("Electronic music"), "🎧"),
            ("hiphop", _("hiphop_genre"), _("Hip hop music"), "🎤"),
            ("country", _("country_genre"), _("Country music"), "🤠"),
            ("blues", _("blues_genre"), _("Blues music"), "🎸"),
        ]
        
        category_items = [
            CompletionItem(
                text=cat[0],
                display_text=cat[1],
                description=cat[2],
                type=CompletionType.GENRE,
                icon=cat[3]
            )
            for cat in categories
        ]
        
        self.completion_sources[CompletionType.GENRE] = category_items
    
    def add_completion_source(self, completion_type: CompletionType, items: List[CompletionItem]):
        """
        Fügt eine Quelle für Vervollständigungen hinzu.
        
        Args:
            completion_type: Typ der Vervollständigungen
            items: Liste der Vervollständigungselemente
        """
        if completion_type not in self.completion_sources:
            self.completion_sources[completion_type] = []
        
        self.completion_sources[completion_type].extend(items)
        logger.debug(f"Vervollständigungsquelle hinzugefügt: {completion_type.value} mit {len(items)} Elementen")
    
    def register_custom_provider(self, name: str, provider: Callable):
        """
        Registriert einen benutzerdefinierten Vervollständigungsanbieter.
        
        Args:
            name: Name des Anbieters
            provider: Funktion, die Vervollständigungen bereitstellt
        """
        self.custom_providers[name] = provider
        logger.debug(f"Benutzerdefinierter Vervollständigungsanbieter registriert: {name}")
    
    def get_completions(self, context: CompletionContext) -> List[CompletionItem]:
        """
        Ruft Vervollständigungen basierend auf dem Kontext ab.
        
        Args:
            context: Vervollständigungskontext
            
        Returns:
            Liste der Vervollständigungselemente
        """
        completions = []
        
        # Verwende verfügbare Typen oder alle Typen
        types_to_check = context.available_types if context.available_types else list(CompletionType)
        
        # Durchlaufe alle relevanten Typen
        for completion_type in types_to_check:
            if completion_type in self.completion_sources:
                source_completions = self.completion_sources[completion_type]
                matched_completions = self._match_completions(context, source_completions)
                completions.extend(matched_completions)
        
        # Füge benutzerdefinierte Vervollständigungen hinzu
        for provider_name, provider in self.custom_providers.items():
            try:
                custom_completions = provider(context)
                if isinstance(custom_completions, list):
                    completions.extend(custom_completions)
            except Exception as e:
                logger.warning(f"Fehler beim Abrufen von benutzerdefinierten Vervollständigungen von {provider_name}: {e}")
        
        # Sortiere nach Priorität
        completions.sort(key=lambda x: x.priority, reverse=True)
        
        # Begrenze auf maximale Anzahl
        return completions[:context.max_suggestions]
    
    def _match_completions(self, context: CompletionContext, completions: List[CompletionItem]) -> List[CompletionItem]:
        """
        Findet passende Vervollständigungen basierend auf dem Kontext.
        
        Args:
            context: Vervollständigungskontext
            completions: Liste der Vervollständigungselemente
            
        Returns:
            Liste der passenden Vervollständigungselemente
        """
        matched = []
        input_text = context.current_input
        
        if not context.case_sensitive:
            input_text = input_text.lower()
        
        for completion in completions:
            # Prüfe auf direkten Textmatch
            completion_text = completion.text if context.case_sensitive else completion.text.lower()
            
            if self._is_match(input_text, completion_text, context.fuzzy_matching):
                matched.append(completion)
                continue
            
            # Prüfe auf Display-Text-Match
            display_text = completion.display_text if context.case_sensitive else completion.display_text.lower()
            if display_text and self._is_match(input_text, display_text, context.fuzzy_matching):
                matched.append(completion)
                continue
        
        return matched
    
    def _is_match(self, input_text: str, completion_text: str, fuzzy: bool) -> bool:
        """
        Prüft, ob der Eingabetext mit dem Vervollständigungstext übereinstimmt.
        
        Args:
            input_text: Eingegebener Text
            completion_text: Text des Vervollständigungselementes
            fuzzy: Ob Fuzzy-Matching verwendet werden soll
            
        Returns:
            True, wenn eine Übereinstimmung vorliegt
        """
        if not input_text:
            return True
        
        if fuzzy:
            # Einfaches Fuzzy-Matching (Teilstring)
            return input_text in completion_text
        else:
            # Exaktes Präfix-Matching
            return completion_text.startswith(input_text)
    
    def add_to_history(self, text: str):
        """
        Fügt Text zur Vervollständigungshistorie hinzu.
        
        Args:
            text: Hinzuzufügender Text
        """
        if text in self.history:
            self.history.remove(text)
        
        self.history.insert(0, text)
        
        # Begrenze die Historie
        if len(self.history) > self.max_history_items:
            self.history = self.history[:self.max_history_items]
        
        logger.debug(f"Text zur Vervollständigungshistorie hinzugefügt: {text}")
    
    def get_history_completions(self, context: CompletionContext) -> List[CompletionItem]:
        """
        Ruft Vervollständigungen aus der Historie ab.
        
        Args:
            context: Vervollständigungskontext
            
        Returns:
            Liste der Historien-Vervollständigungselemente
        """
        completions = []
        
        for item in self.history:
            if context.current_input.lower() in item.lower():
                completions.append(CompletionItem(
                    text=item,
                    display_text=item,
                    description=_("from_history"),
                    type=CompletionType.SEARCH_HISTORY,
                    icon="📜"
                ))
        
        return completions[:context.max_suggestions]
    
    def clear_history(self):
        """Löscht die Vervollständigungshistorie."""
        self.history.clear()
        logger.debug("Vervollständigungshistorie gelöscht")
    
    def display_completions(self, completions: List[CompletionItem], selected_index: int = 0):
        """
        Zeigt Vervollständigungen in der Konsole an.
        
        Args:
            completions: Liste der anzuzeigenden Vervollständigungen
            selected_index: Index des ausgewählten Elements
        """
        if not completions:
            return
        
        # Erstelle ein Panel für die Vervollständigungen
        panel_content = []
        
        for i, completion in enumerate(completions):
            style = "bold white on blue" if i == selected_index else ""
            line = Text()
            
            # Icon
            line.append(f"{completion.icon} ", style=style)
            
            # Text
            text_part = completion.display_text or completion.text
            line.append(text_part, style=style)
            
            # Beschreibung (kleiner)
            if completion.description:
                line.append(f" - {completion.description}", style=f"dim {style}")
            
            panel_content.append(line)
        
        # Zeige das Panel an
        panel = Panel(
            Text("\n").join(panel_content),
            title=_("completions_title"),
            border_style="blue"
        )
        
        console.print(panel)
    
    def get_completion_stats(self) -> Dict[str, int]:
        """
        Gibt Statistiken über die verfügbaren Vervollständigungen zurück.
        
        Returns:
            Dictionary mit Statistiken
        """
        stats = {}
        total = 0
        
        for completion_type, items in self.completion_sources.items():
            count = len(items)
            stats[completion_type.value] = count
            total += count
        
        stats["total"] = total
        stats["history_items"] = len(self.history)
        
        return stats


# Globale Instanz
_auto_completion_manager: Optional[AutoCompletionManager] = None


def get_completion_manager() -> AutoCompletionManager:
    """
    Gibt die globale Instanz des AutoCompletionManagers zurück.
    
    Returns:
        Instanz von AutoCompletionManager
    """
    global _auto_completion_manager
    if _auto_completion_manager is None:
        _auto_completion_manager = AutoCompletionManager()
    return _auto_completion_manager


def get_completions(context: CompletionContext) -> List[CompletionItem]:
    """
    Ruft Vervollständigungen basierend auf dem Kontext ab.
    
    Args:
        context: Vervollständigungskontext
        
    Returns:
        Liste der Vervollständigungselemente
    """
    manager = get_completion_manager()
    return manager.get_completions(context)


def add_completion_source(completion_type: CompletionType, items: List[CompletionItem]):
    """
    Fügt eine Quelle für Vervollständigungen hinzu.
    
    Args:
        completion_type: Typ der Vervollständigungen
        items: Liste der Vervollständigungselemente
    """
    manager = get_completion_manager()
    manager.add_completion_source(completion_type, items)


def register_custom_provider(name: str, provider: Callable):
    """
    Registriert einen benutzerdefinierten Vervollständigungsanbieter.
    
    Args:
        name: Name des Anbieters
        provider: Funktion, die Vervollständigungen bereitstellt
    """
    manager = get_completion_manager()
    manager.register_custom_provider(name, provider)


def add_to_completion_history(text: str):
    """
    Fügt Text zur Vervollständigungshistorie hinzu.
    
    Args:
        text: Hinzuzufügender Text
    """
    manager = get_completion_manager()
    manager.add_to_history(text)


def clear_completion_history():
    """Löscht die Vervollständigungshistorie."""
    manager = get_completion_manager()
    manager.clear_history()


# Deutsche Übersetzungen für automatische Vervollständigung
AUTO_COMPLETION_TRANSLATIONS_DE = {
    "download_command": "Herunterladen",
    "search_command": "Suchen",
    "list_command": "Auflisten",
    "info_command": "Informationen",
    "config_command": "Konfiguration",
    "help_command": "Hilfe",
    "quit_command": "Beenden",
    "history_command": "Historie",
    "favorites_command": "Favoriten",
    "stats_command": "Statistiken",
    "rock_genre": "Rock",
    "pop_genre": "Pop",
    "jazz_genre": "Jazz",
    "classical_genre": "Klassik",
    "electronic_genre": "Elektronik",
    "hiphop_genre": "Hip Hop",
    "country_genre": "Country",
    "blues_genre": "Blues",
    "from_history": "aus Historie",
    "completions_title": "Vervollständigungen",
}