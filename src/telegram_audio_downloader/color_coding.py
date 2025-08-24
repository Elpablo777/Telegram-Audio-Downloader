"""
Farbkodierung für den Telegram Audio Downloader.
"""

from enum import Enum
from typing import Dict, Optional
from dataclasses import dataclass

from rich.style import Style
from rich.color import Color


class ColorTheme(Enum):
    """Enumeration der verfügbaren Farbthemen."""
    DEFAULT = "default"
    DARK = "dark"
    LIGHT = "light"
    HIGH_CONTRAST = "high_contrast"


@dataclass
class ColorScheme:
    """Datenklasse für ein Farbschema."""
    name: str
    primary: str
    secondary: str
    accent: str
    success: str
    warning: str
    error: str
    info: str
    background: str
    text: str


class ColorManager:
    """Klasse zur Verwaltung von Farben und Farbthemen."""
    
    def __init__(self, theme: ColorTheme = ColorTheme.DEFAULT):
        """
        Initialisiert den ColorManager.
        
        Args:
            theme: Zu verwendendes Farbthema
        """
        self.theme = theme
        self.color_schemes = self._initialize_color_schemes()
        self.current_scheme = self.color_schemes[theme.value]
    
    def _initialize_color_schemes(self) -> Dict[str, ColorScheme]:
        """
        Initialisiert die verfügbaren Farbschemata.
        
        Returns:
            Dictionary mit Farbschemata
        """
        return {
            "default": ColorScheme(
                name="Standard",
                primary="#3498db",      # Blau
                secondary="#9b59b6",    # Lila
                accent="#e67e22",       # Orange
                success="#2ecc71",      # Grün
                warning="#f39c12",      # Orange
                error="#e74c3c",        # Rot
                info="#34495e",         # Dunkelgrau
                background="#ffffff",    # Weiß
                text="#2c3e50"          # Dunkelblau
            ),
            "dark": ColorScheme(
                name="Dunkel",
                primary="#1abc9c",      # Türkis
                secondary="#9b59b6",    # Lila
                accent="#e67e22",       # Orange
                success="#27ae60",      # Dunkelgrün
                warning="#f39c12",      # Orange
                error="#c0392b",        # Dunkelrot
                info="#7f8c8d",         # Grau
                background="#2c3e50",    # Dunkelblau
                text="#ecf0f1"          # Hellgrau
            ),
            "light": ColorScheme(
                name="Hell",
                primary="#5dade2",      # Helles Blau
                secondary="#bb8fce",    # Helles Lila
                accent="#e67e22",       # Orange
                success="#58d68d",      # Helles Grün
                warning="#f7dc6f",      # Gelb
                error="#f1948a",        # Helles Rot
                info="#85929e",         # Helles Grau
                background="#f8f9f9",    # Sehr hell
                text="#212f3d"          # Dunkelgrau
            ),
            "high_contrast": ColorScheme(
                name="Hoher Kontrast",
                primary="#0000ff",      # Reines Blau
                secondary="#ff00ff",    # Magenta
                accent="#ffff00",       # Gelb
                success="#00ff00",      # Reines Grün
                warning="#ffff00",      # Gelb
                error="#ff0000",        # Reines Rot
                info="#00ffff",         # Cyan
                background="#000000",    # Schwarz
                text="#ffffff"          # Weiß
            )
        }
    
    def set_theme(self, theme: ColorTheme):
        """
        Setzt das aktuelle Farbthema.
        
        Args:
            theme: Zu verwendendes Farbthema
        """
        self.theme = theme
        self.current_scheme = self.color_schemes[theme.value]
    
    def get_color(self, color_name: str) -> str:
        """
        Gibt eine Farbe aus dem aktuellen Schema zurück.
        
        Args:
            color_name: Name der Farbe (primary, secondary, success, warning, error, info, background, text)
            
        Returns:
            Hex-Farbcode
        """
        return getattr(self.current_scheme, color_name, "#000000")
    
    def get_rich_style(self, color_name: str) -> Style:
        """
        Gibt einen Rich-Style für eine Farbe zurück.
        
        Args:
            color_name: Name der Farbe
            
        Returns:
            Rich Style-Objekt
        """
        color_hex = self.get_color(color_name)
        return Style(color=color_hex)
    
    def get_status_color(self, status: str) -> str:
        """
        Gibt die Farbe für einen Status zurück.
        
        Args:
            status: Status (pending, downloading, completed, failed)
            
        Returns:
            Hex-Farbcode
        """
        status_colors = {
            "pending": self.get_color("info"),
            "downloading": self.get_color("primary"),
            "completed": self.get_color("success"),
            "failed": self.get_color("error")
        }
        return status_colors.get(status, self.get_color("text"))
    
    def get_file_type_color(self, file_type: str) -> str:
        """
        Gibt die Farbe für einen Dateityp zurück.
        
        Args:
            file_type: Dateityp (mp3, flac, m4a, wav, ogg)
            
        Returns:
            Hex-Farbcode
        """
        type_colors = {
            "mp3": self.get_color("primary"),
            "flac": self.get_color("secondary"),
            "m4a": self.get_color("warning"),
            "wav": self.get_color("info"),
            "ogg": self.get_color("success")
        }
        return type_colors.get(file_type.lower(), self.get_color("text"))
    
    def get_category_color(self, category: str) -> str:
        """
        Gibt die Farbe für eine Kategorie zurück.
        
        Args:
            category: Kategorie (classical, jazz, rock, pop, electronic, hiphop, country, reggae, latin, world, unclassified)
            
        Returns:
            Hex-Farbcode
        """
        category_colors = {
            "classical": "#8e44ad",    # Lila
            "jazz": "#d35400",         # Dunkelorange
            "rock": "#2c3e50",         # Dunkelgrau
            "pop": "#f39c12",          # Orange
            "electronic": "#1abc9c",   # Türkis
            "hiphop": "#34495e",       # Sehr dunkelgrau
            "country": "#27ae60",      # Grün
            "reggae": "#2ecc71",       # Hellgrün
            "latin": "#c0392b",        # Dunkelrot
            "world": "#f1c40f",        # Gelb
            "unclassified": "#95a5a6"  # Grau
        }
        return category_colors.get(category.lower(), self.get_color("text"))


# Farbkonstanten für direkte Verwendung
PRIMARY_COLOR = "#3498db"
SECONDARY_COLOR = "#9b59b6"
ACCENT_COLOR = "#e67e22"
SUCCESS_COLOR = "#2ecc71"
WARNING_COLOR = "#f39c12"
ERROR_COLOR = "#e74c3c"
INFO_COLOR = "#34495e"

# Globale Instanz
_color_manager: Optional[ColorManager] = None

def get_color_manager() -> ColorManager:
    """
    Gibt die globale Instanz des ColorManagers zurück.
    
    Returns:
        Instanz von ColorManager
    """
    global _color_manager
    if _color_manager is None:
        _color_manager = ColorManager()
    return _color_manager

def set_color_theme(theme: ColorTheme):
    """
    Setzt das aktuelle Farbthema.
    
    Args:
        theme: Zu verwendendes Farbthema
    """
    color_manager = get_color_manager()
    color_manager.set_theme(theme)

def get_color(color_name: str) -> str:
    """
    Gibt eine Farbe aus dem aktuellen Schema zurück.
    
    Args:
        color_name: Name der Farbe
        
    Returns:
        Hex-Farbcode
    """
    color_manager = get_color_manager()
    return color_manager.get_color(color_name)

def get_rich_style(color_name: str) -> Style:
    """
    Gibt einen Rich-Style für eine Farbe zurück.
    
    Args:
        color_name: Name der Farbe
        
    Returns:
        Rich Style-Objekt
    """
    color_manager = get_color_manager()
    return color_manager.get_rich_style(color_name)

def get_status_color(status: str) -> str:
    """
    Gibt die Farbe für einen Status zurück.
    
    Args:
        status: Status
        
    Returns:
        Hex-Farbcode
    """
    color_manager = get_color_manager()
    return color_manager.get_status_color(status)

def get_file_type_color(file_type: str) -> str:
    """
    Gibt die Farbe für einen Dateityp zurück.
    
    Args:
        file_type: Dateityp
        
    Returns:
        Hex-Farbcode
    """
    color_manager = get_color_manager()
    return color_manager.get_file_type_color(file_type)

def get_category_color(category: str) -> str:
    """
    Gibt die Farbe für eine Kategorie zurück.
    
    Args:
        category: Kategorie
        
    Returns:
        Hex-Farbcode
    """
    color_manager = get_color_manager()
    return color_manager.get_category_color(category)