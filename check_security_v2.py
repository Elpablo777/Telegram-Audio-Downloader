import subprocess
import sys
import json
from pathlib import Path

def check_security():
    """Führt eine Sicherheitsüberprüfung mit pip-audit durch, falls verfügbar."""
    try:
        # Prüfe, ob pip-audit installiert ist
        import importlib.util
        if importlib.util.find_spec("pip_audit") is None:
            print("pip-audit ist nicht installiert. Installiere es mit 'pip install pip-audit'")
            return
            
        # Führe pip-audit aus
        print("Führe Sicherheitsüberprüfung mit pip-audit durch...")
        result = subprocess.run(
            [sys.executable, "-m", "pip_audit", "--requirement", "requirements.txt", "--format", "json"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            try:
                report = json.loads(result.stdout)
                if not report.get("vulnerabilities"):
                    print("✅ Keine Sicherheitslücken gefunden!")
                else:
                    print("⚠️  Gefundene Sicherheitslücken:")
                    for i, vuln in enumerate(report["vulnerabilities"], 1):
                        print(f"\n{i}. Paket: {vuln.get('name', 'Unbekannt')}")
                        print(f"   Version: {vuln.get('installed_version', 'Unbekannt')}")
                        print(f"   Sicherheitslücke: {vuln.get('vuln_id', 'Unbekannt')}")
                        print(f"   Schweregrad: {vuln.get('severity', 'Unbekannt')}")
                        print(f"   Beschreibung: {vuln.get('description', 'Keine Beschreibung verfügbar')}")
            except json.JSONDecodeError:
                print("Fehler beim Verarbeiten der Sicherheitsberichte.")
                print("Rohausgabe:", result.stdout)
        else:
            print("Fehler bei der Ausführung von pip-audit:")
            print(result.stderr)
            
    except Exception as e:
        print(f"Fehler bei der Sicherheitsüberprüfung: {str(e)}")

if __name__ == "__main__":
    check_security()
