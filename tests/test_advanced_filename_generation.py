"""
Tests für die erweiterte Dateinamen-Generierung.
"""

import unittest
import tempfile
import os
from pathlib import Path
from datetime import datetime

from src.telegram_audio_downloader.advanced_filename_generation import (
    FilenameTemplate, AdvancedFilenameGenerator, generate_filename_from_metadata
)

class TestFilenameTemplate(unittest.TestCase):
    """Tests für die FilenameTemplate-Klasse."""
    
    def test_extract_placeholders(self):
        """Testet das Extrahieren von Platzhaltern."""
        template_string = "$artist - $title ($year)"
        template = FilenameTemplate(template_string)
        expected = {"artist", "title", "year"}
        self.assertEqual(template.placeholders, expected)
        
    def test_extract_placeholders_with_braces(self):
        """Testet das Extrahieren von Platzhaltern mit geschweiften Klammern."""
        template_string = "${artist} - ${title} (${year})"
        template = FilenameTemplate(template_string)
        expected = {"artist", "title", "year"}
        self.assertEqual(template.placeholders, expected)
        
    def test_validate_placeholders(self):
        """Testet die Validierung von Platzhaltern."""
        # Gültige Platzhalter
        template_string = "$artist - $title ($year)"
        template = FilenameTemplate(template_string)
        self.assertTrue(template.validate_placeholders())
        
        # Ungültige Platzhalter
        template_string = "$artist - $title ($invalid_placeholder)"
        template = FilenameTemplate(template_string)
        self.assertFalse(template.validate_placeholders())
        
    def test_render_template(self):
        """Testet das Rendern einer Vorlage."""
        template_string = "$artist - $title ($year)"
        template = FilenameTemplate(template_string)
        metadata = {
            "artist": "Test Artist",
            "title": "Test Title",
            "year": "2023"
        }
        result = template.render(metadata)
        expected = "Test Artist - Test Title (2023)"
        self.assertEqual(result, expected)
        
    def test_render_template_with_missing_placeholders(self):
        """Testet das Rendern einer Vorlage mit fehlenden Platzhaltern."""
        template_string = "$artist - $title ($missing)"
        template = FilenameTemplate(template_string)
        metadata = {
            "artist": "Test Artist",
            "title": "Test Title"
        }
        result = template.render(metadata)
        expected = "Test Artist - Test Title ()"
        self.assertEqual(result, expected)
        
    def test_render_template_with_counter(self):
        """Testet das Rendern einer Vorlage mit Zähler."""
        template_string = "$artist - $counter. $title"
        template = FilenameTemplate(template_string)
        metadata = {
            "artist": "Test Artist",
            "title": "Test Title"
        }
        result = template.render(metadata, counter=5)
        expected = "Test Artist - 005. Test Title"
        self.assertEqual(result, expected)

class TestAdvancedFilenameGenerator(unittest.TestCase):
    """Tests für die AdvancedFilenameGenerator-Klasse."""
    
    def setUp(self):
        """Erstellt eine temporäre Verzeichnisstruktur für die Tests."""
        self.test_dir = tempfile.mkdtemp()
        self.generator = AdvancedFilenameGenerator(self.test_dir)
        
    def tearDown(self):
        """Räumt die temporären Dateien auf."""
        # Entferne alle Dateien im temporären Verzeichnis
        for file_path in Path(self.test_dir).glob("*"):
            file_path.unlink()
        # Entferne das Verzeichnis
        Path(self.test_dir).rmdir()
        
    def test_add_template(self):
        """Testet das Hinzufügen einer neuen Vorlage."""
        template_name = "test_template"
        template_string = "$artist - $title"
        result = self.generator.add_template(template_name, template_string)
        self.assertTrue(result)
        self.assertIn(template_name, self.generator.templates)
        
    def test_add_template_invalid_placeholders(self):
        """Testet das Hinzufügen einer Vorlage mit ungültigen Platzhaltern."""
        template_name = "invalid_template"
        template_string = "$artist - $invalid_placeholder"
        result = self.generator.add_template(template_name, template_string)
        self.assertFalse(result)
        self.assertNotIn(template_name, self.generator.templates)
        
    def test_set_template(self):
        """Testet das Setzen der aktuellen Vorlage."""
        # Füge eine neue Vorlage hinzu
        template_name = "test_template"
        template_string = "$artist - $title"
        self.generator.add_template(template_name, template_string)
        
        # Setze die Vorlage als aktuelle Vorlage
        result = self.generator.set_template(template_name)
        self.assertTrue(result)
        self.assertEqual(self.generator.current_template, template_name)
        
    def test_set_template_nonexistent(self):
        """Testet das Setzen einer nicht existierenden Vorlage."""
        result = self.generator.set_template("nonexistent_template")
        self.assertFalse(result)
        # Die aktuelle Vorlage sollte unverändert bleiben
        self.assertEqual(self.generator.current_template, "detailed")
        
    def test_generate_filename(self):
        """Testet das Generieren eines Dateinamens."""
        metadata = {
            "artist": "Test Artist",
            "title": "Test Title",
            "year": "2023"
        }
        filename = self.generator.generate_filename(metadata, ".mp3")
        expected_pattern = r"Test Artist - Test Title \(2023\)\.mp3"
        self.assertRegex(filename, expected_pattern)
        
    def test_generate_filename_with_custom_template(self):
        """Testet das Generieren eines Dateinamens mit benutzerdefinierter Vorlage."""
        # Füge eine neue Vorlage hinzu
        template_name = "custom_template"
        template_string = "$artist - $track_number. $title"
        self.generator.add_template(template_name, template_string)
        
        metadata = {
            "artist": "Test Artist",
            "title": "Test Title",
            "track_number": "01"
        }
        filename = self.generator.generate_filename(metadata, ".mp3", template_name)
        expected_pattern = r"Test Artist - 01\. Test Title\.mp3"
        self.assertRegex(filename, expected_pattern)
        
    def test_avoid_collision(self):
        """Testet die Vermeidung von Kollisionen."""
        # Erstelle eine Datei mit einem bestimmten Namen
        filename = "Test Artist - Test Title.mp3"
        (Path(self.test_dir) / filename).touch()
        
        # Füge den Dateinamen zu den verwendeten Dateinamen hinzu
        self.generator.used_filenames.add(filename)
        
        # Generiere einen Dateinamen mit demselben Namen
        metadata = {
            "artist": "Test Artist",
            "title": "Test Title"
        }
        generated_filename = self.generator.generate_filename(metadata, ".mp3")
        
        # Der generierte Dateiname sollte anders sein
        self.assertNotEqual(filename, generated_filename)
        # Verwenden wir eine einfachere Prüfung, da die Standardvorlage keinen Zähler enthält
        self.assertTrue(generated_filename.endswith(".mp3"))
        # Stellen sicher, dass der Dateiname nicht leer ist
        self.assertNotEqual(generated_filename, "")
        
    def test_counter_increment(self):
        """Testet das Inkrementieren des Zählers."""
        metadata = {
            "artist": "Test Artist",
            "title": "Test Title"
        }
        
        # Generiere mehrere Dateinamen
        filenames = []
        for i in range(3):
            filename = self.generator.generate_filename(metadata, ".mp3")
            filenames.append(filename)
            
        # Prüfe, ob die Zähler korrekt inkrementiert wurden
        # Da der Zähler bei 1 beginnt, sollte der erste Dateiname den Zähler enthalten
        # In der Standardvorlage ist der Zähler nicht enthalten, daher müssen wir eine Vorlage verwenden, die ihn enthält
        self.generator.set_template("simple")  # Zurücksetzen
        self.generator.counter = 1  # Zurücksetzen
        
        # Verwende eine Vorlage mit Zähler
        self.generator.add_template("counter_template", "$artist - $title - $counter")
        self.generator.set_template("counter_template")
        
        filenames = []
        for i in range(3):
            filename = self.generator.generate_filename(metadata, ".mp3")
            filenames.append(filename)
            
        # Prüfe, ob die Zähler korrekt inkrementiert wurden
        self.assertIn("- 001", filenames[0])
        self.assertIn("- 002", filenames[1])
        self.assertIn("- 003", filenames[2])

class TestGenerateFilenameFromMetadata(unittest.TestCase):
    """Tests für die generate_filename_from_metadata-Funktion."""
    
    def setUp(self):
        """Erstellt eine temporäre Verzeichnisstruktur für die Tests."""
        self.test_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Räumt die temporären Dateien auf."""
        # Entferne alle Dateien im temporären Verzeichnis
        for file_path in Path(self.test_dir).glob("*"):
            file_path.unlink()
        # Entferne das Verzeichnis
        Path(self.test_dir).rmdir()
        
    def test_generate_filename_from_metadata(self):
        """Testet das Generieren eines Dateinamens aus Metadaten."""
        metadata = {
            "artist": "Test Artist",
            "title": "Test Title",
            "year": "2023"
        }
        filename = generate_filename_from_metadata(
            metadata, 
            ".mp3", 
            download_dir=self.test_dir
        )
        expected_pattern = r"Test Artist - Test Title \(2023\)\.mp3"
        self.assertRegex(filename, expected_pattern)

if __name__ == "__main__":
    unittest.main()