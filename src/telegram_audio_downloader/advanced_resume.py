"""
Fortschrittliche Download-Wiederaufnahme für den Telegram Audio Downloader.

Robuste Wiederaufnahme mit:
- Prüfsummenprüfung
- Teilweiser Download
- Automatische Wiederholung
- Protokollierung
"""

import hashlib
import os
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime

from .models import AudioFile
from .logging_config import get_logger
from .enhanced_error_handling import handle_error

logger = get_logger(__name__)


@dataclass
class ResumeInfo:
    """Informationen für die Download-Wiederaufnahme."""
    file_id: str
    file_path: Path
    downloaded_bytes: int = 0
    total_bytes: int = 0
    checksum: Optional[str] = None
    last_modified: datetime = field(default_factory=datetime.now)
    retry_count: int = 0
    max_retries: int = 3


class AdvancedResumeManager:
    """Verwaltet die fortgeschrittene Download-Wiederaufnahme."""
    
    def __init__(self, download_dir: Path):
        """
        Initialisiert den AdvancedResumeManager.
        
        Args:
            download_dir: Download-Verzeichnis
        """
        self.download_dir = Path(download_dir)
        self.resume_data: Dict[str, ResumeInfo] = {}
        self.checksum_algorithm = "sha256"
        
        logger.info(f"AdvancedResumeManager initialisiert mit Download-Verzeichnis {self.download_dir}")
    
    def calculate_checksum(self, file_path: Path) -> Optional[str]:
        """
        Berechnet die Prüfsumme einer Datei.
        
        Args:
            file_path: Pfad zur Datei
            
        Returns:
            Prüfsumme der Datei oder None bei Fehler
        """
        try:
            if not file_path.exists():
                return None
            
            hash_obj = hashlib.new(self.checksum_algorithm)
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    hash_obj.update(chunk)
            
            checksum = hash_obj.hexdigest()
            logger.debug(f"Prüfsumme für {file_path} berechnet: {checksum}")
            return checksum
            
        except Exception as e:
            logger.error(f"Fehler bei der Prüfsummenberechnung für {file_path}: {e}")
            return None
    
    def verify_checksum(self, file_path: Path, expected_checksum: str) -> bool:
        """
        Verifiziert die Prüfsumme einer Datei.
        
        Args:
            file_path: Pfad zur Datei
            expected_checksum: Erwartete Prüfsumme
            
        Returns:
            True, wenn die Prüfsumme übereinstimmt
        """
        try:
            actual_checksum = self.calculate_checksum(file_path)
            if actual_checksum is None:
                return False
            
            is_valid = actual_checksum == expected_checksum
            if not is_valid:
                logger.warning(f"Prüfsummenfehler für {file_path}: "
                             f"erwartet {expected_checksum}, erhalten {actual_checksum}")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Fehler bei der Prüfsummenverifikation für {file_path}: {e}")
            return False
    
    def get_resume_info(self, file_id: str, file_path: Path, total_bytes: int) -> ResumeInfo:
        """
        Holt oder erstellt Resume-Informationen für eine Datei.
        
        Args:
            file_id: Telegram-Datei-ID
            file_path: Pfad zur Datei
            total_bytes: Gesamtgröße der Datei
            
        Returns:
            ResumeInfo-Objekt
        """
        if file_id in self.resume_data:
            resume_info = self.resume_data[file_id]
            # Aktualisiere die Dateigröße, falls sie sich geändert hat
            resume_info.total_bytes = total_bytes
            resume_info.last_modified = datetime.now()
            return resume_info
        
        # Erstelle neue Resume-Informationen
        resume_info = ResumeInfo(
            file_id=file_id,
            file_path=file_path,
            total_bytes=total_bytes
        )
        
        self.resume_data[file_id] = resume_info
        return resume_info
    
    def update_resume_info(self, file_id: str, downloaded_bytes: int) -> None:
        """
        Aktualisiert die Resume-Informationen für eine Datei.
        
        Args:
            file_id: Telegram-Datei-ID
            downloaded_bytes: Anzahl der heruntergeladenen Bytes
        """
        if file_id in self.resume_data:
            self.resume_data[file_id].downloaded_bytes = downloaded_bytes
            self.resume_data[file_id].last_modified = datetime.now()
    
    def save_resume_state(self, file_id: str) -> None:
        """
        Speichert den aktuellen Zustand für die Wiederaufnahme.
        
        Args:
            file_id: Telegram-Datei-ID
        """
        if file_id not in self.resume_data:
            logger.warning(f"Keine Resume-Informationen für Datei {file_id} gefunden")
            return
        
        try:
            resume_info = self.resume_data[file_id]
            
            # Berechne Prüfsumme für bereits heruntergeladene Daten
            if resume_info.file_path.exists() and resume_info.downloaded_bytes > 0:
                # Für teilweise heruntergeladene Dateien berechnen wir die Prüfsumme
                # nur für den bereits heruntergeladenen Teil
                resume_info.checksum = self.calculate_checksum(resume_info.file_path)
            
            # Speichere die Resume-Informationen in der Datenbank
            try:
                audio_file = AudioFile.get_by_file_id(file_id)
                if audio_file:
                    audio_file.resume_offset = resume_info.downloaded_bytes
                    audio_file.resume_checksum = resume_info.checksum
                    audio_file.save()
                    logger.debug(f"Resume-Informationen für {file_id} in Datenbank gespeichert")
            except Exception as e:
                logger.error(f"Fehler beim Speichern der Resume-Informationen in der Datenbank: {e}")
                
        except Exception as e:
            logger.error(f"Fehler beim Speichern des Resume-Zustands für {file_id}: {e}")
    
    def load_resume_state(self, file_id: str, file_path: Path, total_bytes: int) -> ResumeInfo:
        """
        Lädt den Resume-Zustand für eine Datei.
        
        Args:
            file_id: Telegram-Datei-ID
            file_path: Pfad zur Datei
            total_bytes: Gesamtgröße der Datei
            
        Returns:
            ResumeInfo-Objekt
        """
        try:
            # Hole Resume-Informationen aus der Datenbank
            try:
                audio_file = AudioFile.get_by_file_id(file_id)
                if audio_file and audio_file.resume_offset and audio_file.resume_offset > 0:
                    resume_info = ResumeInfo(
                        file_id=file_id,
                        file_path=file_path,
                        downloaded_bytes=audio_file.resume_offset,
                        total_bytes=total_bytes,
                        checksum=audio_file.resume_checksum
                    )
                    
                    # Verifiziere Prüfsumme, falls verfügbar
                    if resume_info.checksum and file_path.exists():
                        if not self.verify_checksum(file_path, resume_info.checksum):
                            logger.warning(f"Prüfsummenfehler für {file_id}, starte Download neu")
                            resume_info.downloaded_bytes = 0
                            resume_info.checksum = None
                    
                    self.resume_data[file_id] = resume_info
                    logger.info(f"Resume-Informationen für {file_id} geladen: {resume_info.downloaded_bytes} bytes")
                    return resume_info
                    
            except Exception as e:
                logger.error(f"Fehler beim Laden der Resume-Informationen aus der Datenbank: {e}")
            
            # Falls keine Resume-Informationen in der Datenbank vorhanden sind,
            # erstelle neue
            resume_info = self.get_resume_info(file_id, file_path, total_bytes)
            return resume_info
            
        except Exception as e:
            logger.error(f"Fehler beim Laden des Resume-Zustands für {file_id}: {e}")
            # Rückfall auf neue Resume-Informationen
            return self.get_resume_info(file_id, file_path, total_bytes)
    
    def can_resume(self, file_id: str) -> bool:
        """
        Prüft, ob ein Download wiederaufgenommen werden kann.
        
        Args:
            file_id: Telegram-Datei-ID
            
        Returns:
            True, wenn der Download wiederaufgenommen werden kann
        """
        if file_id not in self.resume_data:
            return False
        
        resume_info = self.resume_data[file_id]
        return (resume_info.downloaded_bytes > 0 and 
                resume_info.downloaded_bytes < resume_info.total_bytes)
    
    def increment_retry_count(self, file_id: str) -> int:
        """
        Erhöht den Wiederholungszähler für eine Datei.
        
        Args:
            file_id: Telegram-Datei-ID
            
        Returns:
            Aktueller Wiederholungszähler
        """
        if file_id in self.resume_data:
            self.resume_data[file_id].retry_count += 1
            return self.resume_data[file_id].retry_count
        return 0
    
    def reset_resume_info(self, file_id: str) -> None:
        """
        Setzt die Resume-Informationen für eine Datei zurück.
        
        Args:
            file_id: Telegram-Datei-ID
        """
        if file_id in self.resume_data:
            resume_info = self.resume_data[file_id]
            resume_info.downloaded_bytes = 0
            resume_info.checksum = None
            resume_info.retry_count = 0
            resume_info.last_modified = datetime.now()
            
            # Aktualisiere auch die Datenbank
            try:
                audio_file = AudioFile.get_by_file_id(file_id)
                if audio_file:
                    audio_file.resume_offset = 0
                    audio_file.resume_checksum = None
                    audio_file.save()
            except Exception as e:
                logger.error(f"Fehler beim Zurücksetzen der Resume-Informationen in der Datenbank: {e}")
    
    def cleanup_resume_info(self, file_id: str) -> None:
        """
        Bereinigt die Resume-Informationen für eine abgeschlossene Datei.
        
        Args:
            file_id: Telegram-Datei-ID
        """
        if file_id in self.resume_data:
            del self.resume_data[file_id]
            logger.debug(f"Resume-Informationen für {file_id} bereinigt")
    
    def get_progress_info(self, file_id: str) -> Dict[str, Any]:
        """
        Gibt Fortschrittsinformationen für eine Datei zurück.
        
        Args:
            file_id: Telegram-Datei-ID
            
        Returns:
            Dictionary mit Fortschrittsinformationen
        """
        if file_id not in self.resume_data:
            return {}
        
        resume_info = self.resume_data[file_id]
        progress_percent = (resume_info.downloaded_bytes / resume_info.total_bytes * 100 
                           if resume_info.total_bytes > 0 else 0)
        
        return {
            "file_id": resume_info.file_id,
            "downloaded_bytes": resume_info.downloaded_bytes,
            "total_bytes": resume_info.total_bytes,
            "progress_percent": round(progress_percent, 2),
            "can_resume": self.can_resume(file_id),
            "retry_count": resume_info.retry_count,
            "last_modified": resume_info.last_modified.isoformat()
        }


# Globale Instanz des ResumeManagers
_resume_manager: Optional[AdvancedResumeManager] = None


def get_resume_manager(download_dir: Path = None) -> AdvancedResumeManager:
    """
    Gibt die globale Instanz des AdvancedResumeManager zurück.
    
    Args:
        download_dir: Download-Verzeichnis (nur für die erste Initialisierung)
        
    Returns:
        AdvancedResumeManager-Instanz
    """
    global _resume_manager
    if _resume_manager is None:
        if download_dir is None:
            raise ValueError("Download-Verzeichnis erforderlich für die erste Initialisierung")
        _resume_manager = AdvancedResumeManager(download_dir)
    return _resume_manager


def initialize_resume_manager(download_dir: Path) -> None:
    """
    Initialisiert den Resume-Manager.
    
    Args:
        download_dir: Download-Verzeichnis
    """
    try:
        global _resume_manager
        _resume_manager = AdvancedResumeManager(download_dir)
        logger.info("Resume-Manager initialisiert")
    except Exception as e:
        handle_error(e, "Fehler bei der Initialisierung des Resume-Managers")
        raise


def load_file_resume_state(file_id: str, file_path: Path, total_bytes: int) -> ResumeInfo:
    """
    Lädt den Resume-Zustand für eine Datei.
    
    Args:
        file_id: Telegram-Datei-ID
        file_path: Pfad zur Datei
        total_bytes: Gesamtgröße der Datei
        
    Returns:
        ResumeInfo-Objekt
    """
    try:
        manager = get_resume_manager()
        return manager.load_resume_state(file_id, file_path, total_bytes)
    except Exception as e:
        handle_error(e, f"Fehler beim Laden des Resume-Zustands für {file_id}")
        raise


def save_file_resume_state(file_id: str) -> None:
    """
    Speichert den Resume-Zustand für eine Datei.
    
    Args:
        file_id: Telegram-Datei-ID
    """
    try:
        manager = get_resume_manager()
        manager.save_resume_state(file_id)
    except Exception as e:
        handle_error(e, f"Fehler beim Speichern des Resume-Zustands für {file_id}")


def update_file_resume_info(file_id: str, downloaded_bytes: int) -> None:
    """
    Aktualisiert die Resume-Informationen für eine Datei.
    
    Args:
        file_id: Telegram-Datei-ID
        downloaded_bytes: Anzahl der heruntergeladenen Bytes
    """
    try:
        manager = get_resume_manager()
        manager.update_resume_info(file_id, downloaded_bytes)
    except Exception as e:
        handle_error(e, f"Fehler beim Aktualisieren der Resume-Informationen für {file_id}")


def can_resume_download(file_id: str) -> bool:
    """
    Prüft, ob ein Download wiederaufgenommen werden kann.
    
    Args:
        file_id: Telegram-Datei-ID
        
    Returns:
        True, wenn der Download wiederaufgenommen werden kann
    """
    try:
        manager = get_resume_manager()
        return manager.can_resume(file_id)
    except Exception as e:
        handle_error(e, f"Fehler bei der Prüfung der Wiederaufnahme für {file_id}")
        return False


def increment_file_retry_count(file_id: str) -> int:
    """
    Erhöht den Wiederholungszähler für eine Datei.
    
    Args:
        file_id: Telegram-Datei-ID
        
    Returns:
        Aktueller Wiederholungszähler
    """
    try:
        manager = get_resume_manager()
        return manager.increment_retry_count(file_id)
    except Exception as e:
        handle_error(e, f"Fehler beim Erhöhen des Wiederholungszählers für {file_id}")
        return 0


def reset_file_resume_info(file_id: str) -> None:
    """
    Setzt die Resume-Informationen für eine Datei zurück.
    
    Args:
        file_id: Telegram-Datei-ID
    """
    try:
        manager = get_resume_manager()
        manager.reset_resume_info(file_id)
    except Exception as e:
        handle_error(e, f"Fehler beim Zurücksetzen der Resume-Informationen für {file_id}")


def cleanup_file_resume_info(file_id: str) -> None:
    """
    Bereinigt die Resume-Informationen für eine abgeschlossene Datei.
    
    Args:
        file_id: Telegram-Datei-ID
    """
    try:
        manager = get_resume_manager()
        manager.cleanup_resume_info(file_id)
    except Exception as e:
        handle_error(e, f"Fehler beim Bereinigen der Resume-Informationen für {file_id}")


def get_file_progress_info(file_id: str) -> Dict[str, Any]:
    """
    Gibt Fortschrittsinformationen für eine Datei zurück.
    
    Args:
        file_id: Telegram-Datei-ID
        
    Returns:
        Dictionary mit Fortschrittsinformationen
    """
    try:
        manager = get_resume_manager()
        return manager.get_progress_info(file_id)
    except Exception as e:
        handle_error(e, f"Fehler beim Abrufen der Fortschrittsinformationen für {file_id}")
        return {}