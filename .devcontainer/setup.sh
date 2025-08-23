#!/bin/bash
# .devcontainer/setup.sh - Development Environment Setup Script

set -e

echo "🚀 Setting up Telegram Audio Downloader Development Environment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

# Update system packages
print_status "Updating system packages..."
apt-get update && apt-get upgrade -y

# Install system dependencies
print_status "Installing system dependencies..."
apt-get install -y \
    build-essential \
    curl \
    wget \
    git \
    vim \
    nano \
    htop \
    tree \
    jq \
    sqlite3 \
    postgresql-client \
    redis-tools \
    ffmpeg \
    sox \
    mediainfo \
    exiftool \
    shellcheck \
    yamllint \
    pandoc \
    graphviz \
    plantuml \
    mermaid-cli

# Install Python dependencies
print_status "Setting up Python environment..."

# Upgrade pip and install build tools
python -m pip install --upgrade pip setuptools wheel

# Install development dependencies
print_status "Installing Python development dependencies..."
pip install \
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

# Install project dependencies
print_status "Installing project dependencies..."
if [ -f "pyproject.toml" ]; then
    pip install -e ".[dev,test,docs]"
else
    print_warning "pyproject.toml not found, installing from requirements..."
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
    fi
    if [ -f "requirements-dev.txt" ]; then
        pip install -r requirements-dev.txt
    fi
fi

# Install additional development tools
print_status "Installing additional development tools..."
pip install \
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
    xenon \
    pytest \
    pytest-cov \
    pytest-xdist \
    pytest-mock \
    pytest-asyncio \
    pytest-benchmark \
    pytest-html \
    coverage \
    codecov \
    sphinx \
    sphinx-rtd-theme \
    myst-parser \
    sphinx-autodoc-typehints

# Install Node.js dependencies for documentation
print_status "Installing Node.js dependencies..."
npm install -g \
    markdownlint-cli \
    prettier \
    @mermaid-js/mermaid-cli \
    live-server \
    http-server

# Setup Git configuration
print_status "Configuring Git..."
git config --global init.defaultBranch main
git config --global pull.rebase false
git config --global core.autocrlf input
git config --global core.safecrlf warn

# Install Git hooks
print_status "Setting up Git hooks..."
if [ -f ".pre-commit-config.yaml" ]; then
    pre-commit install
    pre-commit install --hook-type commit-msg
    print_success "Pre-commit hooks installed"
fi

# Create development directories
print_status "Creating development directories..."
mkdir -p \
    data/downloads \
    data/cache \
    data/logs \
    data/database \
    .vscode/snippets \
    scripts/dev \
    scripts/deploy \
    scripts/utils \
    docs/build \
    tests/fixtures \
    tests/data \
    coverage \
    .pytest_cache

# Set permissions
chmod -R 755 scripts/
chmod -R 777 data/

# Create environment file if it doesn't exist
print_status "Setting up environment configuration..."
if [ ! -f ".env" ]; then
    cp .env.example .env 2>/dev/null || cat > .env << 'EOF'
# Development Environment Configuration
DEVELOPMENT=true
DEBUG=true
LOG_LEVEL=DEBUG

# Telegram API (Get from https://my.telegram.org/apps)
API_ID=your_api_id_here
API_HASH=your_api_hash_here
SESSION_NAME=dev_session

# Database
DATABASE_URL=sqlite:///data/database/dev.db

# Storage
DOWNLOAD_DIR=data/downloads
CACHE_DIR=data/cache
LOG_DIR=data/logs

# Performance
MAX_CONCURRENT_DOWNLOADS=3
RATE_LIMIT_DELAY=1.0

# Testing
TEST_GROUP=@test_group
TEST_DATABASE_URL=sqlite:///data/database/test.db

# Monitoring
ENABLE_METRICS=true
METRICS_PORT=9090
HEALTH_CHECK_PORT=8080
EOF
    print_success "Created .env file template"
else
    print_success ".env file already exists"
fi

# Setup VS Code workspace settings
print_status "Configuring VS Code workspace..."
mkdir -p .vscode

cat > .vscode/settings.json << 'EOF'
{
    "python.defaultInterpreterPath": "/usr/local/bin/python",
    "python.terminal.activateEnvironment": true,
    "python.formatting.provider": "black",
    "python.formatting.blackArgs": ["--config", "pyproject.toml"],
    "python.sortImports.args": ["--profile", "black"],
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.linting.flake8Enabled": true,
    "python.linting.mypyEnabled": true,
    "python.testing.pytestEnabled": true,
    "python.testing.unittestEnabled": false,
    "python.testing.pytestArgs": [
        "tests",
        "--verbose",
        "--tb=short"
    ],
    "files.associations": {
        "*.env": "properties",
        "*.ini": "ini",
        "Dockerfile*": "dockerfile",
        "*.dockerfile": "dockerfile"
    },
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true,
        "source.fixAll": true
    },
    "editor.rulers": [88],
    "terminal.integrated.defaultProfile.linux": "bash",
    "git.autofetch": true,
    "markdownlint.config": {
        "default": true,
        "MD013": false,
        "MD033": false
    }
}
EOF

# Create launch configuration
cat > .vscode/launch.json << 'EOF'
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Current File",
            "type": "python",
            "request": "launch",
            "program": "${file}",
            "console": "integratedTerminal",
            "cwd": "${workspaceFolder}",
            "env": {
                "PYTHONPATH": "${workspaceFolder}/src"
            }
        },
        {
            "name": "Python: CLI Download",
            "type": "python",
            "request": "launch",
            "module": "telegram_audio_downloader.cli",
            "args": ["download", "@test_group", "--limit", "5", "--debug"],
            "console": "integratedTerminal",
            "cwd": "${workspaceFolder}",
            "env": {
                "PYTHONPATH": "${workspaceFolder}/src"
            }
        },
        {
            "name": "Python: Run Tests",
            "type": "python",
            "request": "launch",
            "module": "pytest",
            "args": ["tests/", "-v"],
            "console": "integratedTerminal",
            "cwd": "${workspaceFolder}",
            "env": {
                "PYTHONPATH": "${workspaceFolder}/src"
            }
        },
        {
            "name": "Python: Performance Tests",
            "type": "python",
            "request": "launch",
            "module": "pytest",
            "args": ["tests/test_performance.py", "-v", "--benchmark-only"],
            "console": "integratedTerminal",
            "cwd": "${workspaceFolder}",
            "env": {
                "PYTHONPATH": "${workspaceFolder}/src"
            }
        }
    ]
}
EOF

# Create tasks configuration
cat > .vscode/tasks.json << 'EOF'
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "Run Tests",
            "type": "shell",
            "command": "pytest",
            "args": ["tests/", "-v"],
            "group": "test",
            "presentation": {
                "reveal": "always",
                "panel": "new"
            }
        },
        {
            "label": "Format Code",
            "type": "shell",
            "command": "make",
            "args": ["format"],
            "group": "build",
            "presentation": {
                "reveal": "silent"
            }
        },
        {
            "label": "Lint Code",
            "type": "shell",
            "command": "make",
            "args": ["lint"],
            "group": "build",
            "presentation": {
                "reveal": "always"
            }
        },
        {
            "label": "Type Check",
            "type": "shell",
            "command": "make",
            "args": ["type-check"],
            "group": "build",
            "presentation": {
                "reveal": "always"
            }
        },
        {
            "label": "Security Check",
            "type": "shell",
            "command": "make",
            "args": ["security-check"],
            "group": "build",
            "presentation": {
                "reveal": "always"
            }
        },
        {
            "label": "Quality Check (All)",
            "type": "shell",
            "command": "make",
            "args": ["quality-check"],
            "group": "build",
            "presentation": {
                "reveal": "always",
                "panel": "new"
            }
        },
        {
            "label": "Build Documentation",
            "type": "shell",
            "command": "make",
            "args": ["docs-build"],
            "group": "build",
            "presentation": {
                "reveal": "always"
            }
        },
        {
            "label": "Start Development Server",
            "type": "shell",
            "command": "python",
            "args": ["-m", "telegram_audio_downloader.server", "--dev"],
            "group": "build",
            "presentation": {
                "reveal": "always",
                "panel": "new"
            },
            "isBackground": true
        }
    ]
}
EOF

# Create Python snippets
cat > .vscode/snippets/python.json << 'EOF'
{
    "Async Function": {
        "prefix": "adef",
        "body": [
            "async def ${1:function_name}(${2:args}) -> ${3:return_type}:",
            "    \"\"\"${4:Description}.",
            "    ",
            "    Args:",
            "        ${5:arg}: ${6:Description}",
            "    ",
            "    Returns:",
            "        ${7:Description}",
            "    \"\"\"",
            "    ${0:pass}"
        ],
        "description": "Create async function with docstring"
    },
    "Test Function": {
        "prefix": "tdef",
        "body": [
            "def test_${1:function_name}(${2:fixtures}):",
            "    \"\"\"Test ${3:description}.\"\"\"",
            "    # Arrange",
            "    ${4:setup}",
            "    ",
            "    # Act",
            "    ${5:action}",
            "    ",
            "    # Assert",
            "    ${0:assertion}"
        ],
        "description": "Create test function with AAA pattern"
    },
    "Async Test Function": {
        "prefix": "atdef",
        "body": [
            "@pytest.mark.asyncio",
            "async def test_${1:function_name}(${2:fixtures}):",
            "    \"\"\"Test ${3:description}.\"\"\"",
            "    # Arrange",
            "    ${4:setup}",
            "    ",
            "    # Act",
            "    ${5:action}",
            "    ",
            "    # Assert",
            "    ${0:assertion}"
        ],
        "description": "Create async test function"
    },
    "Logger Setup": {
        "prefix": "logger",
        "body": [
            "from telegram_audio_downloader.logging_config import get_logger",
            "",
            "logger = get_logger(__name__)"
        ],
        "description": "Import and setup logger"
    },
    "Type Hints Import": {
        "prefix": "typing",
        "body": [
            "from typing import Any, Dict, List, Optional, Union, Tuple, Callable, Awaitable"
        ],
        "description": "Common typing imports"
    }
}
EOF

# Setup development scripts
print_status "Creating development scripts..."

cat > scripts/dev/reset_db.sh << 'EOF'
#!/bin/bash
# Reset development database
set -e

echo "🗑️  Resetting development database..."

# Remove existing database
rm -f data/database/dev.db
rm -f data/database/test.db

# Recreate database
python -c "
from src.telegram_audio_downloader.database import init_db, create_tables
init_db('data/database/dev.db')
create_tables()
print('✅ Development database reset complete')
"

echo "✅ Database reset completed"
EOF

cat > scripts/dev/install_hooks.sh << 'EOF'
#!/bin/bash
# Install development hooks
set -e

echo "🪝 Installing development hooks..."

# Install pre-commit hooks
pre-commit install
pre-commit install --hook-type commit-msg

# Install custom Git hooks
cat > .git/hooks/pre-push << 'HOOK'
#!/bin/bash
# Pre-push hook to run quality checks

echo "🔍 Running quality checks before push..."

# Run tests
if ! make test-quick; then
    echo "❌ Tests failed. Push aborted."
    exit 1
fi

# Run linting
if ! make lint-check; then
    echo "❌ Linting failed. Push aborted."
    exit 1
fi

echo "✅ Quality checks passed. Pushing..."
HOOK

chmod +x .git/hooks/pre-push

echo "✅ Development hooks installed"
EOF

cat > scripts/dev/benchmark.sh << 'EOF'
#!/bin/bash
# Run performance benchmarks
set -e

echo "🏃 Running performance benchmarks..."

# Create benchmark directory
mkdir -p benchmarks/results

# Run benchmarks
python -m pytest tests/test_performance.py \
    --benchmark-only \
    --benchmark-json=benchmarks/results/benchmark_$(date +%Y%m%d_%H%M%S).json \
    --benchmark-histogram=benchmarks/results/histogram

echo "✅ Benchmarks completed. Check benchmarks/results/"
EOF

# Make scripts executable
chmod +x scripts/dev/*.sh

# Setup documentation build
print_status "Setting up documentation build..."
mkdir -p docs/build docs/source/_static docs/source/_templates

# Initialize Sphinx if conf.py doesn't exist
if [ ! -f "docs/sphinx/conf.py" ]; then
    sphinx-quickstart -q \
        --sep \
        --project="Telegram Audio Downloader" \
        --author="Pablo" \
        --release="1.0.0" \
        --language="en" \
        --makefile \
        --batchfile \
        docs/sphinx
fi

# Create development database
print_status "Setting up development database..."
python -c "
import os
import sys
sys.path.insert(0, 'src')

try:
    from telegram_audio_downloader.database import init_db
    db_path = 'data/database/dev.db'
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    init_db(db_path)
    print('✅ Development database initialized')
except Exception as e:
    print(f'⚠️  Could not initialize database: {e}')
"

# Setup development shell aliases
print_status "Setting up shell aliases..."
cat >> ~/.bashrc << 'EOF'

# Telegram Audio Downloader Development Aliases
alias tad='python -m telegram_audio_downloader.cli'
alias tad-test='pytest tests/ -v'
alias tad-lint='make lint'
alias tad-format='make format'
alias tad-check='make quality-check'
alias tad-docs='make docs-serve'
alias tad-bench='scripts/dev/benchmark.sh'
alias tad-reset='scripts/dev/reset_db.sh'

# Quick navigation
alias cdtad='cd /workspaces/Telegram-Audio-Downloader'
alias cdsrc='cd /workspaces/Telegram-Audio-Downloader/src'
alias cdtest='cd /workspaces/Telegram-Audio-Downloader/tests'
alias cddocs='cd /workspaces/Telegram-Audio-Downloader/docs'

# Development utilities
alias ll='ls -la'
alias la='ls -la'
alias ..='cd ..'
alias ...='cd ../..'
alias grep='grep --color=auto'
alias tree='tree -I "__pycache__|*.pyc|.git|node_modules|.pytest_cache|.mypy_cache"'

export PYTHONPATH="/workspaces/Telegram-Audio-Downloader/src:$PYTHONPATH"
EOF

# Create welcome message
print_status "Creating development welcome message..."
cat > ~/.motd << 'EOF'
╔═══════════════════════════════════════════════════════════════════════════════╗
║                     🎵 Telegram Audio Downloader 🎵                          ║
║                           Development Environment                             ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║  🚀 Quick Start:                                                              ║
║    tad --help                    # Show CLI help                             ║
║    tad-test                      # Run tests                                 ║
║    tad-check                     # Run quality checks                        ║
║    tad-docs                      # Serve documentation                       ║
║                                                                               ║
║  📁 Navigation:                                                               ║
║    cdtad                         # Go to project root                        ║
║    cdsrc                         # Go to source code                         ║
║    cdtest                        # Go to tests                               ║
║                                                                               ║
║  🔧 Development:                                                              ║
║    make help                     # Show all available commands               ║
║    code .                        # Open in VS Code                           ║
║    scripts/dev/reset_db.sh       # Reset development database                ║
║                                                                               ║
║  📚 Documentation:                                                            ║
║    docs/API_REFERENCE.md         # API documentation                         ║
║    docs/TUTORIALS.md             # Tutorials and examples                    ║
║    docs/TROUBLESHOOTING.md       # Troubleshooting guide                     ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
EOF

# Display welcome message on login
echo 'cat ~/.motd 2>/dev/null || true' >> ~/.bashrc

# Final setup verification
print_status "Verifying setup..."

# Check Python installation
python --version
pip --version

# Check key tools
echo "📦 Installed tools:"
python -c "
import subprocess
import sys

tools = [
    ('black', 'Code formatter'),
    ('ruff', 'Fast linter'),
    ('pytest', 'Testing framework'),
    ('mypy', 'Type checker'),
    ('pre-commit', 'Git hooks'),
    ('sphinx', 'Documentation'),
]

for tool, description in tools:
    try:
        result = subprocess.run([tool, '--version'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f'  ✅ {tool:<12} - {description}')
        else:
            print(f'  ❌ {tool:<12} - Not working properly')
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print(f'  ❌ {tool:<12} - Not installed')
"

print_success "🎉 Development environment setup completed!"
print_status "Next steps:"
echo "  1. Configure your .env file with Telegram API credentials"
echo "  2. Run 'make test' to verify everything works"
echo "  3. Run 'tad --help' to see available commands"
echo "  4. Open project in VS Code with 'code .'"
echo ""
echo "Happy coding! 🚀"