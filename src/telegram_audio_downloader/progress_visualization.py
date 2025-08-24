"""
Fortschrittsvisualisierung für den Telegram Audio Downloader.
"""

import time
from typing import Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass, field
from collections import defaultdict

from rich.console import Console
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn, filesize
from rich.table import Table
from rich.panel import Panel
from rich.live import Live

from .logging_config import get_logger

logger = get_logger(__name__)
console = Console()


@dataclass
class DownloadProgress:
    """Datenklasse für Download-Fortschritt."""
    file_id: str
    file_name: str
    total_size: int
    downloaded: int = 0
    start_time: datetime = field(default_factory=datetime.now)
    last_update: datetime = field(default_factory=datetime.now)
    status: str = "pending"  # pending, downloading, completed, failed
    speed: float = 0.0  # Bytes pro Sekunde
    
    def update(self, downloaded_bytes: int):
        """Aktualisiert den Download-Fortschritt."""
        now = datetime.now()
        time_diff = (now - self.last_update).total_seconds()
        
        if time_diff > 0:
            self.speed = (downloaded_bytes - self.downloaded) / time_diff
        
        self.downloaded = downloaded_bytes
        self.last_update = now
        
        # Aktualisiere Status basierend auf Fortschritt
        if self.downloaded >= self.total_size:
            self.status = "completed"
        elif self.downloaded > 0:
            self.status = "downloading"
    
    @property
    def progress_percent(self) -> float:
        """Gibt den Fortschritt in Prozent zurück."""
        if self.total_size == 0:
            return 0.0
        return (self.downloaded / self.total_size) * 100
    
    @property
    def elapsed_time(self) -> float:
        """Gibt die verstrichene Zeit in Sekunden zurück."""
        return (self.last_update - self.start_time).total_seconds()
    
    @property
    def estimated_time_remaining(self) -> float:
        """Gibt die geschätzte verbleibende Zeit in Sekunden zurück."""
        if self.speed <= 0:
            return 0.0
        remaining_bytes = self.total_size - self.downloaded
        return remaining_bytes / self.speed


class ProgressVisualizer:
    """Klasse zur Visualisierung des Download-Fortschritts."""
    
    def __init__(self):
        """Initialisiert den ProgressVisualizer."""
        self.console = console
        self.downloads: Dict[str, DownloadProgress] = {}
        self.progress_bar = None
        self.live_display = None
    
    def add_download(self, file_id: str, file_name: str, total_size: int):
        """
        Fügt einen neuen Download zur Verfolgung hinzu.
        
        Args:
            file_id: Eindeutige ID der Datei
            file_name: Name der Datei
            total_size: Gesamtgröße der Datei in Bytes
        """
        self.downloads[file_id] = DownloadProgress(
            file_id=file_id,
            file_name=file_name,
            total_size=total_size
        )
        logger.debug(f"Download hinzugefügt: {file_name} ({filesize.decimal(total_size)})")
    
    def update_progress(self, file_id: str, downloaded_bytes: int):
        """
        Aktualisiert den Fortschritt eines Downloads.
        
        Args:
            file_id: Eindeutige ID der Datei
            downloaded_bytes: Anzahl der heruntergeladenen Bytes
        """
        if file_id in self.downloads:
            self.downloads[file_id].update(downloaded_bytes)
            logger.debug(f"Fortschritt aktualisiert für {file_id}: {downloaded_bytes} bytes")
    
    def set_status(self, file_id: str, status: str):
        """
        Setzt den Status eines Downloads.
        
        Args:
            file_id: Eindeutige ID der Datei
            status: Status (pending, downloading, completed, failed)
        """
        if file_id in self.downloads:
            self.downloads[file_id].status = status
            logger.debug(f"Status aktualisiert für {file_id}: {status}")
    
    def get_overall_progress(self) -> Dict[str, Any]:
        """
        Gibt den Gesamtfortschritt aller Downloads zurück.
        
        Returns:
            Dictionary mit Gesamtfortschrittsinformationen
        """
        if not self.downloads:
            return {
                "total_files": 0,
                "completed_files": 0,
                "failed_files": 0,
                "total_size": 0,
                "downloaded_size": 0,
                "progress_percent": 0.0,
                "average_speed": 0.0
            }
        
        total_files = len(self.downloads)
        completed_files = sum(1 for d in self.downloads.values() if d.status == "completed")
        failed_files = sum(1 for d in self.downloads.values() if d.status == "failed")
        total_size = sum(d.total_size for d in self.downloads.values())
        downloaded_size = sum(d.downloaded for d in self.downloads.values())
        progress_percent = (downloaded_size / total_size * 100) if total_size > 0 else 0.0
        average_speed = sum(d.speed for d in self.downloads.values()) / len(self.downloads)
        
        return {
            "total_files": total_files,
            "completed_files": completed_files,
            "failed_files": failed_files,
            "total_size": total_size,
            "downloaded_size": downloaded_size,
            "progress_percent": progress_percent,
            "average_speed": average_speed
        }
    
    def show_progress_bar(self):
        """Zeigt eine einfache Fortschrittsanzeige in der Konsole an."""
        if not self.downloads:
            self.console.print("[yellow]Keine aktiven Downloads.[/yellow]")
            return
        
        # Erstelle eine Rich-Progress-Bar
        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("[progress.download]{task.fields[downloaded]} / {task.fields[total]}"),
            TimeRemainingColumn(),
            console=self.console
        ) as progress:
            # Erstelle Tasks für jeden Download
            tasks = {}
            for file_id, download in self.downloads.items():
                task_id = progress.add_task(
                    download.file_name[:30],  # Kürze den Dateinamen
                    total=download.total_size,
                    downloaded=filesize.decimal(download.downloaded),
                    total=filesize.decimal(download.total_size)
                )
                tasks[file_id] = task_id
            
            # Aktualisiere die Fortschrittsanzeige
            while any(d.status not in ["completed", "failed"] for d in self.downloads.values()):
                for file_id, download in self.downloads.items():
                    if download.status not in ["completed", "failed"]:
                        task_id = tasks[file_id]
                        progress.update(
                            task_id,
                            completed=download.downloaded,
                            downloaded=filesize.decimal(download.downloaded),
                            total=filesize.decimal(download.total_size)
                        )
                time.sleep(0.5)  # Aktualisiere alle 0.5 Sekunden
    
    def show_detailed_progress(self):
        """Zeigt eine detaillierte Fortschrittsanzeige an."""
        if not self.downloads:
            self.console.print("[yellow]Keine aktiven Downloads.[/yellow]")
            return
        
        # Erstelle eine Tabelle mit detaillierten Informationen
        table = Table(title="Download-Fortschritt", show_header=True, header_style="bold magenta")
        table.add_column("Datei", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Fortschritt", style="blue")
        table.add_column("Geschwindigkeit", style="yellow")
        table.add_column("Verbleibend", style="red")
        
        for download in self.downloads.values():
            # Status
            status_icon = {
                "pending": "⏸️",
                "downloading": "⬇️",
                "completed": "✅",
                "failed": "❌"
            }.get(download.status, "❓")
            
            # Fortschritt
            progress_str = f"{download.progress_percent:.1f}%"
            
            # Geschwindigkeit
            if download.speed > 0:
                speed_str = filesize.decimal(download.speed) + "/s"
            else:
                speed_str = "—"
            
            # Verbleibende Zeit
            if download.estimated_time_remaining > 0:
                remaining = download.estimated_time_remaining
                if remaining < 60:
                    remaining_str = f"{remaining:.0f}s"
                elif remaining < 3600:
                    remaining_str = f"{remaining/60:.1f}m"
                else:
                    remaining_str = f"{remaining/3600:.1f}h"
            else:
                remaining_str = "—"
            
            table.add_row(
                download.file_name[:30],
                f"{status_icon} {download.status}",
                progress_str,
                speed_str,
                remaining_str
            )
        
        # Zeige die Tabelle an
        self.console.print(table)
        
        # Zeige Gesamtfortschritt an
        overall = self.get_overall_progress()
        if overall["total_files"] > 0:
            panel_content = (
                f"Dateien: {overall['completed_files']}/{overall['total_files']} abgeschlossen\n"
                f"Fortschritt: {overall['progress_percent']:.1f}%\n"
                f"Downloaded: {filesize.decimal(overall['downloaded_size'])} / {filesize.decimal(overall['total_size'])}\n"
                f"Durchschnittliche Geschwindigkeit: {filesize.decimal(overall['average_speed'])}/s"
            )
            self.console.print(Panel(panel_content, title="Gesamtfortschritt"))
    
    def show_live_progress(self):
        """Zeigt eine Live-Fortschrittsanzeige an."""
        if not self.downloads:
            self.console.print("[yellow]Keine aktiven Downloads.[/yellow]")
            return
        
        # Erstelle eine Live-Anzeige
        with Live(console=self.console, refresh_per_second=4) as live:
            while any(d.status not in ["completed", "failed"] for d in self.downloads.values()):
                # Erstelle die Tabelle für die Live-Anzeige
                table = Table(title="Live Download-Fortschritt", show_header=True, header_style="bold magenta")
                table.add_column("Datei", style="cyan")
                table.add_column("Status", style="green")
                table.add_column("Fortschritt", style="blue")
                table.add_column("Geschwindigkeit", style="yellow")
                
                for download in self.downloads.values():
                    # Status
                    status_icon = {
                        "pending": "⏸️",
                        "downloading": "⬇️",
                        "completed": "✅",
                        "failed": "❌"
                    }.get(download.status, "❓")
                    
                    # Fortschritt
                    progress_str = f"{download.progress_percent:.1f}%"
                    
                    # Geschwindigkeit
                    if download.speed > 0:
                        speed_str = filesize.decimal(download.speed) + "/s"
                    else:
                        speed_str = "—"
                    
                    table.add_row(
                        download.file_name[:25],
                        f"{status_icon} {download.status}",
                        progress_str,
                        speed_str
                    )
                
                # Zeige die Tabelle in der Live-Anzeige
                live.update(table)
                time.sleep(0.25)  # Aktualisiere alle 0.25 Sekunden


# Globale Instanz
_progress_visualizer: Optional[ProgressVisualizer] = None

def get_progress_visualizer() -> ProgressVisualizer:
    """
    Gibt die globale Instanz des ProgressVisualizers zurück.
    
    Returns:
        Instanz von ProgressVisualizer
    """
    global _progress_visualizer
    if _progress_visualizer is None:
        _progress_visualizer = ProgressVisualizer()
    return _progress_visualizer

def add_download_progress(file_id: str, file_name: str, total_size: int):
    """
    Fügt einen neuen Download zur Fortschrittsverfolgung hinzu.
    
    Args:
        file_id: Eindeutige ID der Datei
        file_name: Name der Datei
        total_size: Gesamtgröße der Datei in Bytes
    """
    visualizer = get_progress_visualizer()
    visualizer.add_download(file_id, file_name, total_size)

def update_download_progress(file_id: str, downloaded_bytes: int):
    """
    Aktualisiert den Fortschritt eines Downloads.
    
    Args:
        file_id: Eindeutige ID der Datei
        downloaded_bytes: Anzahl der heruntergeladenen Bytes
    """
    visualizer = get_progress_visualizer()
    visualizer.update_progress(file_id, downloaded_bytes)

def set_download_status(file_id: str, status: str):
    """
    Setzt den Status eines Downloads.
    
    Args:
        file_id: Eindeutige ID der Datei
        status: Status (pending, downloading, completed, failed)
    """
    visualizer = get_progress_visualizer()
    visualizer.set_status(file_id, status)

def show_progress():
    """Zeigt den aktuellen Download-Fortschritt an."""
    visualizer = get_progress_visualizer()
    visualizer.show_detailed_progress()