"""
🎵 Telegram Audio Downloader

A powerful, asynchronous Python tool for downloading and managing audio files 
from Telegram channels and groups with performance monitoring, fuzzy search, 
and Docker support.

Features:
- ⚡ Asynchronous downloads with rate limiting
- 🔍 Advanced fuzzy search and filtering
- 🎵 Audio metadata extraction and management
- 📊 Performance monitoring and metrics
- 🐳 Docker support with multi-stage builds
- 🛡️ Robust error handling and retry mechanisms
- 💾 SQLite database for download tracking
- 🎨 Rich CLI interface with progress bars

Author: Elpablo777
License: MIT
Repository: https://github.com/Elpablo777/Telegram-Audio-Downloader
"""

__version__ = "1.0.0"
__author__ = "Elpablo777"
__email__ = "hannover84@msn.com"
__license__ = "MIT"
__url__ = "https://github.com/Elpablo777/Telegram-Audio-Downloader"
__description__ = "🎵 A powerful, asynchronous Python tool for downloading audio files from Telegram"

# Version info tuple for programmatic access
VERSION_INFO = tuple(map(int, __version__.split('.')))

# Package metadata
__all__ = [
    "__version__",
    "__author__", 
    "__email__",
    "__license__",
    "__url__",
    "__description__",
    "VERSION_INFO",
]

# Import main modules for easier access
try:
    from .cli import main as cli_main
    from .downloader import TelegramAudioDownloader
    from .config import Config
    from .utils import sanitize_filename, format_file_size
    
    __all__.extend([
        "cli_main",
        "TelegramAudioDownloader", 
        "Config",
        "sanitize_filename",
        "format_file_size",
    ])
except ImportError:
    # Handle import errors gracefully during installation
    pass

def get_version():
    """Get the current version string."""
    return __version__

def get_version_info():
    """Get version info as a tuple.""" 
    return VERSION_INFO