# 🛠 **MCP-SERVER MAXIMALE NUTZUNG**
## **Tool-Katalog für direkte API-Kontrolle**

---

## **GitHub MCP Server (mcp_github_*)**
**IMMER verwenden wenn verfügbar! Direkte Repository-Kontrolle!**

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

## **Context7 MCP Server (mcp_context7_*)**
**Für aktuelle Library-Dokumentation**

```bash
mcp_context7_resolve-library-id # Library IDs identifizieren
mcp_context7_get-library-docs   # Neueste Dokumentation abrufen
```

---

## **Playwright Browser Automation (mcp_playwright_*)**
**Für Web-UI Tests und GitHub-Interface-Automation**

```bash
mcp_playwright_browser_navigate # GitHub UI automatisiert navigieren
mcp_playwright_browser_click    # Buttons/Links automatisch betätigen
mcp_playwright_browser_snapshot # Screenshots für Dokumentation
mcp_playwright_browser_type     # Formulare automatisch ausfüllen
```

---

## **MCP-FIRST WORKFLOW**

### **Parallelisierung**
```yaml
✅ PARALLEL ausführen:
  - Mehrere mcp_github_get_file_contents
  - Repository-Analysen
  - Code-Searches
  - Documentation-Retrieval

❌ SEQUENTIELL ausführen:
  - File-Editing-Operations
  - Git-Operations (commits, pushes)
  - Branch-Management
```

### **Error-Handling**
```yaml
Fallback-Strategien:
  - MCP nicht verfügbar → Manual Instructions
  - API-Limits → Batch-Processing
  - Permission-Issues → User-Guidance
```

**🎯 Maximale Automation durch intelligente Tool-Nutzung!**