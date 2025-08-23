"""
Gemeinsame pytest-Konfiguration und Fixtures.
"""
import pytest
import tempfile
import os
import shutil
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock

# Sicherstellen, dass der src-Pfad in PYTHONPATH ist
import sys
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def temp_project_dir():
    """Erstellt ein temporäres Projektverzeichnis für Tests."""
    temp_dir = tempfile.mkdtemp(prefix="telegram_audio_test_")
    temp_path = Path(temp_dir)
    
    # Unterverzeichnisse erstellen
    (temp_path / "data").mkdir()
    (temp_path / "downloads").mkdir() 
    (temp_path / "config").mkdir()
    
    yield temp_path
    
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_telegram_client():
    """Erstellt einen Mock Telegram-Client."""
    client = AsyncMock()
    client.start = AsyncMock()
    client.disconnect = AsyncMock()
    client.get_entity = AsyncMock()
    client.get_messages = AsyncMock()
    client.download_media = AsyncMock()
    client.is_connected.return_value = True
    
    return client


@pytest.fixture
def mock_audio_file():
    """Erstellt eine Mock-Audiodatei für Tests."""
    mock_file = MagicMock()
    mock_file.id = 123456
    mock_file.size = 1024000
    mock_file.mime_type = "audio/mpeg"
    mock_file.file_reference = b"fake_reference"
    
    # Mock AttributeAudio
    mock_attr = MagicMock()
    mock_attr.title = "Test Song"
    mock_attr.performer = "Test Artist"
    mock_attr.duration = 180
    
    mock_file.attributes = [mock_attr]
    
    return mock_file


@pytest.fixture
def mock_telegram_group():
    """Erstellt eine Mock Telegram-Gruppe."""
    group = MagicMock()
    group.id = 987654321
    group.title = "Test Music Group"
    group.username = "testmusicgroup"
    
    return group


@pytest.fixture
def sample_env_vars(monkeypatch):
    """Setzt Test-Umgebungsvariablen."""
    monkeypatch.setenv("API_ID", "12345")
    monkeypatch.setenv("API_HASH", "test_api_hash")
    monkeypatch.setenv("SESSION_NAME", "test_session")


@pytest.fixture
def cleanup_test_files():
    """Räumt Test-Dateien nach dem Test auf."""
    test_files = []
    
    def add_file(file_path):
        test_files.append(Path(file_path))
    
    yield add_file
    
    # Cleanup
    for file_path in test_files:
        if file_path.exists():
            if file_path.is_file():
                file_path.unlink()
            elif file_path.is_dir():
                shutil.rmtree(file_path, ignore_errors=True)


# Marker für verschiedene Test-Kategorien
def pytest_configure(config):
    """Konfiguration für pytest."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "network: mark test as requiring network access"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


def pytest_collection_modifyitems(config, items):
    """Automatisches Markieren von Tests basierend auf Namen."""
    for item in items:
        # Markiere Tests mit 'integration' im Namen
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        
        # Markiere Tests mit 'network' im Namen
        if "network" in item.nodeid:
            item.add_marker(pytest.mark.network)
        
        # Markiere langsame Tests
        if "slow" in item.nodeid or "download" in item.nodeid:
            item.add_marker(pytest.mark.slow)


@pytest.fixture(autouse=True)
def reset_logging():
    """Setzt Logging-Konfiguration für jeden Test zurück."""
    import logging
    
    # Logging-Level zurücksetzen
    logging.getLogger().setLevel(logging.WARNING)
    
    # Alle Handler entfernen
    for handler in logging.getLogger().handlers[:]:
        logging.getLogger().removeHandler(handler)
    
    yield
    
    # Nach dem Test wieder zurücksetzen
    for handler in logging.getLogger().handlers[:]:
        logging.getLogger().removeHandler(handler)