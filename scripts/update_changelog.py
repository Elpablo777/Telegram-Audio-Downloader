#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Changelog Update Automation Script
==================================

Professionelles Skript zur automatisierten Aktualisierung des Changelogs
gemäß den Standards des Telegram Audio Downloaders.

Dieses Skript implementiert:
- Automatische Changelog-Generierung
- Einhaltung des Keep-a-Changelog-Formats
- Versionsnummer-Management
- Release-Informationen-Aktualisierung
"""

import os
import sys
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import subprocess

def get_git_tags() -> List[str]:
    """Ruft die Git-Tags des Repositories ab."""
    try:
        result = subprocess.run(
            ["git", "tag", "--sort=-v:refname"],
            capture_output=True,
            text=True,
            check=True
        )
        return [tag.strip() for tag in result.stdout.strip().split('\n') if tag.strip()]
    except subprocess.CalledProcessError:
        return []

def get_latest_tag() -> Optional[str]:
    """Ruft den neuesten Git-Tag ab."""
    tags = get_git_tags()
    return tags[0] if tags else None

def get_git_commits_since_tag(tag: str = None) -> List[Dict[str, str]]:
    """Ruft Git-Commits seit dem letzten Tag ab."""
    try:
        if tag:
            cmd = ["git", "log", f"{tag}..HEAD", "--oneline", "--no-merges"]
        else:
            cmd = ["git", "log", "--oneline", "--no-merges"]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        commits = []
        for line in result.stdout.strip().split('\n'):
            if line.strip():
                # Extrahiere Commit-Hash und Nachricht
                parts = line.split(' ', 1)
                if len(parts) == 2:
                    commits.append({
                        'hash': parts[0],
                        'message': parts[1]
                    })
        return commits
    except subprocess.CalledProcessError:
        return []

def categorize_commit(message: str) -> str:
    """Kategorisiert einen Commit basierend auf der Nachricht."""
    message_lower = message.lower()
    
    if any(keyword in message_lower for keyword in ['security', 'sicherheit', 'cve', 'vulnerability']):
        return 'Sicherheit'
    elif any(keyword in message_lower for keyword in ['add', 'new', 'implement', 'hinzufügen']):
        return 'Hinzugefügt'
    elif any(keyword in message_lower for keyword in ['change', 'update', 'modify', 'ändern']):
        return 'Geändert'
    elif any(keyword in message_lower for keyword in ['fix', 'bug', 'repair', 'fehler']):
        return 'Behoben'
    elif any(keyword in message_lower for keyword in ['remove', 'delete', 'entfernen']):
        return 'Entfernt'
    elif any(keyword in message_lower for keyword in ['deprecate', 'veraltet']):
        return 'Veraltet'
    else:
        return 'Behoben'  # Standardkategorie

def update_changelog(version: str, commits: List[Dict[str, str]]) -> None:
    """Aktualisiert die CHANGELOG.md-Datei."""
    changelog_path = Path("CHANGELOG.md")
    
    # Kategorisiere Commits
    categorized_commits = {}
    for commit in commits:
        category = categorize_commit(commit['message'])
        if category not in categorized_commits:
            categorized_commits[category] = []
        categorized_commits[category].append(commit['message'])
    
    # Erstelle neuen Changelog-Eintrag
    date_str = datetime.now().strftime("%Y-%m-%d")
    new_entry = f"## [{version}] - {date_str}\n\n"
    
    # Füge kategorisierte Commits hinzu
    categories = ['Hinzugefügt', 'Geändert', 'Veraltet', 'Entfernt', 'Behoben', 'Sicherheit']
    for category in categories:
        if category in categorized_commits and categorized_commits[category]:
            new_entry += f"### {category}\n\n"
            for message in categorized_commits[category]:
                # Entferne ggf. vorhandene Kategoriekennzeichnungen aus der Nachricht
                clean_message = re.sub(r'^(add|change|fix|remove|deprecate|security):\s*', '', message, flags=re.IGNORECASE)
                new_entry += f"- {clean_message}\n"
            new_entry += "\n"
    
    # Lese vorhandene Changelog-Datei
    if changelog_path.exists():
        content = changelog_path.read_text(encoding='utf-8')
        
        # Füge neue Einträge nach dem [Unreleased]-Abschnitt ein
        if '## [Unreleased]' in content:
            lines = content.split('\n')
            new_lines = []
            unreleased_found = False
            unreleased_processed = False
            
            for line in lines:
                if line.strip() == '## [Unreleased]':
                    unreleased_found = True
                    new_lines.append(line)
                    # Füge leere Zeilen für die Kategorien hinzu
                    new_lines.append("")
                    new_lines.append("### Hinzugefügt")
                    new_lines.append("")
                    new_lines.append("### Geändert")
                    new_lines.append("")
                    new_lines.append("### Veraltet")
                    new_lines.append("")
                    new_lines.append("### Entfernt")
                    new_lines.append("")
                    new_lines.append("### Behoben")
                    new_lines.append("")
                    new_lines.append("### Sicherheit")
                    new_lines.append("")
                elif unreleased_found and line.startswith('## [') and not unreleased_processed:
                    # Füge den neuen Eintrag vor dem nächsten Versions-Eintrag ein
                    new_lines.append("")
                    new_lines.append(new_entry.rstrip())
                    new_lines.append("")
                    new_lines.append(line)
                    unreleased_processed = True
                else:
                    new_lines.append(line)
            
            # Wenn [Unreleased] nicht verarbeitet wurde, füge den Eintrag am Ende hinzu
            if unreleased_found and not unreleased_processed:
                new_lines.append("")
                new_lines.append(new_entry.rstrip())
            
            content = '\n'.join(new_lines)
        else:
            # Füge neuen Eintrag am Anfang nach dem Header ein
            lines = content.split('\n')
            if len(lines) > 7:  # Nach dem Standard-Changelog-Header
                lines.insert(7, new_entry.rstrip() + '\n')
                content = '\n'.join(lines)
            else:
                content += '\n' + new_entry
        
        # Aktualisiere Versionsverweise am Ende der Datei
        if f"[{version}]: " not in content:
            # Füge Versionsverweis hinzu (Platzhalter-URL)
            content += f"[{version}]: https://github.com/Elpablo777/Telegram-Audio-Downloader/releases/tag/v{version}\n"
    else:
        # Erstelle neue Changelog-Datei
        content = """# 📝 Changelog

Alle bemerkenswerten Änderungen an diesem Projekt werden in dieser Datei dokumentiert.

Das Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.0.0/),
und dieses Projekt hält sich an [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

"""
        content += new_entry
        content += f"[{version}]: https://github.com/Elpablo777/Telegram-Audio-Downloader/releases/tag/v{version}\n"
    
    # Schreibe aktualisierte Changelog-Datei
    changelog_path.write_text(content, encoding='utf-8')
    print(f"✅ Changelog für Version {version} aktualisiert")

def main():
    """Hauptfunktion des Changelog-Update-Skripts."""
    print("📝 Telegram Audio Downloader - Changelog Update Automation")
    print("=" * 60)
    
    # Bestimme die neue Version
    if len(sys.argv) > 1:
        version = sys.argv[1]
    else:
        # Standardversion (kann angepasst werden)
        version = "1.1.1"
    
    print(f"🚀 Aktualisiere Changelog für Version: {version}")
    
    # Hole Commits seit dem letzten Tag
    latest_tag = get_latest_tag()
    print(f"🔍 Letzter Git-Tag: {latest_tag or 'Keiner gefunden'}")
    
    commits = get_git_commits_since_tag(latest_tag)
    print(f"📋 Gefundene Commits: {len(commits)}")
    
    if commits:
        # Aktualisiere Changelog
        update_changelog(version, commits)
        
        # Zeige eine Vorschau der Änderungen
        print("\n📋 Vorschau der Änderungen:")
        print("-" * 30)
        for commit in commits[:10]:  # Zeige die ersten 10 Commits
            print(f"  • {commit['message']}")
        if len(commits) > 10:
            print(f"  ... und {len(commits) - 10} weitere Commits")
    else:
        print("ℹ️ Keine neuen Commits seit dem letzten Tag gefunden")
    
    print(f"\n✅ Changelog-Aktualisierung abgeschlossen!")
    print("💡 Vergiss nicht, die Änderungen zu commiten:")
    print(f"   git add CHANGELOG.md")
    print(f"   git commit -m \"docs: Update changelog for v{version}\"")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())