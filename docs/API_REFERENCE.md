# 📚 API Reference - Telegram Audio Downloader

**Version:** 1.0.0  
**Updated:** 2024-01-20  
**Target Audience:** Developers, Advanced Users

## 📋 Table of Contents

1. [Core Classes](#core-classes)
2. [AudioDownloader API](#audiodownloader-api)
3. [Database Models](#database-models)
4. [Performance Monitoring](#performance-monitoring)
5. [Logging System](#logging-system)
6. [Error Handling](#error-handling)
7. [Code Examples](#code-examples)
8. [Best Practices](#best-practices)

---

## 🏗️ Core Classes

### AudioDownloader

The main class for downloading audio files from Telegram groups.

```python
from telegram_audio_downloader.downloader import AudioDownloader

class AudioDownloader:
    def __init__(
        self,
        download_dir: str = "downloads",
        max_concurrent_downloads: int = 3,
        rate_limit_delay: float = 1.0,
        session_name: str = "default"
    )
```

**Parameters:**
- `download_dir`: Directory for downloaded files
- `max_concurrent_downloads`: Maximum parallel downloads
- `rate_limit_delay`: Delay between API calls (seconds)
- `session_name`: Telegram session identifier

#### Methods

##### `async initialize_client()`

Initialize the Telegram client connection.

```python
downloader = AudioDownloader()
await downloader.initialize_client()
```

**Raises:**
- `TelegramAuthError`: Authentication failed
- `ConnectionError`: Network connection issues

##### `async download_audio_files()`

Download audio files from a Telegram group.

```python
async def download_audio_files(
    self,
    group_identifier: str,
    limit: Optional[int] = None,
    file_types: List[str] = ["mp3", "m4a", "wav", "flac"],
    skip_existing: bool = True,
    quality_filter: Optional[str] = None
) -> Dict[str, Any]
```

**Parameters:**
- `group_identifier`: Group username (@group) or ID
- `limit`: Maximum files to download
- `file_types`: Allowed audio file extensions
- `skip_existing`: Skip already downloaded files
- `quality_filter`: Quality threshold (e.g., "high", "medium")

**Returns:**
```python
{
    "completed": 15,
    "failed": 2,
    "skipped": 3,
    "total_size": 157286400,  # bytes
    "duration": 45.2,         # seconds
    "files": [
        {
            "file_name": "song.mp3",
            "file_size": 5242880,
            "download_path": "/downloads/group_name/song.mp3",
            "metadata": {
                "title": "Song Title",
                "artist": "Artist Name",
                "duration": 180
            }
        }
    ],
    "errors": []
}
```

##### `async search_messages()`

Search for audio messages in a group.

```python
async def search_messages(
    self,
    group_identifier: str,
    query: Optional[str] = None,
    limit: int = 100,
    filter_options: Optional[Dict] = None
) -> List[Dict[str, Any]]
```

**Filter Options:**
```python
filter_options = {
    "min_duration": 30,      # seconds
    "max_duration": 600,     # seconds
    "min_size": 1048576,     # bytes (1MB)
    "max_size": 52428800,    # bytes (50MB)
    "file_types": ["mp3", "m4a"],
    "date_from": "2024-01-01",
    "date_to": "2024-12-31"
}
```

##### `async get_group_info()`

Get detailed information about a Telegram group.

```python
async def get_group_info(
    self,
    group_identifier: str
) -> Dict[str, Any]
```

**Returns:**
```python
{
    "id": 1234567890,
    "title": "Music Group",
    "username": "music_group",
    "members_count": 5432,
    "description": "Group description",
    "is_public": True,
    "created_date": "2023-01-15T10:30:00Z",
    "audio_count": 1250,
    "total_size": 10737418240  # bytes
}
```

---

## 📊 Database Models

### AudioFile

Represents a downloaded audio file in the database.

```python
from telegram_audio_downloader.models import AudioFile

class AudioFile(BaseModel):
    file_id: str               # Telegram file ID
    file_unique_id: str        # Unique identifier
    file_name: str             # Original filename
    file_size: int             # File size in bytes
    mime_type: str             # MIME type (e.g., "audio/mpeg")
    duration: Optional[int]    # Duration in seconds
    title: Optional[str]       # Song title
    performer: Optional[str]   # Artist name
    local_path: Optional[str]  # Local file path
    download_date: datetime    # When downloaded
    status: str                # DownloadStatus enum
    metadata: Optional[Dict]   # Additional metadata
```

**Usage Examples:**

```python
# Query all downloaded files
all_files = AudioFile.select()

# Search by title
files = AudioFile.select().where(
    AudioFile.title.contains("song")
)

# Get files by status
completed = AudioFile.select().where(
    AudioFile.status == DownloadStatus.COMPLETED.value
)

# Get file statistics
from peewee import fn
stats = AudioFile.select(
    fn.COUNT(AudioFile.id).alias('count'),
    fn.SUM(AudioFile.file_size).alias('total_size'),
    fn.AVG(AudioFile.duration).alias('avg_duration')
).scalar()
```

### TelegramGroup

Represents a Telegram group/channel.

```python
class TelegramGroup(BaseModel):
    group_id: int              # Telegram group ID
    title: str                 # Group title
    username: Optional[str]    # Group username
    description: Optional[str] # Group description
    member_count: Optional[int] # Number of members
    created_date: datetime     # When added to database
    last_updated: datetime     # Last scan date
    is_active: bool           # Currently active
```

---

## 📈 Performance Monitoring

### PerformanceMonitor

Monitor and track download performance.

```python
from telegram_audio_downloader.performance import get_performance_monitor

monitor = get_performance_monitor()

# Track download metrics
monitor.downloads_in_progress += 1
monitor.successful_downloads += 1
monitor.failed_downloads += 1

# Get performance report
report = monitor.get_performance_report()
```

**Performance Report Structure:**
```python
{
    "downloads": {
        "completed": 150,
        "failed": 5,
        "in_progress": 2,
        "success_rate": 96.8
    },
    "performance": {
        "avg_download_speed": 1250000,  # bytes/second
        "avg_file_size": 5242880,       # bytes
        "total_downloaded": 786432000   # bytes
    },
    "resources": {
        "memory_usage": 256.5,          # MB
        "cpu_usage": 15.2,              # percent
        "disk_space_free": 50000000000  # bytes
    },
    "errors": {
        "network_errors": 2,
        "api_errors": 1,
        "file_errors": 2
    }
}
```

### Memory Management

```python
from telegram_audio_downloader.performance import MemoryManager

memory_manager = MemoryManager()

# Monitor memory usage
usage = memory_manager.get_memory_usage()
print(f"Current usage: {usage['current_mb']}MB")

# Force garbage collection
memory_manager.cleanup()

# Check if memory limit exceeded
if memory_manager.is_memory_limit_exceeded():
    memory_manager.emergency_cleanup()
```

### Rate Limiting

```python
from telegram_audio_downloader.performance import RateLimiter

rate_limiter = RateLimiter(
    calls_per_second=1.0,
    burst_limit=5
)

# Use with async operations
async with rate_limiter:
    result = await telegram_operation()
```

---

## 📝 Logging System

### TelegramAudioLogger

Advanced logging with performance tracking.

```python
from telegram_audio_downloader.logging_config import get_logger

logger = get_logger()

# Performance logging
logger.log_performance(
    operation="download_batch",
    duration=45.2,
    details={
        "files_processed": 10,
        "total_size": 52428800,
        "average_speed": 1250000
    }
)

# Download progress logging
logger.log_download_progress(
    file_name="song.mp3",
    progress=75.5,
    speed=1200000.0
)

# API error logging
logger.log_api_error(
    operation="get_messages",
    error=api_exception,
    retry_count=2
)

# System information logging
logger.log_system_info()
```

### Error Tracking

```python
from telegram_audio_downloader.logging_config import get_error_tracker

error_tracker = get_error_tracker()

# Track errors with context
error_tracker.track_error(
    error=exception,
    context="download_operation",
    severity="ERROR"
)

# Get error summary
summary = error_tracker.get_error_summary()
print(f"Total errors: {summary['total']}")
print(f"Error types: {summary['by_type']}")

# Check retry recommendations
should_retry = error_tracker.should_retry(
    error=exception,
    context="api_call",
    max_retries=3
)
```

---

## 🛡️ Error Handling

### Custom Exceptions

```python
from telegram_audio_downloader.exceptions import (
    TelegramAuthError,
    DownloadError,
    ValidationError,
    RateLimitError
)

try:
    await downloader.download_audio_files("@group")
except TelegramAuthError as e:
    print(f"Authentication failed: {e}")
except DownloadError as e:
    print(f"Download failed: {e}")
except RateLimitError as e:
    print(f"Rate limit exceeded: {e}")
    await asyncio.sleep(e.retry_after)
```

### Error Recovery Patterns

```python
import asyncio
from typing import Optional

async def download_with_retry(
    downloader: AudioDownloader,
    group: str,
    max_retries: int = 3,
    backoff_factor: float = 2.0
) -> Optional[Dict]:
    """Download with exponential backoff retry."""
    
    for attempt in range(max_retries + 1):
        try:
            return await downloader.download_audio_files(group)
        except RateLimitError as e:
            if attempt == max_retries:
                raise
            
            wait_time = backoff_factor ** attempt
            logger.warning(f"Rate limited. Retrying in {wait_time}s")
            await asyncio.sleep(wait_time)
        
        except DownloadError as e:
            if attempt == max_retries:
                raise
            
            logger.warning(f"Download failed. Attempt {attempt + 1}/{max_retries}")
            await asyncio.sleep(1.0)
    
    return None
```

---

## 💡 Code Examples

### Basic Usage

```python
import asyncio
from telegram_audio_downloader.downloader import AudioDownloader

async def basic_download():
    """Basic download example."""
    
    downloader = AudioDownloader(
        download_dir="./music",
        max_concurrent_downloads=3
    )
    
    try:
        # Initialize connection
        await downloader.initialize_client()
        
        # Download from group
        result = await downloader.download_audio_files(
            group_identifier="@music_group",
            limit=10
        )
        
        print(f"Downloaded {result['completed']} files")
        print(f"Total size: {result['total_size']} bytes")
        
    finally:
        await downloader.close()

# Run the example
asyncio.run(basic_download())
```

### Advanced Filtering

```python
async def advanced_download():
    """Advanced download with filtering."""
    
    downloader = AudioDownloader()
    await downloader.initialize_client()
    
    # Custom filter options
    filter_options = {
        "min_duration": 60,      # At least 1 minute
        "max_duration": 600,     # Max 10 minutes
        "min_size": 2097152,     # At least 2MB
        "file_types": ["mp3", "m4a"],
        "date_from": "2024-01-01"
    }
    
    # Search first
    messages = await downloader.search_messages(
        group_identifier="@music_group",
        query="jazz",
        filter_options=filter_options
    )
    
    print(f"Found {len(messages)} matching files")
    
    # Download with quality filter
    result = await downloader.download_audio_files(
        group_identifier="@music_group",
        limit=50,
        quality_filter="high",
        skip_existing=True
    )
    
    await downloader.close()
```

### Batch Processing

```python
async def batch_process_groups():
    """Process multiple groups efficiently."""
    
    groups = ["@group1", "@group2", "@group3"]
    downloader = AudioDownloader(max_concurrent_downloads=5)
    
    await downloader.initialize_client()
    
    results = {}
    
    for group in groups:
        print(f"Processing {group}...")
        
        try:
            result = await downloader.download_audio_files(
                group_identifier=group,
                limit=100
            )
            results[group] = result
            
            # Log progress
            print(f"{group}: {result['completed']} files downloaded")
            
        except Exception as e:
            print(f"{group}: Error - {e}")
            results[group] = {"error": str(e)}
    
    await downloader.close()
    return results
```

### Custom Metadata Processing

```python
from telegram_audio_downloader.utils import extract_metadata

async def download_with_metadata():
    """Download and process metadata."""
    
    downloader = AudioDownloader()
    await downloader.initialize_client()
    
    result = await downloader.download_audio_files("@music_group")
    
    # Process downloaded files
    for file_info in result['files']:
        file_path = file_info['download_path']
        
        # Extract detailed metadata
        metadata = extract_metadata(file_path)
        
        # Update database with metadata
        audio_file = AudioFile.get(
            AudioFile.local_path == file_path
        )
        audio_file.metadata = metadata
        audio_file.save()
        
        print(f"Processed: {metadata.get('title', 'Unknown')}")
    
    await downloader.close()
```

---

## 🎯 Best Practices

### 1. Connection Management

```python
# ✅ Good: Use context manager pattern
async def good_connection():
    downloader = AudioDownloader()
    try:
        await downloader.initialize_client()
        # ... operations ...
    finally:
        await downloader.close()

# ✅ Better: Create reusable connection class
class DownloaderContext:
    def __init__(self, **kwargs):
        self.downloader = AudioDownloader(**kwargs)
    
    async def __aenter__(self):
        await self.downloader.initialize_client()
        return self.downloader
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.downloader.close()

# Usage
async with DownloaderContext() as downloader:
    result = await downloader.download_audio_files("@group")
```

### 2. Error Handling

```python
# ✅ Good: Comprehensive error handling
async def robust_download(group: str):
    try:
        async with DownloaderContext() as downloader:
            return await downloader.download_audio_files(group)
    
    except TelegramAuthError:
        logger.error("Authentication failed. Check API credentials.")
        raise
    
    except RateLimitError as e:
        logger.warning(f"Rate limited. Retry after {e.retry_after}s")
        await asyncio.sleep(e.retry_after)
        return await robust_download(group)  # Retry once
    
    except DownloadError as e:
        logger.error(f"Download failed: {e}")
        return {"completed": 0, "failed": 1, "error": str(e)}
    
    except Exception as e:
        logger.exception("Unexpected error occurred")
        raise
```

### 3. Performance Optimization

```python
# ✅ Good: Monitor and optimize performance
async def optimized_download():
    monitor = get_performance_monitor()
    
    downloader = AudioDownloader(
        max_concurrent_downloads=5,  # Adjust based on system
        rate_limit_delay=0.5        # Balance speed vs API limits
    )
    
    async with DownloaderContext() as downloader:
        # Monitor memory before large operations
        if monitor.is_memory_limit_exceeded():
            monitor.emergency_cleanup()
        
        result = await downloader.download_audio_files(
            "@large_group",
            limit=1000
        )
        
        # Log performance metrics
        report = monitor.get_performance_report()
        logger.info(f"Download rate: {report['performance']['avg_download_speed']} bytes/s")
    
    return result
```

### 4. Database Optimization

```python
# ✅ Good: Use transactions for bulk operations
from telegram_audio_downloader.database import get_database

def bulk_update_metadata():
    db = get_database()
    
    with db.atomic():  # Transaction for better performance
        for audio_file in AudioFile.select().where(
            AudioFile.metadata.is_null()
        ):
            metadata = extract_metadata(audio_file.local_path)
            audio_file.metadata = metadata
            audio_file.save()
```

### 5. Configuration Management

```python
# ✅ Good: Centralized configuration
from dataclasses import dataclass
from typing import Optional

@dataclass
class DownloadConfig:
    download_dir: str = "downloads"
    max_concurrent: int = 3
    rate_limit: float = 1.0
    session_name: str = "default"
    quality_filter: Optional[str] = None
    file_types: list = None
    
    def __post_init__(self):
        if self.file_types is None:
            self.file_types = ["mp3", "m4a", "wav", "flac"]

# Usage
config = DownloadConfig(
    download_dir="./music",
    max_concurrent=5,
    quality_filter="high"
)

downloader = AudioDownloader(
    download_dir=config.download_dir,
    max_concurrent_downloads=config.max_concurrent,
    rate_limit_delay=config.rate_limit
)
```

---

## 📚 Additional Resources

- **[Installation Guide](INSTALLATION.md)** - Setup and configuration
- **[CLI Reference](CLI_REFERENCE.md)** - Command-line usage
- **[Tutorials](TUTORIALS.md)** - Step-by-step guides
- **[Troubleshooting](TROUBLESHOOTING.md)** - Common issues and solutions
- **[Performance Guide](PERFORMANCE.md)** - Optimization tips
- **[Contributing](../CONTRIBUTING.md)** - Development guidelines

---

## 🆘 Support

- **GitHub Issues:** [Report bugs and request features](https://github.com/Elpablo777/Telegram-Audio-Downloader/issues)
- **Discussions:** [Community discussions](https://github.com/Elpablo777/Telegram-Audio-Downloader/discussions)
- **Wiki:** [Additional documentation](https://github.com/Elpablo777/Telegram-Audio-Downloader/wiki)

---

*Last updated: 2024-01-20*  
*Version: 1.0.0*