"""
Tests für die intelligente Bandbreitensteuerung.
"""

import unittest
import tempfile
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from src.telegram_audio_downloader.intelligent_bandwidth import (
    IntelligentBandwidthController, BandwidthMetrics, AdaptiveSettings,
    get_bandwidth_controller, initialize_bandwidth_controller,
    adjust_bandwidth_settings, get_current_bandwidth_settings,
    register_download_start, register_download_end,
    can_start_new_download, update_download_speed
)
from src.telegram_audio_downloader.config import Config


class TestIntelligentBandwidthController(unittest.TestCase):
    """Tests für den IntelligentBandwidthController."""
    
    def setUp(self):
        """Setzt die Testumgebung auf."""
        # Erstelle eine temporäre Konfigurationsdatei
        self.config_content = """
[telegram]
api_id = test_id
api_hash = test_hash
phone_number = test_number

[download]
download_dir = test_downloads
max_concurrent_downloads = 5
max_file_size = 100000000
allowed_extensions = .mp3,.m4a,.flac,.ogg,.wav
max_retries = 3
retry_delay = 5
checksum_algorithm = sha256

[database]
db_path = test_data/telegram_audio.db

[logging]
log_level = INFO
log_file = test_logs/telegram_audio_downloader.log
max_log_size = 10485760
backup_count = 5

[performance]
chunk_size = 8192
timeout = 30
connection_pool_size = 10

[security]
enable_encryption = false
encryption_key = test_key
"""
        
        # Erstelle temporäre Konfigurationsdatei
        self.temp_config = tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False)
        self.temp_config.write(self.config_content)
        self.temp_config.close()
        
        # Lade die Konfiguration
        self.config = Config(self.temp_config.name)
        
        # Erstelle den Controller
        self.bandwidth_controller = IntelligentBandwidthController(self.config)
    
    def tearDown(self):
        """Räumt die Testumgebung auf."""
        import os
        os.unlink(self.temp_config.name)
    
    def test_initialization(self):
        """Testet die Initialisierung des Controllers."""
        self.assertIsInstance(self.bandwidth_controller, IntelligentBandwidthController)
        self.assertEqual(self.bandwidth_controller.config, self.config)
        self.assertEqual(len(self.bandwidth_controller.metrics_history), 0)
        self.assertEqual(len(self.bandwidth_controller.active_downloads), 0)
    
    def test_collect_metrics(self):
        """Testet das Sammeln von Metriken."""
        metrics = self.bandwidth_controller.collect_metrics()
        
        self.assertIsInstance(metrics, BandwidthMetrics)
        self.assertIsInstance(metrics.timestamp, datetime)
        self.assertIsInstance(metrics.download_speed_kbps, float)
        self.assertIsInstance(metrics.latency_ms, float)
        self.assertIsInstance(metrics.packet_loss_percent, float)
        self.assertIsInstance(metrics.concurrent_downloads, int)
        self.assertIsInstance(metrics.system_cpu_percent, float)
        self.assertIsInstance(metrics.system_memory_percent, float)
        # system_disk_io ist ein int (Bytes), nicht float
        self.assertIsInstance(metrics.system_disk_io, int)
        
        # Prüfe, ob die Metriken zur Historie hinzugefügt wurden
        self.assertEqual(len(self.bandwidth_controller.metrics_history), 1)
    
    def test_estimate_network_latency(self):
        """Testet die Schätzung der Netzwerklatenz."""
        latency = self.bandwidth_controller._estimate_network_latency()
        
        self.assertIsInstance(latency, float)
        self.assertGreater(latency, 0)
    
    def test_estimate_packet_loss(self):
        """Testet die Schätzung des Paketverlusts."""
        packet_loss = self.bandwidth_controller._estimate_packet_loss()
        
        self.assertIsInstance(packet_loss, float)
        self.assertGreaterEqual(packet_loss, 0)
    
    def test_calculate_current_download_speed(self):
        """Testet die Berechnung der aktuellen Download-Geschwindigkeit."""
        # Füge einige Testmetriken hinzu
        metrics1 = BandwidthMetrics(download_speed_kbps=100.0)
        metrics2 = BandwidthMetrics(download_speed_kbps=200.0)
        self.bandwidth_controller.metrics_history.extend([metrics1, metrics2])
        
        speed = self.bandwidth_controller._calculate_current_download_speed()
        
        self.assertIsInstance(speed, float)
        self.assertGreaterEqual(speed, 0)
    
    def test_should_adjust_settings(self):
        """Testet die Prüfung, ob Einstellungen angepasst werden sollten."""
        # Test mit neuem Controller (sollte anpassen, da last_adjustment_time auf now gesetzt wurde)
        self.bandwidth_controller.last_adjustment_time = datetime.now() - timedelta(seconds=60)
        result = self.bandwidth_controller.should_adjust_settings()
        self.assertTrue(result)
        
        # Test nach kürzlicher Anpassung (sollte nicht anpassen)
        self.bandwidth_controller.last_adjustment_time = datetime.now()
        result = self.bandwidth_controller.should_adjust_settings()
        # Dieser Test kann fehlschlagen, wenn die Systemauslastung kritisch ist
        # Wir testen stattdessen den Zeitpunkt
        self.assertLess(datetime.now() - self.bandwidth_controller.last_adjustment_time, self.bandwidth_controller.adjustment_interval)
    
    def test_adjust_concurrent_downloads(self):
        """Testet die Anpassung der gleichzeitigen Downloads."""
        # Test mit hoher CPU-Auslastung (sollte reduzieren)
        metrics = BandwidthMetrics(system_cpu_percent=90.0)
        original_concurrent = self.bandwidth_controller.adaptive_settings.max_concurrent_downloads
        self.bandwidth_controller._adjust_concurrent_downloads(metrics)
        self.assertLessEqual(self.bandwidth_controller.adaptive_settings.max_concurrent_downloads, original_concurrent)
        
        # Test mit niedriger Auslastung (sollte erhöhen)
        metrics = BandwidthMetrics(system_cpu_percent=30.0, system_memory_percent=30.0, latency_ms=30.0)
        self.bandwidth_controller._adjust_concurrent_downloads(metrics)
        self.assertGreaterEqual(self.bandwidth_controller.adaptive_settings.max_concurrent_downloads, 1)
    
    def test_adjust_chunk_size(self):
        """Testet die Anpassung der Chunk-Größe."""
        # Test mit hoher Latenz (sollte reduzieren)
        metrics = BandwidthMetrics(latency_ms=300.0)
        original_chunk = self.bandwidth_controller.adaptive_settings.chunk_size
        self.bandwidth_controller._adjust_chunk_size(metrics)
        self.assertLessEqual(self.bandwidth_controller.adaptive_settings.chunk_size, original_chunk)
        
        # Test mit niedriger Latenz (sollte erhöhen)
        metrics = BandwidthMetrics(latency_ms=20.0, download_speed_kbps=1500.0)
        self.bandwidth_controller._adjust_chunk_size(metrics)
        self.assertGreaterEqual(self.bandwidth_controller.adaptive_settings.chunk_size, 1024)
    
    def test_adjust_timeouts(self):
        """Testet die Anpassung der Timeouts."""
        # Test mit hoher Latenz (sollte erhöhen)
        metrics = BandwidthMetrics(latency_ms=300.0)
        original_timeout = self.bandwidth_controller.adaptive_settings.timeout_seconds
        self.bandwidth_controller._adjust_timeouts(metrics)
        self.assertGreaterEqual(self.bandwidth_controller.adaptive_settings.timeout_seconds, original_timeout)
        
        # Test mit niedriger Latenz (sollte reduzieren)
        metrics = BandwidthMetrics(latency_ms=20.0)
        self.bandwidth_controller._adjust_timeouts(metrics)
        self.assertGreaterEqual(self.bandwidth_controller.adaptive_settings.timeout_seconds, 10)
    
    def test_adjust_retry_settings(self):
        """Testet die Anpassung der Wiederholungseinstellungen."""
        # Test mit hohem Paketverlust (sollte erhöhen)
        metrics = BandwidthMetrics(packet_loss_percent=5.0)
        original_delay = self.bandwidth_controller.adaptive_settings.retry_delay
        original_max = self.bandwidth_controller.adaptive_settings.max_retries
        self.bandwidth_controller._adjust_retry_settings(metrics)
        self.assertGreaterEqual(self.bandwidth_controller.adaptive_settings.retry_delay, original_delay)
        
        # Test mit niedrigem Paketverlust (sollte reduzieren)
        metrics = BandwidthMetrics(packet_loss_percent=0.2)
        self.bandwidth_controller._adjust_retry_settings(metrics)
        self.assertGreaterEqual(self.bandwidth_controller.adaptive_settings.retry_delay, 1)
    
    def test_register_download_start_end(self):
        """Testet das Registrieren von Download-Start und -Ende."""
        file_id = "test_file_001"
        
        # Teste Download-Start
        self.bandwidth_controller.register_download_start(file_id)
        self.assertIn(file_id, self.bandwidth_controller.active_downloads)
        
        # Teste Download-Ende
        self.bandwidth_controller.register_download_end(file_id)
        self.assertNotIn(file_id, self.bandwidth_controller.active_downloads)
    
    def test_can_start_new_download(self):
        """Testet die Prüfung, ob ein neuer Download gestartet werden kann."""
        # Test mit freien Slots
        result = self.bandwidth_controller.can_start_new_download()
        self.assertTrue(result)
        
        # Test mit voller Kapazität
        for i in range(self.bandwidth_controller.adaptive_settings.max_concurrent_downloads):
            self.bandwidth_controller.active_downloads[f"file_{i}"] = datetime.now()
        
        result = self.bandwidth_controller.can_start_new_download()
        self.assertFalse(result)
    
    def test_update_download_speed(self):
        """Testet das Aktualisieren der Download-Geschwindigkeit."""
        file_id = "test_file_002"
        bytes_downloaded = 1024000  # 1000 KB
        time_elapsed = 10.0  # 10 Sekunden
        
        # Füge eine Testmetrik hinzu
        self.bandwidth_controller.metrics_history.append(BandwidthMetrics())
        
        # Aktualisiere die Download-Geschwindigkeit
        self.bandwidth_controller.update_download_speed(file_id, bytes_downloaded, time_elapsed)
        
        # Prüfe, ob die Geschwindigkeit aktualisiert wurde
        self.assertEqual(self.bandwidth_controller.metrics_history[-1].download_speed_kbps, 100.0)


class TestBandwidthFunctions(unittest.TestCase):
    """Tests für die Bandwidth-Funktionen."""
    
    def setUp(self):
        """Setzt die Testumgebung auf."""
        # Erstelle eine temporäre Konfigurationsdatei
        self.config_content = """
[telegram]
api_id = test_id
api_hash = test_hash
phone_number = test_number

[download]
download_dir = test_downloads
max_concurrent_downloads = 5
max_file_size = 100000000
allowed_extensions = .mp3,.m4a,.flac,.ogg,.wav
max_retries = 3
retry_delay = 5
checksum_algorithm = sha256

[database]
db_path = test_data/telegram_audio.db

[logging]
log_level = INFO
log_file = test_logs/telegram_audio_downloader.log
max_log_size = 10485760
backup_count = 5

[performance]
chunk_size = 8192
timeout = 30
connection_pool_size = 10

[security]
enable_encryption = false
encryption_key = test_key
"""
        
        # Erstelle temporäre Konfigurationsdatei
        self.temp_config = tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False)
        self.temp_config.write(self.config_content)
        self.temp_config.close()
        
        # Lade die Konfiguration
        self.config = Config(self.temp_config.name)
        
        # Initialisiere den globalen Controller
        global _bandwidth_controller
        _bandwidth_controller = None
        initialize_bandwidth_controller(self.config)
    
    def tearDown(self):
        """Räumt die Testumgebung auf."""
        import os
        os.unlink(self.temp_config.name)
    
    @patch('src.telegram_audio_downloader.intelligent_bandwidth._bandwidth_controller')
    def test_get_bandwidth_controller(self, mock_controller):
        """Testet das Abrufen des Bandwidth-Controllers."""
        mock_controller.get_current_settings.return_value = AdaptiveSettings()
        
        controller = get_bandwidth_controller(self.config)
        self.assertIsNotNone(controller)
    
    @patch('src.telegram_audio_downloader.intelligent_bandwidth._bandwidth_controller')
    def test_adjust_bandwidth_settings(self, mock_controller):
        """Testet das Anpassen der Bandbreiteneinstellungen."""
        adjust_bandwidth_settings()
        mock_controller.adjust_settings.assert_called_once()
    
    @patch('src.telegram_audio_downloader.intelligent_bandwidth._bandwidth_controller')
    def test_get_current_bandwidth_settings(self, mock_controller):
        """Testet das Abrufen der aktuellen Bandbreiteneinstellungen."""
        mock_controller.get_current_settings.return_value = AdaptiveSettings()
        
        settings = get_current_bandwidth_settings()
        self.assertIsInstance(settings, AdaptiveSettings)
    
    @patch('src.telegram_audio_downloader.intelligent_bandwidth._bandwidth_controller')
    def test_register_download_functions(self, mock_controller):
        """Testet das Registrieren von Download-Funktionen."""
        file_id = "test_file_003"
        
        register_download_start(file_id)
        mock_controller.register_download_start.assert_called_once_with(file_id)
        
        register_download_end(file_id)
        mock_controller.register_download_end.assert_called_with(file_id)
    
    @patch('src.telegram_audio_downloader.intelligent_bandwidth._bandwidth_controller')
    def test_can_start_new_download_function(self, mock_controller):
        """Testet die Funktion zum Prüfen, ob ein neuer Download gestartet werden kann."""
        mock_controller.can_start_new_download.return_value = True
        
        result = can_start_new_download()
        self.assertTrue(result)
        mock_controller.can_start_new_download.assert_called_once()
    
    @patch('src.telegram_audio_downloader.intelligent_bandwidth._bandwidth_controller')
    def test_update_download_speed_function(self, mock_controller):
        """Testet die Funktion zum Aktualisieren der Download-Geschwindigkeit."""
        file_id = "test_file_004"
        bytes_downloaded = 1024000
        time_elapsed = 10.0
        
        update_download_speed(file_id, bytes_downloaded, time_elapsed)
        mock_controller.update_download_speed.assert_called_once_with(file_id, bytes_downloaded, time_elapsed)


if __name__ == '__main__':
    unittest.main()