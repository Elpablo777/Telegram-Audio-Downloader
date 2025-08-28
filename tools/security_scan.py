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
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Fehler beim Ausführen von {cmd}: {e}")
        return None

def check_dependencies():
    """Überprüft die Abhängigkeiten auf bekannte Sicherheitslücken."""
    print("\n🔍 Überprüfe Abhängigkeiten auf Sicherheitslücken...")
    
    # Führe safety check aus
    try:
        safety_result = run_command(["safety", "check", "--json"])
        if safety_result is not None:
            if safety_result.strip():  # Prüfe ob Ergebnis nicht leer ist
                try:
                    vulnerabilities = json.loads(safety_result)
                    if vulnerabilities:
                        return {
                            "status": "⚠️",
                            "details": [f"{v['package_name']} {v['vulnerable_spec']}: {v['advisory']}" 
                                       for v in vulnerabilities]
                        }
                except json.JSONDecodeError as e:
                    return {"status": "❌", "details": [f"Fehler beim Parsen der safety-Ausgabe: {str(e)}"]}
            return {"status": "✅", "details": ["Keine bekannten Sicherheitslücken gefunden."]}
        else:
            return {"status": "❌", "details": ["Safety-Tool nicht verfügbar oder Ausführung fehlgeschlagen."]}
    except Exception as e:
        return {"status": "❌", "details": [f"Fehler bei der Überprüfung: {str(e)}"]}

def check_secrets():
    """Überprüft das Repository auf versehentlich offengelegte Geheimnisse."""
    print("\n🔍 Suche nach exponierten Geheimnissen...")
    
    # Führe gitleaks aus, falls installiert
    if run_command(["which", "gitleaks"]):
        try:
            leaks = run_command(["gitleaks", "detect", "--source=.", "-v"])
            if leaks is not None:
                if "No leaks found" in leaks:
                    return {"status": "✅", "details": ["Keine exponierten Geheimnisse gefunden."]}
                else:
                    # Do NOT include leaks content; only summary message.
                    return {"status": "⚠️", "details": ["Mögliche Geheimnisse gefunden. Die Details werden aus Sicherheitsgründen nicht im Bericht gespeichert. Bitte überprüfen Sie die Ausgabe von 'gitleaks detect' im Terminal."]}
                # Defensive: you may wish to save leaks output to a safe file with restricted permissions if needed.
        except Exception as e:
            return {"status": "❌", "details": [f"Fehler bei der Überprüfung: {str(e)}"]}
    else:
        return {"status": "ℹ️", "details": ["Gitleaks nicht installiert. Installieren Sie es mit 'brew install gitleaks'."]}

def check_permissions():
    """Überprüft die Berechtigungen der Workflow-Dateien."""
    print("\n🔍 Überprüfe Workflow-Berechtigungen...")
    
    workflow_dir = REPO_ROOT / ".github" / "workflows"
    issues = []
    
    # Prüfe ob das Workflow-Verzeichnis existiert
    if not workflow_dir.exists():
        return {"status": "ℹ️", "details": ["Kein Workflow-Verzeichnis gefunden."]}
    
    try:
        # Prüfe sowohl .yml als auch .yaml Dateien
        for pattern in ["*.yml", "*.yaml"]:
            for workflow_file in workflow_dir.glob(pattern):
                try:
                    with open(workflow_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if 'permissions:' not in content:
                            issues.append(f"{workflow_file.name}: Keine Berechtigungen definiert")
                except Exception as e:
                    issues.append(f"{workflow_file.name}: Fehler beim Lesen der Datei - {str(e)}")
        
        if issues:
            return {"status": "⚠️", "details": issues}
        return {"status": "✅", "details": ["Alle Workflows haben Berechtigungen definiert."]}
    except Exception as e:
        return {"status": "❌", "details": [f"Fehler bei der Überprüfung: {str(e)}"]}

def generate_report(results):
    """Generiert einen Sicherheitsbericht im Markdown-Format."""
    try:
        report = ["# 🔒 Sicherheitsbericht", "", f"Generiert am: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ""]
        
        for check, result in results.items():
            report.append(f"## {check}")
            report.append(f"**Status:** {result['status']}")
            report.append("")
            for detail in result['details']:
                # Never write raw secrets or gitleaks output into the report.
                report.append(f"- {detail}")
            report.append("")
        
        with open(REPORT_FILE, 'w', encoding='utf-8') as f:
            f.write("\n".join(report))
        
        print(f"\n📊 Bericht wurde gespeichert unter: {REPORT_FILE}")
    except Exception as e:
        print(f"\n❌ Fehler beim Erstellen des Berichts: {str(e)}")

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
