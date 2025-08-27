"""
Metriken-Export für den Telegram Audio Downloader.
"""

import json
import time
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from pathlib import Path
import threading


class MetricsCollector:
    """Sammelt und exportiert Metriken für das Monitoring."""

    def __init__(self):
        self.metrics: Dict[str, Any] = {}
        self.counters: Dict[str, int] = {}
        self.gauges: Dict[str, float] = {}
        self.timers: Dict[str, float] = {}
        self.histograms: Dict[str, list] = {}
        self.lock = threading.Lock()

    def increment_counter(self, name: str, value: int = 1) -> None:
        """
        Erhöht einen Zähler.

        Args:
            name: Name des Zählers
            value: Wert, um den der Zähler erhöht werden soll
        """
        with self.lock:
            self.counters[name] = self.counters.get(name, 0) + value

    def set_gauge(self, name: str, value: float) -> None:
        """
        Setzt einen Gauge-Wert.

        Args:
            name: Name des Gauges
            value: Wert des Gauges
        """
        with self.lock:
            self.gauges[name] = value

    def start_timer(self, name: str) -> Callable[[], float]:
        """
        Startet einen Timer.

        Args:
            name: Name des Timers

        Returns:
            Funktion zum Stoppen des Timers und Zurückgeben der Dauer
        """
        start_time = time.time()

        def stop_timer() -> float:
            duration = time.time() - start_time
            with self.lock:
                self.timers[name] = duration
                if name not in self.histograms:
                    self.histograms[name] = []
                self.histograms[name].append(duration)
            return duration

        return stop_timer

    def record_histogram(self, name: str, value: float) -> None:
        """
        Zeichnet einen Wert in einem Histogramm auf.

        Args:
            name: Name des Histogramms
            value: Wert zum Aufzeichnen
        """
        with self.lock:
            if name not in self.histograms:
                self.histograms[name] = []
            self.histograms[name].append(value)

    def get_metrics(self) -> Dict[str, Any]:
        """
        Gibt alle gesammelten Metriken zurück.

        Returns:
            Dictionary mit allen Metriken
        """
        with self.lock:
            return {
                "counters": self.counters.copy(),
                "gauges": self.gauges.copy(),
                "timers": self.timers.copy(),
                "histograms": {k: v.copy() for k, v in self.histograms.items()},
                "timestamp": datetime.now().isoformat()
            }

    def reset_metrics(self) -> None:
        """Setzt alle Metriken zurück."""
        with self.lock:
            self.counters.clear()
            self.gauges.clear()
            self.timers.clear()
            self.histograms.clear()

    def export_to_prometheus(self) -> str:
        """
        Exportiert Metriken im Prometheus-Format.

        Returns:
            Metriken als Prometheus-formatierten String
        """
        metrics = self.get_metrics()
        lines = []

        # Zähler exportieren
        for name, value in metrics["counters"].items():
            lines.append(f"# TYPE {name} counter")
            lines.append(f"{name} {value}")

        # Gauges exportieren
        for name, value in metrics["gauges"].items():
            lines.append(f"# TYPE {name} gauge")
            lines.append(f"{name} {value}")

        # Timer exportieren
        for name, value in metrics["timers"].items():
            lines.append(f"# TYPE {name}_duration_seconds gauge")
            lines.append(f"{name}_duration_seconds {value}")

        # Histogramm-Statistiken exportieren
        for name, values in metrics["histograms"].items():
            if values:
                lines.append(f"# TYPE {name}_histogram histogram")
                lines.append(f"{name}_histogram_count {len(values)}")
                lines.append(f"{name}_histogram_sum {sum(values)}")
                lines.append(f"{name}_histogram_avg {sum(values) / len(values)}")

        return "\n".join(lines)

    def export_to_json(self, file_path: Optional[str] = None) -> str:
        """
        Exportiert Metriken im JSON-Format.

        Args:
            file_path: Optionaler Pfad zur Datei, in die exportiert werden soll

        Returns:
            Metriken als JSON-formatierten String
        """
        metrics = self.get_metrics()
        json_str = json.dumps(metrics, indent=2, ensure_ascii=False)

        if file_path:
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(json_str)

        return json_str

    def export_to_statsd(self, host: str = "localhost", port: int = 8125) -> None:
        """
        Exportiert Metriken im StatsD-Protokoll.

        Args:
            host: StatsD-Host
            port: StatsD-Port
        """
        try:
            import socket
            metrics = self.get_metrics()
            lines = []

            # Zähler exportieren
            for name, value in metrics["counters"].items():
                lines.append(f"{name}:{value}|c")

            # Gauges exportieren
            for name, value in metrics["gauges"].items():
                lines.append(f"{name}:{value}|g")

            # Timer exportieren
            for name, value in metrics["timers"].items():
                lines.append(f"{name}:{value * 1000}|ms")  # Konvertiere zu Millisekunden

            # Senden über UDP
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                message = "\n".join(lines).encode('utf-8')
                sock.sendto(message, (host, port))
        except Exception as e:
            # Im Fehlerfall stillschweigend fehlschlagen
            logger.debug(f"StatsD-Export fehlgeschlagen (nicht kritisch): {e}")


class MetricsMiddleware:
    """Middleware für die Integration von Metriken in Anwendungen."""

    def __init__(self, collector: MetricsCollector):
        self.collector = collector

    def track_request(self, func_name: str):
        """
        Dekorator zum Tracken von Funktionsaufrufen.

        Args:
            func_name: Name der Funktion

        Returns:
            Dekorator-Funktion
        """
        def decorator(func):
            def wrapper(*args, **kwargs):
                # Zähler erhöhen
                self.collector.increment_counter(f"{func_name}_requests_total")

                # Timer starten
                stop_timer = self.collector.start_timer(f"{func_name}_duration_seconds")

                try:
                    result = func(*args, **kwargs)
                    # Erfolgszähler erhöhen
                    self.collector.increment_counter(f"{func_name}_success_total")
                    return result
                except Exception as e:
                    # Fehlerzähler erhöhen
                    self.collector.increment_counter(f"{func_name}_errors_total")
                    raise
                finally:
                    # Timer stoppen
                    stop_timer()
            return wrapper
        return decorator


def export_download_metric(status: str, file_size: int) -> None:
    """
    Exportiert eine Download-Metrik.
    
    Args:
        status: Status des Downloads (success, failure, exception)
        file_size: Größe der Datei in Bytes
    """
    collector = get_metrics_collector()
    collector.increment_counter(f"download_{status}_total")
    if file_size > 0:
        collector.increment_counter("downloaded_bytes_total", file_size)
        collector.record_histogram("download_size_bytes", file_size)

    def track_download(self, file_size: int):
        """
        Trackt einen Download.

        Args:
            file_size: Größe der heruntergeladenen Datei in Bytes
        """
        self.collector.increment_counter("downloads_total")
        self.collector.increment_counter("downloaded_bytes_total", file_size)
        self.collector.record_histogram("download_size_bytes", file_size)


# Globale Instanz des MetricsCollectors
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """
    Gibt die globale Instanz des MetricsCollectors zurück.

    Returns:
        Die MetricsCollector-Instanz
    """
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


def track_performance(operation: str):
    """
    Dekorator zum Tracken der Performance einer Funktion.

    Args:
        operation: Name der Operation

    Returns:
        Dekorator-Funktion
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            collector = get_metrics_collector()
            stop_timer = collector.start_timer(f"{operation}_duration_seconds")
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                stop_timer()
        return wrapper
    return decorator