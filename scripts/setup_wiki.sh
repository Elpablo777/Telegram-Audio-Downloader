#!/bin/bash
# 🚀 Wiki Setup Script for GitHub Wiki
# This script sets up the GitHub Wiki with all documentation pages

set -e

echo "🎵 Setting up Telegram Audio Downloader Wiki..."

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "README.md" ] || [ ! -d "wiki" ]; then
    echo -e "${RED}❌ Error: Please run this script from the project root directory${NC}"
    exit 1
fi

# Repository information
REPO_OWNER="Elpablo777"
REPO_NAME="Telegram-Audio-Downloader"
WIKI_URL="https://github.com/${REPO_OWNER}/${REPO_NAME}.wiki.git"

echo -e "${BLUE}📚 Repository: ${REPO_OWNER}/${REPO_NAME}${NC}"
echo -e "${BLUE}📖 Wiki URL: ${WIKI_URL}${NC}"

# Create temporary directory for wiki
TEMP_WIKI_DIR="temp_wiki_setup"
if [ -d "$TEMP_WIKI_DIR" ]; then
    echo -e "${YELLOW}🧹 Cleaning up existing temp directory...${NC}"
    rm -rf "$TEMP_WIKI_DIR"
fi

echo -e "${BLUE}📂 Creating temporary wiki directory...${NC}"
mkdir -p "$TEMP_WIKI_DIR"

# Clone the wiki repository (create if doesn't exist)
echo -e "${BLUE}📥 Setting up wiki repository...${NC}"
cd "$TEMP_WIKI_DIR"

# Try to clone the wiki, if it doesn't exist, initialize it
if git clone "$WIKI_URL" . 2>/dev/null; then
    echo -e "${GREEN}✅ Wiki repository cloned successfully${NC}"
else
    echo -e "${YELLOW}⚠️ Wiki doesn't exist yet, initializing...${NC}"
    git init
    git remote add origin "$WIKI_URL"
fi

cd ..

# Copy all wiki files from the local wiki directory
echo -e "${BLUE}📋 Copying wiki files...${NC}"

# List of wiki files to copy
declare -A WIKI_FILES
WIKI_FILES["wiki/Home.md"]="Home.md"
WIKI_FILES["wiki/Installation-Guide.md"]="Installation-Guide.md"
WIKI_FILES["wiki/FAQ.md"]="FAQ.md"
WIKI_FILES["wiki/Architecture-Overview.md"]="Architecture-Overview.md"
WIKI_FILES["wiki/Best-Practices.md"]="Best-Practices.md"

# Copy each wiki file
for source_file in "${!WIKI_FILES[@]}"; do
    target_file="${WIKI_FILES[$source_file]}"
    
    if [ -f "$source_file" ]; then
        echo -e "${GREEN}✅ Copying: ${source_file} → ${target_file}${NC}"
        cp "$source_file" "$TEMP_WIKI_DIR/$target_file"
    else
        echo -e "${YELLOW}⚠️ Warning: ${source_file} not found, skipping...${NC}"
    fi
done

# Create additional wiki pages that might be missing
echo -e "${BLUE}📄 Creating additional wiki pages...${NC}"

# Quick Start page
if [ ! -f "$TEMP_WIKI_DIR/Quick-Start.md" ]; then
    cat > "$TEMP_WIKI_DIR/Quick-Start.md" << 'EOF'
# 🚀 Quick Start Guide

Get up and running with Telegram Audio Downloader in just 5 minutes!

## 📦 Installation

```bash
# Install via pip
pip install telegram-audio-downloader

# Or via GitHub
pip install git+https://github.com/Elpablo777/Telegram-Audio-Downloader.git
```

## ⚙️ Configuration

1. **Get your Telegram API credentials** from [my.telegram.org](https://my.telegram.org)
2. **Create a `.env` file** in your project directory:

```env
API_ID=your_api_id_here
API_HASH=your_api_hash_here
SESSION_NAME=my_session
```

## 🎵 First Download

```bash
# Download audio from a Telegram group
telegram-audio-downloader download @your_group_name

# Download with specific options
telegram-audio-downloader download @your_group_name --format=mp3 --parallel=3
```

## 📊 Check Your Downloads

```bash
# List downloaded files
telegram-audio-downloader list

# Search your downloads  
telegram-audio-downloader search "song name"
```

That's it! For more advanced usage, check out the [CLI Commands](CLI-Commands) guide.
EOF
    echo -e "${GREEN}✅ Created: Quick-Start.md${NC}"
fi

# CLI Commands page
if [ ! -f "$TEMP_WIKI_DIR/CLI-Commands.md" ]; then
    cat > "$TEMP_WIKI_DIR/CLI-Commands.md" << 'EOF'
# 🖥️ CLI Commands Reference

Complete reference for all available command-line options.

## 📥 Download Commands

### Basic Download
```bash
telegram-audio-downloader download @group_name
```

### Advanced Download Options
```bash
# Download with specific format
telegram-audio-downloader download @group_name --format=mp3

# Parallel downloads
telegram-audio-downloader download @group_name --parallel=5

# Filter by file size
telegram-audio-downloader download @group_name --min-size=1MB --max-size=100MB

# Download recent files only
telegram-audio-downloader download @group_name --limit=50 --after=2024-01-01
```

## 🔍 Search Commands

```bash
# Search downloaded files
telegram-audio-downloader search "artist name"

# Fuzzy search with typo tolerance
telegram-audio-downloader search "artsit name" --fuzzy

# Search by format
telegram-audio-downloader search --format=flac
```

## 📊 Management Commands

```bash
# List all downloads
telegram-audio-downloader list

# Show statistics
telegram-audio-downloader stats

# Clean up duplicate files
telegram-audio-downloader cleanup --duplicates

# Database maintenance
telegram-audio-downloader db --vacuum
```

## ⚙️ Configuration

```bash
# Show current configuration
telegram-audio-downloader config --show

# Set default options
telegram-audio-downloader config --set parallel=3
telegram-audio-downloader config --set format=mp3
```

For more detailed examples, see [Examples](Examples).
EOF
    echo -e "${GREEN}✅ Created: CLI-Commands.md${NC}"
fi

# Configuration page
if [ ! -f "$TEMP_WIKI_DIR/Configuration.md" ]; then
    cat > "$TEMP_WIKI_DIR/Configuration.md" << 'EOF'
# ⚙️ Configuration Guide

Learn how to configure Telegram Audio Downloader for optimal performance.

## 📁 Configuration Files

### 1. Environment Variables (`.env`)
```env
# Telegram API Configuration
API_ID=your_api_id_here
API_HASH=your_api_hash_here
SESSION_NAME=my_telegram_session

# Download Settings
DEFAULT_FORMAT=mp3
DEFAULT_QUALITY=320
PARALLEL_DOWNLOADS=3
MAX_FILE_SIZE=100MB

# Storage Settings
DOWNLOAD_DIR=./downloads
DATABASE_PATH=./data/downloads.db

# Performance Settings
RATE_LIMIT_DELAY=1.0
MEMORY_LIMIT_MB=2048
```

### 2. YAML Configuration (`config.yaml`)
```yaml
telegram:
  api_id: your_api_id
  api_hash: your_api_hash
  session_name: my_session

downloads:
  output_directory: "./downloads"
  parallel_count: 3
  resume_downloads: true
  verify_checksums: true

audio:
  default_format: "mp3"
  quality: 320
  normalize_volume: false
  
filters:
  min_file_size: "1MB"
  max_file_size: "100MB"
  allowed_formats:
    - mp3
    - flac
    - ogg

logging:
  level: INFO
  file: "./logs/downloader.log"
  max_size: "10MB"
  backup_count: 5
```

## 🔧 Advanced Configuration

### Rate Limiting
```yaml
rate_limiting:
  enabled: true
  requests_per_second: 2
  burst_size: 5
  adaptive: true
```

### Performance Tuning
```yaml
performance:
  chunk_size: 8192
  connection_pool_size: 10
  timeout_seconds: 300
  retry_attempts: 3
  retry_delay: 2.0
```

### Security Settings
```yaml
security:
  encrypt_session: true
  secure_storage: true
  auto_logout_hours: 24
```

For more configuration examples, see [Best Practices](Best-Practices).
EOF
    echo -e "${GREEN}✅ Created: Configuration.md${NC}"
fi

# Troubleshooting page
if [ ! -f "$TEMP_WIKI_DIR/Troubleshooting.md" ]; then
    cat > "$TEMP_WIKI_DIR/Troubleshooting.md" << 'EOF'
# 🔧 Troubleshooting Guide

Common issues and their solutions.

## 🚨 Common Errors

### Authentication Issues

**Error**: `AUTH_KEY_UNREGISTERED`
```
Solution:
1. Delete your session file
2. Re-run the authentication process
3. Make sure your API credentials are correct
```

**Error**: `PHONE_NUMBER_INVALID`
```
Solution:
1. Check your phone number format (+1234567890)
2. Make sure you have access to SMS/calls
3. Try using the Telegram app first
```

### Download Issues

**Error**: `FILE_REFERENCE_EXPIRED`
```
Solution:
1. This is normal for old files
2. The tool will automatically refresh references
3. If it persists, try downloading newer files first
```

**Error**: `FLOOD_WAIT_X`
```
Solution:
1. This is a rate limit from Telegram
2. Wait X seconds as indicated
3. Reduce parallel downloads (--parallel=1)
4. Enable adaptive rate limiting
```

### Performance Issues

**Problem**: Slow downloads
```
Solutions:
1. Increase parallel downloads: --parallel=5
2. Check your internet connection
3. Use wired connection instead of WiFi
4. Close other network-intensive applications
```

**Problem**: High memory usage
```
Solutions:
1. Reduce parallel downloads
2. Set memory limit in config
3. Close other applications
4. Use --low-memory mode
```

## 🛠️ Debugging

### Enable Verbose Logging
```bash
telegram-audio-downloader download @group --verbose --log-level=DEBUG
```

### Check System Requirements
```bash
# Check Python version (requires 3.11+)
python --version

# Check available memory
python -c "import psutil; print(f'Available memory: {psutil.virtual_memory().available / 1024**3:.1f} GB')"

# Check disk space
df -h .
```

### Test Connection
```bash
# Test Telegram connection
telegram-audio-downloader test --connection

# Validate configuration
telegram-audio-downloader config --validate
```

## 🆘 Getting Help

If you can't solve your issue:

1. **Check [FAQ](FAQ)** for common questions
2. **Search [Issues](https://github.com/Elpablo777/Telegram-Audio-Downloader/issues)** for similar problems
3. **Create a new issue** with:
   - Your operating system
   - Python version
   - Full error message
   - Steps to reproduce
4. **Join [Discussions](https://github.com/Elpablo777/Telegram-Audio-Downloader/discussions)** for community help

## 📊 Diagnostics

Run the built-in diagnostics:
```bash
telegram-audio-downloader diagnose --full
```

This will check:
- ✅ Python version compatibility
- ✅ Required dependencies
- ✅ Telegram API connectivity
- ✅ File system permissions
- ✅ Configuration validity
- ✅ Database integrity
EOF
    echo -e "${GREEN}✅ Created: Troubleshooting.md${NC}"
fi

# Now commit and push to the wiki
echo -e "${BLUE}📤 Pushing to GitHub Wiki...${NC}"
cd "$TEMP_WIKI_DIR"

# Configure git if needed
git config user.name "Wiki Setup Script" 2>/dev/null || true
git config user.email "action@github.com" 2>/dev/null || true

# Add all files
git add .

# Check if there are changes to commit
if git diff --staged --quiet; then
    echo -e "${YELLOW}ℹ️ No changes to commit${NC}"
else
    # Commit changes
    git commit -m "📚 Wiki Setup: Add comprehensive documentation

    ✨ Added pages:
    - Home with navigation and highlights
    - Installation Guide with multi-platform support
    - Quick Start for immediate usage
    - CLI Commands reference
    - Configuration guide with examples
    - FAQ with common questions
    - Architecture Overview (technical deep-dive)
    - Best Practices for optimal usage
    - Troubleshooting guide
    
    📊 Features:
    - Complete navigation structure
    - Rich formatting with emojis
    - Cross-references between pages
    - Practical examples and code snippets
    - Multi-platform installation instructions
    - Comprehensive troubleshooting section"
    
    echo -e "${GREEN}✅ Changes committed${NC}"
    
    # Push to origin (this will create the wiki if it doesn't exist)
    echo -e "${BLUE}🚀 Pushing to GitHub Wiki...${NC}"
    if git push origin main 2>/dev/null || git push origin master 2>/dev/null; then
        echo -e "${GREEN}🎉 Wiki successfully updated!${NC}"
        echo -e "${GREEN}🔗 View at: https://github.com/${REPO_OWNER}/${REPO_NAME}/wiki${NC}"
    else
        echo -e "${RED}❌ Failed to push to wiki${NC}"
        echo -e "${YELLOW}💡 You may need to create the wiki manually first:${NC}"
        echo -e "${YELLOW}   1. Go to https://github.com/${REPO_OWNER}/${REPO_NAME}/wiki${NC}"
        echo -e "${YELLOW}   2. Click 'Create the first page'${NC}"
        echo -e "${YELLOW}   3. Add any content and save${NC}"
        echo -e "${YELLOW}   4. Then run this script again${NC}"
    fi
fi

# Cleanup
cd ..
echo -e "${BLUE}🧹 Cleaning up...${NC}"
rm -rf "$TEMP_WIKI_DIR"

echo -e "${GREEN}✅ Wiki setup complete!${NC}"
echo -e "${BLUE}📖 Wiki pages created:${NC}"
echo -e "   • Home (main navigation)"
echo -e "   • Installation Guide"
echo -e "   • Quick Start"
echo -e "   • CLI Commands"
echo -e "   • Configuration"
echo -e "   • FAQ"
echo -e "   • Architecture Overview"
echo -e "   • Best Practices"
echo -e "   • Troubleshooting"

echo -e "${YELLOW}💡 Note: To set up the wiki, you need to:${NC}"
echo -e "${YELLOW}   1. Go to your repository settings${NC}"
echo -e "${YELLOW}   2. Enable Wiki in the Features section${NC}"
echo -e "${YELLOW}   3. Create the first page manually${NC}"
echo -e "${YELLOW}   4. Then the script can populate it automatically${NC}"

echo -e "${GREEN}🎉 All done! Happy documenting! 🎵✨${NC}"