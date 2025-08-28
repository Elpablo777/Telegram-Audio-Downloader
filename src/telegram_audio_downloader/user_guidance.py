"""
Benutzerführung für den Telegram Audio Downloader.
"""

from typing import Optional, Dict, Any, List, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn

from .logging_config import get_logger
from .i18n import _
from .contextual_help import get_help_manager, HelpEntry
from .auto_completion import get_completion_manager, CompletionContext, CompletionType
from .visual_feedback import get_feedback_manager, show_message, FeedbackType, FeedbackLevel

logger = get_logger(__name__)
console = Console()


class GuidanceMode(Enum):
    """Enumeration der Führungungsmodi."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    INTERACTIVE = "interactive"


class GuidanceType(Enum):
    """Enumeration der Führungungstypen."""
    TUTORIAL = "tutorial"
    WIZARD = "wizard"
    HINT = "hint"
    TOOLTIP = "tooltip"
    WALKTHROUGH = "walkthrough"
    ONBOARDING = "onboarding"


@dataclass
class GuidanceStep:
    """Datenklasse für einen Führungungsschritt."""
    step_id: str
    title: str
    description: str
    instructions: str
    expected_input: str = ""
    validation_rules: List[str] = field(default_factory=list)
    help_topic: str = ""
    next_steps: List[str] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    completion_message: str = ""
    estimated_time: int = 0  # Minuten


@dataclass
class UserProgress:
    """Datenklasse für den Benutzerfortschritt."""
    user_id: str
    completed_steps: List[str] = field(default_factory=list)
    current_step: Optional[str] = None
    progress_percentage: float = 0.0
    last_activity: str = ""
    preferences: Dict[str, Any] = field(default_factory=dict)
    completed_tutorials: List[str] = field(default_factory=list)


@dataclass
class GuidanceConfig:
    """Datenklasse für die Führungungskonfiguration."""
    mode: GuidanceMode = GuidanceMode.INTERMEDIATE
    show_hints: bool = True
    interactive_tutorials: bool = True
    auto_advance: bool = False
    language: str = "en"
    theme: str = "default"
    enable_tooltips: bool = True
    show_progress_bar: bool = True
    skip_completed: bool = True


class UserGuidanceManager:
    """Klasse zur Verwaltung der Benutzerführung."""
    
    def __init__(self, config: Optional[GuidanceConfig] = None):
        """Initialisiert den UserGuidanceManager."""
        self.console = console
        self.config = config or GuidanceConfig()
        self.help_system = get_help_manager()
        self.completion_manager = get_completion_manager()
        self.feedback_manager = get_feedback_manager()
        self.user_progress: Dict[str, UserProgress] = {}
        self.guidance_steps: Dict[str, GuidanceStep] = {}
        self.tutorials: Dict[str, List[GuidanceStep]] = {}
        self.wizards: Dict[str, List[GuidanceStep]] = {}
        
        # Standard-Tutorials initialisieren
        self._initialize_standard_tutorials()
        
        # Vervollständigungsquellen für Führung registrieren
        self._register_completion_sources()
    
    def _initialize_standard_tutorials(self):
        """Initialisiert die standardmäßigen Tutorials."""
        # Onboarding-Tutorial
        onboarding_steps = [
            GuidanceStep(
                step_id="onboarding_welcome",
                title=_("welcome_title"),
                description=_("welcome_description"),
                instructions=_("welcome_instructions"),
                completion_message=_("welcome_completed"),
                estimated_time=2
            ),
            GuidanceStep(
                step_id="onboarding_setup",
                title=_("setup_title"),
                description=_("setup_description"),
                instructions=_("setup_instructions"),
                completion_message=_("setup_completed"),
                estimated_time=5
            ),
            GuidanceStep(
                step_id="onboarding_download",
                title=_("download_title"),
                description=_("download_description"),
                instructions=_("download_instructions"),
                completion_message=_("download_completed"),
                estimated_time=3
            )
        ]
        
        self.tutorials["onboarding"] = onboarding_steps
        
        # Fortgeschrittenes Tutorial
        advanced_steps = [
            GuidanceStep(
                step_id="advanced_search",
                title=_("advanced_search_title"),
                description=_("advanced_search_description"),
                instructions=_("advanced_search_instructions"),
                completion_message=_("advanced_search_completed"),
                estimated_time=10
            ),
            GuidanceStep(
                step_id="advanced_filters",
                title=_("advanced_filters_title"),
                description=_("advanced_filters_description"),
                instructions=_("advanced_filters_instructions"),
                completion_message=_("advanced_filters_completed"),
                estimated_time=8
            )
        ]
        
        self.tutorials["advanced_features"] = advanced_steps
    
    def _register_completion_sources(self):
        """Registriert Vervollständigungsquellen für Führungungsfunktionen."""
        # Füge Führungungsmodi als Vervollständigungen hinzu
        mode_items = [
            # CompletionItem für jeden Modus würde hier hinzugefügt werden
        ]
        
        self.completion_manager.add_completion_source(CompletionType.CUSTOM, mode_items)
    
    def start_tutorial(self, tutorial_name: str, user_id: str = "default"):
        """
        Startet ein Tutorial.
        
        Args:
            tutorial_name: Name des Tutorials
            user_id: ID des Benutzers
        """
        if tutorial_name not in self.tutorials:
            show_message(
                _("tutorial_not_found").format(tutorial=tutorial_name),
                FeedbackType.ERROR,
                FeedbackLevel.HIGH
            )
            return
        
        # Erstelle oder lade den Benutzerfortschritt
        if user_id not in self.user_progress:
            self.user_progress[user_id] = UserProgress(user_id=user_id)
        
        user_progress = self.user_progress[user_id]
        tutorial_steps = self.tutorials[tutorial_name]
        
        # Filtere bereits abgeschlossene Schritte, wenn gewünscht
        if self.config.skip_completed:
            remaining_steps = [
                step for step in tutorial_steps 
                if step.step_id not in user_progress.completed_steps
            ]
        else:
            remaining_steps = tutorial_steps
        
        if not remaining_steps:
            show_message(
                _("tutorial_already_completed").format(tutorial=tutorial_name),
                FeedbackType.INFO
            )
            return
        
        # Zeige Tutorial-Einführung
        intro_text = Text(_("tutorial_intro").format(tutorial=tutorial_name), style="bold blue")
        console.print(Panel(intro_text, title=_("tutorial_start")))
        
        # Starte die Tutorial-Schritte
        self._execute_tutorial_steps(remaining_steps, user_id, tutorial_name)
    
    def _execute_tutorial_steps(self, steps: List[GuidanceStep], user_id: str, tutorial_name: str):
        """
        Führt die Tutorial-Schritte aus.
        
        Args:
            steps: Liste der auszuführenden Schritte
            user_id: ID des Benutzers
            tutorial_name: Name des Tutorials
        """
        user_progress = self.user_progress[user_id]
        
        for i, step in enumerate(steps):
            # Setze den aktuellen Schritt
            user_progress.current_step = step.step_id
            
            # Zeige den Schritt an
            self._show_guidance_step(step)
            
            # Warte auf Benutzerinteraktion, wenn nicht im Auto-Advance-Modus
            if not self.config.auto_advance:
                continue_tutorial = Confirm.ask(_("continue_tutorial"), default=True)
                if not continue_tutorial:
                    show_message(_("tutorial_paused"), FeedbackType.INFO)
                    return
            
            # Markiere den Schritt als abgeschlossen
            if step.step_id not in user_progress.completed_steps:
                user_progress.completed_steps.append(step.step_id)
            
            # Aktualisiere den Fortschritt
            progress_percent = (i + 1) / len(steps) * 100
            user_progress.progress_percentage = progress_percent
            
            # Zeige Fortschrittsmeldung
            if step.completion_message:
                show_message(step.completion_message, FeedbackType.SUCCESS)
        
        # Tutorial abgeschlossen
        user_progress.completed_tutorials.append(tutorial_name)
        user_progress.current_step = None
        
        show_message(
            _("tutorial_completed").format(tutorial=tutorial_name),
            FeedbackType.SUCCESS,
            FeedbackLevel.HIGH
        )
    
    def _show_guidance_step(self, step: GuidanceStep):
        """
        Zeigt einen Führungungsschritt an.
        
        Args:
            step: Der anzuzeigende Schritt
        """
        # Erstelle ein Panel für den Schritt
        step_content = Text()
        
        # Titel
        step_content.append(f"{step.title}\n", style="bold blue")
        
        # Beschreibung
        step_content.append(f"{step.description}\n\n", style="dim")
        
        # Anweisungen
        step_content.append(_("instructions") + ":\n", style="bold")
        step_content.append(f"{step.instructions}\n\n")
        
        # Erwartete Eingabe
        if step.expected_input:
            step_content.append(_("expected_input") + ":\n", style="bold")
            step_content.append(f"{step.expected_input}\n\n")
        
        # Geschätzte Zeit
        if step.estimated_time > 0:
            time_text = _("estimated_time").format(minutes=step.estimated_time)
            step_content.append(f"{time_text}\n", style="italic dim")
        
        # Hilfe-Link
        if step.help_topic:
            help_text = _("help_available").format(topic=step.help_topic)
            step_content.append(f"\n{help_text}\n", style="cyan")
        
        # Zeige das Panel an
        console.print(Panel(step_content, title=_("step")))
    
    def show_hint(self, topic: str, context: str = ""):
        """
        Zeigt einen Hinweis zu einem bestimmten Thema an.
        
        Args:
            topic: Thema des Hinweises
            context: Kontextinformation
        """
        if not self.config.show_hints:
            return
        
        # Hole Hilfeinhalte zum Thema
        help_content = self.help_system.get_help_entry(topic)
        
        if not help_content:
            # Versuche, ähnliche Themen zu finden
            similar_topics = self._search_help_topics(topic)
            if similar_topics:
                help_content = _("similar_topics_found").format(
                    topic=topic,
                    topics=", ".join(similar_topics[:3])
                )
            else:
                help_content = _("no_help_available").format(topic=topic)
        
        # Zeige den Hinweis an
        hint_text = Text()
        hint_text.append(_("hint") + ": ", style="bold yellow")
        hint_text.append(str(help_content))  # Stelle sicher, dass help_content ein String ist
        
        if context:
            hint_text.append(f"\n{_('context')}: {context}", style="dim")
        
        console.print(Panel(hint_text, title=_("hint"), border_style="yellow"))
    
    def _search_help_topics(self, topic: str) -> List[str]:
        """
        Sucht nach ähnlichen Hilfethemen.
        
        Args:
            topic: Thema, nach dem gesucht werden soll
            
        Returns:
            Liste mit ähnlichen Themen
        """
        # Verwende die search_help Methode des Hilfe-Systems
        help_manager = get_help_manager()
        results = help_manager.search_help(topic)
        return [entry.title for entry in results]
    
    def show_tooltip(self, element: str, description: str):
        """
        Zeigt einen Tooltip für ein UI-Element an.
        
        Args:
            element: Name des UI-Elements
            description: Beschreibung des Elements
        """
        if not self.config.enable_tooltips:
            return
        
        tooltip_text = Text()
        tooltip_text.append(f"{element}\n", style="bold")
        tooltip_text.append(description, style="dim")
        
        console.print(Panel(tooltip_text, title=_("tooltip"), border_style="cyan"))
    
    def start_wizard(self, wizard_name: str, user_id: str = "default"):
        """
        Startet einen Assistenten.
        
        Args:
            wizard_name: Name des Assistenten
            user_id: ID des Benutzers
        """
        if wizard_name not in self.wizards:
            show_message(
                _("wizard_not_found").format(wizard=wizard_name),
                FeedbackType.ERROR,
                FeedbackLevel.HIGH
            )
            return
        
        # Erstelle oder lade den Benutzerfortschritt
        if user_id not in self.user_progress:
            self.user_progress[user_id] = UserProgress(user_id=user_id)
        
        wizard_steps = self.wizards[wizard_name]
        
        # Zeige Wizard-Einführung
        intro_text = Text(_("wizard_intro").format(wizard=wizard_name), style="bold magenta")
        console.print(Panel(intro_text, title=_("wizard_start")))
        
        # Führe die Wizard-Schritte aus
        results = self._execute_wizard_steps(wizard_steps, user_id)
        
        return results
    
    def _execute_wizard_steps(self, steps: List[GuidanceStep], user_id: str) -> Dict[str, Any]:
        """
        Führt die Wizard-Schritte aus und sammelt Eingaben.
        
        Args:
            steps: Liste der auszuführenden Schritte
            user_id: ID des Benutzers
            
        Returns:
            Dictionary mit den gesammelten Ergebnissen
        """
        results = {}
        
        for step in steps:
            # Zeige den Schritt an
            self._show_guidance_step(step)
            
            # Hole Benutzereingabe
            if step.expected_input:
                user_input = Prompt.ask(step.expected_input)
                results[step.step_id] = user_input
            else:
                # Für Schritte ohne explizite Eingabe, bestätige den Abschluss
                Confirm.ask(_("confirm_step"), default=True)
                results[step.step_id] = True
        
        # Zeige Abschlussmeldung
        show_message(_("wizard_completed"), FeedbackType.SUCCESS)
        
        return results
    
    def get_user_progress(self, user_id: str = "default") -> Optional[UserProgress]:
        """
        Gibt den Fortschritt eines Benutzers zurück.
        
        Args:
            user_id: ID des Benutzers
            
        Returns:
            Benutzerfortschritt oder None
        """
        return self.user_progress.get(user_id)
    
    def reset_user_progress(self, user_id: str = "default"):
        """
        Setzt den Fortschritt eines Benutzers zurück.
        
        Args:
            user_id: ID des Benutzers
        """
        if user_id in self.user_progress:
            self.user_progress[user_id] = UserProgress(user_id=user_id)
            show_message(_("progress_reset"), FeedbackType.SUCCESS)
        else:
            show_message(_("no_progress_found"), FeedbackType.WARNING)
    
    def set_guidance_mode(self, mode: GuidanceMode):
        """
        Setzt den Führungungsmodus.
        
        Args:
            mode: Neuer Führungungsmodus
        """
        self.config.mode = mode
        logger.debug(f"Führungungsmodus gesetzt: {mode.value}")
        
        # Zeige eine Meldung abhängig vom Modus
        mode_messages = {
            GuidanceMode.BEGINNER: _("beginner_mode_activated"),
            GuidanceMode.INTERMEDIATE: _("intermediate_mode_activated"),
            GuidanceMode.ADVANCED: _("advanced_mode_activated"),
            GuidanceMode.INTERACTIVE: _("interactive_mode_activated")
        }
        
        message = mode_messages.get(mode, _("mode_activated").format(mode=mode.value))
        show_message(message, FeedbackType.INFO)
    
    def show_guidance_overview(self):
        """Zeigt eine Übersicht der verfügbaren Führungungsfunktionen an."""
        # Erstelle eine Tabelle mit verfügbaren Tutorials
        table = Table(title=_("guidance_overview"))
        table.add_column(_("name"), style="cyan")
        table.add_column(_("type"), style="magenta")
        table.add_column(_("steps"), style="green")
        table.add_column(_("completed"), style="blue")
        
        # Füge Tutorials hinzu
        for tutorial_name, steps in self.tutorials.items():
            step_count = len(steps)
            
            # Zähle abgeschlossene Schritte für den Standardbenutzer
            completed_count = 0
            if "default" in self.user_progress:
                user_progress = self.user_progress["default"]
                completed_count = len([
                    step for step in steps 
                    if step.step_id in user_progress.completed_steps
                ])
            
            table.add_row(
                tutorial_name,
                _("tutorial"),
                str(step_count),
                f"{completed_count}/{step_count}"
            )
        
        # Füge Wizards hinzu
        for wizard_name, steps in self.wizards.items():
            step_count = len(steps)
            table.add_row(
                wizard_name,
                _("wizard"),
                str(step_count),
                _("not_applicable")
            )
        
        console.print(table)
        
        # Zeige aktuelle Konfiguration
        config_table = Table(title=_("current_configuration"))
        config_table.add_column(_("setting"), style="cyan")
        config_table.add_column(_("value"), style="magenta")
        
        config_table.add_row(_("mode"), self.config.mode.value)
        config_table.add_row(_("show_hints"), str(self.config.show_hints))
        config_table.add_row(_("interactive_tutorials"), str(self.config.interactive_tutorials))
        config_table.add_row(_("auto_advance"), str(self.config.auto_advance))
        config_table.add_row(_("enable_tooltips"), str(self.config.enable_tooltips))
        
        console.print(config_table)


# Globale Instanz
_user_guidance_manager: Optional[UserGuidanceManager] = None


def get_guidance_manager() -> UserGuidanceManager:
    """
    Gibt die globale Instanz des UserGuidanceManagers zurück.
    
    Returns:
        Instanz von UserGuidanceManager
    """
    global _user_guidance_manager
    if _user_guidance_manager is None:
        _user_guidance_manager = UserGuidanceManager()
    return _user_guidance_manager


def start_tutorial(tutorial_name: str, user_id: str = "default"):
    """
    Startet ein Tutorial.
    
    Args:
        tutorial_name: Name des Tutorials
        user_id: ID des Benutzers
    """
    manager = get_guidance_manager()
    manager.start_tutorial(tutorial_name, user_id)


def show_hint(topic: str, context: str = ""):
    """
    Zeigt einen Hinweis zu einem bestimmten Thema an.
    
    Args:
        topic: Thema des Hinweises
        context: Kontextinformation
    """
    manager = get_guidance_manager()
    manager.show_hint(topic, context)


def show_tooltip(element: str, description: str):
    """
    Zeigt einen Tooltip für ein UI-Element an.
    
    Args:
        element: Name des UI-Elements
        description: Beschreibung des Elements
    """
    manager = get_guidance_manager()
    manager.show_tooltip(element, description)


def start_wizard(wizard_name: str, user_id: str = "default") -> Optional[Dict[str, Any]]:
    """
    Startet einen Assistenten.
    
    Args:
        wizard_name: Name des Assistenten
        user_id: ID des Benutzers
        
    Returns:
        Dictionary mit den gesammelten Ergebnissen oder None
    """
    manager = get_guidance_manager()
    return manager.start_wizard(wizard_name, user_id)


def set_guidance_mode(mode: GuidanceMode):
    """
    Setzt den Führungungsmodus.
    
    Args:
        mode: Neuer Führungungsmodus
    """
    manager = get_guidance_manager()
    manager.set_guidance_mode(mode)


def show_guidance_overview():
    """Zeigt eine Übersicht der verfügbaren Führungungsfunktionen an."""
    manager = get_guidance_manager()
    manager.show_guidance_overview()


# Deutsche Übersetzungen für Benutzerführung
USER_GUIDANCE_TRANSLATIONS_DE = {
    "welcome_title": "Willkommen beim Telegram Audio Downloader",
    "welcome_description": "Dies ist eine Einführung in die grundlegenden Funktionen der Anwendung.",
    "welcome_instructions": "Folgen Sie den Anweisungen, um die ersten Schritte zu lernen.",
    "welcome_completed": "Grundlagen erfolgreich abgeschlossen!",
    "setup_title": "Einrichtung",
    "setup_description": "Konfigurieren Sie die Anwendung für die erste Verwendung.",
    "setup_instructions": "Stellen Sie Ihren Download-Ordner und Ihre Telegram-API-Daten ein.",
    "setup_completed": "Einrichtung erfolgreich abgeschlossen!",
    "download_title": "Herunterladen von Audiodateien",
    "download_description": "Lernen Sie, wie Sie Audiodateien von Telegram herunterladen.",
    "download_instructions": "Wählen Sie eine Gruppe aus und starten Sie den Download-Prozess.",
    "download_completed": "Download erfolgreich abgeschlossen!",
    "advanced_search_title": "Erweiterte Suche",
    "advanced_search_description": "Nutzen Sie erweiterte Suchfunktionen, um Dateien schneller zu finden.",
    "advanced_search_instructions": "Verwenden Sie Filter und Suchoperatoren für präzise Ergebnisse.",
    "advanced_search_completed": "Erweiterte Suche erfolgreich beherrscht!",
    "advanced_filters_title": "Erweiterte Filter",
    "advanced_filters_description": "Wenden Sie komplexe Filter auf Ihre Suchergebnisse an.",
    "advanced_filters_instructions": "Kombinieren Sie mehrere Filterkriterien für spezifische Ergebnisse.",
    "advanced_filters_completed": "Erweiterte Filter erfolgreich angewendet!",
    "tutorial_not_found": "Tutorial '{tutorial}' nicht gefunden",
    "tutorial_already_completed": "Tutorial '{tutorial}' wurde bereits abgeschlossen",
    "tutorial_intro": "Starte Tutorial: {tutorial}",
    "tutorial_start": "Tutorial Start",
    "continue_tutorial": "Weiter zum nächsten Schritt?",
    "tutorial_paused": "Tutorial pausiert",
    "tutorial_completed": "Tutorial '{tutorial}' erfolgreich abgeschlossen!",
    "instructions": "Anweisungen",
    "expected_input": "Erwartete Eingabe",
    "estimated_time": "Geschätzte Zeit: {minutes} Minuten",
    "help_available": "Hilfe verfügbar unter: {topic}",
    "step": "Schritt",
    "hint": "Hinweis",
    "similar_topics_found": "Keine Hilfe für '{topic}' gefunden. Ähnliche Themen: {topics}",
    "no_help_available": "Keine Hilfe verfügbar für: {topic}",
    "context": "Kontext",
    "tooltip": "Tooltip",
    "wizard_not_found": "Assistent '{wizard}' nicht gefunden",
    "wizard_intro": "Starte Assistent: {wizard}",
    "wizard_start": "Assistent Start",
    "confirm_step": "Schritt bestätigen?",
    "wizard_completed": "Assistent erfolgreich abgeschlossen!",
    "progress_reset": "Benutzerfortschritt zurückgesetzt",
    "no_progress_found": "Kein Fortschritt für diesen Benutzer gefunden",
    "beginner_mode_activated": "Anfängermodus aktiviert - Detaillierte Anleitung aktiv",
    "intermediate_mode_activated": "Fortgeschrittenenmodus aktiviert - Ausgewogene Unterstützung",
    "advanced_mode_activated": "Expertenmodus aktiviert - Minimale Unterstützung",
    "interactive_mode_activated": "Interaktiver Modus aktiviert - Schritt-für-Schritt-Anleitung",
    "mode_activated": "Modus '{mode}' aktiviert",
    "guidance_overview": "Führungungsübersicht",
    "name": "Name",
    "type": "Typ",
    "steps": "Schritte",
    "completed": "Abgeschlossen",
    "tutorial": "Tutorial",
    "wizard": "Assistent",
    "not_applicable": "N/A",
    "current_configuration": "Aktuelle Konfiguration",
    "setting": "Einstellung",
    "value": "Wert",
    "show_hints": "Hinweise anzeigen",
    "interactive_tutorials": "Interaktive Tutorials",
    "auto_advance": "Automatisch fortfahren",
    "enable_tooltips": "Tooltips aktivieren",
}