#!/bin/bash

# 🚀 WIKI-SOFORT-SETUP - Alle Inhalte automatisch übertragen!
# Führe dieses Script aus: chmod +x wiki_quick_setup.sh && ./wiki_quick_setup.sh

echo "🎵 Telegram Audio Downloader - Wiki Quick Setup"
echo "==============================================="
echo ""

# Farben für schöne Ausgabe
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${BLUE}📘 $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

# Check if git is available
if ! command -v git &> /dev/null; then
    echo -e "${RED}❌ Git ist nicht installiert! Bitte installieren Sie Git zuerst.${NC}"
    exit 1
fi

# Check if we're in the right directory
if [ ! -d "wiki" ]; then
    echo -e "${RED}❌ Wiki-Verzeichnis nicht gefunden! Bitte im Projekt-Root ausführen.${NC}"
    exit 1
fi

print_info "Wiki-Repository klonen..."

# Temporary directory for wiki
WIKI_TEMP_DIR="wiki_temp_setup"
if [ -d "$WIKI_TEMP_DIR" ]; then
    rm -rf "$WIKI_TEMP_DIR"
fi

# Clone the wiki repository
if git clone "https://github.com/Elpablo777/Telegram-Audio-Downloader.wiki.git" "$WIKI_TEMP_DIR" 2>/dev/null; then
    print_success "Wiki-Repository erfolgreich geklont!"
    
    cd "$WIKI_TEMP_DIR"
    
    print_info "Wiki-Inhalte kopieren..."
    
    # Copy all wiki files
    wiki_files=(
        "Home.md"
        "Installation-Guide.md"
        "Quick-Start.md"
        "FAQ.md"
        "CLI-Commands.md"
        "Architecture-Overview.md"
        "Best-Practices.md"
        "Performance-Tuning.md"
        "Troubleshooting.md"
    )
    
    copied_files=0
    for file in "${wiki_files[@]}"; do
        if [ -f "../wiki/$file" ]; then
            cp "../wiki/$file" .
            print_success "Kopiert: $file"
            ((copied_files++))
        else
            print_warning "Nicht gefunden: wiki/$file"
        fi
    done
    
    print_info "Git-Konfiguration..."
    git config --local user.name "Elpablo777"
    git config --local user.email "hannover84@msn.com"
    
    print_info "Änderungen committen..."
    git add .
    
    if git diff --staged --quiet; then
        print_warning "Keine Änderungen zu committen (Dateien bereits vorhanden)"
    else
        git commit -m "📚 Wiki Setup: Umfassende Dokumentation hinzugefügt

✨ Wiki-Seiten hinzugefügt:
- Home: Haupt-Navigation und Überblick
- Installation Guide: Multi-Plattform Installationsanleitung
- Quick Start: 5-Minuten Schnellstart-Guide
- FAQ: Häufig gestellte Fragen
- CLI Commands: Vollständige Befehls-Referenz
- Architecture Overview: Technische Architektur (20+ Seiten)
- Best Practices: Optimierungs-Leitfaden (15+ Seiten)
- Performance Tuning: Performance-Optimierung
- Troubleshooting: Umfassende Problemlösungen

📊 Features:
- Rich Navigation mit Emoji-Icons
- Cross-References zwischen Seiten
- Praktische Code-Beispiele
- Multi-Platform Anleitungen
- Umfassende Troubleshooting-Sektion
- Performance-Optimierungs-Guides

Erstellt von: Qoder AI Assistant für Elpablo777"
        
        print_success "Änderungen committed!"
    fi
    
    print_info "Wiki zu GitHub pushen..."
    
    if git push origin master 2>/dev/null || git push origin main 2>/dev/null; then
        cd ..
        rm -rf "$WIKI_TEMP_DIR"
        
        echo ""
        echo "🎉 WIKI ERFOLGREICH EINGERICHTET!"
        echo "=================================="
        echo ""
        print_success "Wiki ist jetzt verfügbar unter:"
        echo "   🔗 https://github.com/Elpablo777/Telegram-Audio-Downloader/wiki"
        echo ""
        print_success "Übertragene Wiki-Seiten ($copied_files):"
        for file in "${wiki_files[@]}"; do
            if [ -f "wiki/$file" ]; then
                pagename=$(echo "$file" | sed 's/.md$//')
                echo "   📄 $pagename"
            fi
        done
        echo ""
        print_info "Wiki-Features:"
        echo "   📚 Vollständige Benutzer-Dokumentation"
        echo "   🔧 Entwickler-Ressourcen"
        echo "   🎯 Quick-Start Guides"
        echo "   🆘 Umfassender Support"
        echo "   🏗️ Technische Architektur-Details"
        echo ""
        print_success "ALLES FERTIG! Schauen Sie sich Ihr neues Wiki an! 🎵✨"
        
    else
        print_warning "Push fehlgeschlagen - möglicherweise haben Sie keine Schreibrechte"
        print_info "Alternative: Kopieren Sie den Inhalt manuell:"
        echo ""
        cd ..
        rm -rf "$WIKI_TEMP_DIR"
        
        echo "📋 MANUELLE KOPIER-ANWEISUNGEN:"
        echo "==============================="
        for file in "${wiki_files[@]}"; do
            if [ -f "wiki/$file" ]; then
                pagename=$(echo "$file" | sed 's/.md$//')
                echo "🔄 wiki/$file → Wiki-Seite: $pagename"
            fi
        done
        echo ""
        print_info "1. Gehen Sie zu: https://github.com/Elpablo777/Telegram-Audio-Downloader/wiki"
        print_info "2. Erstellen Sie neue Seiten mit den Namen oben"
        print_info "3. Kopieren Sie den Inhalt aus den entsprechenden Dateien"
    fi
    
else
    echo -e "${RED}❌ Konnte Wiki-Repository nicht klonen!${NC}"
    echo ""
    print_warning "Das Wiki wurde möglicherweise noch nicht richtig aktiviert."
    echo ""
    print_info "LÖSUNG: Wiki manuell einrichten"
    echo "==============================="
    echo "1. Gehen Sie zu: https://github.com/Elpablo777/Telegram-Audio-Downloader/wiki"
    echo "2. Erstellen Sie eine weitere Seite (falls nur eine existiert)"
    echo "3. Führen Sie dieses Script erneut aus"
    echo ""
    print_info "ALTERNATIVE: Manuelles Wiki-Setup"
    echo "================================="
    
    wiki_files=(
        "Home.md"
        "Installation-Guide.md"
        "Quick-Start.md"
        "FAQ.md"
        "CLI-Commands.md"
        "Architecture-Overview.md"
        "Best-Practices.md"
        "Performance-Tuning.md"
        "Troubleshooting.md"
    )
    
    echo "📄 Kopieren Sie diese Dateien manuell ins Wiki:"
    for file in "${wiki_files[@]}"; do
        if [ -f "wiki/$file" ]; then
            pagename=$(echo "$file" | sed 's/.md$//')
            echo "   📋 wiki/$file → Wiki-Seite: $pagename"
        fi
    done
fi

echo ""
print_info "Bei Problemen schauen Sie in: WIKI_ACTIVATION_GUIDE.md"
echo ""
print_success "Happy Documenting! 🎵✨"