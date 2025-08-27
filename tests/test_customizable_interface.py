"""
Tests für die anpassbare Oberfläche im Telegram Audio Downloader.
"""

import pytest
import json
import tempfile
from unittest.mock import Mock, patch
from pathlib import Path
from typing import Any, Optional

from src.telegram_audio_downloader.customizable_interface import (
    InterfaceComponent,
    LayoutType,
    ComponentConfig,
    InterfaceLayout,
    InterfaceTheme,
    UserInterfacePreferences,
    CustomizableInterfaceManager,
    get_interface_manager,
    set_theme,
    get_theme,
    set_layout,
    get_layout,
    set_preference,
    get_preference,
    toggle_component_visibility,
    customize_component,
    render_component,
    show_interface_preview,
    reset_to_defaults
)


class TestInterfaceComponent:
    """Testfälle für die InterfaceComponent-Enumeration."""
    
    def test_interface_component_values(self):
        """Testet die Werte der InterfaceComponent-Enumeration."""
        assert InterfaceComponent.HEADER.value == "header"
        assert InterfaceComponent.FOOTER.value == "footer"
        assert InterfaceComponent.SIDEBAR.value == "sidebar"
        assert InterfaceComponent.MAIN_CONTENT.value == "main_content"
        assert InterfaceComponent.STATUS_BAR.value == "status_bar"
        assert InterfaceComponent.PROGRESS_BAR.value == "progress_bar"
        assert InterfaceComponent.NOTIFICATION_AREA.value == "notification_area"
        assert InterfaceComponent.INPUT_AREA.value == "input_area"
        assert InterfaceComponent.OUTPUT_AREA.value == "output_area"
        assert InterfaceComponent.MENU.value == "menu"
        assert InterfaceComponent.TOOLBAR.value == "toolbar"


class TestLayoutType:
    """Testfälle für die LayoutType-Enumeration."""
    
    def test_layout_type_values(self):
        """Testet die Werte der LayoutType-Enumeration."""
        assert LayoutType.DEFAULT.value == "default"
        assert LayoutType.COMPACT.value == "compact"
        assert LayoutType.WIDE.value == "wide"
        assert LayoutType.VERTICAL.value == "vertical"
        assert LayoutType.HORIZONTAL.value == "horizontal"
        assert LayoutType.CUSTOM.value == "custom"


class TestComponentConfig:
    """Testfälle für die ComponentConfig-Datenklasse."""
    
    def test_initialization(self):
        """Testet die Initialisierung der ComponentConfig-Klasse."""
        config = ComponentConfig(
            component=InterfaceComponent.HEADER,
            visible=True,
            position="top",
            size=10,
            style="bold",
            border_style="blue",
            title="Test Header",
            show_title=True,
            collapsible=True,
            collapsed=False
        )
        
        assert config.component == InterfaceComponent.HEADER
        assert config.visible == True
        assert config.position == "top"
        assert config.size == 10
        assert config.style == "bold"
        assert config.border_style == "blue"
        assert config.title == "Test Header"
        assert config.show_title == True
        assert config.collapsible == True
        assert config.collapsed == False
        assert config.custom_content is None


class TestInterfaceLayout:
    """Testfälle für die InterfaceLayout-Datenklasse."""
    
    def test_initialization(self):
        """Testet die Initialisierung der InterfaceLayout-Klasse."""
        components = [
            ComponentConfig(component=InterfaceComponent.HEADER, position="top"),
            ComponentConfig(component=InterfaceComponent.FOOTER, position="bottom")
        ]
        
        layout = InterfaceLayout(
            name="test_layout",
            type=LayoutType.DEFAULT,
            components=components,
            description="A test layout",
            is_default=True,
            theme="dark"
        )
        
        assert layout.name == "test_layout"
        assert layout.type == LayoutType.DEFAULT
        assert layout.components == components
        assert layout.description == "A test layout"
        assert layout.is_default == True
        assert layout.theme == "dark"


class TestInterfaceTheme:
    """Testfälle für die InterfaceTheme-Datenklasse."""
    
    def test_initialization(self):
        """Testet die Initialisierung der InterfaceTheme-Klasse."""
        from src.telegram_audio_downloader.color_coding import ColorScheme
        
        color_scheme = ColorScheme(
            name="Test Theme",
            primary="blue",
            secondary="cyan",
            accent="magenta",
            background="black",
            text="white",
            success="green",
            warning="yellow",
            error="red",
            info="blue"
        )
        
        theme = InterfaceTheme(
            name="test_theme",
            color_scheme=color_scheme,
            styles={"header": "bold white on blue"},
            icons={"download": "📥"},
            fonts={"default": "monospace"},
            layout="default"
        )
        
        assert theme.name == "test_theme"
        assert theme.color_scheme == color_scheme
        assert theme.styles == {"header": "bold white on blue"}
        assert theme.icons == {"download": "📥"}
        assert theme.fonts == {"default": "monospace"}
        assert theme.layout == "default"


class TestUserInterfacePreferences:
    """Testfälle für die UserInterfacePreferences-Datenklasse."""
    
    def test_initialization(self):
        """Testet die Initialisierung der UserInterfacePreferences-Klasse."""
        components = {
            "header": ComponentConfig(component=InterfaceComponent.HEADER)
        }
        
        preferences = UserInterfacePreferences(
            theme="dark",
            layout="compact",
            language="de",
            show_line_numbers=False,
            word_wrap=True,
            max_width=100,
            refresh_rate=2.0,
            enable_animations=False,
            animation_speed=0.5,
            show_timestamps=True,
            compact_mode=True,
            components=components,
            custom_styles={"header": "bold"},
            keybindings={"ctrl+d": "download"},
            accessibility_features=["screen_reader", "high_contrast"]
        )
        
        assert preferences.theme == "dark"
        assert preferences.layout == "compact"
        assert preferences.language == "de"
        assert preferences.show_line_numbers == False
        assert preferences.word_wrap == True
        assert preferences.max_width == 100
        assert preferences.refresh_rate == 2.0
        assert preferences.enable_animations == False
        assert preferences.animation_speed == 0.5
        assert preferences.show_timestamps == True
        assert preferences.compact_mode == True
        assert preferences.components == components
        assert preferences.custom_styles == {"header": "bold"}
        assert preferences.keybindings == {"ctrl+d": "download"}
        assert preferences.accessibility_features == ["screen_reader", "high_contrast"]


class TestCustomizableInterfaceManager:
    """Testfälle für die CustomizableInterfaceManager-Klasse."""
    
    def test_initialization(self):
        """Testet die Initialisierung des CustomizableInterfaceManagers."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = CustomizableInterfaceManager(temp_dir)
            
            assert manager is not None
            assert hasattr(manager, 'console')
            assert hasattr(manager, 'config_dir')
            assert hasattr(manager, 'themes')
            assert hasattr(manager, 'layouts')
            assert hasattr(manager, 'preferences')
            
            # Überprüfe, ob Standard-Themen und Layouts initialisiert wurden
            assert "default" in manager.themes
            assert "dark" in manager.themes
            assert "light" in manager.themes
            assert "default" in manager.layouts
            assert "compact" in manager.layouts
            assert "wide" in manager.layouts
    
    def test_initialize_default_themes(self):
        """Testet die Initialisierung der Standard-Themen."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = CustomizableInterfaceManager(temp_dir)
            
            # Überprüfe, ob die Standard-Themen korrekt initialisiert wurden
            assert "default" in manager.themes
            assert "dark" in manager.themes
            assert "light" in manager.themes
            
            # Überprüfe die Eigenschaften des Standard-Themas
            default_theme = manager.themes["default"]
            assert default_theme.name == "default"
            assert default_theme.color_scheme.primary == "blue"
            assert "header" in default_theme.styles
    
    def test_initialize_default_layouts(self):
        """Testet die Initialisierung der Standard-Layouts."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = CustomizableInterfaceManager(temp_dir)
            
            # Überprüfe, ob die Standard-Layouts korrekt initialisiert wurden
            assert "default" in manager.layouts
            assert "compact" in manager.layouts
            assert "wide" in manager.layouts
            
            # Überprüfe die Eigenschaften des Standard-Layouts
            default_layout = manager.layouts["default"]
            assert default_layout.name == "default"
            assert default_layout.type == LayoutType.DEFAULT
            assert len(default_layout.components) > 0
    
    def test_load_configuration(self):
        """Testet das Laden der Konfiguration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            config_file = temp_path / "interface_config.json"
            
            # Erstelle eine Testkonfigurationsdatei
            test_config = {
                "theme": "dark",
                "layout": "compact",
                "language": "de",
                "show_line_numbers": False,
                "word_wrap": True
            }
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(test_config, f)
            
            # Erstelle den Manager und überprüfe, ob die Konfiguration geladen wurde
            manager = CustomizableInterfaceManager(temp_dir)
            assert manager.preferences.theme == "dark"
            assert manager.preferences.layout == "compact"
            assert manager.preferences.language == "de"
            assert manager.preferences.show_line_numbers == False
            assert manager.preferences.word_wrap == True
    
    def test_save_configuration(self):
        """Testet das Speichern der Konfiguration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            config_file = temp_path / "interface_config.json"
            
            # Erstelle den Manager und ändere einige Einstellungen
            manager = CustomizableInterfaceManager(temp_dir)
            manager.preferences.theme = "dark"
            manager.preferences.layout = "compact"
            
            # Speichere die Konfiguration
            manager._save_configuration()
            
            # Überprüfe, ob die Datei erstellt wurde
            assert config_file.exists()
            
            # Lade die Konfiguration und überprüfe die Werte
            with open(config_file, 'r', encoding='utf-8') as f:
                saved_config = json.load(f)
            
            assert saved_config["theme"] == "dark"
            assert saved_config["layout"] == "compact"
    
    def test_set_theme_valid(self):
        """Testet das Setzen eines gültigen Themas."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = CustomizableInterfaceManager(temp_dir)
            
            # Setze ein gültiges Thema
            manager.set_theme("dark")
            
            assert manager.preferences.theme == "dark"
    
    def test_set_theme_invalid(self):
        """Testet das Setzen eines ungültigen Themas."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = CustomizableInterfaceManager(temp_dir)
            
            # Speichere das ursprüngliche Thema
            original_theme = manager.preferences.theme
            
            # Versuche, ein ungültiges Thema zu setzen
            manager.set_theme("invalid_theme")
            
            # Das Thema sollte unverändert bleiben
            assert manager.preferences.theme == original_theme
    
    def test_get_theme(self):
        """Testet das Abrufen des aktuellen Themas."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = CustomizableInterfaceManager(temp_dir)
            
            # Setze ein Thema
            manager.set_theme("dark")
            
            # Hole das aktuelle Thema
            theme = manager.get_theme()
            
            assert theme is not None
            assert theme.name == "dark"
    
    def test_set_layout_valid(self):
        """Testet das Setzen eines gültigen Layouts."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = CustomizableInterfaceManager(temp_dir)
            
            # Setze ein gültiges Layout
            manager.set_layout("compact")
            
            assert manager.preferences.layout == "compact"
    
    def test_set_layout_invalid(self):
        """Testet das Setzen eines ungültigen Layouts."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = CustomizableInterfaceManager(temp_dir)
            
            # Speichere das ursprüngliche Layout
            original_layout = manager.preferences.layout
            
            # Versuche, ein ungültiges Layout zu setzen
            manager.set_layout("invalid_layout")
            
            # Das Layout sollte unverändert bleiben
            assert manager.preferences.layout == original_layout
    
    def test_get_layout(self):
        """Testet das Abrufen des aktuellen Layouts."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = CustomizableInterfaceManager(temp_dir)
            
            # Setze ein Layout
            manager.set_layout("compact")
            
            # Hole das aktuelle Layout
            layout = manager.get_layout()
            
            assert layout is not None
            assert layout.name == "compact"
    
    def test_set_preference(self):
        """Testet das Setzen einer Präferenz."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = CustomizableInterfaceManager(temp_dir)
            
            # Setze eine Präferenz
            manager.set_preference("theme", "dark")
            manager.set_preference("max_width", 100)
            
            assert manager.preferences.theme == "dark"
            assert manager.preferences.max_width == 100
    
    def test_get_preference(self):
        """Testet das Abrufen einer Präferenz."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = CustomizableInterfaceManager(temp_dir)
            
            # Setze eine Präferenz
            manager.preferences.theme = "dark"
            manager.preferences.max_width = 100
            
            # Hole die Präferenzen
            theme = manager.get_preference("theme")
            max_width = manager.get_preference("max_width")
            invalid_pref = manager.get_preference("invalid_pref", "default")
            
            assert theme == "dark"
            assert max_width == 100
            assert invalid_pref == "default"
    
    def test_toggle_component_visibility(self):
        """Testet das Umschalten der Komponentensichtbarkeit."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = CustomizableInterfaceManager(temp_dir)
            
            # Schalte die Sichtbarkeit einer Komponente um
            manager.toggle_component_visibility(InterfaceComponent.HEADER)
            
            # Überprüfe, ob die Komponente in den Präferenzen ist
            assert InterfaceComponent.HEADER.value in manager.preferences.components
            assert manager.preferences.components[InterfaceComponent.HEADER.value].visible == False
            
            # Schalte erneut um
            manager.toggle_component_visibility(InterfaceComponent.HEADER)
            
            # Überprüfe, ob die Sichtbarkeit wieder True ist
            assert manager.preferences.components[InterfaceComponent.HEADER.value].visible == True
    
    def test_customize_component(self):
        """Testet das Anpassen einer Komponente."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = CustomizableInterfaceManager(temp_dir)
            
            # Passe eine Komponente an
            manager.customize_component(
                InterfaceComponent.HEADER,
                style="bold",
                position="bottom",
                size=20
            )
            
            # Überprüfe, ob die Anpassungen übernommen wurden
            component_config = manager.preferences.components[InterfaceComponent.HEADER.value]
            assert component_config.style == "bold"
            assert component_config.position == "bottom"
            assert component_config.size == 20
    
    def test_render_component_visible(self):
        """Testet das Rendern einer sichtbaren Komponente."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = CustomizableInterfaceManager(temp_dir)
            
            # Stelle sicher, dass die Komponente sichtbar ist
            manager.preferences.components[InterfaceComponent.HEADER.value] = ComponentConfig(
                component=InterfaceComponent.HEADER,
                visible=True,
                title="Test Header"
            )
            
            # Rendere die Komponente
            panel = manager.render_component(InterfaceComponent.HEADER, "Test Content")
            
            assert panel is not None
            # Überprüfe, ob der Titel korrekt gesetzt ist
            assert panel.title == "Test Header"
            # Überprüfe, ob der Inhalt korrekt ist (indirekt über die Render-Methode)
            # Da Rich Panels den Inhalt nicht direkt in str() enthalten, prüfen wir die Eigenschaften
    
    def test_render_component_invisible(self):
        """Testet das Rendern einer unsichtbaren Komponente."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = CustomizableInterfaceManager(temp_dir)
            
            # Stelle sicher, dass die Komponente unsichtbar ist
            manager.preferences.components[InterfaceComponent.HEADER.value] = ComponentConfig(
                component=InterfaceComponent.HEADER,
                visible=False
            )
            
            # Rende die Komponente
            panel = manager.render_component(InterfaceComponent.HEADER, "Test Content")
            
            assert panel is None
    
    def test_show_interface_preview(self):
        """Testet das Anzeigen der Oberflächenvorschau."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = CustomizableInterfaceManager(temp_dir)
            
            # Dies sollte ohne Exception ausgeführt werden
            try:
                manager.show_interface_preview()
                assert True
            except Exception as e:
                pytest.fail(f"Fehler beim Anzeigen der Oberflächenvorschau: {e}")
    
    def test_reset_to_defaults(self):
        """Testet das Zurücksetzen auf die Standardwerte."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = CustomizableInterfaceManager(temp_dir)
            
            # Ändere einige Einstellungen
            manager.preferences.theme = "dark"
            manager.preferences.layout = "compact"
            
            # Setze auf Standardwerte zurück
            manager.reset_to_defaults()
            
            # Überprüfe, ob die Einstellungen zurückgesetzt wurden
            # Da die Standardwerte leer sind, sollten sie None oder die Standardwerte sein
            assert manager.preferences.theme == "default"
            assert manager.preferences.layout == "default"
    
    def test_export_theme(self):
        """Testet das Exportieren eines Themas."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            manager = CustomizableInterfaceManager(temp_dir)
            
            # Exportiere ein Thema
            export_file = temp_path / "exported_theme.json"
            manager.export_theme("default", str(export_file))
            
            # Überprüfe, ob die Datei erstellt wurde
            assert export_file.exists()
            
            # Überprüfe den Inhalt der exportierten Datei
            with open(export_file, 'r', encoding='utf-8') as f:
                exported_theme = json.load(f)
            
            assert exported_theme["name"] == "default"
            assert "color_scheme" in exported_theme
            assert "styles" in exported_theme
    
    def test_import_theme(self):
        """Testet das Importieren eines Themas."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            manager = CustomizableInterfaceManager(temp_dir)
            
            # Erstelle eine Test-Themendatei
            test_theme_data = {
                "name": "test_import_theme",
                "color_scheme": {
                    "primary": "red",
                    "secondary": "green",
                    "accent": "blue",
                    "background": "white",
                    "text": "black",
                    "success": "green",
                    "warning": "yellow",
                    "error": "red",
                    "info": "blue"
                },
                "styles": {"header": "bold black on white"},
                "icons": {"download": "📥"},
                "fonts": {"default": "sans-serif"}
            }
            
            import_file = temp_path / "import_theme.json"
            with open(import_file, 'w', encoding='utf-8') as f:
                json.dump(test_theme_data, f)
            
            # Importiere das Thema
            imported_theme_name = manager.import_theme(str(import_file))
            
            assert imported_theme_name == "test_import_theme"
            assert "test_import_theme" in manager.themes
            
            # Überprüfe die Eigenschaften des importierten Themas
            imported_theme = manager.themes["test_import_theme"]
            assert imported_theme.color_scheme.primary == "red"
            assert imported_theme.styles["header"] == "bold black on white"


class TestGlobalFunctions:
    """Testfälle für die globalen Funktionen."""
    
    def test_get_interface_manager_singleton(self):
        """Testet, dass der CustomizableInterfaceManager als Singleton funktioniert."""
        manager1 = get_interface_manager()
        manager2 = get_interface_manager()
        
        assert manager1 is manager2
    
    def test_set_theme_global(self):
        """Testet das Setzen eines Themas über die globale Funktion."""
        # Setze ein Thema
        set_theme("dark")
        
        # Überprüfe, ob das Thema gesetzt wurde
        theme = get_theme()
        assert theme is not None
        assert theme.name == "dark"
    
    def test_get_theme_global(self):
        """Testet das Abrufen eines Themas über die globale Funktion."""
        # Setze ein Thema
        set_theme("light")
        
        # Hole das Thema
        theme = get_theme()
        assert theme is not None
        assert theme.name == "light"
    
    def test_set_layout_global(self):
        """Testet das Setzen eines Layouts über die globale Funktion."""
        # Setze ein Layout
        set_layout("compact")
        
        # Überprüfe, ob das Layout gesetzt wurde
        layout = get_layout()
        assert layout is not None
        assert layout.name == "compact"
    
    def test_get_layout_global(self):
        """Testet das Abrufen eines Layouts über die globale Funktion."""
        # Setze ein Layout
        set_layout("wide")
        
        # Hole das Layout
        layout = get_layout()
        assert layout is not None
        assert layout.name == "wide"
    
    def test_set_preference_global(self):
        """Testet das Setzen einer Präferenz über die globale Funktion."""
        # Setze eine Präferenz
        set_preference("max_width", 150)
        
        # Hole die Präferenz
        max_width = get_preference("max_width")
        assert max_width == 150
    
    def test_get_preference_global(self):
        """Testet das Abrufen einer Präferenz über die globale Funktion."""
        # Setze eine Präferenz
        set_preference("refresh_rate", 2.5)
        
        # Hole die Präferenz
        refresh_rate = get_preference("refresh_rate")
        assert refresh_rate == 2.5
    
    def test_toggle_component_visibility_global(self):
        """Testet das Umschalten der Komponentensichtbarkeit über die globale Funktion."""
        # Schalte die Sichtbarkeit einer Komponente um
        toggle_component_visibility(InterfaceComponent.FOOTER)
        
        # Überprüfe, ob die Änderung übernommen wurde
        manager = get_interface_manager()
        component_config = manager.preferences.components.get(InterfaceComponent.FOOTER.value)
        assert component_config is not None
        assert component_config.visible == False  # Standardmäßig True, dann umgeschaltet
    
    def test_customize_component_global(self):
        """Testet das Anpassen einer Komponente über die globale Funktion."""
        # Passe eine Komponente an
        customize_component(
            InterfaceComponent.SIDEBAR,
            style="italic",
            size=25
        )
        
        # Überprüfe, ob die Anpassungen übernommen wurden
        manager = get_interface_manager()
        component_config = manager.preferences.components.get(InterfaceComponent.SIDEBAR.value)
        assert component_config is not None
        assert component_config.style == "italic"
        assert component_config.size == 25
    
    def test_render_component_global(self):
        """Testet das Rendern einer Komponente über die globale Funktion."""
        # Stelle sicher, dass die Komponente sichtbar ist
        manager = get_interface_manager()
        manager.preferences.components[InterfaceComponent.MENU.value] = ComponentConfig(
            component=InterfaceComponent.MENU,
            visible=True
        )
        
        # Rendere die Komponente
        panel = render_component(InterfaceComponent.MENU, "Menu Content")
        
        assert panel is not None
        # Überprüfe, ob der Inhalt korrekt ist (indirekt über die Render-Methode)
        # Da Rich Panels den Inhalt nicht direkt in str() enthalten, prüfen wir die Eigenschaften
    
    def test_show_interface_preview_global(self):
        """Testet das Anzeigen der Oberflächenvorschau über die globale Funktion."""
        # Dies sollte ohne Exception ausgeführt werden
        try:
            show_interface_preview()
            assert True
        except Exception as e:
            pytest.fail(f"Fehler beim Anzeigen der Oberflächenvorschau über die globale Funktion: {e}")
    
    def test_reset_to_defaults_global(self):
        """Testet das Zurücksetzen auf die Standardwerte über die globale Funktion."""
        # Ändere einige Einstellungen
        set_preference("theme", "dark")
        set_preference("layout", "compact")
        
        # Setze auf Standardwerte zurück
        reset_to_defaults()
        
        # Überprüfe, ob die Einstellungen zurückgesetzt wurden
        assert get_preference("theme") == "default"
        assert get_preference("layout") == "default"


if __name__ == "__main__":
    pytest.main([__file__])