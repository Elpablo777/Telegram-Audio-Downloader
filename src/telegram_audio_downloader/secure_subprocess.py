"""
Sichere Subprocess-Funktionen für den Telegram Audio Downloader.

Bietet sichere Wrapper für subprocess-Aufrufe mit zusätzlichen Sicherheitsmaßnahmen:
- Validierung von Eingabeparametern
- Beschränkung der Ausführungszeit
- Verhinderung von Shell-Injection
- Sichere Handhabung von Umgebungsvariablen
"""

import subprocess
import asyncio
import logging
import os
import sys
from typing import List, Optional, Dict, Any, Union
from pathlib import Path

from .error_handling import SystemIntegrationError, handle_error
from .logging_config import get_logger

logger = get_logger(__name__)


class SecureSubprocessError(SystemIntegrationError):
    """Fehler bei sicheren Subprocess-Operationen."""
    pass


def secure_run_command(
    command: List[str],
    timeout: int = 30,
    check: bool = True,
    capture_output: bool = True,
    cwd: Optional[Union[str, Path]] = None,
    env: Optional[Dict[str, str]] = None,
    allow_shell: bool = False
) -> subprocess.CompletedProcess:
    """
    Führt einen Befehl sicher aus.
    
    Args:
        command: Liste von Befehlsargumenten
        timeout: Timeout in Sekunden
        check: Ob bei Fehlern eine Exception geworfen werden soll
        capture_output: Ob Ausgabe erfasst werden soll
        cwd: Arbeitsverzeichnis
        env: Umgebungsvariablen
        allow_shell: Ob Shell-Ausführung erlaubt ist (unsicher!)
        
    Returns:
        CompletedProcess-Objekt
        
    Raises:
        SecureSubprocessError: Bei Ausführungsfehlern
    """
    try:
        # Validiere Eingabeparameter
        if not command or not isinstance(command, list):
            raise SecureSubprocessError("Ungültiger Befehl: Muss eine nicht-leere Liste sein")
        
        # Prüfe, ob der Befehl erlaubt ist
        if not _is_command_allowed(command[0]):
            raise SecureSubprocessError(f"Unerlaubter Befehl: {command[0]}")
        
        # Erstelle sichere Umgebung
        safe_env = _create_safe_environment(env)
        
        # Führe den Befehl aus
        result = subprocess.run(
            command,
            timeout=timeout,
            check=check,
            capture_output=capture_output,
            cwd=cwd,
            env=safe_env,
            shell=allow_shell  # Nur erlauben, wenn explizit angefordert
        )
        
        logger.debug(f"Befehl erfolgreich ausgeführt: {' '.join(command)}")
        return result
        
    except subprocess.TimeoutExpired as e:
        logger.error(f"Befehl wegen Timeout abgebrochen: {' '.join(command)}")
        raise SecureSubprocessError(f"Befehl wegen Timeout abgebrochen: {e.cmd}") from e
    except subprocess.CalledProcessError as e:
        logger.error(f"Befehl fehlgeschlagen: {' '.join(command)} - Exit-Code: {e.returncode}")
        raise SecureSubprocessError(f"Befehl fehlgeschlagen mit Exit-Code {e.returncode}: {e.cmd}") from e
    except Exception as e:
        logger.error(f"Unerwarteter Fehler bei Befehlsausführung: {e}")
        raise SecureSubprocessError(f"Unerwarteter Fehler: {e}") from e


async def secure_run_command_async(
    command: List[str],
    timeout: int = 30,
    capture_output: bool = True,
    cwd: Optional[Union[str, Path]] = None,
    env: Optional[Dict[str, str]] = None
) -> subprocess.CompletedProcess:
    """
    Führt einen Befehl asynchron sicher aus.
    
    Args:
        command: Liste von Befehlsargumenten
        timeout: Timeout in Sekunden
        capture_output: Ob Ausgabe erfasst werden soll
        cwd: Arbeitsverzeichnis
        env: Umgebungsvariablen
        
    Returns:
        CompletedProcess-Objekt
        
    Raises:
        SecureSubprocessError: Bei Ausführungsfehlern
    """
    try:
        # Validiere Eingabeparameter
        if not command or not isinstance(command, list):
            raise SecureSubprocessError("Ungültiger Befehl: Muss eine nicht-leere Liste sein")
        
        # Prüfe, ob der Befehl erlaubt ist
        if not _is_command_allowed(command[0]):
            raise SecureSubprocessError(f"Unerlaubter Befehl: {command[0]}")
        
        # Erstelle sichere Umgebung
        safe_env = _create_safe_environment(env)
        
        # Erstelle das subprocess-Objekt
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE if capture_output else None,
            stderr=asyncio.subprocess.PIPE if capture_output else None,
            cwd=cwd,
            env=safe_env
        )
        
        # Warte auf das Ergebnis mit Timeout
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            logger.error(f"Asynchroner Befehl wegen Timeout abgebrochen: {' '.join(command)}")
            raise SecureSubprocessError(f"Asynchroner Befehl wegen Timeout abgebrochen: {' '.join(command)}")
        
        # Erstelle CompletedProcess-Objekt
        result = subprocess.CompletedProcess(
            args=command,
            returncode=process.returncode,
            stdout=stdout if capture_output else None,
            stderr=stderr if capture_output else None
        )
        
        # Prüfe auf Fehler
        if process.returncode != 0:
            logger.error(f"Asynchroner Befehl fehlgeschlagen: {' '.join(command)} - Exit-Code: {process.returncode}")
            raise SecureSubprocessError(f"Asynchroner Befehl fehlgeschlagen mit Exit-Code {process.returncode}: {' '.join(command)}")
        
        logger.debug(f"Asynchroner Befehl erfolgreich ausgeführt: {' '.join(command)}")
        return result
        
    except SecureSubprocessError:
        raise
    except Exception as e:
        logger.error(f"Unerwarteter Fehler bei asynchroner Befehlsausführung: {e}")
        raise SecureSubprocessError(f"Unerwarteter Fehler: {e}") from e


def _is_command_allowed(command: str) -> bool:
    """
    Prüft, ob ein Befehl erlaubt ist.
    
    Args:
        command: Befehlsname
        
    Returns:
        True, wenn der Befehl erlaubt ist
    """
    # Liste erlaubter Befehle
    allowed_commands = {
        "msg", "osascript", "notify-send", "kdialog", "which", "where",
        "explorer", "open", "nautilus", "dolphin", "thunar", "pcmanfm",
        "gmusicbrowser", "rhythmbox-client", "which"
    }
    
    # Prüfe, ob der Befehl in der Liste erlaubter Befehle ist
    return command in allowed_commands


def _create_safe_environment(env: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """
    Erstellt eine sichere Umgebung für subprocess-Aufrufe.
    
    Args:
        env: Benutzerdefinierte Umgebungsvariablen
        
    Returns:
        Sichere Umgebungsvariablen
    """
    # Starte mit einem minimalen Satz von Umgebungsvariablen
    safe_env = {
        "PATH": os.environ.get("PATH", ""),
        "HOME": os.environ.get("HOME", ""),
        "USER": os.environ.get("USER", ""),
        "USERNAME": os.environ.get("USERNAME", ""),
        "TMPDIR": os.environ.get("TMPDIR", "/tmp"),
        "TEMP": os.environ.get("TEMP", "/tmp"),
        "TMP": os.environ.get("TMP", "/tmp"),
    }
    
    # Füge benutzerdefinierte Umgebungsvariablen hinzu, falls angegeben
    if env:
        # Filtere potenziell unsichere Variablen
        for key, value in env.items():
            # Erlaube nur bestimmte Umgebungsvariablen
            if key in ["LANG", "LC_ALL", "LC_CTYPE", "DISPLAY", "XAUTHORITY"]:
                safe_env[key] = value
    
    return safe_env


def secure_which(tool_name: str) -> Optional[str]:
    """
    Findet den Pfad zu einem Tool sicher.
    
    Args:
        tool_name: Name des Tools
        
    Returns:
        Pfad zum Tool oder None, wenn nicht gefunden
    """
    try:
        if sys.platform == "win32":
            result = secure_run_command(["where", tool_name], timeout=5)
        else:
            result = secure_run_command(["which", tool_name], timeout=5)
        
        if result.returncode == 0 and result.stdout:
            # Extrahiere den ersten Pfad
            paths = result.stdout.decode().strip().split("\n")
            return paths[0] if paths else None
        return None
    except SecureSubprocessError:
        return None