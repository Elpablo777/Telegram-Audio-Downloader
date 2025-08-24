"""
Tests für die mehrsprachige Unterstützung im Telegram Audio Downloader.
"""

import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch

from src.telegram_audio_downloader.i18n import (
    Language,
    TranslationManager,
    get_translation_manager,
    set_language,
    _,
    add_translation,
    init_translations,
    DEFAULT_TRANSLATIONS,
    GERMAN_TRANSLATIONS
)


class TestLanguage:
    """Testfälle für die Language-Enumeration."""
    
    def test_language_values(self):
        """Testet die Werte der Language-Enumeration."""
        assert Language.ENGLISH.value == "en"
        assert Language.GERMAN.value == "de"
        assert Language.SPANISH.value == "es"
        assert Language.FRENCH.value == "fr"
        assert Language.ITALIAN.value == "it"
        assert Language.PORTUGUESE.value == "pt"
        assert Language.RUSSIAN.value == "ru"
        assert Language.CHINESE.value == "zh"
        assert Language.JAPANESE.value == "ja"
        assert Language.KOREAN.value == "ko"


class TestTranslationManager:
    """Testfälle für die TranslationManager-Klasse."""
    
    def test_initialization(self):
        """Testet die Initialisierung des TranslationManagers."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = TranslationManager(translations_dir=temp_dir)
            
            assert manager is not None
            assert hasattr(manager, 'language')
            assert hasattr(manager, 'translations_dir')
            assert hasattr(manager, 'translations')
            assert manager.language == Language.ENGLISH
            assert manager.translations == DEFAULT_TRANSLATIONS
    
    def test_initialization_with_language(self):
        """Testet die Initialisierung mit einer bestimmten Sprache."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = TranslationManager(language=Language.GERMAN, translations_dir=temp_dir)
            
            assert manager.language == Language.GERMAN
    
    def test_set_language(self):
        """Testet das Setzen der Sprache."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = TranslationManager(translations_dir=temp_dir)
            
            # Ändere die Sprache
            manager.set_language(Language.GERMAN)
            
            assert manager.language == Language.GERMAN
    
    def test_get_translation(self):
        """Testet das Abrufen einer Übersetzung."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = TranslationManager(translations_dir=temp_dir)
            
            # Teste das Abrufen einer Standardübersetzung
            translation = manager.get_translation("welcome")
            assert translation == "Welcome to Telegram Audio Downloader"
            
            # Teste das Abrufen einer nicht existierenden Übersetzung (Fallback auf Schlüssel)
            translation = manager.get_translation("non_existent_key")
            assert translation == "non_existent_key"
    
    def test_get_translation_with_placeholders(self):
        """Testet das Abrufen einer Übersetzung mit Platzhaltern."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = TranslationManager(translations_dir=temp_dir)
            
            # Teste das Abrufen einer Übersetzung mit Platzhaltern
            translation = manager.get_translation("files_found", count=5)
            assert translation == "5 files found"
    
    def test_add_translation(self):
        """Testet das Hinzufügen einer neuen Übersetzung."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = TranslationManager(translations_dir=temp_dir)
            
            # Füge eine neue Übersetzung hinzu
            manager.add_translation("test_key", "Test Value")
            
            # Hole die Übersetzung
            translation = manager.get_translation("test_key")
            assert translation == "Test Value"
    
    def test_save_translations(self):
        """Testet das Speichern von Übersetzungen."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = TranslationManager(language=Language.GERMAN, translations_dir=temp_dir)
            
            # Füge eine neue Übersetzung hinzu
            manager.add_translation("test_save_key", "Test Save Value")
            
            # Speichere die Übersetzungen
            manager.save_translations()
            
            # Überprüfe, ob die Datei erstellt wurde
            translation_file = Path(temp_dir) / "de.json"
            assert translation_file.exists()
    
    def test_load_translations(self):
        """Testet das Laden von Übersetzungen."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Erstelle eine Übersetzungsdatei
            translation_file = Path(temp_dir) / "de.json"
            test_translations = {"test_load_key": "Test Load Value"}
            
            with open(translation_file, 'w', encoding='utf-8') as f:
                json.dump(test_translations, f, ensure_ascii=False)
            
            # Erstelle einen TranslationManager mit dieser Sprache
            manager = TranslationManager(language=Language.GERMAN, translations_dir=temp_dir)
            
            # Hole die Übersetzung
            translation = manager.get_translation("test_load_key")
            assert translation == "Test Load Value"
    
    def test_create_translation_file(self):
        """Testet das Erstellen einer leeren Übersetzungsdatei."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = TranslationManager(language=Language.SPANISH, translations_dir=temp_dir)
            
            # Die Datei sollte automatisch erstellt worden sein
            translation_file = Path(temp_dir) / "es.json"
            assert translation_file.exists()
            
            # Überprüfe den Inhalt der Datei
            with open(translation_file, 'r', encoding='utf-8') as f:
                content = json.load(f)
                assert isinstance(content, dict)
                # Alle Schlüssel sollten vorhanden sein, aber leer
                for key in DEFAULT_TRANSLATIONS.keys():
                    assert key in content


class TestGlobalFunctions:
    """Testfälle für die globalen Funktionen."""
    
    def test_get_translation_manager_singleton(self):
        """Testet, dass der TranslationManager als Singleton funktioniert."""
        manager1 = get_translation_manager()
        manager2 = get_translation_manager()
        
        assert manager1 is manager2
    
    def test_set_language_global(self):
        """Testet das Setzen der Sprache über die globale Funktion."""
        # Setze die Sprache
        set_language(Language.GERMAN)
        
        # Überprüfe, ob die Sprache gesetzt wurde
        manager = get_translation_manager()
        assert manager.language == Language.GERMAN
    
    def test_get_translation_global(self):
        """Testet das Abrufen einer Übersetzung über die globale Funktion."""
        # Setze die Sprache auf Deutsch
        set_language(Language.GERMAN)
        
        # Hole eine Übersetzung
        translation = _("welcome")
        # Da wir keine deutschen Übersetzungen geladen haben, sollte der Schlüssel zurückgegeben werden
        assert translation == "welcome"
    
    def test_add_translation_global(self):
        """Testet das Hinzufügen einer Übersetzung über die globale Funktion."""
        # Füge eine neue Übersetzung hinzu
        add_translation("global_test_key", "Global Test Value")
        
        # Hole die Übersetzung
        translation = _("global_test_key")
        assert translation == "Global Test Value"
    
    def test_init_translations(self):
        """Testet die Initialisierung von Übersetzungen."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Initialisiere die Übersetzungen
            init_translations(Language.GERMAN)
            
            # Überprüfe, ob der Manager erstellt wurde
            manager = get_translation_manager()
            assert manager is not None
            assert manager.language == Language.GERMAN


class TestDefaultTranslations:
    """Testfälle für die Standardübersetzungen."""
    
    def test_default_translations_exist(self):
        """Testet, ob die Standardübersetzungen existieren."""
        assert isinstance(DEFAULT_TRANSLATIONS, dict)
        assert len(DEFAULT_TRANSLATIONS) > 0
    
    def test_default_translations_keys(self):
        """Testet wichtige Schlüssel in den Standardübersetzungen."""
        required_keys = [
            "welcome",
            "quit",
            "help",
            "search",
            "download",
            "settings",
            "main_menu",
            "search_and_download",
            "error_occurred"
        ]
        
        for key in required_keys:
            assert key in DEFAULT_TRANSLATIONS


class TestGermanTranslations:
    """Testfälle für die deutschen Übersetzungen."""
    
    def test_german_translations_exist(self):
        """Testet, ob die deutschen Übersetzungen existieren."""
        assert isinstance(GERMAN_TRANSLATIONS, dict)
        assert len(GERMAN_TRANSLATIONS) > 0
    
    def test_german_translations_keys(self):
        """Testet wichtige Schlüssel in den deutschen Übersetzungen."""
        required_keys = [
            "welcome",
            "quit",
            "help",
            "search",
            "download",
            "settings",
            "main_menu",
            "search_and_download",
            "error_occurred"
        ]
        
        for key in required_keys:
            assert key in GERMAN_TRANSLATIONS


if __name__ == "__main__":
    pytest.main([__file__])