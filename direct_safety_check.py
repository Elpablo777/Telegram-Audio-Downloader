import json
import subprocess
import sys
from pathlib import Path

def check_dependencies():
    """Führt eine Sicherheitsüberprüfung der Abhängigkeiten durch."""
    requirements_path = Path("requirements.txt")
    if not requirements_path.exists():
        return {"error": "requirements.txt nicht gefunden"}
    
    try:
        # Versuche, safety zu importieren
        try:
            from safety import safety
            from safety.formatter import report
            from safety.util import read_requirements
        except ImportError:
            return {"error": "safety nicht installiert. Bitte mit 'pip install safety' installieren."}
        
        # Lese die Anforderungen
        packages = list(read_requirements(requirements_path, resolve=False))
        
        # Führe die Sicherheitsprüfung durch
        vulns = safety.check(pkgs=packages, key=None, db_mirror=None, cached=False, ignore_ids=[])
        
        # Erstelle einen Bericht
        return {
            "vulnerabilities": [
                {
                    "name": v.name,
                    "installed_version": v.installed_version,
                    "vulnerability_id": v.vulnerability_id,
                    "advisory": v.advisory,
                    "affected_versions": v.specs,
                }
                for v in vulns
            ]
        }
        
    except Exception as e:
        return {"error": f"Fehler bei der Sicherheitsüberprüfung: {str(e)}"}

if __name__ == "__main__":
    result = check_dependencies()
    if "error" in result:
        print(f"Fehler: {result['error']}")
        sys.exit(1)
    
    if not result["vulnerabilities"]:
        print("✅ Keine Sicherheitslücken gefunden!")
    else:
        print("⚠️  Gefundene Sicherheitslücken:")
        for i, vuln in enumerate(result["vulnerabilities"], 1):
            print(f"\n{i}. Paket: {vuln['name']} (Version: {vuln['installed_version']})")
            print(f"   Sicherheitslücke: {vuln['vulnerability_id']}")
            print(f"   Betroffene Versionen: {vuln['affected_versions']}")
            print(f"   Empfehlung: {vuln['advisory']}")
