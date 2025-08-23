# 🧪 Testprobleme und Lösungsansätze

## Aktuelle Probleme

Beim Ausführen der Tests mit pytest treten Konflikte in der Plugin-Registrierung auf:

```
ValueError: Plugin already registered under a different name: pytest_timeout=<module 'pytest_timeout' from 'C:\Users\Pablo\AppData\Roaming\Python\Python313\site-packages\pytest_timeout.py'>
```

## Ursachenanalyse

1. **Plugin-Konflikte**: Es scheint, dass pytest-timeout auf zwei verschiedene Arten registriert ist
2. **Python 3.13 Kompatibilität**: Mögliche Inkompatibilitäten mit der neuesten Python-Version
3. **Conftest.py Probleme**: Die Konfigurationsdatei könnte doppelte Plugin-Registrierungen enthalten

## Lösungsansätze

### 1. Plugin-Bereinigung

```bash
# Deinstalliere und reinstalliere problematische Plugins
pip uninstall pytest-timeout pytest-asyncio pytest-cov pytest-mock pytest-benchmark
pip install pytest-timeout pytest-asyncio pytest-cov pytest-mock pytest-benchmark
```

### 2. Conftest.py Überprüfung

Überprüfe die Datei `tests/conftest.py` auf doppelte Plugin-Importe:

```python
# In conftest.py sollte es keine expliziten Plugin-Imports geben
# Plugins sollten über die pytest.ini oder pyproject.toml konfiguriert werden
```

### 3. Pytest-Konfiguration

Erstelle oder aktualisiere `pytest.ini` im Projektstamm:

```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = --strict-markers --strict-config
markers =
    slow: marks tests as slow
    integration: marks tests as integration tests
```

### 4. Alternative Testausführung

Führe Tests direkt mit Python aus, um die pytest-Plugin-Probleme zu umgehen:

```bash
# Für einzelne Testdateien
python -m tests.test_memory_optimizations

# Für einzelne Testklassen
python -c "from tests.test_memory_optimizations import TestLRUCache; import unittest; unittest.main(module='tests.test_memory_optimizations', argv=[''], exit=False, verbosity=2)"
```

## Manuelle Testvalidierung

Da die automatisierte Testausführung Probleme hat, können wir die Funktionalität manuell validieren:

### Memory Utils Validierung

```python
# Teste MemoryEfficientSet
from src.telegram_audio_downloader.memory_utils import MemoryEfficientSet
s = MemoryEfficientSet(max_size=5)
s.add("item1")
assert "item1" in s
print("MemoryEfficientSet funktioniert")

# Teste LRUCache
from src.telegram_audio_downloader.downloader import LRUCache
c = LRUCache(max_size=3)
c.put("key1", "value1")
assert c.get("key1") == "value1"
print("LRUCache funktioniert")

# Teste StreamingDataProcessor
from src.telegram_audio_downloader.memory_utils import StreamingDataProcessor
p = StreamingDataProcessor(chunk_size=2)
data = list(range(5))
chunks = list(p.process_in_chunks(iter(data)))
assert len(chunks) == 3
print("StreamingDataProcessor funktioniert")
```

## Nächste Schritte

1. Behebung der pytest-Konfigurationsprobleme
2. Erstellung einer robusten Teststrategie
3. Integration der Tests in den CI/CD-Workflow
4. Verbesserung der Testabdeckung für alle neuen Funktionen