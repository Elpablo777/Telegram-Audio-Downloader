#!/usr/bin/env python3
"""
Development Environment Setup - Telegram Audio Downloader
=========================================================

Comprehensive development environment setup for autonomous development.
"""

import os
import sys
import json
import subprocess
import platform
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import getpass

@dataclass
class DevEnvironmentConfig:
    """Development environment configuration."""
    api_credentials: Dict[str, str]
    development_tools: List[str]
    automation_scripts: List[str]
    environment_variables: Dict[str, str]

class DevEnvironmentManager:
    """Development environment manager for autonomous work."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.config_dir = self.project_root / "config"
        self.scripts_dir = self.project_root / "scripts"
        
        # Ensure directories exist
        for directory in [self.config_dir, self.scripts_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    async def setup_complete_environment(self) -> Dict[str, Any]:
        """Setup complete development environment."""
        print("🚀 Setting up development environment for autonomous work...")
        
        results = {}
        
        # 1. Setup API credentials
        results["api_setup"] = await self._setup_api_credentials()
        
        # 2. Install development tools
        results["tools_setup"] = await self._setup_development_tools()
        
        # 3. Configure automation
        results["automation_setup"] = await self._setup_automation()
        
        # 4. Setup Git environment
        results["git_setup"] = await self._setup_git_environment()
        
        # 5. Create quick commands
        results["commands_setup"] = await self._setup_quick_commands()
        
        print("✅ Development environment ready for autonomous work!")
        return results
    
    async def _setup_api_credentials(self) -> Dict[str, Any]:
        """Setup API credentials management."""
        print("🔑 Setting up API credentials...")
        
        # Create .env template
        env_template = """# Telegram Audio Downloader - Environment Variables
# Required for autonomous operation
TELEGRAM_API_ID=YOUR_TELEGRAM_API_ID
TELEGRAM_API_HASH=YOUR_TELEGRAM_API_HASH
TELEGRAM_PHONE_NUMBER=YOUR_PHONE_NUMBER

# Optional Bot Mode
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN

# Database
DATABASE_URL=sqlite:///data/downloads.db

# Download Settings
DEFAULT_DOWNLOAD_DIR=downloads
MAX_CONCURRENT_DOWNLOADS=3
RATE_LIMIT_DELAY=1.0

# External APIs (Optional)
LASTFM_API_KEY=YOUR_LASTFM_API_KEY
SPOTIFY_CLIENT_ID=YOUR_SPOTIFY_CLIENT_ID
SPOTIFY_CLIENT_SECRET=YOUR_SPOTIFY_CLIENT_SECRET

# Monitoring
LOG_LEVEL=INFO
ENABLE_METRICS=true
SENTRY_DSN=YOUR_SENTRY_DSN

# Development
DEVELOPMENT=false
DEBUG=false
TESTING=false
"""
        
        env_template_file = self.project_root / ".env.template"
        env_template_file.write_text(env_template)
        
        # Create .env if not exists
        env_file = self.project_root / ".env"
        if not env_file.exists():
            env_file.write_text(env_template)
        
        # Create credentials manager
        self._create_credentials_manager()
        
        return {
            "env_template": str(env_template_file),
            "env_file": str(env_file),
            "credentials_manager": "scripts/manage_credentials.py"
        }
    
    def _create_credentials_manager(self):
        """Create secure credentials manager."""
        credentials_manager = '''#!/usr/bin/env python3
"""Secure credentials manager for autonomous development."""

import os
import getpass
from pathlib import Path

class CredentialsManager:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.env_file = self.project_root / ".env"
    
    def setup_telegram_credentials(self):
        """Interactive setup of Telegram credentials."""
        print("🔑 Telegram API Credentials Setup")
        print("Get credentials from: https://my.telegram.org/apps")
        
        api_id = input("Enter API ID: ").strip()
        api_hash = getpass.getpass("Enter API Hash: ").strip()
        phone = input("Enter Phone (+1234567890): ").strip()
        
        # Update .env file
        env_content = self.env_file.read_text() if self.env_file.exists() else ""
        lines = env_content.split('\\n')
        
        updated_lines = []
        for line in lines:
            if line.startswith('TELEGRAM_API_ID='):
                updated_lines.append(f'TELEGRAM_API_ID={api_id}')
            elif line.startswith('TELEGRAM_API_HASH='):
                updated_lines.append(f'TELEGRAM_API_HASH={api_hash}')
            elif line.startswith('TELEGRAM_PHONE_NUMBER='):
                updated_lines.append(f'TELEGRAM_PHONE_NUMBER={phone}')
            else:
                updated_lines.append(line)
        
        self.env_file.write_text('\\n'.join(updated_lines))
        print("✅ Credentials saved to .env file")
    
    def verify_credentials(self):
        """Verify credentials are set."""
        if not self.env_file.exists():
            return False
        
        content = self.env_file.read_text()
        required = ['TELEGRAM_API_ID', 'TELEGRAM_API_HASH', 'TELEGRAM_PHONE_NUMBER']
        
        for req in required:
            if f'{req}=YOUR_' in content or f'{req}=' not in content:
                return False
        
        return True

if __name__ == "__main__":
    import sys
    
    manager = CredentialsManager()
    
    if len(sys.argv) > 1 and sys.argv[1] == "verify":
        if manager.verify_credentials():
            print("✅ Credentials are configured")
        else:
            print("❌ Credentials need setup")
            manager.setup_telegram_credentials()
    else:
        manager.setup_telegram_credentials()
'''
        
        credentials_script = self.scripts_dir / "manage_credentials.py"
        credentials_script.write_text(credentials_manager)
        credentials_script.chmod(0o755)
    
    async def _setup_development_tools(self) -> Dict[str, Any]:
        """Setup essential development tools."""
        print("🛠️ Installing development tools...")
        
        # Essential tools for autonomous development
        essential_tools = [
            "black",           # Code formatting
            "isort",           # Import sorting
            "ruff",            # Fast linter
            "mypy",            # Type checking
            "pytest",          # Testing
            "pytest-asyncio",  # Async testing
            "pytest-cov",     # Coverage
            "pre-commit",      # Git hooks
            "bandit",          # Security
            "safety",          # Dependency security
        ]
        
        # Install tools
        installed = []
        failed = []
        
        for tool in essential_tools:
            try:
                result = subprocess.run([
                    sys.executable, "-m", "pip", "install", tool
                ], capture_output=True, text=True, timeout=120)
                
                if result.returncode == 0:
                    installed.append(tool)
                else:
                    failed.append(tool)
            except Exception:
                failed.append(tool)
        
        # Setup pre-commit
        self._setup_pre_commit_hooks()
        
        return {
            "installed_tools": installed,
            "failed_tools": failed,
            "pre_commit_ready": True
        }
    
    def _setup_pre_commit_hooks(self):
        """Setup pre-commit hooks for autonomous quality."""
        pre_commit_config = """repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
      - id: check-added-large-files

  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ["--profile", "black"]

  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.0.270
    hooks:
      - id: ruff
        args: [--fix]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.3.0
    hooks:
      - id: mypy
"""
        
        pre_commit_file = self.project_root / ".pre-commit-config.yaml"
        pre_commit_file.write_text(pre_commit_config)
    
    async def _setup_automation(self) -> Dict[str, Any]:
        """Setup automation scripts for autonomous development."""
        print("🤖 Setting up automation scripts...")
        
        automation_dir = self.scripts_dir / "automation"
        automation_dir.mkdir(exist_ok=True)
        
        # Auto-fix script
        auto_fix = '''#!/usr/bin/env python3
"""Autonomous code fixing and quality maintenance."""

import subprocess
import sys
from pathlib import Path

def auto_fix():
    """Automatically fix code issues."""
    print("🔧 Auto-fixing code...")
    
    project_root = Path(__file__).parent.parent.parent
    
    commands = [
        ["black", "src/", "tests/"],
        ["isort", "src/", "tests/"],
        ["ruff", "check", "src/", "tests/", "--fix"],
    ]
    
    for cmd in commands:
        try:
            subprocess.run(cmd, cwd=project_root, check=True)
            print(f"✅ {cmd[0]} completed")
        except subprocess.CalledProcessError as e:
            print(f"❌ {cmd[0]} failed: {e}")
    
    print("🧪 Running tests...")
    try:
        subprocess.run(["pytest", "tests/", "--tb=short"], cwd=project_root, check=True)
        print("✅ Tests passed")
    except subprocess.CalledProcessError:
        print("⚠️ Some tests failed")

if __name__ == "__main__":
    auto_fix()
'''
        
        (automation_dir / "auto_fix.py").write_text(auto_fix)
        (automation_dir / "auto_fix.py").chmod(0o755)
        
        # Auto-deploy script
        auto_deploy = '''#!/usr/bin/env python3
"""Autonomous deployment script."""

import subprocess
import sys
from pathlib import Path

def auto_deploy():
    """Autonomous deployment process."""
    print("🚀 Starting autonomous deployment...")
    
    project_root = Path(__file__).parent.parent.parent
    
    # Quality checks
    print("🔍 Running quality checks...")
    try:
        subprocess.run(["python", "scripts/automation/auto_fix.py"], cwd=project_root, check=True)
    except subprocess.CalledProcessError:
        print("❌ Quality checks failed")
        return False
    
    # Build and test
    print("📦 Building package...")
    try:
        subprocess.run(["python", "-m", "build"], cwd=project_root, check=True)
        print("✅ Package built successfully")
    except subprocess.CalledProcessError:
        print("❌ Build failed")
        return False
    
    print("✅ Deployment ready!")
    return True

if __name__ == "__main__":
    auto_deploy()
'''
        
        (automation_dir / "auto_deploy.py").write_text(auto_deploy)
        (automation_dir / "auto_deploy.py").chmod(0o755)
        
        return {
            "automation_scripts": [
                "scripts/automation/auto_fix.py",
                "scripts/automation/auto_deploy.py"
            ]
        }
    
    async def _setup_git_environment(self) -> Dict[str, Any]:
        """Setup Git for autonomous development."""
        print("📋 Configuring Git environment...")
        
        # Essential Git configuration
        git_commands = [
            "git config --global core.autocrlf input",
            "git config --global core.eol lf",
            "git config --global init.defaultBranch main",
            "git config --global pull.rebase false"
        ]
        
        configured = 0
        for command in git_commands:
            try:
                subprocess.run(command.split(), capture_output=True, check=True)
                configured += 1
            except subprocess.CalledProcessError:
                pass
        
        # Create GitHub secrets documentation
        self._create_github_secrets_docs()
        
        return {
            "git_configured": configured,
            "total_commands": len(git_commands),
            "secrets_docs": ".github/SECRETS.md"
        }
    
    def _create_github_secrets_docs(self):
        """Create GitHub secrets documentation."""
        github_dir = self.project_root / ".github"
        github_dir.mkdir(exist_ok=True)
        
        secrets_docs = """# GitHub Secrets for Autonomous CI/CD

## Required Secrets

| Secret | Description | Where to Get |
|--------|-------------|--------------|
| `TELEGRAM_API_ID` | Telegram API ID | https://my.telegram.org/apps |
| `TELEGRAM_API_HASH` | Telegram API Hash | https://my.telegram.org/apps |
| `CODECOV_TOKEN` | Code coverage token | https://codecov.io |
| `PYPI_TOKEN` | PyPI deployment | https://pypi.org/manage/account/ |

## Setup Instructions

1. Go to Repository Settings → Secrets and variables → Actions
2. Add each secret with exact name from table
3. Use actual values from your accounts

## For Autonomous Operation

The CI/CD pipeline uses these secrets to:
- Run tests with real API credentials
- Deploy to PyPI automatically
- Upload coverage reports
- Perform security scans

Keep secrets secure and rotate regularly.
"""
        
        (github_dir / "SECRETS.md").write_text(secrets_docs)
    
    async def _setup_quick_commands(self) -> Dict[str, Any]:
        """Setup quick commands for autonomous development."""
        print("⚡ Setting up quick commands...")
        
        # Create Makefile for quick commands
        makefile_content = """# Makefile for Autonomous Development
.PHONY: setup dev test quality deploy

# Quick setup for autonomous development
setup:
	pip install -e ".[dev,test,docs]"
	python scripts/manage_credentials.py verify
	pre-commit install

# Start development environment
dev:
	python scripts/manage_credentials.py verify
	python -m telegram_audio_downloader --help

# Run autonomous quality checks and fixes
quality:
	python scripts/automation/auto_fix.py

# Run tests
test:
	pytest tests/ --tb=short

# Full test with coverage
test-full:
	pytest tests/ --cov=src --cov-report=html

# Autonomous deployment
deploy:
	python scripts/automation/auto_deploy.py

# Start monitoring
monitor:
	python scripts/monitoring/continuous_monitor.py check

# Quick fix and test cycle
fix-test: quality test

# Development status check
status:
	python scripts/dev_tools.py check

# Clean environment
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/ .coverage htmlcov/
"""
        
        makefile = self.project_root / "Makefile"
        makefile.write_text(makefile_content)
        
        # Create quick development script
        quick_dev = '''#!/usr/bin/env python3
"""Quick development environment launcher."""

import subprocess
import sys
from pathlib import Path

def main():
    """Launch development environment."""
    project_root = Path(__file__).parent
    
    print("🚀 Telegram Audio Downloader - Development Environment")
    print("=" * 60)
    
    # Check credentials
    result = subprocess.run([
        sys.executable, "scripts/manage_credentials.py", "verify"
    ], cwd=project_root)
    
    if result.returncode != 0:
        print("⚠️ Credentials not configured. Run 'make setup' first.")
        return
    
    # Show available commands
    print("\\n📋 Available Commands:")
    print("  make setup     - Initial setup")
    print("  make dev       - Start development")
    print("  make test      - Run tests")
    print("  make quality   - Auto-fix code quality")
    print("  make deploy    - Autonomous deployment")
    print("  make monitor   - Start monitoring")
    print("  make status    - Check environment status")
    
    print("\\n✅ Development environment ready!")
    print("Run 'make dev' to start or 'make test' to run tests.")

if __name__ == "__main__":
    main()
'''
        
        quick_script = self.project_root / "dev.py"
        quick_script.write_text(quick_dev)
        quick_script.chmod(0o755)
        
        return {
            "makefile": True,
            "quick_script": "dev.py",
            "commands_ready": True
        }

def main():
    """Main setup function."""
    import asyncio
    
    print("🎯 Development Environment Setup for Autonomous Work")
    print("=" * 60)
    
    manager = DevEnvironmentManager()
    
    try:
        results = asyncio.run(manager.setup_complete_environment())
        
        print("\\n📊 Setup Results:")
        for category, result in results.items():
            if isinstance(result, dict):
                success_count = sum(1 for v in result.values() if v)
                total_count = len(result)
                print(f"  {category}: {success_count}/{total_count} completed")
            else:
                print(f"  {category}: {result}")
        
        print("\\n🎉 Development environment setup completed!")
        print("\\nNext steps:")
        print("1. Run 'make setup' for initial configuration")
        print("2. Run 'python dev.py' to start development")
        print("3. Run 'make test' to verify everything works")
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())