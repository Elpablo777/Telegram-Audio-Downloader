# 🛠️ Troubleshooting Guide - Telegram Audio Downloader

**Version:** 1.0.0  
**Updated:** 2024-01-20  
**Target Audience:** All Users

## 📋 Table of Contents

1. [Quick Diagnostics](#quick-diagnostics)
2. [Installation Issues](#installation-issues)
3. [Authentication Problems](#authentication-problems)
4. [Download Failures](#download-failures)
5. [Performance Issues](#performance-issues)
6. [API Rate Limiting](#api-rate-limiting)
7. [Storage & File Issues](#storage--file-issues)
8. [Network Problems](#network-problems)
9. [Configuration Issues](#configuration-issues)
10. [Advanced Debugging](#advanced-debugging)

---

## 🔍 Quick Diagnostics

### Check System Status

Run these commands to quickly identify common issues:

```bash
# Check if tool is properly installed
telegram-audio-downloader --version

# Test basic functionality
telegram-audio-downloader test-connection

# Check configuration
telegram-audio-downloader config --show

# Verify dependencies
python -c "import telethon, mutagen, peewee; print('Dependencies OK')"
```

### Environment Information

```bash
# System information
python --version
pip --version
telegram-audio-downloader --version

# Check available disk space
df -h

# Check memory usage
free -h  # Linux
vm_stat | head -5  # macOS
```

### Log Analysis

```bash
# Check recent logs for errors
telegram-audio-downloader logs --last 50

# Verbose mode for detailed output
telegram-audio-downloader download @test --verbose --dry-run
```

---

## 🚀 Installation Issues

### Problem: `telegram-audio-downloader: command not found`

**Symptoms:**
- Command not found after installation
- `pip install` completed successfully

**Solutions:**

#### Solution 1: Check PATH
```bash
# Check if pip bin directory is in PATH
python -m pip show telegram-audio-downloader

# Add to PATH (add to ~/.bashrc or ~/.zshrc)
export PATH="$HOME/.local/bin:$PATH"

# Reload shell
source ~/.bashrc  # or ~/.zshrc
```

#### Solution 2: Use python -m
```bash
# Run as module instead
python -m telegram_audio_downloader download @group
```

#### Solution 3: Virtual Environment
```bash
# Create virtual environment
python -m venv telegram-downloader
source telegram-downloader/bin/activate  # Linux/macOS
# telegram-downloader\Scripts\activate  # Windows

# Install in virtual environment
pip install telegram-audio-downloader
```

### Problem: `ModuleNotFoundError` during installation

**Symptoms:**
```
ModuleNotFoundError: No module named 'telegram_audio_downloader'
```

**Solutions:**

#### Check Python Version
```bash
# Ensure Python 3.8+
python --version

# Use specific Python version if needed
python3.11 -m pip install telegram-audio-downloader
```

#### Development Installation
```bash
# If installing from source
git clone https://github.com/Elpablo777/Telegram-Audio-Downloader.git
cd Telegram-Audio-Downloader
pip install -e .
```

### Problem: Dependency Conflicts

**Symptoms:**
```
ERROR: pip's dependency resolver does not currently consider all the packages
```

**Solutions:**

#### Clean Installation
```bash
# Uninstall conflicting packages
pip uninstall telethon telegram-audio-downloader

# Clear pip cache
pip cache purge

# Fresh installation
pip install --no-cache-dir telegram-audio-downloader
```

#### Use Requirements Lock
```bash
# Install with exact versions
pip install telegram-audio-downloader==1.0.0
```

---

## 🔐 Authentication Problems

### Problem: `Invalid API ID or Hash`

**Symptoms:**
- Authentication fails immediately
- "API_ID and API_HASH must be set" error

**Solutions:**

#### Verify API Credentials
```bash
# Check .env file exists and has correct format
cat .env

# Ensure no extra spaces or quotes
API_ID=1234567
API_HASH=abcdef1234567890abcdef1234567890
```

#### Get New Credentials
1. Go to https://my.telegram.org/apps
2. Log in with your phone number
3. Create new application
4. Copy API_ID and API_HASH exactly

#### Environment Variables
```bash
# Set as environment variables
export API_ID=1234567
export API_HASH=abcdef1234567890abcdef1234567890

# Or pass directly
telegram-audio-downloader download @group --api-id 1234567 --api-hash abcdef...
```

### Problem: `Phone number required`

**Symptoms:**
- Prompted for phone number every time
- Session not persisting

**Solutions:**

#### Session Configuration
```bash
# Specify session name
telegram-audio-downloader download @group --session-name my_session

# Check session file location
ls ~/.local/share/telegram-audio-downloader/
```

#### Manual Authentication
```python
# auth_setup.py
import asyncio
from telethon import TelegramClient

async def setup_auth():
    client = TelegramClient('my_session', API_ID, API_HASH)
    await client.start()
    print("Authentication successful!")
    await client.disconnect()

asyncio.run(setup_auth())
```

### Problem: `Two-factor authentication required`

**Symptoms:**
- Prompted for password during authentication
- "Please enter your 2FA password" message

**Solutions:**

#### Interactive Setup
```bash
# Run with interactive mode
telegram-audio-downloader auth --interactive

# Or use specific command
telegram-audio-downloader setup-2fa
```

#### Programmatic 2FA
```python
# Set 2FA password in environment
export TELEGRAM_2FA_PASSWORD=your_password

# Or in .env file
TELEGRAM_2FA_PASSWORD=your_password
```

---

## 📥 Download Failures

### Problem: `No audio files found`

**Symptoms:**
- "No audio files found in group" message
- Download completes with 0 files

**Solutions:**

#### Verify Group Access
```bash
# Check if group exists and is accessible
telegram-audio-downloader info @group_name

# Try with group ID instead of username
telegram-audio-downloader download -1001234567890
```

#### Adjust Search Parameters
```bash
# Remove file type restrictions
telegram-audio-downloader download @group --file-types all

# Increase search limit
telegram-audio-downloader download @group --limit 1000

# Check different date ranges
telegram-audio-downloader download @group --date-from 2023-01-01
```

#### Debug Search
```bash
# Use search command to debug
telegram-audio-downloader search @group --limit 100 --verbose
```

### Problem: `Download interrupted` or `Partial downloads`

**Symptoms:**
- Downloads stop mid-way
- Incomplete files in download directory
- "Connection lost" errors

**Solutions:**

#### Resume Downloads
```bash
# Resume incomplete downloads
telegram-audio-downloader resume

# Or restart with skip-existing
telegram-audio-downloader download @group --skip-existing
```

#### Increase Retry Logic
```bash
# More robust download with retries
telegram-audio-downloader download @group \
    --max-retries 5 \
    --retry-delay 3 \
    --timeout 30
```

#### Reduce Concurrency
```bash
# Lower concurrent downloads
telegram-audio-downloader download @group --max-concurrent 1
```

### Problem: `File corruption` or `Invalid audio files`

**Symptoms:**
- Downloaded files won't play
- "File appears to be corrupted" warnings
- Zero-byte files

**Solutions:**

#### Enable Verification
```bash
# Download with integrity checking
telegram-audio-downloader download @group --verify-downloads

# Post-download verification
telegram-audio-downloader verify --check-integrity
```

#### Clean Up Corrupted Files
```bash
# Remove corrupted files
telegram-audio-downloader cleanup --remove-corrupted

# Re-download specific files
telegram-audio-downloader download @group --force-redownload file_id_123
```

---

## ⚡ Performance Issues

### Problem: `Slow download speeds`

**Symptoms:**
- Downloads taking very long
- Speed below 100 KB/s consistently

**Solutions:**

#### Optimize Concurrency
```bash
# Increase concurrent downloads
telegram-audio-downloader download @group --max-concurrent 8

# Reduce rate limiting
telegram-audio-downloader download @group --rate-limit 0.5
```

#### Network Optimization
```bash
# Use different Telegram DC
telegram-audio-downloader download @group --dc-id 2

# Check network speed
speedtest-cli
```

#### System Resources
```bash
# Check system resources
htop  # or top
iostat 1  # check disk I/O

# Free up memory
telegram-audio-downloader cleanup --clear-cache
```

### Problem: `High memory usage`

**Symptoms:**
- System becoming slow during downloads
- Out of memory errors
- Process killed by system

**Solutions:**

#### Memory Configuration
```bash
# Reduce memory usage
telegram-audio-downloader download @group \
    --max-concurrent 2 \
    --memory-limit 512MB \
    --cleanup-frequency 10
```

#### Batch Processing
```bash
# Process in smaller batches
for i in {1..10}; do
    telegram-audio-downloader download @group \
        --limit 50 \
        --offset $((i * 50)) \
        --skip-existing
    sleep 10
done
```

### Problem: `High CPU usage`

**Symptoms:**
- 100% CPU usage during downloads
- System becomes unresponsive
- Fans running at high speed

**Solutions:**

#### CPU Limiting
```bash
# Limit CPU usage (Linux)
cpulimit -l 50 telegram-audio-downloader download @group

# Use nice to lower priority
nice -n 10 telegram-audio-downloader download @group
```

#### Disable Resource-Intensive Features
```bash
# Disable metadata extraction
telegram-audio-downloader download @group --no-metadata

# Disable file verification
telegram-audio-downloader download @group --no-verify
```

---

## 🚫 API Rate Limiting

### Problem: `Rate limit exceeded`

**Symptoms:**
- "Too many requests" errors
- Downloads suddenly stop
- API timeouts

**Solutions:**

#### Adjust Rate Limiting
```bash
# Increase delay between requests
telegram-audio-downloader download @group --rate-limit 3.0

# Use flood wait handling
telegram-audio-downloader download @group --handle-flood-wait
```

#### Exponential Backoff
```python
# Custom retry script with backoff
import asyncio
import time

async def download_with_backoff():
    backoff = 1
    max_backoff = 300  # 5 minutes
    
    while True:
        try:
            result = await downloader.download_audio_files("@group")
            break
        except FloodWaitError as e:
            wait_time = min(e.seconds, max_backoff)
            print(f"Flood wait: {wait_time}s")
            await asyncio.sleep(wait_time)
        except Exception as e:
            print(f"Error: {e}, backing off {backoff}s")
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, max_backoff)
```

### Problem: `Account temporarily restricted`

**Symptoms:**
- "Your account has been restricted" message
- All API calls failing
- Cannot access any groups

**Solutions:**

#### Wait and Reduce Activity
```bash
# Stop all downloading activity
pkill -f telegram-audio-downloader

# Wait 24 hours before trying again
# Use more conservative settings when resuming
telegram-audio-downloader download @group \
    --rate-limit 5.0 \
    --max-concurrent 1
```

#### Use Different Session
```bash
# Create new session with different phone number
telegram-audio-downloader auth --session-name backup_session
```

---

## 💾 Storage & File Issues

### Problem: `Disk space full`

**Symptoms:**
- "No space left on device" errors
- Downloads failing due to storage
- System becoming slow

**Solutions:**

#### Check and Clean Space
```bash
# Check disk usage
df -h
du -sh downloads/

# Clean up old downloads
find downloads/ -name "*.mp3" -mtime +30 -delete

# Compress old files
find downloads/ -name "*.mp3" -mtime +7 -exec gzip {} \;
```

#### Configure Storage Limits
```bash
# Set maximum storage for downloads
telegram-audio-downloader download @group --max-storage 10GB

# Move to external storage
telegram-audio-downloader download @group --download-dir /mnt/external/music
```

### Problem: `Permission denied` errors

**Symptoms:**
- Cannot create files in download directory
- "Permission denied" when writing files

**Solutions:**

#### Fix Permissions
```bash
# Make download directory writable
chmod 755 downloads/
chown $USER:$USER downloads/

# Create directory if it doesn't exist
mkdir -p downloads && chmod 755 downloads/
```

#### Use Different Directory
```bash
# Download to home directory
telegram-audio-downloader download @group --download-dir ~/Music

# Use temp directory
telegram-audio-downloader download @group --download-dir /tmp/music
```

### Problem: `Filename encoding issues`

**Symptoms:**
- Strange characters in filenames
- "Invalid filename" errors
- Files with question marks or squares

**Solutions:**

#### Set Encoding
```bash
# Force UTF-8 encoding
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8

# Use ASCII-safe filenames
telegram-audio-downloader download @group --ascii-filenames
```

#### Filename Sanitization
```python
# Custom filename cleaning
import re

def clean_filename(filename):
    # Remove invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Limit length
    if len(filename) > 200:
        name, ext = os.path.splitext(filename)
        filename = name[:200-len(ext)] + ext
    return filename
```

---

## 🌐 Network Problems

### Problem: `Connection timeouts`

**Symptoms:**
- "Connection timed out" errors
- Downloads failing to start
- Intermittent connectivity issues

**Solutions:**

#### Increase Timeouts
```bash
# Increase connection timeout
telegram-audio-downloader download @group --timeout 60

# Use different proxy or VPN
telegram-audio-downloader download @group --proxy socks5://localhost:1080
```

#### Test Network
```bash
# Test basic connectivity
ping telegram.org

# Test specific Telegram servers
telnet 149.154.167.50 443
```

### Problem: `Proxy configuration issues`

**Symptoms:**
- Cannot connect through proxy
- "Proxy authentication failed"
- Slow speeds through proxy

**Solutions:**

#### Configure Proxy
```bash
# SOCKS5 proxy
telegram-audio-downloader download @group \
    --proxy socks5://username:password@localhost:1080

# HTTP proxy
telegram-audio-downloader download @group \
    --proxy http://proxy.example.com:8080
```

#### Test Proxy
```bash
# Test proxy connectivity
curl --proxy socks5://localhost:1080 http://httpbin.org/ip
```

### Problem: `Firewall blocking connections`

**Symptoms:**
- "Connection refused" errors
- Cannot connect to Telegram servers
- Works with VPN but not without

**Solutions:**

#### Check Firewall Rules
```bash
# Linux: Check iptables
sudo iptables -L

# macOS: Check built-in firewall
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate

# Windows: Check Windows Firewall
netsh advfirewall show allprofiles
```

#### Allow Telegram Ports
```bash
# Allow Telegram ports (443, 80, 5222)
sudo ufw allow 443
sudo ufw allow 80
sudo ufw allow 5222
```

---

## ⚙️ Configuration Issues

### Problem: `Configuration file not found`

**Symptoms:**
- "Config file not found" warnings
- Settings not persisting
- Using defaults every time

**Solutions:**

#### Create Configuration
```bash
# Generate default config
telegram-audio-downloader config --init

# Edit configuration
telegram-audio-downloader config --edit
```

#### Specify Config Location
```bash
# Use specific config file
telegram-audio-downloader download @group --config ~/my-config.ini

# Set config environment variable
export TELEGRAM_DOWNLOADER_CONFIG=~/my-config.ini
```

### Problem: `Invalid configuration values`

**Symptoms:**
- "Invalid value for..." errors
- Configuration ignored
- Unexpected behavior

**Solutions:**

#### Validate Configuration
```bash
# Check configuration syntax
telegram-audio-downloader config --validate

# Show current configuration
telegram-audio-downloader config --show
```

#### Reset Configuration
```bash
# Reset to defaults
telegram-audio-downloader config --reset

# Remove corrupt config
rm ~/.config/telegram-audio-downloader/config.ini
```

---

## 🔧 Advanced Debugging

### Enable Debug Mode

```bash
# Maximum verbosity
telegram-audio-downloader download @group --debug --verbose

# Save debug logs
telegram-audio-downloader download @group --debug --log-file debug.log
```

### Python Debugging

```python
# debug_session.py
import asyncio
import logging
from telegram_audio_downloader.downloader import AudioDownloader

# Enable all logging
logging.basicConfig(level=logging.DEBUG)

async def debug_download():
    downloader = AudioDownloader()
    
    try:
        await downloader.initialize_client()
        
        # Test basic functionality
        info = await downloader.get_group_info("@test_group")
        print(f"Group info: {info}")
        
        # Test search
        messages = await downloader.search_messages("@test_group", limit=1)
        print(f"Found {len(messages)} messages")
        
    except Exception as e:
        import traceback
        traceback.print_exc()
    
    finally:
        await downloader.close()

asyncio.run(debug_download())
```

### Network Debugging

```bash
# Monitor network traffic
tcpdump -i any host 149.154.167.50

# Check DNS resolution
nslookup telegram.org

# Test with curl
curl -v https://api.telegram.org/bot
```

### Database Debugging

```python
# Check database state
from telegram_audio_downloader.models import AudioFile, TelegramGroup

# Count records
print(f"Audio files: {AudioFile.select().count()}")
print(f"Groups: {TelegramGroup.select().count()}")

# Check for issues
for audio_file in AudioFile.select().where(AudioFile.local_path.is_null(False)):
    if not os.path.exists(audio_file.local_path):
        print(f"Missing file: {audio_file.local_path}")
```

### System Resource Monitoring

```bash
# Monitor during download
# Terminal 1: Start download
telegram-audio-downloader download @large_group --debug

# Terminal 2: Monitor resources
watch -n 1 'ps aux | grep telegram-audio-downloader'
watch -n 1 'free -h'
watch -n 1 'df -h'
```

---

## 🆘 Getting Help

### Before Reporting Issues

1. **Check existing issues:** https://github.com/Elpablo777/Telegram-Audio-Downloader/issues
2. **Run diagnostics:** `telegram-audio-downloader --debug --verbose`
3. **Check logs:** Look for error messages and stack traces
4. **Try minimal reproduction:** Test with a simple command

### Creating Bug Reports

Include this information in bug reports:

```bash
# System information
telegram-audio-downloader --version
python --version
uname -a  # Linux/macOS
ver  # Windows

# Error reproduction
telegram-audio-downloader download @problem_group --debug --verbose 2>&1 | tee error.log

# Configuration (remove sensitive data)
telegram-audio-downloader config --show | grep -v -E "(API_|password|token)"
```

### Community Support

- **GitHub Discussions:** https://github.com/Elpablo777/Telegram-Audio-Downloader/discussions
- **Wiki:** https://github.com/Elpablo777/Telegram-Audio-Downloader/wiki
- **Issue Tracker:** https://github.com/Elpablo777/Telegram-Audio-Downloader/issues

### Professional Support

For enterprise users or complex deployments, consider:

- Custom configuration assistance
- Integration support
- Performance optimization
- Security auditing

---

## 📊 Common Error Codes

| Error Code | Description | Solution |
|------------|-------------|----------|
| AUTH_ERROR_001 | Invalid API credentials | Check API_ID and API_HASH |
| DOWNLOAD_ERROR_002 | File not found | Verify group access and file existence |
| NETWORK_ERROR_003 | Connection timeout | Check network and increase timeout |
| STORAGE_ERROR_004 | Disk space full | Free up space or change download directory |
| RATE_LIMIT_005 | Too many requests | Increase rate limiting delay |
| SESSION_ERROR_006 | Invalid session | Delete session file and re-authenticate |
| PERMISSION_ERROR_007 | Access denied | Check file/directory permissions |
| CONFIG_ERROR_008 | Invalid configuration | Validate and fix configuration file |

---

*For additional help, visit our [GitHub repository](https://github.com/Elpablo777/Telegram-Audio-Downloader) or [community discussions](https://github.com/Elpablo777/Telegram-Audio-Downloader/discussions).*

---

*Last updated: 2024-01-20*  
*Version: 1.0.0*