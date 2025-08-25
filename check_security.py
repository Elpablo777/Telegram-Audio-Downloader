import subprocess
import json
import sys

def run_safety_check():
    try:
        # Führe den Safety-Check aus und erhalte die Ausgabe
        result = subprocess.run(
            [sys.executable, "-m", "safety", "check", "-r", "requirements.txt", "--ignore-unpinned-requirements=false", "--output", "json"],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Parse die JSON-Ausgabe
        try:
            report = json.loads(result.stdout)
            return report
        except json.JSONDecodeError:
            return {"error": "Fehler beim Parsen der JSON-Ausgabe", "output": result.stdout, "stderr": result.stderr}
            
    except subprocess.CalledProcessError as e:
        return {"error": "Fehler beim Ausführen von Safety", "stdout": e.stdout, "stderr": e.stderr}
    except Exception as e:
        return {"error": f"Unbekannter Fehler: {str(e)}"}

if __name__ == "__main__":
    report = run_safety_check()
    if "error" in report:
        print(f"Fehler: {report['error']}")
        if "stdout" in report:
            print(f"\nAusgabe:\n{report['stdout']}")
        if "stderr" in report:
            print(f"\nFehlerausgabe:\n{report['stderr']}")
    else:
        print("Sicherheitsbericht:")
        print(json.dumps(report, indent=2))
