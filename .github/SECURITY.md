# Sicherheitsrichtlinien

## 📧 Melden von Sicherheitslücken

Bitte melden Sie Sicherheitslücken über GitHub Security Advisories:
- Navigieren Sie zu „Security“ > „Advisories“ > „Report a vulnerability“ im Repository
- Alternativ per E-Mail an: hannover84@msn.com
- Wir bestätigen den Eingang innerhalb von 48 Stunden und liefern innerhalb von 7 Tagen einen ersten Status

## 🛡️ Sicherheitsrelevante Checks & Automatisierung

### Aktivierte Tools
- CodeQL: Statische Analyse über GitHub Code Scanning
- Bandit: Python SAST mit SARIF-Upload
- Safety: Überprüfung von Python-Abhängigkeiten auf bekannte CVEs
- Dependabot: Sicherheitswarnungen & PRs für Updates (pip, actions, docker)
- Dependency Review: Blockiert riskante Dependency-Änderungen in PRs
- Gitleaks: Secret-Scanning (lokal/CI) mit konfigurierbarem Allowlist

### Aktuelle Sicherheitsmaßnahmen
- Versionierte Abhängigkeiten mit regelmäßigen Updates via Dependabot
- Automatisierte Scans auf Push/PR und nach Zeitplan
- Minimalprinzip bei Workflow-Berechtigungen (permissions: read + security-events: write)

## 🔐 Workflow-Berechtigungen (Beispiel)

```yaml
permissions:
  contents: read
  security-events: write
```

## 🔒 Geheimnisse & Datenschutz
- Alle Secrets ausschließlich via GitHub Actions Secrets
- Keine Klartext-Schlüssel im Repo (Gitleaks enforced)
- Regelmäßige Rotation kritischer Zugangsdaten

## 🔄 Regelmäßige Sicherheitsüberprüfungen
- Wöchentliche Safety/Pip-Audit Scans
- Kontinuierliches Code Scanning (CodeQL)
- PR-basierte Dependency Review Checks

## 🚀 Richtlinien für Entwickler
1. Keine hartcodierten Anmeldedaten/Token
2. Sicherheitsrelevante Änderungen benötigen Reviewer
3. Abhängigkeiten regelmäßig aktualisieren (Dependabot nutzen)
4. Vor Merge: Linter, Tests, Security-Checks grün

## 📅 SLA & Offenlegung
- Erstreaktion: 48h, erste Einschätzung: 7 Tage
- Koordinierte Offenlegung: Wir veröffentlichen Fixes koordiniert und schreiben CVE/Advisory, falls relevant
