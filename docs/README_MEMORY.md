# 🧠 Speicheroptimierung im Telegram Audio Downloader

## Übersicht

Das Telegram Audio Downloader-Projekt wurde um umfassende Speicheroptimierungen erweitert, um den Ressourcenverbrauch bei großen Download-Mengen zu minimieren und die Performance zu steigern. Diese Optimierungen umfassen:

- Implementierung eines LRU-Caches für bereits heruntergeladene Dateien
- Speichereffiziente Set-Implementierung mit Größenbegrenzung
- Stream-basierte Datenverarbeitung für große Datenmengen
- Memory-Monitoring und automatische Bereinigung
- Object-Pooling für teure Objekte

## Neue Komponenten

### LRUCache (in downloader.py)

Ein Least Recently Used (LRU) Cache mit fester Größe für speichereffizientes Caching von Datei-IDs bereits heruntergeladener Dateien.

**Features:**
- Begrenzte Größe (max. 50.000 Einträge)
- Automatische Entfernung ältester Einträge bei Überschreitung der Kapazität
- Effiziente Zugriffszeiten durch OrderedDict

**Verwendung:**
```python
# In der AudioDownloader-Klasse
self._downloaded_files_cache = LRUCache(max_size=50000)
```

### MemoryEfficientSet (in memory_utils.py)

Eine speichereffiziente Set-Implementierung mit Größenbegrenzung und automatischer Bereinigung. Verwendet eine Kombination aus In-Memory-Set und Weak-References für große Datenmengen.

**Features:**
- Größenbegrenzung mit max_size-Parameter
- Automatische Bereinigung bei Überschreitung der Kapazität
- LRU-ähnliches Verhalten durch deque-basierte Zugriffsverfolgung
- Weak-Reference-Cache für nicht mehr primär benötigte Elemente

**Verwendung:**
```python
# Beispiel für die Verwendung
efficient_set = MemoryEfficientSet(max_size=10000)
efficient_set.add("item_key")
if "item_key" in efficient_set:
    print("Item gefunden")
```

### StreamingDataProcessor (in memory_utils.py)

Verarbeitet große Datenmengen stream-basiert, um Speicher zu schonen.

**Features:**
- Chunk-basierte Verarbeitung mit konfigurierbarer Chunk-Größe
- Zeilenweises Lesen von Dateien ohne vollständiges Laden in den Speicher
- Speichereffiziente Generatoren

**Verwendung:**
```python
# Verarbeitung von Daten in Chunks
processor = StreamingDataProcessor(chunk_size=1000)
for chunk in processor.process_in_chunks(data_source):
    # Verarbeite Chunk
    pass

# Zeilenweises Lesen einer Datei
for line in processor.process_file_lines(file_path):
    # Verarbeite Zeile
    pass
```

### MemoryMonitor (in memory_utils.py)

Überwacht den Speicherverbrauch und führt automatische Bereinigung durch.

**Features:**
- Echtzeit-Monitoring des Speicherverbrauchs
- Konfigurierbare Warn- und Kritische-Schwellenwerte
- Automatische Garbage Collection bei Speicherdruck
- Registrierung von Cleanup-Callbacks

**Verwendung:**
```python
# Globale Instanz abrufen
monitor = get_memory_monitor()

# Speicherbereinigung durchführen
freed_objects = monitor.perform_cleanup()

# Registrierung von Cleanup-Callbacks
monitor.register_cleanup_callback(my_cleanup_function)
```

### ObjectPool (in memory_utils.py)

Object Pool für teure Objekte, um Neuerstellung zu vermeiden.

**Features:**
- Pool-basierte Objektverwaltung mit konfigurierbarer Maximalgröße
- Weak-Reference-Tracking von in Verwendung befindlichen Objekten
- Factory-Funktionen für die Erstellung neuer Objekte

**Verwendung:**
```python
# Pool abrufen oder erstellen
pool = get_object_pool("my_pool", my_factory_function, max_size=10)

# Objekt aus Pool holen
obj = pool.acquire()

# Objekt zurückgeben
pool.release(obj)
```

## Integration in bestehende Komponenten

### AudioDownloader-Klasse

Die [AudioDownloader](file://c:\Users\Pablo\Desktop\Telegram%20Musik%20Tool\src\telegram_audio_downloader\downloader.py#L75-L627)-Klasse verwendet den neuen [LRUCache](file://c:\Users\Pablo\Desktop\Telegram%20Musik%20Tool\src\telegram_audio_downloader\downloader.py#L73-L73) für das Caching bereits heruntergeladener Dateien:

```python
# Initialisierung des Caches
self._downloaded_files_cache = LRUCache(max_size=50000)

# Verwendung beim Laden bereits heruntergeladener Dateien
def _load_downloaded_files(self) -> None:
    downloaded_file_ids = [
        audio.file_id
        for audio in AudioFile.select(AudioFile.file_id).where(
            AudioFile.status == DownloadStatus.COMPLETED.value
        )
    ]
    
    for file_id in downloaded_file_ids:
        self._downloaded_files_cache.put(file_id, True)
```

### Performance-Monitor

Die [PerformanceMonitor](file://c:\Users\Pablo\Desktop\Telegram%20Musik%20Tool\src\telegram_audio_downloader\performance.py#L235-L367)-Klasse integriert den [MemoryManager](file://c:\Users\Pablo\Desktop\Telegram%20Musik%20Tool\src\telegram_audio_downloader\performance.py#L101-L165) für effizientes Memory-Management:

```python
# Memory-Check vor Downloads
def before_download(self, file_size_mb: float) -> bool:
    if self.memory_manager.check_memory_pressure():
        await asyncio.sleep(1)  # Kurze Pause nach GC
```

### CLI-Kommando "performance"

Das neue `performance --cleanup` Kommando verwendet die globalen Speicherbereinigungsfunktionen:

```python
# Memory Cleanup
freed_objects = perform_memory_cleanup()
console.print(
    f"[green]✓ Garbage Collection: {freed_objects} Objekte bereinigt[/green]"
)
```

## Performance-Vorteile

Durch die Implementierung dieser speichereffizienten Komponenten wurden folgende Vorteile erreicht:

1. **Reduzierter Speicherverbrauch**: 
   - Begrenzung des Caches für heruntergeladene Dateien auf 50.000 Einträge
   - Automatische Bereinigung bei Speicherdruck
   - Weak-References für nicht mehr primär benötigte Daten

2. **Verbesserte Performance**:
   - Schnellerer Zugriff auf bereits heruntergeladene Dateien durch LRU-Caching
   - Reduzierte Garbage Collection-Pausen durch proaktives Memory-Management
   - Effizientere Verarbeitung großer Datenmengen durch Streaming

3. **Skalierbarkeit**:
   - Verarbeitung von größeren Download-Mengen ohne Speicherprobleme
   - Bessere Performance bei langlaufenden Download-Sessions
   - Stabile Speicherverwendung auch bei umfangreichen Downloads

## Verwendung der neuen Funktionen

### CLI-Befehle

```bash
# Speicherbereinigung durchführen
telegram-audio-downloader performance --cleanup

# Echtzeit-Monitoring mit Speicheranzeige
telegram-audio-downloader performance --watch
```

### Programmatische Verwendung

```python
from telegram_audio_downloader.memory_utils import (
    perform_memory_cleanup,
    get_memory_monitor,
    get_object_pool
)

# Globale Speicherbereinigung
freed_objects = perform_memory_cleanup()

# Memory-Monitor verwenden
monitor = get_memory_monitor()
memory_info = monitor.get_memory_usage()

# Object-Pool verwenden
pool = get_object_pool("example_pool", my_factory_func)
obj = pool.acquire()
# ... Verwendung des Objekts ...
pool.release(obj)
```

## Zukünftige Optimierungen

Geplante weitere Speicheroptimierungen:

1. **Lazy Loading**: Verzögertes Laden von Metadaten nur bei Bedarf
2. **Datenbank-Caching**: Intelligenteres Caching von Datenbankabfragen
3. **Memory-Mapped Files**: Verwendung von Memory-Mapped Files für große Dateioperationen
4. **Profilierung**: Kontinuierliche Profilierung zur Identifikation von Speicherengpässen

Diese Dokumentation wurde erstellt, um die neuen speichereffizienten Komponenten des Telegram Audio Downloaders zu erklären und deren Verwendung zu dokumentieren.