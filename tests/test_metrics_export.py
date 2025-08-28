#!/usr/bin/env python3
"""
Metriken-Export Tests - Telegram Audio Downloader
==============================================

Tests für das Metriken-Export-System.
"""

import os
import sys
import json
import socket
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from telegram_audio_downloader.metrics_export import (
    get_metrics_collector,
    MetricsCollector,
    MetricsMiddleware,
    track_performance
)


class TestMetricsCollector:
    """Tests für den MetricsCollector."""
    
    def test_metrics_collector_creation(self):
        """Test Erstellung des MetricsCollectors."""
        collector = MetricsCollector()
        assert collector is not None
        assert collector.counters == {}
        assert collector.gauges == {}
        assert collector.timers == {}
        assert collector.histograms == {}
    
    def test_increment_counter(self):
        """Test Inkrementieren von Zählern."""
        collector = MetricsCollector()
        
        # Inkrementiere einen Zähler
        collector.increment_counter("test_counter")
        assert collector.counters["test_counter"] == 1
        
        # Inkrementiere mit benutzerdefiniertem Wert
        collector.increment_counter("test_counter", 5)
        assert collector.counters["test_counter"] == 6
        
        # Inkrementiere einen neuen Zähler
        collector.increment_counter("new_counter", 3)
        assert collector.counters["new_counter"] == 3
    
    def test_set_gauge(self):
        """Test Setzen von Gauge-Werten."""
        collector = MetricsCollector()
        
        # Setze einen Gauge-Wert
        collector.set_gauge("test_gauge", 42.5)
        assert collector.gauges["test_gauge"] == 42.5
        
        # Aktualisiere den Gauge-Wert
        collector.set_gauge("test_gauge", 100.0)
        assert collector.gauges["test_gauge"] == 100.0
    
    def test_start_timer(self):
        """Test Starten von Timern."""
        collector = MetricsCollector()
        
        # Starte einen Timer
        stop_timer = collector.start_timer("test_timer")
        assert callable(stop_timer)
        
        # Stoppe den Timer
        duration = stop_timer()
        assert duration >= 0
        assert "test_timer" in collector.timers
        assert collector.timers["test_timer"] >= 0
        assert "test_timer" in collector.histograms
        assert len(collector.histograms["test_timer"]) == 1
    
    def test_record_histogram(self):
        """Test Aufzeichnen von Histogrammwerten."""
        collector = MetricsCollector()
        
        # Zeichne Werte auf
        collector.record_histogram("test_histogram", 1.0)
        collector.record_histogram("test_histogram", 2.0)
        collector.record_histogram("test_histogram", 3.0)
        
        # Prüfe die aufgezeichneten Werte
        assert "test_histogram" in collector.histograms
        assert collector.histograms["test_histogram"] == [1.0, 2.0, 3.0]
    
    def test_get_metrics(self):
        """Test Abrufen von Metriken."""
        collector = MetricsCollector()
        
        # Füge einige Metriken hinzu
        collector.increment_counter("test_counter", 5)
        collector.set_gauge("test_gauge", 42.0)
        collector.record_histogram("test_histogram", 1.0)
        collector.record_histogram("test_histogram", 2.0)
        
        # Hole die Metriken
        metrics = collector.get_metrics()
        
        # Prüfe die Struktur
        assert "counters" in metrics
        assert "gauges" in metrics
        assert "timers" in metrics
        assert "histograms" in metrics
        assert "timestamp" in metrics
        
        # Prüfe die Werte
        assert metrics["counters"]["test_counter"] == 5
        assert metrics["gauges"]["test_gauge"] == 42.0
        assert metrics["histograms"]["test_histogram"] == [1.0, 2.0]
        assert isinstance(metrics["timestamp"], str)
    
    def test_reset_metrics(self):
        """Test Zurücksetzen von Metriken."""
        collector = MetricsCollector()
        
        # Füge einige Metriken hinzu
        collector.increment_counter("test_counter")
        collector.set_gauge("test_gauge", 42.0)
        collector.record_histogram("test_histogram", 1.0)
        
        # Prüfe, dass Metriken vorhanden sind
        assert len(collector.counters) > 0
        assert len(collector.gauges) > 0
        assert len(collector.histograms) > 0
        
        # Setze Metriken zurück
        collector.reset_metrics()
        
        # Prüfe, dass Metriken zurückgesetzt wurden
        assert collector.counters == {}
        assert collector.gauges == {}
        assert collector.timers == {}
        assert collector.histograms == {}
    
    def test_export_to_prometheus(self):
        """Test Exportieren zu Prometheus."""
        collector = MetricsCollector()
        
        # Füge einige Metriken hinzu
        collector.increment_counter("test_requests_total", 10)
        collector.set_gauge("test_memory_usage_bytes", 1024.0)
        collector.record_histogram("test_response_time_seconds", 0.1)
        collector.record_histogram("test_response_time_seconds", 0.2)
        
        # Exportiere zu Prometheus
        prometheus_output = collector.export_to_prometheus()
        
        # Prüfe, ob die Ausgabe die erwarteten Metriken enthält
        assert "test_requests_total" in prometheus_output
        assert "test_memory_usage_bytes" in prometheus_output
        assert "test_response_time_seconds" in prometheus_output
        assert "# TYPE" in prometheus_output  # Prometheus-Typ-Deklarationen
        assert "10" in prometheus_output  # Zählerwert
        assert "1024.0" in prometheus_output  # Gauge-Wert
    
    def test_export_to_json(self):
        """Test Exportieren zu JSON."""
        collector = MetricsCollector()
        
        # Füge einige Metriken hinzu
        collector.increment_counter("test_counter", 5)
        collector.set_gauge("test_gauge", 42.0)
        
        # Exportiere zu JSON
        json_output = collector.export_to_json()
        
        # Prüfe, ob die Ausgabe gültiges JSON ist
        parsed = json.loads(json_output)
        assert "counters" in parsed
        assert "gauges" in parsed
        assert parsed["counters"]["test_counter"] == 5
        assert parsed["gauges"]["test_gauge"] == 42.0
    
    def test_export_to_json_with_file(self):
        """Test Exportieren zu JSON mit Dateiausgabe."""
        collector = MetricsCollector()
        
        # Erstelle ein temporäres Verzeichnis
        temp_dir = tempfile.mkdtemp(prefix="metrics_test_")
        json_file = Path(temp_dir) / "metrics.json"
        
        try:
            # Füge einige Metriken hinzu
            collector.increment_counter("test_counter", 5)
            
            # Exportiere zu JSON-Datei
            collector.export_to_json(str(json_file))
            
            # Prüfe, ob die Datei erstellt wurde
            assert json_file.exists()
            
            # Prüfe den Inhalt der Datei
            with open(json_file, 'r', encoding='utf-8') as f:
                parsed = json.load(f)
                assert parsed["counters"]["test_counter"] == 5
        finally:
            # Cleanup
            import shutil
            if Path(temp_dir).exists():
                shutil.rmtree(temp_dir)
    
    @patch("socket.socket")
    def test_export_to_statsd(self, mock_socket):
        """Test Exportieren zu StatsD."""
        collector = MetricsCollector()
        
        # Füge einige Metriken hinzu
        collector.increment_counter("test_counter", 5)
        collector.set_gauge("test_gauge", 42.0)
        collector.record_histogram("test_timer", 0.1)
        
        # Exportiere zu StatsD
        collector.export_to_statsd("localhost", 8125)
        
        # Prüfe, ob der Socket verwendet wurde
        mock_socket.assert_called_once_with(socket.AF_INET, socket.SOCK_DGRAM)
        
        # Prüfe, ob sendto aufgerufen wurde
        mock_socket.return_value.__enter__.return_value.sendto.assert_called()


class TestMetricsMiddleware:
    """Tests für die MetricsMiddleware."""
    
    def test_metrics_middleware_creation(self):
        """Test Erstellung der MetricsMiddleware."""
        collector = MetricsCollector()
        middleware = MetricsMiddleware(collector)
        assert middleware is not None
        assert middleware.collector == collector
    
    def test_track_request_decorator(self):
        """Test track_request Dekorator."""
        collector = MetricsCollector()
        middleware = MetricsMiddleware(collector)
        
        # Erstelle eine dekorierte Funktion
        @middleware.track_request("test_function")
        def test_function():
            return "test_result"
        
        # Rufe die Funktion auf
        result = test_function()
        
        # Prüfe das Ergebnis
        assert result == "test_result"
        
        # Prüfe, ob die Metriken aktualisiert wurden
        metrics = collector.get_metrics()
        assert "test_function_requests_total" in metrics["counters"]
        assert metrics["counters"]["test_function_requests_total"] == 1
        assert "test_function_success_total" in metrics["counters"]
        assert metrics["counters"]["test_function_success_total"] == 1
    
    def test_track_request_decorator_with_exception(self):
        """Test track_request Dekorator mit Ausnahme."""
        collector = MetricsCollector()
        middleware = MetricsMiddleware(collector)
        
        # Erstelle eine dekorierte Funktion, die eine Ausnahme wirft
        @middleware.track_request("test_function_with_error")
        def test_function_with_error():
            raise ValueError("Test error")
        
        # Rufe die Funktion auf und fange die Ausnahme
        with pytest.raises(ValueError):
            test_function_with_error()
        
        # Prüfe, ob die Metriken aktualisiert wurden
        metrics = collector.get_metrics()
        assert "test_function_with_error_requests_total" in metrics["counters"]
        assert metrics["counters"]["test_function_with_error_requests_total"] == 1
        assert "test_function_with_error_errors_total" in metrics["counters"]
        assert metrics["counters"]["test_function_with_error_errors_total"] == 1
    
    def test_track_download(self):
        """Test track_download Methode."""
        collector = MetricsCollector()
        middleware = MetricsMiddleware(collector)
        
        # Tracke einen Download
        middleware.track_download(1024 * 1024)  # 1MB
        
        # Prüfe, ob die Metriken aktualisiert wurden
        metrics = collector.get_metrics()
        assert "downloads_total" in metrics["counters"]
        assert metrics["counters"]["downloads_total"] == 1
        assert "downloaded_bytes_total" in metrics["counters"]
        assert metrics["counters"]["downloaded_bytes_total"] == 1024 * 1024
        assert "download_size_bytes" in metrics["histograms"]
        assert metrics["histograms"]["download_size_bytes"] == [1024 * 1024]


class TestTrackPerformanceDecorator:
    """Tests für den track_performance Dekorator."""
    
    def test_track_performance_decorator(self):
        """Test track_performance Dekorator."""
        collector = get_metrics_collector()
        
        # Setze Metriken zurück
        collector.reset_metrics()
        
        # Erstelle eine dekorierte Funktion
        @track_performance("test_operation")
        def test_operation():
            # Simuliere etwas Arbeit
            import time
            time.sleep(0.01)  # 10ms
            return "operation_result"
        
        # Rufe die Funktion auf
        result = test_operation()
        
        # Prüfe das Ergebnis
        assert result == "operation_result"
        
        # Prüfe, ob die Metriken aktualisiert wurden
        metrics = collector.get_metrics()
        assert "test_operation_duration_seconds" in metrics["timers"]
        assert metrics["test_operation_duration_seconds"] >= 0.01


if __name__ == "__main__":
    pytest.main([__file__, "-v"])