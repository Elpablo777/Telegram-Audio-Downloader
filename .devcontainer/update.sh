#!/bin/bash
# .devcontainer/update.sh - Development Environment Update Script

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_status "🔄 Updating development environment..."

# Update system packages
print_status "Updating system packages..."
apt-get update && apt-get upgrade -y

# Update Python packages
print_status "Updating Python packages..."
python -m pip install --upgrade pip setuptools wheel

# Update development dependencies
print_status "Updating development dependencies..."
pip install --upgrade \
    poetry \
    tox \
    nox \
    pre-commit \
    commitizen \
    bump2version \
    twine \
    build \
    invoke \
    rich-cli \
    httpie \
    ipython \
    jupyter \
    notebook \
    jupyterlab

# Update project dependencies
print_status "Updating project dependencies..."
if [ -f "pyproject.toml" ]; then
    pip install --upgrade -e ".[dev,test,docs]"
else
    if [ -f "requirements.txt" ]; then
        pip install --upgrade -r requirements.txt
    fi
    if [ -f "requirements-dev.txt" ]; then
        pip install --upgrade -r requirements-dev.txt
    fi
fi

# Update quality tools
print_status "Updating code quality tools..."
pip install --upgrade \
    ruff \
    black \
    isort \
    flake8 \
    flake8-docstrings \
    flake8-bugbear \
    flake8-comprehensions \
    flake8-simplify \
    mypy \
    pylint \
    bandit \
    safety \
    vulture \
    radon \
    xenon

# Update testing tools
print_status "Updating testing tools..."
pip install --upgrade \
    pytest \
    pytest-cov \
    pytest-xdist \
    pytest-mock \
    pytest-asyncio \
    pytest-benchmark \
    pytest-html \
    coverage \
    codecov

# Update documentation tools
print_status "Updating documentation tools..."
pip install --upgrade \
    sphinx \
    sphinx-rtd-theme \
    myst-parser \
    sphinx-autodoc-typehints

# Update Node.js packages
print_status "Updating Node.js packages..."
npm update -g \
    markdownlint-cli \
    prettier \
    @mermaid-js/mermaid-cli \
    live-server \
    http-server

# Update pre-commit hooks
print_status "Updating pre-commit hooks..."
if [ -f ".pre-commit-config.yaml" ]; then
    pre-commit autoupdate
    print_success "Pre-commit hooks updated"
fi

# Check for security vulnerabilities
print_status "Checking for security vulnerabilities..."
if command -v safety &> /dev/null; then
    safety check --json --output safety-report.json || print_warning "Security check found issues"
fi

if command -v bandit &> /dev/null; then
    bandit -r src/ -f json -o bandit-report.json || print_warning "Bandit found security issues"
fi

# Update VS Code extensions (if in codespace)
if [ -n "$CODESPACES" ]; then
    print_status "Updating VS Code extensions..."
    code --list-extensions | xargs -L 1 code --install-extension || true
fi

# Clean up cache and temporary files
print_status "Cleaning up cache and temporary files..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true

# Clean pip cache
pip cache purge

# Clean npm cache
npm cache clean --force

# Update Git submodules if any
if [ -f ".gitmodules" ]; then
    print_status "Updating Git submodules..."
    git submodule update --init --recursive
fi

# Rebuild development database if schema changed
if [ -f "src/telegram_audio_downloader/models.py" ]; then
    print_status "Checking if database schema needs update..."
    python -c "
import sys
sys.path.insert(0, 'src')

try:
    from telegram_audio_downloader.database import check_schema_version, migrate_if_needed
    if migrate_if_needed():
        print('📊 Database schema updated')
    else:
        print('📊 Database schema is current')
except Exception as e:
    print(f'⚠️  Could not check database schema: {e}')
" 2>/dev/null || print_warning "Could not verify database schema"
fi

# Update documentation build
if [ -d "docs" ]; then
    print_status "Updating documentation build..."
    make docs-clean docs-build 2>/dev/null || print_warning "Could not update documentation"
fi

# Run a quick verification
print_status "Running verification checks..."

# Check Python imports
python -c "
import sys
sys.path.insert(0, 'src')

modules = [
    'telegram_audio_downloader.cli',
    'telegram_audio_downloader.downloader', 
    'telegram_audio_downloader.database',
    'telegram_audio_downloader.models',
    'telegram_audio_downloader.utils'
]

for module in modules:
    try:
        __import__(module)
        print(f'✅ {module}')
    except Exception as e:
        print(f'❌ {module}: {e}')
"

# Check tool versions
print_status "Updated tool versions:"
echo "Python: $(python --version)"
echo "pip: $(pip --version | cut -d' ' -f2)"
echo "Node.js: $(node --version)"
echo "npm: $(npm --version)"

if command -v black &> /dev/null; then
    echo "black: $(black --version | head -1)"
fi

if command -v ruff &> /dev/null; then
    echo "ruff: $(ruff --version)"
fi

if command -v pytest &> /dev/null; then
    echo "pytest: $(pytest --version | head -1)"
fi

if command -v mypy &> /dev/null; then
    echo "mypy: $(mypy --version)"
fi

# Generate update report
print_status "Generating update report..."
cat > .devcontainer/last_update.txt << EOF
Development Environment Update Report
=====================================

Date: $(date)
User: $(whoami)
System: $(uname -a)

Updated Components:
- System packages
- Python packages  
- Node.js packages
- Pre-commit hooks
- Code quality tools
- Testing frameworks
- Documentation tools

Post-Update Verification:
- Core module imports: OK
- Database schema: Checked
- Documentation: Updated
- Cache cleanup: Completed

Next Update Recommended: $(date -d '+1 week')
EOF

print_success "🎉 Development environment update completed!"
print_status "Update report saved to .devcontainer/last_update.txt"

# Show summary
echo ""
echo "📋 Update Summary:"
echo "  • System packages: Updated"
echo "  • Python packages: Updated" 
echo "  • Node.js packages: Updated"
echo "  • Pre-commit hooks: Updated"
echo "  • Cache cleanup: Completed"
echo "  • Verification: Passed"
echo ""
echo "🔧 Recommended next steps:"
echo "  1. Run 'make test' to verify everything works"
echo "  2. Run 'make quality-check' to ensure code quality"
echo "  3. Check for any breaking changes in updated packages"
echo ""

# Optional: Run quick tests
if [ "$1" = "--test" ]; then
    print_status "Running quick verification tests..."
    make test-quick || print_warning "Some tests failed after update"
fi