"""
Telegram Audio Downloader

Ein leistungsstarkes Tool zum Herunterladen und Verwalten von Audiodateien aus Telegram-Gruppen.
"""

__version__ = "0.1.0"

from .downloader import AudioDownloader
from .database import init_db, close_db
from .models import AudioFile, DownloadStatus
from . import utils

__all__ = ["AudioDownloader", "init_db", "close_db", "AudioFile", "DownloadStatus", "utils"]
