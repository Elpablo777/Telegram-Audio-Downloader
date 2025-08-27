"""
Tests für den interaktiven Modus im Telegram Audio Downloader.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import asyncio

from src.telegram_audio_downloader.interactive_mode import InteractiveMode, start_interactive_mode
from src.telegram_audio_downloader.downloader import AudioDownloader
from src.telegram_audio_downloader.models import AudioFile


class TestInteractiveMode:
    """Testfälle für den interaktiven Modus."""
    
    @pytest.fixture
    def mock_downloader(self):
        """Erstellt einen gemockten AudioDownloader."""
        downloader = Mock(spec=AudioDownloader)
        downloader.client = AsyncMock()
        return downloader
    
    @pytest.fixture
    def interactive_mode(self, mock_downloader):
        """Erstellt eine InteractiveMode-Instanz mit gemocktem Downloader."""
        return InteractiveMode(mock_downloader)
    
    def test_initialization(self, interactive_mode):
        """Testet die Initialisierung des interaktiven Modus."""
        assert interactive_mode is not None
        assert hasattr(interactive_mode, 'downloader')
        assert hasattr(interactive_mode, 'console')
        assert hasattr(interactive_mode, 'categorizer')
    
    @pytest.mark.asyncio
    async def test_start_interactive_mode(self, mock_downloader):
        """Testet die start_interactive_mode-Funktion."""
        # Dieser Test ist schwierig, da er Benutzerinteraktion erfordert
        # Wir testen stattdessen, ob die Funktion korrekt aufgerufen werden kann
        with patch('src.telegram_audio_downloader.interactive_mode.InteractiveMode.run', new_callable=AsyncMock) as mock_run:
            await start_interactive_mode(mock_downloader)
            mock_run.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_show_main_menu(self, interactive_mode, capsys):
        """Testet die Anzeige des Hauptmenüs."""
        # Dieser Test ist schwierig, da rich.Console verwendet wird
        # Wir testen stattdessen, ob die Methode aufgerufen werden kann
        try:
            interactive_mode._show_main_menu()
            # Wenn keine Exception geworfen wird, ist der Test erfolgreich
            assert True
        except Exception as e:
            pytest.fail(f"Fehler beim Anzeigen des Hauptmenüs: {e}")
    
    @pytest.mark.asyncio
    async def test_view_settings(self, interactive_mode):
        """Testet die Anzeige der Einstellungen."""
        # Dieser Test ist schwierig, da rich.Console verwendet wird
        # Wir testen stattdessen, ob die Methode aufgerufen werden kann
        try:
            await interactive_mode._view_settings()
            # Wenn keine Exception geworfen wird, ist der Test erfolgreich
            assert True
        except Exception as e:
            pytest.fail(f"Fehler beim Anzeigen der Einstellungen: {e}")
    
    @pytest.mark.asyncio
    async def test_view_downloaded_files(self, interactive_mode):
        """Testet die Anzeige heruntergeladener Dateien."""
        # Mock die Datenbankabfrage
        with patch('src.telegram_audio_downloader.interactive_mode.AudioFile') as mock_audio_file:
            mock_audio_file.select.return_value.where.return_value = []
            
            # Teste, ob die Methode aufgerufen werden kann
            try:
                await interactive_mode._view_downloaded_files()
                # Wenn keine Exception geworfen wird, ist der Test erfolgreich
                assert True
            except Exception as e:
                pytest.fail(f"Fehler beim Anzeigen heruntergeladener Dateien: {e}")
    
    @pytest.mark.asyncio
    async def test_search_downloaded_files(self, interactive_mode):
        """Testet die Suche in heruntergeladenen Dateien."""
        # Mock die Suchfunktion
        with patch('src.telegram_audio_downloader.interactive_mode.search_downloaded_files') as mock_search:
            mock_search.return_value = []
            
            # Teste, ob die Methode aufgerufen werden kann
            try:
                with patch('src.telegram_audio_downloader.interactive_mode.Prompt.ask', return_value='test'):
                    await interactive_mode._search_downloaded_files()
                # Wenn keine Exception geworfen wird, ist der Test erfolgreich
                assert True
            except Exception as e:
                pytest.fail(f"Fehler bei der Suche in heruntergeladenen Dateien: {e}")


if __name__ == "__main__":
    pytest.main([__file__])