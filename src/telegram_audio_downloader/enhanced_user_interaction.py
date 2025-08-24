"""
Erweiterte Benutzerinteraktion für den Telegram Audio Downloader.
"""

import asyncio
import logging
import threading
import time
from typing import Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum

from rich.console import Console
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn, DownloadColumn
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.live import Live
from rich.layout import Layout
from rich.text import Text

logger = logging.getLogger(__name__)
console = Console()

class NotificationType(Enum):
    """Typen von Benachrichtigungen."""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"

@dataclass
class Notification:
    """Eine Benachrichtigung."""
    message: str
    type: NotificationType
    timestamp: float

class EnhancedUserInteraction:
    """Klasse zur Verwaltung erweiterter Benutzerinteraktionen."""
    
    def __init__(self):
        """Initialisiert die erweiterte Benutzerinteraktionsklasse."""
        self.console = console
        self.notifications = []
        self.notification_callback: Optional[Callable[[Notification], None]] = None
        self.progress_bar = None
        self.live_display = None
        self.is_interactive_mode = False
        
    def set_notification_callback(self, callback: Callable[[Notification], None]) -> None:
        """
        Setzt einen Callback für Benachrichtigungen.
        
        Args:
            callback: Funktion, die bei Benachrichtigungen aufgerufen wird
        """
        self.notification_callback = callback
        
    def show_notification(self, message: str, notification_type: NotificationType = NotificationType.INFO) -> None:
        """
        Zeigt eine Benachrichtigung an.
        
        Args:
            message: Nachrichtentext
            notification_type: Typ der Benachrichtigung
        """
        notification = Notification(message, notification_type, time.time())
        self.notifications.append(notification)
        
        # Konsolen-Ausgabe
        if notification_type == NotificationType.INFO:
            self.console.print(f"[blue]ℹ[/blue] {message}")
        elif notification_type == NotificationType.SUCCESS:
            self.console.print(f"[green]✓[/green] {message}")
        elif notification_type == NotificationType.WARNING:
            self.console.print(f"[yellow]⚠[/yellow] {message}")
        elif notification_type == NotificationType.ERROR:
            self.console.print(f"[red]✗[/red] {message}")
            
        # Callback aufrufen, wenn gesetzt
        if self.notification_callback:
            try:
                self.notification_callback(notification)
            except Exception as e:
                logger.warning(f"Fehler beim Aufrufen des Notification-Callbacks: {e}")
    
    def show_progress_bar(self, total: int, description: str = "Verarbeite...") -> Progress:
        """
        Zeigt eine erweiterte Fortschrittsanzeige an.
        
        Args:
            total: Gesamtanzahl der Schritte
            description: Beschreibungstext
            
        Returns:
            Rich Progress-Objekt
        """
        progress = Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=None),
            "[progress.percentage]{task.percentage:>3.0f}%",
            "•",
            DownloadColumn(),
            "•",
            TimeRemainingColumn(),
        )
        
        progress.add_task(description, total=total)
        return progress
    
    def show_live_progress(self, renderable: Any) -> Live:
        """
        Zeigt ein Live-Display an.
        
        Args:
            renderable: Das anzuzeigende Element
            
        Returns:
            Rich Live-Objekt
        """
        live = Live(renderable, refresh_per_second=4)
        return live
    
    def show_context_menu(self, title: str, options: list) -> int:
        """
        Zeigt ein Kontextmenü an.
        
        Args:
            title: Titel des Menüs
            options: Liste der Optionen
            
        Returns:
            Index der ausgewählten Option (0-basiert)
        """
        self.console.print(Panel(title, style="bold blue"))
        for i, option in enumerate(options, 1):
            self.console.print(f"{i}. {option}")
        
        while True:
            try:
                choice = int(Prompt.ask("Bitte wählen Sie eine Option", choices=[str(i) for i in range(1, len(options)+1)]))
                return choice - 1
            except ValueError:
                self.console.print("[red]Ungültige Eingabe. Bitte geben Sie eine Zahl ein.[/red]")
    
    def show_confirmation_dialog(self, message: str, default: bool = True) -> bool:
        """
        Zeigt einen Bestätigungsdialog an.
        
        Args:
            message: Nachrichtentext
            default: Standardwert (True für Ja, False für Nein)
            
        Returns:
            True, wenn bestätigt, False sonst
        """
        return Confirm.ask(message, default=default)
    
    def show_download_summary(self, stats: dict) -> None:
        """
        Zeigt eine Download-Zusammenfassung an.
        
        Args:
            stats: Statistikdaten
        """
        table = Table(title="Download-Zusammenfassung")
        table.add_column("Metrik", style="cyan")
        table.add_column("Wert", style="green")
        
        table.add_row("Gesamtdateien", str(stats.get("total_files", 0)))
        table.add_row("Erfolgreich", str(stats.get("successful_downloads", 0)))
        table.add_row("Fehlgeschlagen", str(stats.get("failed_downloads", 0)))
        table.add_row("Gesamtgröße", str(stats.get("total_size", "0 MB")))
        table.add_row("Dauer", str(stats.get("duration", "0s")))
        table.add_row("Durchschnittsgeschwindigkeit", str(stats.get("avg_speed", "0 MB/s")))
        
        self.console.print(table)
    
    def enable_interactive_mode(self) -> None:
        """Aktiviert den interaktiven Modus."""
        self.is_interactive_mode = True
        self.show_notification("Interaktiver Modus aktiviert", NotificationType.SUCCESS)
    
    def disable_interactive_mode(self) -> None:
        """Deaktiviert den interaktiven Modus."""
        self.is_interactive_mode = False
        self.show_notification("Interaktiver Modus deaktiviert", NotificationType.INFO)
    
    def handle_keyboard_shortcuts(self) -> None:
        """
        Verarbeitet Tastaturkürzel.
        """
        # Diese Methode würde in einer echten Implementierung die Tastatureingaben verarbeiten
        # Da dies in einer CLI-Umgebung komplex ist, zeigen wir nur eine Benachrichtigung
        self.show_notification("Tastaturkürzel werden verarbeitet...", NotificationType.INFO)

# Globale Instanz
_enhanced_ui: Optional[EnhancedUserInteraction] = None

def get_enhanced_ui() -> EnhancedUserInteraction:
    """
    Gibt die globale Instanz der erweiterten Benutzerinteraktion zurück.
    
    Returns:
        Instanz von EnhancedUserInteraction
    """
    global _enhanced_ui
    if _enhanced_ui is None:
        _enhanced_ui = EnhancedUserInteraction()
    return _enhanced_ui

# Hilfsfunktionen für die Verwendung außerhalb der Klasse
def show_notification(message: str, notification_type: NotificationType = NotificationType.INFO) -> None:
    """
    Zeigt eine Benachrichtigung an.
    
    Args:
        message: Nachrichtentext
        notification_type: Typ der Benachrichtigung
    """
    ui = get_enhanced_ui()
    ui.show_notification(message, notification_type)

def show_progress_bar(total: int, description: str = "Verarbeite...") -> Progress:
    """
    Zeigt eine erweiterte Fortschrittsanzeige an.
    
    Args:
        total: Gesamtanzahl der Schritte
        description: Beschreibungstext
        
    Returns:
        Rich Progress-Objekt
    """
    ui = get_enhanced_ui()
    return ui.show_progress_bar(total, description)

def show_live_progress(renderable: Any) -> Live:
    """
    Zeigt ein Live-Display an.
    
    Args:
        renderable: Das anzuzeigende Element
        
    Returns:
        Rich Live-Objekt
    """
    ui = get_enhanced_ui()
    return ui.show_live_progress(renderable)

def show_context_menu(title: str, options: list) -> int:
    """
    Zeigt ein Kontextmenü an.
    
    Args:
        title: Titel des Menüs
        options: Liste der Optionen
        
    Returns:
        Index der ausgewählten Option (0-basiert)
    """
    ui = get_enhanced_ui()
    return ui.show_context_menu(title, options)

def show_confirmation_dialog(message: str, default: bool = True) -> bool:
    """
    Zeigt einen Bestätigungsdialog an.
    
    Args:
        message: Nachrichtentext
        default: Standardwert (True für Ja, False für Nein)
        
    Returns:
        True, wenn bestätigt, False sonst
    """
    ui = get_enhanced_ui()
    return ui.show_confirmation_dialog(message, default)

def show_download_summary(stats: dict) -> None:
    """
    Zeigt eine Download-Zusammenfassung an.
    
    Args:
        stats: Statistikdaten
    """
    ui = get_enhanced_ui()
    ui.show_download_summary(stats)

def enable_interactive_mode() -> None:
    """Aktiviert den interaktiven Modus."""
    ui = get_enhanced_ui()
    ui.enable_interactive_mode()

def disable_interactive_mode() -> None:
    """Deaktiviert den interaktiven Modus."""
    ui = get_enhanced_ui()
    ui.disable_interactive_mode()

def handle_keyboard_shortcuts() -> None:
    """Verarbeitet Tastaturkürzel."""
    ui = get_enhanced_ui()
    ui.handle_keyboard_shortcuts()