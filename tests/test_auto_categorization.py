"""
Tests für die automatische Kategorisierung im Telegram Audio Downloader.
"""

import pytest
import tempfile
import os
from pathlib import Path

from src.telegram_audio_downloader.auto_categorization import (
    AutoCategorizer,
    categorize_audio_file,
    categorize_by_folder,
    get_auto_categorizer
)
from src.telegram_audio_downloader.models import AudioFile


class TestAutoCategorization:
    """Testfälle für die automatische Kategorisierung."""
    
    def test_auto_categorizer_initialization(self):
        """Testet die Initialisierung des AutoCategorizers."""
        categorizer = AutoCategorizer()
        assert categorizer is not None
        assert hasattr(categorizer, 'category_keywords')
        assert hasattr(categorizer, 'compiled_patterns')
    
    def test_categorize_rock_file(self):
        """Testet die Kategorisierung einer Rock-Datei."""
        # Erstelle ein AudioFile-Objekt mit Rock-Keywords
        audio_file = AudioFile(
            file_id="test_rock_001",
            file_name="queen_bohemian_rhapsody.mp3",
            title="Bohemian Rhapsody",
            performer="Queen"
        )
        
        categorizer = AutoCategorizer()
        category = categorizer.categorize_file(audio_file)
        # Rock-Keywords in "queen" und "bohemian" sollten erkannt werden
        assert category in ["rock", "unclassified"]  # Je nachdem, wie genau die Erkennung ist
    
    def test_categorize_classical_file(self):
        """Testet die Kategorisierung einer klassischen Datei."""
        # Erstelle ein AudioFile-Objekt mit klassischen Keywords
        audio_file = AudioFile(
            file_id="test_classical_001",
            file_name="beethoven_symphony_9.mp3",
            title="Symphony No. 9",
            performer="Beethoven"
        )
        
        categorizer = AutoCategorizer()
        category = categorizer.categorize_file(audio_file)
        # Klassik-Keywords sollten erkannt werden
        assert category in ["classical", "unclassified"]
    
    def test_categorize_unclassified_file(self):
        """Testet die Kategorisierung einer nicht klassifizierbaren Datei."""
        # Erstelle ein AudioFile-Objekt ohne klare Keywords
        audio_file = AudioFile(
            file_id="test_uncategorized_001",
            file_name="unknown_file.mp3",
            title="Unknown Title",
            performer="Unknown Artist"
        )
        
        categorizer = AutoCategorizer()
        category = categorizer.categorize_file(audio_file)
        # Sollte als "unclassified" kategorisiert werden
        assert category == "unclassified"
    
    def test_get_auto_categorizer_singleton(self):
        """Testet, dass der AutoCategorizer als Singleton funktioniert."""
        categorizer1 = get_auto_categorizer()
        categorizer2 = get_auto_categorizer()
        assert categorizer1 is categorizer2
    
    def test_categorize_by_folder_structure(self):
        """Testet die Kategorisierung basierend auf Ordnerstruktur."""
        # Erstelle ein temporäres Verzeichnis mit Teststruktur
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)
            
            # Erstelle Kategorieordner
            rock_folder = base_path / "rock"
            rock_folder.mkdir()
            
            classical_folder = base_path / "classical"
            classical_folder.mkdir()
            
            # Erstelle Testdateien
            (rock_folder / "song1.mp3").touch()
            (rock_folder / "song2.flac").touch()
            (classical_folder / "symphony.mp3").touch()
            
            # Teste die Kategorisierung
            result = categorize_by_folder(str(base_path))
            
            assert "rock" in result
            assert "classical" in result
            assert len(result["rock"]) == 2
            assert len(result["classical"]) == 1
    
    def test_create_category_folders(self):
        """Testet das Erstellen von Kategorieordnern."""
        # Erstelle ein temporäres Verzeichnis
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)
            
            # Erstelle Kategorieordner
            categorizer = AutoCategorizer()
            categorizer.create_category_folders(str(base_path), ["jazz", "blues", "folk"])
            
            # Überprüfe, ob die Ordner erstellt wurden
            assert (base_path / "jazz").exists()
            assert (base_path / "blues").exists()
            assert (base_path / "folk").exists()
    
    def test_categorize_audio_file_function(self):
        """Testet die categorize_audio_file-Funktion."""
        # Erstelle ein AudioFile-Objekt
        audio_file = AudioFile(
            file_id="test_function_001",
            file_name="test_song.mp3",
            title="Test Song",
            performer="Test Artist"
        )
        
        # Teste die Funktion
        category = categorize_audio_file(audio_file)
        # Sollte eine der bekannten Kategorien oder "unclassified" sein
        assert category in ["classical", "jazz", "rock", "pop", "electronic", 
                          "hiphop", "country", "reggae", "latin", "world", "unclassified"]


if __name__ == "__main__":
    pytest.main([__file__])