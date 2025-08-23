# 📚 Wiki Setup Instructions

The GitHub Wiki has been prepared with comprehensive documentation. Follow these steps to activate it:

## 🎯 Quick Setup

### 1. Enable Wiki in Repository Settings
1. Go to your repository: https://github.com/Elpablo777/Telegram-Audio-Downloader
2. Click on **Settings** tab
3. Scroll down to **Features** section
4. Check ✅ **Wikis** to enable the Wiki feature

### 2. Initialize the Wiki
1. Navigate to the **Wiki** tab in your repository
2. Click **"Create the first page"**
3. Add any temporary content (e.g., "Setting up wiki...")
4. Click **"Save Page"**

### 3. Run the Automated Setup
```bash
# Make the script executable
chmod +x scripts/setup_wiki.sh

# Run the wiki setup
./scripts/setup_wiki.sh
```

## 📖 What Gets Created

The script will automatically create these wiki pages:

### 🏠 **Main Pages**
- **Home** - Main navigation hub with highlights
- **Installation Guide** - Multi-platform setup instructions
- **Quick Start** - 5-minute getting started guide
- **FAQ** - Common questions and answers

### 🔧 **Reference Documentation**
- **CLI Commands** - Complete command reference
- **Configuration** - Detailed configuration options
- **Architecture Overview** - Technical system design
- **Best Practices** - Optimization guidelines

### 🆘 **Support Pages**
- **Troubleshooting** - Problem solving guide
- **Error Codes** - Error message explanations

## 🎨 **Features**

- ✅ **Rich Navigation** with emoji-based organization
- ✅ **Cross-references** between related pages
- ✅ **Code examples** with syntax highlighting
- ✅ **Multi-platform instructions** (Windows, macOS, Linux)
- ✅ **Comprehensive troubleshooting** section
- ✅ **Performance optimization** guides
- ✅ **Security best practices**

## 🔄 Manual Alternative

If the automated script doesn't work, you can manually copy the content:

1. **Source Files**: All wiki content is in the `wiki/` directory
2. **Target**: Copy each `.md` file to the GitHub Wiki editor
3. **Navigation**: Update the Home page with links to all other pages

### File Mapping:
```
wiki/Home.md                 → Home
wiki/Installation-Guide.md   → Installation-Guide  
wiki/FAQ.md                  → FAQ
wiki/Architecture-Overview.md → Architecture-Overview
wiki/Best-Practices.md       → Best-Practices
```

## 🎉 Result

After setup, your wiki will be available at:
**https://github.com/Elpablo777/Telegram-Audio-Downloader/wiki**

The wiki provides:
- 📚 Complete user documentation
- 🔧 Developer resources  
- 🎯 Quick start guides
- 🆘 Comprehensive support
- 🏗️ Technical architecture details

## 💡 Tips

- **Update regularly**: Keep wiki content synchronized with code changes
- **Community contributions**: Enable community editing for collaborative documentation
- **Search optimization**: Use clear headings and keywords for better discoverability
- **Cross-linking**: Link related pages together for better navigation

---

**Happy documenting!** 🎵✨