# 🔒 Security Policy

## 📋 **Supported Versions**

Wir unterstützen die folgenden Versionen mit Sicherheitsupdates:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | ✅ Yes            |
| < 1.0   | ❌ No             |

---

## 🚨 **Reporting a Vulnerability**

### **Wie Sie Sicherheitslücken melden**

Die Sicherheit unserer Benutzer ist uns sehr wichtig. Wenn Sie eine Sicherheitslücke entdecken, bitten wir Sie, diese verantwortungsvoll zu melden.

### **📧 Kontakt**
- **E-Mail**: hannover84@msn.com
- **Subject**: `[SECURITY] Telegram Audio Downloader - Vulnerability Report`
- **Antwortzeit**: Wir versuchen innerhalb von 48 Stunden zu antworten

### **📋 Was in Ihren Bericht gehört**

Bitte fügen Sie folgende Informationen bei:

1. **Beschreibung der Schwachstelle**
   - Klare, detaillierte Beschreibung des Problems
   - Welche Komponente ist betroffen?

2. **Reproduktion**
   - Schritt-für-Schritt-Anleitung zur Reproduktion
   - Code-Beispiele (falls zutreffend)
   - Screenshots oder Videos (falls hilfreich)

3. **Impact**
   - Welche Auswirkungen hat die Schwachstelle?
   - Welche Daten oder Systeme könnten kompromittiert werden?

4. **Umgebung**
   - Betriebssystem und Version
   - Python-Version
   - Tool-Version
   - Relevante Konfiguration

### **🎯 Beispiel-Report**
```
Subject: [SECURITY] Telegram Audio Downloader - API Key Exposure

Beschreibung:
Die .env-Datei wird unter bestimmten Umständen in den Download-Ordner kopiert,
wodurch API-Credentials exponiert werden könnten.

Reproduktion:
1. Tool mit spezieller Konfiguration starten
2. Download in Verzeichnis X durchführen
3. .env-Datei erscheint im Download-Ordner

Impact:
- API-Credentials könnten durch andere Benutzer eingesehen werden
- Potentieller Zugriff auf Telegram-Account des Benutzers

Umgebung:
- OS: Windows 11
- Python: 3.11.5
- Tool: v1.0.0
- Config: [relevante Teile ohne Credentials]
```

---

## 🔐 **Security Guidelines für Benutzer**

### **API-Credentials schützen**
```bash
# ✅ RICHTIG: .env-Datei verwenden
echo "API_ID=1234567" > .env
echo "API_HASH=abcdef..." >> .env
chmod 600 .env  # Linux/macOS: Nur Owner kann lesen

# ❌ FALSCH: Credentials in Scripts
telegram-audio-downloader download @gruppe  # Nutzt .env
```

### **Session-Dateien sichern**
```bash
# Session-Dateien enthalten Zugriffs-Tokens
ls *.session*
# Diese Dateien NIEMALS teilen oder in Git committen!

# .gitignore prüfen
grep -i session .gitignore
```

### **Docker-Sicherheit**
```bash
# ✅ RICHTIG: Secrets als Dateien mounten
docker run -v $(pwd)/.env:/app/.env telegram-audio-downloader

# ❌ FALSCH: Credentials als Environment Variables
docker run -e API_ID=1234567 telegram-audio-downloader
```

### **Download-Verzeichnis-Permissions**
```bash
# Downloads-Ordner nur für Owner lesbar machen
chmod 700 downloads/

# Bei sensiblen Inhalten: Verschlüsselung erwägen
# Beispiel mit encfs (Linux):
encfs ~/.encrypted_music ~/music
```

---

## 🛡️ **Sicherheitsfeatures des Tools**

### **Was wir bereits implementiert haben**

#### **✅ Sichere Credential-Verwaltung**
- API-Credentials nur über .env-Dateien
- Keine Hardcoding von Secrets im Code
- .env-Dateien in .gitignore ausgeschlossen

#### **✅ Input-Validation**
- Dateinamen werden bereinigt und validiert
- Pfad-Traversal-Angriffe verhindert
- Größen-Limits für Downloads

#### **✅ Rate-Limiting**
- Schutz vor API-Missbrauch
- Automatische Anpassung bei FloodWait-Fehlern
- Konfigurierbare Download-Limits

#### **✅ Secure Defaults**
- Minimale erforderliche Permissions
- Sichere Temp-File-Behandlung
- Automatische Cleanup-Mechanismen

#### **✅ Error Handling**
- Keine Credential-Exposition in Logs
- Strukturierte Fehlerbehandlung
- Sichere Fallback-Mechanismen

---

## 🔍 **Bekannte Sicherheits-Überlegungen**

### **⚠️ Inherente Risiken** (nicht behebbar)

#### **Telegram-API-Abhängigkeit**
- Tool benötigt Zugriff auf Ihr Telegram-Konto
- API-Credentials ermöglichen Account-Zugriff
- **Empfehlung**: Eigene App-ID erstellen, nicht teilen

#### **Local Storage**
- Heruntergeladene Dateien werden lokal gespeichert
- Session-Dateien enthalten Zugriffs-Tokens
- **Empfehlung**: Sichere Ordner-Permissions verwenden

#### **Network Traffic**
- Alle Downloads gehen über Telegram-Server
- Meta-Daten können von ISP/Proxy eingesehen werden
- **Empfehlung**: VPN verwenden bei sensiblen Inhalten

### **⚙️ Konfigurierbare Sicherheit**

#### **Logging-Level**
```ini
# config/default.ini
[logging]
level = INFO  # Nicht DEBUG in Production
log_api_calls = false  # API-Calls nicht loggen
log_file_paths = false  # Dateipfade nicht loggen
```

#### **Download-Restrictions**
```ini
[downloads]
max_file_size_mb = 100  # Limit für einzelne Dateien
allowed_extensions = mp3,flac,ogg,m4a,wav,opus  # Nur Audio
scan_downloads = true  # Malware-Scan (falls verfügbar)
```

---

## 📊 **Security Response Process**

### **Nach Erhalt eines Security-Reports**

1. **Bestätigung** (binnen 48h)
   - Report-Empfang bestätigen
   - Erste Einschätzung der Schwere

2. **Analyse** (binnen 1 Woche)
   - Schwachstelle reproduzieren
   - Impact-Analyse durchführen
   - Fix entwickeln

3. **Koordination** (nach Analyse)
   - Timeline für Fix koordinieren
   - Disclosure-Timeline festlegen
   - CVE-Nummer beantragen (falls nötig)

4. **Release** (koordiniert)
   - Security-Patch veröffentlichen
   - Advisory veröffentlichen
   - Reporter würdigen (falls gewünscht)

### **Disclosure Timeline**
- **Sofort**: Kritische Schwachstellen (RCE, Credential-Theft)
- **1-2 Wochen**: Hohe Schwachstellen (Privilege Escalation)
- **2-4 Wochen**: Mittlere Schwachstellen (Information Disclosure)
- **Nach Absprache**: Niedrige Schwachstellen

---

## 🏆 **Responsible Disclosure Anerkennung**

### **Hall of Fame**
Wir würdigen Security-Forscher, die verantwortungsvoll Schwachstellen melden:

| Reporter | Schwachstelle | Datum | Severity |
|----------|---------------|-------|----------|
| *Ihre Name hier* | *Beschreibung* | *Datum* | *Level* |

### **Anerkennung**
- **Nennung in Release Notes** (falls gewünscht)
- **Credits in SECURITY.md**
- **Danksagung auf Social Media**
- **Früher Zugang zu neuen Features**

---

## 📚 **Security Resources**

### **Best Practices für Benutzer**
- **[OWASP Top 10](https://owasp.org/www-project-top-ten/)** - Allgemeine Web-Sicherheit
- **[Python Security Guide](https://python-security.readthedocs.io/)** - Python-spezifische Sicherheit
- **[Telegram Security Guide](https://core.telegram.org/api/obtaining_api_id)** - Sichere API-Nutzung

### **Security Tools**
```bash
# Code-Analyse
bandit -r src/  # Python Security Linter
safety check    # Dependency Vulnerability Check
semgrep --config=auto src/  # SAST Analysis

# Dependency-Updates
pip-audit  # Python Dependency Audit
npm audit  # Wenn Node.js Dependencies vorhanden
```

### **Monitoring**
- **GitHub Security Advisories** abonnieren
- **Dependabot Alerts** aktivieren
- **Tool regelmäßig updaten**

---

## 📞 **Kontakt für Security-Fragen**

- **Allgemeine Security-Fragen**: GitHub Issues (öffentlich)
- **Vertrauliche Schwachstellen**: hannover84@msn.com
- **Dringende Sicherheitsprobleme**: hannover84@msn.com (Subject: [URGENT SECURITY])

---

**Vielen Dank für Ihre Hilfe dabei, das Telegram Audio Downloader Tool sicher zu halten! 🔒**