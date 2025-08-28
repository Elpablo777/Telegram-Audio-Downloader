"""
Tests für die Farbkodierung im Telegram Audio Downloader.
"""

import pytest
from unittest.mock import patch

from src.telegram_audio_downloader.color_coding import (
    ColorTheme,
    ColorScheme,
    ColorManager,
    get_color_manager,
    set_color_theme,
    get_color,
    get_rich_style,
    get_status_color,
    get_file_type_color,
    get_category_color
)


class TestColorTheme:
    """Testfälle für die ColorTheme-Enumeration."""
    
    def test_color_theme_values(self):
        """Testet die Werte der ColorTheme-Enumeration."""
        assert ColorTheme.DEFAULT.value == "default"
        assert ColorTheme.DARK.value == "dark"
        assert ColorTheme.LIGHT.value == "light"
        assert ColorTheme.HIGH_CONTRAST.value == "high_contrast"


class TestColorScheme:
    """Testfälle für die ColorScheme-Datenklasse."""
    
    def test_color_scheme_initialization(self):
        """Testet die Initialisierung der ColorScheme-Klasse."""
        scheme = ColorScheme(
            name="Test Scheme",
            primary="#ff0000",
            secondary="#00ff00",
            success="#0000ff",
            warning="#ffff00",
            error="#ff00ff",
            info="#00ffff",
            background="#000000",
            text="#ffffff"
        )
        
        assert scheme.name == "Test Scheme"
        assert scheme.primary == "#ff0000"
        assert scheme.secondary == "#00ff00"
        assert scheme.success == "#0000ff"
        assert scheme.warning == "#ffff00"
        assert scheme.error == "#ff00ff"
        assert scheme.info == "#00ffff"
        assert scheme.background == "#000000"
        assert scheme.text == "#ffffff"


class TestColorManager:
    """Testfälle für die ColorManager-Klasse."""
    
    def test_initialization(self):
        """Testet die Initialisierung des ColorManagers."""
        color_manager = ColorManager()
        
        assert color_manager is not None
        assert hasattr(color_manager, 'theme')
        assert hasattr(color_manager, 'color_schemes')
        assert hasattr(color_manager, 'current_scheme')
        assert color_manager.theme == ColorTheme.DEFAULT
    
    def test_initialization_with_theme(self):
        """Testet die Initialisierung mit einem bestimmten Thema."""
        color_manager = ColorManager(ColorTheme.DARK)
        
        assert color_manager.theme == ColorTheme.DARK
        assert color_manager.current_scheme.name == "Dunkel"
    
    def test_set_theme(self):
        """Testet das Setzen eines Farbthemas."""
        color_manager = ColorManager()
        
        # Ändere das Thema
        color_manager.set_theme(ColorTheme.DARK)
        
        assert color_manager.theme == ColorTheme.DARK
        assert color_manager.current_scheme.name == "Dunkel"
    
    def test_get_color(self):
        """Testet das Abrufen einer Farbe."""
        color_manager = ColorManager()
        
        # Teste verschiedene Farben
        primary_color = color_manager.get_color("primary")
        assert primary_color == "#3498db"
        
        success_color = color_manager.get_color("success")
        assert success_color == "#2ecc71"
        
        # Teste eine nicht existierende Farbe (sollte Standardwert zurückgeben)
        unknown_color = color_manager.get_color("unknown")
        assert unknown_color == "#000000"
    
    def test_get_rich_style(self):
        """Testet das Abrufen eines Rich-Styles."""
        color_manager = ColorManager()
        
        # Teste das Abrufen eines Styles
        style = color_manager.get_rich_style("primary")
        
        assert style is not None
        assert hasattr(style, 'color')
    
    def test_get_status_color(self):
        """Testet das Abrufen einer Status-Farbe."""
        color_manager = ColorManager()
        
        # Teste verschiedene Status
        pending_color = color_manager.get_status_color("pending")
        assert pending_color == color_manager.get_color("info")
        
        downloading_color = color_manager.get_status_color("downloading")
        assert downloading_color == color_manager.get_color("primary")
        
        completed_color = color_manager.get_status_color("completed")
        assert completed_color == color_manager.get_color("success")
        
        failed_color = color_manager.get_status_color("failed")
        assert failed_color == color_manager.get_color("error")
        
        # Teste einen unbekannten Status
        unknown_status_color = color_manager.get_status_color("unknown")
        assert unknown_status_color == color_manager.get_color("text")
    
    def test_get_file_type_color(self):
        """Testet das Abrufen einer Dateityp-Farbe."""
        color_manager = ColorManager()
        
        # Teste verschiedene Dateitypen
        mp3_color = color_manager.get_file_type_color("mp3")
        assert mp3_color == color_manager.get_color("primary")
        
        flac_color = color_manager.get_file_type_color("flac")
        assert flac_color == color_manager.get_color("secondary")
        
        # Teste einen unbekannten Dateityp
        unknown_type_color = color_manager.get_file_type_color("unknown")
        assert unknown_type_color == color_manager.get_color("text")
    
    def test_get_category_color(self):
        """Testet das Abrufen einer Kategorie-Farbe."""
        color_manager = ColorManager()
        
        # Teste verschiedene Kategorien
        classical_color = color_manager.get_category_color("classical")
        assert classical_color == "#8e44ad"
        
        jazz_color = color_manager.get_category_color("jazz")
        assert jazz_color == "#d35400"
        
        # Teste eine unbekannte Kategorie
        unknown_category_color = color_manager.get_category_color("unknown")
        assert unknown_category_color == color_manager.get_color("text")


class TestGlobalFunctions:
    """Testfälle für die globalen Funktionen."""
    
    def test_get_color_manager_singleton(self):
        """Testet, dass der ColorManager als Singleton funktioniert."""
        manager1 = get_color_manager()
        manager2 = get_color_manager()
        
        assert manager1 is manager2
    
    def test_set_color_theme(self):
        """Testet das Setzen eines Farbthemas über die globale Funktion."""
        # Setze das Thema
        set_color_theme(ColorTheme.DARK)
        
        # Überprüfe, ob das Thema gesetzt wurde
        manager = get_color_manager()
        assert manager.theme == ColorTheme.DARK
    
    def test_get_color_global(self):
        """Testet das Abrufen einer Farbe über die globale Funktion."""
        color = get_color("primary")
        assert color == "#3498db"
    
    def test_get_rich_style_global(self):
        """Testet das Abrufen eines Rich-Styles über die globale Funktion."""
        style = get_rich_style("primary")
        
        assert style is not None
        assert hasattr(style, 'color')
    
    def test_get_status_color_global(self):
        """Testet das Abrufen einer Status-Farbe über die globale Funktion."""
        color = get_status_color("completed")
        assert color == "#2ecc71"
    
    def test_get_file_type_color_global(self):
        """Testet das Abrufen einer Dateityp-Farbe über die globale Funktion."""
        color = get_file_type_color("mp3")
        assert color == "#3498db"
    
    def test_get_category_color_global(self):
        """Testet das Abrufen einer Kategorie-Farbe über die globale Funktion."""
        color = get_category_color("classical")
        assert color == "#8e44ad"


if __name__ == "__main__":
    pytest.main([__file__])