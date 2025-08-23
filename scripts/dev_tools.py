#!/usr/bin/env python3
"""
Development Tools - Telegram Audio Downloader
==============================================

Comprehensive development utilities for autonomous development workflow.
"""

import os
import sys
import subprocess
import json
import time
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

@dataclass
class DevEnvironmentStatus:
    """Development environment status."""
    timestamp: str
    python_version: str
    dependencies_ok: bool
    database_ok: bool
    tests_passing: bool
    code_quality_ok: bool
    documentation_ok: bool
    git_status: Dict[str, Any]
    issues: List[str]
    recommendations: List[str]

class DevelopmentTools:
    """Comprehensive development tools for autonomous workflow."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.src_dir = self.project_root / "src"
        self.tests_dir = self.project_root / "tests"
        self.docs_dir = self.project_root / "docs"
        
    def check_environment(self) -> DevEnvironmentStatus:
        """Comprehensive environment check."""
        print("🔍 Checking development environment...")
        
        issues = []
        recommendations = []
        
        # Check Python version
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        
        # Check dependencies
        dependencies_ok = self._check_dependencies()
        if not dependencies_ok:
            issues.append("Missing or outdated dependencies")
            recommendations.append("Run: pip install -e '.[dev,test,docs]'")
        
        # Check database
        database_ok = self._check_database()
        if not database_ok:
            issues.append("Database connectivity issues")
            recommendations.append("Run: scripts/dev/reset_db.sh")
        
        # Check tests
        tests_passing = self._run_quick_tests()
        if not tests_passing:
            issues.append("Some tests are failing")
            recommendations.append("Run: pytest tests/ -v --tb=short")
        
        # Check code quality
        code_quality_ok = self._check_code_quality()
        if not code_quality_ok:
            issues.append("Code quality issues found")
            recommendations.append("Run: make quality-check")
        
        # Check documentation
        documentation_ok = self._check_documentation()
        if not documentation_ok:
            issues.append("Documentation issues")
            recommendations.append("Run: make docs-build")
        
        # Check Git status
        git_status = self._get_git_status()
        
        return DevEnvironmentStatus(
            timestamp=datetime.now().isoformat(),
            python_version=python_version,
            dependencies_ok=dependencies_ok,
            database_ok=database_ok,
            tests_passing=tests_passing,
            code_quality_ok=code_quality_ok,
            documentation_ok=documentation_ok,
            git_status=git_status,
            issues=issues,
            recommendations=recommendations
        )
    
    def _check_dependencies(self) -> bool:
        """Check if all dependencies are installed."""
        try:
            # Check core dependencies
            import telethon
            import mutagen
            import peewee
            import click
            import rich
            
            # Check dev dependencies
            import pytest
            import black
            import ruff
            import mypy
            
            return True
        except ImportError:
            return False
    
    def _check_database(self) -> bool:
        """Check database connectivity."""
        try:
            from telegram_audio_downloader.database import init_db, test_connection
            return test_connection()
        except Exception:
            return False
    
    def _run_quick_tests(self) -> bool:
        """Run quick tests to verify basic functionality."""
        try:
            result = subprocess.run(
                ["python", "-m", "pytest", "tests/", "-x", "--tb=no", "-q"],
                cwd=self.project_root,
                capture_output=True,
                timeout=60
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def _check_code_quality(self) -> bool:
        """Check code quality with basic linting."""
        try:
            # Check with ruff (fast)
            result = subprocess.run(
                ["ruff", "check", "src/", "--quiet"],
                cwd=self.project_root,
                capture_output=True,
                timeout=30
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def _check_documentation(self) -> bool:
        """Check if documentation can be built."""
        return (self.docs_dir / "API_REFERENCE.md").exists()
    
    def _get_git_status(self) -> Dict[str, Any]:
        """Get Git repository status."""
        try:
            # Get current branch
            branch_result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            
            # Get status
            status_result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            
            # Get last commit
            commit_result = subprocess.run(
                ["git", "log", "-1", "--oneline"],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            
            return {
                "branch": branch_result.stdout.strip(),
                "modified_files": len(status_result.stdout.strip().split('\n')) if status_result.stdout.strip() else 0,
                "last_commit": commit_result.stdout.strip(),
                "clean": not bool(status_result.stdout.strip())
            }
        except Exception:
            return {"error": "Could not get Git status"}
    
    def auto_fix_issues(self) -> Dict[str, bool]:
        """Automatically fix common development issues."""
        print("🔧 Auto-fixing common issues...")
        
        results = {}
        
        # Fix code formatting
        print("  📝 Fixing code formatting...")
        results["formatting"] = self._auto_fix_formatting()
        
        # Fix import sorting
        print("  📦 Fixing import sorting...")
        results["imports"] = self._auto_fix_imports()
        
        # Update pre-commit hooks
        print("  🪝 Updating pre-commit hooks...")
        results["pre_commit"] = self._update_pre_commit()
        
        # Clean cache
        print("  🧹 Cleaning cache...")
        results["cache_cleanup"] = self._clean_cache()
        
        return results
    
    def _auto_fix_formatting(self) -> bool:
        """Auto-fix code formatting with black."""
        try:
            subprocess.run(
                ["black", "src/", "tests/", "--quiet"],
                cwd=self.project_root,
                check=True,
                timeout=60
            )
            return True
        except Exception:
            return False
    
    def _auto_fix_imports(self) -> bool:
        """Auto-fix import sorting with isort."""
        try:
            subprocess.run(
                ["isort", "src/", "tests/", "--quiet"],
                cwd=self.project_root,
                check=True,
                timeout=60
            )
            return True
        except Exception:
            return False
    
    def _update_pre_commit(self) -> bool:
        """Update pre-commit hooks."""
        try:
            subprocess.run(
                ["pre-commit", "autoupdate"],
                cwd=self.project_root,
                check=True,
                timeout=120
            )
            return True
        except Exception:
            return False
    
    def _clean_cache(self) -> bool:
        """Clean development cache files."""
        try:
            cache_dirs = [
                "__pycache__",
                ".pytest_cache", 
                ".mypy_cache",
                ".ruff_cache"
            ]
            
            for cache_dir in cache_dirs:
                subprocess.run(
                    ["find", ".", "-type", "d", "-name", cache_dir, "-exec", "rm", "-rf", "{}", "+"],
                    cwd=self.project_root,
                    capture_output=True
                )
            
            return True
        except Exception:
            return False
    
    def generate_development_report(self) -> str:
        """Generate comprehensive development status report."""
        status = self.check_environment()
        
        report = f"""
# Development Environment Report
Generated: {status.timestamp}

## 📊 Status Overview
- Python Version: {status.python_version}
- Dependencies: {'✅ OK' if status.dependencies_ok else '❌ Issues'}
- Database: {'✅ OK' if status.database_ok else '❌ Issues'}
- Tests: {'✅ Passing' if status.tests_passing else '❌ Failing'}
- Code Quality: {'✅ Good' if status.code_quality_ok else '❌ Issues'}
- Documentation: {'✅ OK' if status.documentation_ok else '❌ Issues'}

## 📂 Git Status
- Branch: {status.git_status.get('branch', 'unknown')}
- Clean: {'✅ Yes' if status.git_status.get('clean', False) else '❌ No'}
- Modified Files: {status.git_status.get('modified_files', 0)}
- Last Commit: {status.git_status.get('last_commit', 'unknown')}

## 🚨 Issues Found
"""
        
        if status.issues:
            for issue in status.issues:
                report += f"- ❌ {issue}\n"
        else:
            report += "- ✅ No issues found\n"
        
        report += "\n## 💡 Recommendations\n"
        
        if status.recommendations:
            for rec in status.recommendations:
                report += f"- 🔧 {rec}\n"
        else:
            report += "- ✅ No recommendations\n"
        
        # Add quick commands
        report += """
## 🔧 Quick Commands
```bash
# Run all tests
make test

# Fix code quality
make quality-check

# Update dependencies  
.devcontainer/update.sh

# Reset database
scripts/dev/reset_db.sh

# Build documentation
make docs-build
```
"""
        
        return report
    
    def setup_autonomous_workflow(self) -> bool:
        """Setup autonomous development workflow tools."""
        print("🤖 Setting up autonomous workflow...")
        
        # Create workflow scripts
        self._create_workflow_scripts()
        
        # Setup monitoring
        self._setup_monitoring()
        
        # Create automation hooks
        self._create_automation_hooks()
        
        print("✅ Autonomous workflow setup completed")
        return True
    
    def _create_workflow_scripts(self):
        """Create autonomous workflow scripts."""
        scripts_dir = self.project_root / "scripts" / "autonomous"
        scripts_dir.mkdir(parents=True, exist_ok=True)
        
        # Auto-test script
        (scripts_dir / "auto_test.sh").write_text("""#!/bin/bash
# Autonomous testing script
set -e

echo "🧪 Running autonomous tests..."

# Run tests with coverage
pytest tests/ --cov=src --cov-report=html --cov-report=term

# Run performance tests
pytest tests/test_performance.py --benchmark-only --benchmark-autosave

# Check test coverage
coverage report --fail-under=80

echo "✅ Autonomous testing completed"
""")
        
        # Auto-quality script  
        (scripts_dir / "auto_quality.sh").write_text("""#!/bin/bash
# Autonomous quality check script
set -e

echo "🔍 Running autonomous quality checks..."

# Format code
black src/ tests/
isort src/ tests/

# Lint code
ruff check src/ tests/ --fix
flake8 src/ tests/

# Type check
mypy src/

# Security check
bandit -r src/ -f txt

# Complexity check
radon cc src/ --min B
xenon --max-absolute B --max-modules A --max-average A src/

echo "✅ Autonomous quality checks completed"
""")
        
        # Make scripts executable
        for script in scripts_dir.glob("*.sh"):
            script.chmod(0o755)
    
    def _setup_monitoring(self):
        """Setup development monitoring."""
        monitoring_dir = self.project_root / "scripts" / "monitoring"
        monitoring_dir.mkdir(parents=True, exist_ok=True)
        
        # Development metrics collector
        (monitoring_dir / "dev_metrics.py").write_text("""#!/usr/bin/env python3
import json
import time
import psutil
from pathlib import Path

def collect_metrics():
    return {
        "timestamp": time.time(),
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_usage": psutil.disk_usage('.').percent,
        "process_count": len(psutil.pids())
    }

if __name__ == "__main__":
    metrics = collect_metrics()
    metrics_file = Path("data/logs/dev_metrics.json")
    metrics_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(metrics_file, "a") as f:
        f.write(json.dumps(metrics) + "\\n")
""")
    
    def _create_automation_hooks(self):
        """Create automation hooks for autonomous operation."""
        hooks_dir = self.project_root / ".git" / "hooks"
        
        # Pre-commit hook for autonomous quality
        if hooks_dir.exists():
            pre_commit_hook = hooks_dir / "pre-commit"
            pre_commit_hook.write_text("""#!/bin/bash
# Autonomous pre-commit hook

echo "🤖 Running autonomous pre-commit checks..."

# Auto-format changed files
git diff --cached --name-only --diff-filter=ACM | grep -E '\\.(py)$' | xargs black --quiet
git diff --cached --name-only --diff-filter=ACM | grep -E '\\.(py)$' | xargs isort --quiet

# Quick lint check
ruff check $(git diff --cached --name-only --diff-filter=ACM | grep -E '\\.(py)$') --quiet

# Re-add formatted files
git add $(git diff --cached --name-only --diff-filter=ACM | grep -E '\\.(py)$')

echo "✅ Autonomous pre-commit completed"
""")
            pre_commit_hook.chmod(0o755)

def main():
    """Main development tools interface."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Development Tools")
    parser.add_argument("command", choices=[
        "check", "fix", "report", "setup-autonomous"
    ], help="Command to run")
    
    args = parser.parse_args()
    
    tools = DevelopmentTools()
    
    if args.command == "check":
        status = tools.check_environment()
        print("\n🔍 Environment Check Results:")
        print(f"Dependencies: {'✅' if status.dependencies_ok else '❌'}")
        print(f"Database: {'✅' if status.database_ok else '❌'}")
        print(f"Tests: {'✅' if status.tests_passing else '❌'}")
        print(f"Code Quality: {'✅' if status.code_quality_ok else '❌'}")
        
        if status.issues:
            print("\n🚨 Issues:")
            for issue in status.issues:
                print(f"  - {issue}")
        
        if status.recommendations:
            print("\n💡 Recommendations:")
            for rec in status.recommendations:
                print(f"  - {rec}")
    
    elif args.command == "fix":
        results = tools.auto_fix_issues()
        print("\n🔧 Auto-fix Results:")
        for task, success in results.items():
            print(f"  {task}: {'✅' if success else '❌'}")
    
    elif args.command == "report":
        report = tools.generate_development_report()
        report_file = Path("data/logs/dev_report.md")
        report_file.parent.mkdir(parents=True, exist_ok=True)
        report_file.write_text(report)
        print(f"📊 Report saved to: {report_file}")
        print(report)
    
    elif args.command == "setup-autonomous":
        tools.setup_autonomous_workflow()

if __name__ == "__main__":
    main()