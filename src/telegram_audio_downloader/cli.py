"""
Kommandozeilenschnittstelle für den Telegram Audio Downloader.
"""

import asyncio
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.prompt import Prompt

from .config import Config
from .database import init_db, AudioFile
from .downloader import AudioDownloader
from .error_handling import handle_error, ConfigurationError
from .logger import get_logger, log_function_call
from .performance import PerformanceMonitor
from .search import search_audio_files
from .utils import format_duration, format_file_size, sanitize_filename, is_audio_file
from .batch_processing import BatchItem, BatchProcessor, Priority  # Neue Importe für Batch-Verarbeitung
from .enhanced_user_interaction import (
    get_enhanced_ui, show_notification, NotificationType, 
    show_progress_bar, show_context_menu, show_confirmation_dialog,
    show_download_summary, enable_interactive_mode, disable_interactive_mode
)
from .keyboard_shortcuts import (
    get_keyboard_shortcut_manager, register_shortcut, Shortcut
)

# Füge die benötigten Importe hinzu
from .models import DownloadStatus
from .error_handling import AuthenticationError, TelegramAPIError, NetworkError, DownloadError

# Rich-Konsole
console = Console()


def print_banner():
    """Gibt das Willkommensbanner aus."""
    banner = """
    [bold blue]╔══════════════════════════════════════════════╗
    ║  [white]Telegram Audio Downloader v0.1.0[/white]        ║
    ║  [dim]Ein leistungsstarkes Tool zum Herunterladen[/dim]  ║
    ║  [dim]und Verwalten von Audiodateien[/dim]               ║
    ╚══════════════════════════════════════════════╝[/bold blue]
    """
    console.print(banner, highlight=False)


def load_config(ctx, config_path: Optional[str] = None) -> Config:
    """
    Lädt die Konfiguration mit Priorisierung.
    
    Args:
        ctx: Click-Kontext
        config_path: Optionaler Pfad zur Konfigurationsdatei
        
    Returns:
        Config: Geladene Konfiguration
    """
    try:
        # Lade Konfiguration mit CLI-Argumenten
        cli_args = ctx.params if ctx else {}
        config = Config(config_path=config_path)  # Korrigiert: Verwende den Konstruktor
        
        # Validiere erforderliche Felder
        config.validate_required_fields()
        
        return config
    except ConfigurationError as e:
        handle_error(e, "load_config", exit_on_error=True)  # Korrigiert: Parametername
        # Füge eine Standardkonfiguration zurück, falls der Fehler nicht zum Programmabbruch führt
        return Config()


@click.group()
@click.option("--debug", is_flag=True, help="Aktiviert Debug-Logging")
@click.option("--config", type=click.Path(exists=True), help="Pfad zur Konfigurationsdatei")
@click.option("--interactive", "-i", is_flag=True, help="Aktiviert den interaktiven Modus")
@click.pass_context
@log_function_call
def cli(ctx, debug: bool, config: str, interactive: bool):
    """Telegram Audio Downloader - Ein Tool zum Herunterladen von Audiodateien aus Telegram-Gruppen."""
    # Konfiguration laden
    config_obj = load_config(ctx, config_path=config)  # Korrigiert: Verwende anderen Variablennamen
    
    # Logging-System initialisieren
    logger = get_logger(debug=debug)

    # Banner anzeigen
    print_banner()

    # Datenbank initialisieren
    try:
        init_db()
        logger.info("Datenbank erfolgreich initialisiert")
    except Exception as e:
        error = ConfigurationError(f"Fehler bei Datenbank-Initialisierung: {e}")
        handle_error(error, "cli_init_db", exit_on_error=True)

    # Context-Objekt initialisieren
    ctx.ensure_object(dict)
    ctx.obj["DEBUG"] = debug
    ctx.obj["LOGGER"] = logger
    ctx.obj["CONFIG"] = config_obj  # Korrigiert: Verwende das geladene Config-Objekt
    
    # Erweiterte Benutzerinteraktion initialisieren
    enhanced_ui = get_enhanced_ui()
    if interactive:
        enable_interactive_mode()
        show_notification("Interaktiver Modus aktiviert", NotificationType.SUCCESS)
    else:
        disable_interactive_mode()


@cli.command()
@click.option("--group", "-g", required=True, help="Name der Telegram-Gruppe")
@click.option("--limit", "-l", type=int, help="Maximale Anzahl an Dateien zum Herunterladen")
@click.option("--output", "-o", type=click.Path(), help="Ausgabeverzeichnis")
@click.option("--parallel", "-p", type=int, help="Anzahl paralleler Downloads")
@click.option(
    "--filename-template",
    "-t",
    type=str,
    default=None,
    help="Benutzerdefinierte Vorlage für Dateinamen (z.B. '$artist - $title')",
)
@click.option("--interactive", "-i", is_flag=True, help="Aktiviert den interaktiven Modus für diesen Download")
@click.pass_context
@log_function_call
def download(ctx, group: str, limit: Optional[int], output: Optional[str], parallel: Optional[int], filename_template: Optional[str], interactive: bool):
    """Lädt Audiodateien aus einer Telegram-Gruppe herunter."""
    config = ctx.obj.get("CONFIG")
    
    # Verwende Konfigurationswerte falls nicht über CLI angegeben
    if output is None:
        output = config.download_dir
    if parallel is None:
        parallel = config.max_concurrent_downloads
    
    if not check_env():
        sys.exit(1)
    
    # Validierung der Gruppenparameter
    if not group or not group.strip():
        error = ConfigurationError("Gruppenname darf nicht leer sein")
        handle_error(error, "download_group_validation", exit_on_error=True)
        return
    
    # Validierung des Limit-Parameters
    if limit is not None and limit <= 0:
        error = ConfigurationError("Limit muss eine positive Zahl sein")
        handle_error(error, "download_limit_validation", exit_on_error=True)
        return

    # Ausgabeverzeichnis erstellen
    try:
        output_path = Path(output) if output else Path(config.download_dir)  # Korrigiert: Typsicherheit
        output_path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        error = ConfigurationError(f"Fehler beim Erstellen des Ausgabeverzeichnisses: {e}")
        handle_error(error, "download_output_dir", exit_on_error=True)
        return

    # Downloader initialisieren
    downloader = AudioDownloader(
        download_dir=str(output_path), max_concurrent_downloads=parallel or config.max_concurrent_downloads  # Korrigiert: Typsicherheit
    )
    
    # Wenn eine benutzerdefinierte Vorlage angegeben wurde, füge sie hinzu
    if filename_template:
        try:
            downloader.filename_generator.add_template("custom_cli_template", filename_template)
            downloader.filename_generator.set_template("custom_cli_template")
            console.print(f"[green]Benutzerdefinierte Dateinamen-Vorlage gesetzt:[/green] {filename_template}")
        except Exception as e:
            error = ConfigurationError(f"Fehler beim Setzen der Dateinamen-Vorlage: {e}")
            handle_error(error, "download_filename_template", exit_on_error=True)
            return

    console.print(f"[blue]Parallele Downloads:[/blue] {parallel}")

    try:
        # Herunterladen starten
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            task = progress.add_task("Verbinde mit Telegram...", total=None)

            async def run_download():
                logger = ctx.obj.get("LOGGER", get_logger())
                # Entferne den fehlerhaften Import
                # error_tracker = get_error_tracker()

                try:
                    await downloader.initialize_client()
                    progress.update(
                        task,
                        description=f"Lade Audiodateien aus Gruppe '{group}' herunter...",
                    )

                    start_time = time.time()
                    await downloader.download_audio_files(group, limit=limit)
                    duration = time.time() - start_time

                    progress.update(task, description="[green]Fertig![/green]")
                    logger.info(f"Download abgeschlossen in {duration:.2f}s")

                    # Entferne den fehlerhaften Code
                    # Error-Summary anzeigen
                    # error_summary = error_tracker.get_error_summary()
                    # if error_summary["total"] > 0:
                    #     console.print(
                    #         f"\n[yellow]Warnung: {error_summary['total']} Fehler aufgetreten[/yellow]"
                    #     )
                    #     if ctx.obj.get("DEBUG"):
                    #         console.print("Letzte Fehler:")
                    #         for error in error_summary["recent"]:
                    #             console.print(
                    #                 f"  - {error['type']} in {error['context']} ({error['time']})"
                    #             )

                except Exception as e:
                    # error_tracker.track_error(e, "cli_download", "ERROR")
                    logger.error(
                        f"Download-Fehler: {e}", exc_info=ctx.obj.get("DEBUG", False)
                    )
                    
                    # Spezifische Fehlerbehandlung
                    if "API_ID" in str(e) or "API_HASH" in str(e):
                        error = ConfigurationError("Ungültige oder fehlende API-Zugangsdaten")
                        handle_error(error, "download_auth", exit_on_error=True)
                    elif "FloodWaitError" in str(type(e)):
                        error = TelegramAPIError(f"Telegram API Rate-Limit erreicht: {e}")
                        handle_error(error, "download_flood_wait")
                    elif "ConnectionError" in str(type(e)) or "Timeout" in str(type(e)):
                        error = NetworkError(f"Netzwerkverbindungsfehler: {e}")
                        handle_error(error, "download_network")
                    else:
                        error = DownloadError(f"Download fehlgeschlagen: {e}")
                        handle_error(error, "download_general", exit_on_error=True)

            asyncio.run(run_download())

    except KeyboardInterrupt:
        console.print("\n[red]Vorgang vom Benutzer abgebrochen[/red]")
        sys.exit(1)
    except Exception as e:
        handle_error(e, "download_unexpected", exit_on_error=True)
    finally:
        asyncio.run(downloader.close())


@cli.command()
@click.option("--query", "-q", required=True, help="Suchbegriff")
@click.option("--group", "-g", help="Nach Gruppe filtern")
@click.option("--limit", "-l", type=int, default=20, help="Maximale Anzahl an Ergebnissen")
@click.pass_context
@log_function_call
def search(ctx, query: str, group: Optional[str], limit: int):
    """Durchsucht heruntergeladene Audiodateien."""
    try:
        config = ctx.obj["CONFIG"]
        console_obj = ctx.obj["console"]
        
        # Durchsuche die Datenbank
        # Verwende die richtige Funktion
        from .search import search_downloaded_files
        results = search_downloaded_files(query)
        
        # Begrenze die Ergebnisse, falls ein Limit angegeben ist
        if limit:
            results = results[:limit]
        
        if not results:
            console_obj.print("[yellow]Keine Dateien gefunden.[/yellow]")
            return
        
        # Erstelle eine Tabelle zur Anzeige der Ergebnisse
        table = Table(title="Suchergebnisse")
        table.add_column("Titel", style="cyan", no_wrap=True)
        table.add_column("Künstler", style="green")
        table.add_column("Größe", justify="right")
        table.add_column("Dauer", justify="right")
        table.add_column("Format", justify="center")
        table.add_column("Checksum", style="dim")
        table.add_column("Status", justify="center")
        table.add_column("Gruppe", style="blue")
        table.add_column("Heruntergeladen am", style="dim")
        
        # Importiere DownloadStatus
        from .models import DownloadStatus
        
        for file in results:
            # Dateigröße formatieren
            size_mb = file.file_size / (1024 * 1024)
            size_str = f"{size_mb:.1f} MB"
            
            # Status formatieren
            status_style = {
                DownloadStatus.COMPLETED.value: "[green]✓[/green]",
                DownloadStatus.FAILED.value: "[red]✗[/red]",
                DownloadStatus.DOWNLOADING.value: "[yellow]↓[/yellow]",
                DownloadStatus.PENDING.value: "[dim]…[/dim]",
            }.get(str(file.status), str(file.status))
            
            # Korrigiere den Zugriff auf die duration und downloaded_at Felder
            duration_value = getattr(file, 'duration', 0) or 0
            duration_str = format_duration(float(duration_value)) if duration_value is not None else "-"
            downloaded_at_value = getattr(file, 'downloaded_at', None)
            downloaded_at_str = downloaded_at_value.strftime("%d.%m.%Y %H:%M") if downloaded_at_value is not None else "-"
            
            # Basis-Zeile vorbereiten
            row_data = [
                file.title or file.file_name,
                file.performer or "Unbekannt",
                size_str,
                duration_str,
                file.file_extension[1:].upper() if file.file_extension else "-",
                file.checksum_md5[:8] + "..." if file.checksum_md5 else "-",
                status_style,
                file.group.title if file.group else "-",
                downloaded_at_str
            ]
            
            table.add_row(*row_data)
        
        console_obj.print(table)
        console_obj.print(f"[dim]{len(results)} Dateien gefunden[/dim]")
        
    except Exception as e:
        handle_error(e, "search", exit_on_error=True)


@cli.command()
@click.pass_context
@log_function_call
def history(ctx):
    """Zeigt die Download-Historie an."""
    try:
        config = ctx.obj["CONFIG"]
        console_obj = ctx.obj["console"]
        
        # Hole die Download-Historie aus der Datenbank
        from .models import DownloadStatus
        history = AudioFile.select().order_by(AudioFile.downloaded_at.desc()).limit(20)
        
        if not history:
            console_obj.print("[yellow]Keine Downloads in der Historie.[/yellow]")
            return
        
        # Erstelle eine Tabelle zur Anzeige der Historie
        table = Table(title="Download-Historie")
        table.add_column("Titel", style="cyan", no_wrap=True)
        table.add_column("Künstler", style="green")
        table.add_column("Größe", justify="right")
        table.add_column("Dauer", justify="right")
        table.add_column("Format", justify="center")
        table.add_column("Checksum", style="dim")
        table.add_column("Status", justify="center")
        table.add_column("Gruppe", style="blue")
        table.add_column("Heruntergeladen am", style="dim")
        
        for file in history:
            # Dateigröße formatieren
            size_mb = file.file_size / (1024 * 1024)
            size_str = f"{size_mb:.1f} MB"
            
            # Status formatieren
            status_style = {
                DownloadStatus.COMPLETED.value: "[green]✓[/green]",
                DownloadStatus.FAILED.value: "[red]✗[/red]",
                DownloadStatus.DOWNLOADING.value: "[yellow]↓[/yellow]",
                DownloadStatus.PENDING.value: "[dim]…[/dim]",
            }.get(str(file.status), str(file.status))
            
            # Korrigiere den Zugriff auf die duration und downloaded_at Felder
            duration_value = getattr(file, 'duration', 0) or 0
            duration_str = format_duration(float(duration_value)) if duration_value is not None else "-"
            downloaded_at_value = getattr(file, 'downloaded_at', None)
            downloaded_at_str = downloaded_at_value.strftime("%d.%m.%Y %H:%M") if downloaded_at_value is not None else "-"
            
            # Basis-Zeile vorbereiten
            row_data = [
                file.title or file.file_name,
                file.performer or "Unbekannt",
                size_str,
                duration_str,
                file.file_extension[1:].upper() if file.file_extension else "-",
                file.checksum_md5[:8] + "..." if file.checksum_md5 else "-",
                status_style,
                file.group.title if file.group else "-",
                downloaded_at_str
            ]
            
            table.add_row(*row_data)
        
        console_obj.print(table)
        
    except Exception as e:
        handle_error(e, "history", exit_on_error=True)


@cli.group()
@click.pass_context
def config(ctx):
    """Verwaltet die Konfiguration."""
    try:
        config = ctx.obj["CONFIG"]
        ctx.obj["console"] = console
        
    except Exception as e:
        handle_error(e, "config_group", exit_on_error=True)


@config.command()
@click.pass_context
@log_function_call
def show(ctx):
    """Zeigt die aktuelle Konfiguration an."""
    try:
        config = ctx.obj["CONFIG"]
        console_obj = ctx.obj["console"]
        
        config_data = config.to_dict()
        console_obj.print("Aktuelle Konfiguration:")
        for key, value in config_data.items():
            console_obj.print(f"{key}: {value}")
        
    except Exception as e:
        handle_error(e, "config_show", exit_on_error=True)


@config.command()
@click.argument("key")
@click.argument("value")
@click.pass_context
@log_function_call
def set(ctx, key: str, value: str):
    """Setzt einen Konfigurationswert."""
    try:
        config = ctx.obj["CONFIG"]
        console_obj = ctx.obj["console"]
        
        config.set(key, value)
        config.save()
        console_obj.print(f"[green]Konfigurationswert '{key}' auf '{value}' gesetzt[/green]")
        
    except Exception as e:
        handle_error(e, "config_set", exit_on_error=True)


@cli.command()
@click.option("--group", "-g", required=True, help="Name der Telegram-Gruppe")
@click.option("--limit", "-l", type=int, help="Maximale Anzahl an Dateien zum Herunterladen")
@click.option("--output", "-o", type=click.Path(), help="Ausgabeverzeichnis")
@click.option("--parallel", "-p", type=int, help="Anzahl paralleler Downloads")
@click.option("--priority", "-P", type=click.Choice(['LOW', 'NORMAL', 'HIGH', 'CRITICAL']), default='NORMAL', help="Priorität des Batch-Jobs")
@click.pass_context
@log_function_call
def batch_add(ctx, group: str, limit: Optional[int], output: Optional[str], parallel: Optional[int], priority: str):
    """Fügt einen Download-Auftrag zur Batch-Verarbeitung hinzu."""
    try:
        config = ctx.obj["CONFIG"]
        console_obj = ctx.obj["console"]
        
        # Erstelle einen Batch-Item
        batch_item = BatchItem(
            id=f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            group_name=group,
            limit=limit,
            priority=Priority[priority],
            output_dir=Path(output) if output else None,
            parallel_downloads=parallel
        )
        
        # Speichere den Batch-Item (in einer echten Implementierung würde dies in einer Datenbank gespeichert)
        # Für dieses Beispiel fügen wir ihn einfach zu einer Liste hinzu
        if "batch_queue" not in ctx.obj:
            ctx.obj["batch_queue"] = []
        ctx.obj["batch_queue"].append(batch_item)
        
        console_obj.print(f"[green]Batch-Auftrag {batch_item.id} zur Warteschlange hinzugefügt[/green]")
        console_obj.print(f"  Gruppe: {group}")
        console_obj.print(f"  Priorität: {priority}")
        if limit:
            console_obj.print(f"  Limit: {limit}")
        if output:
            console_obj.print(f"  Ausgabeverzeichnis: {output}")
        if parallel:
            console_obj.print(f"  Parallele Downloads: {parallel}")
            
    except Exception as e:
        error = ConfigurationError(f"Fehler beim Hinzufügen des Batch-Auftrags: {e}")
        handle_error(error, "batch_add", exit_on_error=True)


@cli.command()
@click.option("--max-concurrent", "-c", type=int, default=3, help="Maximale Anzahl gleichzeitiger Batch-Verarbeitungen")
@click.pass_context
@log_function_call
def batch_process(ctx, max_concurrent: int):
    """Verarbeitet alle Batch-Aufträge in der Warteschlange."""
    try:
        config = ctx.obj["CONFIG"]
        console_obj = ctx.obj["console"]
        logger = ctx.obj["LOGGER"]
        
        # Prüfe, ob Batch-Aufträge vorhanden sind
        if "batch_queue" not in ctx.obj or not ctx.obj["batch_queue"]:
            console_obj.print("[yellow]Keine Batch-Aufträge in der Warteschlange[/yellow]")
            return
        
        # Erstelle den Batch-Prozessor
        batch_processor = BatchProcessor(max_concurrent_batches=max_concurrent)
        
        # Füge alle Batch-Items zum Prozessor hinzu
        for item in ctx.obj["batch_queue"]:
            batch_processor.add_batch_item(item)
        
        # Erstelle eine Download-Funktion, die mit dem Batch-Prozessor kompatibel ist
        async def download_function(group: str, limit: Optional[int] = None, output: Optional[str] = None, parallel: Optional[int] = None):
            downloader = AudioDownloader(
                download_dir=output or config.download_dir,
                max_concurrent_downloads=parallel or config.max_concurrent_downloads
            )
            await downloader.download_audio_files(group, limit)
        
        # Verarbeite die Batch-Aufträge
        console_obj.print(f"[blue]Starte Batch-Verarbeitung mit {len(ctx.obj['batch_queue'])} Aufträgen[/blue]")
        asyncio.run(batch_processor.process_batches(download_function))
        
        # Zeige eine Zusammenfassung
        progress = batch_processor.get_progress()
        console_obj.print("[bold blue]Batch-Verarbeitung abgeschlossen[/bold blue]")
        console_obj.print(f"  Gesamt: {progress['total_items']}")
        console_obj.print(f"  Abgeschlossen: {progress['completed_items']}")
        console_obj.print(f"  Fehlgeschlagen: {progress['failed_items']}")
        console_obj.print(f"  Gesamtfortschritt: {progress['overall_progress']:.2%}")
        
        # Sende Benachrichtigung über abgeschlossene Batch-Verarbeitung
        try:
            from .advanced_notifications import send_batch_completed_notification
            send_batch_completed_notification(
                total_files=progress['total_items'],
                successful=progress['completed_items'],
                failed=progress['failed_items']
            )
        except Exception as e:
            logger.warning(f"Fehler beim Senden der Batch-Benachrichtigung: {e}")
        
        # Leere die Warteschlange
        ctx.obj["batch_queue"] = []
        
    except Exception as e:
        error = ConfigurationError(f"Fehler bei der Batch-Verarbeitung: {e}")
        handle_error(error, "batch_process", exit_on_error=True)


@cli.command()
@click.pass_context
@log_function_call
def batch_list(ctx):
    """Listet alle Batch-Aufträge in der Warteschlange auf."""
    try:
        console_obj = ctx.obj["console"]
        logger = ctx.obj["LOGGER"]
        
        # Prüfe, ob Batch-Aufträge vorhanden sind
        if "batch_queue" not in ctx.obj or not ctx.obj["batch_queue"]:
            console_obj.print("[yellow]Keine Batch-Aufträge in der Warteschlange[/yellow]")
            return
        
        # Erstelle eine Tabelle zur Anzeige der Batch-Aufträge
        table = Table(title="Batch-Aufträge in der Warteschlange")
        table.add_column("ID", style="cyan")
        table.add_column("Gruppe", style="magenta")
        table.add_column("Limit", style="green")
        table.add_column("Priorität", style="yellow")
        table.add_column("Ausgabeverzeichnis", style="blue")
        table.add_column("Parallele Downloads", style="red")
        
        for item in ctx.obj["batch_queue"]:
            table.add_row(
                item.id,
                item.group_name,
                str(item.limit) if item.limit else "Kein Limit",
                item.priority.name,
                str(item.output_dir) if item.output_dir else "Standard",
                str(item.parallel_downloads) if item.parallel_downloads else "Standard"
            )
        
        console_obj.print(table)
        
    except Exception as e:
        error = ConfigurationError(f"Fehler beim Auflisten der Batch-Aufträge: {e}")
        handle_error(error, "batch_list", exit_on_error=True)


@cli.command()
@click.option("--output", "-o", type=click.Path(), help="Ausgabeverzeichnis (standardmäßig aus Konfiguration)")
@click.pass_context
@log_function_call
def show_downloads(ctx, output: Optional[str]):
    """Zeigt das Download-Verzeichnis im Dateimanager an."""
    try:
        config = ctx.obj["CONFIG"]
        console_obj = ctx.obj["console"]
        logger = ctx.obj["LOGGER"]
        
        # Bestimme das Download-Verzeichnis
        if output:
            download_dir = Path(output)
        else:
            download_dir = Path(config.download_dir)
        
        # Prüfe, ob das Verzeichnis existiert
        if not download_dir.exists():
            console_obj.print(f"[yellow]Download-Verzeichnis {download_dir} existiert nicht[/yellow]")
            # Frage den Benutzer, ob er das Verzeichnis erstellen möchte
            if click.confirm("Soll das Verzeichnis erstellt werden?"):
                download_dir.mkdir(parents=True, exist_ok=True)
                console_obj.print(f"[green]Download-Verzeichnis {download_dir} erstellt[/green]")
            else:
                return
        
        # Importiere den Downloader, um die Funktion zu verwenden
        from .downloader import AudioDownloader
        
        # Erstelle einen temporären Downloader, um die Funktion zu verwenden
        downloader = AudioDownloader(download_dir=str(download_dir))
        result = downloader.show_downloads_in_file_manager()
        
        if result:
            console_obj.print(f"[green]Download-Verzeichnis {download_dir} im Dateimanager geöffnet[/green]")
        else:
            console_obj.print(f"[red]Fehler beim Öffnen des Download-Verzeichnisses {download_dir}[/red]")
            
    except Exception as e:
        error = ConfigurationError(f"Fehler beim Öffnen des Download-Verzeichnisses: {e}")
        handle_error(error, "show_downloads", exit_on_error=True)


def check_env() -> bool:
    """Überprüft, ob alle erforderlichen Umgebungsvariablen gesetzt sind."""
    # Die Validierung erfolgt jetzt über die Config-Klasse
    return True


def main():
    """Hauptfunktion für die Kommandozeilenschnittstelle."""
    try:
        cli(obj={})
    except KeyboardInterrupt:
        console.print("\n[red]Vorgang abgebrochen[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Fehler: {e}[/red]")
        sys.exit(1)
    finally:
        # Datenbankverbindung schließen
        from .database import close_db
        close_db()


if __name__ == "__main__":
    main()