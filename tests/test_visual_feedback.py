"""
Tests für das visuelle Feedback im Telegram Audio Downloader.
"""

import pytest
import time
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from src.telegram_audio_downloader.visual_feedback import (
    FeedbackType,
    FeedbackLevel,
    VisualFeedbackConfig,
    FeedbackMessage,
    VisualFeedbackManager,
    get_feedback_manager,
    show_message,
    show_success,
    show_error,
    show_warning,
    show_info,
    show_progress,
    update_progress,
    stop_progress,
    show_notification_center,
    clear_notifications
)


class TestFeedbackType:
    """Testfälle für die FeedbackType-Enumeration."""
    
    def test_feedback_type_values(self):
        """Testet die Werte der FeedbackType-Enumeration."""
        assert FeedbackType.SUCCESS.value == "success"
        assert FeedbackType.ERROR.value == "error"
        assert FeedbackType.WARNING.value == "warning"
        assert FeedbackType.INFO.value == "info"
        assert FeedbackType.PROGRESS.value == "progress"
        assert FeedbackType.NOTIFICATION.value == "notification"
        assert FeedbackType.CONFIRMATION.value == "confirmation"
        assert FeedbackType.DEBUG.value == "debug"


class TestFeedbackLevel:
    """Testfälle für die FeedbackLevel-Enumeration."""
    
    def test_feedback_level_values(self):
        """Testet die Werte der FeedbackLevel-Enumeration."""
        assert FeedbackLevel.LOW.value == "low"
        assert FeedbackLevel.MEDIUM.value == "medium"
        assert FeedbackLevel.HIGH.value == "high"
        assert FeedbackLevel.CRITICAL.value == "critical"


class TestVisualFeedbackConfig:
    """Testfälle für die VisualFeedbackConfig-Datenklasse."""
    
    def test_initialization(self):
        """Testet die Initialisierung der VisualFeedbackConfig-Klasse."""
        config = VisualFeedbackConfig(
            enable_animations=True,
            enable_colors=False,
            feedback_level=FeedbackLevel.HIGH,
            animation_speed=2.0,
            show_timestamps=True,
            persistent_notifications=True,
            max_notification_age=600
        )
        
        assert config.enable_animations == True
        assert config.enable_colors == False
        assert config.feedback_level == FeedbackLevel.HIGH
        assert config.animation_speed == 2.0
        assert config.show_timestamps == True
        assert config.persistent_notifications == True
        assert config.max_notification_age == 600


class TestFeedbackMessage:
    """Testfälle für die FeedbackMessage-Datenklasse."""
    
    def test_initialization(self):
        """Testet die Initialisierung der FeedbackMessage-Klasse."""
        message = FeedbackMessage(
            message="Test message",
            type=FeedbackType.INFO,
            level=FeedbackLevel.MEDIUM,
            title="Test Title",
            details="Test details",
            duration=5.0,
            icon="ℹ️"
        )
        
        assert message.message == "Test message"
        assert message.type == FeedbackType.INFO
        assert message.level == FeedbackLevel.MEDIUM
        assert message.title == "Test Title"
        assert message.details == "Test details"
        assert message.duration == 5.0
        assert message.icon == "ℹ️"
        assert isinstance(message.timestamp, datetime)
        assert message.action_buttons == {}
        assert message.metadata == {}


class TestVisualFeedbackManager:
    """Testfälle für die VisualFeedbackManager-Klasse."""
    
    def test_initialization(self):
        """Testet die Initialisierung des VisualFeedbackManagers."""
        manager = VisualFeedbackManager()
        
        assert manager is not None
        assert hasattr(manager, 'console')
        assert hasattr(manager, 'config')
        assert isinstance(manager.notifications, dict)
        assert isinstance(manager.active_progress_bars, dict)
        assert isinstance(manager.live_displays, dict)
        assert isinstance(manager.message_history, list)
    
    def test_initialization_with_config(self):
        """Testet die Initialisierung mit benutzerdefinierter Konfiguration."""
        config = VisualFeedbackConfig(feedback_level=FeedbackLevel.HIGH)
        manager = VisualFeedbackManager(config)
        
        assert manager.config.feedback_level == FeedbackLevel.HIGH
    
    def test_show_message_string(self):
        """Testet das Anzeigen einer Nachricht als String."""
        manager = VisualFeedbackManager()
        
        # Teste das Anzeigen einer einfachen Nachricht
        manager.show_message("Test message", FeedbackType.INFO)
        
        # Überprüfe, ob die Nachricht zur Historie hinzugefügt wurde
        assert len(manager.message_history) == 1
        assert manager.message_history[0].message == "Test message"
        assert manager.message_history[0].type == FeedbackType.INFO
    
    def test_show_message_object(self):
        """Testet das Anzeigen einer Nachricht als FeedbackMessage-Objekt."""
        manager = VisualFeedbackManager()
        
        message_obj = FeedbackMessage(
            message="Test object message",
            type=FeedbackType.SUCCESS
        )
        
        manager.show_message(message_obj)
        
        # Überprüfe, ob die Nachricht zur Historie hinzugefügt wurde
        assert len(manager.message_history) == 1
        assert manager.message_history[0].message == "Test object message"
        assert manager.message_history[0].type == FeedbackType.SUCCESS
    
    def test_should_show_message(self):
        """Testet die Prüfung, ob eine Nachricht angezeigt werden soll."""
        config = VisualFeedbackConfig(feedback_level=FeedbackLevel.MEDIUM)
        manager = VisualFeedbackManager(config)
        
        # Nachricht mit niedrigerem Level sollte nicht angezeigt werden
        low_message = FeedbackMessage(
            message="Low priority message",
            type=FeedbackType.DEBUG,
            level=FeedbackLevel.LOW
        )
        assert manager._should_show_message(low_message) == False
        
        # Nachricht mit gleichem Level sollte angezeigt werden
        medium_message = FeedbackMessage(
            message="Medium priority message",
            type=FeedbackType.INFO,
            level=FeedbackLevel.MEDIUM
        )
        assert manager._should_show_message(medium_message) == True
        
        # Nachricht mit höherem Level sollte angezeigt werden
        high_message = FeedbackMessage(
            message="High priority message",
            type=FeedbackType.ERROR,
            level=FeedbackLevel.HIGH
        )
        assert manager._should_show_message(high_message) == True
    
    def test_show_notification(self):
        """Testet das Anzeigen einer Benachrichtigung."""
        config = VisualFeedbackConfig(persistent_notifications=True)
        manager = VisualFeedbackManager(config)
        
        # Zeige eine Benachrichtigung
        manager.show_message("Test notification", FeedbackType.NOTIFICATION)
        
        # Überprüfe, ob die Benachrichtigung gespeichert wurde
        assert len(manager.notifications) == 1
        assert len(manager.message_history) == 1
    
    def test_show_progress(self):
        """Testet das Anzeigen eines Fortschrittsbalkens."""
        manager = VisualFeedbackManager()
        
        # Zeige einen Fortschrittsbalken
        progress = manager.show_progress("test_task", "Test task", total=100.0)
        
        # Überprüfe, ob der Fortschrittsbalken gespeichert wurde
        assert "test_task" in manager.active_progress_bars
        assert manager.active_progress_bars["test_task"] is progress
        
        # Stoppe den Fortschrittsbalken
        manager.stop_progress("test_task")
        assert "test_task" not in manager.active_progress_bars
    
    def test_update_progress(self):
        """Testet das Aktualisieren eines Fortschrittsbalkens."""
        manager = VisualFeedbackManager()
        
        # Zeige einen Fortschrittsbalken
        progress = manager.show_progress("update_test", "Update test", total=100.0, start=False)
        
        # Aktualisiere den Fortschritt
        manager.update_progress("update_test", advance=50.0)
        
        # Stoppe den Fortschrittsbalken
        manager.stop_progress("update_test")
    
    def test_show_live_display(self):
        """Testet das Anzeigen einer Live-Anzeige."""
        manager = VisualFeedbackManager()
        
        # Erstelle ein einfaches Renderable
        from rich.text import Text
        renderable = Text("Live display test")
        
        # Zeige die Live-Anzeige
        live = manager.show_live_display("test_display", renderable)
        
        # Überprüfe, ob die Live-Anzeige gespeichert wurde
        assert "test_display" in manager.live_displays
        assert manager.live_displays["test_display"] is live
        
        # Stoppe die Live-Anzeige
        manager.stop_live_display("test_display")
        assert "test_display" not in manager.live_displays
    
    def test_update_live_display(self):
        """Testet das Aktualisieren einer Live-Anzeige."""
        manager = VisualFeedbackManager()
        
        # Erstelle ein einfaches Renderable
        from rich.text import Text
        renderable1 = Text("First display")
        renderable2 = Text("Second display")
        
        # Zeige die Live-Anzeige
        manager.show_live_display("update_test", renderable1)
        
        # Aktualisiere die Live-Anzeige
        manager.update_live_display("update_test", renderable2)
        
        # Stoppe die Live-Anzeige
        manager.stop_live_display("update_test")
    
    def test_notification_center(self):
        """Testet das Benachrichtigungszentrum."""
        config = VisualFeedbackConfig(persistent_notifications=True)
        manager = VisualFeedbackManager(config)
        
        # Füge einige Benachrichtigungen hinzu
        manager.show_message("Notification 1", FeedbackType.NOTIFICATION)
        manager.show_message("Notification 2", FeedbackType.NOTIFICATION)
        
        # Überprüfe, ob Benachrichtigungen vorhanden sind
        assert len(manager.notifications) == 2
        
        # Lösche die Benachrichtigungen
        manager.clear_notifications()
        assert len(manager.notifications) == 0
    
    def test_get_feedback_stats(self):
        """Testet das Abrufen von Feedback-Statistiken."""
        manager = VisualFeedbackManager()
        
        # Füge einige Nachrichten hinzu
        manager.show_message("Info message", FeedbackType.INFO)
        manager.show_message("Success message", FeedbackType.SUCCESS)
        manager.show_message("Error message", FeedbackType.ERROR)
        
        # Zeige einen Fortschrittsbalken
        manager.show_progress("stats_test", "Stats test")
        
        # Erstelle eine Live-Anzeige
        from rich.text import Text
        renderable = Text("Stats display")
        manager.show_live_display("stats_display", renderable)
        
        # Hole die Statistiken
        stats = manager.get_feedback_stats()
        
        assert isinstance(stats, dict)
        assert stats["total"] == 3
        assert stats["info"] == 1
        assert stats["success"] == 1
        assert stats["error"] == 1
        assert stats["active_progress"] == 1
        assert stats["live_displays"] == 1
    
    def test_set_config(self):
        """Testet das Setzen der Konfiguration."""
        manager = VisualFeedbackManager()
        
        # Erstelle eine neue Konfiguration
        new_config = VisualFeedbackConfig(feedback_level=FeedbackLevel.CRITICAL)
        
        # Setze die neue Konfiguration
        manager.set_config(new_config)
        
        assert manager.config.feedback_level == FeedbackLevel.CRITICAL


class TestGlobalFunctions:
    """Testfälle für die globalen Funktionen."""
    
    def test_get_feedback_manager_singleton(self):
        """Testet, dass der VisualFeedbackManager als Singleton funktioniert."""
        manager1 = get_feedback_manager()
        manager2 = get_feedback_manager()
        
        assert manager1 is manager2
    
    def test_show_message_global(self):
        """Testet das Anzeigen einer Nachricht über die globale Funktion."""
        # Zeige eine Nachricht
        show_message("Global test message", FeedbackType.INFO)
        
        # Überprüfe, ob die Nachricht angezeigt wurde
        manager = get_feedback_manager()
        assert len(manager.message_history) > 0
        assert manager.message_history[-1].message == "Global test message"
    
    def test_show_success_global(self):
        """Testet das Anzeigen einer Erfolgsmeldung über die globale Funktion."""
        show_success("Success test", "Test title", "Test details")
        
        manager = get_feedback_manager()
        last_message = manager.message_history[-1]
        assert last_message.message == "Success test"
        assert last_message.type == FeedbackType.SUCCESS
        assert last_message.title == "Test title"
        assert last_message.details == "Test details"
    
    def test_show_error_global(self):
        """Testet das Anzeigen einer Fehlermeldung über die globale Funktion."""
        show_error("Error test", "Error title", "Error details")
        
        manager = get_feedback_manager()
        last_message = manager.message_history[-1]
        assert last_message.message == "Error test"
        assert last_message.type == FeedbackType.ERROR
        assert last_message.title == "Error title"
        assert last_message.details == "Error details"
    
    def test_show_warning_global(self):
        """Testet das Anzeigen einer Warnung über die globale Funktion."""
        show_warning("Warning test", "Warning title", "Warning details")
        
        manager = get_feedback_manager()
        last_message = manager.message_history[-1]
        assert last_message.message == "Warning test"
        assert last_message.type == FeedbackType.WARNING
        assert last_message.title == "Warning title"
        assert last_message.details == "Warning details"
    
    def test_show_info_global(self):
        """Testet das Anzeigen einer Informationsmeldung über die globale Funktion."""
        show_info("Info test", "Info title", "Info details")
        
        manager = get_feedback_manager()
        last_message = manager.message_history[-1]
        assert last_message.message == "Info test"
        assert last_message.type == FeedbackType.INFO
        assert last_message.title == "Info title"
        assert last_message.details == "Info details"
    
    def test_show_progress_global(self):
        """Testet das Anzeigen eines Fortschrittsbalkens über die globale Funktion."""
        # Zeige einen Fortschrittsbalken
        progress = show_progress("global_test", "Global test")
        
        # Überprüfe, ob der Fortschrittsbalken angezeigt wurde
        manager = get_feedback_manager()
        assert "global_test" in manager.active_progress_bars
        
        # Stoppe den Fortschrittsbalken
        stop_progress("global_test")
        assert "global_test" not in manager.active_progress_bars
    
    def test_update_progress_global(self):
        """Testet das Aktualisieren eines Fortschrittsbalkens über die globale Funktion."""
        # Zeige einen Fortschrittsbalken
        show_progress("global_update_test", "Global update test", start=False)
        
        # Aktualisiere den Fortschritt
        update_progress("global_update_test", advance=50.0)
        
        # Stoppe den Fortschrittsbalken
        stop_progress("global_update_test")
    
    def test_show_notification_center_global(self):
        """Testet das Anzeigen des Benachrichtigungszentrums über die globale Funktion."""
        # Dies sollte ohne Exception ausgeführt werden können
        try:
            show_notification_center()
            assert True
        except Exception as e:
            pytest.fail(f"Fehler beim Anzeigen des Benachrichtigungszentrums: {e}")
    
    def test_clear_notifications_global(self):
        """Testet das Löschen von Benachrichtigungen über die globale Funktion."""
        # Dies sollte ohne Exception ausgeführt werden können
        try:
            clear_notifications()
            assert True
        except Exception as e:
            pytest.fail(f"Fehler beim Löschen von Benachrichtigungen: {e}")


if __name__ == "__main__":
    pytest.main([__file__])