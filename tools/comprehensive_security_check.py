#!/usr/bin/env python3
"""
Umfassender Sicherheitsscan für das Telegram Audio Downloader Projekt.
Führt alle empfohlenen Sicherheitsprüfungen durch:
- Abhängigkeitsüberprüfungen (pip-audit, safety)
- Suche nach sensiblen Dateien (gitleaks)
- Berechtigungsprüfungen
"""

import json
import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime

# Konfiguration
REPO_ROOT = Path(__file__).parent.parent
REQUIREMENTS_FILE = REPO_ROOT / "requirements.txt"
REPORT_FILE = REPO_ROOT / "security_report.md"

def run_command(command, cwd=None):
    """Führt einen Shell-Befehl sicher aus und gibt das Ergebnis zurück."""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            cwd=cwd,
            capture_output=True, 
            text=True,
            timeout=300  # 5 Minuten Timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Befehl timed out"
    except Exception as e:
        return -1, "", str(e)

def check_dependencies():
    """Überprüft die Abhängigkeiten auf bekannte Sicherheitslücken."""
    print("\n🔍 Überprüfe Abhängigkeiten auf Sicherheitslücken...")
    
    results = {}
    
    # Prüfe mit pip-audit
    print("  → Führe pip-audit aus...")
    returncode, stdout, stderr = run_command(f"pip-audit --requirement {REQUIREMENTS_FILE}")
    if returncode == 0:
        results["pip-audit"] = {"status": "✅", "details": ["Keine bekannten Sicherheitslücken gefunden."]}
    else:
        results["pip-audit"] = {"status": "⚠️", "details": [stdout, stderr]}
    
    # Prüfe mit safety
    print("  → Führe safety check aus...")
    returncode, stdout, stderr = run_command(f"safety check --file={REQUIREMENTS_FILE}")
    if returncode == 0:
        results["safety"] = {"status": "✅", "details": ["Keine bekannten Sicherheitslücken gefunden."]}
    else:
        results["safety"] = {"status": "⚠️", "details": [stdout, stderr]}
    
    return results

def check_sensitive_files():
    """Überprüft auf sensible Dateien im Repository."""
    print("\n🔍 Suche nach sensiblen Dateien...")
    
    # Prüfe mit gitleaks
    print("  → Führe gitleaks scan aus...")
    returncode, stdout, stderr = run_command("gitleaks detect --source=. -v")
    if returncode == 0:
        return {"status": "✅", "details": ["Keine sensiblen Daten gefunden."]}
    else:
        return {"status": "⚠️", "details": [stdout, stderr]}

def check_permissions():
    """Überprüft die Berechtigungen sensibler Dateien."""
    print("\n🔍 Überprüfe Dateiberechtigungen...")
    
    issues = []
    
    # Prüfe .env-Dateien
    env_files = list(REPO_ROOT.glob(".env*"))
    for env_file in env_files:
        if env_file.exists():
            # Auf Unix-Systemen prüfen wir die Berechtigungen
            if os.name != 'nt':  # Nicht auf Windows
                stat = env_file.stat()
                # Prüfe ob die Datei nur für den Besitzer lesbar ist (chmod 600)
                if stat.st_mode & 0o777 != 0o600:
                    issues.append(f"{env_file}: Sollte chmod 600 haben")
    
    if issues:
        return {"status": "⚠️", "details": issues}
    return {"status": "✅", "details": ["Alle sensiblen Dateien haben korrekte Berechtigungen."]}

def check_workflows():
    """Überprüft die GitHub Actions Workflows auf Sicherheitsprobleme."""
    print("\n🔍 Überprüfe GitHub Actions Workflows...")
    
    workflow_dir = REPO_ROOT / ".github" / "workflows"
    issues = []
    
    if workflow_dir.exists():
        for workflow_file in workflow_dir.glob("*.yml"):
            with open(workflow_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # Prüfe auf minimale Berechtigungen
                if 'permissions:' not in content:
                    issues.append(f"{workflow_file.name}: Keine Berechtigungen definiert")
                # Prüfe auf unsichere Praktiken
                if 'GITHUB_TOKEN' in content and 'secrets.GITHUB_TOKEN' not in content:
                    issues.append(f"{workflow_file.name}: Potenziell unsichere Token-Verwendung")
    
    if issues:
        return {"status": "⚠️", "details": issues}
    return {"status": "✅", "details": ["Alle Workflows haben korrekte Sicherheitseinstellungen."]}

def generate_report(results):
    """Generiert einen Sicherheitsbericht im Markdown-Format."""
    report = ["# 🔒 Umfassender Sicherheitsbericht", "", f"Generiert am: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ""]
    
    for check, result in results.items():
        # Für verschachtelte Ergebnisse (wie bei Abhängigkeitsprüfungen)
        if isinstance(result, dict) and 'pip-audit' in result:
            report.append(f"## {check}")
            for subcheck, subresult in result.items():
                report.append(f"### {subcheck}")
                report.append(f"**Status:** {subresult['status']}")
                report.append("")
                for detail in subresult['details']:
                    if detail.strip():
                        report.append(f"- {detail}")
                report.append("")
        else:
            report.append(f"## {check}")
            report.append(f"**Status:** {result['status']}")
            report.append("")
            for detail in result['details']:
                if detail.strip():
                    report.append(f"- {detail}")
            report.append("")
    
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        f.write("\n".join(report))
    
    print(f"\n📊 Bericht wurde gespeichert unter: {REPORT_FILE}")

def main():
    """Hauptfunktion für den umfassenden Sicherheitsscan."""
    print("🚀 Starte umfassenden Sicherheitsscan...")
    
    results = {
        "Abhängigkeiten": check_dependencies(),
        "Sensible Dateien": check_sensitive_files(),
        "Dateiberechtigungen": check_permissions(),
        "GitHub Workflows": check_workflows()
    }
    
    generate_report(results)
    print("\n✅ Umfassender Sicherheitsscan abgeschlossen!")

if __name__ == "__main__":
    main()