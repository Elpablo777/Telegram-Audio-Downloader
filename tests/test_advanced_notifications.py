#!/usr/bin/env python3
"""
Tests für die erweiterten Benachrichtigungen - Telegram Audio Downloader
======================================================================

Tests für die verschiedenen Benachrichtigungsmethoden.
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from telegram_audio_downloader.advanced_notifications import (
    EmailConfig, PushConfig, WebhookConfig, NotificationEvent,
    EmailNotifier, PushNotifier, WebhookNotifier, AdvancedNotifier,
    get_advanced_notifier, send_download_completed_notification,
    send_download_failed_notification, send_batch_completed_notification
)

class TestEmailNotifier:
    """Tests für den E-Mail-Benachrichtigungsmanager."""
    
    def test_email_config_creation(self):
        """Test erstellt eine E-Mail-Konfiguration."""
        config = EmailConfig(
            smtp_server="smtp.example.com",
            smtp_port=587,
            username="test@example.com",
            password=os.getenv("TEST_EMAIL_PASSWORD", "fake_test_password"),
            sender_email="test@example.com",
            recipient_emails=["recipient@example.com"]
        )
        
        assert config.smtp_server == "smtp.example.com"
        assert config.smtp_port == 587
        assert config.username == "test@example.com"
        assert config.password == "password"
        assert config.sender_email == "test@example.com"
        assert config.recipient_emails == ["recipient@example.com"]
    
    @patch('telegram_audio_downloader.advanced_notifications.smtplib.SMTP')
    def test_send_email_success(self, mock_smtp):
        """Test sendet eine E-Mail erfolgreich."""
        # Mock die SMTP-Verbindung
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        # Erstelle die Konfiguration
        config = EmailConfig(
            smtp_server="smtp.example.com",
            smtp_port=587,
            username="test@example.com",
            password=os.getenv("TEST_EMAIL_PASSWORD", "fake_test_password"),
            sender_email="test@example.com",
            recipient_emails=["recipient@example.com"]
        )
        
        # Erstelle den Notifier
        notifier = EmailNotifier(config)
        
        # Sende die E-Mail
        result = notifier.send_email("Test Subject", "Test Body")
        
        # Überprüfe die Ergebnisse
        assert result is True
        mock_smtp.assert_called_once_with("smtp.example.com", 587)
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("test@example.com", "password")
        mock_server.send_message.assert_called_once()
    
    @patch('telegram_audio_downloader.advanced_notifications.smtplib.SMTP')
    def test_send_email_failure(self, mock_smtp):
        """Test behandelt einen Fehler beim Senden einer E-Mail."""
        # Mock die SMTP-Verbindung, um einen Fehler zu simulieren
        mock_smtp.side_effect = Exception("SMTP Error")
        
        # Erstelle die Konfiguration
        config = EmailConfig(
            smtp_server="smtp.example.com",
            smtp_port=587,
            username="test@example.com",
            password=os.getenv("TEST_EMAIL_PASSWORD", "fake_test_password"),
            sender_email="test@example.com",
            recipient_emails=["recipient@example.com"]
        )
        
        # Erstelle den Notifier
        notifier = EmailNotifier(config)
        
        # Sende die E-Mail
        result = notifier.send_email("Test Subject", "Test Body")
        
        # Überprüfe die Ergebnisse
        assert result is False

class TestPushNotifier:
    """Tests für den Push-Benachrichtigungsmanager."""
    
    def test_push_config_creation(self):
        """Test erstellt eine Push-Konfiguration."""
        config = PushConfig(
            service_url="https://api.push.example.com/send",
            api_key="api_key",
            device_token="device_token"
        )
        
        assert config.service_url == "https://api.push.example.com/send"
        assert config.api_key == "api_key"
        assert config.device_token == "device_token"
    
    @patch('telegram_audio_downloader.advanced_notifications.requests.post')
    def test_send_push_success(self, mock_post):
        """Test sendet eine Push-Benachrichtigung erfolgreich."""
        # Mock die HTTP-Anfrage
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # Erstelle die Konfiguration
        config = PushConfig(
            service_url="https://api.push.example.com/send",
            api_key="api_key",
            device_token="device_token"
        )
        
        # Erstelle den Notifier
        notifier = PushNotifier(config)
        
        # Sende die Push-Benachrichtigung
        result = notifier.send_push("Test Title", "Test Message")
        
        # Überprüfe die Ergebnisse
        assert result is True
        mock_post.assert_called_once()
    
    @patch('telegram_audio_downloader.advanced_notifications.requests.post')
    def test_send_push_failure(self, mock_post):
        """Test behandelt einen Fehler beim Senden einer Push-Benachrichtigung."""
        # Mock die HTTP-Anfrage, um einen Fehler zu simulieren
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response
        
        # Erstelle die Konfiguration
        config = PushConfig(
            service_url="https://api.push.example.com/send",
            api_key="api_key",
            device_token="device_token"
        )
        
        # Erstelle den Notifier
        notifier = PushNotifier(config)
        
        # Sende die Push-Benachrichtigung
        result = notifier.send_push("Test Title", "Test Message")
        
        # Überprüfe die Ergebnisse
        assert result is False

class TestWebhookNotifier:
    """Tests für den Webhook-Benachrichtigungsmanager."""
    
    def test_webhook_config_creation(self):
        """Test erstellt eine Webhook-Konfiguration."""
        config = WebhookConfig(
            url="https://webhook.example.com/notify",
            method="POST",
            headers={"Authorization": "Bearer token"},
            payload_template='{"title": "{title}", "message": "{message}"}'
        )
        
        assert config.url == "https://webhook.example.com/notify"
        assert config.method == "POST"
        assert config.headers == {"Authorization": "Bearer token"}
        assert config.payload_template == '{"title": "{title}", "message": "{message}"}'
    
    @patch('telegram_audio_downloader.advanced_notifications.requests.request')
    def test_send_webhook_success(self, mock_request):
        """Test sendet einen Webhook erfolgreich."""
        # Mock die HTTP-Anfrage
        mock_response = Mock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response
        
        # Erstelle die Konfiguration
        config = WebhookConfig(
            url="https://webhook.example.com/notify"
        )
        
        # Erstelle den Notifier
        notifier = WebhookNotifier(config)
        
        # Erstelle ein Ereignis
        event = NotificationEvent(
            event_type="test",
            title="Test Title",
            message="Test Message",
            timestamp=datetime.now()
        )
        
        # Sende den Webhook
        result = notifier.send_webhook(event)
        
        # Überprüfe die Ergebnisse
        assert result is True
        mock_request.assert_called_once()
    
    @patch('telegram_audio_downloader.advanced_notifications.requests.request')
    def test_send_webhook_failure(self, mock_request):
        """Test behandelt einen Fehler beim Senden eines Webhooks."""
        # Mock die HTTP-Anfrage, um einen Fehler zu simulieren
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_request.return_value = mock_response
        
        # Erstelle die Konfiguration
        config = WebhookConfig(
            url="https://webhook.example.com/notify"
        )
        
        # Erstelle den Notifier
        notifier = WebhookNotifier(config)
        
        # Erstelle ein Ereignis
        event = NotificationEvent(
            event_type="test",
            title="Test Title",
            message="Test Message",
            timestamp=datetime.now()
        )
        
        # Sende den Webhook
        result = notifier.send_webhook(event)
        
        # Überprüfe die Ergebnisse
        assert result is False

class TestAdvancedNotifier:
    """Tests für den erweiterten Benachrichtigungsmanager."""
    
    def test_notification_event_creation(self):
        """Test erstellt ein Benachrichtigungsereignis."""
        event = NotificationEvent(
            event_type="test",
            title="Test Title",
            message="Test Message",
            timestamp=datetime.now(),
            data={"key": "value"},
            priority="high"
        )
        
        assert event.event_type == "test"
        assert event.title == "Test Title"
        assert event.message == "Test Message"
        assert event.data == {"key": "value"}
        assert event.priority == "high"
    
    @patch('telegram_audio_downloader.advanced_notifications.get_system_notifier')
    def test_send_notification(self, mock_get_system_notifier):
        """Test sendet eine Benachrichtigung über alle Kanäle."""
        # Mock den System-Notifier
        mock_system_notifier = Mock()
        mock_system_notifier.send_notification.return_value = True
        mock_get_system_notifier.return_value = mock_system_notifier
        
        # Erstelle den Notifier ohne zusätzliche Konfigurationen
        notifier = AdvancedNotifier()
        
        # Erstelle ein Ereignis
        event = NotificationEvent(
            event_type="test",
            title="Test Title",
            message="Test Message",
            timestamp=datetime.now()
        )
        
        # Sende die Benachrichtigung
        results = notifier.send_notification(event)
        
        # Überprüfe die Ergebnisse
        assert isinstance(results, dict)
        assert results["system"] is True
        assert "email" not in results
        assert "push" not in results
        assert "webhook" not in results
    
    @patch('telegram_audio_downloader.advanced_notifications.get_system_notifier')
    def test_send_download_completed(self, mock_get_system_notifier):
        """Test sendet eine Benachrichtigung über einen abgeschlossenen Download."""
        # Mock den System-Notifier
        mock_system_notifier = Mock()
        mock_system_notifier.send_notification.return_value = True
        mock_get_system_notifier.return_value = mock_system_notifier
        
        # Erstelle den Notifier
        notifier = AdvancedNotifier()
        
        # Sende die Benachrichtigung
        results = notifier.send_download_completed("test.mp3", 1024*1024, 5.5)
        
        # Überprüfe die Ergebnisse
        assert isinstance(results, dict)
        assert results["system"] is True

class TestGlobalFunctions:
    """Tests für die globalen Hilfsfunktionen."""
    
    @patch('telegram_audio_downloader.advanced_notifications.get_advanced_notifier')
    def test_send_download_completed_notification(self, mock_get_notifier):
        """Test sendet eine Benachrichtigung über einen abgeschlossenen Download."""
        # Mock den Notifier
        mock_notifier = Mock()
        mock_notifier.send_download_completed.return_value = {"system": True}
        mock_get_notifier.return_value = mock_notifier
        
        # Sende die Benachrichtigung
        results = send_download_completed_notification("test.mp3", 1024*1024, 5.5)
        
        # Überprüfe die Ergebnisse
        assert results == {"system": True}
        mock_notifier.send_download_completed.assert_called_once_with("test.mp3", 1024*1024, 5.5)
    
    @patch('telegram_audio_downloader.advanced_notifications.get_advanced_notifier')
    def test_send_download_failed_notification(self, mock_get_notifier):
        """Test sendet eine Benachrichtigung über einen fehlgeschlagenen Download."""
        # Mock den Notifier
        mock_notifier = Mock()
        mock_notifier.send_download_failed.return_value = {"system": True}
        mock_get_notifier.return_value = mock_notifier
        
        # Sende die Benachrichtigung
        results = send_download_failed_notification("test.mp3", "Connection error")
        
        # Überprüfe die Ergebnisse
        assert results == {"system": True}
        mock_notifier.send_download_failed.assert_called_once_with("test.mp3", "Connection error")
    
    @patch('telegram_audio_downloader.advanced_notifications.get_advanced_notifier')
    def test_send_batch_completed_notification(self, mock_get_notifier):
        """Test sendet eine Benachrichtigung über abgeschlossene Batch-Verarbeitung."""
        # Mock den Notifier
        mock_notifier = Mock()
        mock_notifier.send_batch_completed.return_value = {"system": True}
        mock_get_notifier.return_value = mock_notifier
        
        # Sende die Benachrichtigung
        results = send_batch_completed_notification(10, 8, 2)
        
        # Überprüfe die Ergebnisse
        assert results == {"system": True}
        mock_notifier.send_batch_completed.assert_called_once_with(10, 8, 2)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])