"""
Kommandozeilenschnittstelle für den Telegram Audio Downloader.
"""

import asyncio
import os
import sys
import time
from pathlib import Path
from typing import Optional

import click
from peewee import JOIN, fn
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from .error_handling import (
    AuthenticationError,
    ConfigurationError,
    DatabaseError,
    DownloadError,
    FileOperationError,
    NetworkError,
    TelegramAPIError,
    get_error_handler,
    handle_error,
)
from .database import close_db, init_db
from .downloader import AudioDownloader, DownloadStatus
from .logging_config import get_error_tracker, get_logger, setup_logging
from .models import AudioFile, TelegramGroup
from .performance import get_performance_monitor
from .memory_utils import perform_memory_cleanup, get_memory_monitor

# Rich-Konsole
console = Console()
error_handler = get_error_handler()


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


def check_env() -> bool:
    """Überprüft, ob alle erforderlichen Umgebungsvariablen gesetzt sind."""
    required_vars = ["API_ID", "API_HASH"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        error = ConfigurationError(
            f"Fehlende Umgebungsvariablen: {', '.join(missing_vars)}. "
            "Bitte erstellen Sie eine .env-Datei mit den erforderlichen Variablen. "
            "Beispiel: API_ID=12345, API_HASH=your_api_hash_here, SESSION_NAME=session_name"
        )
        handle_error(error, "check_env", exit_on_error=True)
        return False
    return True


@click.group()
@click.option("--debug", is_flag=True, help="Aktiviert den Debug-Modus")
@click.pass_context
def cli(ctx, debug):
    """Hauptbefehl für den Telegram Audio Downloader."""
    # Logging-System initialisieren
    logger = setup_logging(debug=debug)

    # Banner anzeigen
    print_banner()

    # Datenbank initialisieren
    try:
        init_db()
        logger.info("Datenbank erfolgreich initialisiert")
    except Exception as e:
        error = DatabaseError(f"Fehler bei Datenbank-Initialisierung: {e}")
        handle_error(error, "cli_init_db", exit_on_error=True)

    # Context-Objekt initialisieren
    ctx.ensure_object(dict)
    ctx.obj["DEBUG"] = debug
    ctx.obj["LOGGER"] = logger


@cli.command()
@click.argument("group")
@click.option(
    "--limit",
    type=int,
    default=None,
    help="Maximale Anzahl der zu verarbeitenden Nachrichten",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(file_okay=False),
    default="downloads",
    help="Ausgabeverzeichnis für die heruntergeladenen Dateien",
)
@click.option(
    "--parallel",
    "-p",
    type=click.IntRange(1, 10),
    default=3,
    help="Maximale Anzahl paralleler Downloads (Standard: 3, Max: 10)",
)
@click.pass_context
def download(ctx, group: str, limit: Optional[int], output: str, parallel: int):
    """Lädt Audiodateien aus einer Telegram-Gruppe herunter."""
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
        output_path = Path(output)
        output_path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        error = FileOperationError(f"Fehler beim Erstellen des Ausgabeverzeichnisses: {e}")
        handle_error(error, "download_output_dir", exit_on_error=True)
        return

    # Downloader initialisieren
    downloader = AudioDownloader(
        download_dir=str(output_path), max_concurrent_downloads=parallel
    )

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
                error_tracker = get_error_tracker()

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

                    # Error-Summary anzeigen
                    error_summary = error_tracker.get_error_summary()
                    if error_summary["total"] > 0:
                        console.print(
                            f"\n[yellow]Warnung: {error_summary['total']} Fehler aufgetreten[/yellow]"
                        )
                        if ctx.obj.get("DEBUG"):
                            console.print("Letzte Fehler:")
                            for error in error_summary["recent"]:
                                console.print(
                                    f"  - {error['type']} in {error['context']} ({error['time']})"
                                )

                except Exception as e:
                    error_tracker.track_error(e, "cli_download", "ERROR")
                    logger.error(
                        f"Download-Fehler: {e}", exc_info=ctx.obj.get("DEBUG", False)
                    )
                    
                    # Spezifische Fehlerbehandlung
                    if "API_ID" in str(e) or "API_HASH" in str(e):
                        error = AuthenticationError("Ungültige oder fehlende API-Zugangsdaten")
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
@click.argument("query", required=False)
@click.option("--group", "-g", help="Filtere nach einer bestimmten Gruppe")
@click.option(
    "--status",
    type=click.Choice([s.value for s in DownloadStatus]),
    help="Filtere nach Download-Status",
)
@click.option(
    "--limit", type=click.IntRange(1, 1000), default=10, help="Maximale Anzahl der anzuzeigenden Ergebnisse (1-1000)"
)
@click.option("--all", "show_all", is_flag=True, help="Zeige alle Einträge an")
@click.option("--metadata", "-m", is_flag=True, help="Zeige erweiterte Metadaten an")
@click.option(
    "--fuzzy", "-f", is_flag=True, help="Aktiviere Fuzzy-Suche (unscharfe Suche)"
)
@click.option("--min-size", type=str, help='Minimale Dateigröße (z.B. "5MB")')
@click.option("--max-size", type=str, help='Maximale Dateigröße (z.B. "100MB")')
@click.option("--format", "audio_format", help="Audioformat filtern (mp3, flac, etc.)")
@click.option("--duration-min", type=click.IntRange(0, 86400), help="Minimale Dauer in Sekunden (0-86400)")
@click.option("--duration-max", type=click.IntRange(0, 86400), help="Maximale Dauer in Sekunden (0-86400)")
def search(
    query: Optional[str],
    group: Optional[str],
    status: Optional[str],
    limit: int,
    show_all: bool,
    metadata: bool,
    fuzzy: bool,
    min_size: Optional[str],
    max_size: Optional[str],
    audio_format: Optional[str],
    duration_min: Optional[int],
    duration_max: Optional[int],
):
    """Durchsucht heruntergeladene Audiodateien mit erweiterten Filtern."""
    
    # Validierung der Dauer-Parameter
    if duration_min is not None and duration_max is not None and duration_min > duration_max:
        console.print("[red]Fehler: duration-min darf nicht größer als duration-max sein[/red]")
        return

    # Hilfsfunktion für Größen-Parsing
    def parse_size(size_str: str) -> int:
        """Konvertiert Größen-Strings wie '5MB' zu Bytes."""
        if not size_str:
            return 0
            
        size_str = size_str.upper().strip()
        if size_str.endswith("KB"):
            return int(float(size_str[:-2]) * 1024)
        elif size_str.endswith("MB"):
            return int(float(size_str[:-2]) * 1024 * 1024)
        elif size_str.endswith("GB"):
            return int(float(size_str[:-2]) * 1024 * 1024 * 1024)
        else:
            # Versuche, es als reine Zahl zu parsen (Bytes)
            try:
                return int(size_str)
            except ValueError:
                raise ValueError(f"Ungültiges Größenformat: {size_str}")

    # Validierung der Dateigrößen-Parameter
    if min_size:
        try:
            min_bytes = parse_size(min_size)
            if min_bytes < 0:
                console.print("[red]Fehler: Minimale Dateigröße muss positiv sein[/red]")
                return
        except ValueError as e:
            console.print(f"[red]Fehler: {e}[/red]")
            return

    if max_size:
        try:
            max_bytes = parse_size(max_size)
            if max_bytes < 0:
                console.print("[red]Fehler: Maximale Dateigröße muss positiv sein[/red]")
                return
        except ValueError as e:
            console.print(f"[red]Fehler: {e}[/red]")
            return

    # Validierung, dass min_size nicht größer als max_size ist
    if min_size and max_size:
        try:
            min_bytes = parse_size(min_size)
            max_bytes = parse_size(max_size)
            if min_bytes > max_bytes:
                console.print("[red]Fehler: Minimale Dateigröße darf nicht größer als maximale Dateigröße sein[/red]")
                return
        except ValueError:
            # Fehler wurden bereits oben behandelt
            return

    # Validierung des Audioformat-Parameters
    if audio_format:
        valid_formats = {"mp3", "m4a", "ogg", "flac", "wav", "opus"}
        if audio_format.lower() not in valid_formats:
            console.print(f"[red]Fehler: Ungültiges Audioformat. Gültige Formate: {', '.join(valid_formats)}[/red]")
            return

    # Basis-Abfrage erstellen
    query_set = AudioFile.select()

    # Textsuche (erweitert mit Fuzzy-Option)
    if query:
        if fuzzy:
            # Fuzzy-Suche: Toleriert Schreibfehler
            # Vereinfachte Implementierung mit LIKE und Wildcards
            fuzzy_query = f"%{query.replace(' ', '%')}%"
            query_set = query_set.where(
                (AudioFile.title.contains(query))
                | (AudioFile.performer.contains(query))
                | (AudioFile.file_name.contains(query))
                | (AudioFile.title**fuzzy_query)  # Peewee fuzzy matching
                | (AudioFile.performer**fuzzy_query)
                | (AudioFile.file_name**fuzzy_query)
            )
        else:
            # Normale Suche
            query_set = query_set.where(
                (AudioFile.title.contains(query))
                | (AudioFile.performer.contains(query))
                | (AudioFile.file_name.contains(query))
            )

    # Weitere Filter anwenden
    if group:
        query_set = query_set.join(TelegramGroup).where(
            (TelegramGroup.title.contains(group))
            | (TelegramGroup.username.contains(group))
        )

    if status:
        query_set = query_set.where(AudioFile.status == status)

    # Dateigrößen-Filter
    if min_size:
        try:
            min_bytes = parse_size(min_size)
            query_set = query_set.where(AudioFile.file_size >= min_bytes)
        except ValueError:
            console.print(f"[red]Ungültige Größen-Angabe: {min_size}[/red]")
            return

    if max_size:
        try:
            max_bytes = parse_size(max_size)
            query_set = query_set.where(AudioFile.file_size <= max_bytes)
        except ValueError:
            console.print(f"[red]Ungültige Größen-Angabe: {max_size}[/red]")
            return

    # Format-Filter
    if audio_format:
        format_extension = f".{audio_format.lower()}"
        query_set = query_set.where(AudioFile.file_name.endswith(format_extension))

    # Dauer-Filter
    if duration_min:
        query_set = query_set.where(AudioFile.duration >= duration_min)

    if duration_max:
        query_set = query_set.where(AudioFile.duration <= duration_max)

    # Sortierung und Limit
    query_set = query_set.order_by(AudioFile.downloaded_at.desc())

    if not show_all:
        query_set = query_set.limit(limit)

    # Ergebnisse anzeigen
    files = list(query_set)

    if not files:
        console.print("[yellow]Keine Dateien gefunden.[/yellow]")
        return

    # Tabelle erstellen
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Titel", style="cyan", no_wrap=True)
    table.add_column("Künstler", style="green")
    table.add_column("Größe", justify="right")

    if metadata:
        table.add_column("Dauer", justify="right")
        table.add_column("Format", justify="center")
        table.add_column("Checksum", style="dim")

    table.add_column("Status", justify="center")
    table.add_column("Gruppe", style="blue")
    table.add_column("Heruntergeladen am", style="dim")

    for file in files:
        # Dateigröße formatieren
        size_mb = file.file_size / (1024 * 1024)
        size_str = f"{size_mb:.1f} MB"

        # Status formatieren
        status_style = {
            DownloadStatus.COMPLETED.value: "[green]✓[/green]",
            DownloadStatus.FAILED.value: "[red]✗[/red]",
            DownloadStatus.DOWNLOADING.value: "[yellow]↓[/yellow]",
            DownloadStatus.PENDING.value: "[dim]…[/dim]",
        }.get(file.status, file.status)

        # Basis-Zeile vorbereiten
        row_data = [
            file.title or file.file_name,
            file.performer or "Unbekannt",
            size_str,
        ]

        # Erweiterte Metadaten hinzufügen
        if metadata:
            from .utils import format_duration

            duration_str = format_duration(file.duration) if file.duration else "-"
            format_str = file.file_extension[1:].upper() if file.file_extension else "-"
            checksum_short = file.checksum_md5[:8] + "..." if file.checksum_md5 else "-"

            row_data.extend([duration_str, format_str, checksum_short])

        # Status und weitere Daten hinzufügen
        row_data.extend(
            [
                status_style,
                file.group.title if file.group else "-",
                (
                    file.downloaded_at.strftime("%d.%m.%Y %H:%M")
                    if file.downloaded_at
                    else "-"
                ),
            ]
        )

        table.add_row(*row_data)

    console.print(table)
    console.print(f"[dim]{len(files)} Dateien gefunden[/dim]")


@cli.command()
def groups():
    """Zeigt alle bekannten Telegram-Gruppen an."""
    groups = TelegramGroup.select().order_by(TelegramGroup.title)

    if not groups:
        console.print("[yellow]Keine Gruppen gefunden.[/yellow]")
        return

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("ID", style="cyan")
    table.add_column("Titel", style="green")
    table.add_column("Benutzername", style="blue")
    table.add_column("Letzte Überprüfung", style="dim")
    table.add_column("Dateien", justify="right")

    for group in groups:
        file_count = AudioFile.select().where(AudioFile.group == group).count()
        table.add_row(
            str(group.group_id),
            group.title,
            f"@{group.username}" if group.username else "-",
            (
                group.last_checked.strftime("%d.%m.%Y %H:%M")
                if group.last_checked
                else "-"
            ),
            str(file_count),
        )

    console.print(table)


@cli.command()
@click.option(
    "--update",
    "-u",
    is_flag=True,
    help="Aktualisiere Metadaten aus bereits heruntergeladenen Dateien",
)
@click.option("--verify", "-v", is_flag=True, help="Verifiziere Checksums")
@click.option("--file-id", help="Analysiere nur eine bestimmte Datei")
def metadata(update: bool, verify: bool, file_id: Optional[str]):
    """Analysiert und aktualisiert Metadaten von heruntergeladenen Dateien."""
    from pathlib import Path

    from .utils import calculate_file_hash, extract_audio_metadata

    # Dateien für Analyse auswählen
    query = AudioFile.select().where(AudioFile.status == DownloadStatus.COMPLETED.value)

    if file_id:
        query = query.where(AudioFile.file_id == file_id)

    files = list(query)

    if not files:
        console.print("[yellow]Keine Dateien für Metadaten-Analyse gefunden.[/yellow]")
        return

    console.print(f"[blue]Analysiere {len(files)} Datei(en)...[/blue]")

    updated_count = 0
    verified_count = 0
    error_count = 0

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task("Analysiere Metadaten...", total=len(files))

        for file in files:
            if not file.local_path or not Path(file.local_path).exists():
                error_count += 1
                progress.update(
                    task,
                    advance=1,
                    description=f"Datei nicht gefunden: {file.file_name}",
                )
                continue

            try:
                file_path = Path(file.local_path)

                # Metadaten aktualisieren
                if update:
                    metadata_info = extract_audio_metadata(file_path)

                    changes_made = False
                    if not file.title and metadata_info.get("title"):
                        file.title = metadata_info["title"]
                        changes_made = True

                    if not file.performer and metadata_info.get("artist"):
                        file.performer = metadata_info["artist"]
                        changes_made = True

                    if not file.duration and metadata_info.get("duration"):
                        file.duration = int(metadata_info["duration"])
                        changes_made = True

                    if changes_made:
                        file.save()
                        updated_count += 1

                # Checksum verifizieren
                if verify:
                    if file.checksum_md5:
                        current_checksum = calculate_file_hash(file_path, "md5")
                        if current_checksum == file.checksum_md5:
                            verified_count += 1
                        else:
                            console.print(
                                f"[red]Checksum-Fehler: {file.file_name}[/red]"
                            )
                            error_count += 1
                    else:
                        # Checksum erstmalig berechnen
                        file.checksum_md5 = calculate_file_hash(file_path, "md5")
                        file.checksum_verified = True
                        file.save()
                        verified_count += 1

                progress.update(
                    task, advance=1, description=f"Verarbeitet: {file.file_name}"
                )

            except Exception as e:
                console.print(f"[red]Fehler bei {file.file_name}: {e}[/red]")
                error_count += 1
                progress.update(task, advance=1)

    # Zusammenfassung
    console.print("\n[bold]Metadaten-Analyse abgeschlossen:[/bold]")
    if update:
        console.print(f"[green]Metadaten aktualisiert:[/green] {updated_count}")
    if verify:
        console.print(f"[blue]Checksums verifiziert:[/blue] {verified_count}")
    if error_count > 0:
        console.print(f"[red]Fehler:[/red] {error_count}")


@cli.command()
def stats():
    """Zeigt Statistiken zu den heruntergeladenen Dateien an."""
    # Gesamtstatistiken
    total_files = AudioFile.select().count()
    completed = (
        AudioFile.select()
        .where(AudioFile.status == DownloadStatus.COMPLETED.value)
        .count()
    )
    failed = (
        AudioFile.select()
        .where(AudioFile.status == DownloadStatus.FAILED.value)
        .count()
    )
    total_size = sum(f.file_size for f in AudioFile.select() if f.file_size)

    # Statistiken nach Gruppe
    groups = (
        TelegramGroup.select(
            TelegramGroup,
            fn.COUNT(AudioFile.id).alias("file_count"),
            fn.SUM(AudioFile.file_size).alias("total_size"),
        )
        .join(AudioFile, JOIN.LEFT_OUTER)
        .group_by(TelegramGroup.id)
        .order_by(fn.COUNT(AudioFile.id).desc())
    )

    # Zusammenfassung anzeigen
    console.print("[bold]📊 Statistik[/bold]\n")
    console.print(f"[cyan]Gesamtanzahl Dateien:[/cyan] {total_files}")
    console.print(f"[green]Erfolgreich heruntergeladen:[/green] {completed}")
    console.print(f"[red]Fehlgeschlagen:[/red] {failed}")
    console.print(f"[blue]Gesamtgröße:[/blue] {total_size / (1024*1024):.2f} MB\n")

    # Gruppierte Statistiken
    if groups:
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Gruppe", style="cyan")
        table.add_column("Dateien", justify="right")
        table.add_column("Größe", justify="right")

        for group in groups:
            size_mb = (group.total_size or 0) / (1024 * 1024)
            table.add_row(group.title, str(group.file_count or 0), f"{size_mb:.2f} MB")

        console.print("[bold]📂 Nach Gruppe[/bold]")
        console.print(table)


@cli.command()
@click.option("--watch", "-w", is_flag=True, help="Überwache Performance in Echtzeit")
@click.option(
    "--cleanup",
    "-c",
    is_flag=True,
    help="Bereinige Temp-Dateien und führe Garbage Collection durch",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(file_okay=False),
    default="downloads",
    help="Download-Verzeichnis für Disk-Space-Analyse",
)
def performance(watch: bool, cleanup: bool, output: str):
    """Zeigt Performance-Statistiken und Systemmetriken an."""
    output_path = Path(output)

    # Performance-Monitor initialisieren
    perf_monitor = get_performance_monitor(output_path)

    if cleanup:
        console.print("[blue]🧹 Bereinige System...[/blue]")

        # Memory Cleanup
        freed_objects = perform_memory_cleanup()
        console.print(
            f"[green]✓ Garbage Collection: {freed_objects} Objekte bereinigt[/green]"
        )

        # Temp-Files Cleanup
        cleaned_files = perf_monitor.disk_manager.cleanup_temp_files()
        console.print(
            f"[green]✓ Temp-Dateien bereinigt: {cleaned_files} Dateien[/green]"
        )

        return

    if watch:
        console.print(
            "[blue]👁️  Performance-Überwachung gestartet (Strg+C zum Beenden)[/blue]"
        )
        console.print("[dim]Aktualisierung alle 5 Sekunden...[/dim]\n")

        try:
            while True:
                # Performance-Report abrufen
                report = perf_monitor.get_performance_report()

                # Bildschirm löschen
                os.system("cls" if os.name == "nt" else "clear")

                # Header
                console.print("[bold blue]📊 PERFORMANCE MONITOR[/bold blue]")
                console.print(
                    f"[dim]Laufzeit: {report['uptime_seconds']:.0f}s | {time.strftime('%H:%M:%S')}[/dim]\n"
                )

                # Downloads-Tabelle
                downloads_table = Table(title="Downloads", show_header=True)
                downloads_table.add_column("Metrik")
                downloads_table.add_column("Wert", justify="right")

                downloads_table.add_row(
                    "Erfolgreich", str(report["downloads"]["completed"])
                )
                downloads_table.add_row(
                    "Fehlgeschlagen", str(report["downloads"]["failed"])
                )
                downloads_table.add_row(
                    "Erfolgsrate", f"{report['downloads']['success_rate']:.1f}%"
                )
                downloads_table.add_row(
                    "Downloads/Min",
                    f"{report['performance']['downloads_per_minute']:.1f}",
                )
                downloads_table.add_row(
                    "Ø Geschwindigkeit",
                    f"{report['performance']['average_speed_mbps']:.1f} MB/s",
                )
                downloads_table.add_row(
                    "Gesamt heruntergeladen",
                    f"{report['performance']['total_gb_downloaded']:.2f} GB",
                )

                console.print(downloads_table)
                console.print()

                # System-Tabelle
                system_table = Table(title="System-Ressourcen", show_header=True)
                system_table.add_column("Ressource")
                system_table.add_column("Verwendung", justify="right")
                system_table.add_column("Status", justify="center")

                # Memory Status
                memory_mb = report["resources"]["memory_mb"]
                memory_status = (
                    "🟢" if memory_mb < 512 else "🟡" if memory_mb < 1024 else "🔴"
                )
                system_table.add_row(
                    "Arbeitsspeicher", f"{memory_mb:.0f} MB", memory_status
                )

                # CPU Status
                cpu_percent = report["resources"]["cpu_percent"]
                cpu_status = (
                    "🟢" if cpu_percent < 50 else "🟡" if cpu_percent < 80 else "🔴"
                )
                system_table.add_row("CPU", f"{cpu_percent:.1f}%", cpu_status)

                # Disk Status
                disk_free = report["resources"]["disk_free_gb"]
                disk_status = "🟢" if disk_free > 5 else "🟡" if disk_free > 1 else "🔴"
                system_table.add_row(
                    "Freier Speicher", f"{disk_free:.1f} GB", disk_status
                )

                console.print(system_table)
                console.print()

                # Rate-Limiting
                rate_table = Table(title="Rate-Limiting", show_header=True)
                rate_table.add_column("Metrik")
                rate_table.add_column("Wert", justify="right")

                rate_table.add_row(
                    "Aktuelle Rate",
                    f"{report['rate_limiting']['current_rate']:.2f} req/s",
                )
                rate_table.add_row(
                    "Verfügbare Tokens",
                    f"{report['rate_limiting']['tokens_available']:.1f}",
                )

                console.print(rate_table)
                console.print("\n[dim]Drücken Sie Strg+C zum Beenden...[/dim]")

                time.sleep(5)

        except KeyboardInterrupt:
            console.print("\n[yellow]Performance-Überwachung beendet[/yellow]")
            return

    else:
        # Einmalige Anzeige
        report = perf_monitor.get_performance_report()

        console.print("[bold blue]📊 PERFORMANCE REPORT[/bold blue]\n")

        # Allgemeine Info
        console.print(f"[cyan]Laufzeit:[/cyan] {report['uptime_seconds']:.0f} Sekunden")
        console.print(f"[cyan]Zeitpunkt:[/cyan] {time.strftime('%d.%m.%Y %H:%M:%S')}\n")

        # Downloads
        console.print("[bold]📥 Downloads[/bold]")
        console.print(
            f"  Erfolgreich: [green]{report['downloads']['completed']}[/green]"
        )
        console.print(f"  Fehlgeschlagen: [red]{report['downloads']['failed']}[/red]")
        console.print(f"  Erfolgsrate: {report['downloads']['success_rate']:.1f}%")
        console.print(
            f"  Gesamt heruntergeladen: {report['performance']['total_gb_downloaded']:.2f} GB"
        )
        console.print(
            f"  Ø Geschwindigkeit: {report['performance']['average_speed_mbps']:.1f} MB/s\n"
        )

        # System-Ressourcen
        console.print("[bold]🖥️  System-Ressourcen[/bold]")
        console.print(f"  Arbeitsspeicher: {report['resources']['memory_mb']:.0f} MB")
        console.print(f"  CPU-Auslastung: {report['resources']['cpu_percent']:.1f}%")
        console.print(
            f"  Festplatte verwendet: {report['resources']['disk_used_gb']:.1f} GB"
        )
        console.print(
            f"  Festplatte frei: {report['resources']['disk_free_gb']:.1f} GB\n"
        )

        # Rate-Limiting
        console.print("[bold]⏱️  Rate-Limiting[/bold]")
        console.print(
            f"  Aktuelle Rate: {report['rate_limiting']['current_rate']:.2f} Anfragen/Sekunde"
        )
        console.print(
            f"  Verfügbare Tokens: {report['rate_limiting']['tokens_available']:.1f}"
        )

        # System-Memory-Details
        memory_info = perf_monitor.memory_manager.get_system_memory_info()
        console.print("\n[bold]💾 System-Speicher[/bold]")
        console.print(f"  Gesamt: {memory_info['total_gb']:.1f} GB")
        console.print(f"  Verfügbar: {memory_info['available_gb']:.1f} GB")
        console.print(f"  Auslastung: {memory_info['used_percent']:.1f}%")

        # Empfehlungen
        console.print("\n[bold]💡 Empfehlungen[/bold]")
        if report["resources"]["memory_mb"] > 1024:
            console.print(
                "  [yellow]⚠️  Hoher Speicherverbrauch - erwägen Sie --cleanup[/yellow]"
            )
        if report["resources"]["disk_free_gb"] < 2:
            console.print("  [red]🚨 Wenig Festplattenspeicher verfügbar[/red]")
        if report["rate_limiting"]["current_rate"] < 0.5:
            console.print(
                "  [blue]ℹ️  Rate-Limiting aktiv - Downloads verlangsamt[/blue]"
            )

        if (
            report["resources"]["memory_mb"] <= 512
            and report["resources"]["disk_free_gb"] > 5
            and report["rate_limiting"]["current_rate"] >= 1.0
        ):
            console.print("  [green]✅ System läuft optimal[/green]")


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
        close_db()


if __name__ == "__main__":
    main()