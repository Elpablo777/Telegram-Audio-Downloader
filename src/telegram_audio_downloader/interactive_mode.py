"""
Interaktiver Modus für den Telegram Audio Downloader.
"""

import sys
import asyncio
from typing import Optional, List
from pathlib import Path

from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.panel import Panel

from .downloader import AudioDownloader
from .config import Config
from .models import AudioFile, TelegramGroup
from .search import search_audio_files, search_downloaded_files, search_groups
from .logging_config import get_logger
from .auto_categorization import get_auto_categorizer

logger = get_logger(__name__)
console = Console()


class InteractiveMode:
    """Klasse für den interaktiven Modus des Telegram Audio Downloaders."""
    
    def __init__(self, downloader: AudioDownloader):
        """
        Initialisiert den interaktiven Modus.
        
        Args:
            downloader: AudioDownloader-Instanz
        """
        self.downloader = downloader
        self.console = console
        self.categorizer = get_auto_categorizer()
    
    async def run(self):
        """Startet den interaktiven Modus."""
        self.console.print(Panel("[bold blue]Telegram Audio Downloader - Interaktiver Modus[/bold blue]"))
        
        while True:
            try:
                self._show_main_menu()
                choice = Prompt.ask("Wähle eine Option", choices=["1", "2", "3", "4", "5", "6", "7", "q"])
                
                if choice == "1":
                    await self._search_and_download()
                elif choice == "2":
                    await self._manage_downloads()
                elif choice == "3":
                    await self._view_downloaded_files()
                elif choice == "4":
                    await self._search_downloaded_files()
                elif choice == "5":
                    await self._manage_groups()
                elif choice == "6":
                    await self._view_settings()
                elif choice == "7":
                    await self._advanced_options()
                elif choice.lower() == "q":
                    if Confirm.ask("Möchtest du das Programm wirklich beenden?"):
                        break
                        
            except KeyboardInterrupt:
                if Confirm.ask("\nMöchtest du das Programm beenden?"):
                    break
            except Exception as e:
                logger.error(f"Fehler im interaktiven Modus: {e}")
                self.console.print(f"[red]Fehler: {e}[/red]")
    
    def _show_main_menu(self):
        """Zeigt das Hauptmenü an."""
        self.console.print("\n[bold]Hauptmenü:[/bold]")
        self.console.print("1. Suchen und Herunterladen")
        self.console.print("2. Downloads verwalten")
        self.console.print("3. Heruntergeladene Dateien anzeigen")
        self.console.print("4. In heruntergeladenen Dateien suchen")
        self.console.print("5. Telegram-Gruppen verwalten")
        self.console.print("6. Einstellungen anzeigen")
        self.console.print("7. Erweiterte Optionen")
        self.console.print("q. Beenden")
    
    async def _search_and_download(self):
        """Sucht nach Audiodateien und lädt sie herunter."""
        self.console.print("\n[bold]Suchen und Herunterladen[/bold]")
        
        # Gruppen auswählen
        groups = list(TelegramGroup.select())
        if not groups:
            self.console.print("[yellow]Keine Telegram-Gruppen gefunden. Bitte füge zuerst Gruppen hinzu.[/yellow]")
            return
        
        self.console.print("\nVerfügbare Gruppen:")
        for i, group in enumerate(groups, 1):
            self.console.print(f"{i}. {group.title}")
        
        try:
            group_choice = int(Prompt.ask("Wähle eine Gruppe", choices=[str(i) for i in range(1, len(groups) + 1)])) - 1
            selected_group = groups[group_choice]
        except (ValueError, IndexError):
            self.console.print("[red]Ungültige Auswahl.[/red]")
            return
        
        # Suchanfrage
        query = Prompt.ask("Suchbegriff (leer für alle Dateien)")
        limit = Prompt.ask("Maximale Anzahl Ergebnisse (leer für alle)", default="50")
        
        try:
            limit = int(limit) if limit else None
        except ValueError:
            limit = 50
        
        # Suche nach Audiodateien
        self.console.print("[blue]Suche nach Audiodateien...[/blue]")
        try:
            # Hole die Gruppen-Entity
            group_entity = await self.downloader.client.get_entity(selected_group.group_id)
            
            # Suche nach Audiodateien
            audio_files = await search_audio_files(
                self.downloader.client, 
                group_entity, 
                query if query else None,
                limit
            )
            
            if not audio_files:
                self.console.print("[yellow]Keine Audiodateien gefunden.[/yellow]")
                return
            
            # Zeige Ergebnisse an
            self.console.print(f"\n[yellow]{len(audio_files)} Audiodateien gefunden:[/yellow]")
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Nr.", style="dim", width=4)
            table.add_column("Titel")
            table.add_column("Künstler")
            table.add_column("Dateiname")
            table.add_column("Größe", justify="right")
            
            for i, file_info in enumerate(audio_files, 1):
                title = file_info.get("title", "Unbekannt") or "Unbekannt"
                performer = file_info.get("performer", "Unbekannt") or "Unbekannt"
                file_name = file_info.get("file_name", "Unbekannt")
                file_size = f"{file_info.get('file_size', 0) / (1024*1024):.2f} MB"
                
                table.add_row(
                    str(i),
                    title[:30],
                    performer[:20],
                    file_name[:30],
                    file_size
                )
            
            self.console.print(table)
            
            # Auswahl für Download
            download_choice = Prompt.ask(
                "Welche Dateien herunterladen? (z.B. '1,2,3' oder '1-5' oder 'all')", 
                default="all"
            )
            
            files_to_download = []
            if download_choice.lower() == "all":
                files_to_download = audio_files
            else:
                # Parse die Auswahl
                try:
                    if "-" in download_choice:
                        # Bereichsauswahl
                        start, end = map(int, download_choice.split("-"))
                        files_to_download = audio_files[start-1:end]
                    else:
                        # Einzelauswahl
                        indices = [int(x.strip()) - 1 for x in download_choice.split(",")]
                        files_to_download = [audio_files[i] for i in indices if 0 <= i < len(audio_files)]
                except (ValueError, IndexError):
                    self.console.print("[red]Ungültige Auswahl.[/red]")
                    return
            
            if not files_to_download:
                self.console.print("[yellow]Keine Dateien zum Herunterladen ausgewählt.[/yellow]")
                return
            
            # Bestätigung
            if not Confirm.ask(f"Möchtest du {len(files_to_download)} Datei(en) herunterladen?"):
                return
            
            # Download der ausgewählten Dateien
            self.console.print("[blue]Starte Download...[/blue]")
            for file_info in files_to_download:
                try:
                    # Erstelle ein AudioFile-Objekt für den Download
                    audio_file = AudioFile(
                        file_id=file_info["file_id"],
                        message_id=file_info["message_id"],
                        file_name=file_info["file_name"],
                        file_size=file_info["file_size"],
                        mime_type=file_info["mime_type"],
                        duration=file_info.get("duration"),
                        title=file_info.get("title"),
                        performer=file_info.get("performer"),
                        date=file_info["date"]
                    )
                    
                    # Führe den Download durch
                    await self.downloader.download_audio_file(audio_file, selected_group)
                    self.console.print(f"[green]✓ {file_info['file_name']} heruntergeladen[/green]")
                    
                except Exception as e:
                    logger.error(f"Fehler beim Herunterladen von {file_info['file_name']}: {e}")
                    self.console.print(f"[red]✗ Fehler beim Herunterladen von {file_info['file_name']}: {e}[/red]")
            
            self.console.print("[green]Download abgeschlossen![/green]")
            
        except Exception as e:
            logger.error(f"Fehler bei der Suche: {e}")
            self.console.print(f"[red]Fehler bei der Suche: {e}[/red]")
    
    async def _manage_downloads(self):
        """Verwaltet aktive Downloads."""
        self.console.print("\n[bold]Downloads verwalten[/bold]")
        self.console.print("[yellow]Diese Funktion ist noch in Entwicklung.[/yellow]")
    
    async def _view_downloaded_files(self):
        """Zeigt heruntergeladene Dateien an."""
        self.console.print("\n[bold]Heruntergeladene Dateien[/bold]")
        
        try:
            # Hole alle heruntergeladenen Dateien
            downloaded_files = list(AudioFile.select().where(AudioFile.status == "completed"))
            
            if not downloaded_files:
                self.console.print("[yellow]Keine heruntergeladenen Dateien gefunden.[/yellow]")
                return
            
            # Zeige Dateien an
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Titel")
            table.add_column("Künstler")
            table.add_column("Dateiname")
            table.add_column("Größe", justify="right")
            table.add_column("Kategorie")
            
            for file in downloaded_files:
                # Kategorisiere die Datei
                category = self.categorizer.categorize_file(file)
                
                title = file.title or "Unbekannt"
                performer = file.performer or "Unbekannt"
                file_name = file.file_name
                file_size = f"{file.file_size / (1024*1024):.2f} MB" if file.file_size else "Unbekannt"
                
                table.add_row(
                    title[:30],
                    performer[:20],
                    file_name[:30],
                    file_size,
                    category
                )
            
            self.console.print(table)
            
        except Exception as e:
            logger.error(f"Fehler beim Anzeigen der heruntergeladenen Dateien: {e}")
            self.console.print(f"[red]Fehler: {e}[/red]")
    
    async def _search_downloaded_files(self):
        """Sucht in heruntergeladenen Dateien."""
        self.console.print("\n[bold]In heruntergeladenen Dateien suchen[/bold]")
        
        query = Prompt.ask("Suchbegriff")
        if not query:
            self.console.print("[yellow]Kein Suchbegriff eingegeben.[/yellow]")
            return
        
        try:
            # Suche in heruntergeladenen Dateien
            results = search_downloaded_files(query)
            
            if not results:
                self.console.print("[yellow]Keine Dateien gefunden.[/yellow]")
                return
            
            # Zeige Ergebnisse an
            self.console.print(f"\n[yellow]{len(results)} Dateien gefunden:[/yellow]")
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Titel")
            table.add_column("Künstler")
            table.add_column("Dateiname")
            table.add_column("Größe", justify="right")
            
            for file in results:
                title = file.title or "Unbekannt"
                performer = file.performer or "Unbekannt"
                file_name = file.file_name
                file_size = f"{file.file_size / (1024*1024):.2f} MB" if file.file_size else "Unbekannt"
                
                table.add_row(
                    title[:30],
                    performer[:20],
                    file_name[:30],
                    file_size
                )
            
            self.console.print(table)
            
        except Exception as e:
            logger.error(f"Fehler bei der Suche: {e}")
            self.console.print(f"[red]Fehler: {e}[/red]")
    
    async def _manage_groups(self):
        """Verwaltet Telegram-Gruppen."""
        self.console.print("\n[bold]Telegram-Gruppen verwalten[/bold]")
        self.console.print("[yellow]Diese Funktion ist noch in Entwicklung.[/yellow]")
    
    async def _view_settings(self):
        """Zeigt die Einstellungen an."""
        self.console.print("\n[bold]Einstellungen[/bold]")
        
        try:
            config = Config()
            
            table = Table(show_header=False)
            table.add_column("Einstellung", style="cyan")
            table.add_column("Wert")
            
            table.add_row("Download-Verzeichnis", config.DOWNLOAD_PATH)
            table.add_row("Max. parallele Downloads", str(config.MAX_CONCURRENT_DOWNLOADS))
            table.add_row("Download-Wiederholungen", str(config.DOWNLOAD_RETRIES))
            table.add_row("Timeout (Sekunden)", str(config.TIMEOUT))
            table.add_row("Qualität", config.QUALITY)
            table.add_row("Datenbank-Pfad", config.DATABASE_PATH)
            
            self.console.print(table)
            
        except Exception as e:
            logger.error(f"Fehler beim Anzeigen der Einstellungen: {e}")
            self.console.print(f"[red]Fehler: {e}[/red]")
    
    async def _advanced_options(self):
        """Zeigt erweiterte Optionen an."""
        self.console.print("\n[bold]Erweiterte Optionen[/bold]")
        self.console.print("[yellow]Diese Funktion ist noch in Entwicklung.[/yellow]")


# Hilfsfunktionen
async def start_interactive_mode(downloader: AudioDownloader):
    """
    Startet den interaktiven Modus.
    
    Args:
        downloader: AudioDownloader-Instanz
    """
    interactive_mode = InteractiveMode(downloader)
    await interactive_mode.run()