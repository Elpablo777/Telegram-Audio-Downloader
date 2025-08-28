#!/usr/bin/env python3
"""
Einfacher Sicherheitsscan für das Telegram Audio Downloader Projekt.
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

def check_dependencies():
    """Überprüft die Abhängigkeiten auf bekannte Sicherheitslücken mit pip-audit."""
    print("\n🔍 Überprüfe Abhängigkeiten auf Sicherheitslücken...")
    
    try:
        # Prüfe, ob pip-audit verfügbar ist
        import pip_audit
        from pip_audit import audit as pip_audit_audit
        
        # Führe pip-audit aus
        result = pip_audit_audit.audit()
        
        if result.vulnerabilities:
            issues = []
            for vuln in result.vulnerabilities:
                for cve in vuln.vuln_id:
                    issues.append(f"{vuln.package.name} {vuln.package.version}: {cve}")
            return {"status": "⚠️", "details": issues}
        return {"status": "✅", "details": ["Keine bekannten Sicherheitslücken gefunden."]}
        
    except ImportError:
        return {"status": "ℹ️", "details": ["pip-audit nicht installiert. Installieren Sie es mit 'pip install pip-audit'."]}
    except Exception as e:
        return {"status": "❌", "details": [f"Fehler bei der Überprüfung: {str(e)}"]}

def check_permissions():
    """Überprüft die Berechtigungen der Workflow-Dateien."""
    print("\n🔍 Überprüfe Workflow-Berechtigungen...")
    
    workflow_dir = REPO_ROOT / ".github" / "workflows"
    issues = []
    
    for workflow_file in workflow_dir.glob("*.yml"):
        with open(workflow_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'permissions:' not in content:
                issues.append(f"{workflow_file.name}: Keine Berechtigungen definiert")
    
    if issues:
        return {"status": "⚠️", "details": issues}
    return {"status": "✅", "details": ["Alle Workflows haben Berechtigungen definiert."]}

def check_sensitive_files():
    """Überprüft auf sensible Dateien im Repository."""
    print("\n🔍 Suche nach sensiblen Dateien...")
    
    sensitive_patterns = [
        '*.pem', '*.key', '*.p12', '*.pfx', '*.cer', '*.crt',
        'id_rsa*', 'id_dsa*', 'id_ecdsa*', 'id_ed25519*',
        '*.env', '.env*', 'secrets.*', 'config.*', '*.config',
        'credentials.json', 'appsettings.json', '*.pem', '*.p8', '*.p12',
        '*.p7b', '*.p7c', '*.p7m', '*.p7s', '*.pfx', '*.key', '*.gpg',
        '*.jks', '*.keystore', '*.ovpn', '*.srl', '*.srt', '*.sst',
        '*.stl', '*.stm', '*.stx', '*.sublime-workspace', '*.sublime-project'
    ]
    
    found_files = []
    for pattern in sensitive_patterns:
        for file in REPO_ROOT.rglob(pattern):
            if file.is_file():
                found_files.append(str(file.relative_to(REPO_ROOT)))
    
    if found_files:
        return {"status": "⚠️", "details": [f"Möglicherweise sensible Datei gefunden: {f}" for f in found_files]}
    return {"status": "✅", "details": ["Keine offensichtlich sensiblen Dateien gefunden."]}

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
        "Workflow-Berechtigungen": check_permissions(),
        "Sensible Dateien": check_sensitive_files()
    }
    
    generate_report(results)
    print("\n✅ Sicherheitsscan abgeschlossen!")

if __name__ == "__main__":
    main()
