#!/usr/bin/env python3
"""
Changelog Update Script
=======================

Dieses Skript hilft bei der Aktualisierung des Changelogs gemäß den Keep a Changelog Richtlinien.
"""

import os
import sys
import re
from datetime import datetime
from typing import List, Dict, Optional


class ChangelogUpdater:
    """Hilft bei der Aktualisierung des Changelogs."""
    
    def __init__(self, changelog_path: str = "CHANGELOG.md"):
        self.changelog_path = changelog_path
        self.version_pattern = re.compile(r'^## \[(\d+\.\d+\.\d+(?:-[a-zA-Z0-9]+)?)\]')
        
    def read_changelog(self) -> List[str]:
        """Liest die Changelog-Datei."""
        if not os.path.exists(self.changelog_path):
            raise FileNotFoundError(f"Changelog-Datei {self.changelog_path} nicht gefunden")
            
        try:
            with open(self.changelog_path, 'r', encoding='utf-8') as f:
                return f.readlines()
        except UnicodeDecodeError:
            # Fallback zu latin-1 Kodierung
            with open(self.changelog_path, 'r', encoding='latin-1') as f:
                return f.readlines()
    
    def write_changelog(self, lines: List[str]) -> None:
        """Schreibt die Changelog-Datei."""
        with open(self.changelog_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
    
    def get_unreleased_changes(self) -> List[str]:
        """Extrahiert Änderungen aus dem [Unreleased] Abschnitt."""
        lines = self.read_changelog()
        unreleased_content = []
        in_unreleased = False
        
        for line in lines:
            if line.startswith('## [Unreleased]'):
                in_unreleased = True
                continue
            elif line.startswith('## [') and in_unreleased:
                break
            elif in_unreleased:
                unreleased_content.append(line)
                
        return [line for line in unreleased_content if line.strip()]
    
    def get_existing_versions(self) -> List[str]:
        """Extrahiert alle existierenden Versionen."""
        lines = self.read_changelog()
        versions = []
        
        for line in lines:
            match = self.version_pattern.match(line.strip())
            if match:
                versions.append(match.group(1))
                
        return versions
    
    def create_new_version_section(self, version: str, changes: List[str]) -> List[str]:
        """Erstellt einen neuen Versionsabschnitt."""
        today = datetime.now().strftime('%Y-%m-%d')
        section = [
            f"## [{version}] - {today}\n",
            "\n"
        ]
        
        # Gruppiere Änderungen nach Typ
        change_groups = {
            'Hinzugefügt': [],
            'Geändert': [],
            'Veraltet': [],
            'Entfernt': [],
            'Behoben': [],
            'Sicherheit': []
        }
        
        current_group = None
        for change in changes:
            stripped = change.strip()
            if stripped.startswith('### '):
                group_name = stripped[4:]
                if group_name in change_groups:
                    current_group = group_name
                continue
            elif current_group and stripped:
                change_groups[current_group].append(change)
        
        # Füge nicht-leere Gruppen hinzu
        for group_name, group_changes in change_groups.items():
            if group_changes:
                section.append(f"### {group_name}\n")
                section.extend(group_changes)
                section.append("\n")
        
        return section
    
    def update_changelog_for_release(self, new_version: str) -> None:
        """Aktualisiert das Changelog für ein neues Release."""
        lines = self.read_changelog()
        changes = self.get_unreleased_changes()
        
        if not changes:
            print("Keine Änderungen im [Unreleased] Abschnitt gefunden.")
            return
        
        # Erstelle neuen Versionsabschnitt
        new_section = self.create_new_version_section(new_version, changes)
        
        # Finde die Position für den neuen Abschnitt
        insert_pos = -1
        for i, line in enumerate(lines):
            if line.startswith('## [Unreleased]'):
                insert_pos = i + 1
                break
        
        if insert_pos == -1:
            raise ValueError("Konnte [Unreleased] Abschnitt nicht finden")
        
        # Füge den neuen Abschnitt hinzu
        lines[insert_pos:insert_pos] = new_section
        
        # Leere den [Unreleased] Abschnitt (behalte nur die Überschrift und leere Gruppen)
        unreleased_start = insert_pos - 1
        next_section = -1
        for i in range(unreleased_start + 1, len(lines)):
            if lines[i].startswith('## ['):
                next_section = i
                break
        
        if next_section != -1:
            # Behalte nur die Gruppenüberschriften im [Unreleased] Abschnitt
            clean_unreleased = [
                '## [Unreleased]\n',
                '\n',
                '### Hinzugefügt\n',
                '\n',
                '### Geändert\n',
                '\n',
                '### Veraltet\n',
                '\n',
                '### Entfernt\n',
                '\n',
                '### Behoben\n',
                '\n',
                '### Sicherheit\n',
                '\n',
                '\n'
            ]
            lines[unreleased_start + 1:next_section] = clean_unreleased
        
        # Aktualisiere Versionslinks
        self.update_version_links(lines, new_version)
        
        # Schreibe die aktualisierte Changelog
        self.write_changelog(lines)
        print(f"Changelog erfolgreich für Version {new_version} aktualisiert.")
    
    def update_version_links(self, lines: List[str], new_version: str) -> None:
        """Aktualisiert die Versionslinks am Ende der Changelog."""
        # Finde das Ende der Datei
        link_section_start = -1
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].startswith('['):
                link_section_start = i
                break
        
        if link_section_start == -1:
            # Füge am Ende der Datei hinzu
            lines.extend(['\n', f'[Unreleased]: https://github.com/Elpablo777/Telegram-Audio-Downloader/compare/v{new_version}...HEAD\n'])
            lines.extend([f'[{new_version}]: https://github.com/Elpablo777/Telegram-Audio-Downloader/releases/tag/v{new_version}\n'])
        else:
            # Aktualisiere bestehende Links
            unreleased_link_idx = -1
            version_link_idx = -1
            
            for i in range(link_section_start, len(lines)):
                if lines[i].startswith('[Unreleased]:'):
                    unreleased_link_idx = i
                elif lines[i].startswith(f'[{new_version}]:'):
                    version_link_idx = i
            
            # Aktualisiere den Unreleased-Link
            if unreleased_link_idx != -1:
                lines[unreleased_link_idx] = f'[Unreleased]: https://github.com/Elpablo777/Telegram-Audio-Downloader/compare/v{new_version}...HEAD\n'
            
            # Füge den neuen Versionslink hinzu, wenn er nicht existiert
            if version_link_idx == -1:
                lines.insert(unreleased_link_idx + 1, f'[{new_version}]: https://github.com/Elpablo777/Telegram-Audio-Downloader/releases/tag/v{new_version}\n')
    
    def add_unreleased_change(self, change_type: str, change_description: str) -> None:
        """Fügt eine Änderung zum [Unreleased] Abschnitt hinzu."""
        lines = self.read_changelog()
        
        # Finde den richtigen Abschnitt
        section_start = -1
        for i, line in enumerate(lines):
            if line.startswith(f'### {change_type}'):
                section_start = i
                break
        
        # Wenn der Abschnitt nicht gefunden wurde, füge ihn hinzu
        if section_start == -1:
            # Finde das Ende des [Unreleased] Abschnitts
            unreleased_start = -1
            unreleased_end = len(lines)
            
            for i, line in enumerate(lines):
                if line.startswith('## [Unreleased]'):
                    unreleased_start = i
                elif line.startswith('## [') and unreleased_start != -1 and i > unreleased_start:
                    unreleased_end = i
                    break
            
            if unreleased_start != -1:
                # Füge den neuen Abschnitt hinzu
                lines.insert(unreleased_end, f'### {change_type}\n')
                lines.insert(unreleased_end + 1, '\n')
                section_start = unreleased_end + 1
        
        # Füge die neue Änderung hinzu
        if section_start != -1:
            # Finde das Ende des Abschnitts
            section_end = section_start + 1
            for i in range(section_start + 1, len(lines)):
                if lines[i].startswith('### ') or lines[i].startswith('## '):
                    section_end = i
                    break
            else:
                section_end = len(lines)
            
            # Füge die neue Änderung hinzu
            lines.insert(section_end, f'- {change_description}\n')
        
        # Schreibe die aktualisierte Changelog
        self.write_changelog(lines)
        print(f"Änderung zum Typ '{change_type}' hinzugefügt: {change_description}")
    
    def initialize_changelog(self) -> None:
        """Initialisiert eine neue Changelog-Datei."""
        if os.path.exists(self.changelog_path):
            print("Changelog-Datei existiert bereits.")
            return
        
        content = """# Changelog

Alle bemerkenswerten Änderungen an diesem Projekt werden in dieser Datei dokumentiert.

Das Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.0.0/),
und dieses Projekt hält sich an [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Hinzugefügt

### Geändert

### Veraltet

### Entfernt

### Behoben

### Sicherheit

"""
        
        with open(self.changelog_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("Changelog-Datei erfolgreich initialisiert.")


def main():
    """Hauptfunktion des Skripts."""
    if len(sys.argv) < 2:
        print("Verwendung:")
        print("  python update_changelog.py init                    - Initialisiert eine neue Changelog-Datei")
        print("  python update_changelog.py add <Typ> <Beschreibung> - Fügt eine Änderung hinzu")
        print("  python update_changelog.py release <Version>       - Erstellt ein Release")
        return
    
    updater = ChangelogUpdater()
    
    command = sys.argv[1]
    
    if command == "init":
        updater.initialize_changelog()
    elif command == "add" and len(sys.argv) >= 4:
        change_type = sys.argv[2]
        change_description = " ".join(sys.argv[3:])
        updater.add_unreleased_change(change_type, change_description)
    elif command == "release" and len(sys.argv) >= 3:
        version = sys.argv[2]
        updater.update_changelog_for_release(version)
    else:
        print("Ungültiger Befehl oder fehlende Argumente.")
        print("Verwendung:")
        print("  python update_changelog.py init                    - Initialisiert eine neue Changelog-Datei")
        print("  python update_changelog.py add <Typ> <Beschreibung> - Fügt eine Änderung hinzu")
        print("  python update_changelog.py release <Version>       - Erstellt ein Release")


if __name__ == "__main__":
    main()