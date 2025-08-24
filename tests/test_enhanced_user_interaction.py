"""
Tests für die erweiterte Benutzerinteraktion.
"""

import unittest
from unittest.mock import patch, MagicMock

from src.telegram_audio_downloader.enhanced_user_interaction import (
    EnhancedUserInteraction, Notification, NotificationType
)

class TestEnhancedUserInteraction(unittest.TestCase):
    """Tests für die EnhancedUserInteraction-Klasse."""
    
    def setUp(self):
        """Erstellt eine Instanz der EnhancedUserInteraction-Klasse."""
        self.ui = EnhancedUserInteraction()
    
    def test_show_notification_info(self):
        """Testet die Anzeige einer Info-Benachrichtigung."""
        # Speichere die ursprüngliche Länge
        original_length = len(self.ui.notifications)
        
        with patch('src.telegram_audio_downloader.enhanced_user_interaction.console.print') as mock_print:
            self.ui.show_notification("Testnachricht", NotificationType.INFO)
            mock_print.assert_called_once()
            # Überprüfe, ob eine Benachrichtigung hinzugefügt wurde
            self.assertEqual(len(self.ui.notifications), original_length + 1)
            self.assertEqual(self.ui.notifications[-1].message, "Testnachricht")
            self.assertEqual(self.ui.notifications[-1].type, NotificationType.INFO)
    
    def test_show_notification_success(self):
        """Testet die Anzeige einer Erfolgs-Benachrichtigung."""
        # Speichere die ursprüngliche Länge
        original_length = len(self.ui.notifications)
        
        with patch('src.telegram_audio_downloader.enhanced_user_interaction.console.print') as mock_print:
            self.ui.show_notification("Erfolgsnachricht", NotificationType.SUCCESS)
            mock_print.assert_called_once()
            # Überprüfe, ob eine Benachrichtigung hinzugefügt wurde
            self.assertEqual(len(self.ui.notifications), original_length + 1)
            self.assertEqual(self.ui.notifications[-1].message, "Erfolgsnachricht")
            self.assertEqual(self.ui.notifications[-1].type, NotificationType.SUCCESS)
    
    def test_show_notification_warning(self):
        """Testet die Anzeige einer Warnungs-Benachrichtigung."""
        # Speichere die ursprüngliche Länge
        original_length = len(self.ui.notifications)
        
        with patch('src.telegram_audio_downloader.enhanced_user_interaction.console.print') as mock_print:
            self.ui.show_notification("Warnungsnachricht", NotificationType.WARNING)
            mock_print.assert_called_once()
            # Überprüfe, ob eine Benachrichtigung hinzugefügt wurde
            self.assertEqual(len(self.ui.notifications), original_length + 1)
            self.assertEqual(self.ui.notifications[-1].message, "Warnungsnachricht")
            self.assertEqual(self.ui.notifications[-1].type, NotificationType.WARNING)
    
    def test_show_notification_error(self):
        """Testet die Anzeige einer Fehler-Benachrichtigung."""
        # Speichere die ursprüngliche Länge
        original_length = len(self.ui.notifications)
        
        with patch('src.telegram_audio_downloader.enhanced_user_interaction.console.print') as mock_print:
            self.ui.show_notification("Fehlernachricht", NotificationType.ERROR)
            mock_print.assert_called_once()
            # Überprüfe, ob eine Benachrichtigung hinzugefügt wurde
            self.assertEqual(len(self.ui.notifications), original_length + 1)
            self.assertEqual(self.ui.notifications[-1].message, "Fehlernachricht")
            self.assertEqual(self.ui.notifications[-1].type, NotificationType.ERROR)
    
    def test_notification_callback(self):
        """Testet den Notification-Callback."""
        callback = MagicMock()
        self.ui.set_notification_callback(callback)
        
        with patch('src.telegram_audio_downloader.enhanced_user_interaction.console.print'):
            self.ui.show_notification("Testnachricht")
            callback.assert_called_once()
            notification = callback.call_args[0][0]
            self.assertIsInstance(notification, Notification)
            self.assertEqual(notification.message, "Testnachricht")
    
    def test_show_context_menu(self):
        """Testet die Anzeige eines Kontextmenüs."""
        with patch('src.telegram_audio_downloader.enhanced_user_interaction.console.print') as mock_print, \
             patch('src.telegram_audio_downloader.enhanced_user_interaction.Prompt.ask', return_value='1') as mock_ask:
            options = ["Option 1", "Option 2", "Option 3"]
            result = self.ui.show_context_menu("Testmenü", options)
            self.assertEqual(result, 0)  # 0-basiert
            self.assertEqual(mock_print.call_count, 4)  # Titel + 3 Optionen
            mock_ask.assert_called_once()
    
    def test_show_confirmation_dialog(self):
        """Testet die Anzeige eines Bestätigungsdialogs."""
        with patch('src.telegram_audio_downloader.enhanced_user_interaction.Confirm.ask', return_value=True) as mock_confirm:
            result = self.ui.show_confirmation_dialog("Bestätigen?")
            self.assertTrue(result)
            mock_confirm.assert_called_once_with("Bestätigen?", default=True)
    
    def test_enable_interactive_mode(self):
        """Testet das Aktivieren des interaktiven Modus."""
        with patch('src.telegram_audio_downloader.enhanced_user_interaction.console.print') as mock_print:
            self.ui.enable_interactive_mode()
            self.assertTrue(self.ui.is_interactive_mode)
            mock_print.assert_called_once()
    
    def test_disable_interactive_mode(self):
        """Testet das Deaktivieren des interaktiven Modus."""
        with patch('src.telegram_audio_downloader.enhanced_user_interaction.console.print') as mock_print:
            self.ui.is_interactive_mode = True
            self.ui.disable_interactive_mode()
            self.assertFalse(self.ui.is_interactive_mode)
            mock_print.assert_called_once()
    
    def test_show_download_summary(self):
        """Testet die Anzeige einer Download-Zusammenfassung."""
        with patch('src.telegram_audio_downloader.enhanced_user_interaction.console.print') as mock_print:
            stats = {
                "total_files": 10,
                "successful_downloads": 8,
                "failed_downloads": 2,
                "total_size": "50 MB",
                "duration": "10s",
                "avg_speed": "5 MB/s"
            }
            self.ui.show_download_summary(stats)
            mock_print.assert_called_once()

if __name__ == "__main__":
    unittest.main()