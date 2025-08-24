"""
Kontextbezogene Hilfe für den Telegram Audio Downloader.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown

from .logging_config import get_logger

logger = get_logger(__name__)
console = Console()


class HelpContext(Enum):
    """Enumeration der verfügbaren Hilfekontexte."""
    GLOBAL = "global"
    SEARCH = "search"
    DOWNLOAD = "download"
    SETTINGS = "settings"
    INTERACTIVE = "interactive"
    PROGRESS = "progress"
    CATEGORIES = "categories"


@dataclass
class HelpEntry:
    """Datenklasse für einen Hilfeeintrag."""
    title: str
    description: str
    usage: Optional[str] = None
    examples: List[str] = field(default_factory=list)
    related_commands: List[str] = field(default_factory=list)
    context: HelpContext = HelpContext.GLOBAL


class ContextualHelpManager:
    """Klasse zur Verwaltung von kontextbezogener Hilfe."""
    
    def __init__(self):
        """Initialisiert den ContextualHelpManager."""
        self.console = console
        self.help_entries: Dict[str, HelpEntry] = {}
        self._initialize_help_entries()
    
    def _initialize_help_entries(self):
        """Initialisiert die standardmäßigen Hilfeeinträge."""
        # Globale Hilfeeinträge
        self.add_help_entry(
            key="welcome",
            title="Willkommen beim Telegram Audio Downloader",
            description="Ein leistungsstarker Download-Manager für Audiodateien aus Telegram-Gruppen.",
            usage="Starten Sie das Programm mit `python -m telegram_audio_downloader`",
            examples=[
                "python -m telegram_audio_downloader  # Startet den interaktiven Modus",
                "python -m telegram_audio_downloader --help  # Zeigt diese Hilfe an"
            ]
        )
        
        self.add_help_entry(
            key="navigation",
            title="Navigation",
            description="Verwenden Sie die Pfeiltasten oder Tastaturkürzel zur Navigation.",
            usage="Verwenden Sie die entsprechenden Tasten für verschiedene Aktionen",
            examples=[
                "q - Programm beenden",
                "h - Hilfe anzeigen",
                "s - Suchen starten",
                "d - Download starten"
            ],
            context=HelpContext.INTERACTIVE
        )
        
        # Suchhilfe
        self.add_help_entry(
            key="search",
            title="Suchen",
            description="Suchen Sie nach Audiodateien in Telegram-Gruppen.",
            usage="Geben Sie Suchbegriffe ein, um nach Dateien zu suchen",
            examples=[
                "rock - Sucht nach Dateien mit 'rock' im Titel oder Künstler",
                "beethoven - Sucht nach klassischer Musik",
                "* - Zeigt alle Dateien in der ausgewählten Gruppe an"
            ],
            context=HelpContext.SEARCH
        )
        
        # Download-Hilfe
        self.add_help_entry(
            key="download",
            title="Herunterladen",
            description="Laden Sie Audiodateien aus Telegram-Gruppen herunter.",
            usage="Wählen Sie Dateien aus und starten Sie den Download",
            examples=[
                "1,2,3 - Lädt die Dateien 1, 2 und 3 herunter",
                "1-5 - Lädt die Dateien 1 bis 5 herunter",
                "all - Lädt alle angezeigten Dateien herunter"
            ],
            context=HelpContext.DOWNLOAD
        )
        
        # Einstellungshilfe
        self.add_help_entry(
            key="settings",
            title="Einstellungen",
            description="Konfigurieren Sie das Verhalten des Downloaders.",
            usage="Ändern Sie Einstellungen in der Konfigurationsdatei oder über die Benutzeroberfläche",
            examples=[
                "DOWNLOAD_PATH - Legt das Download-Verzeichnis fest",
                "MAX_CONCURRENT_DOWNLOADS - Setzt die maximale Anzahl paralleler Downloads",
                "QUALITY - Legt die Audioqualität fest"
            ],
            context=HelpContext.SETTINGS
        )
        
        # Fortschritts-Hilfe
        self.add_help_entry(
            key="progress",
            title="Fortschrittsanzeige",
            description="Verfolgen Sie den Fortschritt Ihrer Downloads.",
            usage="Die Fortschrittsanzeige wird während des Downloads automatisch aktualisiert",
            examples=[
                "Grün - Abgeschlossen",
                "Blau - In Arbeit",
                "Rot - Fehler",
                "Gelb - Wartend"
            ],
            context=HelpContext.PROGRESS
        )
        
        # Kategorisierungshilfe
        self.add_help_entry(
            key="categories",
            title="Kategorisierung",
            description="Dateien werden automatisch nach Genre oder Künstler kategorisiert.",
            usage="Die Kategorisierung erfolgt automatisch basierend auf Metadaten",
            examples=[
                "Rock - Queen, Led Zeppelin, Pink Floyd",
                "Klassik - Beethoven, Mozart, Bach",
                "Jazz - Miles Davis, John Coltrane"
            ],
            context=HelpContext.CATEGORIES
        )
        
        # Tastaturkürzel-Hilfe
        self.add_help_entry(
            key="shortcuts",
            title="Tastaturkürzel",
            description="Verwenden Sie Tastaturkürzel für schnellen Zugriff auf Funktionen.",
            usage="Drücken Sie die entsprechenden Tasten für verschiedene Aktionen",
            examples=[
                "q - Programm beenden",
                "h - Hilfe anzeigen",
                "s - Suchen",
                "d - Download starten",
                "p - Downloads pausieren/fortsetzen",
                "c - Einstellungen anzeigen"
            ],
            context=HelpContext.GLOBAL
        )
    
    def add_help_entry(self, key: str, title: str, description: str, usage: Optional[str] = None, 
                      examples: Optional[List[str]] = None, related_commands: Optional[List[str]] = None, 
                      context: HelpContext = HelpContext.GLOBAL):
        """
        Fügt einen neuen Hilfeeintrag hinzu.
        
        Args:
            key: Eindeutiger Schlüssel für den Hilfeeintrag
            title: Titel des Hilfeeintrags
            description: Beschreibung des Hilfeeintrags
            usage: Verwendungshinweise
            examples: Beispiele
            related_commands: Verwandte Befehle
            context: Kontext des Hilfeeintrags
        """
        if examples is None:
            examples = []
        if related_commands is None:
            related_commands = []
            
        help_entry = HelpEntry(
            title=title,
            description=description,
            usage=usage,
            examples=examples,
            related_commands=related_commands,
            context=context
        )
        
        self.help_entries[key] = help_entry
        logger.debug(f"Hilfeeintrag hinzugefügt: {key} - {title}")
    
    def remove_help_entry(self, key: str):
        """
        Entfernt einen Hilfeeintrag.
        
        Args:
            key: Schlüssel des zu entfernenden Hilfeeintrags
        """
        if key in self.help_entries:
            del self.help_entries[key]
            logger.debug(f"Hilfeeintrag entfernt: {key}")
    
    def get_help_entry(self, key: str) -> Optional[HelpEntry]:
        """
        Gibt einen Hilfeeintrag zurück.
        
        Args:
            key: Schlüssel des Hilfeeintrags
            
        Returns:
            HelpEntry-Objekt oder None, wenn nicht gefunden
        """
        return self.help_entries.get(key)
    
    def get_help_for_context(self, context: HelpContext) -> List[HelpEntry]:
        """
        Gibt Hilfeeinträge für einen bestimmten Kontext zurück.
        
        Args:
            context: Kontext
            
        Returns:
            Liste von HelpEntry-Objekten
        """
        return [
            entry for entry in self.help_entries.values()
            if entry.context == context or entry.context == HelpContext.GLOBAL
        ]
    
    def show_help(self, context: Optional[HelpContext] = None, key: Optional[str] = None):
        """
        Zeigt Hilfe an.
        
        Args:
            context: Kontext, für den Hilfe angezeigt werden soll
            key: Spezifischer Hilfeeintrag, der angezeigt werden soll
        """
        if key:
            # Zeige einen spezifischen Hilfeeintrag an
            entry = self.get_help_entry(key)
            if entry:
                self._display_help_entry(entry)
            else:
                self.console.print(f"[red]Hilfeeintrag '{key}' nicht gefunden.[/red]")
        elif context:
            # Zeige Hilfe für einen bestimmten Kontext an
            entries = self.get_help_for_context(context)
            if entries:
                self._display_help_entries(entries, context)
            else:
                self.console.print(f"[yellow]Keine Hilfe für Kontext '{context.value}' verfügbar.[/yellow]")
        else:
            # Zeige allgemeine Hilfe an
            self._display_general_help()
    
    def _display_help_entry(self, entry: HelpEntry):
        """
        Zeigt einen einzelnen Hilfeeintrag an.
        
        Args:
            entry: HelpEntry-Objekt
        """
        # Titel
        self.console.print(Panel(f"[bold blue]{entry.title}[/bold blue]", expand=False))
        
        # Beschreibung
        self.console.print(f"[green]{entry.description}[/green]")
        
        # Verwendung
        if entry.usage:
            self.console.print("\n[bold]Verwendung:[/bold]")
            self.console.print(entry.usage)
        
        # Beispiele
        if entry.examples:
            self.console.print("\n[bold]Beispiele:[/bold]")
            for example in entry.examples:
                self.console.print(f"  • {example}")
        
        # Verwandte Befehle
        if entry.related_commands:
            self.console.print("\n[bold]Verwandte Befehle:[/bold]")
            for command in entry.related_commands:
                self.console.print(f"  • {command}")
        
        # Kontext
        self.console.print(f"\n[yellow]Kontext: {entry.context.value}[/yellow]")
    
    def _display_help_entries(self, entries: List[HelpEntry], context: HelpContext):
        """
        Zeigt eine Liste von Hilfeeinträgen an.
        
        Args:
            entries: Liste von HelpEntry-Objekten
            context: Kontext
        """
        self.console.print(Panel(f"[bold blue]Hilfe für Kontext: {context.value}[/bold blue]", expand=False))
        
        for entry in entries:
            self.console.print(f"\n[bold]{entry.title}[/bold]")
            self.console.print(f"[green]{entry.description}[/green]")
            
            if entry.usage:
                self.console.print(f"[cyan]Verwendung:[/cyan] {entry.usage}")
    
    def _display_general_help(self):
        """Zeigt die allgemeine Hilfe an."""
        # Willkommensmeldung
        welcome_entry = self.get_help_entry("welcome")
        if welcome_entry:
            self.console.print(Panel(f"[bold blue]{welcome_entry.title}[/bold blue]", expand=False))
            self.console.print(f"[green]{welcome_entry.description}[/green]")
        
        # Verfügbare Kontexte
        self.console.print("\n[bold]Verfügbare Hilfekontexte:[/bold]")
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Kontext", style="cyan")
        table.add_column("Beschreibung")
        
        for context in HelpContext:
            # Finde einen repräsentativen Eintrag für diesen Kontext
            representative_entry = None
            for entry in self.help_entries.values():
                if entry.context == context:
                    representative_entry = entry
                    break
            
            description = representative_entry.description if representative_entry else "Allgemeine Hilfe"
            table.add_row(context.value, description)
        
        self.console.print(table)
        
        # Tastaturkürzel
        shortcuts_entry = self.get_help_entry("shortcuts")
        if shortcuts_entry:
            self.console.print(f"\n[bold]{shortcuts_entry.title}[/bold]")
            self.console.print(f"[green]{shortcuts_entry.description}[/green]")
            for example in shortcuts_entry.examples:
                self.console.print(f"  • {example}")
    
    def search_help(self, query: str) -> List[HelpEntry]:
        """
        Sucht nach Hilfeeinträgen.
        
        Args:
            query: Suchbegriff
            
        Returns:
            Liste von HelpEntry-Objekten
        """
        query = query.lower()
        results = []
        
        for entry in self.help_entries.values():
            # Suche in Titel, Beschreibung und Beispielen
            if (query in entry.title.lower() or 
                query in entry.description.lower() or
                any(query in example.lower() for example in entry.examples)):
                results.append(entry)
        
        return results


# Globale Instanz
_help_manager: Optional[ContextualHelpManager] = None

def get_help_manager() -> ContextualHelpManager:
    """
    Gibt die globale Instanz des ContextualHelpManagers zurück.
    
    Returns:
        Instanz von ContextualHelpManager
    """
    global _help_manager
    if _help_manager is None:
        _help_manager = ContextualHelpManager()
    return _help_manager

def show_help(context: Optional[HelpContext] = None, key: Optional[str] = None):
    """
    Zeigt Hilfe an.
    
    Args:
        context: Kontext, für den Hilfe angezeigt werden soll
        key: Spezifischer Hilfeeintrag, der angezeigt werden soll
    """
    manager = get_help_manager()
    manager.show_help(context, key)

def search_help(query: str) -> List[HelpEntry]:
    """
    Sucht nach Hilfeeinträgen.
    
    Args:
        query: Suchbegriff
        
    Returns:
        Liste von HelpEntry-Objekten
    """
    manager = get_help_manager()
    return manager.search_help(query)

def add_help_entry(key: str, title: str, description: str, usage: Optional[str] = None, 
                  examples: Optional[List[str]] = None, related_commands: Optional[List[str]] = None, 
                  context: HelpContext = HelpContext.GLOBAL):
    """
    Fügt einen neuen Hilfeeintrag hinzu.
    
    Args:
        key: Eindeutiger Schlüssel für den Hilfeeintrag
        title: Titel des Hilfeeintrags
        description: Beschreibung des Hilfeeintrags
        usage: Verwendungshinweise
        examples: Beispiele
        related_commands: Verwandte Befehle
        context: Kontext des Hilfeeintrags
    """
    manager = get_help_manager()
    manager.add_help_entry(key, title, description, usage, examples, related_commands, context)