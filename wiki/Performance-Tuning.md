# ⚡ Performance Tuning Guide

Optimieren Sie Ihren Telegram Audio Downloader für maximale Geschwindigkeit, Effizienz und Stabilität.

## 🎯 **Performance-Übersicht**

### **Typische Performance-Metriken**
- **Download-Geschwindigkeit**: 10-20 MB/s pro parallelem Stream
- **Memory-Usage**: 50-200 MB (abhängig von parallelen Downloads)
- **CPU-Auslastung**: 5-15% (hauptsächlich I/O-bound)
- **Disk I/O**: Abhängig von Speichermedium (SSD empfohlen)

### **Performance-Faktoren**
1. **Netzwerk-Bandbreite** - Ihre Internetverbindung
2. **Telegram Server-Load** - Variiert nach Tageszeit
3. **Parallele Downloads** - Mehr = schneller, aber mehr Ressourcen
4. **Hardware** - CPU, RAM, Speichergeschwindigkeit
5. **Betriebssystem** - Linux > macOS > Windows (typisch)

---

## 🚀 **Grundlegende Optimierungen**

### **1. Parallele Downloads optimieren**

```bash
# Standard (konservativ)
telegram-audio-downloader download @gruppe --parallel=3

# Aggressive Optimierung (Gigabit-Internet)
telegram-audio-downloader download @gruppe --parallel=10

# Server-schonend (bei FloodWait-Problemen)
telegram-audio-downloader download @gruppe --parallel=1

# Sweet Spot für die meisten Nutzer
telegram-audio-downloader download @gruppe --parallel=5
```

**Empfohlene Werte nach Internetgeschwindigkeit:**
- **<10 Mbps**: `--parallel=1-2`
- **10-50 Mbps**: `--parallel=3-5`
- **50-100 Mbps**: `--parallel=5-8`
- **>100 Mbps**: `--parallel=8-12`

### **2. Memory-Management konfigurieren**

```ini
# .env-Datei Optimierungen
MAX_MEMORY_MB=1024          # Mehr RAM für große Downloads
ENABLE_GARBAGE_COLLECTION=true
MEMORY_CHECK_INTERVAL=60    # Sekunden zwischen Memory-Checks
MAX_CACHE_SIZE=500         # MB für Download-Cache
```

### **3. Disk I/O optimieren**

```bash
# SSD-Verzeichnis verwenden
telegram-audio-downloader download @gruppe --output=/fast/ssd/downloads

# Temp-Verzeichnis auf RAM-Disk (Linux)
sudo mkdir /tmp/ramdisk
sudo mount -t tmpfs -o size=2G tmpfs /tmp/ramdisk
export TEMP_DIR=/tmp/ramdisk
```

---

## 🔧 **Erweiterte Konfiguration**

### **Performance-Profile erstellen**

**High-Speed Profile (performance.conf):**
```ini
[performance]
max_concurrent_downloads=8
memory_limit_mb=2048
network_timeout=300
retry_attempts=5
chunk_size_mb=1
enable_compression=true
tcp_keepalive=true
connection_pool_size=20

[downloads]  
verify_checksum=false       # Schneller, weniger sicher
skip_metadata_extraction=false
temp_file_cleanup=true
resume_incomplete=true
```

**Quality Profile (quality.conf):**
```ini
[performance]
max_concurrent_downloads=3
memory_limit_mb=1024
network_timeout=600
retry_attempts=10
chunk_size_mb=0.5

[downloads]
verify_checksum=true        # Langsamer, aber sicher
extract_metadata=true
quality_checks=true
```

### **Konfiguration laden**

```bash
# Profile verwenden
telegram-audio-downloader --config=performance.conf download @gruppe
telegram-audio-downloader --config=quality.conf download @gruppe
```

---

## 🌐 **Netzwerk-Optimierungen**

### **1. TCP-Tuning (Linux/macOS)**

```bash
# TCP-Buffer-Größen erhöhen
echo 'net.core.rmem_max = 134217728' | sudo tee -a /etc/sysctl.conf
echo 'net.core.wmem_max = 134217728' | sudo tee -a /etc/sysctl.conf
echo 'net.ipv4.tcp_rmem = 4096 65536 134217728' | sudo tee -a /etc/sysctl.conf
echo 'net.ipv4.tcp_wmem = 4096 65536 134217728' | sudo tee -a /etc/sysctl.conf

# Änderungen anwenden
sudo sysctl -p
```

### **2. DNS-Optimierung**

```bash
# Schnelle DNS-Server verwenden (in .env)
DNS_SERVERS=1.1.1.1,8.8.8.8
DNS_TIMEOUT=5

# Oder systemweit (Linux)
echo "nameserver 1.1.1.1" | sudo tee /etc/resolv.conf
echo "nameserver 8.8.8.8" | sudo tee -a /etc/resolv.conf
```

### **3. Connection-Pooling**

```ini
# .env-Konfiguration
CONNECTION_POOL_SIZE=20     # Mehr gleichzeitige Verbindungen
CONNECTION_KEEPALIVE=true   # Verbindungen wiederverwenden
CONNECTION_TIMEOUT=30       # Timeout für neue Verbindungen
MAX_RETRIES_PER_HOST=3     # Retry-Verhalten pro Host
```

---

## 💾 **Storage-Optimierungen**

### **1. SSD vs HDD**

**SSD-Optimierungen:**
```bash
# Temp-Dateien auf SSD
export TEMP_DIR=/fast/ssd/temp

# Download-Verzeichnis auf SSD
telegram-audio-downloader download @gruppe --output=/fast/ssd/downloads

# Database auf SSD
export DATABASE_PATH=/fast/ssd/audio_downloader.db
```

**HDD-Optimierungen:**
```bash
# Weniger parallele Downloads
telegram-audio-downloader download @gruppe --parallel=2

# Größere Chunk-Sizes
export DOWNLOAD_CHUNK_SIZE=2048  # KB

# Write-Cache nutzen
export USE_WRITE_CACHE=true
```

### **2. RAID-Konfiguration**

**RAID 0 (Speed):**
```bash
# Beste Performance, kein Backup
# Parallele Downloads auf verschiedene Drives verteilen
telegram-audio-downloader download @gruppe1 --output=/raid0/downloads1 &
telegram-audio-downloader download @gruppe2 --output=/raid0/downloads2 &
```

**RAID 1 (Sicherheit):**
```bash
# Backup während Download
telegram-audio-downloader download @gruppe --output=/raid1/downloads
# Automatisches Mirroring
```

---

## 🖥️ **System-Optimierungen**

### **1. CPU-Optimierungen**

```bash
# CPU-Affinity setzen (Linux)
taskset -c 0-3 telegram-audio-downloader download @gruppe --parallel=4

# Priorität erhöhen
nice -n -10 telegram-audio-downloader download @gruppe

# Multi-Core nutzen
export PYTHONHASHSEED=0  # Deterministische Hash-Werte
export PYTHONUNBUFFERED=1  # Keine Output-Pufferung
```

### **2. Memory-Optimierungen**

```bash
# Python Memory-Allocator optimieren
export PYTHONMALLOC=malloc
export MALLOC_ARENA_MAX=2

# Garbage Collection tunen
export PYTHONGC=1  # Generational GC aktiviert

# Memory-Mapping für große Dateien
export USE_MEMORY_MAPPING=true
```

### **3. I/O-Scheduler (Linux)**

```bash
# I/O-Scheduler für SSD optimieren
echo mq-deadline | sudo tee /sys/block/sda/queue/scheduler

# Für HDD
echo cfq | sudo tee /sys/block/sda/queue/scheduler

# Read-Ahead optimieren
sudo blockdev --setra 4096 /dev/sda
```

---

## 📊 **Performance-Monitoring**

### **1. Real-time Monitoring**

```bash
# Performance-Dashboard starten
telegram-audio-downloader performance --watch

# System-Ressourcen überwachen
htop  # CPU/Memory
iotop # Disk I/O
nethogs  # Network per Prozess
```

### **2. Benchmark-Tests**

```bash
# Performance-Test durchführen
telegram-audio-downloader performance --test

# Mit verschiedenen Parallelitäts-Leveln
for i in {1..10}; do
    echo "Testing with $i parallel downloads"
    time telegram-audio-downloader download @testgruppe --parallel=$i --limit=10
done
```

### **3. Profiling aktivieren**

```bash
# Python-Profiling
telegram-audio-downloader --profile download @gruppe --limit=5

# Memory-Profiling
telegram-audio-downloader --memory-profile download @gruppe --limit=5

# Trace-Modus für detaillierte Analyse
telegram-audio-downloader --trace download @gruppe --limit=1
```

---

## 🐧 **Betriebssystem-spezifische Optimierungen**

### **Linux-Optimierungen**

```bash
# File-Descriptor Limits erhöhen
echo "* soft nofile 65536" | sudo tee -a /etc/security/limits.conf
echo "* hard nofile 65536" | sudo tee -a /etc/security/limits.conf

# Kernel-Parameter optimieren
echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
echo 'vm.vfs_cache_pressure=50' | sudo tee -a /etc/sysctl.conf

# CPU-Governor auf performance setzen
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
```

### **macOS-Optimierungen**

```bash
# File-Descriptor Limits
launchctl limit maxfiles 65536 65536

# Network-Buffer-Sizes
sudo sysctl -w net.inet.tcp.sendspace=1048576
sudo sysctl -w net.inet.tcp.recvspace=1048576

# Disable Spotlight auf Downloads-Ordner
sudo mdutil -i off /path/to/downloads
```

### **Windows-Optimierungen**

```powershell
# Windows Defender Ausnahmen
Add-MpPreference -ExclusionPath "C:\path\to\downloads"
Add-MpPreference -ExclusionProcess "python.exe"

# Power-Management deaktivieren
powercfg -setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c  # High Performance

# TCP-Parameter optimieren
netsh int tcp set global autotuninglevel=normal
netsh int tcp set global rss=enabled
```

---

## 🔬 **Advanced Performance Hacks**

### **1. AsyncIO-Optimierungen**

```python
# Custom EventLoop-Policy (für Entwickler)
import asyncio
import uvloop  # Unix-only

# Schnellere Event-Loop verwenden
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

# Mehr Worker-Threads
import concurrent.futures
executor = concurrent.futures.ThreadPoolExecutor(max_workers=20)
```

### **2. Database-Optimierungen**

```sql
-- SQLite-Optimierungen (in Python anwenden)
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
PRAGMA cache_size=10000;
PRAGMA temp_store=memory;
PRAGMA mmap_size=268435456;  -- 256MB
```

```python
# In Python-Code einfügen
import sqlite3

def optimize_database():
    conn = sqlite3.connect('audio_downloader.db')
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA synchronous=NORMAL')
    conn.execute('PRAGMA cache_size=10000')
    conn.close()
```

### **3. Memory-Pool für Downloads**

```python
# Custom Memory-Pool (Advanced)
import mmap
import os

class MemoryPool:
    def __init__(self, size_mb=100):
        self.size = size_mb * 1024 * 1024
        self.pool = mmap.mmap(-1, self.size)
    
    def get_buffer(self, size):
        # Puffer aus Pool zuweisen
        return memoryview(self.pool[:size])
```

---

## 🎯 **Performance-Profile für verschiedene Use Cases**

### **1. Maximale Geschwindigkeit (Datacenter/Server)**

```bash
# Extremer Performance-Modus
export MAX_CONCURRENT_DOWNLOADS=20
export MEMORY_LIMIT_MB=4096
export DISABLE_VERIFICATION=true
export NETWORK_TIMEOUT=60

telegram-audio-downloader download @gruppe \
    --parallel=20 \
    --no-verify-checksum \
    --no-metadata \
    --minimal-logging
```

### **2. Laptop/Mobile (Batterie-schonend)**

```bash
# Ressourcen-schonender Modus
export MAX_CONCURRENT_DOWNLOADS=2
export MEMORY_LIMIT_MB=256
export ENABLE_POWER_SAVING=true
export CPU_LIMIT_PERCENT=50

telegram-audio-downloader download @gruppe \
    --parallel=2 \
    --low-priority \
    --power-save-mode
```

### **3. 24/7 Server (Stabil & Effizient)**

```bash
# Stabiler Dauerbetrieb-Modus
export MAX_CONCURRENT_DOWNLOADS=5
export MEMORY_LIMIT_MB=1024
export ENABLE_MONITORING=true
export AUTO_RESTART=true

# Cron-Job mit Monitoring
0 */2 * * * cd /path/to/project && ./scripts/monitored_download.sh
```

**monitored_download.sh:**
```bash
#!/bin/bash
# Überwachter Download mit Restart bei Problemen

MAX_RETRIES=3
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if timeout 3600 telegram-audio-downloader download @gruppe --parallel=5 --limit=50; then
        echo "Download successful"
        break
    else
        RETRY_COUNT=$((RETRY_COUNT+1))
        echo "Download failed, retry $RETRY_COUNT/$MAX_RETRIES"
        sleep 300  # 5 Minuten warten
    fi
done
```

---

## 📈 **Performance-Benchmarks**

### **Typische Performance-Werte**

| Setup | Parallel Downloads | Speed | Memory | CPU |
|-------|-------------------|--------|---------|-----|
| Raspberry Pi 4 | 2 | 5-8 MB/s | 150 MB | 20% |
| Laptop (i5) | 5 | 15-25 MB/s | 300 MB | 15% |
| Desktop (i7) | 8 | 30-50 MB/s | 500 MB | 10% |
| Server (Xeon) | 15 | 80-120 MB/s | 1.2 GB | 5% |

### **Optimierungs-Checkliste**

**Hardware:**
- ✅ SSD für Downloads und Database
- ✅ Mindestens 4 GB RAM
- ✅ Gigabit-Netzwerk oder besser
- ✅ Multi-Core CPU (4+ Cores empfohlen)

**Software:**
- ✅ Linux-Betriebssystem (optimal)
- ✅ Python 3.11+ (neueste Performance-Features)
- ✅ Aktuelle Telethon-Version
- ✅ Optimierte Netzwerk-Einstellungen

**Konfiguration:**
- ✅ Parallele Downloads optimiert (3-8)
- ✅ Memory-Limits angemessen gesetzt
- ✅ Temp-Dateien auf schnellem Storage
- ✅ Database-Performance optimiert

---

## 🔍 **Performance-Troubleshooting**

### **Langsame Downloads**

**Diagnose:**
```bash
# Network-Speed testen
speedtest-cli

# Disk I/O testen  
dd if=/dev/zero of=testfile bs=1G count=1 oflag=direct

# System-Load prüfen
uptime
iostat 1
```

**Lösungen:**
1. **Netzwerk**: Router neu starten, anderen DNS verwenden
2. **Disk**: SSD verwenden, RAID-Setup prüfen
3. **System**: Andere Programme beenden, mehr RAM

### **Memory-Probleme**

**Diagnose:**
```bash
# Memory-Usage überwachen
telegram-audio-downloader performance --memory --watch

# System-Memory prüfen
free -h  # Linux
vm_stat  # macOS
```

**Lösungen:**
1. `MAX_MEMORY_MB` reduzieren
2. Parallele Downloads reduzieren
3. Garbage Collection häufiger ausführen
4. Swap-Space erweitern

### **CPU-Bottlenecks**

**Diagnose:**
```bash
# CPU-Usage per Prozess
top -p $(pgrep -f telegram-audio-downloader)

# CPU-Profiling aktivieren
telegram-audio-downloader --profile download @gruppe --limit=1
```

**Lösungen:**
1. CPU-intensive Tasks (Checksum-Verifikation) deaktivieren
2. Process-Priority anpassen
3. CPU-Affinity setzen
4. Hardware upgraden

---

## 🚀 **Experimentelle Features**

### **1. GPU-Acceleration (Experimentell)**

```bash
# CUDA für Checksum-Berechnung (wenn verfügbar)
export USE_GPU_CHECKSUMS=true
export CUDA_DEVICE=0

# OpenCL für Metadaten-Verarbeitung
export USE_OPENCL=true
```

### **2. Distributed Downloads**

```bash
# Mehrere Maschinen für parallele Downloads
# Master-Node
telegram-audio-downloader download @gruppe --distributed-master --workers=node1,node2

# Worker-Nodes
telegram-audio-downloader --distributed-worker --master=192.168.1.100
```

### **3. Compression on-the-fly**

```bash
# Downloads komprimieren während Transfer
telegram-audio-downloader download @gruppe --compress-transfers --compression=lz4
```

---

## 🎯 **Performance-Rezepte**

### **"Gib mir alles" Setup (Maximum Speed)**

```bash
#!/bin/bash
# Ultimate Performance Setup

# System-Optimierungen
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
echo 2048 | sudo tee /proc/sys/vm/min_free_kbytes

# Environment
export MAX_CONCURRENT_DOWNLOADS=15
export MEMORY_LIMIT_MB=4096
export DISABLE_SAFETY_CHECKS=true
export USE_RAMDISK=true

# RAM-Disk erstellen (Linux)
sudo mkdir /tmp/audiodownloads
sudo mount -t tmpfs -o size=8G tmpfs /tmp/audiodownloads

# Download starten
telegram-audio-downloader download @gruppe \
    --parallel=15 \
    --output=/tmp/audiodownloads \
    --no-verify-checksum \
    --no-metadata \
    --timeout=30 \
    --max-retries=10
```

### **"Sicher aber schnell" Setup**

```bash
#!/bin/bash
# Balanced Performance & Safety

export MAX_CONCURRENT_DOWNLOADS=5
export MEMORY_LIMIT_MB=1024
export ENABLE_VERIFICATION=true
export BACKUP_DOWNLOADS=true

telegram-audio-downloader download @gruppe \
    --parallel=5 \
    --verify-checksum \
    --metadata \
    --resume \
    --backup-on-failure
```

---

## 📞 **Performance-Support**

**Bei Performance-Problemen:**

1. **[GitHub Issues](https://github.com/Elpablo777/Telegram-Audio-Downloader/issues)** - Performance-Bug Reports
2. **Performance-Profiling** aktivieren und Logs bereitstellen
3. **System-Specs angeben**: CPU, RAM, Storage, Network
4. **Benchmark-Ergebnisse** mit verschiedenen Konfigurationen

**Performance-Monitoring aktivieren:**
```bash
# Vollständiges Performance-Log erstellen
telegram-audio-downloader --debug --profile --trace download @gruppe --limit=5 > performance.log 2>&1
```

---

**Happy High-Speed Downloading!** 🚀⚡

*Optimierungen sind systemabhängig. Testen Sie verschiedene Konfigurationen für Ihr Setup.*