"""
Datenbank-Sicherheit für den Telegram Audio Downloader.

Umfasst:
- Verschlüsselung sensibler Daten
- Datenmaskierung
- Audit-Logging
- Zugriffskontrollen
"""

import hashlib
import hmac
import os
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from .models import db
from .logging_config import get_logger
from .audit_logging import log_audit_event

logger = get_logger(__name__)


class DatabaseSecurityManager:
    """Verwaltet die Datenbanksicherheit."""
    
    def __init__(self, encryption_key: Optional[bytes] = None):
        """
        Initialisiert den DatabaseSecurityManager.
        
        Args:
            encryption_key: Optionaler Verschlüsselungsschlüssel
        """
        self.encryption_key = encryption_key or self._generate_key()
        self.cipher_suite = Fernet(self.encryption_key)
        
        logger.info("DatabaseSecurityManager initialisiert")
    
    def _generate_key(self) -> bytes:
        """
        Generiert einen Verschlüsselungsschlüssel.
        
        Returns:
            Verschlüsselungsschlüssel
        """
        # In einer Produktionsumgebung sollte der Schlüssel sicher gespeichert werden
        # Für dieses Beispiel generieren wir einen neuen Schlüssel
        return Fernet.generate_key()
    
    def encrypt_data(self, data: str) -> str:
        """
        Verschlüsselt Daten.
        
        Args:
            data: Zu verschlüsselnde Daten
            
        Returns:
            Verschlüsselte Daten als String
        """
        try:
            encrypted_data = self.cipher_suite.encrypt(data.encode())
            return encrypted_data.decode()
        except Exception as e:
            logger.error(f"Fehler bei der Datenverschlüsselung: {e}")
            raise
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """
        Entschlüsselt Daten.
        
        Args:
            encrypted_data: Zu entschlüsselnde Daten
            
        Returns:
            Entschlüsselte Daten als String
        """
        try:
            decrypted_data = self.cipher_suite.decrypt(encrypted_data.encode())
            return decrypted_data.decode()
        except Exception as e:
            logger.error(f"Fehler bei der Datenentschlüsselung: {e}")
            raise
    
    def hash_password(self, password: str, salt: Optional[bytes] = None) -> tuple:
        """
        Hashed ein Passwort mit Salt.
        
        Args:
            password: Zu hashendes Passwort
            salt: Optionales Salt (wird generiert, wenn nicht angegeben)
            
        Returns:
            Tuple aus (hashed_password, salt)
        """
        if salt is None:
            salt = os.urandom(32)  # 32 Bytes = 256 Bits
        
        # Erstelle den PBKDF2-Hash
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        password_hash = kdf.derive(password.encode())
        
        return (password_hash.hex(), salt.hex())
    
    def verify_password(self, password: str, hashed_password: str, salt: str) -> bool:
        """
        Verifiziert ein Passwort gegen einen Hash.
        
        Args:
            password: Zu verifizierendes Passwort
            hashed_password: Gespeicherter Hash
            salt: Gespeichertes Salt
            
        Returns:
            True, wenn das Passwort korrekt ist
        """
        try:
            # Konvertiere Hex-Strings zurück in Bytes
            salt_bytes = bytes.fromhex(salt)
            hashed_password_bytes = bytes.fromhex(hashed_password)
            
            # Erstelle den KDF mit dem gleichen Salt
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt_bytes,
                iterations=100000,
            )
            
            # Verifiziere das Passwort
            kdf.verify(password.encode(), hashed_password_bytes)
            return True
        except Exception:
            return False
    
    def mask_sensitive_data(self, data: str, mask_char: str = "*") -> str:
        """
        Maskiert sensible Daten.
        
        Args:
            data: Zu maskierende Daten
            mask_char: Zeichen für die Maskierung
            
        Returns:
            Maskierte Daten
        """
        if len(data) <= 4:
            return mask_char * len(data)
        else:
            # Zeige die ersten 2 und letzten 2 Zeichen, maskiere den Rest
            return data[:2] + mask_char * (len(data) - 4) + data[-2:]
    
    def log_sensitive_operation(self, operation: str, user_id: Optional[int] = None,
                              details: Optional[Dict[str, Any]] = None) -> None:
        """
        Loggt eine sensible Operation.
        
        Args:
            operation: Name der Operation
            user_id: ID des Benutzers (optional)
            details: Zusätzliche Details (werden maskiert)
        """
        try:
            # Maskiere sensible Details
            masked_details = {}
            if details:
                for key, value in details.items():
                    if isinstance(value, str) and len(value) > 0:
                        # Maskiere möglicherweise sensible Felder
                        if any(sensitive in key.lower() for sensitive in 
                              ['password', 'token', 'key', 'secret', 'api']):
                            masked_details[key] = self.mask_sensitive_data(value)
                        else:
                            masked_details[key] = value
                    else:
                        masked_details[key] = value
            
            # Logge das Ereignis
            log_audit_event(
                event_type="sensitive_operation",
                description=f"Sensible Operation: {operation}",
                user_id=user_id,
                details=masked_details
            )
        except Exception as e:
            logger.error(f"Fehler beim Loggen der sensiblen Operation: {e}")
    
    def get_security_stats(self) -> Dict[str, Any]:
        """
        Gibt Sicherheitsstatistiken zurück.
        
        Returns:
            Dictionary mit Sicherheitsstatistiken
        """
        try:
            # Zähle verschlüsselte Datensätze
            encrypted_count = 0  # In einer echten Implementierung würden wir dies zählen
            
            # Zähle Audit-Logs
            audit_log_count = 0  # In einer echten Implementierung würden wir dies zählen
            
            return {
                "encrypted_records": encrypted_count,
                "audit_log_entries": audit_log_count,
                "key_age_days": 0,  # In einer echten Implementierung würden wir dies berechnen
                "last_security_check": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Sicherheitsstatistiken: {e}")
            return {}


class DataIntegrityChecker:
    """Prüft die Datenintegrität."""
    
    def __init__(self):
        """Initialisiert den DataIntegrityChecker."""
        logger.info("DataIntegrityChecker initialisiert")
    
    def calculate_checksum(self, data: str) -> str:
        """
        Berechnet eine Prüfsumme für Daten.
        
        Args:
            data: Daten für die Prüfsumme
            
        Returns:
            Prüfsumme als Hex-String
        """
        return hashlib.sha256(data.encode()).hexdigest()
    
    def verify_checksum(self, data: str, checksum: str) -> bool:
        """
        Verifiziert eine Prüfsumme.
        
        Args:
            data: Daten für die Prüfsumme
            checksum: Zu verifizierende Prüfsumme
            
        Returns:
            True, wenn die Prüfsumme korrekt ist
        """
        return self.calculate_checksum(data) == checksum
    
    def create_hmac(self, data: str, key: bytes) -> str:
        """
        Erstellt einen HMAC für Daten.
        
        Args:
            data: Daten für den HMAC
            key: Schlüssel für den HMAC
            
        Returns:
            HMAC als Hex-String
        """
        return hmac.new(key, data.encode(), hashlib.sha256).hexdigest()
    
    def verify_hmac(self, data: str, hmac_value: str, key: bytes) -> bool:
        """
        Verifiziert einen HMAC.
        
        Args:
            data: Daten für den HMAC
            hmac_value: Zu verifizierender HMAC
            key: Schlüssel für den HMAC
            
        Returns:
            True, wenn der HMAC korrekt ist
        """
        return hmac.compare_digest(self.create_hmac(data, key), hmac_value)
    
    def check_database_integrity(self) -> Dict[str, Any]:
        """
        Prüft die Integrität der Datenbank.
        
        Returns:
            Dictionary mit Integritätsprüfungen
        """
        try:
            integrity_issues = []
            
            # Prüfe auf doppelte file_ids in AudioFile
            try:
                cursor = db.execute_sql("""
                    SELECT file_id, COUNT(*) as count
                    FROM audio_files
                    GROUP BY file_id
                    HAVING COUNT(*) > 1;
                """)
                
                duplicates = cursor.fetchall()
                if duplicates:
                    integrity_issues.append({
                        "type": "duplicate_file_ids",
                        "count": len(duplicates),
                        "details": [row[0] for row in duplicates]
                    })
            except Exception as e:
                logger.error(f"Fehler bei der Prüfung auf doppelte file_ids: {e}")
            
            # Prüfe auf fehlende Gruppen-Referenzen
            try:
                cursor = db.execute_sql("""
                    SELECT id
                    FROM audio_files
                    WHERE group_id IS NOT NULL
                    AND group_id NOT IN (SELECT id FROM telegram_groups);
                """)
                
                orphaned_files = cursor.fetchall()
                if orphaned_files:
                    integrity_issues.append({
                        "type": "orphaned_files",
                        "count": len(orphaned_files),
                        "details": [row[0] for row in orphaned_files]
                    })
            except Exception as e:
                logger.error(f"Fehler bei der Prüfung auf verwaiste Dateien: {e}")
            
            return {
                "checked_at": datetime.now().isoformat(),
                "issues_found": len(integrity_issues),
                "issues": integrity_issues,
                "status": "ok" if not integrity_issues else "issues_found"
            }
            
        except Exception as e:
            logger.error(f"Fehler bei der Datenbank-Integritätsprüfung: {e}")
            return {
                "checked_at": datetime.now().isoformat(),
                "issues_found": 0,
                "issues": [],
                "status": "error",
                "error": str(e)
            }


# Globale Instanzen
_security_manager: Optional[DatabaseSecurityManager] = None
_integrity_checker: Optional[DataIntegrityChecker] = None


def get_security_manager() -> DatabaseSecurityManager:
    """
    Gibt die globale Instanz des DatabaseSecurityManager zurück.
    
    Returns:
        DatabaseSecurityManager-Instanz
    """
    global _security_manager
    if _security_manager is None:
        _security_manager = DatabaseSecurityManager()
    return _security_manager


def get_integrity_checker() -> DataIntegrityChecker:
    """
    Gibt die globale Instanz des DataIntegrityChecker zurück.
    
    Returns:
        DataIntegrityChecker-Instanz
    """
    global _integrity_checker
    if _integrity_checker is None:
        _integrity_checker = DataIntegrityChecker()
    return _integrity_checker


def encrypt_sensitive_data(data: str) -> str:
    """
    Verschlüsselt sensible Daten.
    
    Args:
        data: Zu verschlüsselnde Daten
        
    Returns:
        Verschlüsselte Daten als String
    """
    try:
        manager = get_security_manager()
        return manager.encrypt_data(data)
    except Exception as e:
        logger.error(f"Fehler bei der Datenverschlüsselung: {e}")
        raise


def decrypt_sensitive_data(encrypted_data: str) -> str:
    """
    Entschlüsselt sensible Daten.
    
    Args:
        encrypted_data: Zu entschlüsselnde Daten
        
    Returns:
        Entschlüsselte Daten als String
    """
    try:
        manager = get_security_manager()
        return manager.decrypt_data(encrypted_data)
    except Exception as e:
        logger.error(f"Fehler bei der Datenentschlüsselung: {e}")
        raise


def hash_user_password(password: str) -> tuple:
    """
    Hashed ein Benutzerpasswort.
    
    Args:
        password: Zu hashendes Passwort
        
    Returns:
        Tuple aus (hashed_password, salt)
    """
    try:
        manager = get_security_manager()
        return manager.hash_password(password)
    except Exception as e:
        logger.error(f"Fehler beim Hashen des Passworts: {e}")
        raise


def verify_user_password(password: str, hashed_password: str, salt: str) -> bool:
    """
    Verifiziert ein Benutzerpasswort.
    
    Args:
        password: Zu verifizierendes Passwort
        hashed_password: Gespeicherter Hash
        salt: Gespeichertes Salt
        
    Returns:
        True, wenn das Passwort korrekt ist
    """
    try:
        manager = get_security_manager()
        return manager.verify_password(password, hashed_password, salt)
    except Exception as e:
        logger.error(f"Fehler bei der Passwortverifizierung: {e}")
        return False


def check_data_integrity() -> Dict[str, Any]:
    """
    Prüft die Datenintegrität der Datenbank.
    
    Returns:
        Dictionary mit Integritätsprüfungen
    """
    try:
        checker = get_integrity_checker()
        return checker.check_database_integrity()
    except Exception as e:
        logger.error(f"Fehler bei der Datenintegritätsprüfung: {e}")
        return {
            "checked_at": datetime.now().isoformat(),
            "issues_found": 0,
            "issues": [],
            "status": "error",
            "error": str(e)
        }