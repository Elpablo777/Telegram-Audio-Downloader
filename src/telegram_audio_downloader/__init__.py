"""
Telegram Audio Downloader

Ein leistungsstarkes Tool zum Herunterladen und Verwalten von Audiodateien aus Telegram-Gruppen.
"""

__version__ = "1.0.0"
__author__ = "Elpablo777"
__email__ = "hannover84@msn.com"
__description__ = "Ein leistungsstarker, asynchroner Python-Bot zum Herunterladen und Verwalten von Audiodateien aus Telegram-Gruppen"

from .downloader import AudioDownloader
from .database import init_db, close_db
from .models import AudioFile, DownloadStatus, TelegramGroup
from . import utils

__all__ = [
    "AudioDownloader", 
    "init_db", 
    "close_db", 
    "AudioFile", 
    "DownloadStatus", 
    "TelegramGroup",
    "utils",
    "__version__",
    "__author__",
    "__email__",
]
