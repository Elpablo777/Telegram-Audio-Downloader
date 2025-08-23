# 🛠 **02_TOOL_MASTERY.md: Der Tool-Katalog**
## **Maximale Nutzung aller MCP-Server für direkte API-Kontrolle**

---

## **2.1. GitHub MCP Server (`mcp_github_*`)**
**Prioritisiere die Verwendung dieser Tools für direkte Repository-Kontrolle, sofern verfügbar.**

### **Repository-Management**
```bash
mcp_github_get_file_contents     # Dateien lesen und analysieren
mcp_github_create_or_update_file # Einzelne Dateien erstellen/bearbeiten  
mcp_github_push_files           # Mehrere Dateien gleichzeitig pushen
mcp_github_create_repository    # Neue Repositories erstellen
mcp_github_fork_repository      # Repository-Forks erstellen
mcp_github_create_branch        # Feature-Branches erstellen
```

### **Issues & Pull Requests**
```bash
mcp_github_create_issue         # Issues automatisiert erstellen
mcp_github_list_issues         # Issue-Übersicht und Filtering
mcp_github_create_pull_request  # Pull Requests erstellen
mcp_github_merge_pull_request   # PRs automatisch mergen
mcp_github_search_issues        # Issues durchsuchen
mcp_github_get_pull_request     # PR-Details abrufen
```

### **Code-Analyse & History**
```bash
mcp_github_list_commits         # Commit-Historie analysieren
mcp_github_search_code          # Code-Suche im Repository
mcp_github_get_pull_request_files # Geänderte Dateien in PRs
```

---

## **2.2. Kontext- & Automatisierungs-Server**

### **Context7 MCP Server (`mcp_context7_*`)**
**Für aktuelle Library-Dokumentation**

```bash
mcp_context7_resolve-library-id # Library IDs identifizieren
mcp_context7_get-library-docs   # Neueste Dokumentation abrufen
```

### **Playwright Browser Automation (`mcp_playwright_*`)**
**Für Web-UI Tests und GitHub-Interface-Automation**

```bash
mcp_playwright_browser_navigate # GitHub UI automatisiert navigieren
mcp_playwright_browser_click    # Buttons/Links automatisch betätigen
mcp_playwright_browser_snapshot # Screenshots für Dokumentation
mcp_playwright_browser_type     # Formulare automatisch ausfüllen
```

---

## **2.3. Tool-Call Standards & Error Handling**

### **Standardisierte Tool-Call-Formate**
```json
{
  "tool": "mcp_github_create_or_update_file",
  "input": {"path":"README.md","content":"..."},
  "result": {"status":"ok","sha":"abc123"} | {"status":"error","code":502,"message":"..."}
}
```

### **Fallback-Strategien als Templates**
```yaml
Wenn mcp_github_create_or_update_file fehlschlägt:
  → Rückfall: Anleitung an Nutzer zur manuellen Erstellung
  → Retry-Policy: 3x mit exponential backoff
```

### **Rate limits / retries**
```yaml
Retry-Policy:
  - Max 3 Versuche
  - Exponential backoff (1s, 2s, 4s)
  - Bei Rate-Limit-Fehlern warten und erneut versuchen
```

### **Test-Mock-Mode**
```yaml
MCP_MODE: DRY_RUN | LIVE
  - DRY_RUN: Nur Pseudobefehle generieren
  - LIVE: Tatsächliche API-Calls ausführen
```

**Ziel: Maximale Automatisierung durch effiziente Nutzung der verfügbaren Tools.**