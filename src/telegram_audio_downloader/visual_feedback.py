"""
Visuelles Feedback für den Telegram Audio Downloader.
"""

from typing import Optional, Dict, Any, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import time
from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn, SpinnerColumn
from rich.table import Table
from rich.text import Text
from rich.style import Style
from rich.live import Live
from rich.layout import Layout
from rich.align import Align

from .logging_config import get_logger
from .i18n import _
from .color_coding import get_color_manager, ColorTheme

logger = get_logger(__name__)
console = Console()


class FeedbackType(Enum):
    """Enumeration der Feedback-Typen."""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    PROGRESS = "progress"
    NOTIFICATION = "notification"
    CONFIRMATION = "confirmation"
    DEBUG = "debug"


class FeedbackLevel(Enum):
    """Enumeration der Feedback-Level."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class VisualFeedbackConfig:
    """Datenklasse für die visuelle Feedback-Konfiguration."""
    enable_animations: bool = True
    enable_colors: bool = True
    feedback_level: FeedbackLevel = FeedbackLevel.MEDIUM
    animation_speed: float = 1.0  # Multiplikator für Animationsgeschwindigkeit
    show_timestamps: bool = False
    persistent_notifications: bool = False
    max_notification_age: int = 300  # Sekunden
    theme: ColorTheme = ColorTheme.DEFAULT


@dataclass
class FeedbackMessage:
    """Datenklasse für eine Feedback-Nachricht."""
    message: str
    type: FeedbackType
    level: FeedbackLevel = FeedbackLevel.MEDIUM
    title: str = ""
    details: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    duration: Optional[float] = None  # Sekunden, wie lange die Nachricht angezeigt wird
    icon: str = ""
    action_buttons: Dict[str, Callable] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class VisualFeedbackManager:
    """Klasse zur Verwaltung von visuellem Feedback."""
    
    def __init__(self, config: Optional[VisualFeedbackConfig] = None):
        """Initialisiert den VisualFeedbackManager."""
        self.console = console
        self.config = config or VisualFeedbackConfig()
        self.color_manager = get_color_manager()
        self.notifications: Dict[str, FeedbackMessage] = {}
        self.active_progress_bars: Dict[str, Progress] = {}
        self.live_displays: Dict[str, Live] = {}
        self.message_history: list = []
        self.max_history_size = 100
        
        # Standard-Icons für verschiedene Feedback-Typen
        self.icons = {
            FeedbackType.SUCCESS: "✅",
            FeedbackType.ERROR: "❌",
            FeedbackType.WARNING: "⚠️",
            FeedbackType.INFO: "ℹ️",
            FeedbackType.PROGRESS: "🔄",
            FeedbackType.NOTIFICATION: "🔔",
            FeedbackType.CONFIRMATION: "❓",
            FeedbackType.DEBUG: "🐛"
        }
    
    def show_message(self, message: Union[str, FeedbackMessage], 
                     feedback_type: Optional[FeedbackType] = None,
                     level: FeedbackLevel = FeedbackLevel.MEDIUM,
                     title: str = "",
                     details: str = "",
                     duration: Optional[float] = None):
        """
        Zeigt eine Feedback-Nachricht an.
        
        Args:
            message: Die anzuzeigende Nachricht oder ein FeedbackMessage-Objekt
            feedback_type: Typ der Nachricht
            level: Wichtigkeit der Nachricht
            title: Titel der Nachricht
            details: Zusätzliche Details
            duration: Anzeigedauer in Sekunden
        """
        # Erstelle ein FeedbackMessage-Objekt, falls ein String übergeben wurde
        if isinstance(message, str):
            feedback_message = FeedbackMessage(
                message=message,
                type=feedback_type or FeedbackType.INFO,
                level=level,
                title=title,
                details=details,
                duration=duration,
                icon=self.icons.get(feedback_type or FeedbackType.INFO, "")
            )
        else:
            feedback_message = message
        
        # Prüfe, ob die Nachricht angezeigt werden soll basierend auf dem Feedback-Level
        if not self._should_show_message(feedback_message):
            return
        
        # Füge zur Historie hinzu
        self.message_history.append(feedback_message)
        if len(self.message_history) > self.max_history_size:
            self.message_history.pop(0)
        
        # Zeige die Nachricht an
        self._display_message(feedback_message)
        
        # Füge zu Benachrichtigungen hinzu, falls persistent
        if self.config.persistent_notifications and feedback_message.type == FeedbackType.NOTIFICATION:
            notification_id = str(hash(feedback_message.message + str(feedback_message.timestamp)))
            self.notifications[notification_id] = feedback_message
        
        logger.debug(f"Feedback-Nachricht angezeigt: {feedback_message.message}")
    
    def _should_show_message(self, message: FeedbackMessage) -> bool:
        """
        Prüft, ob eine Nachricht basierend auf dem Feedback-Level angezeigt werden soll.
        
        Args:
            message: Die zu prüfende Nachricht
            
        Returns:
            True, wenn die Nachricht angezeigt werden soll
        """
        level_order = {
            FeedbackLevel.LOW: 0,
            FeedbackLevel.MEDIUM: 1,
            FeedbackLevel.HIGH: 2,
            FeedbackLevel.CRITICAL: 3
        }
        
        config_level = level_order[self.config.feedback_level]
        message_level = level_order[message.level]
        
        return message_level >= config_level
    
    def _display_message(self, message: FeedbackMessage):
        """
        Zeigt eine Nachricht auf der Konsole an.
        
        Args:
            message: Die anzuzeigende Nachricht
        """
        # Bestimme die Farbe basierend auf dem Nachrichtentyp
        color_map = {
            FeedbackType.SUCCESS: "green",
            FeedbackType.ERROR: "red",
            FeedbackType.WARNING: "yellow",
            FeedbackType.INFO: "blue",
            FeedbackType.NOTIFICATION: "magenta",
            FeedbackType.CONFIRMATION: "cyan",
            FeedbackType.DEBUG: "bright_black",
            FeedbackType.PROGRESS: "blue"
        }
        
        color = color_map.get(message.type, "white")
        
        # Erstelle den Nachrichtentext
        text_parts = []
        
        # Icon
        if message.icon:
            text_parts.append(f"{message.icon} ")
        
        # Timestamp
        if self.config.show_timestamps:
            timestamp_str = message.timestamp.strftime("%H:%M:%S")
            text_parts.append(f"[{timestamp_str}] ")
        
        # Titel
        if message.title:
            text_parts.append(f"[bold]{message.title}[/bold]: ")
        
        # Nachricht
        text_parts.append(message.message)
        
        # Details
        if message.details:
            text_parts.append(f"\n[dim]{message.details}[/dim]")
        
        # Erstelle den Text
        text = Text("".join(text_parts), style=color)
        
        # Zeige die Nachricht an
        if message.type == FeedbackType.ERROR:
            console.print(text, style="bold red")
        elif message.type == FeedbackType.WARNING:
            console.print(text, style="bold yellow")
        elif message.type == FeedbackType.SUCCESS:
            console.print(text, style="bold green")
        else:
            console.print(text)
    
    def show_progress(self, task_id: str, 
                      description: str = "", 
                      total: Optional[float] = None,
                      start: bool = True) -> Progress:
        """
        Zeigt einen Fortschrittsbalken an.
        
        Args:
            task_id: Eindeutige ID für die Aufgabe
            description: Beschreibung der Aufgabe
            total: Gesamtanzahl der Schritte
            start: Ob der Fortschrittsbalken sofort gestartet werden soll
            
        Returns:
            Rich Progress-Objekt
        """
        # Erstelle einen neuen Fortschrittsbalken
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=40),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            console=self.console,
            transient=True,
            refresh_per_second=10 * self.config.animation_speed
        )
        
        if start:
            progress.start()
        
        # Füge eine Aufgabe hinzu
        progress.add_task(description or _("processing"), total=total)
        
        # Speichere den Fortschrittsbalken
        self.active_progress_bars[task_id] = progress
        
        return progress
    
    def update_progress(self, task_id: str, advance: float = 1.0, description: Optional[str] = None):
        """
        Aktualisiert einen Fortschrittsbalken.
        
        Args:
            task_id: ID der Aufgabe
            advance: Anzahl der Schritte, um die fortgeschritten werden soll
            description: Neue Beschreibung (optional)
        """
        if task_id in self.active_progress_bars:
            progress = self.active_progress_bars[task_id]
            task_ids = list(progress.task_ids)
            if task_ids:
                if description:
                    progress.update(task_ids[0], advance=advance, description=description)
                else:
                    progress.update(task_ids[0], advance=advance)
    
    def stop_progress(self, task_id: str):
        """
        Stoppt und entfernt einen Fortschrittsbalken.
        
        Args:
            task_id: ID der Aufgabe
        """
        if task_id in self.active_progress_bars:
            progress = self.active_progress_bars[task_id]
            progress.stop()
            del self.active_progress_bars[task_id]
    
    def show_live_display(self, display_id: str, renderable, refresh_rate: float = 4.0):
        """
        Zeigt eine Live-Anzeige an.
        
        Args:
            display_id: Eindeutige ID für die Anzeige
            renderable: Das anzuzeigende Element
            refresh_rate: Aktualisierungsrate in Hz
        """
        live = Live(
            renderable,
            console=self.console,
            refresh_per_second=refresh_rate * self.config.animation_speed,
            transient=True
        )
        
        live.start()
        self.live_displays[display_id] = live
        
        return live
    
    def update_live_display(self, display_id: str, renderable):
        """
        Aktualisiert eine Live-Anzeige.
        
        Args:
            display_id: ID der Anzeige
            renderable: Das neue anzuzeigende Element
        """
        if display_id in self.live_displays:
            self.live_displays[display_id].update(renderable)
    
    def stop_live_display(self, display_id: str):
        """
        Stoppt und entfernt eine Live-Anzeige.
        
        Args:
            display_id: ID der Anzeige
        """
        if display_id in self.live_displays:
            self.live_displays[display_id].stop()
            del self.live_displays[display_id]
    
    def show_notification_center(self):
        """Zeigt das Benachrichtigungszentrum an."""
        if not self.notifications:
            self.show_message(_("no_notifications"), FeedbackType.INFO)
            return
        
        # Erstelle eine Tabelle für die Benachrichtigungen
        table = Table(title=_("notification_center"))
        table.add_column(_("time"), style="cyan", no_wrap=True)
        table.add_column(_("message"), style="magenta")
        table.add_column(_("type"), style="green")
        
        # Sortiere Benachrichtigungen nach Zeit (neueste zuerst)
        sorted_notifications = sorted(
            self.notifications.items(),
            key=lambda x: x[1].timestamp,
            reverse=True
        )
        
        for notification_id, notification in sorted_notifications:
            # Prüfe, ob die Benachrichtigung zu alt ist
            age = (datetime.now() - notification.timestamp).total_seconds()
            if age > self.config.max_notification_age:
                del self.notifications[notification_id]
                continue
            
            time_str = notification.timestamp.strftime("%H:%M:%S")
            type_str = _(notification.type.value)
            table.add_row(time_str, notification.message, type_str)
        
        console.print(table)
    
    def clear_notifications(self):
        """Löscht alle Benachrichtigungen."""
        self.notifications.clear()
        self.show_message(_("notifications_cleared"), FeedbackType.SUCCESS)
    
    def get_feedback_stats(self) -> Dict[str, int]:
        """
        Gibt Statistiken über das Feedback zurück.
        
        Returns:
            Dictionary mit Statistiken
        """
        stats = {}
        total = 0
        
        # Zähle Nachrichten nach Typ
        for message in self.message_history:
            type_name = message.type.value
            stats[type_name] = stats.get(type_name, 0) + 1
            total += 1
        
        stats["total"] = total
        stats["notifications"] = len(self.notifications)
        stats["active_progress"] = len(self.active_progress_bars)
        stats["live_displays"] = len(self.live_displays)
        
        return stats
    
    def set_config(self, config: VisualFeedbackConfig):
        """
        Setzt die Feedback-Konfiguration.
        
        Args:
            config: Neue Konfiguration
        """
        self.config = config
        logger.debug("Visuelle Feedback-Konfiguration aktualisiert")


# Globale Instanz
_visual_feedback_manager: Optional[VisualFeedbackManager] = None


def get_feedback_manager() -> VisualFeedbackManager:
    """
    Gibt die globale Instanz des VisualFeedbackManagers zurück.
    
    Returns:
        Instanz von VisualFeedbackManager
    """
    global _visual_feedback_manager
    if _visual_feedback_manager is None:
        _visual_feedback_manager = VisualFeedbackManager()
    return _visual_feedback_manager


def show_message(message: Union[str, FeedbackMessage], 
                 feedback_type: Optional[FeedbackType] = None,
                 level: FeedbackLevel = FeedbackLevel.MEDIUM,
                 title: str = "",
                 details: str = "",
                 duration: Optional[float] = None):
    """
    Zeigt eine Feedback-Nachricht an.
    
    Args:
        message: Die anzuzeigende Nachricht oder ein FeedbackMessage-Objekt
        feedback_type: Typ der Nachricht
        level: Wichtigkeit der Nachricht
        title: Titel der Nachricht
        details: Zusätzliche Details
        duration: Anzeigedauer in Sekunden
    """
    manager = get_feedback_manager()
    manager.show_message(message, feedback_type, level, title, details, duration)


def show_success(message: str, title: str = "", details: str = ""):
    """
    Zeigt eine Erfolgsmeldung an.
    
    Args:
        message: Die Nachricht
        title: Titel der Nachricht
        details: Zusätzliche Details
    """
    show_message(message, FeedbackType.SUCCESS, title=title, details=details)


def show_error(message: str, title: str = "", details: str = ""):
    """
    Zeigt eine Fehlermeldung an.
    
    Args:
        message: Die Nachricht
        title: Titel der Nachricht
        details: Zusätzliche Details
    """
    show_message(message, FeedbackType.ERROR, FeedbackLevel.HIGH, title, details)


def show_warning(message: str, title: str = "", details: str = ""):
    """
    Zeigt eine Warnung an.
    
    Args:
        message: Die Nachricht
        title: Titel der Nachricht
        details: Zusätzliche Details
    """
    show_message(message, FeedbackType.WARNING, title=title, details=details)


def show_info(message: str, title: str = "", details: str = ""):
    """
    Zeigt eine Informationsmeldung an.
    
    Args:
        message: Die Nachricht
        title: Titel der Nachricht
        details: Zusätzliche Details
    """
    show_message(message, FeedbackType.INFO, title=title, details=details)


def show_progress(task_id: str, description: str = "", total: Optional[float] = None, start: bool = True):
    """
    Zeigt einen Fortschrittsbalken an.
    
    Args:
        task_id: Eindeutige ID für die Aufgabe
        description: Beschreibung der Aufgabe
        total: Gesamtanzahl der Schritte
        start: Ob der Fortschrittsbalken sofort gestartet werden soll
        
    Returns:
        Rich Progress-Objekt
    """
    manager = get_feedback_manager()
    return manager.show_progress(task_id, description, total, start)


def update_progress(task_id: str, advance: float = 1.0, description: Optional[str] = None):
    """
    Aktualisiert einen Fortschrittsbalken.
    
    Args:
        task_id: ID der Aufgabe
        advance: Anzahl der Schritte, um die fortgeschritten werden soll
        description: Neue Beschreibung (optional)
    """
    manager = get_feedback_manager()
    manager.update_progress(task_id, advance, description)


def stop_progress(task_id: str):
    """
    Stoppt und entfernt einen Fortschrittsbalken.
    
    Args:
        task_id: ID der Aufgabe
    """
    manager = get_feedback_manager()
    manager.stop_progress(task_id)


def show_notification_center():
    """Zeigt das Benachrichtigungszentrum an."""
    manager = get_feedback_manager()
    manager.show_notification_center()


def clear_notifications():
    """Löscht alle Benachrichtigungen."""
    manager = get_feedback_manager()
    manager.clear_notifications()


# Deutsche Übersetzungen für visuelles Feedback
VISUAL_FEEDBACK_TRANSLATIONS_DE = {
    "processing": "Verarbeite...",
    "no_notifications": "Keine Benachrichtigungen vorhanden",
    "notification_center": "Benachrichtigungszentrum",
    "time": "Zeit",
    "message": "Nachricht",
    "type": "Typ",
    "notifications_cleared": "Benachrichtigungen gelöscht",
    "success": "Erfolg",
    "error": "Fehler",
    "warning": "Warnung",
    "info": "Info",
    "progress": "Fortschritt",
    "notification": "Benachrichtigung",
    "confirmation": "Bestätigung",
    "debug": "Debug",
}