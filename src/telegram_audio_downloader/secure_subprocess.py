"""
Sichere Subprocess-Funktionen für den Telegram Audio Downloader.

Bietet sichere Wrapper für subprocess-Aufrufe mit zusätzlichen Sicherheitsmaßnahmen:
- Validierung von Eingabeparametern
- Beschränkung der Ausführungszeit
- Verhinderung von Shell-Injection
- Sichere Handhabung von Umgebungsvariablen
"""

import subprocess  # nosec B404 - Subprocess wird sicher verwendet mit Validierung und Timeout
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
    """Error in secure subprocess operations."""
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
    Executes a command securely.
    
    Args:
        command: List of command arguments
        timeout: Timeout in seconds
        check: Whether to throw an exception on errors
        capture_output: Whether to capture output
        cwd: Working directory
        env: Environment variables
        allow_shell: Whether shell execution is allowed (unsafe!)
        
    Returns:
        CompletedProcess object
        
    Raises:
        SecureSubprocessError: On execution errors
    """
    try:
        # Validiere Eingabeparameter
        if not command or not isinstance(command, list):
            raise SecureSubprocessError("Invalid command: Must be a non-empty list")
        
        # Check if the command is allowed
        if not _is_command_allowed(command[0]):
            raise SecureSubprocessError(f"Unauthorized command: {command[0]}")
        
        # Create secure environment
        safe_env = _create_safe_environment(env)
        
        # Execute the command
        result = subprocess.run(
            command,
            timeout=timeout,
            check=check,
            capture_output=capture_output,
            cwd=cwd,
            env=safe_env,
            shell=allow_shell  # Only allow if explicitly requested  # nosec B602
        )
        
        logger.debug(f"Command executed successfully: {' '.join(command)}")
        return result
        
    except subprocess.TimeoutExpired as e:
        logger.error(f"Command cancelled due to timeout: {' '.join(command)}")
        raise SecureSubprocessError(f"Command cancelled due to timeout: {e.cmd}") from e
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {' '.join(command)} - Exit code: {e.returncode}")
        raise SecureSubprocessError(f"Command failed with exit code {e.returncode}: {e.cmd}") from e
    except Exception as e:
        logger.error(f"Unexpected error during command execution: {e}")
        raise SecureSubprocessError(f"Unexpected error: {e}") from e


async def secure_run_command_async(
    command: List[str],
    timeout: int = 30,
    capture_output: bool = True,
    cwd: Optional[Union[str, Path]] = None,
    env: Optional[Dict[str, str]] = None
) -> subprocess.CompletedProcess:
    """
    Executes a command securely asynchronously.
    
    Args:
        command: List of command arguments
        timeout: Timeout in seconds
        capture_output: Whether to capture output
        cwd: Working directory
        env: Environment variables
        
    Returns:
        CompletedProcess object
        
    Raises:
        SecureSubprocessError: On execution errors
    """
    try:
        # Validiere Eingabeparameter
        if not command or not isinstance(command, list):
            raise SecureSubprocessError("Invalid command: Must be a non-empty list")
        
        # Check if the command is allowed
        if not _is_command_allowed(command[0]):
            raise SecureSubprocessError(f"Unauthorized command: {command[0]}")
        
        # Create secure environment
        safe_env = _create_safe_environment(env)
        
        # Create subprocess object
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE if capture_output else None,
            stderr=asyncio.subprocess.PIPE if capture_output else None,
            cwd=cwd,
            env=safe_env
        )
        
        # Wait for result with timeout
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            logger.error(f"Asynchronous command cancelled due to timeout: {' '.join(command)}")
            raise SecureSubprocessError(f"Asynchronous command cancelled due to timeout: {' '.join(command)}")
        
        # Create CompletedProcess object
        result = subprocess.CompletedProcess(
            args=command,
            returncode=process.returncode,
            stdout=stdout if capture_output else None,
            stderr=stderr if capture_output else None
        )
        
        # Check for errors
        if process.returncode != 0:
            logger.error(f"Asynchronous command failed: {' '.join(command)} - Exit code: {process.returncode}")
            raise SecureSubprocessError(f"Asynchronous command failed with exit code {process.returncode}: {' '.join(command)}")
        
        logger.debug(f"Asynchronous command executed successfully: {' '.join(command)}")
        return result
        
    except SecureSubprocessError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during asynchronous command execution: {e}")
        raise SecureSubprocessError(f"Unexpected error: {e}") from e


def _is_command_allowed(command: str) -> bool:
    """
    Checks if a command is allowed.
    
    Args:
        command: Command name
        
    Returns:
        True if the command is allowed
    """
    # List of allowed commands
    allowed_commands = {
        "msg", "osascript", "notify-send", "kdialog", "which", "where",
        "explorer", "open", "nautilus", "dolphin", "thunar", "pcmanfm",
        "gmusicbrowser", "rhythmbox-client", "which"
    }
    
    # Check if the command is in the list of allowed commands
    return command in allowed_commands


def _create_safe_environment(env: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """
    Creates a secure environment for subprocess calls.
    
    Args:
        env: Custom environment variables
        
    Returns:
        Secure environment variables
    """
    # Start with a minimal set of environment variables
    safe_env = {
        "PATH": os.environ.get("PATH", ""),
        "HOME": os.environ.get("HOME", ""),
        "USER": os.environ.get("USER", ""),
        "USERNAME": os.environ.get("USERNAME", ""),
        "TMPDIR": os.environ.get("TMPDIR", "/tmp"),  # nosec B108
        "TEMP": os.environ.get("TEMP", "/tmp"),  # nosec B108
        "TMP": os.environ.get("TMP", "/tmp"),  # nosec B108
    }
    
    # Add custom environment variables if provided
    if env:
        # Filter potentially unsafe variables
        for key, value in env.items():
            # Only allow certain environment variables
            if key in ["LANG", "LC_ALL", "LC_CTYPE", "DISPLAY", "XAUTHORITY"]:
                safe_env[key] = value
    
    return safe_env


def secure_which(tool_name: str) -> Optional[str]:
    """
    Finds the path to a tool securely.
    
    Args:
        tool_name: Tool name
        
    Returns:
        Path to the tool or None if not found
    """
    try:
        if sys.platform == "win32":
            result = secure_run_command(["where", tool_name], timeout=5)
        else:
            result = secure_run_command(["which", tool_name], timeout=5)
        
        if result.returncode == 0 and result.stdout:
            # Extract the first path
            paths = result.stdout.decode().strip().split("\n")
            return paths[0] if paths else None
        return None
    except SecureSubprocessError:
        return None