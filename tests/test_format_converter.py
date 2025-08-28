"""
Tests für die Formatkonvertierung.
"""

import unittest
import tempfile
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.telegram_audio_downloader.format_converter import (
    FormatConverter, SUPPORTED_FORMATS, convert_audio_file, convert_audio_file_async
)
from src.telegram_audio_downloader.error_handling import FileOperationError, ConfigurationError

class TestFormatConverter(unittest.TestCase):
    """Tests für die FormatConverter-Klasse."""
    
    def setUp(self):
        """Erstellt eine temporäre Verzeichnisstruktur für die Tests."""
        self.test_dir = tempfile.mkdtemp()
        # Überspringe Tests, wenn pydub nicht verfügbar ist
        if not hasattr(FormatConverter, '_test_skip_reason'):
            try:
                self.converter = FormatConverter(self.test_dir)
            except ConfigurationError as e:
                if "Python 3.13" in str(e):
                    self.skipTest("pydub ist nicht mit Python 3.13 kompatibel")
                else:
                    raise
    
    def tearDown(self):
        """Räumt die temporären Dateien auf."""
        if hasattr(self, 'converter'):
            self.converter.cleanup_temp_files()
        # Entferne alle Dateien im temporären Verzeichnis
        for file_path in Path(self.test_dir).glob("*"):
            try:
                file_path.unlink()
            except PermissionError:
                pass
        # Entferne das Verzeichnis
        try:
            Path(self.test_dir).rmdir()
        except PermissionError:
            pass
    
    def test_supported_formats(self):
        """Testet die unterstützten Formate."""
        # Überspringe den Test, wenn pydub nicht verfügbar ist
        if not hasattr(self, 'converter'):
            self.skipTest("pydub ist nicht verfügbar")
            
        self.assertIn("mp3", SUPPORTED_FORMATS)
        self.assertIn("m4a", SUPPORTED_FORMATS)
        self.assertIn("flac", SUPPORTED_FORMATS)
        self.assertIn("opus", SUPPORTED_FORMATS)
        
        # Prüfe die Formatinformationen
        self.assertEqual(SUPPORTED_FORMATS["mp3"]["extension"], ".mp3")
        self.assertEqual(SUPPORTED_FORMATS["mp3"]["format"], "mp3")
        self.assertEqual(SUPPORTED_FORMATS["m4a"]["extension"], ".m4a")
        self.assertEqual(SUPPORTED_FORMATS["m4a"]["format"], "mp4")
        self.assertEqual(SUPPORTED_FORMATS["flac"]["extension"], ".flac")
        self.assertEqual(SUPPORTED_FORMATS["flac"]["format"], "flac")
        self.assertEqual(SUPPORTED_FORMATS["opus"]["extension"], ".opus")
        self.assertEqual(SUPPORTED_FORMATS["opus"]["format"], "opus")
    
    def test_init_with_custom_temp_dir(self):
        """Testet die Initialisierung mit benutzerdefiniertem Temp-Verzeichnis."""
        # Überspringe den Test, wenn pydub nicht verfügbar ist
        if not hasattr(self, 'converter'):
            self.skipTest("pydub ist nicht verfügbar")
            
        custom_temp_dir = Path(self.test_dir) / "custom_temp"
        converter = FormatConverter(custom_temp_dir)
        self.assertTrue(custom_temp_dir.exists())
    
    @patch('src.telegram_audio_downloader.format_converter.AudioSegment')
    def test_convert_audio_file_success(self, mock_audio_segment):
        """Testet die erfolgreiche Konvertierung einer Audiodatei."""
        # Überspringe den Test, wenn pydub nicht verfügbar ist
        if not hasattr(self, 'converter'):
            self.skipTest("pydub ist nicht verfügbar")
            
        # Erstelle eine Mock-Quelldatei
        source_file = Path(self.test_dir) / "test.mp3"
        source_file.touch()
        
        # Erstelle Mock-AudioSegment
        mock_audio = MagicMock()
        mock_audio_segment.from_file.return_value = mock_audio
        mock_audio.set_frame_rate.return_value = mock_audio
        mock_audio.set_channels.return_value = mock_audio
        mock_audio.export.return_value = None
        
        # Führe die Konvertierung durch
        target_file = self.converter.convert_audio_file(source_file, "flac")
        
        # Prüfe, ob die Mocks korrekt aufgerufen wurden
        mock_audio_segment.from_file.assert_called_once_with(str(source_file))
        mock_audio.export.assert_called_once()
        
        # Prüfe den Zielpfad
        self.assertEqual(target_file, source_file.parent / "test.flac")
    
    def test_convert_audio_file_nonexistent_source(self):
        """Testet die Konvertierung mit nicht existierender Quelldatei."""
        # Überspringe den Test, wenn pydub nicht verfügbar ist
        if not hasattr(self, 'converter'):
            self.skipTest("pydub ist nicht verfügbar")
            
        source_file = Path(self.test_dir) / "nonexistent.mp3"
        with self.assertRaises(FileOperationError):
            self.converter.convert_audio_file(source_file, "flac")
    
    def test_convert_audio_file_unsupported_format(self):
        """Testet die Konvertierung mit nicht unterstütztem Format."""
        # Überspringe den Test, wenn pydub nicht verfügbar ist
        if not hasattr(self, 'converter'):
            self.skipTest("pydub ist nicht verfügbar")
            
        source_file = Path(self.test_dir) / "test.mp3"
        source_file.touch()
        with self.assertRaises(ConfigurationError):
            self.converter.convert_audio_file(source_file, "unsupported_format")
    
    @patch('src.telegram_audio_downloader.format_converter.AudioSegment')
    def test_convert_audio_file_with_options(self, mock_audio_segment):
        """Testet die Konvertierung mit zusätzlichen Optionen."""
        # Überspringe den Test, wenn pydub nicht verfügbar ist
        if not hasattr(self, 'converter'):
            self.skipTest("pydub ist nicht verfügbar")
            
        # Erstelle eine Mock-Quelldatei
        source_file = Path(self.test_dir) / "test.wav"
        source_file.touch()
        
        # Erstelle Mock-AudioSegment
        mock_audio = MagicMock()
        mock_audio_segment.from_file.return_value = mock_audio
        mock_audio.set_frame_rate.return_value = mock_audio
        mock_audio.set_channels.return_value = mock_audio
        mock_audio.export.return_value = None
        
        # Führe die Konvertierung mit Optionen durch
        target_file = self.converter.convert_audio_file(
            source_file, "mp3", 
            bitrate="192k", 
            sample_rate=44100, 
            channels=2
        )
        
        # Prüfe, ob die Mocks korrekt aufgerufen wurden
        mock_audio_segment.from_file.assert_called_once_with(str(source_file))
        mock_audio.set_frame_rate.assert_called_once_with(44100)
        mock_audio.set_channels.assert_called_once_with(2)
        mock_audio.export.assert_called_once()
        
        # Prüfe den Zielpfad
        self.assertEqual(target_file, source_file.parent / "test.mp3")
    
    def test_batch_convert(self):
        """Testet die Batch-Konvertierung."""
        # Überspringe den Test, wenn pydub nicht verfügbar ist
        if not hasattr(self, 'converter'):
            self.skipTest("pydub ist nicht verfügbar")
            
        # Erstelle Mock-Dateien
        source1 = Path(self.test_dir) / "test1.mp3"
        source2 = Path(self.test_dir) / "test2.wav"
        source1.touch()
        source2.touch()
        
        # Erstelle Mocks für die Konvertierung
        with patch.object(self.converter, 'convert_audio_file') as mock_convert:
            mock_convert.return_value = Path(self.test_dir) / "converted.flac"
            
            # Führe die Batch-Konvertierung durch
            file_mappings = {
                source1: {"target_format": "flac"},
                source2: {"target_format": "mp3", "bitrate": "192k"}
            }
            results = self.converter.batch_convert(file_mappings)
            
            # Prüfe die Ergebnisse
            self.assertEqual(len(results), 2)
            mock_convert.assert_any_call(source1, "flac", None)
            mock_convert.assert_any_call(source2, "mp3", None, bitrate="192k")
    
    def test_cleanup_temp_files(self):
        """Testet das Aufräumen temporärer Dateien."""
        # Überspringe den Test, wenn pydub nicht verfügbar ist
        if not hasattr(self, 'converter'):
            self.skipTest("pydub ist nicht verfügbar")
            
        # Erstelle eine temporäre Datei
        temp_file = self.converter.temp_dir / "temp_file.txt"
        temp_file.touch()
        self.assertTrue(temp_file.exists())
        
        # Räume auf
        self.converter.cleanup_temp_files()
        
        # Prüfe, ob das Temp-Verzeichnis noch existiert (es sollte neu erstellt worden sein)
        self.assertTrue(self.converter.temp_dir.exists())

class TestGlobalFunctions(unittest.TestCase):
    """Tests für die globalen Hilfsfunktionen."""
    
    def setUp(self):
        """Erstellt eine temporäre Verzeichnisstruktur für die Tests."""
        self.test_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Räumt die temporären Dateien auf."""
        # Entferne alle Dateien im temporären Verzeichnis
        for file_path in Path(self.test_dir).glob("*"):
            try:
                file_path.unlink()
            except PermissionError:
                pass
        # Entferne das Verzeichnis
        try:
            Path(self.test_dir).rmdir()
        except PermissionError:
            pass
    
    @patch('src.telegram_audio_downloader.format_converter.get_format_converter')
    def test_convert_audio_file_function(self, mock_get_converter):
        """Testet die globale convert_audio_file-Funktion."""
        # Erstelle Mocks
        mock_converter = MagicMock()
        mock_get_converter.return_value = mock_converter
        mock_converter.convert_audio_file.return_value = Path("converted.mp3")
        
        # Führe die Funktion aus
        source_file = Path(self.test_dir) / "test.wav"
        source_file.touch()
        result = convert_audio_file(source_file, "mp3")
        
        # Prüfe die Ergebnisse
        mock_get_converter.assert_called_once()
        mock_converter.convert_audio_file.assert_called_once_with(source_file, "mp3", None)
        self.assertEqual(result, Path("converted.mp3"))

if __name__ == "__main__":
    unittest.main()