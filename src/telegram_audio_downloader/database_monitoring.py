"""
Datenbank-Performance-Monitoring für den Telegram Audio Downloader.

Metriken:
- Abfrageleistung
- Verbindungsstatistiken
- Indizeffizienz
- Locks und Deadlocks
"""

import time
import threading
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Callable
from collections import defaultdict, deque
from dataclasses import dataclass, field
import sqlite3

from .models import db
from .logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class QueryMetrics:
    """Metriken für eine einzelne Abfrage."""
    query: str
    execution_time_ms: float
    timestamp: datetime = field(default_factory=datetime.now)
    rows_returned: int = 0
    error: Optional[str] = None


@dataclass
class ConnectionMetrics:
    """Metriken für Datenbankverbindungen."""
    connection_id: int
    connected_at: datetime
    last_query_at: Optional[datetime] = None
    query_count: int = 0
    total_query_time_ms: float = 0.0
    is_active: bool = True


class DatabasePerformanceMonitor:
    """Überwacht die Datenbankperformance in Echtzeit."""
    
    def __init__(self, history_size: int = 1000):
        """
        Initialisiert den DatabasePerformanceMonitor.
        
        Args:
            history_size: Maximale Größe der Metrik-Historie
        """
        self.history_size = history_size
        self.query_history = deque(maxlen=history_size)
        self.connection_metrics: Dict[int, ConnectionMetrics] = {}
        self.index_usage_stats = defaultdict(int)  # index_name -> usage_count
        self.lock_stats = {
            "acquired_locks": 0,
            "released_locks": 0,
            "deadlocks": 0,
            "lock_waits": 0
        }
        
        # Statistiken
        self.total_queries = 0
        self.total_query_time_ms = 0.0
        self.slow_query_threshold_ms = 100.0  # Schwellenwert für langsame Abfragen
        self.slow_queries = deque(maxlen=100)
        
        # Monitoring-Status
        self.is_monitoring = False
        self.monitoring_thread = None
        
        logger.info("DatabasePerformanceMonitor initialisiert")
    
    def start_monitoring(self) -> None:
        """Startet das Echtzeit-Monitoring."""
        if self.is_monitoring:
            return
            
        self.is_monitoring = True
        self.monitoring_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitoring_thread.start()
        logger.info("Datenbank-Performance-Monitoring gestartet")
    
    def stop_monitoring(self) -> None:
        """Stoppt das Echtzeit-Monitoring."""
        self.is_monitoring = False
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=5)
        logger.info("Datenbank-Performance-Monitoring gestoppt")
    
    def _monitor_loop(self) -> None:
        """Hauptschleife für das Monitoring."""
        while self.is_monitoring:
            try:
                # Aktualisiere Statistiken
                self._update_statistics()
                
                # Prüfe auf Probleme
                self._check_for_issues()
                
                # Warte bis zur nächsten Aktualisierung
                time.sleep(10)  # Alle 10 Sekunden aktualisieren
            except Exception as e:
                logger.error(f"Fehler im Monitoring-Loop: {e}")
                time.sleep(10)
    
    def _update_statistics(self) -> None:
        """Aktualisiert die Datenbankstatistiken."""
        try:
            # Hole SQLite-Statistiken
            cursor = db.execute_sql("PRAGMA pragma_stats;")
            stats = cursor.fetchall()
            
            # Verarbeite die Statistiken
            for row in stats:
                # In einer echten Implementierung würden wir hier die Statistiken analysieren
                pass
                
        except Exception as e:
            logger.debug(f"Fehler beim Aktualisieren der Datenbankstatistiken: {e}")
    
    def _check_for_issues(self) -> None:
        """Prüft auf Performance-Probleme."""
        try:
            # Prüfe auf langsame Abfragen
            recent_slow_queries = [
                q for q in self.query_history 
                if q.execution_time_ms > self.slow_query_threshold_ms
            ]
            
            if len(recent_slow_queries) > 10:  # Mehr als 10 langsame Abfragen
                logger.warning(
                    f"Performance-Problem erkannt: {len(recent_slow_queries)} "
                    f"langsame Abfragen in den letzten {self.history_size} Abfragen"
                )
            
            # Prüfe auf Lock-Probleme
            if self.lock_stats["deadlocks"] > 0:
                logger.warning(f"Deadlock erkannt: {self.lock_stats['deadlocks']} Deadlocks")
                
        except Exception as e:
            logger.error(f"Fehler bei der Problemerkennung: {e}")
    
    def record_query(self, query: str, execution_time_ms: float, 
                    rows_returned: int = 0, error: Optional[str] = None) -> None:
        """
        Zeichnet eine Abfrage auf.
        
        Args:
            query: SQL-Abfrage
            execution_time_ms: Ausführungszeit in Millisekunden
            rows_returned: Anzahl zurückgegebener Zeilen
            error: Fehlermeldung (falls aufgetreten)
        """
        try:
            metric = QueryMetrics(
                query=query[:200],  # Kürze lange Abfragen
                execution_time_ms=execution_time_ms,
                rows_returned=rows_returned,
                error=error
            )
            
            self.query_history.append(metric)
            self.total_queries += 1
            self.total_query_time_ms += execution_time_ms
            
            # Zeichne langsame Abfragen separat auf
            if execution_time_ms > self.slow_query_threshold_ms:
                self.slow_queries.append(metric)
                logger.debug(f"Langsame Abfrage erkannt: {execution_time_ms:.2f}ms - {query[:100]}...")
            
            # Aktualisiere Index-Nutzungsstatistiken
            self._update_index_usage(query)
            
        except Exception as e:
            logger.error(f"Fehler beim Aufzeichnen der Abfrage: {e}")
    
    def _update_index_usage(self, query: str) -> None:
        """
        Aktualisiert die Index-Nutzungsstatistiken.
        
        Args:
            query: SQL-Abfrage
        """
        # In einer echten Implementierung würden wir hier die tatsächlich
        # verwendeten Indizes aus dem Query Plan extrahieren
        # Für dieses Beispiel simulieren wir die Aktualisierung
        pass
    
    def record_connection(self, connection_id: int) -> None:
        """
        Zeichnet eine neue Verbindung auf.
        
        Args:
            connection_id: ID der Verbindung
        """
        try:
            self.connection_metrics[connection_id] = ConnectionMetrics(
                connection_id=connection_id,
                connected_at=datetime.now()
            )
        except Exception as e:
            logger.error(f"Fehler beim Aufzeichnen der Verbindung: {e}")
    
    def update_connection_metrics(self, connection_id: int, query_time_ms: float,
                                rows_returned: int = 0) -> None:
        """
        Aktualisiert die Metriken einer Verbindung.
        
        Args:
            connection_id: ID der Verbindung
            query_time_ms: Ausführungszeit der Abfrage in ms
            rows_returned: Anzahl zurückgegebener Zeilen
        """
        try:
            if connection_id in self.connection_metrics:
                metrics = self.connection_metrics[connection_id]
                metrics.last_query_at = datetime.now()
                metrics.query_count += 1
                metrics.total_query_time_ms += query_time_ms
        except Exception as e:
            logger.error(f"Fehler beim Aktualisieren der Verbindungsmetriken: {e}")
    
    def close_connection(self, connection_id: int) -> None:
        """
        Markiert eine Verbindung als geschlossen.
        
        Args:
            connection_id: ID der Verbindung
        """
        try:
            if connection_id in self.connection_metrics:
                self.connection_metrics[connection_id].is_active = False
        except Exception as e:
            logger.error(f"Fehler beim Schließen der Verbindung: {e}")
    
    def record_lock_event(self, event_type: str) -> None:
        """
        Zeichnet ein Lock-Ereignis auf.
        
        Args:
            event_type: Typ des Lock-Ereignisses
        """
        try:
            if event_type == "acquired":
                self.lock_stats["acquired_locks"] += 1
            elif event_type == "released":
                self.lock_stats["released_locks"] += 1
            elif event_type == "deadlock":
                self.lock_stats["deadlocks"] += 1
            elif event_type == "wait":
                self.lock_stats["lock_waits"] += 1
        except Exception as e:
            logger.error(f"Fehler beim Aufzeichnen des Lock-Ereignisses: {e}")
    
    def get_performance_report(self) -> Dict[str, Any]:
        """
        Erstellt einen Performance-Bericht.
        
        Returns:
            Dictionary mit Performance-Daten
        """
        try:
            # Berechne Durchschnittswerte
            avg_query_time = (
                self.total_query_time_ms / self.total_queries 
                if self.total_queries > 0 else 0.0
            )
            
            # Finde langsame Abfragen
            slow_query_count = len(self.slow_queries)
            
            # Verbindungsstatistiken
            active_connections = sum(1 for m in self.connection_metrics.values() if m.is_active)
            total_connections = len(self.connection_metrics)
            
            return {
                "timestamp": datetime.now().isoformat(),
                "query_statistics": {
                    "total_queries": self.total_queries,
                    "average_query_time_ms": round(avg_query_time, 2),
                    "total_query_time_ms": round(self.total_query_time_ms, 2),
                    "slow_queries": slow_query_count,
                    "slow_query_threshold_ms": self.slow_query_threshold_ms
                },
                "connection_statistics": {
                    "active_connections": active_connections,
                    "total_connections": total_connections,
                    "connection_metrics": [
                        {
                            "connection_id": m.connection_id,
                            "connected_at": m.connected_at.isoformat(),
                            "query_count": m.query_count,
                            "total_query_time_ms": round(m.total_query_time_ms, 2),
                            "is_active": m.is_active
                        }
                        for m in self.connection_metrics.values()
                    ]
                },
                "lock_statistics": self.lock_stats,
                "index_usage": dict(self.index_usage_stats),
                "recent_slow_queries": [
                    {
                        "query": q.query,
                        "execution_time_ms": q.execution_time_ms,
                        "rows_returned": q.rows_returned,
                        "timestamp": q.timestamp.isoformat(),
                        "error": q.error
                    }
                    for q in list(self.slow_queries)[-10:]  # Letzte 10 langsame Abfragen
                ]
            }
            
        except Exception as e:
            logger.error(f"Fehler beim Erstellen des Performance-Berichts: {e}")
            return {}
    
    def get_query_analysis(self, time_window_minutes: int = 60) -> Dict[str, Any]:
        """
        Analysiert Abfragen in einem Zeitfenster.
        
        Args:
            time_window_minutes: Zeitfenster in Minuten
            
        Returns:
            Dictionary mit Abfrage-Analysen
        """
        try:
            cutoff_time = datetime.now() - timedelta(minutes=time_window_minutes)
            
            # Filtere Abfragen im Zeitfenster
            recent_queries = [
                q for q in self.query_history 
                if q.timestamp >= cutoff_time
            ]
            
            if not recent_queries:
                return {"message": "Keine Abfragen im Zeitfenster gefunden"}
            
            # Analysiere die Abfragen
            total_time = sum(q.execution_time_ms for q in recent_queries)
            avg_time = total_time / len(recent_queries)
            
            # Gruppiere nach Abfragetyp
            query_types = defaultdict(list)
            for q in recent_queries:
                # Extrahiere den Abfragetyp (SELECT, INSERT, UPDATE, DELETE)
                query_type = q.query.strip().split()[0].upper() if q.query.strip() else "UNKNOWN"
                query_types[query_type].append(q)
            
            # Berechne Statistiken pro Typ
            type_stats = {}
            for query_type, queries in query_types.items():
                type_total_time = sum(q.execution_time_ms for q in queries)
                type_avg_time = type_total_time / len(queries)
                type_slow_queries = [
                    q for q in queries 
                    if q.execution_time_ms > self.slow_query_threshold_ms
                ]
                
                type_stats[query_type] = {
                    "count": len(queries),
                    "total_time_ms": round(type_total_time, 2),
                    "average_time_ms": round(type_avg_time, 2),
                    "slow_queries": len(type_slow_queries)
                }
            
            return {
                "time_window_minutes": time_window_minutes,
                "total_queries": len(recent_queries),
                "total_time_ms": round(total_time, 2),
                "average_time_ms": round(avg_time, 2),
                "by_type": type_stats,
                "slowest_queries": sorted(
                    recent_queries, 
                    key=lambda q: q.execution_time_ms, 
                    reverse=True
                )[:10]  # Langsamste 10 Abfragen
            }
            
        except Exception as e:
            logger.error(f"Fehler bei der Abfrage-Analyse: {e}")
            return {}
    
    def reset_statistics(self) -> None:
        """Setzt die Statistiken zurück."""
        try:
            self.query_history.clear()
            self.connection_metrics.clear()
            self.index_usage_stats.clear()
            self.lock_stats = {
                "acquired_locks": 0,
                "released_locks": 0,
                "deadlocks": 0,
                "lock_waits": 0
            }
            self.total_queries = 0
            self.total_query_time_ms = 0.0
            self.slow_queries.clear()
            
            logger.info("Datenbank-Performance-Statistiken zurückgesetzt")
        except Exception as e:
            logger.error(f"Fehler beim Zurücksetzen der Statistiken: {e}")


class DatabaseQueryProfiler:
    """Profilierer für Datenbankabfragen."""
    
    def __init__(self, monitor: DatabasePerformanceMonitor):
        """
        Initialisiert den DatabaseQueryProfiler.
        
        Args:
            monitor: DatabasePerformanceMonitor-Instanz
        """
        self.monitor = monitor
        logger.info("DatabaseQueryProfiler initialisiert")
    
    def profile_query(self, query_func: Callable, *args, **kwargs) -> Any:
        """
        Profiliert eine Datenbankabfrage.
        
        Args:
            query_func: Funktion, die die Abfrage ausführt
            *args: Positionelle Argumente für die Abfragefunktion
            **kwargs: Schlüsselwortargumente für die Abfragefunktion
            
        Returns:
            Ergebnis der Abfragefunktion
        """
        start_time = time.time()
        error = None
        rows_returned = 0
        
        try:
            # Führe die Abfrage aus
            result = query_func(*args, **kwargs)
            
            # Zähle die zurückgegebenen Zeilen, falls möglich
            if hasattr(result, '__len__'):
                rows_returned = len(result)
            elif hasattr(result, 'rowcount'):
                rows_returned = getattr(result, 'rowcount', 0)
            
            return result
            
        except Exception as e:
            error = str(e)
            raise
        finally:
            # Berechne die Ausführungszeit
            execution_time_ms = (time.time() - start_time) * 1000
            
            # Extrahiere die SQL-Abfrage aus den Argumenten, falls verfügbar
            query = "UNKNOWN"
            if args and isinstance(args[0], str):
                query = args[0]
            elif 'query' in kwargs:
                query = kwargs['query']
            
            # Zeichne die Abfrage auf
            self.monitor.record_query(
                query=query,
                execution_time_ms=execution_time_ms,
                rows_returned=rows_returned,
                error=error
            )


# Globale Instanzen
_performance_monitor: Optional[DatabasePerformanceMonitor] = None
_query_profiler: Optional[DatabaseQueryProfiler] = None


def get_performance_monitor() -> DatabasePerformanceMonitor:
    """
    Gibt die globale Instanz des DatabasePerformanceMonitor zurück.
    
    Returns:
        DatabasePerformanceMonitor-Instanz
    """
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = DatabasePerformanceMonitor()
    return _performance_monitor


def get_query_profiler() -> DatabaseQueryProfiler:
    """
    Gibt die globale Instanz des DatabaseQueryProfiler zurück.
    
    Returns:
        DatabaseQueryProfiler-Instanz
    """
    global _query_profiler
    if _query_profiler is None:
        monitor = get_performance_monitor()
        _query_profiler = DatabaseQueryProfiler(monitor)
    return _query_profiler


def start_database_monitoring() -> None:
    """Startet das Datenbank-Performance-Monitoring."""
    try:
        monitor = get_performance_monitor()
        monitor.start_monitoring()
    except Exception as e:
        logger.error(f"Fehler beim Starten des Datenbank-Monitoring: {e}")


def stop_database_monitoring() -> None:
    """Stoppt das Datenbank-Performance-Monitoring."""
    try:
        monitor = get_performance_monitor()
        monitor.stop_monitoring()
    except Exception as e:
        logger.error(f"Fehler beim Stoppen des Datenbank-Monitoring: {e}")


def get_database_performance_report() -> Dict[str, Any]:
    """
    Gibt einen Datenbank-Performance-Bericht zurück.
    
    Returns:
        Dictionary mit Performance-Daten
    """
    try:
        monitor = get_performance_monitor()
        return monitor.get_performance_report()
    except Exception as e:
        logger.error(f"Fehler beim Abrufen des Performance-Berichts: {e}")
        return {}


def profile_database_query(query_func: Callable, *args, **kwargs) -> Any:
    """
    Profiliert eine Datenbankabfrage.
    
    Args:
        query_func: Funktion, die die Abfrage ausführt
        *args: Positionelle Argumente für die Abfragefunktion
        **kwargs: Schlüsselwortargumente für die Abfragefunktion
        
    Returns:
        Ergebnis der Abfragefunktion
    """
    try:
        profiler = get_query_profiler()
        return profiler.profile_query(query_func, *args, **kwargs)
    except Exception as e:
        logger.error(f"Fehler beim Profilieren der Datenbankabfrage: {e}")
        raise