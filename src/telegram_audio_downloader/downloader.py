"""
Hauptklasse für den Telegram Audio Downloader.
"""

import asyncio
import os
import time
import weakref
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Set
from collections import OrderedDict

from telethon import TelegramClient
from telethon.errors import FloodWaitError, RPCError
from telethon.tl.types import (
    Document,
    DocumentAttributeAudio,
    Message,
    MessageMediaDocument,
)
from tqdm import tqdm

from .models import AudioFile, TelegramGroup, DownloadStatus
from .config import Config
from .logging_config import get_logger
from .error_handling import handle_error
from .utils import sanitize_filename, format_file_size
from .network_optimization import get_optimized_client
from .prefetching import get_prefetch_manager
from .adaptive_parallelism import get_parallelism_manager
from .advanced_memory_management import get_memory_manager
from .automatic_error_recovery import get_error_recovery
from .audit_logging import log_audit_event
from .metrics_export import export_download_metric
from .realtime_performance_analysis import get_performance_analyzer
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
        self, download_dir: str = "downloads", max_concurrent_downloads: int = 3
    ):
        """
        Initialisiert den AudioDownloader.

        Args:
            download_dir: Verzeichnis, in das die Audiodateien heruntergeladen werden sollen
            max_concurrent_downloads: Maximale Anzahl paralleler Downloads
        """
        self.client: Optional[TelegramClient] = None
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.max_concurrent_downloads = max_concurrent_downloads
        
        # Erweiterter Dateinamen-Generator
        self.filename_generator = get_advanced_filename_generator(self.download_dir)
        
        # Adaptive Parallelism Controller
        self.adaptive_parallelism = AdaptiveParallelismController(
            download_dir=self.download_dir,
            initial_concurrent_downloads=max_concurrent_downloads,
            min_concurrent_downloads=1,
            max_concurrent_downloads=10
        )
        
        # Prefetch Manager
        self.prefetch_manager = PrefetchManager(download_dir=self.download_dir)
        
        # Network Optimizer
        self.network_optimizer = NetworkOptimizer(download_dir=self.download_dir)
        
        # Advanced Memory Manager
        self.memory_manager = AdvancedMemoryManager(
            download_dir=self.download_dir,
            max_memory_mb=1024
        )
        
        # Realtime Performance Analyzer
        self.performance_analyzer = RealtimePerformanceAnalyzer(download_dir=self.download_dir)
        
        # Automatic Error Recovery
        self.error_recovery = AutomaticErrorRecovery(download_dir=self.download_dir)
        
        # Neue Sicherheitskomponenten
        self.file_access_control = get_file_access_control()
        self.file_integrity_checker = get_file_integrity_checker()
        self.audit_logger = get_audit_logger()
        
        # Verwende initially die statische Semaphore für Abwärtskompatibilität
        self.download_semaphore = asyncio.Semaphore(max_concurrent_downloads)

        # Performance-Monitor initialisieren
        self.performance_monitor = get_performance_monitor(
            download_dir=self.download_dir, max_memory_mb=1024
        )

        # Datenbank initialisieren
        init_db()

        # Speichereffizienter Cache für bereits heruntergeladene Dateien (max. 50.000 Einträge)
        self._downloaded_files_cache = LRUCache(max_size=50000)
        self._load_downloaded_files()

        # Download-Statistiken
        self.downloads_in_progress = 0
        self.total_downloads = 0
        self.successful_downloads = 0
        self.failed_downloads = 0

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
            self.client = TelegramClient(session_name, int(api_id), api_hash)
            await self.client.start()
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

    def _is_audio_file(self, document: Document) -> bool:
        """Überprüft, ob es sich bei dem Dokument um eine Audiodatei handelt."""
        try:
            # Überprüfe die Dateiendung
            file_ext = Path(document.mime_type or "").suffix.lower()
            if file_ext and file_ext in AUDIO_EXTENSIONS:
                return True

            # Überprüfe die MIME-Type
            if document.mime_type and any(
                audio_type in document.mime_type for audio_type in ["audio", "mpeg"]
            ):
                return True

            # Überprüfe die Attribute
            for attr in document.attributes:
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
            title = getattr(audio_attrs, "title", None)
            performer = getattr(audio_attrs, "performer", None)

            # Verwende den erweiterten Dateinamen-Generator
            metadata = {
                "title": title,
                "artist": performer,
            }
            
            # Generiere den Dateinamen mit dem erweiterten Generator
            filename = self.filename_generator.generate_filename(metadata, file_ext)

            return {
                "file_id": str(document.id),
                "file_unique_id": document.file_reference.hex(),
                "file_name": filename,
                "file_size": document.size,
                "mime_type": document.mime_type or "audio/mpeg",
                "duration": getattr(audio_attrs, "duration", None) if audio_attrs else None,
                "title": title,
                "performer": performer,
            }
        except Exception as e:
            error = DownloadError(f"Fehler beim Extrahieren von Audio-Informationen: {e}")
            handle_error(error, "_extract_audio_info")
            raise error

    async def download_audio_files(
        self, group_name: str, limit: Optional[int] = None
    ) -> None:
        """
        Lädt alle Audiodateien aus der angegebenen Gruppe herunter (parallel).

        Args:
            group_name: Name oder ID der Telegram-Gruppe
            limit: Maximale Anzahl der zu verarbeitenden Nachrichten (optional)
        """
        if not self.client:
            await self.initialize_client()

        try:
            # Gruppe abrufen
            group_entity = await self.client.get_entity(group_name)
            logger.info(
                f"Gruppe gefunden: {group_entity.title} (ID: {group_entity.id})"
            )

            # Gruppeninformationen in der Datenbank speichern
            group, _ = TelegramGroup.get_or_create(
                group_id=group_entity.id,
                defaults={
                    "title": getattr(group_entity, "title", ""),
                    "username": getattr(group_entity, "username", None),
                },
            )

            # Nachrichten abrufen
            logger.info("Sammle Audiodateien...")
            audio_messages = []

            async for message in self.client.iter_messages(group_entity, limit=limit):
                if not hasattr(message, "media") or not isinstance(
                    message.media, MessageMediaDocument
                ):
                    continue

                document = message.media.document
                if not document or not self._is_audio_file(document):
                    continue

                # Prüfe, ob die Datei bereits heruntergeladen wurde
                file_id = str(document.id)
                if file_id in self._downloaded_files_cache:
                    logger.debug(
                        f"Überspringe bereits heruntergeladene Datei: {file_id}"
                    )
                    continue

                audio_messages.append((message, document, group))

            logger.info(f"{len(audio_messages)} neue Audiodateien gefunden")
            self.total_downloads = len(audio_messages)

            # Aufzeichnung in der Performance-Analyse
            self.performance_analyzer.current_metrics.queue_length = len(audio_messages)

            if not audio_messages:
                logger.info("Keine neuen Audiodateien zum Herunterladen gefunden")
                return

            # Parallele Downloads starten
            download_tasks = [
                self._download_audio_concurrent(message, document, group)
                for message, document, group in audio_messages
            ]

            # Alle Downloads parallel ausführen
            results = await asyncio.gather(*download_tasks, return_exceptions=True)

            # Prefetching im Hintergrund starten, wenn verfügbar
            if self.prefetch_manager.should_prefetch():
                asyncio.create_task(self.prefetch_manager.start_prefetching(self))

            # Ergebnisse auswerten
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Download-Fehler: {result}")
                    self.failed_downloads += 1
                else:
                    self.successful_downloads += 1

            logger.info(
                f"Downloads abgeschlossen: {self.successful_downloads} erfolgreich, "
                f"{self.failed_downloads} fehlgeschlagen"
            )

            # Sende Systembenachrichtigung über abgeschlossene Downloads
            if self.successful_downloads > 0 or self.failed_downloads > 0:
                send_system_notification(
                    title="Telegram Audio Downloader",
                    message=f"Downloads abgeschlossen: {self.successful_downloads} erfolgreich, {self.failed_downloads} fehlgeschlagen",
                    timeout=5000
                )

        except Exception as e:
            logger.error(
                f"Fehler beim Herunterladen der Audiodateien: {e}", exc_info=True
            )
            # Sende Fehlerbenachrichtigung
            send_system_notification(
                title="Download-Fehler",
                message=f"Fehler beim Herunterladen: {str(e)}",
                timeout=5000
            )
            raise

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
        self.performance_analyzer.record_download_start()
        
        # Aktualisiere die adaptive Parallelisierung
        await self.adaptive_parallelism.update_parallelism()
        
        # Verwende die adaptive Semaphore
        async with self.adaptive_parallelism.get_semaphore():
            self.downloads_in_progress += 1
            try:
                await self._download_audio(message, document, group)
                return True
            except Exception as e:
                logger.error(f"Fehler beim parallelen Download: {e}")
                # Fehler in der Performance-Analyse aufzeichnen
                self.performance_analyzer.record_error(type(e).__name__, "_download_audio_concurrent")
                return False
            finally:
                self.downloads_in_progress -= 1

    async def _download_audio(
        self, message: Message, document: Document, group: TelegramGroup
    ) -> None:
        """Lädt eine einzelne Audiodatei herunter (mit Resume-Unterstützung)."""
        file_id = str(document.id)
        file_size_mb = document.size / (1024 * 1024)
        start_time = time.time()

        # Performance-Checks vor Download
        if not await self.performance_monitor.before_download(file_size_mb):
            logger.error(f"Performance-Check fehlgeschlagen für {file_id}, überspringe")
            return

        try:
            # Audiodaten extrahieren
            audio_info = self._extract_audio_info(document)

            # Periodische Wartung
            await self.performance_monitor.periodic_maintenance()

            # Speicherwartung durchführen
            await self.memory_manager.perform_memory_maintenance()

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
            self.prefetch_manager.record_download(
                group_id=group.group_id,
                file_extension=Path(audio_info["file_name"]).suffix,
                file_size=audio_info["file_size"],
                file_id=file_id
            )

            # Prüfen, ob bereits vollständig heruntergeladen
            if not created and audio_file.is_downloaded:
                logger.debug(
                    f"Datei bereits heruntergeladen: {audio_info['file_name']}"
                )
                self._downloaded_files_cache.put(file_id, True)
                return

            # Download-Versuch zählen
            audio_file.download_attempts += 1
            audio_file.last_attempt_at = datetime.now()
            audio_file.save()

            # Zielpfad erstellen
            download_path = self.download_dir / audio_info["file_name"]
            download_path = utils.get_unique_filepath(download_path)

            # Partielle Datei-Pfad
            partial_path = download_path.with_suffix(download_path.suffix + ".partial")

            # Prüfen, ob Download fortgesetzt werden kann
            start_byte = 0
            if audio_file.can_resume_download():
                partial_size = Path(audio_file.partial_file_path).stat().st_size
                if partial_size == audio_file.downloaded_bytes:
                    start_byte = partial_size
                    logger.info(
                        f"Setze Download fort ab Byte {start_byte}: {audio_info['file_name']}"
                    )
                else:
                    logger.warning(
                        f"Partielle Datei inkonsistent, starte neu: {audio_info['file_name']}"
                    )
                    audio_file.downloaded_bytes = 0

            # Status aktualisieren
            audio_file.status = DownloadStatus.DOWNLOADING.value
            audio_file.partial_file_path = str(partial_path)
            audio_file.save()

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
            downloaded_bytes = await self._download_with_resume(
                message, partial_path, start_byte, audio_file
            )

            # Prüfen, ob vollständig heruntergeladen
            if downloaded_bytes >= document.size:
                # Datei von partial zu final verschieben
                partial_path.rename(download_path)

                # Checksum berechnen und prüfen
                checksum = utils.calculate_file_hash(download_path, "md5")

                # Erweiterte Metadaten mit mutagen extrahieren
                extended_metadata = utils.extract_audio_metadata(download_path)

                # Datenbank aktualisieren
                audio_file.local_path = str(download_path)
                audio_file.status = DownloadStatus.COMPLETED.value
                audio_file.downloaded_at = datetime.now()
                audio_file.downloaded_bytes = downloaded_bytes
                audio_file.checksum_md5 = checksum
                audio_file.checksum_verified = True
                audio_file.partial_file_path = None

                # Erweiterte Metadaten einfügen (falls nicht bereits vorhanden)
                if not audio_file.title and extended_metadata.get("title"):
                    audio_file.title = extended_metadata["title"]
                if not audio_file.performer and extended_metadata.get("artist"):
                    audio_file.performer = extended_metadata["artist"]
                if not audio_file.duration and extended_metadata.get("duration"):
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

                audio_file.save()

                # In den Cache aufnehmen
                self._downloaded_files_cache.put(file_id, True)

                // Sicherheitsprüfung: Dateiintegrität verifizieren
                if not verify_file_integrity(download_path):
                    log_security_event(
                        "file_integrity_violation",
                        f"Integritätsprüfung für {download_path} fehlgeschlagen",
                        "high"
                    )
                    raise SecurityError(f"Integritätsprüfung für {download_path} fehlgeschlagen")

                // Audit-Logging für erfolgreichen Download
                log_security_event(
                    "download_success",
                    f"Download erfolgreich abgeschlossen: {download_path}",
                    "low"
                )

                // Audit-Logging für Dateiintegrität
                log_security_event(
                    "file_integrity_verified",
                    f"Dateiintegrität von {download_path} bestätigt",
                    "low"
                )

                # Performance-Tracking
                duration = time.time() - start_time
                self.performance_monitor.after_download(True, file_size_mb, duration)
                
                # Geschwindigkeit an den AdaptiveParallelismController übergeben
                if duration > 0:
                    speed_mbps = file_size_mb / duration
                    self.adaptive_parallelism.record_download_speed(speed_mbps)
                
                # Erfolg in der Performance-Analyse aufzeichnen
                self.performance_analyzer.record_download_completion(True, file_size_mb, duration)

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
                audio_file.downloaded_bytes = downloaded_bytes
                audio_file.status = DownloadStatus.FAILED.value
                audio_file.error_message = "Download unvollständig"
                audio_file.save()

                logger.warning(f"Download unvollständig: {audio_info['file_name']}")
                
                # Fehler in der Performance-Analyse aufzeichnen
                duration = time.time() - start_time
                self.performance_analyzer.record_download_completion(False, file_size_mb, duration)

        except FloodWaitError as e:
            log_security_event(
                "flood_wait_error",
                f"FloodWaitError beim Download von {audio_info['file_name']}: {e.seconds} Sekunden",
                "medium"
            )
            log_security_event(
                "flood_wait_error",
                f"FloodWaitError beim Download von {audio_info['file_name']}: {e.seconds} Sekunden",
                "medium"
            )

            # Performance-Monitor über FloodWait informieren
            self.performance_monitor.handle_flood_wait(e.seconds)

            # Wartezeit einhalten
            wait_time = e.seconds
            error_tracker.track_error(e, f"download_{file_id}", "WARNING")
            logger.warning(
                f"FloodWaitError: Warte {wait_time} Sekunden für {audio_info['file_name']}..."
            )
            await asyncio.sleep(wait_time)

            # Performance-Tracking für fehlgeschlagenen Download
            duration = time.time() - start_time
            self.performance_monitor.after_download(False, file_size_mb, duration)
            
            # Automatische Fehlerbehebung versuchen
            recovery_data = {
                "file_id": file_id,
                "file_name": audio_info['file_name'],
                "wait_time": wait_time
            }
            recovery_success = await self.error_recovery.attempt_recovery(e, f"download_{file_id}", recovery_data)
            
            # Fehler in der Performance-Analyse aufzeichnen
            self.performance_analyzer.record_error("FloodWaitError", f"download_{file_id}")

            # Retry nur wenn sinnvoll oder Fehlerbehebung erfolgreich
            if recovery_success or error_tracker.should_retry(e, f"download_{file_id}"):
                await self._download_audio(message, document, group)
            else:
                logger.error(f"Zu viele FloodWait-Fehler für {file_id}, überspringe")

        except (RPCError, ConnectionError) as e:
            # Audit-Logging für Netzwerkfehler
            log_security_event(
                "network_error",
                f"Netzwerkfehler beim Download von {audio_info['file_name']}: {type(e).__name__}",
                "medium"
            )

            error_tracker.track_error(e, f"network_{file_id}", "ERROR")

            # Automatische Fehlerbehebung versuchen
            recovery_data = {
                "file_id": file_id,
                "file_name": audio_info['file_name'],
                "download_attempts": audio_file.download_attempts if 'audio_file' in locals() else 0
            }
            recovery_success = await self.error_recovery.attempt_recovery(e, f"network_{file_id}", recovery_data)

            if recovery_success or error_tracker.should_retry(e, f"network_{file_id}"):
                retry_delay = min(
                    60, 2**audio_file.download_attempts
                )  # Exponential backoff, max 60s
                logger.warning(
                    f"Netzwerk-Fehler bei {audio_info['file_name']}, Retry in {retry_delay}s: {e}"
                )
                await asyncio.sleep(retry_delay)
                await self._download_audio(message, document, group)
            else:
                logger.error(f"Zu viele Netzwerk-Fehler für {file_id}, überspringe")
                if "audio_file" in locals():
                    audio_file.status = DownloadStatus.FAILED.value
                    audio_file.error_message = f"Netzwerk-Fehler: {str(e)}"
                    audio_file.save()
                
                # Fehler in der Performance-Analyse aufzeichnen
                duration = time.time() - start_time
                self.performance_monitor.after_download(False, file_size_mb, duration)
                self.performance_analyzer.record_error(type(e).__name__, f"network_{file_id}")

        except Exception as e:
            # Audit-Logging für unerwartete Fehler
            log_security_event(
                "unexpected_error",
                f"Unerwarteter Fehler beim Download von {audio_info['file_name']}: {type(e).__name__}: {e}",
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
                "file_name": audio_info['file_name'] if 'audio_info' in locals() else 'unknown'
            }
            recovery_success = await self.error_recovery.attempt_recovery(e, f"download_{file_id}", recovery_data)

            # Fehler in der Datenbank speichern
            if "audio_file" in locals():
                audio_file.status = DownloadStatus.FAILED.value
                audio_file.error_message = str(e)
                audio_file.save()
            
            # Sende Benachrichtigung über fehlgeschlagenen Download
            try:
                send_download_failed_notification(
                    file_name=audio_info['file_name'] if 'audio_info' in locals() else 'unknown',
                    error_message=str(e)
                )
            except Exception as notification_error:
                logger.warning(f"Fehler beim Senden der Fehlerbenachrichtigung: {notification_error}")
            
            # Fehler in der Performance-Analyse aufzeichnen
            duration = time.time() - start_time
            self.performance_monitor.after_download(False, file_size_mb, duration)
            self.performance_analyzer.record_error(type(e).__name__, f"download_{file_id}")

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
                if (
                    file_path.exists()
                    and file_path.stat().st_size > audio_file.file_size
                ):
                    file_path.unlink()
                    start_byte = 0

                # Fortschrittsbalken erstellen
                with tqdm(
                    total=audio_file.file_size,
                    initial=start_byte,
                    unit="B",
                    unit_scale=True,
                    unit_divisor=1024,
                    desc=audio_file.file_name[:30],
                    leave=False,
                ) as pbar:

                    downloaded_bytes = start_byte

                    def progress_callback(received_bytes: int, total: int) -> None:
                        nonlocal downloaded_bytes
                        downloaded_bytes = received_bytes
                        pbar.update(received_bytes - pbar.n)

                        # Datenbank periodisch aktualisieren
                        if received_bytes % (1024 * 1024) == 0:  # Alle 1MB
                            audio_file.downloaded_bytes = received_bytes
                            audio_file.save()

                    # Datei herunterladen
                    await self.client.download_media(
                        message, file=file_path, progress_callback=progress_callback
                    )

                    # Finale Größe prüfen
                    if file_path.exists():
                        actual_size = file_path.stat().st_size
                        
                        # Sicherheitsprüfung: Dateiintegrität verifizieren
                        if not verify_file_integrity(file_path):
                            log_security_event(
                                "file_integrity_violation",
                                f"Integritätsprüfung für {file_path} fehlgeschlagen",
                                "high"
                            )
                            raise SecurityError(f"Integritätsprüfung für {file_path} fehlgeschlagen")
                        
                        return actual_size
                    else:
                        return downloaded_bytes

            except FloodWaitError as e:
                # Audit-Logging für FloodWaitError
                log_security_event(
                    "flood_wait_error",
                    f"FloodWaitError beim Download von {audio_file.file_name}: {e.seconds} Sekunden",
                    "medium"
                )

                wait_time = e.seconds
                logger.warning(f"FloodWaitError: Warte {wait_time} Sekunden...")
                await asyncio.sleep(wait_time)
                continue

            except Exception as e:
                // Audit-Logging für Download-Fehler
                log_security_event(
                    "download_error",
                    f"Fehler beim Download von {audio_file.file_name}: {type(e).__name__}: {e}",
                    "medium"
                )

                retry_count += 1
                if retry_count < max_retries:
                    wait_time = 2**retry_count  # Exponential backoff
                    logger.warning(
                        f"Download-Fehler (Versuch {retry_count}/{max_retries}): {e}. "
                        f"Wiederhole in {wait_time} Sekunden..."
                    )
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(
                        f"Download fehlgeschlagen nach {max_retries} Versuchen: {e}"
                    )
                    raise

        return 0

    def _get_unique_filename(self, path: Path) -> Path:
        """Erstellt einen eindeutigen Dateinamen, falls die Datei bereits existiert."""
        if not path.exists():
            return path

        counter = 1
        while True:
            new_path = path.parent / f"{path.stem}_{counter}{path.suffix}"
            if not new_path.exists():
                return new_path
            counter += 1

    async def close(self) -> None:
        """Schließt die Verbindung zum Telegram-Client."""
        if self.client:
            await self.client.disconnect()
            logger.info("Telegram-Client-Verbindung geschlossen")

    def show_downloads_in_file_manager(self) -> bool:
        """
        Zeigt das Download-Verzeichnis im Dateimanager an.
        
        Returns:
            True, wenn der Dateimanager geöffnet wurde, False sonst
        """
        try:
            return show_in_default_file_manager(self.download_dir)
        except Exception as e:
            logger.error(f"Fehler beim Öffnen des Download-Verzeichnisses: {e}")
            send_system_notification(
                title="Fehler",
                message=f"Fehler beim Öffnen des Download-Verzeichnisses: {str(e)}",
                timeout=3000
            )
            return False

    async def download_file(self, file_id: str, file_name: str, file_size: int, 
                           group_id: int, message_id: int, 
                           title: Optional[str] = None, 
                           performer: Optional[str] = None) -> bool:
        """
        Lädt eine Datei herunter.
        
        Args:
            file_id: Telegram-Datei-ID
            file_name: Name der Datei
            file_size: Größe der Datei in Bytes
            group_id: ID der Telegram-Gruppe
            message_id: ID der Nachricht
            title: Optionaler Titel
            performer: Optionaler Interpret
            
        Returns:
            True, wenn der Download erfolgreich war
        """
        // Sicherheitsprüfung: Zugriff auf das Download-Verzeichnis prüfen
        if not check_file_access(self.download_dir):
            log_security_event(
                "unauthorized_access",
                f"Zugriff auf Download-Verzeichnis {self.download_dir} verweigert",
                "high"
            )
            raise SecurityError(f"Zugriff auf Download-Verzeichnis {self.download_dir} verweigert")

        # Audit-Logging für Download-Start
        log_security_event(
            "download_start",
            f"Starte Download von {file_name}",
            "low"
        )

        # Prüfe, ob ein neuer Download gestartet werden kann
        if not can_start_new_download():
            logger.warning(f"Maximale Anzahl gleichzeitiger Downloads erreicht, warte auf {file_name}")
            # Warte, bis ein Slot frei wird
            while not can_start_new_download():
                await asyncio.sleep(1)
        
        # Registriere den Download-Start
        register_download_start(file_id)
        
        try:
            # Hole den Bandwidth-Controller und passe Einstellungen an
            bandwidth_controller = get_bandwidth_controller(self.config)
            adjust_bandwidth_settings()
            current_settings = bandwidth_controller.get_current_settings()
            
            # Verwende die angepassten Einstellungen
            chunk_size = current_settings.chunk_size
            timeout = current_settings.timeout_seconds
            
            # Erstelle oder aktualisiere den AudioFile-Datensatz
            audio_file, created = AudioFile.get_or_create(
                file_id=file_id,
                defaults={
                    'file_name': file_name,
                    'file_size': file_size,
                    'title': title,
                    'performer': performer,
                    'group_id': group_id,
                    'status': DownloadStatus.PENDING.value,
                    'download_attempts': 0
                }
            )
            
            if not created:
                # Aktualisiere vorhandenen Datensatz
                audio_file.file_name = file_name
                audio_file.file_size = file_size
                audio_file.title = title
                audio_file.performer = performer
                audio_file.group_id = group_id
                audio_file.status = DownloadStatus.PENDING.value
                audio_file.save()
            
            # Startzeit für Geschwindigkeitsmessung
            start_time = time.time()
            
            # Hole den Telegram-Client
            client = get_optimized_client()
            
            # Sicherheitsprüfung: Zugriff auf das Download-Verzeichnis prüfen
            if not check_file_access(self.download_dir):
                log_security_event(
                    "unauthorized_access",
                    f"Zugriff auf Download-Verzeichnis {self.download_dir} verweigert",
                    "high"
                )
                raise SecurityError(f"Zugriff auf Download-Verzeichnis {self.download_dir} verweigert")
            
            # Erstelle den vollständigen Dateipfad
            full_path = self.download_dir / file_name
            
            # Sicherheitsprüfung: Zugriff auf die Datei prüfen
            if not check_file_access(full_path.parent):
                log_security_event(
                    "unauthorized_access",
                    f"Zugriff auf Verzeichnis {full_path.parent} verweigert",
                    "high"
                )
                raise SecurityError(f"Zugriff auf Verzeichnis {full_path.parent.parent} verweigert")
            
            # Lade Resume-Informationen
            resume_info = load_file_resume_state(file_id, full_path, file_size)
            
            # Prüfe, ob der Download wiederaufgenommen werden kann
            resume_download = can_resume_download(file_id) and resume_info.downloaded_bytes > 0
            
            if resume_download:
                logger.info(f"Setze Download von {file_name} bei {format_file_size(resume_info.downloaded_bytes)} fort")
                log_audit_event("download_resume", f"Fortsetzung des Downloads von {file_name}", {
                    "file_id": file_id,
                    "resumed_bytes": resume_info.downloaded_bytes
                })
            
            # Öffne die Datei im richtigen Modus
            file_mode = "ab" if resume_download else "wb"
            
            # Sichere Dateioperation durchführen
            def open_file():
                return open(full_path, file_mode)
            
            f = secure_file_operation(open_file)
            
            # Setze den Dateizeiger ans Ende, falls wir im Anhäng-Modus sind
            if resume_download:
                f.seek(0, 2)  # Gehe ans Ende der Datei
            
            # Hole den aktuellen Dateizeiger (für Resume-Offset)
            start_offset = f.tell() if resume_download else 0
            
            # Aktualisiere den AudioFile-Datensatz mit dem Start-Offset
            audio_file.resume_offset = start_offset
            audio_file.download_attempts += 1
            audio_file.status = DownloadStatus.DOWNLOADING.value
            audio_file.save()
            
            try:
                # Lade die Datei herunter
                async def progress_callback(current, total):
                    # Aktualisiere die Resume-Informationen
                    update_file_resume_info(file_id, start_offset + current)
                    
                    # Aktualisiere die Performance-Analyse
                    analyzer = get_performance_analyzer()
                    analyzer.record_download_progress(file_id, current, total)
                    
                    # Logge den Fortschritt alle 10%
                    if total > 0 and current % (total // 10) == 0:
                        progress_percent = (current / total) * 100
                        logger.info(f"Download-Fortschritt für {file_name}: {progress_percent:.1f}%")
                
                # Führe den Download durch
                await client.download_media(
                    message_id,
                    output_file=f,
                    progress_callback=progress_callback
                )
                
                // Sicherheitsprüfung: Dateiintegrität verifizieren
                if not verify_file_integrity(full_path):
                    log_security_event(
                        "file_integrity_violation",
                        f"Integritätsprüfung für {full_path} fehlgeschlagen",
                        "high"
                    )
                    raise SecurityError(f"Integritätsprüfung für {full_path} fehlgeschlagen")
                
                // Audit-Logging für Dateiintegrität
                log_security_event(
                    "file_integrity_verified",
                    f"Dateiintegrität von {full_path} bestätigt",
                    "low"
                )
                
                # Berechne die Download-Geschwindigkeit
                end_time = time.time()
                time_elapsed = end_time - start_time
                total_bytes = full_path.stat().st_size if full_path.exists() else 0
                update_download_speed(file_id, total_bytes, time_elapsed)
                
                # Aktualisiere die Resume-Informationen nach erfolgreichem Download
                save_file_resume_state(file_id)
                
                # Aktualisiere den AudioFile-Datensatz
                audio_file.downloaded_at = datetime.now()
                audio_file.status = DownloadStatus.COMPLETED.value
                audio_file.error_message = None
                audio_file.resume_offset = 0  # Zurücksetzen nach erfolgreichem Download
                audio_file.resume_checksum = None  # Zurücksetzen nach erfolgreichem Download
                audio_file.save()
                
                logger.info(f"Download von {file_name} erfolgreich abgeschlossen")
                log_audit_event("download_success", f"Download von {file_name} abgeschlossen", {
                    "file_id": file_id,
                    "file_size": file_size
                })
                
                // Audit-Logging für erfolgreichen Download
                log_security_event(
                    "download_success",
                    f"Download erfolgreich abgeschlossen: {file_name}",
                    "low"
                )
                
                # Exportiere die Download-Metrik
                export_download_metric("success", file_size)
                
                # Bereinige die Resume-Informationen
                cleanup_file_resume_info(file_id)
                
                return True
                
            except Exception as e:
                // Audit-Logging für Download-Fehler
                log_security_event(
                    "download_error",
                    f"Fehler beim Download von {file_name}: {type(e).__name__}: {e}",
                    "medium"
                )
                
                // Sicherheitsprüfung: Dateiintegrität verifizieren
                if full_path.exists() and not verify_file_integrity(full_path):
                    log_security_event(
                        "file_integrity_violation",
                        f"Integritätsprüfung für {full_path} nach Fehler fehlgeschlagen",
                        "high"
                    )
                
                # Speichere den Fehlerzustand
                save_file_resume_state(file_id)
                
                # Aktualisiere den AudioFile-Datensatz mit dem Fehler
                audio_file.status = DownloadStatus.FAILED.value
                audio_file.error_message = str(e)
                audio_file.save()
                
                logger.error(f"Fehler beim Download von {file_name}: {e}")
                log_audit_event("download_error", f"Fehler beim Download von {file_name}", {
                    "file_id": file_id,
                    "error": str(e)
                })
                
                # Exportiere die Download-Metrik
                export_download_metric("failure", file_size)
                
                # Prüfe, ob eine Wiederholung möglich ist
                retry_count = increment_file_retry_count(file_id)
                max_retries = current_settings.max_retries
                
                if retry_count < max_retries:
                    logger.info(f"Versuche erneuten Download von {file_name} (Versuch {retry_count + 1}/{max_retries})")
                    log_audit_event("download_retry", f"Erneuter Download-Versuch von {file_name}", {
                        "file_id": file_id,
                        "retry_count": retry_count + 1
                    })
                    
                    # Audit-Logging für Download-Wiederholung
                    log_security_event(
                        "download_retry",
                        f"Erneuter Download-Versuch von {file_name} (Versuch {retry_count + 1}/{max_retries})",
                        "low"
                    )
                    
                    # Warte etwas vor der Wiederholung
                    await asyncio.sleep(current_settings.retry_delay * (retry_count + 1))
                    
                    # Rekursiver Aufruf für die Wiederholung
                    return await self.download_file(file_id, file_name, file_size, group_id, message_id, title, performer)
                else:
                    logger.error(f"Maximale Wiederholungsversuche für {file_name} erreicht")
                    log_audit_event("download_max_retries", f"Maximale Wiederholungen für {file_name} erreicht", {
                        "file_id": file_id,
                        "max_retries": max_retries
                    })
                    
                    # Audit-Logging für maximale Wiederholungen erreicht
                    log_security_event(
                        "download_max_retries",
                        f"Maximale Wiederholungen für {file_name} erreicht",
                        "medium"
                    )
                    
                    # Setze die Resume-Informationen zurück
                    reset_file_resume_info(file_id)
                    
                    return False
        
        except Exception as e:
            handle_error(e, f"Fehler beim Download von {file_name}")
            log_audit_event("download_exception", f"Schwerwiegender Fehler beim Download von {file_name}", {
                "file_id": file_id,
                "error": str(e)
            })
            export_download_metric("exception", 0)
            
            # Audit-Logging für schwerwiegenden Fehler
            log_security_event(
                "download_exception",
                f"Schwerwiegender Fehler beim Download von {file_name}: {type(e).__name__}: {e}",
                "high"
            )
            
            return False
        finally:
            # Registriere das Ende des Downloads
            register_download_end(file_id)
            
            // Audit-Logging für Download-Ende
            log_security_event(
                "download_end",
                f"Download von {file_name} beendet",
                "low"
            )
