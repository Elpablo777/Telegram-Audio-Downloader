"""
Tests für die Fortschrittsvisualisierung im Telegram Audio Downloader.
"""

import pytest
import time
from unittest.mock import Mock, patch

from src.telegram_audio_downloader.progress_visualization import (
    DownloadProgress,
    ProgressVisualizer,
    get_progress_visualizer,
    add_download_progress,
    update_download_progress,
    set_download_status,
    show_progress
)


class TestDownloadProgress:
    """Testfälle für die DownloadProgress-Datenklasse."""
    
    def test_initialization(self):
        """Testet die Initialisierung der DownloadProgress-Klasse."""
        progress = DownloadProgress(
            file_id="test_001",
            file_name="test_file.mp3",
            total_size=1000000
        )
        
        assert progress.file_id == "test_001"
        assert progress.file_name == "test_file.mp3"
        assert progress.total_size == 1000000
        assert progress.downloaded == 0
        assert progress.status == "pending"
        assert progress.speed == 0.0
    
    def test_update_progress(self):
        """Testet die Aktualisierung des Download-Fortschritts."""
        progress = DownloadProgress(
            file_id="test_001",
            file_name="test_file.mp3",
            total_size=1000000
        )
        
        # Aktualisiere den Fortschritt
        progress.update(500000)
        
        assert progress.downloaded == 500000
        assert progress.status == "downloading"
        
        # Aktualisiere auf abgeschlossen
        progress.update(1000000)
        
        assert progress.downloaded == 1000000
        assert progress.status == "completed"
    
    def test_progress_percent(self):
        """Testet die Berechnung des Fortschritts in Prozent."""
        progress = DownloadProgress(
            file_id="test_001",
            file_name="test_file.mp3",
            total_size=1000000
        )
        
        # Teste verschiedene Fortschrittsstufen
        assert progress.progress_percent == 0.0
        
        progress.downloaded = 500000
        assert progress.progress_percent == 50.0
        
        progress.downloaded = 1000000
        assert progress.progress_percent == 100.0
    
    def test_elapsed_time(self):
        """Testet die Berechnung der verstrichenen Zeit."""
        progress = DownloadProgress(
            file_id="test_001",
            file_name="test_file.mp3",
            total_size=1000000
        )
        
        # Die verstrichene Zeit sollte größer oder gleich 0 sein
        assert progress.elapsed_time >= 0.0
    
    def test_estimated_time_remaining(self):
        """Testet die Berechnung der geschätzten verbleibenden Zeit."""
        progress = DownloadProgress(
            file_id="test_001",
            file_name="test_file.mp3",
            total_size=1000000
        )
        
        # Ohne Geschwindigkeit sollte die verbleibende Zeit 0 sein
        assert progress.estimated_time_remaining == 0.0
        
        # Setze eine Geschwindigkeit und teste die Berechnung
        progress.speed = 100000  # 100 KB/s
        progress.downloaded = 500000
        
        # Geschätzte verbleibende Zeit: (1000000 - 500000) / 100000 = 5 Sekunden
        assert progress.estimated_time_remaining == 5.0


class TestProgressVisualizer:
    """Testfälle für die ProgressVisualizer-Klasse."""
    
    def test_initialization(self):
        """Testet die Initialisierung des ProgressVisualizers."""
        visualizer = ProgressVisualizer()
        
        assert visualizer is not None
        assert hasattr(visualizer, 'console')
        assert hasattr(visualizer, 'downloads')
        assert len(visualizer.downloads) == 0
    
    def test_add_download(self):
        """Testet das Hinzufügen eines Downloads."""
        visualizer = ProgressVisualizer()
        
        visualizer.add_download("test_001", "test_file.mp3", 1000000)
        
        assert len(visualizer.downloads) == 1
        assert "test_001" in visualizer.downloads
        
        download = visualizer.downloads["test_001"]
        assert download.file_id == "test_001"
        assert download.file_name == "test_file.mp3"
        assert download.total_size == 1000000
    
    def test_update_progress(self):
        """Testet die Aktualisierung des Download-Fortschritts."""
        visualizer = ProgressVisualizer()
        
        # Füge einen Download hinzu
        visualizer.add_download("test_001", "test_file.mp3", 1000000)
        
        # Aktualisiere den Fortschritt
        visualizer.update_progress("test_001", 500000)
        
        download = visualizer.downloads["test_001"]
        assert download.downloaded == 500000
        assert download.status == "downloading"
    
    def test_set_status(self):
        """Testet das Setzen des Download-Status."""
        visualizer = ProgressVisualizer()
        
        # Füge einen Download hinzu
        visualizer.add_download("test_001", "test_file.mp3", 1000000)
        
        # Setze den Status
        visualizer.set_status("test_001", "completed")
        
        download = visualizer.downloads["test_001"]
        assert download.status == "completed"
    
    def test_get_overall_progress(self):
        """Testet die Berechnung des Gesamtfortschritts."""
        visualizer = ProgressVisualizer()
        
        # Füge mehrere Downloads hinzu
        visualizer.add_download("test_001", "test_file1.mp3", 1000000)
        visualizer.add_download("test_002", "test_file2.mp3", 2000000)
        visualizer.add_download("test_003", "test_file3.mp3", 3000000)
        
        # Aktualisiere den Fortschritt
        visualizer.update_progress("test_001", 1000000)  # Abgeschlossen
        visualizer.update_progress("test_002", 1000000)  # Halbwegs
        visualizer.update_progress("test_003", 0)        # Nicht gestartet
        
        # Setze Status
        visualizer.set_status("test_001", "completed")
        visualizer.set_status("test_002", "downloading")
        visualizer.set_status("test_003", "pending")
        
        # Hole den Gesamtfortschritt
        overall = visualizer.get_overall_progress()
        
        assert overall["total_files"] == 3
        assert overall["completed_files"] == 1
        assert overall["failed_files"] == 0
        assert overall["total_size"] == 6000000
        assert overall["downloaded_size"] == 2000000
        assert overall["progress_percent"] == pytest.approx(33.33, 0.01)
    
    def test_get_progress_visualizer_singleton(self):
        """Testet, dass der ProgressVisualizer als Singleton funktioniert."""
        visualizer1 = get_progress_visualizer()
        visualizer2 = get_progress_visualizer()
        
        assert visualizer1 is visualizer2
    
    def test_global_functions(self):
        """Testet die globalen Funktionen."""
        # Füge einen Download hinzu
        add_download_progress("test_global_001", "test_global_file.mp3", 1000000)
        
        # Aktualisiere den Fortschritt
        update_download_progress("test_global_001", 500000)
        
        # Setze den Status
        set_download_status("test_global_001", "completed")
        
        # Zeige den Fortschritt an (sollte ohne Fehler ausgeführt werden können)
        try:
            show_progress()
            # Wenn keine Exception geworfen wird, ist der Test erfolgreich
            assert True
        except Exception as e:
            pytest.fail(f"Fehler beim Anzeigen des Fortschritts: {e}")


if __name__ == "__main__":
    pytest.main([__file__])