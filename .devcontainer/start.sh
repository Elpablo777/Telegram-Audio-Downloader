#!/bin/bash
# .devcontainer/start.sh - Development Environment Startup Script

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
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

print_status "🚀 Starting development services..."

# Source environment variables
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Start background services if needed
print_status "Checking for required services..."

# Check if Redis is available (for caching)
if command -v redis-cli &> /dev/null; then
    if ! redis-cli ping &> /dev/null; then
        print_warning "Redis not running, some caching features may be disabled"
    else
        print_success "Redis is running"
    fi
fi

# Check if PostgreSQL is available (for production-like testing)
if command -v psql &> /dev/null; then
    if ! pg_isready -h localhost -p 5432 &> /dev/null; then
        print_warning "PostgreSQL not running, using SQLite for development"
    else
        print_success "PostgreSQL is running"
    fi
fi

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    print_status "Activating virtual environment..."
    source venv/bin/activate
    print_success "Virtual environment activated"
fi

# Update PYTHONPATH
export PYTHONPATH="${PWD}/src:${PYTHONPATH}"

# Run pre-commit autoupdate
if [ -f ".pre-commit-config.yaml" ]; then
    print_status "Updating pre-commit hooks..."
    pre-commit autoupdate --quiet || print_warning "Could not update pre-commit hooks"
fi

# Create necessary directories
print_status "Ensuring development directories exist..."
mkdir -p \
    data/downloads \
    data/cache \
    data/logs \
    data/database \
    coverage \
    benchmarks/results

# Set permissions
chmod -R 777 data/ 2>/dev/null || true

# Check database connectivity
print_status "Checking database connectivity..."
python -c "
import sys
sys.path.insert(0, 'src')

try:
    from telegram_audio_downloader.database import test_connection
    if test_connection():
        print('✅ Database connection successful')
    else:
        print('⚠️  Database connection failed')
except Exception as e:
    print(f'⚠️  Could not test database: {e}')
" 2>/dev/null || print_warning "Could not verify database connection"

# Start development metrics collector if available
if [ -f "scripts/dev/metrics_collector.py" ]; then
    print_status "Starting development metrics collector..."
    nohup python scripts/dev/metrics_collector.py > data/logs/metrics.log 2>&1 &
    print_success "Metrics collector started in background"
fi

# Check for updates
print_status "Checking for dependency updates..."
if command -v pip-check &> /dev/null; then
    pip-check --quiet || print_warning "Some dependencies may have updates available"
fi

# Verify core functionality
print_status "Verifying core functionality..."
python -c "
import sys
sys.path.insert(0, 'src')

try:
    from telegram_audio_downloader.cli import main
    print('✅ CLI module importable')
except Exception as e:
    print(f'❌ CLI import failed: {e}')

try:
    from telegram_audio_downloader.downloader import AudioDownloader
    print('✅ AudioDownloader importable')
except Exception as e:
    print(f'❌ AudioDownloader import failed: {e}')

try:
    from telegram_audio_downloader.database import init_db
    print('✅ Database module importable')
except Exception as e:
    print(f'❌ Database import failed: {e}')
" || print_warning "Some core modules may have issues"

# Display useful information
print_status "Development environment ready!"
echo ""
echo "📋 Quick Reference:"
echo "  • Project root: ${PWD}"
echo "  • Python path: ${PYTHONPATH}"
echo "  • Database: $([ -f 'data/database/dev.db' ] && echo 'SQLite (dev.db)' || echo 'Not initialized')"
echo "  • Cache dir: data/cache"
echo "  • Log dir: data/logs"
echo ""
echo "🔧 Available commands:"
echo "  • tad --help           - Show CLI help"
echo "  • make test            - Run tests"
echo "  • make quality-check   - Run all quality checks"
echo "  • make docs-serve      - Serve documentation"
echo "  • scripts/dev/reset_db.sh - Reset database"
echo ""

# Show current Git status
if git rev-parse --git-dir > /dev/null 2>&1; then
    echo "📊 Git Status:"
    git status --porcelain | head -5
    if [ $(git status --porcelain | wc -l) -gt 5 ]; then
        echo "   ... and $(( $(git status --porcelain | wc -l) - 5 )) more files"
    fi
    echo ""
fi

# Show running processes related to development
print_status "Active development processes:"
ps aux | grep -E "(python|node|redis|postgres)" | grep -v grep | head -3 || echo "  No development processes found"

print_success "🎉 Development environment startup completed!"

# Optional: Start development server if requested
if [ "$1" = "--server" ]; then
    print_status "Starting development server..."
    python -m telegram_audio_downloader.server --dev
fi