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

from .error_handling import (
    AuthenticationError,
    ConfigurationError,
    DatabaseError,
    DownloadError,
    FileOperationError,
    NetworkError,
    TelegramAPIError,
    handle_error,
)
from . import utils
from .database import init_db
from .logging_config import get_error_tracker, get_logger
from .models import AudioFile, DownloadStatus, TelegramGroup
from .performance import get_performance_monitor

# Logger und Error-Tracker initialisieren
logger = get_logger(__name__)
error_tracker = get_error_tracker()

# Unterstützte Audioformate
AUDIO_EXTENSIONS = {".mp3", ".m4a", ".ogg", ".flac", ".wav", ".opus"}


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

            # Generiere einen Dateinamen
            filename = f"audio_{document.id}{file_ext}"

            # Extrahiere Metadaten
            title = getattr(audio_attrs, "title", None)
            performer = getattr(audio_attrs, "performer", None)

            # Wenn Titel und Interpret vorhanden sind, verwende sie für den Dateinamen
            if title and performer:
                filename = f"{performer} - {title}{file_ext}"
            elif title:
                filename = f"{title}{file_ext}"

            # Ersetze ungültige Zeichen im Dateinamen
            filename = "".join(c if c.isalnum() or c in " .-_" else "_" for c in filename)

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

        except Exception as e:
            logger.error(
                f"Fehler beim Herunterladen der Audiodateien: {e}", exc_info=True
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
        async with self.download_semaphore:
            self.downloads_in_progress += 1
            try:
                await self._download_audio(message, document, group)
                return True
            except Exception as e:
                logger.error(f"Fehler beim parallelen Download: {e}")
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

            # Datenbankeintrag abrufen oder erstellen
            audio_file, created = AudioFile.get_or_create(
                file_id=file_id,
                defaults={
                    **audio_info,
                    "group": group,
                    "status": DownloadStatus.PENDING.value,
                },
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
                    audio_file.duration = int(extended_metadata["duration"])

                audio_file.save()

                # In den Cache aufnehmen
                self._downloaded_files_cache.put(file_id, True)

                # Performance-Tracking
                duration = time.time() - start_time
                self.performance_monitor.after_download(True, file_size_mb, duration)

                logger.info(f"Download erfolgreich: {download_path} ({duration:.2f}s)")
            else:
                # Partieller Download
                audio_file.downloaded_bytes = downloaded_bytes
                audio_file.status = DownloadStatus.FAILED.value
                audio_file.error_message = "Download unvollständig"
                audio_file.save()

                logger.warning(f"Download unvollständig: {audio_info['file_name']}")

        except FloodWaitError as e:
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

            # Retry nur wenn sinnvoll
            if error_tracker.should_retry(e, f"download_{file_id}"):
                await self._download_audio(message, document, group)
            else:
                logger.error(f"Zu viele FloodWait-Fehler für {file_id}, überspringe")

        except (RPCError, ConnectionError) as e:
            error_tracker.track_error(e, f"network_{file_id}", "ERROR")

            if error_tracker.should_retry(e, f"network_{file_id}"):
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

        except Exception as e:
            error_tracker.track_error(e, f"download_{file_id}", "ERROR")
            logger.error(
                f"Unerwarteter Fehler beim Herunterladen der Datei {file_id}: {e}",
                exc_info=True,
            )

            # Fehler in der Datenbank speichern
            if "audio_file" in locals():
                audio_file.status = DownloadStatus.FAILED.value
                audio_file.error_message = str(e)
                audio_file.save()

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
                        return actual_size
                    else:
                        return downloaded_bytes

            except FloodWaitError as e:
                wait_time = e.seconds
                logger.warning(f"FloodWaitError: Warte {wait_time} Sekunden...")
                await asyncio.sleep(wait_time)
                continue

            except Exception as e:
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