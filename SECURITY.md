# 🔒 Security Policy

## Supported Versions

Wir unterstützen derzeit die folgenden Versionen mit Sicherheitsupdates:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | ✅ Aktiv unterstützt |
| < 1.0   | ❌ Nicht unterstützt |

## 🛡️ Reporting a Vulnerability

Die Sicherheit unseres Projekts ist uns sehr wichtig. Wenn Sie eine Sicherheitslücke entdecken, bitten wir Sie, verantwortungsvoll vorzugehen.

### 📧 Meldung von Sicherheitslücken

**Bitte melden Sie Sicherheitslücken NICHT über öffentliche GitHub Issues.**

Stattdessen senden Sie bitte eine E-Mail an:
- **E-Mail**: hannover84@msn.com
- **Betreff**: [SECURITY] Telegram Audio Downloader - Sicherheitslücke

### 📋 Erforderliche Informationen

Bitte geben Sie folgende Informationen an:

1. **Art der Sicherheitslücke**
   - Beschreibung des Problems
   - Potential Impact
   - Affected Components

2. **Reproduktion**
   - Schritt-für-Schritt Anleitung
   - Proof of Concept (falls vorhanden)
   - Screenshots/Logs (falls relevant)

3. **Umgebung**
   - Python Version
   - Betriebssystem
   - Projektversion

4. **Vorgeschlagene Lösung** (optional)
   - Mögliche Fixes
   - Workarounds

### ⏱️ Response Timeline

Wir bemühen uns, auf Sicherheitsmeldungen zeitnah zu reagieren:

- **Erste Antwort**: Innerhalb von 48 Stunden
- **Status-Update**: Innerhalb von 7 Tagen
- **Fix-Timeline**: Abhängig von der Schwere der Lücke

### 🏆 Anerkennung

Wir schätzen die Arbeit von Security Researchers sehr:

- **Responsible Disclosure**: Öffentliche Anerkennung nach dem Fix
- **Hall of Fame**: Auflistung in unseren Projekt-Credits
- **CVE Credits**: Bei offiziellen CVE-Einträgen

### 🔐 Sicherheits-Best-Practices

#### Für Entwickler:
- Niemals API-Keys oder Credentials in den Code committen
- Regelmäßige Dependency-Updates mit `dependabot`
- Code-Review für alle Security-relevanten Änderungen
- Statische Code-Analyse mit `bandit` und `safety`

#### Für Benutzer:
- Verwenden Sie immer die neueste Version
- Sichern Sie Ihre Telegram-API-Credentials
- Verwenden Sie starke Passwörter für Ihr Telegram-Konto
- Überprüfen Sie regelmäßig die Download-Verzeichnis-Berechtigungen

### 📚 Security Resources

- [Python Security Guide](https://python-security.readthedocs.io/)
- [Telegram Bot Security](https://core.telegram.org/bots/faq#security)
- [OWASP Python Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Python_Security_Cheat_Sheet.html)

### 🚨 Emergency Contact

Bei kritischen Sicherheitslücken, die eine sofortige Reaktion erfordern:
- **Urgent Email**: hannover84@msn.com (Subject: [CRITICAL SECURITY])
- **Response Time**: < 24 Stunden

---

**Vielen Dank, dass Sie dabei helfen, unser Projekt sicher zu halten!** 🙏