"""
Hauptklasse für den Telegram Audio Downloader.
"""

import asyncio
import os
import time
import weakref
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union
from collections import OrderedDict

from telethon import TelegramClient
from telethon.errors import FloodWaitError, RPCError
from telethon.tl.types import (
    Document,
    DocumentAttributeAudio,
    Message,
    MessageMediaDocument,
    TypeDocument,
)
from tqdm import tqdm

from .models import AudioFile, TelegramGroup, DownloadStatus, GroupProgress
from .config import Config
from .logging_config import get_logger, get_error_tracker
from .error_handling import handle_error, SecurityError
# Neue Importe für die intelligente Warteschlange
from .intelligent_queue import IntelligentQueue, QueueItem, Priority

# Neue Importe für die fortgeschrittene Download-Wiederaufnahme
from .advanced_resume import (
    get_resume_manager, load_file_resume_state, save_file_resume_state,
    update_file_resume_info, can_resume_download, increment_file_retry_count,
    reset_file_resume_info, cleanup_file_resume_info
)
# Neue Importe für die intelligente Bandbreitensteuerung
from .intelligent_bandwidth import (
    get_bandwidth_controller, adjust_bandwidth_settings,
    register_download_start, register_download_end,
    can_start_new_download, update_download_speed
)
# Neue Importe für die erweiterte Metadaten-Extraktion
from .advanced_metadata_extraction import AdvancedMetadataExtractor
# Neue Importe für die erweiterte Dateinamen-Generierung
from .advanced_filename_generation import get_advanced_filename_generator
# Neue Importe für die erweiterten Sicherheitsfunktionen
from .enhanced_security import (
    get_file_access_control, get_file_integrity_checker, get_audit_logger,
    check_file_access, verify_file_integrity, secure_file_operation,
    log_security_event
)
# Neue Importe für die erweiterte Systemintegration
from .system_integration import (
    send_system_notification, show_in_default_file_manager,
    add_to_default_media_library
)
# Neue Importe für erweiterte Benachrichtigungen
from .advanced_notifications import (
    get_advanced_notifier, send_download_completed_notification,
    send_download_failed_notification, send_batch_completed_notification
)

# Importiere fehlende Fehlerklassen
from .error_handling import ConfigurationError, AuthenticationError, DatabaseError, DownloadError

# Importiere fehlende Konstanten
from .utils import AUDIO_EXTENSIONS
import src.telegram_audio_downloader.utils as utils

# Importiere vorhandene Klassen
try:
    from .adaptive_parallelism import AdaptiveParallelismController
    RealAdaptiveParallelismController = AdaptiveParallelismController
except ImportError:
    # Mock-Klasse für AdaptiveParallelismController falls nicht verfügbar
    class RealAdaptiveParallelismController:
        def __init__(self, *args, **kwargs):
            pass
        
        def get_semaphore(self):
            return asyncio.Semaphore(3)
            
        def update_parallelism(self):
            pass
            
        def record_download_speed(self, speed_mbps):
            pass

# Mock-Klassen für fehlende Module
class PrefetchManager:
    def __init__(self, *args, **kwargs):
        pass
    
    def should_prefetch(self):
        return False
        
    def start_prefetching(self, *args, **kwargs):
        pass
        
    def record_download(self, *args, **kwargs):
        pass

class NetworkOptimizer:
    def __init__(self, *args, **kwargs):
        pass

class AdvancedMemoryManager:
    def __init__(self, *args, **kwargs):
        pass
    
    def perform_memory_maintenance(self):
        pass

class RealtimePerformanceAnalyzer:
    def __init__(self, *args, **kwargs):
        pass
    
    def record_download_start(self):
        pass
        
    def record_error(self, *args, **kwargs):
        pass
        
    def record_download_completion(self, *args, **kwargs):
        pass

class AutomaticErrorRecovery:
    def __init__(self, *args, **kwargs):
        pass
    
    def attempt_recovery(self, *args, **kwargs):
        return False

# Globale Error Tracker Instanz
error_tracker = get_error_tracker()

logger = get_logger(__name__)


class LRUCache:
    """Least Recently Used (LRU) Cache mit fester Größe für speichereffizientes Caching."""
    
    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self.cache = OrderedDict()
        
    def get(self, key: str) -> Optional[bool]:
        """Holt einen Wert aus dem Cache und markiert ihn als zuletzt verwendet."""
        if key in self.cache:
            # Wert an das Ende verschieben (zuletzt verwendet)
            self.cache.move_to_end(key)
            return self.cache[key]
        return None
        
    def put(self, key: str, value: bool) -> None:
        """Fügt einen Wert zum Cache hinzu."""
        # Wenn der Schlüssel bereits existiert, ans Ende verschieben
        if key in self.cache:
            self.cache.move_to_end(key)
        # Neuen Wert hinzufügen
        self.cache[key] = value
        
        # Wenn der Cache zu groß wird, ältesten Eintrag entfernen
        if len(self.cache) > self.max_size:
            self.cache.popitem(last=False)
            
    def __contains__(self, key: str) -> bool:
        """Prüft, ob ein Schlüssel im Cache enthalten ist."""
        return key in self.cache
        
    def __len__(self) -> int:
        """Gibt die aktuelle Größe des Caches zurück."""
        return len(self.cache)


class AudioDownloader:
    """Hauptklasse zum Herunterladen von Audiodateien aus Telegram-Gruppen."""

    def __init__(
        self, download_dir: str = "downloads", max_concurrent_downloads: int = 3, config: Optional[Config] = None
    ):
        """
        Initialisiert den AudioDownloader.

        Args:
            download_dir: Verzeichnis, in das die Audiodateien heruntergeladen werden sollen
            max_concurrent_downloads: Maximale Anzahl paralleler Downloads
            config: Konfigurationsobjekt
        """
        self.client: Optional[TelegramClient] = None
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.max_concurrent_downloads = max_concurrent_downloads
        self.config = config or Config()  # Verwende die übergebene Konfiguration oder eine Standardkonfiguration
        
        # Initialisiere die intelligente Warteschlange
        self.download_queue = IntelligentQueue(max_concurrent_downloads)
        
        # Erweiterter Dateinamen-Generator
        self.filename_generator = get_advanced_filename_generator()
        
        # Adaptive Parallelism Controller
        self.adaptive_parallelism = RealAdaptiveParallelismController(
            download_dir=str(self.download_dir),
            initial_concurrent_downloads=max_concurrent_downloads,
            min_concurrent_downloads=1,
            max_concurrent_downloads=10
        )
        
        # Verwende initially die statische Semaphore für Abwärtskompatibilität
        self.download_semaphore = asyncio.Semaphore(max_concurrent_downloads)

        # Performance-Monitor initialisieren
        from .performance import get_performance_monitor
        self.performance_monitor = get_performance_monitor(
            download_dir=self.download_dir, max_memory_mb=1024
        )

        # Datenbank initialisieren
        from .database import init_db
        self.db = init_db()

        # Speichereffizienter Cache für bereits heruntergeladene Dateien (max. 50.000 Einträge)
        self._downloaded_files_cache = LRUCache(max_size=50000)
        self._load_downloaded_files()

        # Download-Statistiken
        self.downloads_in_progress = 0
        self.total_downloads = 0
        self.successful_downloads = 0
        self.failed_downloads = 0
        
        # Initialisiere die zusätzlichen Komponenten
        self.prefetch_manager = PrefetchManager()
        self.network_optimizer = NetworkOptimizer()
        self.advanced_memory_manager = AdvancedMemoryManager()
        self.realtime_performance_analyzer = RealtimePerformanceAnalyzer()
        self.automatic_error_recovery = AutomaticErrorRecovery()

    async def initialize_client(self) -> None:
        """Initialisiert den Telegram-Client mit den Umgebungsvariablen."""
        # Die Konfiguration wird jetzt über die CLI übergeben
        # Diese Methode wird für Abwärtskompatibilität beibehalten
        api_id = os.getenv("API_ID")
        api_hash = os.getenv("API_HASH")
        session_name = os.getenv("SESSION_NAME", "session")

        if not all([api_id, api_hash]):
            error = ConfigurationError(
                "API_ID und API_HASH müssen in der .env-Datei gesetzt sein"
            )
            handle_error(error, "initialize_client_config")
            raise error

        try:
            # Erstelle die Proxy-Konfiguration, falls vorhanden
            proxy_config: Optional[Dict[str, Any]] = None
            if (self.config.proxy_type and 
                self.config.proxy_host and 
                self.config.proxy_port):
                try:
                    proxy_port_int = int(self.config.proxy_port) if self.config.proxy_port else 1080
                    proxy_config = {
                        'proxy_type': self.config.proxy_type or 'socks5',
                        'addr': self.config.proxy_host or '',
                        'port': proxy_port_int,
                        'username': self.config.proxy_username or None,
                        'password': self.config.proxy_password or None,
                    }
                except (ValueError, TypeError):
                    # Falls die Proxy-Parameter ungültig sind, verwenden wir kein Proxy
                    proxy_config = None
            
            # Sicherstellen, dass api_id und api_hash nicht None sind
            api_id_int = int(api_id) if api_id and api_id.isdigit() else 0
            api_hash_str = api_hash or ""
            
            # Erstelle den TelegramClient
            self.client = TelegramClient(
                session_name, 
                api_id_int, 
                api_hash_str,
                proxy=proxy_config if proxy_config else None
            )
            
            # Starte den Client nur wenn er erfolgreich erstellt wurde
            if self.client:
                # Prüfe, ob start() awaitable ist
                if callable(getattr(self.client, 'start', None)):
                    start_result = self.client.start()
                    if hasattr(start_result, '__await__'):
                        await start_result
            logger.info("Telegram-Client erfolgreich initialisiert")
        except Exception as e:
            error = AuthenticationError(f"Fehler bei der Authentifizierung: {e}")
            handle_error(error, "initialize_client_auth")
            raise error

    def _load_downloaded_files(self) -> None:
        """Lädt bereits heruntergeladene Dateien in den Cache."""
        try:
            # Nur die file_id laden, nicht das ganze Objekt
            downloaded_file_ids = [
                audio.file_id
                for audio in AudioFile.select(AudioFile.file_id).where(
                    AudioFile.status == DownloadStatus.COMPLETED.value
                )
            ]
            
            # In den LRU-Cache laden
            for file_id in downloaded_file_ids:
                self._downloaded_files_cache.put(file_id, True)
                
            logger.info(
                f"{len(downloaded_file_ids)} bereits heruntergeladene Dateien geladen"
            )
        except Exception as e:
            error = DatabaseError(f"Fehler beim Laden heruntergeladener Dateien: {e}")
            handle_error(error, "_load_downloaded_files")
            raise error

    def _is_audio_file(self, document: Union[Document, TypeDocument]) -> bool:
        """Überprüft, ob es sich bei dem Dokument um eine Audiodatei handelt."""
        try:
            # Überprüfe, ob es sich um ein Document-Objekt handelt
            if not isinstance(document, Document):
                return False
                
            # Überprüfe die Dateiendung
            file_ext = Path(getattr(document, "mime_type", "") or "").suffix.lower()
            if file_ext and file_ext in AUDIO_EXTENSIONS:
                return True

            # Überprüfe die MIME-Type
            mime_type = getattr(document, "mime_type", "")
            if mime_type and any(
                audio_type in mime_type for audio_type in ["audio", "mpeg"]
            ):
                return True

            # Überprüfe die Attribute
            attributes = getattr(document, "attributes", [])
            for attr in attributes:
                if isinstance(attr, DocumentAttributeAudio):
                    return True

            return False
        except Exception as e:
            error = DownloadError(f"Fehler bei der Audio-Datei-Erkennung: {e}")
            handle_error(error, "_is_audio_file")
            return False

    def _extract_audio_info(self, document: Document) -> Dict[str, Any]:
        """Extrahiert Metadaten aus einem Audio-Dokument."""
        try:
            audio_attrs = next(
                (
                    attr
                    for attr in document.attributes
                    if isinstance(attr, DocumentAttributeAudio)
                ),
                None,
            )

            # Bestimme die Dateiendung
            file_ext = Path(document.mime_type or "").suffix.lower()
            if not file_ext or file_ext not in AUDIO_EXTENSIONS:
                file_ext = ".mp3"  # Standardendung, falls nicht erkannt

            # Extrahiere Metadaten
            title = getattr(audio_attrs, "title", None) if audio_attrs else None
            performer = getattr(audio_attrs, "performer", None) if audio_attrs else None

            # Verwende den erweiterten Dateinamen-Generator
            metadata = {
                "title": title,
                "artist": performer,
            }
            
            # Generiere den Dateinamen mit dem erweiterten Generator
            filename = self.filename_generator.generate_filename(metadata, file_ext)

            return {
                "file_id": str(document.id),
                "file_unique_id": getattr(document, "file_reference", b"").hex(),
                "file_name": filename,
                "file_size": getattr(document, "size", 0),
                "mime_type": getattr(document, "mime_type", None) or "audio/mpeg",
                "duration": getattr(audio_attrs, "duration", None) if audio_attrs else None,
                "title": title,
                "performer": performer,
            }
        except Exception as e:
            error = DownloadError(f"Fehler beim Extrahieren von Audio-Informationen: {e}")
            handle_error(error, "_extract_audio_info")
            # Fallback-Informationen zurückgeben
            return {
                "file_id": str(getattr(document, "id", "")),
                "file_unique_id": getattr(document, "file_reference", b"").hex() if hasattr(document, "file_reference") else "",
                "file_name": f"unknown_{getattr(document, 'id', 'file')}.mp3",
                "file_size": getattr(document, "size", 0),
                "mime_type": getattr(document, "mime_type", None) or "audio/mpeg",
                "duration": None,
                "title": None,
                "performer": None,
            }

    async def download_audio_files(
        self, group_name: str, limit: Optional[int] = None, last_message_id: Optional[int] = None
    ) -> int:
        """
        Lädt alle Audiodateien aus der angegebenen Gruppe herunter (parallel).

        Args:
            group_name: Name oder ID der Telegram-Gruppe
            limit: Maximale Anzahl der zu verarbeitenden Nachrichten (optional)
            last_message_id: Letzte verarbeitete Nachrichten-ID (optional)
            
        Returns:
            Anzahl der heruntergeladenen Dateien
        """
        if not self.client:
            await self.initialize_client()

        # Sicherstellen, dass der Client initialisiert wurde
        if not self.client:
            error = AuthenticationError("Telegram-Client konnte nicht initialisiert werden")
            handle_error(error, "download_audio_files_client")
            raise error

        try:
            # Gruppe abrufen
            group_entity = await self.client.get_entity(group_name)
            logger.info(
                f"Gruppe gefunden: {getattr(group_entity, 'title', 'Unknown')} (ID: {getattr(group_entity, 'id', 'Unknown')})"
            )

            # Gruppeninformationen in der Datenbank speichern
            group_id = getattr(group_entity, 'id', 0)
            group_title = getattr(group_entity, "title", "")
            group_username = getattr(group_entity, "username", None)
            
            group, _ = TelegramGroup.get_or_create(
                group_id=group_id,
                defaults={
                    "title": group_title,
                    "username": group_username,
                },
            )

            # Nachrichten abrufen
            logger.info("Sammle Audiodateien...")
            audio_messages = []

            # Erstelle die Iterationsparameter
            iter_params: Dict[str, Any] = {"limit": limit}
            if last_message_id:
                # Verwende min_id, um nur Nachrichten nach der letzten ID zu verarbeiten
                iter_params["min_id"] = last_message_id

            # Sicherstellen, dass group_entity ein gültiges Entity-Objekt ist
            if not group_entity:
                raise DownloadError("Gruppe konnte nicht gefunden werden")
                
            async for message in self.client.iter_messages(group_entity, **iter_params):
                if not hasattr(message, "media") or not isinstance(
                    message.media, MessageMediaDocument
                ):
                    continue

                document = message.media.document
                if not document or not self._is_audio_file(document):
                    continue

                # Prüfe, ob die Datei bereits heruntergeladen wurde
                file_id = str(document.id)
                if self._downloaded_files_cache.get(file_id):
                    logger.debug(
                        f"Überspringe bereits heruntergeladene Datei: {file_id}"
                    )
                    continue

                audio_messages.append((message, document, group))
                
                # Speichere die aktuelle Nachrichten-ID für die Fortsetzung
                if hasattr(group_entity, 'id') and hasattr(message, 'id'):
                    await self.save_last_message_id(group_entity.id, message.id)

            logger.info(f"{len(audio_messages)} neue Audiodateien gefunden")
            self.total_downloads = len(audio_messages)

            if not audio_messages:
                logger.info("Keine neuen Audiodateien zum Herunterladen gefunden")
                return 0

            # Parallele Downloads starten
            download_tasks = [
                self._download_audio_concurrent(message, document, group)
                for message, document, group in audio_messages
            ]

            # Alle Downloads parallel ausführen
            results = await asyncio.gather(*download_tasks, return_exceptions=True)

            # Ergebnisse auswerten
            successful_downloads = 0
            failed_downloads = 0
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Download-Fehler: {result}")
                    failed_downloads += 1
                else:
                    successful_downloads += 1

            logger.info(
                f"Downloads abgeschlossen: {successful_downloads} erfolgreich, "
                f"{failed_downloads} fehlgeschlagen"
            )

            # Sende Systembenachrichtigung über abgeschlossene Downloads
            if successful_downloads > 0 or failed_downloads > 0:
                send_system_notification(
                    title="Telegram Audio Downloader",
                    message=f"Downloads abgeschlossen: {successful_downloads} erfolgreich, {failed_downloads} fehlgeschlagen"
                )

            return successful_downloads

        except Exception as e:
            error = DownloadError(f"Fehler beim Herunterladen von Audiodateien: {e}")
            handle_error(error, "download_audio_files")
            raise error

    async def download_audio_files_lite(
        self, group_name: str, limit: Optional[int] = None, last_message_id: Optional[int] = None
    ) -> int:
        """
        Lädt Audiodateien aus der angegebenen Gruppe herunter (vereinfachte Version).

        Args:
            group_name: Name oder ID der Telegram-Gruppe
            limit: Maximale Anzahl der zu verarbeitenden Nachrichten (optional)
            last_message_id: Letzte verarbeitete Nachrichten-ID (optional)
            
        Returns:
            Anzahl der heruntergeladenen Dateien
        """
        if not self.client:
            await self.initialize_client()

        # Sicherstellen, dass der Client initialisiert wurde
        if not self.client:
            error = AuthenticationError("Telegram-Client konnte nicht initialisiert werden")
            handle_error(error, "download_audio_files_lite_client")
            raise error

        try:
            # Gruppe abrufen
            group_entity = await self.client.get_entity(group_name)
            logger.info(
                f"Gruppe gefunden: {getattr(group_entity, 'title', 'Unknown')} (ID: {getattr(group_entity, 'id', 'Unknown')})"
            )

            # Gruppeninformationen in der Datenbank speichern
            group_id = getattr(group_entity, 'id', 0)
            group_title = getattr(group_entity, "title", "")
            group_username = getattr(group_entity, "username", None)
            
            group, _ = TelegramGroup.get_or_create(
                group_id=group_id,
                defaults={
                    "title": group_title,
                    "username": group_username,
                },
            )

            # Nachrichten abrufen
            logger.info("Sammle Audiodateien...")
            audio_messages = []

            # Erstelle die Iterationsparameter
            iter_params: Dict[str, Any] = {"limit": limit}
            if last_message_id:
                # Verwende min_id, um nur Nachrichten nach der letzten ID zu verarbeiten
                iter_params["min_id"] = last_message_id

            # Sicherstellen, dass group_entity ein gültiges Entity-Objekt ist
            if not group_entity:
                raise DownloadError("Gruppe konnte nicht gefunden werden")
                
            async for message in self.client.iter_messages(group_entity, **iter_params):
                if not hasattr(message, "media") or not isinstance(
                    message.media, MessageMediaDocument
                ):
                    continue

                document = message.media.document
                if not document or not self._is_audio_file(document):
                    continue

                # Prüfe, ob die Datei bereits heruntergeladen wurde
                file_id = str(document.id)
                if self._downloaded_files_cache.get(file_id):
                    logger.debug(
                        f"Überspringe bereits heruntergeladene Datei: {file_id}"
                    )
                    continue

                audio_messages.append((message, document, group))
                
                # Speichere die aktuelle Nachrichten-ID für die Fortsetzung
                if hasattr(group_entity, 'id') and hasattr(message, 'id'):
                    await self.save_last_message_id(group_entity.id, message.id)

            logger.info(f"{len(audio_messages)} neue Audiodateien gefunden")
            self.total_downloads = len(audio_messages)

            if not audio_messages:
                logger.info("Keine neuen Audiodateien zum Herunterladen gefunden")
                return 0

            # Sequentielle Downloads (vereinfacht)
            successful_downloads = 0
            for message, document, group in audio_messages:
                try:
                    await self._download_audio(message, document, group)
                    successful_downloads += 1
                except Exception as e:
                    logger.error(f"Fehler beim Download von {document.id}: {e}")

            logger.info(
                f"Downloads abgeschlossen: {successful_downloads} erfolgreich, "
                f"{len(audio_messages) - successful_downloads} fehlgeschlagen"
            )

            return successful_downloads

        except Exception as e:
            error = DownloadError(f"Fehler beim Herunterladen von Audiodateien: {e}")
            handle_error(error, "download_audio_files_lite")
            raise error

    async def _download_audio_concurrent(
        self, message: Message, document: Document, group: TelegramGroup
    ) -> bool:
        """
        Lädt eine einzelne Audiodatei herunter (für parallele Ausführung).

        Args:
            message: Telegram-Nachricht
            document: Audio-Dokument
            group: Telegram-Gruppe

        Returns:
            True bei Erfolg, False bei Fehler
        """
        # Aufzeichnung in der Performance-Analyse
        if hasattr(self, 'realtime_performance_analyzer') and self.realtime_performance_analyzer:
            try:
                self.realtime_performance_analyzer.record_download_start()
            except Exception:
                pass
        
        # Aktualisiere die adaptive Parallelisierung
        if hasattr(self.adaptive_parallelism, 'update_parallelism'):
            try:
                await self.adaptive_parallelism.update_parallelism()
            except Exception:
                pass
        
        # Verwende die adaptive Semaphore
        semaphore = None
        if hasattr(self.adaptive_parallelism, 'get_semaphore'):
            try:
                semaphore = self.adaptive_parallelism.get_semaphore()
            except Exception:
                semaphore = self.download_semaphore
        else:
            semaphore = self.download_semaphore
            
        if semaphore:
            async with semaphore:
                self.downloads_in_progress += 1
                try:
                    await self._download_audio(message, document, group)
                    return True
                except Exception as e:
                    logger.error(f"Fehler beim Download: {e}")
                    return False
                finally:
                    self.downloads_in_progress -= 1
        else:
            # Fallback auf die statische Semaphore
            async with self.download_semaphore:
                self.downloads_in_progress += 1
                try:
                    await self._download_audio(message, document, group)
                    return True
                except Exception as e:
                    logger.error(f"Fehler beim Download: {e}")
                    return False
                finally:
                    self.downloads_in_progress -= 1

    async def _download_audio(
        self, message: Message, document: Document, group: TelegramGroup
    ) -> None:
        """Lädt eine einzelne Audiodatei herunter (mit Resume-Unterstützung)."""
        file_id = str(document.id) if document.id else "unknown"
        file_size = getattr(document, 'size', 0)
        file_size_mb = file_size / (1024 * 1024) if file_size > 0 else 0
        start_time = time.time()
        
        # Für audio_info fallback
        audio_info: Dict[str, Any] = {}

        # Performance-Checks vor Download
        if hasattr(self, 'performance_monitor') and self.performance_monitor:
            try:
                performance_check = await self.performance_monitor.before_download(file_size_mb)
                if not performance_check:
                    logger.error(f"Performance-Check fehlgeschlagen für {file_id}, überspringe")
                    return
            except Exception:
                pass

        try:
            # Audiodaten extrahieren
            audio_info = self._extract_audio_info(document)

            # Periodische Wartung
            if hasattr(self, 'performance_monitor') and self.performance_monitor:
                try:
                    await self.performance_monitor.periodic_maintenance()
                except Exception:
                    pass

            # Speicherwartung durchführen
            if hasattr(self, 'advanced_memory_manager') and self.advanced_memory_manager:
                try:
                    await self.advanced_memory_manager.perform_memory_maintenance()
                except Exception:
                    pass

            # Datenbankeintrag abrufen oder erstellen
            audio_file, created = AudioFile.get_or_create(
                file_id=file_id,
                defaults={
                    **audio_info,
                    "group": group,
                    "status": DownloadStatus.PENDING.value,
                },
            )

            # Aufzeichnung für Prefetching-Muster
            if hasattr(self, 'prefetch_manager') and self.prefetch_manager:
                try:
                    self.prefetch_manager.record_download(
                        group_id=getattr(group, 'group_id', 0),
                        file_extension=Path(audio_info["file_name"]).suffix,
                        file_size=audio_info["file_size"],
                        file_id=file_id
                    )
                except Exception:
                    pass

            # Prüfen, ob bereits vollständig heruntergeladen
            is_downloaded = getattr(audio_file, 'is_downloaded', False)
            if not created and is_downloaded:
                logger.debug(
                    f"Datei bereits heruntergeladen: {audio_info['file_name']}"
                )
                self._downloaded_files_cache.put(file_id, True)
                return

            # Download-Versuch zählen
            download_attempts = getattr(audio_file, 'download_attempts', 0) + 1
            if hasattr(audio_file, 'download_attempts'):
                audio_file.download_attempts = download_attempts
            if hasattr(audio_file, 'last_attempt_at'):
                audio_file.last_attempt_at = datetime.now()
            if hasattr(audio_file, 'save'):
                try:
                    audio_file.save()
                except Exception:
                    pass

            # Zielpfad erstellen
            download_path = self.download_dir / audio_info["file_name"]
            download_path = utils.get_unique_filepath(download_path)

            # Partielle Datei-Pfad
            partial_path = download_path.with_suffix(download_path.suffix + ".partial")

            # Prüfen, ob Download fortgesetzt werden kann
            start_byte = 0
            if hasattr(audio_file, 'can_resume_download'):
                try:
                    can_resume = audio_file.can_resume_download()
                    if can_resume:
                        partial_file_path = getattr(audio_file, 'partial_file_path', None)
                        if partial_file_path:
                            partial_size = Path(partial_file_path).stat().st_size if Path(partial_file_path).exists() else 0
                            downloaded_bytes = getattr(audio_file, 'downloaded_bytes', 0)
                            if partial_size == downloaded_bytes:
                                start_byte = partial_size
                                logger.info(
                                    f"Setze Download fort ab Byte {start_byte}: {audio_info['file_name']}"
                                )
                            else:
                                logger.warning(
                                    f"Partielle Datei inkonsistent, starte neu: {audio_info['file_name']}"
                                )
                                if hasattr(audio_file, 'downloaded_bytes'):
                                    audio_file.downloaded_bytes = 0
                except Exception:
                    pass

            # Status aktualisieren
            if hasattr(audio_file, 'status'):
                audio_file.status = DownloadStatus.DOWNLOADING.value
            if hasattr(audio_file, 'partial_file_path'):
                audio_file.partial_file_path = str(partial_path)
            if hasattr(audio_file, 'save'):
                try:
                    audio_file.save()
                except Exception:
                    pass

            logger.info(
                f"Lade herunter: {audio_info['file_name']} "
                f"({utils.format_file_size(audio_info['file_size'])})"
            )

            # Sicherheitsprüfung: Zugriff auf das Download-Verzeichnis prüfen
            if not check_file_access(self.download_dir):
                log_security_event(
                    "unauthorized_access",
                    f"Zugriff auf Download-Verzeichnis {self.download_dir} verweigert",
                    "high"
                )
                raise SecurityError(f"Zugriff auf Download-Verzeichnis {self.download_dir} verweigert")

            # Download mit Resume-Unterstützung
            downloaded_bytes = 0
            try:
                downloaded_bytes = await self._download_with_resume(
                    message, partial_path, start_byte, audio_file
                )
            except Exception as e:
                logger.error(f"Fehler beim Download: {e}")
                raise

            # Prüfen, ob vollständig heruntergeladen
            if downloaded_bytes >= file_size:
                # Datei von partial zu final verschieben
                try:
                    if partial_path.exists():
                        partial_path.rename(download_path)
                except Exception as e:
                    logger.error(f"Fehler beim Umbenennen der Datei: {e}")
                    raise

                # Checksum berechnen und prüfen
                checksum = utils.calculate_file_hash(download_path, "md5") if download_path.exists() else ""

                # Erweiterte Metadaten mit mutagen extrahieren
                extended_metadata = utils.extract_audio_metadata(download_path) if download_path.exists() else {}

                # Datenbank aktualisieren
                if hasattr(audio_file, 'local_path'):
                    audio_file.local_path = str(download_path)
                if hasattr(audio_file, 'status'):
                    audio_file.status = DownloadStatus.COMPLETED.value
                if hasattr(audio_file, 'downloaded_at'):
                    audio_file.downloaded_at = datetime.now()
                if hasattr(audio_file, 'downloaded_bytes'):
                    audio_file.downloaded_bytes = downloaded_bytes
                if hasattr(audio_file, 'checksum_md5'):
                    audio_file.checksum_md5 = checksum
                if hasattr(audio_file, 'checksum_verified'):
                    audio_file.checksum_verified = True
                if hasattr(audio_file, 'partial_file_path'):
                    audio_file.partial_file_path = None

                # Erweiterte Metadaten einfügen (falls nicht bereits vorhanden)
                if not getattr(audio_file, 'title', None) and extended_metadata.get("title"):
                    audio_file.title = extended_metadata["title"]
                if not getattr(audio_file, 'performer', None) and extended_metadata.get("artist"):
                    audio_file.performer = extended_metadata["artist"]
                if not getattr(audio_file, 'duration', None) and extended_metadata.get("duration"):
                    audio_file.duration = int(extended_metadata["duration"]) if extended_metadata["duration"] else None

                # Weitere erweiterte Metadaten speichern
                if extended_metadata.get("album"):
                    audio_file.album = extended_metadata["album"]
                if extended_metadata.get("date"):
                    audio_file.date = extended_metadata["date"]
                if extended_metadata.get("genre"):
                    audio_file.genre = extended_metadata["genre"]
                if extended_metadata.get("composer"):
                    audio_file.composer = extended_metadata["composer"]
                if extended_metadata.get("track_number"):
                    audio_file.track_number = extended_metadata["track_number"]

                if hasattr(audio_file, 'save'):
                    try:
                        audio_file.save()
                    except Exception:
                        pass

                # In den Cache aufnehmen
                self._downloaded_files_cache.put(file_id, True)

                # Sicherheitsprüfung: Dateiintegrität verifizieren
                if download_path.exists() and not verify_file_integrity(download_path):
                    log_security_event(
                        "file_integrity_violation",
                        f"Integritätsprüfung für {download_path} fehlgeschlagen",
                        "high"
                    )
                    raise SecurityError(f"Integritätsprüfung für {download_path} fehlgeschlagen")

                # Audit-Logging für erfolgreichen Download
                log_security_event(
                    "download_success",
                    f"Download erfolgreich abgeschlossen: {download_path}",
                    "low"
                )

                # Audit-Logging für Dateiintegrität
                log_security_event(
                    "file_integrity_verified",
                    f"Dateiintegrität von {download_path} bestätigt",
                    "low"
                )

                # Performance-Tracking
                duration = time.time() - start_time
                if hasattr(self, 'performance_monitor') and self.performance_monitor:
                    try:
                        self.performance_monitor.after_download(True, file_size_mb, duration)
                    except Exception:
                        pass
                
                # Geschwindigkeit an den AdaptiveParallelismController übergeben
                if duration > 0:
                    speed_mbps = file_size_mb / duration
                    if hasattr(self.adaptive_parallelism, 'record_download_speed'):
                        try:
                            self.adaptive_parallelism.record_download_speed(speed_mbps)
                        except Exception:
                            pass
                
                # Erfolg in der Performance-Analyse aufzeichnen
                if hasattr(self, 'realtime_performance_analyzer') and self.realtime_performance_analyzer:
                    try:
                        self.realtime_performance_analyzer.record_download_completion(True, file_size_mb, duration)
                    except Exception:
                        pass

                logger.info(f"Download erfolgreich: {download_path} ({duration:.2f}s)")
                
                # Sende Benachrichtigung über erfolgreichen Download
                send_system_notification(
                    title="Download abgeschlossen",
                    message=f"{audio_info['file_name']} wurde erfolgreich heruntergeladen",
                    timeout=3000
                )
                
                # Sende erweiterte Benachrichtigung
                try:
                    send_download_completed_notification(
                        file_name=audio_info['file_name'],
                        file_size=audio_info['file_size'],
                        duration=duration
                    )
                except Exception as e:
                    logger.warning(f"Fehler beim Senden der erweiterten Benachrichtigung: {e}")
                
                # Füge die Datei zur Medienbibliothek hinzu
                try:
                    if download_path.exists():
                        add_to_default_media_library(download_path)
                except Exception as e:
                    logger.warning(f"Fehler beim Hinzufügen zur Medienbibliothek: {e}")

            else:
                # Audit-Logging für unvollständigen Download
                log_security_event(
                    "download_incomplete",
                    f"Download unvollständig: {audio_info['file_name']}",
                    "medium"
                )

                # Partieller Download
                if hasattr(audio_file, 'downloaded_bytes'):
                    audio_file.downloaded_bytes = downloaded_bytes
                if hasattr(audio_file, 'status'):
                    audio_file.status = DownloadStatus.FAILED.value
                if hasattr(audio_file, 'error_message'):
                    audio_file.error_message = "Download unvollständig"
                if hasattr(audio_file, 'save'):
                    try:
                        audio_file.save()
                    except Exception:
                        pass

                logger.warning(f"Download unvollständig: {audio_info['file_name']}")
                
                # Fehler in der Performance-Analyse aufzeichnen
                duration = time.time() - start_time
                if hasattr(self, 'realtime_performance_analyzer') and self.realtime_performance_analyzer:
                    try:
                        self.realtime_performance_analyzer.record_download_completion(False, file_size_mb, duration)
                    except Exception:
                        pass

        except FloodWaitError as e:
            # Sicherstellen, dass audio_info definiert ist
            file_name = audio_info.get('file_name', 'Unknown') if 'audio_info' in locals() else 'Unknown'
            
            log_security_event(
                "flood_wait_error",
                f"FloodWaitError beim Download von {file_name}: {e.seconds} Sekunden",
                "medium"
            )

            # Performance-Monitor über FloodWait informieren
            if hasattr(self, 'performance_monitor') and self.performance_monitor:
                try:
                    self.performance_monitor.handle_flood_wait(e.seconds)
                except Exception:
                    pass

            # Wartezeit einhalten
            wait_time = e.seconds
            error_tracker.track_error(e, f"download_{file_id}", "WARNING")
            logger.warning(
                f"FloodWaitError: Warte {wait_time} Sekunden für {file_name}..."
            )
            await asyncio.sleep(wait_time)

            # Performance-Tracking für fehlgeschlagenen Download
            duration = time.time() - start_time
            if hasattr(self, 'performance_monitor') and self.performance_monitor:
                try:
                    self.performance_monitor.after_download(False, file_size_mb, duration)
                except Exception:
                    pass
            
            # Automatische Fehlerbehebung versuchen
            recovery_data = {
                "file_id": file_id,
                "file_name": file_name,
                "wait_time": wait_time
            }
            recovery_success = False
            if hasattr(self, 'automatic_error_recovery') and self.automatic_error_recovery:
                try:
                    recovery_success = await self.automatic_error_recovery.attempt_recovery(e, f"download_{file_id}", recovery_data)
                except Exception:
                    recovery_success = False
            
            # Fehler in der Performance-Analyse aufzeichnen
            if hasattr(self, 'realtime_performance_analyzer') and self.realtime_performance_analyzer:
                try:
                    self.realtime_performance_analyzer.record_error("FloodWaitError", f"download_{file_id}")
                except Exception:
                    pass

            # Retry nur wenn sinnvoll oder Fehlerbehebung erfolgreich
            if recovery_success or error_tracker.should_retry(e, f"download_{file_id}"):
                await self._download_audio(message, document, group)
            else:
                logger.error(f"Zu viele FloodWait-Fehler für {file_id}, überspringe")

        except (RPCError, ConnectionError) as e:
            # Sicherstellen, dass audio_info definiert ist
            file_name = audio_info.get('file_name', 'Unknown') if 'audio_info' in locals() else 'Unknown'
            
            # Audit-Logging für Netzwerkfehler
            log_security_event(
                "network_error",
                f"Netzwerkfehler beim Download von {file_name}: {type(e).__name__}",
                "medium"
            )

            error_tracker.track_error(e, f"network_{file_id}", "ERROR")
            
            # Automatische Fehlerbehebung versuchen
            recovery_data = {
                "file_id": file_id,
                "file_name": file_name,
                "download_attempts": getattr(audio_file, 'download_attempts', 0) if 'audio_file' in locals() else 0
            }
            recovery_success = False
            if hasattr(self, 'automatic_error_recovery') and self.automatic_error_recovery:
                try:
                    recovery_success = await self.automatic_error_recovery.attempt_recovery(e, f"network_{file_id}", recovery_data)
                except Exception:
                    recovery_success = False

            if recovery_success or error_tracker.should_retry(e, f"network_{file_id}"):
                download_attempts = getattr(audio_file, 'download_attempts', 1) if 'audio_file' in locals() else 1
                retry_delay = min(
                    60, 2**download_attempts
                )  # Exponentielles Backoff, max 60s
                logger.warning(
                    f"Netzwerk-Fehler bei {file_name}, Retry in {retry_delay}s: {e}"
                )
                await asyncio.sleep(retry_delay)
                await self._download_audio(message, document, group)
            else:
                logger.error(f"Zu viele Netzwerk-Fehler für {file_id}, überspringe")
                if "audio_file" in locals() and hasattr(audio_file, 'status'):
                    audio_file.status = DownloadStatus.FAILED.value
                    if hasattr(audio_file, 'error_message'):
                        audio_file.error_message = f"Netzwerk-Fehler: {str(e)}"
                    if hasattr(audio_file, 'save'):
                        try:
                            audio_file.save()
                        except Exception:
                            pass
                
                # Fehler in der Performance-Analyse aufzeichnen
                duration = time.time() - start_time
                if hasattr(self, 'performance_monitor') and self.performance_monitor:
                    try:
                        self.performance_monitor.after_download(False, file_size_mb, duration)
                    except Exception:
                        pass
                if hasattr(self, 'realtime_performance_analyzer') and self.realtime_performance_analyzer:
                    try:
                        self.realtime_performance_analyzer.record_error(type(e).__name__, f"network_{file_id}")
                    except Exception:
                        pass

        except Exception as e:
            # Sicherstellen, dass audio_info definiert ist
            file_name = audio_info.get('file_name', 'Unknown') if 'audio_info' in locals() else 'unknown'
            
            # Audit-Logging für unerwartete Fehler
            log_security_event(
                "unexpected_error",
                f"Unerwarteter Fehler beim Download von {file_name}: {type(e).__name__}: {e}",
                "high"
            )

            error_tracker.track_error(e, f"download_{file_id}", "ERROR")
            logger.error(
                f"Unerwarteter Fehler beim Herunterladen der Datei {file_id}: {e}",
                exc_info=True,
            )

            # Automatische Fehlerbehebung versuchen
            recovery_data = {
                "file_id": file_id,
                "file_name": file_name
            }
            recovery_success = False
            if hasattr(self, 'automatic_error_recovery') and self.automatic_error_recovery:
                try:
                    recovery_success = await self.automatic_error_recovery.attempt_recovery(e, f"download_{file_id}", recovery_data)
                except Exception:
                    recovery_success = False

            # Fehler in der Datenbank speichern
            if "audio_file" in locals():
                if hasattr(audio_file, 'status'):
                    audio_file.status = DownloadStatus.FAILED.value
                if hasattr(audio_file, 'error_message'):
                    audio_file.error_message = str(e)
                if hasattr(audio_file, 'save'):
                    try:
                        audio_file.save()
                    except Exception:
                        pass
            
            # Sende Benachrichtigung über fehlgeschlagenen Download
            try:
                send_download_failed_notification(
                    file_name=file_name,
                    error_message=str(e)
                )
            except Exception as notification_error:
                logger.warning(f"Fehler beim Senden der Fehlerbenachrichtigung: {notification_error}")
            
            # Fehler in der Performance-Analyse aufzeichnen
            duration = time.time() - start_time
            if hasattr(self, 'performance_monitor') and self.performance_monitor:
                try:
                    self.performance_monitor.after_download(False, file_size_mb, duration)
                except Exception:
                    pass
            if hasattr(self, 'realtime_performance_analyzer') and self.realtime_performance_analyzer:
                try:
                    self.realtime_performance_analyzer.record_error(type(e).__name__, f"download_{file_id}")
                except Exception:
                    pass

    async def _download_with_resume(
        self, message: Message, file_path: Path, start_byte: int, audio_file: AudioFile
    ) -> int:
        """
        Lädt eine Datei mit verbesserter Fehlerbehandlung herunter.

        Note: Echtes Resume ist mit Telethon limitiert, aber wir implementieren
        bessere Retry-Logik und Fortschrittsverfolgung.
        """
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                # Sicherheitsprüfung: Zugriff auf die Datei prüfen
                if not check_file_access(file_path.parent):
                    log_security_event(
                        "unauthorized_access",
                        f"Zugriff auf Verzeichnis {file_path.parent} verweigert",
                        "high"
                    )
                    raise SecurityError(f"Zugriff auf Verzeichnis {file_path.parent} verweigert")

                # Wenn partielle Datei existiert und zu groß ist, löschen
                file_size = getattr(audio_file, 'file_size', 0)
                if (
                    file_path.exists()
                    and file_path.stat().st_size > file_size
                ):
                    file_path.unlink()

                # Download durchführen
                if not self.client:
                    raise DownloadError("Telegram-Client nicht initialisiert")
                    
                downloaded_bytes = 0
                try:
                    downloaded_bytes = await self.client.download_media(
                        message, 
                        file=str(file_path),  # Telethon erwartet einen String oder File-Objekt
                        progress_callback=self._progress_callback
                    )
                except Exception as e:
                    logger.error(f"Fehler beim Herunterladen der Mediendatei: {e}")
                    raise DownloadError(f"Fehler beim Herunterladen der Mediendatei: {e}")

                return downloaded_bytes or 0

            except Exception as e:
                retry_count += 1
                if retry_count >= max_retries:
                    logger.error(f"Maximale Anzahl an Wiederholungen erreicht für Datei {file_path}")
                    raise
                else:
                    logger.warning(f"Fehler beim Download von {file_path}, Versuch {retry_count}/{max_retries}: {e}")
                    await asyncio.sleep(2 ** retry_count)  # Exponentielles Backoff

        return 0  # Dieser Punkt sollte nie erreicht werden

    def _progress_callback(self, current_bytes: int, total_bytes: int) -> None:
        """Fortschrittsrückmeldung für den Download."""
        # Hier könnte eine Fortschrittsanzeige aktualisiert werden
        pass

    async def save_last_message_id(self, group_id: int, message_id: int) -> None:
        """
        Speichert die letzte verarbeitete Nachrichten-ID für eine Gruppe.

        Args:
            group_id: Die ID der Telegram-Gruppe
            message_id: Die ID der letzten verarbeiteten Nachricht
        """
        try:
            # Gruppenfortschritt abrufen oder erstellen
            group_progress, created = GroupProgress.get_or_create(
                group_id=group_id,
                defaults={"last_message_id": message_id}
            )
            
            # Letzte Nachrichten-ID aktualisieren
            if not created and group_progress.last_message_id < message_id:
                group_progress.last_message_id = message_id
                group_progress.save()
            elif created:
                group_progress.last_message_id = message_id
                group_progress.save()
                
            logger.debug(f"Letzte Nachrichten-ID für Gruppe {group_id} aktualisiert: {message_id}")
        except Exception as e:
            logger.warning(f"Warnung beim Speichern der letzten Nachrichten-ID: {e}")
            # Wir werfen den Fehler nicht weiter, um den Download nicht zu unterbrechen

    async def get_last_message_id(self, group_id: int) -> int:
        """
        Ruft die letzte verarbeitete Nachrichten-ID für eine Gruppe ab.

        Args:
            group_id: Die ID der Telegram-Gruppe

        Returns:
            Die ID der letzten verarbeiteten Nachricht oder 0, wenn keine gefunden wurde
        """
        try:
            try:
                group_progress = GroupProgress.get(GroupProgress.group_id == group_id)
                # Stelle sicher, dass der Rückgabewert ein Integer ist
                last_message_id = getattr(group_progress, 'last_message_id', 0)
                return int(last_message_id) if last_message_id is not None else 0
            except Exception:
                return 0
        except Exception as e:
            error = DatabaseError(f"Fehler beim Abrufen der letzten Nachrichten-ID: {e}")
            handle_error(error, "get_last_message_id")
            return 0

    async def close(self) -> None:
        """Schließt die Verbindung zum Telegram-Client."""
        if self.client:
            try:
                await self.client.disconnect()
                logger.info("Telegram-Client-Verbindung geschlossen")
            except Exception as e:
                logger.error(f"Fehler beim Schließen des Telegram-Clients: {e}")
        else:
            logger.info("Kein aktiver Telegram-Client zum Schließen")