"""
Erweiterte Systemintegration für den Telegram Audio Downloader.

Bietet nahtlose Integration mit:
- Systembenachrichtigungen
- Shell-Integration
- Dateimanager-Integration
- Medienbibliothek-Integration
"""

import os
import sys
import platform
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass

# Verwende sichere Subprocess-Funktionen
from .secure_subprocess import secure_run_command, secure_which
from .logging_config import get_logger
from .error_handling import handle_error, SystemIntegrationError

logger = get_logger(__name__)

@dataclass
class SystemNotification:
    """Eine Systembenachrichtigung."""
    title: str
    message: str
    icon: Optional[str] = None
    timeout: int = 5000  # ms

class SystemNotifier:
    """Verwaltung von Systembenachrichtigungen."""
    
    def __init__(self):
        """Initialisiert den Systembenachrichtigungsmanager."""
        self.platform = platform.system().lower()
        self.notification_backend = self._detect_notification_backend()
    
    def _detect_notification_backend(self) -> str:
        """
        Erkennt das verfügbare Benachrichtigungs-Backend.
        
        Returns:
            Name des Benachrichtigungs-Backends
        """
        if self.platform == "windows":
            return "windows"
        elif self.platform == "darwin":  # macOS
            if self._is_tool_available("osascript"):
                return "macos"
            else:
                return "none"
        else:  # Linux
            if self._is_tool_available("notify-send"):
                return "linux"
            elif self._is_tool_available("kdialog"):
                return "kdialog"
            else:
                return "none"
    
    def _is_tool_available(self, tool_name: str) -> bool:
        """
        Prüft, ob ein Tool verfügbar ist.
        
        Args:
            tool_name: Name des Tools
            
        Returns:
            True, wenn das Tool verfügbar ist, False sonst
        """
        try:
            result = secure_which(tool_name)
            return result is not None
        except Exception:
            return False
    
    def send_notification(self, notification: SystemNotification) -> bool:
        """
        Sendet eine Systembenachrichtigung.
        
        Args:
            notification: Die zu sendende Benachrichtigung
            
        Returns:
            True, wenn die Benachrichtigung gesendet wurde, False sonst
        """
        try:
            if self.notification_backend == "windows":
                return self._send_windows_notification(notification)
            elif self.notification_backend == "macos":
                return self._send_macos_notification(notification)
            elif self.notification_backend == "linux":
                return self._send_linux_notification(notification)
            elif self.notification_backend == "kdialog":
                return self._send_kdialog_notification(notification)
            else:
                logger.debug("Kein Benachrichtigungs-Backend verfügbar")
                return False
        except Exception as e:
            logger.warning(f"Fehler beim Senden der Benachrichtigung: {e}")
            return False
    
    def _send_windows_notification(self, notification: SystemNotification) -> bool:
        """
        Sendet eine Windows-Benachrichtigung.
        
        Args:
            notification: Die zu sendende Benachrichtigung
            
        Returns:
            True, wenn die Benachrichtigung gesendet wurde, False sonst
        """
        try:
            # Für Windows verwenden wir plyer oder win10toast
            try:
                from plyer import notification as plyer_notification
                plyer_notification.notify(
                    title=notification.title,
                    message=notification.message,
                    app_name="Telegram Audio Downloader",
                    timeout=notification.timeout // 1000
                )
                return True
            except ImportError:
                # Fallback auf Windows PowerShell
                cmd = [
                    "powershell", "-Command",
                    f"New-BurntToastNotification -Text '{notification.title}', '{notification.message}'"
                ]
                result = secure_run_command(cmd, timeout=10)
                return result.returncode == 0
        except Exception as e:
            logger.warning(f"Fehler beim Senden der Windows-Benachrichtigung: {e}")
            return False
    
    def _send_macos_notification(self, notification: SystemNotification) -> bool:
        """
        Sendet eine macOS-Benachrichtigung.
        
        Args:
            notification: Die zu sendende Benachrichtigung
            
        Returns:
            True, wenn die Benachrichtigung gesendet wurde, False sonst
        """
        try:
            cmd = [
                "osascript", "-e",
                f'display notification "{notification.message}" with title "{notification.title}"'
            ]
            result = secure_run_command(cmd, timeout=10)
            return result.returncode == 0
        except Exception as e:
            logger.warning(f"Fehler beim Senden der macOS-Benachrichtigung: {e}")
            return False
    
    def _send_linux_notification(self, notification: SystemNotification) -> bool:
        """
        Sendet eine Linux-Benachrichtigung über notify-send.
        
        Args:
            notification: Die zu sendende Benachrichtigung
            
        Returns:
            True, wenn die Benachrichtigung gesendet wurde, False sonst
        """
        try:
            cmd = [
                "notify-send",
                notification.title,
                notification.message,
                f"--expire-time={notification.timeout}"
            ]
            if notification.icon:
                cmd.extend(["--icon", notification.icon])
            result = secure_run_command(cmd, timeout=10)
            return result.returncode == 0
        except Exception as e:
            logger.warning(f"Fehler beim Senden der Linux-Benachrichtigung: {e}")
            return False
    
    def _send_kdialog_notification(self, notification: SystemNotification) -> bool:
        """
        Sendet eine Linux-Benachrichtigung über kdialog.
        
        Args:
            notification: Die zu sendende Benachrichtigung
            
        Returns:
            True, wenn die Benachrichtigung gesendet wurde, False sonst
        """
        try:
            cmd = [
                "kdialog",
                "--title", notification.title,
                "--passivepopup", notification.message,
                str(notification.timeout // 1000)  # kdialog erwartet Sekunden
            ]
            result = secure_run_command(cmd, timeout=10)
            return result.returncode == 0
        except Exception as e:
            logger.warning(f"Fehler beim Senden der kdialog-Benachrichtigung: {e}")
            return False

class ShellIntegration:
    """Integration mit der Shell."""
    
    def __init__(self):
        """Initialisiert die Shell-Integration."""
        self.shell = self._detect_shell()
    
    def _detect_shell(self) -> str:
        """
        Erkennt die aktuelle Shell.
        
        Returns:
            Name der Shell
        """
        shell = os.environ.get("SHELL", "")
        if "bash" in shell:
            return "bash"
        elif "zsh" in shell:
            return "zsh"
        elif "fish" in shell:
            return "fish"
        elif sys.platform == "win32":
            return "powershell"
        else:
            return "unknown"
    
    def add_to_path(self, path: Path) -> bool:
        """
        Fügt einen Pfad zur PATH-Variable hinzu.
        
        Args:
            path: Der hinzuzufügende Pfad
            
        Returns:
            True, wenn der Pfad hinzugefügt wurde, False sonst
        """
        try:
            path_str = str(path.resolve())
            
            if sys.platform == "win32":
                # Windows PowerShell
                cmd = [
                    "powershell", "-Command",
                    f"[Environment]::SetEnvironmentVariable('PATH', [Environment]::GetEnvironmentVariable('PATH', 'User') + ';{path_str}', 'User')"
                ]
                secure_run_command(cmd, check=True)
            else:
                # Unix-Systeme
                shell_config = self._get_shell_config_file()
                if shell_config:
                    with open(shell_config, "a") as f:
                        f.write(f"\n# Telegram Audio Downloader\nexport PATH=\"$PATH:{path_str}\"\n")
                    return True
                else:
                    return False
            
            return True
        except Exception as e:
            logger.warning(f"Fehler beim Hinzufügen zum PATH: {e}")
            return False
    
    def _get_shell_config_file(self) -> Optional[Path]:
        """
        Gibt die Konfigurationsdatei der aktuellen Shell zurück.
        
        Returns:
            Pfad zur Shell-Konfigurationsdatei oder None
        """
        home = Path.home()
        
        if self.shell == "bash":
            return home / ".bashrc"
        elif self.shell == "zsh":
            return home / ".zshrc"
        elif self.shell == "fish":
            return home / ".config" / "fish" / "config.fish"
        else:
            return None
    
    def create_alias(self, alias_name: str, command: str) -> bool:
        """
        Erstellt einen Shell-Alias.
        
        Args:
            alias_name: Name des Aliases
            command: Das auszuführende Kommando
            
        Returns:
            True, wenn der Alias erstellt wurde, False sonst
        """
        try:
            if sys.platform == "win32":
                # PowerShell
                profile_path = Path.home() / "Documents" / "WindowsPowerShell" / "Microsoft.PowerShell_profile.ps1"
                profile_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(profile_path, "a") as f:
                    f.write(f"\n# Telegram Audio Downloader Alias\nfunction {alias_name} {{ {command} $args }}\n")
            else:
                # Unix-Systeme
                shell_config = self._get_shell_config_file()
                if shell_config:
                    with open(shell_config, "a") as f:
                        f.write(f"\n# Telegram Audio Downloader Alias\nalias {alias_name}='{command}'\n")
                    return True
                else:
                    return False
            
            return True
        except Exception as e:
            logger.warning(f"Fehler beim Erstellen des Aliases: {e}")
            return False

class FileManagerIntegration:
    """Integration mit Dateimanagern."""
    
    def __init__(self):
        """Initialisiert die Dateimanager-Integration."""
        self.platform = platform.system().lower()
    
    def show_in_file_manager(self, path: Path) -> bool:
        """
        Öffnet einen Pfad im Standard-Dateimanager.
        
        Args:
            path: Pfad zum Ordner oder zur Datei
            
        Returns:
            True, wenn erfolgreich, False sonst
        """
        try:
            if self.platform == "windows":
                # Windows Explorer
                cmd = ["explorer", "/select,", str(path)]
                result = secure_run_command(cmd, timeout=10)
                return result.returncode == 0
            elif self.platform == "darwin":  # macOS
                # Finder
                cmd = ["open", "-R", str(path)]
                result = secure_run_command(cmd, timeout=10)
                return result.returncode == 0
            else:  # Linux
                # Versuche verschiedene Dateimanager
                file_managers = ["nautilus", "dolphin", "thunar", "pcmanfm"]
                for fm in file_managers:
                    if secure_which(fm):
                        try:
                            if fm == "nautilus":
                                cmd = [fm, "--select", str(path)]
                            else:
                                cmd = [fm, str(path.parent)]
                            result = secure_run_command(cmd, timeout=10)
                            if result.returncode == 0:
                                return True
                        except Exception:
                            continue
                return False
        except Exception as e:
            logger.error(f"Fehler beim Öffnen im Dateimanager: {e}")
            return False
    
    def _is_tool_available(self, tool_name: str) -> bool:
        """
        Prüft, ob ein Tool verfügbar ist.
        
        Args:
            tool_name: Name des Tools
            
        Returns:
            True, wenn das Tool verfügbar ist, False sonst
        """
        try:
            # Verwende secure_which für die Tool-Verfügbarkeitsprüfung
            return secure_which(tool_name) is not None
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

class MediaLibraryIntegration:
    """Integration mit Medienbibliotheken."""
    
    def __init__(self):
        """Initialisiert die Medienbibliothek-Integration."""
        self.platform = platform.system().lower()
    
    def add_to_media_library(self, file_path: Path) -> bool:
        """
        Fügt eine Datei zur Standard-Medienbibliothek hinzu.
        
        Args:
            file_path: Pfad zur Datei
            
        Returns:
            True, wenn erfolgreich, False sonst
        """
        try:
            if self.platform == "darwin":  # macOS
                cmd = ["osascript", "-e", f'tell application "Music" to add POSIX file "{file_path}"']
                result = secure_run_command(cmd, timeout=30)
                return result.returncode == 0
            elif self.platform == "windows":  # Windows
                # Versuche verschiedene Player
                players = ["gmusicbrowser", "rhythmbox-client"]
                for player in players:
                    if secure_which(player):
                        try:
                            if player == "gmusicbrowser":
                                cmd = ["gmusicbrowser", "- enqueue", str(file_path)]
                            else:  # rhythmbox-client
                                cmd = ["rhythmbox-client", "--enqueue", str(file_path)]
                            result = secure_run_command(cmd, timeout=10)
                            if result.returncode == 0:
                                return True
                        except Exception:
                            continue
                return False
            else:  # Linux
                # Für Linux verwenden wir einfach den Dateimanager
                return self.show_in_file_manager(file_path)
        except Exception as e:
            logger.error(f"Fehler beim Hinzufügen zur Medienbibliothek: {e}")
            return False

# Globale Instanzen
_system_notifier: Optional[SystemNotifier] = None
_shell_integration: Optional[ShellIntegration] = None
_file_manager_integration: Optional[FileManagerIntegration] = None
_media_library_integration: Optional[MediaLibraryIntegration] = None

def get_system_notifier() -> SystemNotifier:
    """
    Gibt die globale Instanz des Systembenachrichtigungsmanagers zurück.
    
    Returns:
        Instanz von SystemNotifier
    """
    global _system_notifier
    if _system_notifier is None:
        _system_notifier = SystemNotifier()
    return _system_notifier

def get_shell_integration() -> ShellIntegration:
    """
    Gibt die globale Instanz der Shell-Integration zurück.
    
    Returns:
        Instanz von ShellIntegration
    """
    global _shell_integration
    if _shell_integration is None:
        _shell_integration = ShellIntegration()
    return _shell_integration

def get_file_manager_integration() -> FileManagerIntegration:
    """
    Gibt die globale Instanz der Dateimanager-Integration zurück.
    
    Returns:
        Instanz von FileManagerIntegration
    """
    global _file_manager_integration
    if _file_manager_integration is None:
        _file_manager_integration = FileManagerIntegration()
    return _file_manager_integration

def get_media_library_integration() -> MediaLibraryIntegration:
    """
    Gibt die globale Instanz der Medienbibliothek-Integration zurück.
    
    Returns:
        Instanz von MediaLibraryIntegration
    """
    global _media_library_integration
    if _media_library_integration is None:
        _media_library_integration = MediaLibraryIntegration()
    return _media_library_integration

# Hilfsfunktionen für die Verwendung außerhalb der Klassen
def send_system_notification(title: str, message: str, icon: Optional[str] = None, timeout: int = 5000) -> bool:
    """
    Sendet eine Systembenachrichtigung.
    
    Args:
        title: Titel der Benachrichtigung
        message: Nachrichtentext
        icon: Pfad zum Icon (optional)
        timeout: Timeout in ms (optional)
        
    Returns:
        True, wenn die Benachrichtigung gesendet wurde, False sonst
    """
    notification = SystemNotification(title=title, message=message, icon=icon, timeout=timeout)
    notifier = get_system_notifier()
    return notifier.send_notification(notification)

def add_to_system_path(path: Path) -> bool:
    """
    Fügt einen Pfad zur System-PATH-Variable hinzu.
    
    Args:
        path: Der hinzuzufügende Pfad
        
    Returns:
        True, wenn der Pfad hinzugefügt wurde, False sonst
    """
    shell_integration = get_shell_integration()
    return shell_integration.add_to_path(path)

def create_shell_alias(alias_name: str, command: str) -> bool:
    """
    Erstellt einen Shell-Alias.
    
    Args:
        alias_name: Name des Aliases
        command: Das auszuführende Kommando
        
    Returns:
        True, wenn der Alias erstellt wurde, False sonst
    """
    shell_integration = get_shell_integration()
    return shell_integration.create_alias(alias_name, command)

def show_in_default_file_manager(path: Path) -> bool:
    """
    Zeigt eine Datei oder ein Verzeichnis im Standard-Dateimanager an.
    
    Args:
        path: Der anzuzeigende Pfad
        
    Returns:
        True, wenn der Dateimanager geöffnet wurde, False sonst
    """
    file_manager = get_file_manager_integration()
    return file_manager.show_in_file_manager(path)

def add_to_default_media_library(file_path: Path) -> bool:
    """
    Fügt eine Datei zur Standard-Medienbibliothek hinzu.
    
    Args:
        file_path: Pfad zur Datei
        
    Returns:
        True, wenn die Datei hinzugefügt wurde, False sonst
    """
    media_library = get_media_library_integration()
    return media_library.add_to_media_library(file_path)