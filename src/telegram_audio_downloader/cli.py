"""
Kommandozeilenschnittstelle für den Telegram Audio Downloader.
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .config import Config
from .database import init_db
from .downloader import AudioDownloader
from .error_handling import handle_error, ConfigurationError
from .logger import get_logger, log_function_call
from .batch_processing import BatchItem, BatchProcessor, Priority
from .enhanced_user_interaction import (
    show_download_summary, enable_interactive_mode, disable_interactive_mode
)
from .utils import format_file_size

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


def load_config(config_path: Optional[str] = None) -> Config:
    """Lädt die Konfiguration mit Priorisierung.
    
    Args:
        config_path: Optionaler Pfad zur Konfigurationsdatei
        
    Returns:
        Config: Geladene Konfiguration
    """
    try:
        # Lade Konfiguration mit CLI-Argumenten
        config = Config(config_path=config_path)
        
        # Validiere erforderliche Felder
        config.validate_required_fields()
        
        return config
    except ConfigurationError as e:
        handle_error(e, "load_config", exit_on_error=True)
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
    config_obj = load_config(config_path=config)
    
    # Logging-System initialisieren
    logger = get_logger(debug=debug)

    # Banner anzeigen
    print_banner()

    # Datenbank initialisieren
    init_db()

    # Kontext für Unterkommandos vorbereiten
    ctx.ensure_object(dict)
    ctx.obj["CONFIG"] = config_obj
    ctx.obj["LOGGER"] = logger
    ctx.obj["INTERACTIVE"] = interactive

    # Performance-Monitoring initialisieren
    from .performance import PerformanceMonitor
    performance_monitor = PerformanceMonitor()
    ctx.obj["PERFORMANCE_MONITOR"] = performance_monitor


@cli.command()
@click.option("--group", "-g", required=True, help="Name oder ID der Telegram-Gruppe")
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
    # Note: filename_template parameter is currently unused but kept for future implementation
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
        output_path = Path(output) if output else Path(config.download_dir)
        output_path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        error = ConfigurationError(f"Fehler beim Erstellen des Ausgabeverzeichnisses: {e}")
        handle_error(error, "download_output_dir", exit_on_error=True)
        return

    # Downloader initialisieren
    downloader = AudioDownloader(
        download_dir=str(output_path),
        max_concurrent_downloads=parallel or config.max_concurrent_downloads,
        config=config
    )

    # Interaktiven Modus aktivieren wenn angefordert
    if interactive or ctx.obj.get("INTERACTIVE"):
        enable_interactive_mode()
    else:
        disable_interactive_mode()

    # Batch-Verarbeitung initialisieren
    batch_processor = BatchProcessor(downloader, max_workers=parallel or config.max_concurrent_downloads)
    
    # Download-Statistiken initialisieren
    start_time = datetime.now()
    downloaded_count = 0
    failed_count = 0
    total_size = 0

    # Download-Fortschritt anzeigen
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
    ) as progress:
        task = progress.add_task("Verbinde mit Telegram...", total=None)
        
        async def run_download():
            nonlocal downloaded_count, failed_count, total_size
            try:
                # Telegram-Client initialisieren
                logger = ctx.obj.get("LOGGER", get_logger())
                
                # Verbindung mit Telegram herstellen
                await downloader.connect()
                progress.update(task, description="Suche Audiodateien...")
                
                # Audiodateien in der Gruppe suchen
                audio_files = await downloader.search_audio_files(group, limit=limit)
                if not audio_files:
                    console.print("[yellow]Keine Audiodateien in der Gruppe gefunden[/yellow]")
                    return

                # Batch-Items erstellen
                batch_items = [
                    BatchItem(
                        file_id=file.id,
                        filename=file.name,
                        priority=Priority.HIGH if file.size > 10 * 1024 * 1024 else Priority.NORMAL,
                        metadata={"size": file.size, "duration": file.duration}
                    )
                    for file in audio_files
                ]

                # Download-Task aktualisieren
                progress.update(task, total=len(batch_items), description="Lade Dateien herunter...")
                
                # Batch-Verarbeitung starten
                results = await batch_processor.process_batch(batch_items)
                
                # Statistiken aktualisieren
                for result in results:
                    if result.success:
                        downloaded_count += 1
                        total_size += result.metadata.get("size", 0) if result.metadata else 0
                    else:
                        failed_count += 1
                        logger.error(f"Download fehlgeschlagen für {result.item.filename}: {result.error}")
                
                # Download abschließen
                await downloader.disconnect()
                
                # Download-Zusammenfassung anzeigen
                end_time = datetime.now()
                duration = end_time - start_time
                stats = {
                    "total_files": len(batch_items),
                    "successful_downloads": downloaded_count,
                    "failed_downloads": failed_count,
                    "total_size": format_file_size(total_size),
                    "duration": str(duration),
                    "avg_speed": "Unbekannt"
                }
                show_download_summary(stats)
                
            except Exception as e:
                await downloader.disconnect()
                error = ConfigurationError(f"Fehler beim Herunterladen: {e}")
                handle_error(error, "download", exit_on_error=True)

        # Run the async download
        asyncio.run(run_download())


@cli.command()
@click.option("--group", "-g", required=True, help="Name oder ID der Telegram-Gruppe")
@click.option("--limit", "-l", type=int, help="Maximale Anzahl an Dateien zum Herunterladen")
@click.option("--output", "-o", type=click.Path(), help="Ausgabeverzeichnis")
@click.option("--parallel", "-p", type=int, help="Anzahl paralleler Downloads")
@click.pass_context
@log_function_call
def lite(ctx, group: str, limit: Optional[int], output: Optional[str], parallel: Optional[int]):
    """Lite-Modus: Schnelles Herunterladen ohne komplexe Funktionen."""
    config = ctx.obj["CONFIG"]
    
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
        output_path = Path(output) if output else Path(config.download_dir)
        output_path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        error = ConfigurationError(f"Fehler beim Erstellen des Ausgabeverzeichnisses: {e}")
        handle_error(error, "download_output_dir", exit_on_error=True)
        return

    # Lite-Modus aktivieren
    console.print("[blue]Lite-Modus aktiviert[/blue]")

    # Downloader initialisieren
    downloader = AudioDownloader(
        download_dir=str(output_path),
        max_concurrent_downloads=parallel or config.max_concurrent_downloads,
        config=config
    )

    # Download-Statistiken initialisieren
    start_time = datetime.now()
    downloaded_count = 0

    # Download-Fortschritt anzeigen
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Verbinde mit Telegram...", total=None)
        
        async def run_download():
            nonlocal downloaded_count
            try:
                # Telegram-Client initialisieren
                logger = ctx.obj.get("LOGGER", get_logger())
                
                # Verbindung mit Telegram herstellen
                await downloader.connect()
                progress.update(task, description="Suche Audiodateien...")
                
                # Audiodateien in der Gruppe suchen
                audio_files = await downloader.search_audio_files(group, limit=limit)
                if not audio_files:
                    console.print("[yellow]Keine Audiodateien in der Gruppe gefunden[/yellow]")
                    return

                # Download-Task aktualisieren
                progress.update(task, total=len(audio_files), description="Lade Dateien herunter...")
                
                # Dateien herunterladen
                for file in audio_files:
                    try:
                        await downloader.download_file(file)
                        downloaded_count += 1
                        progress.update(task, advance=1)
                    except Exception as e:
                        logger.error(f"Fehler beim Herunterladen von {file.name}: {e}")
                        continue
                
                # Download abschließen
                await downloader.disconnect()
                
                # Download-Zusammenfassung anzeigen
                end_time = datetime.now()
                duration = end_time - start_time
                stats = {
                    "total_files": downloaded_count,
                    "successful_downloads": downloaded_count,
                    "failed_downloads": 0,
                    "total_size": "Unbekannt",
                    "duration": str(duration),
                    "avg_speed": "Unbekannt"
                }
                show_download_summary(stats)
                
            except Exception as e:
                await downloader.disconnect()
                error = ConfigurationError(f"Unerwarteter Fehler beim Herunterladen: {e}")
                handle_error(error, "download_lite", exit_on_error=True)

        # Run the async download
        asyncio.run(run_download())


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