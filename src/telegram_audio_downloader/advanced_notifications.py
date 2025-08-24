"""
Erweiterte Benachrichtigungen für den Telegram Audio Downloader.
"""

import json
import smtplib
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional

import requests
from plyer import notification as plyer_notification

from .config import Config
from .error_handling import handle_error
from .logging_config import get_logger
from .system_integration import SystemNotification, get_system_notifier

# Eigene Systembenachrichtigungsklasse ohne externe Abhängigkeiten
class SimpleSystemNotifier:
    """Einfache Systembenachrichtigungen ohne externe Abhängigkeiten."""
    
    def __init__(self):
        self.logger = get_logger(__name__ + ".SimpleSystemNotifier")
    
    def send_notification(self, notification: SystemNotification) -> bool:
        """
        Sendet eine Systembenachrichtigung.
        
        Args:
            notification: Systembenachrichtigung
            
        Returns:
            True, wenn die Benachrichtigung gesendet wurde, False sonst
        """
        try:
            # Versuche verschiedene Plattformmethoden
            if sys.platform == "win32":
                return self._send_windows_notification(notification)
            elif sys.platform == "darwin":
                return self._send_macos_notification(notification)
            else:
                return self._send_linux_notification(notification)
        except Exception as e:
            self.logger.warning(f"Fehler beim Senden der Systembenachrichtigung: {e}")
            return False
    
    def _send_windows_notification(self, notification: SystemNotification) -> bool:
        """Sendet eine Windows-Benachrichtigung."""
        try:
            # Verwende msg-Befehl unter Windows
            subprocess.run([
                "msg", 
                "*", 
                f"{notification.title}: {notification.message}"
            ], capture_output=True, timeout=5)
            return True
        except Exception:
            # Fallback: Einfache Ausgabe in der Konsole
            print(f"[NOTIFICATION] {notification.title}: {notification.message}")
            return True
    
    def _send_macos_notification(self, notification: SystemNotification) -> bool:
        """Sendet eine macOS-Benachrichtigung."""
        try:
            subprocess.run([
                "osascript", 
                "-e", 
                f'display notification "{notification.message}" with title "{notification.title}"'
            ], capture_output=True, timeout=5)
            return True
        except Exception:
            # Fallback: Einfache Ausgabe in der Konsole
            print(f"[NOTIFICATION] {notification.title}: {notification.message}")
            return True
    
    def _send_linux_notification(self, notification: SystemNotification) -> bool:
        """Sendet eine Linux-Benachrichtigung."""
        try:
            subprocess.run([
                "notify-send", 
                notification.title, 
                notification.message
            ], capture_output=True, timeout=5)
            return True
        except Exception:
            # Fallback: Einfache Ausgabe in der Konsole
            print(f"[NOTIFICATION] {notification.title}: {notification.message}")
            return True

# Globale Instanz für einfache Systembenachrichtigungen
_simple_system_notifier = SimpleSystemNotifier()

def get_simple_system_notifier() -> SimpleSystemNotifier:
    """
    Gibt die globale Instanz des einfachen Systembenachrichtigungsmanagers zurück.
    
    Returns:
        Instanz von SimpleSystemNotifier
    """
    return _simple_system_notifier

logger = get_logger(__name__)


@dataclass
class EmailConfig:
    """Konfiguration für E-Mail-Benachrichtigungen."""
    smtp_server: str
    smtp_port: int
    username: str
    password: str
    sender_email: str
    recipient_emails: List[str]
    use_tls: bool = True

@dataclass
class PushConfig:
    """Konfiguration für Push-Benachrichtigungen."""
    service_url: str
    api_key: str
    device_token: str

@dataclass
class WebhookConfig:
    """Konfiguration für Webhook-Benachrichtigungen."""
    url: str
    method: str = "POST"
    headers: Dict[str, str] = None
    payload_template: str = None

@dataclass
class NotificationEvent:
    """Ein Benachrichtigungsereignis."""
    event_type: str
    title: str
    message: str
    timestamp: datetime
    data: Optional[Dict[str, Any]] = None
    priority: str = "normal"  # low, normal, high, critical

class EmailNotifier:
    """Verwaltung von E-Mail-Benachrichtigungen."""
    
    def __init__(self, config: EmailConfig):
        """
        Initialisiert den E-Mail-Benachrichtigungsmanager.
        
        Args:
            config: E-Mail-Konfiguration
        """
        self.config = config
        self.logger = get_logger(__name__ + ".EmailNotifier")
    
    def send_email(self, subject: str, body: str, html_body: Optional[str] = None) -> bool:
        """
        Sendet eine E-Mail.
        
        Args:
            subject: Betreff der E-Mail
            body: Textkörper der E-Mail
            html_body: Optionaler HTML-Körper
            
        Returns:
            True, wenn die E-Mail gesendet wurde, False sonst
        """
        try:
            # Erstelle die Nachricht
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.config.sender_email
            msg["To"] = ", ".join(self.config.recipient_emails)
            
            # Füge den Textkörper hinzu
            text_part = MIMEText(body, "plain")
            msg.attach(text_part)
            
            # Füge den HTML-Körper hinzu, falls vorhanden
            if html_body:
                html_part = MIMEText(html_body, "html")
                msg.attach(html_part)
            
            # Verbinde mit dem SMTP-Server
            with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
                if self.config.use_tls:
                    server.starttls()
                server.login(self.config.username, self.config.password)
                server.send_message(msg)
            
            self.logger.info(f"E-Mail gesendet: {subject}")
            return True
        except Exception as e:
            self.logger.error(f"Fehler beim Senden der E-Mail: {e}")
            return False

class PushNotifier:
    """Verwaltung von Push-Benachrichtigungen."""
    
    def __init__(self, config: PushConfig):
        """
        Initialisiert den Push-Benachrichtigungsmanager.
        
        Args:
            config: Push-Konfiguration
        """
        self.config = config
        self.logger = get_logger(__name__ + ".PushNotifier")
    
    def send_push(self, title: str, message: str, data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Sendet eine Push-Benachrichtigung.
        
        Args:
            title: Titel der Benachrichtigung
            message: Nachrichtentext
            data: Optionale zusätzliche Daten
            
        Returns:
            True, wenn die Push-Benachrichtigung gesendet wurde, False sonst
        """
        try:
            # Erstelle die Payload
            payload = {
                "to": self.config.device_token,
                "title": title,
                "body": message,
                "data": data or {}
            }
            
            # Sende die Anfrage
            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                self.config.service_url,
                headers=headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                self.logger.info(f"Push-Benachrichtigung gesendet: {title}")
                return True
            else:
                self.logger.error(f"Fehler beim Senden der Push-Benachrichtigung: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.logger.error(f"Fehler beim Senden der Push-Benachrichtigung: {e}")
            return False

class WebhookNotifier:
    """Webhook-Benachrichtigungen."""
    
    def __init__(self, config: WebhookConfig):
        """
        Initialisiert den Webhook-Notifier.
        
        Args:
            config: Webhook-Konfiguration
        """
        self.config = config
        self.logger = get_logger(__name__ + ".WebhookNotifier")
    
    def _json_serializer(self, obj: Any) -> Any:
        """
        Hilfsfunktion zur Serialisierung von Objekten für JSON.
        
        Args:
            obj: Zu serialisierendes Objekt
            
        Returns:
            Serialisierbare Darstellung des Objekts
        """
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")
    
    def send_webhook(self, event: NotificationEvent) -> bool:
        """
        Sendet eine Webhook-Benachrichtigung.
        
        Args:
            event: Benachrichtigungsereignis
            
        Returns:
            True, wenn der Webhook gesendet wurde, False sonst
        """
        try:
            # Erstelle die Payload
            payload = asdict(event)
            
            # Wende das Template an, falls vorhanden
            if self.config.payload_template:
                # Dies ist eine vereinfachte Implementierung
                # In einer echten Implementierung würde man ein Template-System verwenden
                try:
                    # Verwende die benutzerdefinierte Serialisierung
                    formatted_payload = json.dumps(payload, default=self._json_serializer)
                    payload = json.loads(
                        self.config.payload_template.format(**payload)
                    )
                except Exception as e:
                    self.logger.warning(f"Fehler beim Anwenden des Payload-Templates: {e}")
            
            # Sende die Anfrage
            headers = self.config.headers or {}
            # Stelle sicher, dass das Content-Type korrekt gesetzt ist
            if 'Content-Type' not in headers:
                headers['Content-Type'] = 'application/json'
            
            response = requests.request(
                self.config.method,
                self.config.url,
                headers=headers,
                data=json.dumps(payload, default=self._json_serializer),  # Verwende benutzerdefinierte Serialisierung
                timeout=10
            )
            
            if response.status_code < 400:
                self.logger.info(f"Webhook gesendet: {event.title}")
                return True
            else:
                self.logger.error(f"Fehler beim Senden des Webhooks: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.logger.error(f"Fehler beim Senden des Webhooks: {e}")
            return False

class AdvancedNotifier:
    """Erweiterte Benachrichtigungsverwaltung."""
    
    def __init__(
        self,
        email_config: Optional[EmailConfig] = None,
        push_config: Optional[PushConfig] = None,
        webhook_config: Optional[WebhookConfig] = None
    ):
        """
        Initialisiert den erweiterten Benachrichtigungsmanager.
        
        Args:
            email_config: Optionale E-Mail-Konfiguration
            push_config: Optionale Push-Konfiguration
            webhook_config: Optionale Webhook-Konfiguration
        """
        self.email_notifier = EmailNotifier(email_config) if email_config else None
        self.push_notifier = PushNotifier(push_config) if push_config else None
        self.webhook_notifier = WebhookNotifier(webhook_config) if webhook_config else None
        self.system_notifier = get_simple_system_notifier()  # Verwende die eigene Implementierung
        self.logger = get_logger(__name__ + ".AdvancedNotifier")
    
    def send_notification(self, event: NotificationEvent) -> Dict[str, bool]:
        """
        Sendet eine Benachrichtigung über alle konfigurierten Kanäle.
        
        Args:
            event: Benachrichtigungsereignis
            
        Returns:
            Dictionary mit den Ergebnissen für jeden Kanal
        """
        results = {}
        
        # Sende Systembenachrichtigung
        system_notification = SystemNotification(
            title=event.title,
            message=event.message,
            timeout=5000
        )
        results["system"] = self.system_notifier.send_notification(system_notification)
        
        # Sende E-Mail, falls konfiguriert
        if self.email_notifier:
            email_body = f"{event.message}\n\nZeitstempel: {event.timestamp}\nTyp: {event.event_type}"
            if event.data:
                email_body += f"\nDaten: {json.dumps(event.data, indent=2)}"
            
            results["email"] = self.email_notifier.send_email(
                subject=event.title,
                body=email_body
            )
        
        # Sende Push-Benachrichtigung, falls konfiguriert
        if self.push_notifier:
            results["push"] = self.push_notifier.send_push(
                title=event.title,
                message=event.message,
                data=event.data
            )
        
        # Sende Webhook, falls konfiguriert
        if self.webhook_notifier:
            results["webhook"] = self.webhook_notifier.send_webhook(event)
        
        self.logger.info(f"Benachrichtigung gesendet: {event.title} - Ergebnisse: {results}")
        return results
    
    def send_download_completed(self, file_name: str, file_size: int, duration: float) -> Dict[str, bool]:
        """
        Sendet eine Benachrichtigung über einen abgeschlossenen Download.
        
        Args:
            file_name: Name der heruntergeladenen Datei
            file_size: Größe der Datei in Bytes
            duration: Dauer des Downloads in Sekunden
            
        Returns:
            Dictionary mit den Ergebnissen für jeden Kanal
        """
        # Formatierung der Dateigröße
        if file_size < 1024:
            size_str = f"{file_size} B"
        elif file_size < 1024 * 1024:
            size_str = f"{file_size / 1024:.2f} KB"
        elif file_size < 1024 * 1024 * 1024:
            size_str = f"{file_size / (1024 * 1024):.2f} MB"
        else:
            size_str = f"{file_size / (1024 * 1024 * 1024):.2f} GB"
        
        event = NotificationEvent(
            event_type="download_completed",
            title="Download abgeschlossen",
            message=f"{file_name} wurde erfolgreich heruntergeladen ({size_str} in {duration:.2f}s)",
            timestamp=datetime.now(),
            data={
                "file_name": file_name,
                "file_size": file_size,
                "duration": duration
            },
            priority="normal"
        )
        
        return self.send_notification(event)
    
    def send_download_failed(self, file_name: str, error_message: str) -> Dict[str, bool]:
        """
        Sendet eine Benachrichtigung über einen fehlgeschlagenen Download.
        
        Args:
            file_name: Name der Datei, deren Download fehlgeschlagen ist
            error_message: Fehlermeldung
            
        Returns:
            Dictionary mit den Ergebnissen für jeden Kanal
        """
        event = NotificationEvent(
            event_type="download_failed",
            title="Download fehlgeschlagen",
            message=f"Download von {file_name} ist fehlgeschlagen: {error_message}",
            timestamp=datetime.now(),
            data={
                "file_name": file_name,
                "error": error_message
            },
            priority="high"
        )
        
        return self.send_notification(event)
    
    def send_batch_completed(self, total_files: int, successful: int, failed: int) -> Dict[str, bool]:
        """
        Sendet eine Benachrichtigung über abgeschlossene Batch-Verarbeitung.
        
        Args:
            total_files: Gesamtanzahl der Dateien
            successful: Anzahl erfolgreicher Downloads
            failed: Anzahl fehlgeschlagener Downloads
            
        Returns:
            Dictionary mit den Ergebnissen für jeden Kanal
        """
        event = NotificationEvent(
            event_type="batch_completed",
            title="Batch-Verarbeitung abgeschlossen",
            message=f"Batch-Verarbeitung abgeschlossen: {successful}/{total_files} Dateien erfolgreich heruntergeladen, {failed} fehlgeschlagen",
            timestamp=datetime.now(),
            data={
                "total_files": total_files,
                "successful": successful,
                "failed": failed
            },
            priority="normal"
        )
        
        return self.send_notification(event)

# Globale Instanz
_advanced_notifier: Optional[AdvancedNotifier] = None

def get_advanced_notifier(
    email_config: Optional[EmailConfig] = None,
    push_config: Optional[PushConfig] = None,
    webhook_config: Optional[WebhookConfig] = None
) -> AdvancedNotifier:
    """
    Gibt die globale Instanz des erweiterten Benachrichtigungsmanagers zurück.
    
    Args:
        email_config: Optionale E-Mail-Konfiguration
        push_config: Optionale Push-Konfiguration
        webhook_config: Optionale Webhook-Konfiguration
        
    Returns:
        Instanz von AdvancedNotifier
    """
    global _advanced_notifier
    if _advanced_notifier is None:
        _advanced_notifier = AdvancedNotifier(email_config, push_config, webhook_config)
    return _advanced_notifier

# Hilfsfunktionen für die Verwendung außerhalb der Klassen
def send_download_completed_notification(file_name: str, file_size: int, duration: float) -> Dict[str, bool]:
    """
    Sendet eine Benachrichtigung über einen abgeschlossenen Download.
    
    Args:
        file_name: Name der heruntergeladenen Datei
        file_size: Größe der Datei in Bytes
        duration: Dauer des Downloads in Sekunden
        
    Returns:
        Dictionary mit den Ergebnissen für jeden Kanal
    """
    notifier = get_advanced_notifier()
    return notifier.send_download_completed(file_name, file_size, duration)

def send_download_failed_notification(file_name: str, error_message: str) -> Dict[str, bool]:
    """
    Sendet eine Benachrichtigung über einen fehlgeschlagenen Download.
    
    Args:
        file_name: Name der Datei, deren Download fehlgeschlagen ist
        error_message: Fehlermeldung
        
    Returns:
        Dictionary mit den Ergebnissen für jeden Kanal
    """
    notifier = get_advanced_notifier()
    return notifier.send_download_failed(file_name, error_message)

def send_batch_completed_notification(total_files: int, successful: int, failed: int) -> Dict[str, bool]:
    """
    Sendet eine Benachrichtigung über abgeschlossene Batch-Verarbeitung.
    
    Args:
        total_files: Gesamtanzahl der Dateien
        successful: Anzahl erfolgreicher Downloads
        failed: Anzahl fehlgeschlagener Downloads
        
    Returns:
        Dictionary mit den Ergebnissen für jeden Kanal
    """
    notifier = get_advanced_notifier()
    return notifier.send_batch_completed(total_files, successful, failed)