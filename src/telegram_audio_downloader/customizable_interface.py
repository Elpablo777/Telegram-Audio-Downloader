"""
Anpassbare Oberfläche für den Telegram Audio Downloader.
"""

from typing import Optional, Dict, Any, List, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path

from rich.console import Console
from rich.theme import Theme
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.layout import Layout
from rich.align import Align
from rich.style import Style

from .logging_config import get_logger
from .i18n import _
from .color_coding import get_color_manager, ColorTheme, ColorScheme
from .keyboard_shortcuts import get_shortcut_manager, KeyBinding
from .custom_keybindings import get_keybinding_manager, KeyContext
from .accessibility import get_accessibility_manager, AccessibilityFeature

logger = get_logger(__name__)
console = Console()


class InterfaceComponent(Enum):
    """Enumeration der Oberflächenkomponenten."""
    HEADER = "header"
    FOOTER = "footer"
    SIDEBAR = "sidebar"
    MAIN_CONTENT = "main_content"
    STATUS_BAR = "status_bar"
    PROGRESS_BAR = "progress_bar"
    NOTIFICATION_AREA = "notification_area"
    INPUT_AREA = "input_area"
    OUTPUT_AREA = "output_area"
    MENU = "menu"
    TOOLBAR = "toolbar"


class LayoutType(Enum):
    """Enumeration der Layout-Typen."""
    DEFAULT = "default"
    COMPACT = "compact"
    WIDE = "wide"
    VERTICAL = "vertical"
    HORIZONTAL = "horizontal"
    CUSTOM = "custom"


@dataclass
class ComponentConfig:
    """Datenklasse für die Konfiguration einer Komponente."""
    component: InterfaceComponent
    visible: bool = True
    position: str = "top"  # top, bottom, left, right
    size: Optional[int] = None  # Prozentuale Größe
    style: Optional[str] = None  # Rich Style
    border_style: Optional[str] = None
    title: Optional[str] = None
    show_title: bool = True
    collapsible: bool = False
    collapsed: bool = False
    custom_content: Optional[Callable] = None


@dataclass
class InterfaceLayout:
    """Datenklasse für ein Oberflächenlayout."""
    name: str
    type: LayoutType
    components: List[ComponentConfig] = field(default_factory=list)
    description: str = ""
    is_default: bool = False
    theme: Optional[str] = None


@dataclass
class InterfaceTheme:
    """Datenklasse für ein Oberflächenthema."""
    name: str
    color_scheme: ColorScheme
    styles: Dict[str, str] = field(default_factory=dict)
    icons: Dict[str, str] = field(default_factory=dict)
    fonts: Dict[str, str] = field(default_factory=dict)
    layout: Optional[str] = None  # Name des Layouts


@dataclass
class UserInterfacePreferences:
    """Datenklasse für Benutzeroberflächenpräferenzen."""
    theme: str = "default"
    layout: str = "default"
    language: str = "en"
    show_line_numbers: bool = True
    word_wrap: bool = True
    max_width: int = 120
    refresh_rate: float = 1.0  # Hz
    enable_animations: bool = True
    animation_speed: float = 1.0
    show_timestamps: bool = False
    compact_mode: bool = False
    components: Dict[str, ComponentConfig] = field(default_factory=dict)
    custom_styles: Dict[str, str] = field(default_factory=dict)
    keybindings: Dict[str, str] = field(default_factory=dict)
    accessibility_features: List[str] = field(default_factory=list)


class CustomizableInterfaceManager:
    """Klasse zur Verwaltung der anpassbaren Oberfläche."""
    
    def __init__(self, config_dir: Optional[str] = None):
        """Initialisiert den CustomizableInterfaceManager."""
        self.console = console
        self.config_dir = Path(config_dir) if config_dir else Path.home() / ".telegram_audio_downloader"
        self.config_file = self.config_dir / "interface_config.json"
        self.themes_dir = self.config_dir / "themes"
        self.layouts_dir = self.config_dir / "layouts"
        
        # Erstelle Verzeichnisse, falls sie nicht existieren
        self.config_dir.mkdir(exist_ok=True)
        self.themes_dir.mkdir(exist_ok=True)
        self.layouts_dir.mkdir(exist_ok=True)
        
        # Manager für andere Systeme
        self.color_manager = get_color_manager()
        self.shortcut_manager = get_shortcut_manager()
        self.keybinding_manager = get_keybinding_manager()
        self.accessibility_manager = get_accessibility_manager()
        
        # Interne Speicher
        self.themes: Dict[str, InterfaceTheme] = {}
        self.layouts: Dict[str, InterfaceLayout] = {}
        self.preferences = UserInterfacePreferences()
        
        # Standard-Themen und Layouts initialisieren
        self._initialize_default_themes()
        self._initialize_default_layouts()
        
        # Konfiguration laden
        self._load_configuration()
    
    def _initialize_default_themes(self):
        """Initialisiert die standardmäßigen Themen."""
        # Standard-Thema
        default_theme = InterfaceTheme(
            name="default",
            color_scheme=ColorScheme(
                primary="blue",
                secondary="cyan",
                accent="magenta",
                background="black",
                text="white",
                success="green",
                warning="yellow",
                error="red",
                info="blue"
            ),
            styles={
                "header": "bold white on blue",
                "footer": "dim white on black",
                "sidebar": "white on bright_black",
                "status_bar": "white on blue",
                "progress_bar": "green",
                "notification": "yellow",
                "error": "bold red",
                "success": "bold green",
                "warning": "bold yellow"
            },
            icons={
                "download": "📥",
                "search": "🔍",
                "settings": "⚙️",
                "help": "❓",
                "info": "ℹ️",
                "success": "✅",
                "warning": "⚠️",
                "error": "❌",
                "notification": "🔔"
            }
        )
        
        self.themes["default"] = default_theme
        
        # Dunkles Thema
        dark_theme = InterfaceTheme(
            name="dark",
            color_scheme=ColorScheme(
                primary="bright_blue",
                secondary="bright_cyan",
                accent="bright_magenta",
                background="black",
                text="bright_white",
                success="bright_green",
                warning="bright_yellow",
                error="bright_red",
                info="bright_blue"
            ),
            styles={
                "header": "bold bright_white on bright_black",
                "footer": "dim bright_white on black",
                "sidebar": "bright_white on black",
                "status_bar": "bright_white on bright_black",
                "progress_bar": "bright_green",
                "notification": "bright_yellow",
                "error": "bold bright_red",
                "success": "bold bright_green",
                "warning": "bold bright_yellow"
            },
            icons={
                "download": "📥",
                "search": "🔍",
                "settings": "⚙️",
                "help": "❓",
                "info": "ℹ️",
                "success": "✅",
                "warning": "⚠️",
                "error": "❌",
                "notification": "🔔"
            }
        )
        
        self.themes["dark"] = dark_theme
        
        # Helles Thema
        light_theme = InterfaceTheme(
            name="light",
            color_scheme=ColorScheme(
                primary="blue",
                secondary="cyan",
                accent="magenta",
                background="white",
                text="black",
                success="green",
                warning="orange",
                error="red",
                info="blue"
            ),
            styles={
                "header": "bold black on white",
                "footer": "dim black on bright_white",
                "sidebar": "black on bright_white",
                "status_bar": "black on white",
                "progress_bar": "green",
                "notification": "orange",
                "error": "bold red",
                "success": "bold green",
                "warning": "bold orange"
            },
            icons={
                "download": "📥",
                "search": "🔍",
                "settings": "⚙️",
                "help": "❓",
                "info": "ℹ️",
                "success": "✅",
                "warning": "⚠️",
                "error": "❌",
                "notification": "🔔"
            }
        )
        
        self.themes["light"] = light_theme
    
    def _initialize_default_layouts(self):
        """Initialisiert die standardmäßigen Layouts."""
        # Standard-Layout
        default_layout = InterfaceLayout(
            name="default",
            type=LayoutType.DEFAULT,
            description=_("default_layout_description"),
            is_default=True,
            components=[
                ComponentConfig(
                    component=InterfaceComponent.HEADER,
                    position="top",
                    style="header",
                    title=_("application_header"),
                    show_title=True
                ),
                ComponentConfig(
                    component=InterfaceComponent.FOOTER,
                    position="bottom",
                    style="footer",
                    title=_("status_footer"),
                    show_title=True
                ),
                ComponentConfig(
                    component=InterfaceComponent.SIDEBAR,
                    position="left",
                    size=20,
                    style="sidebar",
                    title=_("navigation"),
                    show_title=True,
                    collapsible=True
                ),
                ComponentConfig(
                    component=InterfaceComponent.MAIN_CONTENT,
                    position="center",
                    style="default"
                ),
                ComponentConfig(
                    component=InterfaceComponent.STATUS_BAR,
                    position="bottom",
                    style="status_bar",
                    title=_("status"),
                    show_title=False
                ),
                ComponentConfig(
                    component=InterfaceComponent.NOTIFICATION_AREA,
                    position="top",
                    style="notification",
                    title=_("notifications"),
                    show_title=True,
                    collapsible=True,
                    collapsed=True
                )
            ]
        )
        
        self.layouts["default"] = default_layout
        
        # Kompaktes Layout
        compact_layout = InterfaceLayout(
            name="compact",
            type=LayoutType.COMPACT,
            description=_("compact_layout_description"),
            components=[
                ComponentConfig(
                    component=InterfaceComponent.HEADER,
                    position="top",
                    style="header",
                    title=_("app_title"),
                    show_title=True
                ),
                ComponentConfig(
                    component=InterfaceComponent.MAIN_CONTENT,
                    position="center",
                    style="default"
                ),
                ComponentConfig(
                    component=InterfaceComponent.STATUS_BAR,
                    position="bottom",
                    style="status_bar",
                    show_title=False
                )
            ]
        )
        
        self.layouts["compact"] = compact_layout
        
        # Breites Layout
        wide_layout = InterfaceLayout(
            name="wide",
            type=LayoutType.WIDE,
            description=_("wide_layout_description"),
            components=[
                ComponentConfig(
                    component=InterfaceComponent.HEADER,
                    position="top",
                    style="header",
                    title=_("application_header"),
                    show_title=True
                ),
                ComponentConfig(
                    component=InterfaceComponent.SIDEBAR,
                    position="left",
                    size=15,
                    style="sidebar",
                    title=_("navigation"),
                    show_title=True,
                    collapsible=True
                ),
                ComponentConfig(
                    component=InterfaceComponent.MAIN_CONTENT,
                    position="center",
                    style="default"
                ),
                ComponentConfig(
                    component=InterfaceComponent.SIDEBAR,
                    position="right",
                    size=15,
                    style="sidebar",
                    title=_("tools"),
                    show_title=True,
                    collapsible=True
                ),
                ComponentConfig(
                    component=InterfaceComponent.FOOTER,
                    position="bottom",
                    style="footer",
                    title=_("status_footer"),
                    show_title=True
                )
            ]
        )
        
        self.layouts["wide"] = wide_layout
    
    def _load_configuration(self):
        """Lädt die Oberflächenkonfiguration aus der Datei."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # Konvertiere das Dictionary in ein UserInterfacePreferences-Objekt
                self.preferences = UserInterfacePreferences(**config_data)
                logger.debug("Oberflächenkonfiguration geladen")
            except Exception as e:
                logger.warning(f"Fehler beim Laden der Oberflächenkonfiguration: {e}")
                # Verwende Standardkonfiguration
                self.preferences = UserInterfacePreferences()
        else:
            # Verwende Standardkonfiguration
            self.preferences = UserInterfacePreferences()
            self._save_configuration()
    
    def _save_configuration(self):
        """Speichert die Oberflächenkonfiguration in der Datei."""
        try:
            # Konvertiere das UserInterfacePreferences-Objekt in ein Dictionary
            config_data = {
                "theme": self.preferences.theme,
                "layout": self.preferences.layout,
                "language": self.preferences.language,
                "show_line_numbers": self.preferences.show_line_numbers,
                "word_wrap": self.preferences.word_wrap,
                "max_width": self.preferences.max_width,
                "refresh_rate": self.preferences.refresh_rate,
                "enable_animations": self.preferences.enable_animations,
                "animation_speed": self.preferences.animation_speed,
                "show_timestamps": self.preferences.show_timestamps,
                "compact_mode": self.preferences.compact_mode,
                "components": {k: {
                    "component": v.component.value,
                    "visible": v.visible,
                    "position": v.position,
                    "size": v.size,
                    "style": v.style,
                    "border_style": v.border_style,
                    "title": v.title,
                    "show_title": v.show_title,
                    "collapsible": v.collapsible,
                    "collapsed": v.collapsed
                } for k, v in self.preferences.components.items()},
                "custom_styles": self.preferences.custom_styles,
                "keybindings": self.preferences.keybindings,
                "accessibility_features": self.preferences.accessibility_features
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            logger.debug("Oberflächenkonfiguration gespeichert")
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Oberflächenkonfiguration: {e}")
    
    def set_theme(self, theme_name: str):
        """
        Setzt das aktuelle Thema.
        
        Args:
            theme_name: Name des Themas
        """
        if theme_name not in self.themes:
            logger.warning(f"Thema '{theme_name}' nicht gefunden")
            return
        
        self.preferences.theme = theme_name
        self._save_configuration()
        logger.debug(f"Thema gesetzt: {theme_name}")
    
    def get_theme(self) -> Optional[InterfaceTheme]:
        """
        Gibt das aktuelle Thema zurück.
        
        Returns:
            Aktuelles Thema oder None
        """
        return self.themes.get(self.preferences.theme)
    
    def set_layout(self, layout_name: str):
        """
        Setzt das aktuelle Layout.
        
        Args:
            layout_name: Name des Layouts
        """
        if layout_name not in self.layouts:
            logger.warning(f"Layout '{layout_name}' nicht gefunden")
            return
        
        self.preferences.layout = layout_name
        self._save_configuration()
        logger.debug(f"Layout gesetzt: {layout_name}")
    
    def get_layout(self) -> Optional[InterfaceLayout]:
        """
        Gibt das aktuelle Layout zurück.
        
        Returns:
            Aktuelles Layout oder None
        """
        return self.layouts.get(self.preferences.layout)
    
    def set_preference(self, key: str, value: Any):
        """
        Setzt eine Benutzeroberflächenpräferenz.
        
        Args:
            key: Name der Präferenz
            value: Wert der Präferenz
        """
        # Verwende setattr, um das Attribut dynamisch zu setzen
        if hasattr(self.preferences, key):
            setattr(self.preferences, key, value)
            self._save_configuration()
            logger.debug(f"Präferenz gesetzt: {key} = {value}")
        else:
            logger.warning(f"Unbekannte Präferenz: {key}")
    
    def get_preference(self, key: str, default: Any = None) -> Any:
        """
        Gibt eine Benutzeroberflächenpräferenz zurück.
        
        Args:
            key: Name der Präferenz
            default: Standardwert, falls die Präferenz nicht existiert
            
        Returns:
            Wert der Präferenz oder Standardwert
        """
        if hasattr(self.preferences, key):
            return getattr(self.preferences, key)
        return default
    
    def toggle_component_visibility(self, component: InterfaceComponent):
        """
        Schaltet die Sichtbarkeit einer Komponente um.
        
        Args:
            component: Die Komponente
        """
        component_name = component.value
        
        if component_name in self.preferences.components:
            # Toggle die Sichtbarkeit
            self.preferences.components[component_name].visible = not self.preferences.components[component_name].visible
        else:
            # Erstelle eine neue Komponentenkonfiguration
            self.preferences.components[component_name] = ComponentConfig(
                component=component,
                visible=False
            )
        
        self._save_configuration()
        logger.debug(f"Komponentensichtbarkeit umgeschaltet: {component_name}")
    
    def customize_component(self, component: InterfaceComponent, **kwargs):
        """
        Passt eine Komponente an.
        
        Args:
            component: Die Komponente
            **kwargs: Eigenschaften zum Anpassen
        """
        component_name = component.value
        
        if component_name not in self.preferences.components:
            # Erstelle eine neue Komponentenkonfiguration
            self.preferences.components[component_name] = ComponentConfig(component=component)
        
        # Aktualisiere die Eigenschaften
        for key, value in kwargs.items():
            if hasattr(self.preferences.components[component_name], key):
                setattr(self.preferences.components[component_name], key, value)
        
        self._save_configuration()
        logger.debug(f"Komponente angepasst: {component_name}")
    
    def apply_custom_style(self, element: str, style: str):
        """
        Wendet einen benutzerdefinierten Stil an.
        
        Args:
            element: Name des Elements
            style: Rich Style-String
        """
        self.preferences.custom_styles[element] = style
        self._save_configuration()
        logger.debug(f"Benutzerdefinierter Stil angewendet: {element} = {style}")
    
    def get_custom_style(self, element: str) -> Optional[str]:
        """
        Gibt einen benutzerdefinierten Stil zurück.
        
        Args:
            element: Name des Elements
            
        Returns:
            Benutzerdefinierter Stil oder None
        """
        return self.preferences.custom_styles.get(element)
    
    def render_component(self, component: InterfaceComponent, content: Any = None) -> Optional[Panel]:
        """
        Rendert eine Komponente.
        
        Args:
            component: Die zu rendernde Komponente
            content: Inhalt der Komponente
            
        Returns:
            Gerendertes Panel oder None
        """
        component_name = component.value
        component_config = self.preferences.components.get(component_name)
        
        # Wenn die Komponente nicht konfiguriert ist, verwende Standardkonfiguration
        if not component_config:
            component_config = ComponentConfig(component=component)
        
        # Wenn die Komponente nicht sichtbar ist, rendere sie nicht
        if not component_config.visible:
            return None
        
        # Wenn ein benutzerdefinierter Inhalt angegeben ist, verwende ihn
        if component_config.custom_content:
            try:
                content = component_config.custom_content()
            except Exception as e:
                logger.warning(f"Fehler beim Rendern des benutzerdefinierten Inhalts: {e}")
                content = str(content) if content is not None else ""
        else:
            content = str(content) if content is not None else ""
        
        # Erstelle das Panel
        panel_kwargs = {}
        
        # Titel
        if component_config.show_title and component_config.title:
            panel_kwargs["title"] = component_config.title
        elif component_config.show_title:
            # Verwende Standardtitel basierend auf der Komponente
            title_map = {
                InterfaceComponent.HEADER: _("header"),
                InterfaceComponent.FOOTER: _("footer"),
                InterfaceComponent.SIDEBAR: _("sidebar"),
                InterfaceComponent.STATUS_BAR: _("status_bar"),
                InterfaceComponent.NOTIFICATION_AREA: _("notifications"),
                InterfaceComponent.INPUT_AREA: _("input"),
                InterfaceComponent.OUTPUT_AREA: _("output"),
                InterfaceComponent.MENU: _("menu"),
                InterfaceComponent.TOOLBAR: _("toolbar")
            }
            panel_kwargs["title"] = title_map.get(component, component_name)
        
        # Stil
        style = component_config.style
        if not style and self.preferences.theme in self.themes:
            theme = self.themes[self.preferences.theme]
            style = theme.styles.get(component_name)
        
        if style:
            panel_kwargs["style"] = style
        
        # Rahmenstil
        if component_config.border_style:
            panel_kwargs["border_style"] = component_config.border_style
        
        # Erstelle und gib das Panel zurück
        return Panel(content, **panel_kwargs)
    
    def show_interface_preview(self):
        """Zeigt eine Vorschau der aktuellen Oberflächenkonfiguration an."""
        # Hole das aktuelle Layout
        layout = self.get_layout()
        if not layout:
            layout = self.layouts.get("default")
        
        if not layout:
            logger.warning("Kein Layout verfügbar")
            return
        
        # Erstelle eine Tabelle für die Vorschau
        table = Table(title=_("interface_preview"))
        table.add_column(_("component"), style="cyan")
        table.add_column(_("visible"), style="green")
        table.add_column(_("position"), style="magenta")
        table.add_column(_("size"), style="yellow")
        
        # Füge Komponenten hinzu
        for component_config in layout.components:
            visible = "✓" if component_config.visible else "✗"
            size = f"{component_config.size}%" if component_config.size else "-"
            
            table.add_row(
                component_config.component.value,
                visible,
                component_config.position,
                size
            )
        
        # Zeige die Tabelle an
        console.print(table)
        
        # Zeige aktuelle Präferenzen an
        pref_table = Table(title=_("current_preferences"))
        pref_table.add_column(_("preference"), style="cyan")
        pref_table.add_column(_("value"), style="magenta")
        
        pref_table.add_row(_("theme"), self.preferences.theme)
        pref_table.add_row(_("layout"), self.preferences.layout)
        pref_table.add_row(_("language"), self.preferences.language)
        pref_table.add_row(_("compact_mode"), str(self.preferences.compact_mode))
        pref_table.add_row(_("animations"), str(self.preferences.enable_animations))
        
        console.print(pref_table)
    
    def reset_to_defaults(self):
        """Setzt die Oberflächenkonfiguration auf die Standardwerte zurück."""
        self.preferences = UserInterfacePreferences()
        self._save_configuration()
        logger.debug("Oberflächenkonfiguration auf Standardwerte zurückgesetzt")
    
    def export_theme(self, theme_name: str, file_path: str):
        """
        Exportiert ein Thema in eine Datei.
        
        Args:
            theme_name: Name des Themas
            file_path: Zielpfad
        """
        if theme_name not in self.themes:
            logger.warning(f"Thema '{theme_name}' nicht gefunden")
            return
        
        theme = self.themes[theme_name]
        
        # Konvertiere das Thema in ein serialisierbares Format
        theme_data = {
            "name": theme.name,
            "color_scheme": {
                "primary": theme.color_scheme.primary,
                "secondary": theme.color_scheme.secondary,
                "accent": theme.color_scheme.accent,
                "background": theme.color_scheme.background,
                "text": theme.color_scheme.text,
                "success": theme.color_scheme.success,
                "warning": theme.color_scheme.warning,
                "error": theme.color_scheme.error,
                "info": theme.color_scheme.info
            },
            "styles": theme.styles,
            "icons": theme.icons,
            "fonts": theme.fonts,
            "layout": theme.layout
        }
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(theme_data, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"Thema exportiert: {file_path}")
        except Exception as e:
            logger.error(f"Fehler beim Exportieren des Themas: {e}")
    
    def import_theme(self, file_path: str) -> Optional[str]:
        """
        Importiert ein Thema aus einer Datei.
        
        Args:
            file_path: Pfad zur Themendatei
            
        Returns:
            Name des importierten Themas oder None
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                theme_data = json.load(f)
            
            # Erstelle ein InterfaceTheme-Objekt aus den Daten
            color_scheme = ColorScheme(
                primary=theme_data["color_scheme"]["primary"],
                secondary=theme_data["color_scheme"]["secondary"],
                accent=theme_data["color_scheme"]["accent"],
                background=theme_data["color_scheme"]["background"],
                text=theme_data["color_scheme"]["text"],
                success=theme_data["color_scheme"]["success"],
                warning=theme_data["color_scheme"]["warning"],
                error=theme_data["color_scheme"]["error"],
                info=theme_data["color_scheme"]["info"]
            )
            
            theme = InterfaceTheme(
                name=theme_data["name"],
                color_scheme=color_scheme,
                styles=theme_data["styles"],
                icons=theme_data["icons"],
                fonts=theme_data["fonts"],
                layout=theme_data.get("layout")
            )
            
            # Füge das Thema hinzu
            self.themes[theme.name] = theme
            
            logger.debug(f"Thema importiert: {theme.name}")
            return theme.name
        except Exception as e:
            logger.error(f"Fehler beim Importieren des Themas: {e}")
            return None


# Globale Instanz
_customizable_interface_manager: Optional[CustomizableInterfaceManager] = None


def get_interface_manager() -> CustomizableInterfaceManager:
    """
    Gibt die globale Instanz des CustomizableInterfaceManagers zurück.
    
    Returns:
        Instanz von CustomizableInterfaceManager
    """
    global _customizable_interface_manager
    if _customizable_interface_manager is None:
        _customizable_interface_manager = CustomizableInterfaceManager()
    return _customizable_interface_manager


def set_theme(theme_name: str):
    """
    Setzt das aktuelle Thema.
    
    Args:
        theme_name: Name des Themas
    """
    manager = get_interface_manager()
    manager.set_theme(theme_name)


def get_theme() -> Optional[InterfaceTheme]:
    """
    Gibt das aktuelle Thema zurück.
    
    Returns:
        Aktuelles Thema oder None
    """
    manager = get_interface_manager()
    return manager.get_theme()


def set_layout(layout_name: str):
    """
    Setzt das aktuelle Layout.
    
    Args:
        layout_name: Name des Layouts
    """
    manager = get_interface_manager()
    manager.set_layout(layout_name)


def get_layout() -> Optional[InterfaceLayout]:
    """
    Gibt das aktuelle Layout zurück.
    
    Returns:
        Aktuelles Layout oder None
    """
    manager = get_interface_manager()
    return manager.get_layout()


def set_preference(key: str, value: Any):
    """
    Setzt eine Benutzeroberflächenpräferenz.
    
    Args:
        key: Name der Präferenz
        value: Wert der Präferenz
    """
    manager = get_interface_manager()
    manager.set_preference(key, value)


def get_preference(key: str, default: Any = None) -> Any:
    """
    Gibt eine Benutzeroberflächenpräferenz zurück.
    
    Args:
        key: Name der Präferenz
        default: Standardwert, falls die Präferenz nicht existiert
        
    Returns:
        Wert der Präferenz oder Standardwert
    """
    manager = get_interface_manager()
    return manager.get_preference(key, default)


def toggle_component_visibility(component: InterfaceComponent):
    """
    Schaltet die Sichtbarkeit einer Komponente um.
    
    Args:
        component: Die Komponente
    """
    manager = get_interface_manager()
    manager.toggle_component_visibility(component)


def customize_component(component: InterfaceComponent, **kwargs):
    """
    Passt eine Komponente an.
    
    Args:
        component: Die Komponente
        **kwargs: Eigenschaften zum Anpassen
    """
    manager = get_interface_manager()
    manager.customize_component(component, **kwargs)


def render_component(component: InterfaceComponent, content: Any = None) -> Optional[Panel]:
    """
    Rendert eine Komponente.
    
    Args:
        component: Die zu rendernde Komponente
        content: Inhalt der Komponente
        
    Returns:
        Gerendertes Panel oder None
    """
    manager = get_interface_manager()
    return manager.render_component(component, content)


def show_interface_preview():
    """Zeigt eine Vorschau der aktuellen Oberflächenkonfiguration an."""
    manager = get_interface_manager()
    manager.show_interface_preview()


def reset_to_defaults():
    """Setzt die Oberflächenkonfiguration auf die Standardwerte zurück."""
    manager = get_interface_manager()
    manager.reset_to_defaults()


# Deutsche Übersetzungen für anpassbare Oberfläche
CUSTOMIZABLE_INTERFACE_TRANSLATIONS_DE = {
    "default_layout_description": "Standardlayout mit Header, Sidebar und Footer",
    "compact_layout_description": "Kompaktes Layout für kleine Bildschirme",
    "wide_layout_description": "Breites Layout mit zwei Sidebars",
    "application_header": "Telegram Audio Downloader",
    "status_footer": "Bereit",
    "navigation": "Navigation",
    "status": "Status",
    "notifications": "Benachrichtigungen",
    "app_title": "TAD",
    "header": "Kopfzeile",
    "footer": "Fußzeile",
    "sidebar": "Seitenleiste",
    "status_bar": "Statusleiste",
    "input": "Eingabe",
    "output": "Ausgabe",
    "menu": "Menü",
    "toolbar": "Werkzeugleiste",
    "interface_preview": "Oberflächenvorschau",
    "component": "Komponente",
    "visible": "Sichtbar",
    "position": "Position",
    "size": "Größe",
    "current_preferences": "Aktuelle Einstellungen",
    "preference": "Einstellung",
    "value": "Wert",
    "theme": "Thema",
    "layout": "Layout",
    "language": "Sprache",
    "compact_mode": "Kompaktmodus",
    "animations": "Animationen",
}