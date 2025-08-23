#!/usr/bin/env python3
"""
Version Management Script
=========================

Dieses Skript verwaltet die Versionsinformationen im gesamten Projekt.
"""

import os
import re
import sys
from typing import Dict, Optional


class VersionManager:
    """Verwaltet die Versionsinformationen im Projekt."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = project_root
        self.version_files = {
            "__init__.py": os.path.join(project_root, "src", "telegram_audio_downloader", "__init__.py"),
            "setup.py": os.path.join(project_root, "setup.py"),
            "pyproject.toml": os.path.join(project_root, "pyproject.toml")
        }
    
    def get_current_version(self) -> Optional[str]:
        """Ruft die aktuelle Version aus __init__.py ab."""
        init_path = self.version_files["__init__.py"]
        if not os.path.exists(init_path):
            return None
            
        try:
            with open(init_path, 'r', encoding='utf-8') as f:
                content = f.read()
                match = re.search(r'__version__ = "([^"]+)"', content)
                if match:
                    return match.group(1)
        except UnicodeDecodeError:
            # Fallback zu latin-1 Kodierung
            with open(init_path, 'r', encoding='latin-1') as f:
                content = f.read()
                match = re.search(r'__version__ = "([^"]+)"', content)
                if match:
                    return match.group(1)
        
        return None
    
    def set_version(self, new_version: str) -> bool:
        """Setzt die Version in allen relevanten Dateien."""
        try:
            # Aktualisiere __init__.py
            self._update_init_version(new_version)
            
            # Aktualisiere setup.py (wenn benötigt)
            self._update_setup_version(new_version)
            
            # Aktualisiere pyproject.toml
            self._update_pyproject_version(new_version)
            
            print(f"Version erfolgreich auf {new_version} aktualisiert.")
            return True
        except Exception as e:
            print(f"Fehler beim Aktualisieren der Version: {e}")
            return False
    
    def _update_init_version(self, new_version: str) -> None:
        """Aktualisiert die Version in __init__.py."""
        init_path = self.version_files["__init__.py"]
        if not os.path.exists(init_path):
            raise FileNotFoundError(f"__init__.py nicht gefunden: {init_path}")
        
        # Lese den Inhalt mit der richtigen Kodierung
        try:
            with open(init_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(init_path, 'r', encoding='latin-1') as f:
                content = f.read()
        
        # Ersetze die Versionszeile
        updated_content = re.sub(
            r'__version__ = "[^"]+"',
            f'__version__ = "{new_version}"',
            content
        )
        
        # Schreibe den Inhalt mit der richtigen Kodierung
        with open(init_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
    
    def _update_setup_version(self, new_version: str) -> None:
        """Aktualisiert die Version in setup.py."""
        setup_path = self.version_files["setup.py"]
        if not os.path.exists(setup_path):
            print("setup.py nicht gefunden, überspringe Update")
            return
        
        # Lese den Inhalt mit der richtigen Kodierung
        try:
            with open(setup_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(setup_path, 'r', encoding='latin-1') as f:
                content = f.read()
        
        # In setup.py wird die Version aus __init__.py importiert, daher muss nur sichergestellt werden,
        # dass der Import korrekt ist
        if 'from telegram_audio_downloader import __version__' not in content:
            # Füge den Import hinzu, wenn er fehlt
            updated_content = re.sub(
                r'sys\.path\.insert\(0, os\.path\.join\(os\.path\.dirname\(__file__\), \'src\'\)\)',
                'sys.path.insert(0, os.path.join(os.path.dirname(__file__), \'src\'))\n\ntry:\n    from telegram_audio_downloader import __version__\nexcept ImportError:\n    # Fallback if module import fails\n    __version__ = "1.0.0"',
                content
            )
            
            # Schreibe den Inhalt mit der richtigen Kodierung
            with open(setup_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
    
    def _update_pyproject_version(self, new_version: str) -> None:
        """Aktualisiert die Version in pyproject.toml."""
        pyproject_path = self.version_files["pyproject.toml"]
        if not os.path.exists(pyproject_path):
            print("pyproject.toml nicht gefunden, überspringe Update")
            return
        
        # Lese den Inhalt mit der richtigen Kodierung
        try:
            with open(pyproject_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(pyproject_path, 'r', encoding='latin-1') as f:
                content = f.read()
        
        # Ersetze die Versionszeile
        updated_content = re.sub(
            r'version = "[^"]+"',
            f'version = "{new_version}"',
            content
        )
        
        # Schreibe den Inhalt mit der richtigen Kodierung
        with open(pyproject_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
    
    def validate_version_format(self, version: str) -> bool:
        """Validiert das Versionsformat (Semantic Versioning)."""
        pattern = r'^\d+\.\d+\.\d+(?:-(?:alpha|beta|rc)\.\d+)?$'
        return bool(re.match(pattern, version))
    
    def get_version_info(self) -> Dict[str, str]:
        """Ruft Versionsinformationen aus allen Dateien ab."""
        versions = {}
        
        # __init__.py
        init_path = self.version_files["__init__.py"]
        if os.path.exists(init_path):
            try:
                with open(init_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    match = re.search(r'__version__ = "([^"]+)"', content)
                    if match:
                        versions["__init__.py"] = match.group(1)
            except UnicodeDecodeError:
                with open(init_path, 'r', encoding='latin-1') as f:
                    content = f.read()
                    match = re.search(r'__version__ = "([^"]+)"', content)
                    if match:
                        versions["__init__.py"] = match.group(1)
        
        # setup.py
        setup_path = self.version_files["setup.py"]
        if os.path.exists(setup_path):
            try:
                with open(setup_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # In setup.py wird die Version aus __init__.py importiert
                    versions["setup.py"] = versions.get("__init__.py", "unknown")
            except UnicodeDecodeError:
                with open(setup_path, 'r', encoding='latin-1') as f:
                    content = f.read()
                    # In setup.py wird die Version aus __init__.py importiert
                    versions["setup.py"] = versions.get("__init__.py", "unknown")
        
        # pyproject.toml
        pyproject_path = self.version_files["pyproject.toml"]
        if os.path.exists(pyproject_path):
            try:
                with open(pyproject_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    match = re.search(r'version = "([^"]+)"', content)
                    if match:
                        versions["pyproject.toml"] = match.group(1)
            except UnicodeDecodeError:
                with open(pyproject_path, 'r', encoding='latin-1') as f:
                    content = f.read()
                    match = re.search(r'version = "([^"]+)"', content)
                    if match:
                        versions["pyproject.toml"] = match.group(1)
        
        return versions


def main():
    """Hauptfunktion des Skripts."""
    if len(sys.argv) < 2:
        print("Verwendung:")
        print("  python version_manager.py get           - Zeigt die aktuelle Version an")
        print("  python version_manager.py set <version> - Setzt eine neue Version")
        print("  python version_manager.py validate <version> - Validiert ein Versionsformat")
        print("  python version_manager.py info          - Zeigt Versionsinformationen an")
        return
    
    manager = VersionManager()
    
    command = sys.argv[1]
    
    if command == "get":
        version = manager.get_current_version()
        if version:
            print(f"Aktuelle Version: {version}")
        else:
            print("Konnte die aktuelle Version nicht ermitteln")
    elif command == "set" and len(sys.argv) >= 3:
        new_version = sys.argv[2]
        if manager.validate_version_format(new_version):
            manager.set_version(new_version)
        else:
            print(f"Ungültiges Versionsformat: {new_version}")
            print("Bitte verwenden Sie Semantic Versioning (z.B. 1.2.3 oder 1.2.3-beta.1)")
    elif command == "validate" and len(sys.argv) >= 3:
        version = sys.argv[2]
        if manager.validate_version_format(version):
            print(f"Version {version} ist gültig")
        else:
            print(f"Version {version} ist ungültig")
    elif command == "info":
        versions = manager.get_version_info()
        print("Versionsinformationen:")
        for file, version in versions.items():
            print(f"  {file}: {version}")
    else:
        print("Ungültiger Befehl oder fehlende Argumente.")
        print("Verwendung:")
        print("  python version_manager.py get           - Zeigt die aktuelle Version an")
        print("  python version_manager.py set <version> - Setzt eine neue Version")
        print("  python version_manager.py validate <version> - Validiert ein Versionsformat")
        print("  python version_manager.py info          - Zeigt Versionsinformationen an")


if __name__ == "__main__":
    main()