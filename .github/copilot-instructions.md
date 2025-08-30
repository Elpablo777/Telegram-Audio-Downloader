# Telegram Audio Downloader

Telegram Audio Downloader is a comprehensive Python application for downloading and managing audio files from Telegram groups. The project features extensive testing infrastructure, multi-platform CI/CD, and professional development tooling.

**ALWAYS reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.**

## Working Effectively

### Bootstrap, Build, and Test the Repository

**CRITICAL TIMING EXPECTATIONS:**
- **NEVER CANCEL**: Dependency installation can take 10-20 minutes due to network timeouts and complex builds (especially telethon). Set timeout to 30+ minutes.
- **NEVER CANCEL**: Full test suite takes 5-10 minutes with 60+ test files (447 test items). Set timeout to 15+ minutes.
- **NEVER CANCEL**: Security scanning takes 3-5 minutes. Set timeout to 10+ minutes.
- **NEVER CANCEL**: Docker builds take 15-30 minutes due to multi-stage builds and Python dependency compilation. Set timeout to 45+ minutes.

#### Essential Setup Commands:
```bash
# Core build tools (30 seconds)
python -m pip install --upgrade pip setuptools wheel

# Development tools (2-3 minutes) - Install these first as they work reliably
pip install pytest ruff mypy bandit

# Core app dependencies (WARNING: May fail due to network issues)
pip install -r requirements.txt  # Takes 10-20 minutes, may timeout on telethon
# Alternative if full install fails:
pip install python-dotenv click rich tqdm

# Complete development setup via Makefile (WARNING: Often fails)
make setup  # Takes 15-25 minutes, NEVER CANCEL, frequently fails on network timeouts
```

#### Working Commands (Validated):
```bash
# These commands work and have been tested:
make help                    # Show all available commands (instant)
make lint                    # Run ruff linter (under 1 minute)
make info                    # Show environment info (instant)
pytest tests/test_simple.py  # Run simple test (under 1 minute)
ruff check .                 # Direct linting (under 1 minute)
bandit -r .                  # Security scan (3-5 minutes)
mypy --version              # Type checker (instant)
```

#### Commands That Often Fail:
```bash
# These frequently fail due to network timeouts or missing dependencies:
make setup                   # Fails on pip install timeouts
pip install -r requirements.txt  # Fails on telethon build
make format                  # Fails if black not installed
python telegram_audio_downloader.py  # Fails without telethon
safety check                 # Fails due to typer version conflict
```

### Project Structure

#### Source Code:
- **`src/telegram_audio_downloader/`** - Main application source code (60+ modules)
- **`telegram_audio_downloader.py`** - Root-level entry point script
- **`tests/`** - Comprehensive test suite (60+ test files, 447 test items)

#### Key Configuration Files:
- **`Makefile`** - Development automation with 40+ commands
- **`pyproject.toml`** - Modern Python packaging and tool configuration
- **`setup.py`** - Legacy setuptools configuration (still used)
- **`requirements.txt`** - Production dependencies
- **`.github/workflows/`** - CI/CD pipelines (14 workflow files)

#### Build System:
- **Python 3.11+** required (tested with 3.11, 3.12)
- **Dual build system**: setuptools + pyproject.toml
- **Package manager**: pip (no poetry/pipenv)
- **Virtual environments**: Standard venv (no conda)

## Development Workflow

### Quality Checks
```bash
# Code quality (under 1 minute each, all work reliably)
ruff check .                 # Fast modern linter
ruff check . --fix          # Auto-fix issues
mypy src/ --ignore-missing-imports  # Type checking

# Security (3-5 minutes, NEVER CANCEL)
bandit -r . -f json         # Security analysis
# Note: safety check currently broken due to typer dependency conflict
```

### Testing
```bash
# Simple tests (under 1 minute)
pytest tests/test_simple.py -v

# Full test suite (5-10 minutes, NEVER CANCEL)
pytest tests/ -v            # May have import errors without dependencies

# Specific test categories (if dependencies available):
pytest tests/ -m unit       # Unit tests only
pytest tests/ -m integration  # Integration tests
pytest tests/ -m performance  # Performance tests
```

### Docker Support
```bash
# Docker build (15-30 minutes, NEVER CANCEL, often fails on dependencies)
docker buildx build --platform linux/amd64 -t telegram-audio-downloader:test . --load

# Docker compose (if build succeeds)
docker-compose up -d
docker-compose down
```

## Validation Scenarios

### CRITICAL: Manual Validation Requirements

**Always manually validate changes by testing these core scenarios:**

1. **Basic Import Test**:
   ```bash
   python -c "import sys; sys.path.append('src'); import telegram_audio_downloader"
   # Expected: Should import without errors (may fail without dependencies)
   ```

2. **CLI Help Test**:
   ```bash
   python -m src.telegram_audio_downloader.cli --help
   # Expected: Should show CLI help or fail gracefully with dependency error
   ```

3. **Configuration Test**:
   ```bash
   # Create test .env file
   echo "TELEGRAM_API_ID=123456" > .env.test
   echo "TELEGRAM_API_HASH=test_hash" >> .env.test
   # Verify configuration loading (requires python-dotenv)
   ```

4. **Database Schema Test**:
   ```bash
   # Test database module import
   python -c "import sys; sys.path.append('src'); from telegram_audio_downloader import database"
   # Expected: Should import or fail with clear dependency error
   ```

### Network and Dependency Issues

**CRITICAL WARNINGS:**
- **PyPI timeouts are frequent** - pip install commands often fail with ReadTimeoutError
- **Telethon installation is problematic** - requires compilation and often fails
- **Docker builds frequently timeout** during pip install phase
- **CI/CD includes fallback strategies** for dependency installation failures

**Working around dependency issues:**
```bash
# Install core dev tools first (these work reliably):
pip install pytest ruff mypy bandit

# Then try application dependencies individually:
pip install python-dotenv click rich tqdm aiofiles

# Skip problematic dependencies like telethon for basic validation
```

## CI/CD Pipeline

### GitHub Actions Workflows (Validated Working):
- **Multi-OS testing**: Ubuntu (primary), Windows
- **Python versions**: 3.11 (primary), 3.12
- **Security scanning**: CodeQL, bandit, safety (with fallbacks)
- **Code quality**: ruff, mypy
- **Docker builds**: Conditional on labels/main branch

### CI/CD Timing (From .github/workflows/ci.yml):
- **Dependency installation**: 2-5 minutes
- **Security scans**: 3-5 minutes, NEVER CANCEL
- **Code quality checks**: under 1 minute
- **Docker builds**: 15-25 minutes, NEVER CANCEL
- **Full CI pipeline**: 10-30 minutes total

### Pre-commit Hooks:
```bash
# Install pre-commit (if available)
pip install pre-commit
pre-commit install

# Manual pre-commit run
make pre-commit-run
```

## Common Development Tasks

### Code Quality Workflow:
```bash
# 1. Lint code (under 1 minute)
ruff check .

# 2. Fix auto-fixable issues
ruff check . --fix

# 3. Type check (1-2 minutes)
mypy src/ --ignore-missing-imports

# 4. Security scan (3-5 minutes, NEVER CANCEL)
bandit -r . -f json
```

### Testing Workflow:
```bash
# 1. Run simple tests first
pytest tests/test_simple.py -v

# 2. If dependencies available, run full suite (5-10 minutes, NEVER CANCEL)
pytest tests/ -v --tb=short

# 3. Coverage (if pytest-cov available)
pytest tests/ --cov=src --cov-report=term
```

### Release Preparation:
```bash
# 1. Full quality checks
make lint  # or ruff check .
mypy src/ --ignore-missing-imports
bandit -r .

# 2. Test suite (if dependencies available)
pytest tests/

# 3. Build package
python -m build  # requires build package

# 4. Docker build test (15-30 minutes, NEVER CANCEL)
docker buildx build -t telegram-audio-downloader:test .
```

## Known Issues and Workarounds

### Dependency Installation Issues:
- **telethon**: Often fails to build, requires retries
- **safety**: Currently broken due to typer version conflict
- **Docker builds**: Frequently timeout on pip install phase

### Network Timeouts:
- **PyPI connections**: Use `--timeout 300` for pip commands
- **Docker builds**: May need multiple attempts
- **CI/CD**: Has built-in retry mechanisms

### Platform Differences:
- **Windows**: PowerShell scripts available in `scripts/`
- **Linux/macOS**: Bash scripts and Makefile commands
- **Docker**: Multi-platform builds supported

## Troubleshooting

### If pip install fails:
```bash
# Try with longer timeout
pip install --timeout 300 -r requirements.txt

# Or install core dependencies individually
pip install python-dotenv click rich tqdm
```

### If tests fail with import errors:
```bash
# Install minimal test dependencies
pip install pytest

# Run only tests that don't require app dependencies
pytest tests/test_simple.py
```

### If Docker build fails:
```bash
# Check if it's a network issue
docker buildx build --no-cache -t test .

# Or try building without pip cache
docker build --build-arg PIP_NO_CACHE_DIR=1 -t test .
```

## Development Environment Tiers

### Beginner (Basic validation):
```bash
pip install pytest ruff mypy bandit
pytest tests/test_simple.py
ruff check .
```

### Developer (Full environment):
```bash
make setup  # May fail, use alternative commands
pip install -r requirements.txt  # 10-20 minutes, may timeout
pytest tests/  # 5-10 minutes
```

### Maintainer (Production-ready):
```bash
make ci-local  # Full CI simulation locally
docker buildx build .  # 15-30 minutes
make release-check
```

## Important File Locations

### Configuration:
- `.env.example` - Environment variable template
- `config/` - Configuration file examples
- `pyproject.toml` - All tool configurations

### Documentation:
- `README.md` - Comprehensive project documentation
- `docs/` - Additional documentation
- `wiki/` - GitHub wiki setup files

### Automation:
- `Makefile` - 40+ development commands
- `.github/workflows/` - CI/CD pipelines
- `scripts/` - Utility scripts

### Tests:
- `tests/` - 60+ test files, organized by functionality
- `conftest.py` - Pytest configuration
- `pytest.ini` - Test runner settings

**Remember: ALWAYS use appropriate timeouts (15+ minutes for builds, 10+ minutes for tests) and NEVER CANCEL long-running operations as they are expected to take significant time.**