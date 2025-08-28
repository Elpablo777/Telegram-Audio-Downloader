"""
Erweiterte Sicherheitsfunktionen für den Telegram Audio Downloader.
"""

import hashlib
import logging
import os
import stat
import tempfile
from pathlib import Path
from typing import Optional, Set, Dict, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import json

from .error_handling import handle_error, SecurityError, FileOperationError

logger = logging.getLogger(__name__)

@dataclass
class SecurityEvent:
    """Ein Sicherheitsereignis."""
    timestamp: datetime
    event_type: str
    description: str
    severity: str
    user: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class FileAccessControl:
    """Zugriffskontrolle für Dateien."""
    
    def __init__(self, allowed_users: Optional[Set[str]] = None):
        """
        Initialisiert die Zugriffskontrolle.
        
        Args:
            allowed_users: Liste der erlaubten Benutzer (None für alle erlaubt)
        """
        self.allowed_users = allowed_users or set()
        self.security_events: list[SecurityEvent] = []
    
    def check_file_access(self, file_path: Path, user: Optional[str] = None) -> bool:
        """
        Prüft, ob der Zugriff auf eine Datei erlaubt ist.
        
        Args:
            file_path: Pfad zur Datei
            user: Benutzer, der auf die Datei zugreifen möchte
            
        Returns:
            True, wenn der Zugriff erlaubt ist, False sonst
        """
        # Wenn keine Benutzerbeschränkung besteht, ist der Zugriff erlaubt
        if not self.allowed_users:
            return True
            
        # Wenn kein Benutzer angegeben ist, ist der Zugriff nicht erlaubt
        if not user:
            self._log_security_event("unauthorized_access", f"Zugriff auf {file_path} ohne Benutzerangabe verweigert", "high")
            return False
            
        # Prüfe, ob der Benutzer erlaubt ist
        if user in self.allowed_users:
            return True
        else:
            self._log_security_event("unauthorized_access", f"Zugriff auf {file_path} für Benutzer {user} verweigert", "medium")
            return False
    
    def add_allowed_user(self, user: str) -> None:
        """
        Fügt einen Benutzer zur Liste der erlaubten Benutzer hinzu.
        
        Args:
            user: Benutzername
        """
        self.allowed_users.add(user)
        self._log_security_event("user_added", f"Benutzer {user} zur Zugriffsliste hinzugefügt", "low")
    
    def remove_allowed_user(self, user: str) -> None:
        """
        Entfernt einen Benutzer von der Liste der erlaubten Benutzer.
        
        Args:
            user: Benutzername
        """
        self.allowed_users.discard(user)
        self._log_security_event("user_removed", f"Benutzer {user} von der Zugriffsliste entfernt", "low")
    
    def _log_security_event(self, event_type: str, description: str, severity: str, user: Optional[str] = None, details: Optional[Dict[str, Any]] = None) -> None:
        """
        Protokolliert ein Sicherheitsereignis.
        
        Args:
            event_type: Typ des Ereignisses
            description: Beschreibung des Ereignisses
            severity: Schweregrad (low, medium, high)
            user: Benutzer, der das Ereignis ausgelöst hat
            details: Zusätzliche Details
        """
        event = SecurityEvent(
            timestamp=datetime.now(),
            event_type=event_type,
            description=description,
            severity=severity,
            user=user,
            details=details
        )
        self.security_events.append(event)
        logger.info(f"Sicherheitsereignis: {description}")

class FileIntegrityChecker:
    """Prüfung der Dateiintegrität."""
    
    def __init__(self, hash_algorithm: str = "sha256"):
        """
        Initialisiert den Dateiintegritätsprüfer.
        
        Args:
            hash_algorithm: Zu verwendender Hash-Algorithmus
        """
        self.hash_algorithm = hash_algorithm
        self.known_hashes: Dict[str, str] = {}
    
    def calculate_file_hash(self, file_path: Path) -> str:
        """
        Berechnet den Hash einer Datei.
        
        Args:
            file_path: Pfad zur Datei
            
        Returns:
            Hash der Datei
        """
        hash_func = hashlib.new(self.hash_algorithm)
        
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_func.update(chunk)
            return hash_func.hexdigest()
        except Exception as e:
            raise FileOperationError(f"Fehler beim Berechnen des Hash für {file_path}: {e}")
    
    def verify_file_integrity(self, file_path: Path, expected_hash: Optional[str] = None) -> bool:
        """
        Verifiziert die Integrität einer Datei.
        
        Args:
            file_path: Pfad zur Datei
            expected_hash: Erwarteter Hash (optional)
            
        Returns:
            True, wenn die Integrität bestätigt ist, False sonst
        """
        try:
            if not file_path.exists():
                logger.warning(f"Datei {file_path} existiert nicht für Integritätsprüfung")
                return False
                
            file_hash = self.calculate_file_hash(file_path)
            
            # Wenn ein erwarteter Hash angegeben ist, prüfe ihn
            if expected_hash:
                if file_hash == expected_hash:
                    logger.debug(f"Dateiintegrität von {file_path} bestätigt")
                    return True
                else:
                    logger.warning(f"Dateiintegrität von {file_path} verletzt")
                    return False
            
            # Wenn kein erwarteter Hash angegeben ist, prüfe gegen bekannte Hashes
            file_key = str(file_path)
            if file_key in self.known_hashes:
                if file_hash == self.known_hashes[file_key]:
                    logger.debug(f"Dateiintegrität von {file_path} bestätigt")
                    return True
                else:
                    logger.warning(f"Dateiintegrität von {file_path} verletzt")
                    return False
            else:
                # Speichere den Hash als bekannt
                self.known_hashes[file_key] = file_hash
                logger.debug(f"Neue Datei {file_path} zur Integritätsprüfung hinzugefügt")
                return True
                
        except Exception as e:
            logger.error(f"Fehler bei der Integritätsprüfung von {file_path}: {e}")
            return False
    
    def add_known_file(self, file_path: Path) -> None:
        """
        Fügt eine Datei als bekannt hinzu.
        
        Args:
            file_path: Pfad zur Datei
        """
        try:
            if file_path.exists():
                file_hash = self.calculate_file_hash(file_path)
                self.known_hashes[str(file_path)] = file_hash
                logger.debug(f"Datei {file_path} zur Liste bekannter Dateien hinzugefügt")
        except Exception as e:
            logger.error(f"Fehler beim Hinzufügen von {file_path} zur Liste bekannter Dateien: {e}")

class SandboxingManager:
    """Verwaltung von Sandboxing für sichere Dateioperationen."""
    
    def __init__(self, sandbox_dir: Optional[Path] = None):
        """
        Initialisiert den Sandboxing-Manager.
        
        Args:
            sandbox_dir: Verzeichnis für Sandbox-Operationen (temporär, wenn nicht angegeben)
        """
        if sandbox_dir is None:
            # Erstelle ein temporäres Verzeichnis für die Sandbox
            self.sandbox_dir = Path(tempfile.mkdtemp(prefix="telegram_downloader_sandbox_"))
            self._cleanup_on_exit = True
        else:
            self.sandbox_dir = sandbox_dir
            self.sandbox_dir.mkdir(parents=True, exist_ok=True)
            self._cleanup_on_exit = False
        
        # Setze sichere Berechtigungen für das Sandbox-Verzeichnis
        try:
            os.chmod(self.sandbox_dir, stat.S_IRWXU)  # Nur für den Besitzer lesbar/schreibbar/ausführbar
        except Exception as e:
            logger.warning(f"Fehler beim Setzen sicherer Berechtigungen für Sandbox-Verzeichnis: {e}")
    
    def __enter__(self):
        """Kontextmanager-Eintritt."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Kontextmanager-Austritt."""
        if self._cleanup_on_exit:
            self._cleanup()
    
    def _cleanup(self) -> None:
        """Räumt die Sandbox auf."""
        try:
            import shutil
            if self.sandbox_dir.exists():
                shutil.rmtree(self.sandbox_dir)
                logger.debug(f"Sandbox-Verzeichnis {self.sandbox_dir} aufgeräumt")
        except Exception as e:
            logger.warning(f"Fehler beim Aufräumen der Sandbox: {e}")
    
    def secure_file_operation(self, operation_func, *args, **kwargs) -> Any:
        """
        Führt eine Dateioperation sicher in der Sandbox aus.
        
        Args:
            operation_func: Funktion zur Ausführung
            *args: Positionelle Argumente
            **kwargs: Schlüsselwortargumente
            
        Returns:
            Ergebnis der Operation
        """
        try:
            # Führe die Operation in der Sandbox aus
            result = operation_func(*args, **kwargs)
            return result
        except Exception as e:
            logger.error(f"Fehler bei sicherer Dateioperation: {e}")
            raise SecurityError(f"Sichere Dateioperation fehlgeschlagen: {e}")

class AuditLogger:
    """Audit-Logging für Sicherheitsereignisse."""
    
    def __init__(self, log_file: Optional[Path] = None):
        """
        Initialisiert den Audit-Logger.
        
        Args:
            log_file: Datei für Audit-Logs (standardmäßig audit.log im data-Verzeichnis)
        """
        if log_file is None:
            log_file = Path("data") / "audit.log"
        
        self.log_file = log_file
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Erstelle die Log-Datei, falls sie nicht existiert
        self.log_file.touch(exist_ok=True)
    
    def log_event(self, event: SecurityEvent) -> None:
        """
        Protokolliert ein Sicherheitsereignis im Audit-Log.
        
        Args:
            event: Sicherheitsereignis
        """
        try:
            # Konvertiere das Ereignis in ein Dictionary
            event_dict = asdict(event)
            # Konvertiere den Zeitstempel in einen String
            event_dict['timestamp'] = event_dict['timestamp'].isoformat()
            
            # Schreibe das Ereignis in die Log-Datei
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(event_dict, ensure_ascii=False) + "\n")
                
        except Exception as e:
            logger.error(f"Fehler beim Schreiben des Audit-Logs: {e}")

# Globale Instanzen
_file_access_control: Optional[FileAccessControl] = None
_file_integrity_checker: Optional[FileIntegrityChecker] = None
_audit_logger: Optional[AuditLogger] = None

def get_file_access_control(allowed_users: Optional[Set[str]] = None) -> FileAccessControl:
    """
    Gibt die globale Instanz der Zugriffskontrolle zurück.
    
    Args:
        allowed_users: Liste der erlaubten Benutzer
        
    Returns:
        Instanz von FileAccessControl
    """
    global _file_access_control
    if _file_access_control is None:
        _file_access_control = FileAccessControl(allowed_users)
    return _file_access_control

def get_file_integrity_checker(hash_algorithm: str = "sha256") -> FileIntegrityChecker:
    """
    Gibt die globale Instanz des Dateiintegritätsprüfers zurück.
    
    Args:
        hash_algorithm: Zu verwendender Hash-Algorithmus
        
    Returns:
        Instanz von FileIntegrityChecker
    """
    global _file_integrity_checker
    if _file_integrity_checker is None:
        _file_integrity_checker = FileIntegrityChecker(hash_algorithm)
    return _file_integrity_checker

def get_audit_logger(log_file: Optional[Path] = None) -> AuditLogger:
    """
    Gibt die globale Instanz des Audit-Loggers zurück.
    
    Args:
        log_file: Datei für Audit-Logs
        
    Returns:
        Instanz von AuditLogger
    """
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger(log_file)
    return _audit_logger

# Hilfsfunktionen für die Verwendung außerhalb der Klassen
def check_file_access(file_path: Path, user: Optional[str] = None) -> bool:
    """
    Prüft, ob der Zugriff auf eine Datei erlaubt ist.
    
    Args:
        file_path: Pfad zur Datei
        user: Benutzer, der auf die Datei zugreifen möchte
        
    Returns:
        True, wenn der Zugriff erlaubt ist, False sonst
    """
    access_control = get_file_access_control()
    return access_control.check_file_access(file_path, user)

def verify_file_integrity(file_path: Path, expected_hash: Optional[str] = None) -> bool:
    """
    Verifiziert die Integrität einer Datei.
    
    Args:
        file_path: Pfad zur Datei
        expected_hash: Erwarteter Hash (optional)
        
    Returns:
        True, wenn die Integrität bestätigt ist, False sonst
    """
    integrity_checker = get_file_integrity_checker()
    return integrity_checker.verify_file_integrity(file_path, expected_hash)

def secure_file_operation(operation_func, *args, **kwargs) -> Any:
    """
    Führt eine Dateioperation sicher in einer Sandbox aus.
    
    Args:
        operation_func: Funktion zur Ausführung
        *args: Positionelle Argumente
        **kwargs: Schlüsselwortargumente
        
    Returns:
        Ergebnis der Operation
    """
    with SandboxingManager() as sandbox:
        return sandbox.secure_file_operation(operation_func, *args, **kwargs)

def log_security_event(event_type: str, description: str, severity: str, user: Optional[str] = None, details: Optional[Dict[str, Any]] = None) -> None:
    """
    Protokolliert ein Sicherheitsereignis.
    
    Args:
        event_type: Typ des Ereignisses
        description: Beschreibung des Ereignisses
        severity: Schweregrad (low, medium, high)
        user: Benutzer, der das Ereignis ausgelöst hat
        details: Zusätzliche Details
    """
    access_control = get_file_access_control()
    access_control._log_security_event(event_type, description, severity, user, details)
    
    # Protokolliere auch im Audit-Log
    event = SecurityEvent(
        timestamp=datetime.now(),
        event_type=event_type,
        description=description,
        severity=severity,
        user=user,
        details=details
    )
    audit_logger = get_audit_logger()
    audit_logger.log_event(event)