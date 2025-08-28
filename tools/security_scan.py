#!/usr/bin/env python3
"""
Sicherheitsscan für das Telegram Audio Downloader Projekt.
Führt verschiedene Sicherheitsprüfungen durch und generiert einen Bericht.
"""

import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime

# Konfiguration
REPO_ROOT = Path(__file__).parent.parent
REQUIREMENTS_FILE = REPO_ROOT / "requirements.txt"
REPORT_FILE = REPO_ROOT / "security_report.md"


def run_command(cmd, cwd=None):
    """Führt einen Shell-Befehl aus und gibt die Ausgabe zurück."""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd or REPO_ROOT,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Fehler beim Ausführen von {cmd}: {e}")
        return None


def check_dependencies():
    """Überprüft die Abhängigkeiten auf bekannte Sicherheitslücken."""
    print("\n🔍 Überprüfe Abhängigkeiten auf Sicherheitslücken...")
    
    # Führe safety check aus
    try:
        safety_result = run_command(["safety", "check", "--json"])
        if safety_result:
            vulnerabilities = json.loads(safety_result)
            if vulnerabilities:
                return {
                    "status": "⚠️",
                    "details": [f"{v['package_name']} {v['vulnerable_spec']}: {v['advisory']}" 
                               for v in vulnerabilities]
                }
        return {"status": "✅", "details": ["Keine bekannten Sicherheitslücken gefunden."]}
    except Exception as e:
        return {"status": "❌", "details": [f"Fehler bei der Überprüfung: {str(e)}"]}


def check_secrets():
    """Überprüft das Repository auf versehentlich offengelegte Geheimnisse."""
    print("\n🔍 Suche nach exponierten Geheimnissen...")
    
    # Führe gitleaks aus, falls installiert
    if run_command(["which", "gitleaks"]):
        try:
            leaks = run_command(["gitleaks", "detect", "--source=.", "-v"])
            if "No leaks found" in leaks:
                return {"status": "✅", "details": ["Keine exponierten Geheimnisse gefunden."]}
            else:
                return {"status": "⚠️", "details": ["Mögliche Geheimnisse gefunden. Bitte überprüfen Sie die Ausgabe von 'gitleaks detect'."]}
        except Exception as e:
            return {"status": "❌", "details": [f"Fehler bei der Überprüfung: {str(e)}"]}
    else:
        return {"status": "ℹ️", "details": ["Gitleaks nicht installiert. Installieren Sie es mit 'brew install gitleaks'."]}


def check_permissions():
    """Überprüft die Berechtigungen der Workflow-Dateien."""
    print("\n🔍 Überprüfe Workflow-Berechtigungen...")
    
    workflow_dir = REPO_ROOT / ".github" / "workflows"
    issues = []
    
    if workflow_dir.exists():
        for workflow_file in workflow_dir.glob("*.yml"):
            with open(workflow_file, 'r') as f:
                content = f.read()
                if 'permissions:' not in content:
                    issues.append(f"{workflow_file.name}: Keine Berechtigungen definiert")
    
    if issues:
        return {"status": "⚠️", "details": issues}
    return {"status": "✅", "details": ["Alle Workflows haben Berechtigungen definiert."]}


def generate_report(results):
    """Generiert einen Sicherheitsbericht im Markdown-Format."""
    report = ["# 🔒 Sicherheitsbericht", "", f"Generiert am: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ""]
    
    for check, result in results.items():
        report.append(f"## {check}")
        report.append(f"**Status:** {result['status']}")
        report.append("")
        for detail in result['details']:
            report.append(f"- {detail}")
        report.append("")
    
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        f.write("\n".join(report))
    
    print(f"\n📊 Bericht wurde gespeichert unter: {REPORT_FILE}")


def main():
    """Hauptfunktion für den Sicherheitsscan."""
    print("🚀 Starte Sicherheitsscan...")
    
    results = {
        "Abhängigkeiten": check_dependencies(),
        "Geheimnisse": check_secrets(),
        "Berechtigungen": check_permissions()
    }
    
    generate_report(results)
    print("\n✅ Sicherheitsscan abgeschlossen!")


if __name__ == "__main__":
    main()