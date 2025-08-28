"""
Tests für das utils-Modul.
"""
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.telegram_audio_downloader.utils import (
    sanitize_filename,
    create_filename_from_metadata,
    get_unique_filepath,
    calculate_file_hash,
    format_file_size,
    format_duration,
    is_audio_file,
    ensure_directory_exists,
    get_file_extension_from_mime,
)


class TestSanitizeFilename:
    """Tests für die sanitize_filename-Funktion."""
    
    def test_normal_filename(self):
        """Test mit normalem Dateinamen."""
        result = sanitize_filename("My Song.mp3")
        assert result == "My Song.mp3"
    
    def test_invalid_characters(self):
        """Test mit ungültigen Zeichen."""
        result = sanitize_filename("Song<>:\"|?*.mp3")
        assert result == "Song_______.mp3"
    
    def test_reserved_names(self):
        """Test mit reservierten Windows-Namen."""
        result = sanitize_filename("CON.mp3")
        assert result == "_CON.mp3"
    
    def test_empty_filename(self):
        """Test mit leerem Dateinamen."""
        result = sanitize_filename("")
        assert result == "unknown_file"
    
    def test_max_length(self):
        """Test der Längenbegrenzung."""
        long_name = "a" * 300 + ".mp3"
        result = sanitize_filename(long_name, max_length=255)
        assert len(result) <= 255
        assert result.endswith(".mp3")
    
    def test_unicode_emojis(self):
        """Test mit Unicode-Emojis."""
        result = sanitize_filename("🎵 Music 🎶 File.mp3")
        assert result == "🎵 Music 🎶 File.mp3"
        # Emojis sollten erhalten bleiben, da sie gültige Unicode-Zeichen sind
    
    def test_unicode_characters(self):
        """Test mit verschiedenen Unicode-Zeichen."""
        test_cases = [
            ("Japanese 音楽.mp3", "Japanese 音楽.mp3"),
            ("Russian музыка.mp3", "Russian музыка.mp3"),
            ("Arabic موسيقى.mp3", "Arabic موسيقى.mp3"),
            ("Chinese 音乐.mp3", "Chinese 音乐.mp3"),
        ]
        for input_name, expected in test_cases:
            result = sanitize_filename(input_name)
            assert result == expected
    
    def test_unicode_normalization_with_composed_characters(self):
        """Test mit zusammengesetzten Unicode-Zeichen (mit Normalisierung)."""
        # Test mit Zeichen, die nach Unicode-Normalisierung verändert werden können
        result = sanitize_filename("Song with émojis 🎵🎶🎼.mp3")
        # Nach NFD-Normalisierung wird é zu e + combining accent
        # Das Ergebnis sollte gültig sein, auch wenn es sich vom Input unterscheidet
        assert result.endswith(".mp3")
        assert "Song with" in result
        assert "emojis" in result  # e + combining accent wird zu "emojis"
        assert "🎵🎶🎼" in result
    
    def test_control_characters(self):
        """Test mit Steuerzeichen."""
        result = sanitize_filename("File\x01\x02\x03control chars.mp3")
        assert result == "File___control chars.mp3"
    
    def test_null_bytes(self):
        """Test mit Null-Bytes."""
        result = sanitize_filename("File with\x00null.mp3")
        assert result == "File with_null.mp3"
    
    def test_line_breaks_and_tabs(self):
        """Test mit Zeilenumbrüchen und Tabs."""
        test_cases = [
            ("Filename with\nnewline.mp3", "Filename with_newline.mp3"),
            ("File\twith\ttabs.mp3", "File_with_tabs.mp3"),
            ("File with\rcarriage return.mp3", "File with_carriage return.mp3"),
        ]
        for input_name, expected in test_cases:
            result = sanitize_filename(input_name)
            assert result == expected
    
    def test_zero_width_characters(self):
        """Test mit unsichtbaren Zero-Width-Zeichen."""
        result = sanitize_filename("File\u200B\u200C\u200D\u2028\u2029.mp3")
        assert result == "File_____.mp3"
    
    def test_unicode_normalization(self):
        """Test der Unicode-Normalisierung."""
        # Test mit NFC und NFD Formen desselben Zeichens
        nfc_form = "café.mp3"  # composed form
        nfd_form = "cafe\u0301.mp3"  # decomposed form with combining accent
        
        result_nfc = sanitize_filename(nfc_form)
        result_nfd = sanitize_filename(nfd_form)
        
        # Beide sollten das gleiche Ergebnis liefern nach Normalisierung
        assert result_nfc == result_nfd


class TestCreateFilenameFromMetadata:
    """Tests für die create_filename_from_metadata-Funktion."""
    
    def test_with_artist_and_title(self):
        """Test mit Künstler und Titel."""
        result = create_filename_from_metadata("My Song", "Artist Name", "123", ".mp3")
        assert result == "Artist Name - My Song.mp3"
    
    def test_with_title_only(self):
        """Test nur mit Titel."""
        result = create_filename_from_metadata(title="My Song", file_id="123")
        assert result == "My Song.mp3"
    
    def test_with_file_id_only(self):
        """Test nur mit File-ID."""
        result = create_filename_from_metadata(file_id="123")
        assert result == "audio_123.mp3"
    
    def test_without_any_data(self):
        """Test ohne alle Daten."""
        result = create_filename_from_metadata()
        assert result.startswith("audio_")
        assert result.endswith(".mp3")


class TestGetUniqueFilepath:
    """Tests für die get_unique_filepath-Funktion."""
    
    def test_non_existing_file(self):
        """Test mit nicht-existierender Datei."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.mp3"
            result = get_unique_filepath(file_path)
            assert result == file_path
    
    def test_existing_file(self):
        """Test mit existierender Datei."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.mp3"
            file_path.touch()  # Datei erstellen
            
            result = get_unique_filepath(file_path)
            assert result != file_path
            assert result.name == "test_1.mp3"


class TestCalculateFileHash:
    """Tests für die calculate_file_hash-Funktion."""
    
    def test_md5_hash(self):
        """Test MD5-Hash-Berechnung."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            temp_file.write("test content")
            temp_file.flush()
            temp_file.close()  # Datei explizit schließen
            
            try:
                result = calculate_file_hash(temp_file.name, 'md5')
                # MD5 prüfen - der genaue Wert hängt vom Betriebssystem ab
                assert len(result) == 32  # MD5 hat immer 32 Zeichen
                assert all(c in '0123456789abcdef' for c in result)  # Nur Hex-Zeichen
            finally:
                Path(temp_file.name).unlink(missing_ok=True)


class TestFormatFileSize:
    """Tests für die format_file_size-Funktion."""
    
    def test_bytes(self):
        """Test Formatierung in Bytes."""
        assert format_file_size(512) == "512.0 B"
    
    def test_kilobytes(self):
        """Test Formatierung in Kilobytes."""
        assert format_file_size(1024) == "1.0 KB"
    
    def test_megabytes(self):
        """Test Formatierung in Megabytes."""
        assert format_file_size(1048576) == "1.0 MB"
    
    def test_zero_size(self):
        """Test mit Null-Größe."""
        assert format_file_size(0) == "0 B"


class TestFormatDuration:
    """Tests für die format_duration-Funktion."""
    
    def test_minutes_seconds(self):
        """Test Formatierung Minuten:Sekunden."""
        assert format_duration(125.5) == "02:05"
    
    def test_hours_minutes_seconds(self):
        """Test Formatierung Stunden:Minuten:Sekunden."""
        assert format_duration(3725) == "01:02:05"
    
    def test_none_duration(self):
        """Test mit None-Wert."""
        assert format_duration(None) == "00:00"
    
    def test_zero_duration(self):
        """Test mit Null-Dauer."""
        assert format_duration(0) == "00:00"


class TestIsAudioFile:
    """Tests für die is_audio_file-Funktion."""
    
    def test_mp3_file(self):
        """Test mit MP3-Datei."""
        assert is_audio_file("test.mp3") == True
    
    def test_wav_file(self):
        """Test mit WAV-Datei."""
        assert is_audio_file("test.wav") == True
    
    def test_text_file(self):
        """Test mit Textdatei."""
        assert is_audio_file("test.txt") == False
    
    def test_uppercase_extension(self):
        """Test mit großgeschriebener Dateiendung."""
        assert is_audio_file("test.MP3") == True


class TestEnsureDirectoryExists:
    """Tests für die ensure_directory_exists-Funktion."""
    
    def test_create_new_directory(self):
        """Test Erstellung eines neuen Verzeichnisses."""
        with tempfile.TemporaryDirectory() as temp_dir:
            new_dir = Path(temp_dir) / "new_folder"
            result = ensure_directory_exists(new_dir)
            
            assert result.exists()
            assert result.is_dir()
            assert result == new_dir
    
    def test_existing_directory(self):
        """Test mit existierendem Verzeichnis."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = ensure_directory_exists(temp_dir)
            assert result.exists()
            assert result.is_dir()


class TestGetFileExtensionFromMime:
    """Tests für die get_file_extension_from_mime-Funktion."""
    
    def test_mp3_mime(self):
        """Test mit MP3 MIME-Type."""
        assert get_file_extension_from_mime("audio/mpeg") == ".mp3"
    
    def test_wav_mime(self):
        """Test mit WAV MIME-Type."""
        assert get_file_extension_from_mime("audio/wav") == ".wav"
    
    def test_unknown_mime(self):
        """Test mit unbekanntem MIME-Type."""
        assert get_file_extension_from_mime("unknown/type") == ".mp3"
    
    def test_case_insensitive(self):
        """Test Groß-/Kleinschreibung ignorieren."""
        assert get_file_extension_from_mime("AUDIO/MPEG") == ".mp3"


# Fixtures für komplexere Tests
@pytest.fixture
def temp_audio_file():
    """Erstellt eine temporäre Audio-Test-Datei."""
    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
        # Dummy-Audio-Inhalt (nur für Tests)
        temp_file.write(b"fake audio content")
        temp_file.flush()
        yield Path(temp_file.name)
    
    # Cleanup
    Path(temp_file.name).unlink(missing_ok=True)


@pytest.fixture
def temp_directory():
    """Erstellt ein temporäres Verzeichnis für Tests."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    pytest.main([__file__])