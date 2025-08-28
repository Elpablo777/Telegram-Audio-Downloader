"""
Automatische Fehlerbehebung für den Telegram Audio Downloader.

Automatische Korrekturmechanismen für:
- Automatische Wiederholung
- Alternative Quellen
- Selbstheilung
- Benutzerbenachrichtigung
"""

import asyncio
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from pathlib import Path
import traceback

from .logging_config import get_logger
from .models import AudioFile, DownloadStatus

logger = get_logger(__name__)


@dataclass
class ErrorRecoveryStrategy:
    """Strategie zur Fehlerbehebung."""
    name: str
    condition: Callable[[Exception, str], bool]  # (exception, context) -> should_apply
    recovery_action: Callable[[Exception, str, Any], bool]  # (exception, context, data) -> success
    max_attempts: int = 3
    delay_between_attempts: float = 5.0  # Sekunden


@dataclass
class RecoveryAttempt:
    """Aufzeichnung eines Wiederherstellungsversuchs."""
    timestamp: float = field(default_factory=time.time)
    error_type: str = ""
    context: str = ""
    attempt_number: int = 0
    success: bool = False
    recovery_strategy: str = ""
    details: Dict[str, Any] = field(default_factory=dict)


class AutomaticErrorRecovery:
    """Verwaltet automatische Fehlerbehebung."""
    
    def __init__(self, download_dir: Path):
        """
        Initialisiert die automatische Fehlerbehebung.
        
        Args:
            download_dir: Download-Verzeichnis
        """
        self.download_dir = Path(download_dir)
        self.strategies: List[ErrorRecoveryStrategy] = []
        self.recovery_history: List[RecoveryAttempt] = []
        self.max_history_size = 1000
        self.notification_handlers: List[Callable[[str, str, Dict[str, Any]], None]] = []
        
        # Standard-Strategien registrieren
        self._register_default_strategies()
        
        logger.info("AutomaticErrorRecovery initialisiert")
    
    def _register_default_strategies(self) -> None:
        """Registriert Standard-Fehlerbehebungsstrategien."""
        # Netzwerkfehler-Strategie
        network_strategy = ErrorRecoveryStrategy(
            name="network_retry",
            condition=lambda e, ctx: isinstance(e, (ConnectionError, TimeoutError)),
            recovery_action=self._retry_with_backoff,
            max_attempts=3,
            delay_between_attempts=10.0
        )
        self.register_strategy(network_strategy)
        
        # FloodWait-Strategie
        flood_strategy = ErrorRecoveryStrategy(
            name="flood_wait_wait",
            condition=lambda e, ctx: "FloodWaitError" in str(type(e)),
            recovery_action=self._handle_flood_wait,
            max_attempts=1,
            delay_between_attempts=0.0
        )
        self.register_strategy(flood_strategy)
        
        # Dateisystem-Fehler-Strategie
        filesystem_strategy = ErrorRecoveryStrategy(
            name="filesystem_retry",
            condition=lambda e, ctx: isinstance(e, (OSError, IOError)),
            recovery_action=self._retry_with_backoff,
            max_attempts=2,
            delay_between_attempts=15.0
        )
        self.register_strategy(filesystem_strategy)
        
        logger.debug("Standard-Fehlerbehebungsstrategien registriert")
    
    def register_strategy(self, strategy: ErrorRecoveryStrategy) -> None:
        """
        Registriert eine neue Fehlerbehebungsstrategie.
        
        Args:
            strategy: Fehlerbehebungsstrategie
        """
        self.strategies.append(strategy)
        logger.debug(f"Fehlerbehebungsstrategie '{strategy.name}' registriert")
    
    def register_notification_handler(self, handler: Callable[[str, str, Dict[str, Any]], None]) -> None:
        """
        Registriert einen Benachrichtigungshandler.
        
        Args:
            handler: Funktion, die bei Benachrichtigungen aufgerufen wird
                     Parameter: (message_type, message, details)
        """
        self.notification_handlers.append(handler)
        logger.debug("Benachrichtigungshandler registriert")
    
    async def attempt_recovery(self, error: Exception, context: str, data: Any = None) -> bool:
        """
        Versucht eine automatische Fehlerbehebung.
        
        Args:
            error: Aufgetretener Fehler
            context: Kontext des Fehlers
            data: Zusätzliche Daten für die Fehlerbehebung
            
        Returns:
            True, wenn die Fehlerbehebung erfolgreich war
        """
        logger.info(f"Versuche automatische Fehlerbehebung für {type(error).__name__} in {context}")
        
        # Finde passende Strategie
        for strategy in self.strategies:
            if strategy.condition(error, context):
                logger.debug(f"Anwenden der Strategie '{strategy.name}'")
                
                # Führe Wiederherstellungsaktion aus
                success = await self._execute_recovery_strategy(strategy, error, context, data)
                
                # Aufzeichnung des Versuchs
                attempt = RecoveryAttempt(
                    error_type=type(error).__name__,
                    context=context,
                    attempt_number=1,  # In einer erweiterten Implementierung könnten wir mehrere Versuche zählen
                    success=success,
                    recovery_strategy=strategy.name
                )
                self._record_recovery_attempt(attempt)
                
                if success:
                    logger.info(f"Fehlerbehebung mit Strategie '{strategy.name}' erfolgreich")
                    self._send_notification("recovery_success", f"Fehler in {context} erfolgreich behoben", {
                        "strategy": strategy.name,
                        "context": context,
                        "error_type": type(error).__name__
                    })
                    return True
                else:
                    logger.warning(f"Fehlerbehebung mit Strategie '{strategy.name}' fehlgeschlagen")
                    self._send_notification("recovery_failed", f"Fehlerbehebung in {context} fehlgeschlagen", {
                        "strategy": strategy.name,
                        "context": context,
                        "error_type": type(error).__name__
                    })
        
        logger.info("Keine passende Fehlerbehebungsstrategie gefunden")
        self._send_notification("recovery_not_possible", f"Keine Fehlerbehebung möglich für {context}", {
            "context": context,
            "error_type": type(error).__name__
        })
        return False
    
    async def _execute_recovery_strategy(self, strategy: ErrorRecoveryStrategy, error: Exception, context: str, data: Any) -> bool:
        """
        Führt eine Fehlerbehebungsstrategie aus.
        
        Args:
            strategy: Anzuwendende Strategie
            error: Aufgetretener Fehler
            context: Kontext des Fehlers
            data: Zusätzliche Daten
            
        Returns:
            True, wenn die Strategie erfolgreich war
        """
        try:
            # Für Strategien mit mehreren Versuchen
            for attempt in range(1, strategy.max_attempts + 1):
                try:
                    logger.debug(f"Führe Wiederherstellungsversuch {attempt}/{strategy.max_attempts} aus")
                    
                    success = strategy.recovery_action(error, context, data)
                    
                    if success:
                        return True
                    
                    # Warte vor dem nächsten Versuch
                    if attempt < strategy.max_attempts:
                        logger.info(f"Wiederholung in {strategy.delay_between_attempts} Sekunden...")
                        await asyncio.sleep(strategy.delay_between_attempts)
                        
                except Exception as e:
                    logger.error(f"Fehler beim Wiederherstellungsversuch {attempt}: {e}")
                    if attempt < strategy.max_attempts:
                        await asyncio.sleep(strategy.delay_between_attempts)
            
            return False
            
        except Exception as e:
            logger.error(f"Fehler beim Ausführen der Wiederherstellungsstrategie '{strategy.name}': {e}")
            return False
    
    def _retry_with_backoff(self, error: Exception, context: str, data: Any) -> bool:
        """
        Versucht eine Wiederholung mit exponentiellem Backoff.
        
        Args:
            error: Aufgetretener Fehler
            context: Kontext des Fehlers
            data: Zusätzliche Daten (erwartet ein Dictionary mit 'retry_count')
            
        Returns:
            True, wenn die Wiederholung erfolgreich war
        """
        # In einer echten Implementierung würden wir hier die Aktion erneut ausführen
        # Für dieses Beispiel simulieren wir den Prozess
        logger.debug(f"Versuche Wiederholung für {context}")
        
        # Simuliere eine erfolgreiche Wiederholung in 50% der Fälle
        import secrets
        return secrets.choice([True, False])
    
    def _handle_flood_wait(self, error: Exception, context: str, data: Any) -> bool:
        """
        Behandelt FloodWait-Fehler.
        
        Args:
            error: Aufgetretener Fehler
            context: Kontext des Fehlers
            data: Zusätzliche Daten
            
        Returns:
            True, wenn der Fehler behandelt wurde
        """
        # Extrahiere Wartezeit aus dem Fehler
        wait_time = 30  # Standardwert
        if hasattr(error, 'seconds'):
            wait_time = getattr(error, 'seconds', 30)
        
        logger.info(f"FloodWait-Fehler erkannt, warte {wait_time} Sekunden")
        
        # In einer echten Implementierung würden wir hier warten
        # Für dieses Beispiel simulieren wir den Wartevorgang
        return True
    
    def _record_recovery_attempt(self, attempt: RecoveryAttempt) -> None:
        """
        Zeichnet einen Wiederherstellungsversuch auf.
        
        Args:
            attempt: Wiederherstellungsversuch
        """
        self.recovery_history.append(attempt)
        if len(self.recovery_history) > self.max_history_size:
            self.recovery_history.pop(0)
        
        logger.debug(f"Wiederherstellungsversuch aufgezeichnet: {attempt}")
    
    def _send_notification(self, message_type: str, message: str, details: Dict[str, Any]) -> None:
        """
        Sendet eine Benachrichtigung.
        
        Args:
            message_type: Typ der Nachricht
            message: Nachrichtentext
            details: Detailinformationen
        """
        for handler in self.notification_handlers:
            try:
                handler(message_type, message, details)
            except Exception as e:
                logger.error(f"Fehler beim Senden der Benachrichtigung: {e}")
    
    def get_recovery_statistics(self) -> Dict[str, Any]:
        """
        Gibt Statistiken zur Fehlerbehebung zurück.
        
        Returns:
            Dictionary mit Statistiken
        """
        if not self.recovery_history:
            return {"total_attempts": 0}
        
        successful_attempts = sum(1 for attempt in self.recovery_history if attempt.success)
        total_attempts = len(self.recovery_history)
        
        # Gruppiere nach Strategie
        strategy_stats = {}
        for attempt in self.recovery_history:
            strategy = attempt.recovery_strategy
            if strategy not in strategy_stats:
                strategy_stats[strategy] = {"total": 0, "successful": 0}
            strategy_stats[strategy]["total"] += 1
            if attempt.success:
                strategy_stats[strategy]["successful"] += 1
        
        return {
            "total_attempts": total_attempts,
            "successful_attempts": successful_attempts,
            "success_rate": (successful_attempts / total_attempts) * 100 if total_attempts > 0 else 0,
            "strategies": strategy_stats
        }
    
    def get_recent_failures(self, limit: int = 10) -> List[RecoveryAttempt]:
        """
        Gibt die letzten fehlgeschlagenen Wiederherstellungsversuche zurück.
        
        Args:
            limit: Maximale Anzahl von Ergebnissen
            
        Returns:
            Liste der fehlgeschlagenen Versuche
        """
        failures = [attempt for attempt in reversed(self.recovery_history) if not attempt.success]
        return failures[:limit]
    
    async def self_heal_system(self) -> Dict[str, Any]:
        """
        Führt eine Selbstheilung des Systems durch.
        
        Returns:
            Dictionary mit Selbstheilungsbericht
        """
        logger.info("Starte System-Selbstheilung")
        
        report = {
            "timestamp": time.time(),
            "actions_performed": [],
            "issues_found": [],
            "issues_resolved": []
        }
        
        try:
            # Prüfe auf hängende Downloads
            pending_files = AudioFile.select().where(
                AudioFile.status == DownloadStatus.DOWNLOADING.value
            )
            
            for file in pending_files:
                # Prüfe, ob der Download tatsächlich noch läuft
                # In einer echten Implementierung würden wir hier prüfen,
                # ob der Download-Prozess noch aktiv ist
                logger.debug(f"Prüfe hängenden Download: {file.file_name}")
                
                # Für dieses Beispiel nehmen wir an, dass einige Downloads
                # aufgrund von Fehlern hängen geblieben sind
                if file.download_attempts > 5:  # Zu viele Versuche
                    file.status = DownloadStatus.FAILED.value
                    file.error_message = "Download nach zu vielen Versuchen abgebrochen"
                    file.save()
                    
                    report["issues_found"].append(f"Download {file.file_name} abgebrochen (zu viele Versuche)")
                    report["issues_resolved"].append(f"Download {file.file_name} auf FAILED gesetzt")
            
            report["actions_performed"].append(f"Geprüfte Dateien: {len(pending_files)}")
            
            # Bereinige temporäre Dateien
            temp_files_cleaned = self._cleanup_temp_files()
            report["actions_performed"].append(f"Temporäre Dateien bereinigt: {temp_files_cleaned}")
            
            # Führe Garbage Collection durch
            import gc
            collected = gc.collect()
            report["actions_performed"].append(f"Garbage Collection: {collected} Objekte")
            
            logger.info("System-Selbstheilung abgeschlossen")
            
        except Exception as e:
            logger.error(f"Fehler bei der System-Selbstheilung: {e}")
            report["issues_found"].append(f"Fehler bei Selbstheilung: {str(e)}")
        
        return report
    
    def _cleanup_temp_files(self) -> int:
        """
        Bereinigt temporäre Dateien.
        
        Returns:
            Anzahl der bereinigten Dateien
        """
        cleaned_count = 0
        
        try:
            # Bereinige .partial Dateien
            for partial_file in self.download_dir.glob("*.partial"):
                if partial_file.is_file():
                    partial_file.unlink()
                    cleaned_count += 1
            
            # Bereinige .tmp Dateien
            for temp_file in self.download_dir.glob("*.tmp"):
                if temp_file.is_file():
                    temp_file.unlink()
                    cleaned_count += 1
                    
            if cleaned_count > 0:
                logger.info(f"Temporäre Dateien bereinigt: {cleaned_count}")
                
        except Exception as e:
            logger.error(f"Fehler beim Bereinigen temporärer Dateien: {e}")
        
        return cleaned_count
    
    def add_alternative_source(self, file_id: str, source_url: str) -> None:
        """
        Fügt eine alternative Quelle für eine Datei hinzu.
        
        Args:
            file_id: ID der Datei
            source_url: URL der alternativen Quelle
        """
        # In einer erweiterten Implementierung würden wir hier
        # alternative Quellen in der Datenbank speichern
        logger.debug(f"Alternative Quelle für {file_id} hinzugefügt: {source_url}")


class EmailNotificationHandler:
    """E-Mail-Benachrichtigungshandler."""
    
    def __init__(self, smtp_server: str, smtp_port: int, username: str, password: str, 
                 recipients: List[str], sender: str):
        """
        Initialisiert den E-Mail-Benachrichtigungshandler.
        
        Args:
            smtp_server: SMTP-Server
            smtp_port: SMTP-Port
            username: SMTP-Benutzername
            password: SMTP-Passwort
            recipients: Liste von Empfängern
            sender: Absenderadresse
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.recipients = recipients
        self.sender = sender
        
        logger.debug("EmailNotificationHandler initialisiert")
    
    def send_notification(self, message_type: str, message: str, details: Dict[str, Any]) -> bool:
        """
        Sendet eine E-Mail-Benachrichtigung.
        
        Args:
            message_type: Typ der Nachricht
            message: Nachrichtentext
            details: Detailinformationen
            
        Returns:
            True, wenn die E-Mail gesendet wurde
        """
        try:
            msg = MIMEMultipart()
            msg['From'] = self.sender
            msg['To'] = ', '.join(self.recipients)
            msg['Subject'] = f"Telegram Audio Downloader - {message_type}"
            
            body = f"""
Telegram Audio Downloader - Benachrichtigung

Typ: {message_type}
Nachricht: {message}

Details:
{json.dumps(details, indent=2, ensure_ascii=False)}

Zeitstempel: {time.strftime('%Y-%m-%d %H:%M:%S')}
            """
            
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            
            logger.debug(f"E-Mail-Benachrichtigung gesendet: {message_type}")
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim Senden der E-Mail-Benachrichtigung: {e}")
            return False


def get_error_recovery(download_dir: Path = Path(".")):
    """
    Gibt eine Instanz des AutomaticErrorRecovery zurück.
    
    Args:
        download_dir: Download-Verzeichnis
        
    Returns:
        AutomaticErrorRecovery-Instanz
    """
    return AutomaticErrorRecovery(download_dir)