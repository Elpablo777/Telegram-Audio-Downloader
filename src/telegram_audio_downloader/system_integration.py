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
import subprocess
import platform
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass

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
            subprocess.run(
                ["which", tool_name] if self.platform != "windows" else ["where", tool_name],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
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
                subprocess.run(cmd, check=True, capture_output=True)
                return True
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
            subprocess.run(cmd, check=True, capture_output=True)
            return True
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
            subprocess.run(cmd, check=True, capture_output=True)
            return True
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
                str(notification.timeout // 1000)
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            return True
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
                subprocess.run(cmd, check=True, capture_output=True)
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
        Zeigt eine Datei oder ein Verzeichnis im Dateimanager an.
        
        Args:
            path: Der anzuzeigende Pfad
            
        Returns:
            True, wenn der Dateimanager geöffnet wurde, False sonst
        """
        try:
            path = path.resolve()
            
            if self.platform == "windows":
                # Windows Explorer
                subprocess.run(["explorer", "/select,", str(path)], check=True)
            elif self.platform == "darwin":  # macOS
                # Finder
                subprocess.run(["open", "-R", str(path)], check=True)
            else:  # Linux
                # Versuche verschiedene Dateimanager
                file_managers = ["xdg-open", "nautilus", "dolphin", "thunar"]
                for fm in file_managers:
                    if self._is_tool_available(fm):
                        if fm == "nautilus":
                            subprocess.run([fm, "--select", str(path)], check=True)
                        else:
                            subprocess.run([fm, str(path.parent)], check=True)
                        return True
                return False
            
            return True
        except Exception as e:
            logger.warning(f"Fehler beim Öffnen im Dateimanager: {e}")
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
            subprocess.run(
                ["which", tool_name] if self.platform != "windows" else ["where", tool_name],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
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
        Fügt eine Datei zur Medienbibliothek hinzu.
        
        Args:
            file_path: Pfad zur Datei
            
        Returns:
            True, wenn die Datei hinzugefügt wurde, False sonst
        """
        try:
            if not file_path.exists():
                logger.warning(f"Datei {file_path} existiert nicht")
                return False
            
            if self.platform == "windows":
                return self._add_to_windows_media_library(file_path)
            elif self.platform == "darwin":  # macOS
                return self._add_to_macos_media_library(file_path)
            else:  # Linux
                return self._add_to_linux_media_library(file_path)
        except Exception as e:
            logger.warning(f"Fehler beim Hinzufügen zur Medienbibliothek: {e}")
            return False
    
    def _add_to_windows_media_library(self, file_path: Path) -> bool:
        """
        Fügt eine Datei zur Windows-Medienbibliothek hinzu.
        
        Args:
            file_path: Pfad zur Datei
            
        Returns:
            True, wenn die Datei hinzugefügt wurde, False sonst
        """
        try:
            # Windows Media Player Library aktualisieren
            # Dies ist eine vereinfachte Implementierung
            import ctypes
            from ctypes import wintypes
            
            # Versuche, die Datei in die Medienbibliothek zu integrieren
            # Dies erfordert möglicherweise zusätzliche Berechtigungen
            shell = ctypes.windll.shell32
            result = shell.SHChangeNotify(0x08000000, 0, str(file_path).encode('utf-16le'), None)
            return True
        except Exception as e:
            logger.warning(f"Fehler beim Hinzufügen zur Windows-Medienbibliothek: {e}")
            return False
    
    def _add_to_macos_media_library(self, file_path: Path) -> bool:
        """
        Fügt eine Datei zur macOS-Medienbibliothek hinzu.
        
        Args:
            file_path: Pfad zur Datei
            
        Returns:
            True, wenn die Datei hinzugefügt wurde, False sonst
        """
        try:
            # iTunes/Music Library aktualisieren
            cmd = ["osascript", "-e", f'tell application "Music" to add POSIX file "{file_path}"']
            subprocess.run(cmd, check=True, capture_output=True)
            return True
        except Exception as e:
            logger.warning(f"Fehler beim Hinzufügen zur macOS-Medienbibliothek: {e}")
            return False
    
    def _add_to_linux_media_library(self, file_path: Path) -> bool:
        """
        Fügt eine Datei zur Linux-Medienbibliothek hinzu.
        
        Args:
            file_path: Pfad zur Datei
            
        Returns:
            True, wenn die Datei hinzugefügt wurde, False sonst
        """
        try:
            # Versuche, gmusicbrowser oder rhythmbox zu verwenden
            if self._is_tool_available("gmusicbrowser"):
                cmd = ["gmusicbrowser", "- enqueue", str(file_path)]
                subprocess.run(cmd, check=True, capture_output=True)
                return True
            elif self._is_tool_available("rhythmbox-client"):
                cmd = ["rhythmbox-client", "--enqueue", str(file_path)]
                subprocess.run(cmd, check=True, capture_output=True)
                return True
            else:
                # Fallback: Datei in Musikordner kopieren
                music_dir = Path.home() / "Music"
                if music_dir.exists():
                    import shutil
                    shutil.copy2(file_path, music_dir)
                    return True
                return False
        except Exception as e:
            logger.warning(f"Fehler beim Hinzufügen zur Linux-Medienbibliothek: {e}")
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
            subprocess.run(["which", tool_name], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
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