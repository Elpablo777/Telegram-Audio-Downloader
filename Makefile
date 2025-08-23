# Makefile for Autonomous Development - Telegram Audio Downloader
# =================================================================

.PHONY: help setup dev test quality deploy monitor clean install
.DEFAULT_GOAL := help

# Colors for output
BOLD := \033[1m
RESET := \033[0m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
BLUE := \033[34m

# Project settings
PROJECT_NAME := telegram-audio-downloader
PYTHON := python
PIP := pip
PYTEST := pytest

# Help command
help: ## 📚 Show this help message
	@echo "$(BOLD)$(BLUE)Telegram Audio Downloader - Development Commands$(RESET)"
	@echo "=================================================="
	@echo ""
	@echo "$(BOLD)Quick Start:$(RESET)"
	@echo "  make setup      # Initial setup for development"
	@echo "  make dev        # Start development environment"
	@echo "  make test       # Run tests"
	@echo ""
	@echo "$(BOLD)Available Commands:$(RESET)"
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*##/ {printf "  $(GREEN)%-15s$(RESET) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Environment Setup
setup: ## 🚀 Complete development environment setup
	@echo "$(BOLD)$(BLUE)Setting up development environment...$(RESET)"
	@$(PYTHON) -m pip install --upgrade pip
	@$(PIP) install -e ".[dev,test,docs]"
	@$(PYTHON) scripts/setup_dev_environment.py
	@echo "$(BOLD)$(GREEN)✅ Setup completed! Run 'make dev' to start.$(RESET)"

install: ## 📦 Install package and dependencies
	@echo "$(BOLD)Installing package...$(RESET)"
	@$(PIP) install -e ".[dev,test,docs]"
	@echo "$(BOLD)$(GREEN)✅ Package installed$(RESET)"

# Development
dev: ## 💻 Start development environment
	@echo "$(BOLD)$(BLUE)Starting development environment...$(RESET)"
	@$(PYTHON) scripts/manage_credentials.py verify
	@$(PYTHON) -m telegram_audio_downloader --help
	@echo "$(BOLD)$(GREEN)✅ Development environment ready$(RESET)"

credentials: ## 🔑 Setup API credentials
	@$(PYTHON) scripts/manage_credentials.py setup

verify-credentials: ## ✅ Verify API credentials
	@$(PYTHON) scripts/manage_credentials.py verify

# Code Quality
quality: ## 🔍 Run all quality checks and auto-fixes
	@echo "$(BOLD)$(BLUE)Running quality checks...$(RESET)"
	@$(PYTHON) scripts/automation/auto_fix.py

format: ## 📝 Format code with black and isort
	@echo "$(BOLD)Formatting code...$(RESET)"
	@black src/ tests/ scripts/
	@isort src/ tests/ scripts/
	@echo "$(BOLD)$(GREEN)✅ Code formatted$(RESET)"

lint: ## 🔍 Run linting with ruff
	@echo "$(BOLD)Running linter...$(RESET)"
	@ruff check src/ tests/ scripts/
	@echo "$(BOLD)$(GREEN)✅ Linting completed$(RESET)"

lint-fix: ## 🔧 Run linting with auto-fix
	@echo "$(BOLD)Running linter with auto-fix...$(RESET)"
	@ruff check src/ tests/ scripts/ --fix
	@echo "$(BOLD)$(GREEN)✅ Linting with fixes completed$(RESET)"

type-check: ## 🎯 Run type checking with mypy
	@echo "$(BOLD)Running type checking...$(RESET)"
	@mypy src/
	@echo "$(BOLD)$(GREEN)✅ Type checking completed$(RESET)"

security: ## 🔒 Run security checks
	@echo "$(BOLD)Running security checks...$(RESET)"
	@bandit -r src/
	@safety check
	@echo "$(BOLD)$(GREEN)✅ Security checks completed$(RESET)"

# Testing
test: ## 🧪 Run unit tests
	@echo "$(BOLD)$(BLUE)Running tests...$(RESET)"
	@$(PYTEST) tests/ --tb=short
	@echo "$(BOLD)$(GREEN)✅ Tests completed$(RESET)"

test-verbose: ## 🧪 Run tests with verbose output
	@echo "$(BOLD)Running tests (verbose)...$(RESET)"
	@$(PYTEST) tests/ -v

test-fast: ## ⚡ Run fast tests only
	@echo "$(BOLD)Running fast tests...$(RESET)"
	@$(PYTEST) tests/ -m "not slow" --tb=short

test-slow: ## 🐌 Run slow tests only
	@echo "$(BOLD)Running slow tests...$(RESET)"
	@$(PYTEST) tests/ -m "slow" --tb=short

test-e2e: ## 🎯 Run end-to-end tests
	@echo "$(BOLD)Running E2E tests...$(RESET)"
	@$(PYTEST) tests/test_e2e.py -v
	@$(PYTHON) tests/test_e2e.py

test-performance: ## ⚡ Run performance tests
	@echo "$(BOLD)Running performance tests...$(RESET)"
	@$(PYTEST) tests/ -m "performance" --benchmark-only

coverage: ## 📊 Run tests with coverage report
	@echo "$(BOLD)$(BLUE)Running tests with coverage...$(RESET)"
	@$(PYTEST) tests/ --cov=src --cov-report=html --cov-report=term-missing
	@echo "$(BOLD)$(GREEN)✅ Coverage report generated in htmlcov/$(RESET)"

coverage-xml: ## 📊 Generate XML coverage report
	@$(PYTEST) tests/ --cov=src --cov-report=xml

# Documentation
docs: ## 📚 Build documentation
	@echo "$(BOLD)$(BLUE)Building documentation...$(RESET)"
	@sphinx-build -W -b html docs/sphinx docs/build
	@echo "$(BOLD)$(GREEN)✅ Documentation built in docs/build/$(RESET)"

docs-serve: ## 🌐 Serve documentation locally
	@echo "$(BOLD)Starting documentation server...$(RESET)"
	@echo "$(BOLD)$(BLUE)📖 Documentation available at: http://localhost:8000$(RESET)"
	@cd docs/build && $(PYTHON) -m http.server 8000

docs-auto: ## 📚 Build docs with auto-reload
	@echo "$(BOLD)Starting documentation with auto-reload...$(RESET)"
	@sphinx-autobuild docs/sphinx docs/build --host 0.0.0.0 --port 8000

# Monitoring
monitor: ## 🏥 Run health monitoring check
	@echo "$(BOLD)$(BLUE)Running health check...$(RESET)"
	@$(PYTHON) scripts/monitoring/continuous_monitor.py check

monitor-start: ## 🔄 Start continuous monitoring
	@echo "$(BOLD)Starting continuous monitoring...$(RESET)"
	@$(PYTHON) scripts/monitoring/continuous_monitor.py start

monitor-dashboard: ## 📊 Start monitoring dashboard
	@echo "$(BOLD)Starting monitoring dashboard...$(RESET)"
	@echo "$(BOLD)$(BLUE)🏥 Dashboard available at: http://localhost:8080$(RESET)"
	@$(PYTHON) scripts/monitoring/dashboard.py

status: ## 📋 Check development environment status
	@echo "$(BOLD)$(BLUE)Checking environment status...$(RESET)"
	@$(PYTHON) scripts/dev_tools.py check

# Build and Deploy
build: ## 📦 Build package
	@echo "$(BOLD)$(BLUE)Building package...$(RESET)"
	@$(PYTHON) -m build
	@echo "$(BOLD)$(GREEN)✅ Package built in dist/$(RESET)"

deploy: ## 🚀 Autonomous deployment
	@echo "$(BOLD)$(BLUE)Starting autonomous deployment...$(RESET)"
	@$(PYTHON) scripts/automation/auto_deploy.py

deploy-test: ## 🧪 Deploy to test PyPI
	@echo "$(BOLD)Deploying to test PyPI...$(RESET)"
	@twine upload --repository testpypi dist/*

deploy-prod: ## 🚀 Deploy to production PyPI
	@echo "$(BOLD)$(RED)Deploying to production PyPI...$(RESET)"
	@twine upload dist/*

# Docker
docker-build: ## 🐳 Build Docker image
	@echo "$(BOLD)Building Docker image...$(RESET)"
	@docker build -t $(PROJECT_NAME) .
	@echo "$(BOLD)$(GREEN)✅ Docker image built$(RESET)"

docker-run: ## 🐳 Run Docker container
	@echo "$(BOLD)Running Docker container...$(RESET)"
	@docker run -it --rm -v $(PWD)/downloads:/app/downloads $(PROJECT_NAME)

docker-compose-up: ## 🐳 Start Docker Compose services
	@echo "$(BOLD)Starting Docker Compose services...$(RESET)"
	@docker-compose up -d

docker-compose-down: ## 🐳 Stop Docker Compose services
	@docker-compose down

# Database
db-init: ## 🗄️ Initialize database
	@echo "$(BOLD)Initializing database...$(RESET)"
	@$(PYTHON) -c "from telegram_audio_downloader.database import init_db; import asyncio; asyncio.run(init_db())"
	@echo "$(BOLD)$(GREEN)✅ Database initialized$(RESET)"

db-reset: ## 🗄️ Reset database
	@echo "$(BOLD)$(YELLOW)Resetting database...$(RESET)"
	@rm -f data/downloads.db
	@$(MAKE) db-init

# Git and Pre-commit
pre-commit: ## 🪝 Install pre-commit hooks
	@echo "$(BOLD)Installing pre-commit hooks...$(RESET)"
	@pre-commit install
	@pre-commit install --hook-type commit-msg
	@echo "$(BOLD)$(GREEN)✅ Pre-commit hooks installed$(RESET)"

pre-commit-run: ## 🪝 Run pre-commit on all files
	@echo "$(BOLD)Running pre-commit on all files...$(RESET)"
	@pre-commit run --all-files

# Clean up
clean: ## 🧹 Clean up build artifacts and cache
	@echo "$(BOLD)$(BLUE)Cleaning up...$(RESET)"
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@rm -rf build/ dist/ .coverage htmlcov/ .tox/ .nox/
	@echo "$(BOLD)$(GREEN)✅ Cleanup completed$(RESET)"

clean-all: clean ## 🧹 Clean everything including virtual environment
	@echo "$(BOLD)$(YELLOW)Cleaning everything...$(RESET)"
	@rm -rf venv/ .venv/
	@echo "$(BOLD)$(GREEN)✅ Deep cleanup completed$(RESET)"

# Workflow shortcuts
fix-test: quality test ## 🔄 Quick fix and test cycle

full-check: quality coverage security ## 🔍 Run all checks (quality, coverage, security)

release-check: full-check build ## 🚀 Pre-release checks (quality, tests, build)

# Development workflow
dev-setup: setup pre-commit credentials ## 🎯 Complete development setup

dev-start: verify-credentials dev ## ▶️ Start development session

dev-test: format lint-fix test ## 🔄 Development test cycle

# Environment information
info: ## ℹ️ Show environment information
	@echo "$(BOLD)$(BLUE)Environment Information:$(RESET)"
	@echo "Project: $(PROJECT_NAME)"
	@echo "Python: $(shell $(PYTHON) --version)"
	@echo "Pip: $(shell $(PIP) --version)"
	@echo "Working Directory: $(shell pwd)"
	@echo "Git Branch: $(shell git branch --show-current 2>/dev/null || echo 'Not a git repository')"
	@echo "Git Status: $(shell git status --porcelain 2>/dev/null | wc -l || echo 'N/A') modified files"

# Advanced commands
tox: ## 🧪 Run tests with tox (multiple Python versions)
	@echo "$(BOLD)Running tests with tox...$(RESET)"
	@tox

nox: ## 🧪 Run tests with nox (modern alternative to tox)
	@echo "$(BOLD)Running tests with nox...$(RESET)"
	@nox

benchmark: ## ⚡ Run performance benchmarks
	@echo "$(BOLD)Running performance benchmarks...$(RESET)"
	@$(PYTEST) tests/ --benchmark-only --benchmark-sort=mean

profile: ## 📊 Profile application performance
	@echo "$(BOLD)Profiling application...$(RESET)"
	@$(PYTHON) -m cProfile -o profile.stats -m telegram_audio_downloader --help
	@$(PYTHON) -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative').print_stats(20)"

# CI/CD simulation
ci-local: ## 🔄 Simulate CI/CD pipeline locally
	@echo "$(BOLD)$(BLUE)Simulating CI/CD pipeline...$(RESET)"
	@$(MAKE) clean
	@$(MAKE) install
	@$(MAKE) quality
	@$(MAKE) test
	@$(MAKE) security
	@$(MAKE) build
	@echo "$(BOLD)$(GREEN)✅ CI/CD simulation completed$(RESET)"

# Quick commands for different user types
beginner: setup dev-start ## 👶 Quick start for beginners
	@echo "$(BOLD)$(GREEN)✅ Ready for development! Try 'make test' next.$(RESET)"

developer: dev-setup dev-test ## 👨‍💻 Setup for experienced developers
	@echo "$(BOLD)$(GREEN)✅ Developer environment ready!$(RESET)"

contributor: dev-setup full-check ## 🤝 Setup for contributors
	@echo "$(BOLD)$(GREEN)✅ Contributor environment ready!$(RESET)"

maintainer: dev-setup ci-local ## 👑 Setup for maintainers
	@echo "$(BOLD)$(GREEN)✅ Maintainer environment ready!$(RESET)"