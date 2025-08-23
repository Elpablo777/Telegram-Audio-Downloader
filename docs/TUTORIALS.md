# 🎓 Tutorials - Telegram Audio Downloader

**Version:** 1.0.0  
**Updated:** 2024-01-20  
**Target Audience:** Beginners to Advanced Users

## 📋 Table of Contents

1. [Getting Started](#getting-started)
2. [Basic Downloads](#basic-downloads)
3. [Advanced Filtering](#advanced-filtering)
4. [Batch Processing](#batch-processing)
5. [Custom Scripts](#custom-scripts)
6. [Performance Optimization](#performance-optimization)
7. [Automation & Scheduling](#automation--scheduling)
8. [Integration Examples](#integration-examples)

---

## 🚀 Getting Started

### Your First Download

Let's start with downloading a few audio files from a Telegram group.

#### Step 1: Setup Environment

```bash
# Ensure you have Python 3.8+ installed
python --version

# Install the package
pip install telegram-audio-downloader

# Create a working directory
mkdir my-music-downloads
cd my-music-downloads
```

#### Step 2: Configure API Credentials

Create a `.env` file in your working directory:

```env
# Get these from https://my.telegram.org/apps
API_ID=1234567
API_HASH=abcdef1234567890abcdef1234567890
SESSION_NAME=my_session
```

#### Step 3: Your First Download

```bash
# Download 5 audio files from a public music group
telegram-audio-downloader download @music_group --limit 5

# Check what was downloaded
ls downloads/
```

**Expected Output:**
```
✅ Connected to Telegram
📁 Scanning @music_group...
🎵 Found 150 audio files
⬇️  Downloading 5 files...
✅ Downloaded: Song1.mp3 (4.2 MB)
✅ Downloaded: Song2.mp3 (3.8 MB)
✅ Downloaded: Song3.mp3 (5.1 MB)
✅ Downloaded: Song4.mp3 (4.5 MB)
✅ Downloaded: Song5.mp3 (3.9 MB)

📊 Summary:
   • Downloaded: 5 files
   • Total size: 21.5 MB
   • Duration: 45 seconds
```

---

## 📦 Basic Downloads

### Download from Different Sources

#### Public Groups/Channels

```bash
# Download from public music channel
telegram-audio-downloader download @musicchannel --limit 10

# Download from multiple groups
telegram-audio-downloader download @group1 @group2 @group3 --limit 5
```

#### Private Groups (by ID)

```bash
# Use group ID for private groups
telegram-audio-downloader download -1001234567890 --limit 20
```

#### Specific File Types

```bash
# Only download MP3 files
telegram-audio-downloader download @group --file-types mp3

# Download multiple formats
telegram-audio-downloader download @group --file-types mp3,m4a,flac
```

### Download with Custom Directory Structure

```bash
# Custom download directory
telegram-audio-downloader download @group --download-dir /home/user/Music

# Organize by group name
telegram-audio-downloader download @group --organize-by-group

# Result: downloads/group_name/song.mp3
```

### Size and Duration Filters

```bash
# Download files between 2-10 MB
telegram-audio-downloader download @group --min-size 2MB --max-size 10MB

# Download songs 1-5 minutes long
telegram-audio-downloader download @group --min-duration 60 --max-duration 300
```

---

## 🔍 Advanced Filtering

### Search and Filter by Content

#### Text-based Search

```bash
# Search for specific songs
telegram-audio-downloader search @group "Beatles" --limit 10

# Search with multiple keywords
telegram-audio-downloader search @group "rock classic" --match-all

# Case-insensitive search
telegram-audio-downloader search @group "JAZZ" --ignore-case
```

#### Date Range Filtering

```bash
# Download files from last month
telegram-audio-downloader download @group --date-from "2024-01-01" --date-to "2024-01-31"

# Download recent files only
telegram-audio-downloader download @group --recent-days 7
```

#### Quality Filtering

```bash
# Download only high-quality files (>320kbps equivalent)
telegram-audio-downloader download @group --quality high

# Skip low-quality files
telegram-audio-downloader download @group --min-bitrate 192
```

### Advanced Search Examples

```bash
# Complex search query
telegram-audio-downloader search @group \
  --query "jazz OR blues" \
  --min-duration 180 \
  --max-size 15MB \
  --date-from "2023-01-01" \
  --quality medium

# Search in multiple groups
telegram-audio-downloader search @jazz_group @blues_group \
  --query "miles davis" \
  --limit 50
```

---

## 📚 Batch Processing

### Download from Multiple Groups

Create a groups list file `groups.txt`:
```
@jazz_music
@classical_music
@rock_classics
@electronic_music
@indie_songs
```

Batch download script:
```bash
#!/bin/bash
# batch_download.sh

while IFS= read -r group; do
    echo "Processing $group..."
    telegram-audio-downloader download "$group" \
        --limit 20 \
        --organize-by-group \
        --skip-existing \
        --quality high
    
    echo "Waiting 30 seconds before next group..."
    sleep 30
done < groups.txt

echo "Batch download completed!"
```

### Automated Quality Control

```bash
#!/bin/bash
# quality_download.sh

# Download with strict quality filters
telegram-audio-downloader download @music_group \
    --min-size 3MB \
    --max-size 25MB \
    --min-duration 120 \
    --max-duration 600 \
    --quality high \
    --file-types mp3,flac \
    --limit 100 \
    --organize-by-group

# Verify downloads
echo "Verifying downloaded files..."
telegram-audio-downloader verify --check-integrity --remove-corrupted

# Generate report
telegram-audio-downloader stats --export-json > download_report.json
```

---

## 🐍 Custom Scripts

### Python Script for Selective Downloads

Create `selective_download.py`:

```python
#!/usr/bin/env python3
"""
Selective music downloader with custom logic.
"""
import asyncio
from telegram_audio_downloader.downloader import AudioDownloader
from telegram_audio_downloader.models import AudioFile, TelegramGroup

async def selective_download():
    """Download music based on custom criteria."""
    
    # Artists we want to collect
    wanted_artists = [
        "The Beatles", "Pink Floyd", "Led Zeppelin",
        "Queen", "Bob Dylan", "David Bowie"
    ]
    
    # File size preferences (in bytes)
    min_size = 3 * 1024 * 1024    # 3 MB
    max_size = 25 * 1024 * 1024   # 25 MB
    
    downloader = AudioDownloader(
        download_dir="./curated_music",
        max_concurrent_downloads=3
    )
    
    await downloader.initialize_client()
    
    try:
        # Search for music from wanted artists
        for artist in wanted_artists:
            print(f"🎵 Searching for {artist}...")
            
            messages = await downloader.search_messages(
                group_identifier="@music_archive",
                query=artist,
                filter_options={
                    "min_size": min_size,
                    "max_size": max_size,
                    "file_types": ["mp3", "flac"],
                    "min_duration": 120  # At least 2 minutes
                }
            )
            
            if messages:
                print(f"Found {len(messages)} songs by {artist}")
                
                # Download with custom naming
                result = await downloader.download_audio_files(
                    group_identifier="@music_archive",
                    limit=len(messages),
                    custom_filter=lambda msg: any(
                        artist.lower() in (msg.get('performer', '') or '').lower()
                        for artist in wanted_artists
                    )
                )
                
                print(f"Downloaded {result['completed']} songs by {artist}")
            
            # Be nice to the API
            await asyncio.sleep(5)
    
    finally:
        await downloader.close()

if __name__ == "__main__":
    asyncio.run(selective_download())
```

Run the script:
```bash
python selective_download.py
```

### Metadata Enhancement Script

Create `enhance_metadata.py`:

```python
#!/usr/bin/env python3
"""
Enhance downloaded files with metadata from external sources.
"""
import os
import json
from pathlib import Path
from telegram_audio_downloader.utils import extract_metadata
from telegram_audio_downloader.models import AudioFile

def enhance_metadata():
    """Enhance metadata for all downloaded files."""
    
    download_dir = Path("downloads")
    
    for audio_file in AudioFile.select().where(
        AudioFile.local_path.is_null(False)
    ):
        file_path = Path(audio_file.local_path)
        
        if not file_path.exists():
            continue
        
        print(f"Processing: {file_path.name}")
        
        # Extract current metadata
        metadata = extract_metadata(str(file_path))
        
        # Enhance with additional info
        enhanced = {
            **metadata,
            "file_size_mb": round(file_path.stat().st_size / 1024 / 1024, 2),
            "added_date": audio_file.download_date.isoformat(),
            "source_group": audio_file.group.title,
            "quality_score": calculate_quality_score(metadata)
        }
        
        # Update database
        audio_file.metadata = enhanced
        audio_file.save()
        
        print(f"  ✅ Enhanced metadata for {enhanced.get('title', 'Unknown')}")

def calculate_quality_score(metadata):
    """Calculate a quality score based on metadata."""
    score = 0
    
    # Bitrate scoring
    bitrate = metadata.get('bitrate', 0)
    if bitrate >= 320:
        score += 50
    elif bitrate >= 256:
        score += 40
    elif bitrate >= 192:
        score += 30
    elif bitrate >= 128:
        score += 20
    
    # Duration scoring (prefer 2-8 minute songs)
    duration = metadata.get('duration', 0)
    if 120 <= duration <= 480:
        score += 30
    elif 60 <= duration <= 600:
        score += 20
    
    # File size scoring
    size = metadata.get('file_size', 0)
    if 3 * 1024 * 1024 <= size <= 15 * 1024 * 1024:  # 3-15 MB
        score += 20
    
    return min(score, 100)

if __name__ == "__main__":
    enhance_metadata()
```

---

## ⚡ Performance Optimization

### Optimize for Speed

```bash
# Maximum performance configuration
telegram-audio-downloader download @group \
    --max-concurrent 8 \
    --rate-limit 0.5 \
    --skip-existing \
    --no-verify \
    --limit 1000
```

### Optimize for Quality

```bash
# Quality-focused configuration
telegram-audio-downloader download @group \
    --max-concurrent 2 \
    --rate-limit 2.0 \
    --verify-downloads \
    --quality high \
    --min-size 5MB \
    --check-duplicates
```

### Memory-Efficient Downloads

Create `memory_efficient.py`:

```python
#!/usr/bin/env python3
"""
Memory-efficient downloading for large groups.
"""
import asyncio
import gc
from telegram_audio_downloader.downloader import AudioDownloader
from telegram_audio_downloader.performance import get_performance_monitor

async def memory_efficient_download():
    """Download large amounts with memory management."""
    
    monitor = get_performance_monitor()
    downloader = AudioDownloader(
        max_concurrent_downloads=2,  # Lower concurrency
        rate_limit_delay=1.5         # Slower but safer
    )
    
    await downloader.initialize_client()
    
    try:
        batch_size = 50  # Process in smaller batches
        total_downloaded = 0
        
        while True:
            # Check memory before each batch
            if monitor.is_memory_limit_exceeded():
                print("🧹 Memory limit reached, cleaning up...")
                gc.collect()
                await asyncio.sleep(5)
            
            # Download batch
            result = await downloader.download_audio_files(
                group_identifier="@large_music_archive",
                limit=batch_size,
                skip_existing=True
            )
            
            total_downloaded += result['completed']
            print(f"📊 Total downloaded: {total_downloaded}")
            
            # Stop if no more files
            if result['completed'] == 0:
                break
            
            # Short break between batches
            await asyncio.sleep(10)
    
    finally:
        await downloader.close()

if __name__ == "__main__":
    asyncio.run(memory_efficient_download())
```

---

## 🕒 Automation & Scheduling

### Cron Job Setup

Create a daily download script `daily_download.sh`:

```bash
#!/bin/bash
# daily_download.sh - Run daily music collection

LOG_FILE="/var/log/telegram-audio-downloader.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$DATE] Starting daily download..." >> $LOG_FILE

# Download new music from favorite groups
telegram-audio-downloader download \
    @daily_music @new_releases @underground_music \
    --limit 10 \
    --recent-days 1 \
    --skip-existing \
    --organize-by-group \
    --quality medium \
    >> $LOG_FILE 2>&1

# Generate daily report
telegram-audio-downloader stats \
    --format json \
    --output "/var/reports/daily-$(date +%Y%m%d).json" \
    >> $LOG_FILE 2>&1

echo "[$DATE] Daily download completed." >> $LOG_FILE
```

Add to crontab:
```bash
# Edit crontab
crontab -e

# Add daily download at 3 AM
0 3 * * * /home/user/scripts/daily_download.sh
```

### Systemd Service

Create `/etc/systemd/system/telegram-downloader.service`:

```ini
[Unit]
Description=Telegram Audio Downloader Service
After=network.target

[Service]
Type=oneshot
User=music
Group=music
WorkingDirectory=/home/music/downloads
Environment=PYTHONPATH=/home/music/telegram-audio-downloader
ExecStart=/usr/local/bin/telegram-audio-downloader download @music_feed --limit 20 --recent-days 1
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Create timer `/etc/systemd/system/telegram-downloader.timer`:

```ini
[Unit]
Description=Run Telegram Audio Downloader every 6 hours
Requires=telegram-downloader.service

[Timer]
OnCalendar=*-*-* 00,06,12,18:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

Enable and start:
```bash
sudo systemctl enable telegram-downloader.timer
sudo systemctl start telegram-downloader.timer
```

---

## 🔌 Integration Examples

### Music Library Management

Create `library_manager.py`:

```python
#!/usr/bin/env python3
"""
Integrate with music library management systems.
"""
import json
import shutil
from pathlib import Path
from telegram_audio_downloader.models import AudioFile
from telegram_audio_downloader.utils import extract_metadata

class MusicLibraryManager:
    def __init__(self, library_path="/home/user/Music"):
        self.library_path = Path(library_path)
        self.library_path.mkdir(exist_ok=True)
    
    def organize_by_artist(self):
        """Organize downloaded music by artist."""
        
        for audio_file in AudioFile.select().where(
            AudioFile.local_path.is_null(False)
        ):
            source_path = Path(audio_file.local_path)
            
            if not source_path.exists():
                continue
            
            # Get metadata
            metadata = json.loads(audio_file.metadata or '{}')
            artist = metadata.get('artist', 'Unknown Artist')
            album = metadata.get('album', 'Unknown Album')
            
            # Create target directory
            target_dir = self.library_path / artist / album
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # Move file
            target_path = target_dir / source_path.name
            if not target_path.exists():
                shutil.move(str(source_path), str(target_path))
                
                # Update database
                audio_file.local_path = str(target_path)
                audio_file.save()
                
                print(f"📁 Moved: {artist} - {source_path.name}")
    
    def export_playlist(self, format="m3u"):
        """Export playlists in various formats."""
        
        playlist_content = []
        
        for audio_file in AudioFile.select().where(
            AudioFile.local_path.is_null(False)
        ):
            if Path(audio_file.local_path).exists():
                playlist_content.append(audio_file.local_path)
        
        # Write playlist
        playlist_file = self.library_path / f"telegram_downloads.{format}"
        
        if format == "m3u":
            with open(playlist_file, 'w', encoding='utf-8') as f:
                f.write("#EXTM3U\n")
                for path in playlist_content:
                    f.write(f"{path}\n")
        
        elif format == "json":
            with open(playlist_file, 'w', encoding='utf-8') as f:
                json.dump(playlist_content, f, indent=2)
        
        print(f"📝 Exported playlist: {playlist_file}")

# Usage
if __name__ == "__main__":
    manager = MusicLibraryManager()
    manager.organize_by_artist()
    manager.export_playlist("m3u")
    manager.export_playlist("json")
```

### Discord Bot Integration

Create `discord_bot.py`:

```python
#!/usr/bin/env python3
"""
Discord bot for requesting music downloads.
"""
import asyncio
import discord
from discord.ext import commands
from telegram_audio_downloader.downloader import AudioDownloader

class MusicBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.downloader = None
    
    async def cog_load(self):
        """Initialize downloader when cog loads."""
        self.downloader = AudioDownloader()
        await self.downloader.initialize_client()
    
    async def cog_unload(self):
        """Cleanup when cog unloads."""
        if self.downloader:
            await self.downloader.close()
    
    @commands.command(name='download')
    async def download_music(self, ctx, group: str, *, query: str = None):
        """Download music from Telegram group."""
        
        await ctx.send(f"🔍 Searching for music in {group}...")
        
        try:
            if query:
                # Search for specific query
                messages = await self.downloader.search_messages(
                    group_identifier=group,
                    query=query,
                    limit=5
                )
                
                if not messages:
                    await ctx.send(f"❌ No music found for '{query}' in {group}")
                    return
                
                await ctx.send(f"🎵 Found {len(messages)} songs, downloading...")
            
            # Download
            result = await self.downloader.download_audio_files(
                group_identifier=group,
                limit=5 if query else 10
            )
            
            # Report results
            embed = discord.Embed(
                title="Download Complete",
                color=discord.Color.green()
            )
            embed.add_field(
                name="Downloaded",
                value=f"{result['completed']} files"
            )
            embed.add_field(
                name="Total Size",
                value=f"{result['total_size'] / 1024 / 1024:.1f} MB"
            )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Error: {str(e)}")
    
    @commands.command(name='stats')
    async def music_stats(self, ctx):
        """Show download statistics."""
        
        from telegram_audio_downloader.models import AudioFile
        
        total_files = AudioFile.select().count()
        total_size = sum(
            af.file_size for af in AudioFile.select()
            if af.file_size
        )
        
        embed = discord.Embed(
            title="Music Library Stats",
            color=discord.Color.blue()
        )
        embed.add_field(name="Total Files", value=total_files)
        embed.add_field(
            name="Total Size",
            value=f"{total_size / 1024 / 1024 / 1024:.2f} GB"
        )
        
        await ctx.send(embed=embed)

# Bot setup
bot = commands.Bot(command_prefix='!', intents=discord.Intents.default())

async def main():
    await bot.add_cog(MusicBot(bot))
    await bot.start('YOUR_DISCORD_BOT_TOKEN')

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 🎯 Advanced Use Cases

### Music Discovery Workflow

Create a complete music discovery and download workflow:

```python
#!/usr/bin/env python3
"""
Advanced music discovery and curation workflow.
"""
import asyncio
import json
from datetime import datetime, timedelta
from telegram_audio_downloader.downloader import AudioDownloader
from telegram_audio_downloader.models import AudioFile, TelegramGroup

class MusicDiscoveryBot:
    def __init__(self):
        self.downloader = AudioDownloader(
            download_dir="./discovered_music",
            max_concurrent_downloads=3
        )
        self.discovery_groups = [
            "@new_music_daily",
            "@underground_music",
            "@indie_discoveries",
            "@electronic_new",
            "@jazz_discoveries"
        ]
    
    async def daily_discovery(self):
        """Run daily music discovery."""
        
        await self.downloader.initialize_client()
        
        try:
            discovered = []
            
            for group in self.discovery_groups:
                print(f"🔍 Discovering from {group}...")
                
                # Search for recent high-quality music
                messages = await self.downloader.search_messages(
                    group_identifier=group,
                    filter_options={
                        "date_from": (datetime.now() - timedelta(days=1)).isoformat(),
                        "min_size": 3 * 1024 * 1024,  # 3MB+
                        "min_duration": 120,           # 2+ minutes
                        "file_types": ["mp3", "m4a", "flac"]
                    },
                    limit=20
                )
                
                if messages:
                    # Download and analyze
                    result = await self.downloader.download_audio_files(
                        group_identifier=group,
                        limit=len(messages),
                        quality_filter="medium"
                    )
                    
                    discovered.extend(result['files'])
                    print(f"  ✅ Downloaded {result['completed']} tracks")
                
                # Rate limiting
                await asyncio.sleep(10)
            
            # Generate discovery report
            await self.generate_discovery_report(discovered)
            
        finally:
            await self.downloader.close()
    
    async def generate_discovery_report(self, files):
        """Generate a report of discovered music."""
        
        report = {
            "date": datetime.now().isoformat(),
            "total_discovered": len(files),
            "files": files,
            "genres_found": self.analyze_genres(files),
            "recommendations": self.get_recommendations(files)
        }
        
        # Save report
        with open(f"discovery_report_{datetime.now().strftime('%Y%m%d')}.json", 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📊 Discovery report saved: {len(files)} new tracks")
    
    def analyze_genres(self, files):
        """Analyze music genres from metadata."""
        # Simplified genre analysis
        return {"electronic": 5, "indie": 3, "jazz": 2}
    
    def get_recommendations(self, files):
        """Generate recommendations based on discoveries."""
        return [
            "Try searching @ambient_music for similar electronic tracks",
            "Check @jazz_fusion for more experimental jazz"
        ]

# Run the discovery bot
async def main():
    bot = MusicDiscoveryBot()
    await bot.daily_discovery()

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 🆘 Troubleshooting Common Issues

### Connection Issues

```bash
# Test connection
telegram-audio-downloader test-connection

# Reset session if auth fails
rm -f ~/.local/share/telegram-audio-downloader/*.session
telegram-audio-downloader download @test_group --limit 1
```

### Performance Issues

```bash
# Reduce concurrent downloads
telegram-audio-downloader download @group --max-concurrent 1

# Increase rate limiting
telegram-audio-downloader download @group --rate-limit 3.0

# Monitor performance
telegram-audio-downloader download @group --monitor --verbose
```

### Storage Issues

```bash
# Check disk space
df -h

# Clean up failed downloads
telegram-audio-downloader cleanup --remove-incomplete

# Compress old downloads
find downloads/ -name "*.mp3" -mtime +30 -exec gzip {} \;
```

---

## 📚 Next Steps

### Explore More Features

- **[API Reference](API_REFERENCE.md)** - Learn programmatic usage
- **[Performance Guide](PERFORMANCE.md)** - Optimize your setup
- **[Troubleshooting](TROUBLESHOOTING.md)** - Solve common issues

### Join the Community

- **[GitHub Discussions](https://github.com/Elpablo777/Telegram-Audio-Downloader/discussions)** - Share tips and ask questions
- **[Contributing](../CONTRIBUTING.md)** - Help improve the project

### Advanced Topics

- Setting up distributed downloads across multiple machines
- Integration with music streaming services
- Building custom web interfaces
- Creating automated music curation systems

---

*Happy music collecting! 🎵*

---

*Last updated: 2024-01-20*  
*Version: 1.0.0*