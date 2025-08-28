"""
Nox configuration for advanced testing and automation.
Alternative to tox with more Python-native configuration.
"""

import nox
from pathlib import Path

# Project configuration
PROJECT_ROOT = Path(__file__).parent
SRC_DIR = PROJECT_ROOT / "src"
TESTS_DIR = PROJECT_ROOT / "tests"
DOCS_DIR = PROJECT_ROOT / "docs"

# Python versions to test
PYTHON_VERSIONS = ["3.8", "3.9", "3.10", "3.11", "3.12"]
PYTHON_DEFAULT = "3.11"

# Default sessions to run
nox.options.default_venv_backend = "virtualenv"
nox.options.reuse_existing_virtualenvs = True
nox.options.sessions = ["tests", "lint", "type_check", "security"]

@nox.session(python=PYTHON_VERSIONS)
def tests(session):
    """Run comprehensive test suite."""
    session.install("-e", ".[test]")
    
    # Environment setup
    session.env.update({
        "PYTHONPATH": str(SRC_DIR),
        "TESTING": "true",
        "LOG_LEVEL": "DEBUG",
        "DATABASE_URL": "sqlite:///:memory:",
        "API_ID": "123456",
        "API_HASH": "test_hash_for_testing",
    })
    
    # Run tests with coverage
    args = [
        "pytest",
        "tests/",
        "--cov=telegram_audio_downloader",
        "--cov-report=term-missing",
        f"--cov-report=html:{session.create_tmp()}/htmlcov",
        f"--cov-report=xml:{session.create_tmp()}/coverage.xml",
        f"--junit-xml={session.create_tmp()}/junit.xml",
        "--strict-markers",
        "--strict-config",
        "-ra",
    ]
    
    if session.posargs:
        args.extend(session.posargs)
    
    session.run(*args)

@nox.session(python=PYTHON_DEFAULT)
def lint(session):
    """Run linting with ruff and flake8."""
    session.install(
        "ruff>=0.1.0",
        "flake8>=6.0.0",
        "flake8-docstrings>=1.7.0",
        "flake8-bugbear>=23.3.23",
        "flake8-comprehensions>=3.12.0",
        "flake8-simplify>=0.19.3",
        "pylint>=2.17.4",
    )
    
    # Ruff check
    session.run("ruff", "check", "src/", "tests/", "--statistics")
    
    # Flake8 check
    session.run("flake8", "src/", "tests/", "--statistics")
    
    # Pylint check
    session.run("pylint", "src/telegram_audio_downloader/")

@nox.session(python=PYTHON_DEFAULT)
def format_code(session):
    """Format code with black and isort."""
    session.install("black>=23.3.0", "isort>=5.12.0")
    
    # Check if code needs formatting
    session.run("black", "src/", "tests/", "--check", "--diff")
    session.run("isort", "src/", "tests/", "--check-only", "--diff")

@nox.session(python=PYTHON_DEFAULT)
def format_fix(session):
    """Auto-fix code formatting."""
    session.install("black>=23.3.0", "isort>=5.12.0")
    
    # Auto-fix formatting
    session.run("black", "src/", "tests/")
    session.run("isort", "src/", "tests/")

@nox.session(python=PYTHON_DEFAULT)
def type_check(session):
    """Run type checking with mypy."""
    session.install("mypy>=1.3.0", "types-requests", "types-setuptools")
    session.install("-e", ".[dev]")
    
    # Create output directory
    output_dir = session.create_tmp() / "mypy"
    output_dir.mkdir(exist_ok=True)
    
    session.run(
        "mypy",
        "src/telegram_audio_downloader/",
        f"--html-report={output_dir}/html",
        f"--txt-report={output_dir}/txt",
        f"--junit-xml={output_dir}/junit.xml",
    )

@nox.session(python=PYTHON_DEFAULT)
def security(session):
    """Run security checks with bandit and safety."""
    session.install("bandit>=1.7.5", "safety>=2.3.5", "pip-audit>=2.5.5")
    
    output_dir = session.create_tmp()
    
    # Bandit security check
    session.run(
        "bandit",
        "-r", "src/",
        "-f", "json",
        "-o", f"{output_dir}/bandit.json",
    )
    
    # Safety dependency check
    session.run(
        "safety", "check",
        "--json",
        "--output", f"{output_dir}/safety.json",
        "--continue-on-error",
    )
    
    # Pip audit
    session.run(
        "pip-audit",
        "--format=json",
        f"--output={output_dir}/pip-audit.json",
        "--desc",
    )

@nox.session(python=PYTHON_DEFAULT)
def docs(session):
    """Build documentation with Sphinx."""
    session.install("-e", ".[docs]")
    
    output_dir = session.create_tmp() / "docs"
    
    # Build HTML documentation
    session.run(
        "sphinx-build",
        "-W", "-b", "html",
        "docs/sphinx",
        f"{output_dir}/html",
    )
    
    # Check links
    session.run(
        "sphinx-build",
        "-W", "-b", "linkcheck",
        "docs/sphinx",
        f"{output_dir}/linkcheck",
    )
    
    # Run doctests
    session.run(
        "sphinx-build",
        "-W", "-b", "doctest",
        "docs/sphinx",
        f"{output_dir}/doctest",
    )
    
    session.log(f"Documentation built in {output_dir}/html")

@nox.session(python=PYTHON_DEFAULT)
def docs_serve(session):
    """Serve documentation with live reload."""
    session.install("-e", ".[docs]", "sphinx-autobuild>=2021.3.14")
    
    session.run(
        "sphinx-autobuild",
        "docs/sphinx",
        "docs/build",
        "--host", "127.0.0.1",
        "--port", "8000",
        "--watch", "src/",
    )

@nox.session(python=PYTHON_DEFAULT)
def coverage(session):
    """Generate comprehensive coverage report."""
    session.install("coverage>=7.2.5", "coverage-badge>=1.1.0")
    
    output_dir = session.create_tmp()
    
    # Combine coverage files
    session.run("coverage", "combine")
    
    # Generate reports
    session.run("coverage", "report", "--show-missing", "--fail-under=80")
    session.run("coverage", "html", "-d", f"{output_dir}/htmlcov")
    session.run("coverage", "xml", "-o", f"{output_dir}/coverage.xml")
    
    # Generate badge
    session.run("coverage-badge", "-f", "-o", f"{output_dir}/coverage.svg")
    
    session.log(f"Coverage report generated in {output_dir}")

@nox.session(python=PYTHON_DEFAULT)
def integration(session):
    """Run integration tests."""
    session.install("-e", ".[test]", "docker>=6.1.2", "testcontainers>=3.7.1")
    
    session.env.update({
        "PYTHONPATH": str(SRC_DIR),
        "INTEGRATION_TESTS": "true",
        "TEST_TIMEOUT": "300",
    })
    
    session.run(
        "pytest",
        "tests/integration/",
        "--timeout=300",
        "-v",
        "-m", "integration",
        *session.posargs,
    )

@nox.session(python=PYTHON_DEFAULT)
def performance(session):
    """Run performance benchmarks."""
    session.install("-e", ".[test]", "pytest-benchmark>=4.0.0")
    
    output_dir = session.create_tmp()
    
    session.env.update({
        "PYTHONPATH": str(SRC_DIR),
        "PERFORMANCE_TESTS": "true",
    })
    
    session.run(
        "pytest",
        "tests/performance/",
        "--benchmark-only",
        f"--benchmark-json={output_dir}/benchmark.json",
        f"--benchmark-histogram={output_dir}/histogram",
        "--benchmark-sort=mean",
        "-v",
        *session.posargs,
    )

@nox.session(python=PYTHON_DEFAULT)
def stress(session):
    """Run stress tests."""
    session.install("-e", ".[test]", "locust>=2.15.1")
    
    session.env.update({
        "PYTHONPATH": str(SRC_DIR),
        "STRESS_TESTS": "true",
    })
    
    session.run(
        "pytest",
        "tests/stress/",
        "--stress",
        "--timeout=600",
        "-v",
        *session.posargs,
    )

@nox.session(python=PYTHON_DEFAULT)
def build(session):
    """Test package building."""
    session.install("build>=0.10.0", "twine>=4.0.2", "check-manifest>=0.49")
    
    # Check manifest
    session.run("check-manifest")
    
    # Build package
    session.run("python", "-m", "build")
    
    # Check package
    session.run("twine", "check", "dist/*")

@nox.session(python=PYTHON_DEFAULT)
def dev_setup(session):
    """Setup development environment."""
    session.install("-e", ".[dev,test,docs]")
    session.install("pre-commit>=3.3.0", "commitizen>=3.2.1")
    
    # Install pre-commit hooks
    session.run("pre-commit", "install")
    session.run("pre-commit", "install", "--hook-type", "commit-msg")
    
    # Run environment check
    session.run("python", "scripts/dev_tools.py", "check")

@nox.session(python=PYTHON_DEFAULT)
def quality_check(session):
    """Run all quality checks."""
    session.install("-e", ".[dev,test]")
    
    # Install all quality tools
    session.install(
        "ruff>=0.1.0",
        "black>=23.3.0",
        "isort>=5.12.0",
        "flake8>=6.0.0",
        "mypy>=1.3.0",
        "bandit>=1.7.5",
        "safety>=2.3.5",
    )
    
    session.env.update({
        "PYTHONPATH": str(SRC_DIR),
        "TESTING": "true",
    })
    
    # Run quality checks
    session.log("🔍 Running code formatting checks...")
    session.run("black", "src/", "tests/", "--check")
    session.run("isort", "src/", "tests/", "--check-only")
    
    session.log("🔍 Running linting...")
    session.run("ruff", "check", "src/", "tests/")
    session.run("flake8", "src/", "tests/")
    
    session.log("🔍 Running type checking...")
    session.run("mypy", "src/telegram_audio_downloader/")
    
    session.log("🔍 Running security checks...")
    session.run("bandit", "-r", "src/")
    session.run("safety", "check")
    
    session.log("🔍 Running tests...")
    session.run("pytest", "tests/", "--tb=short", "-x")
    
    session.log("✅ All quality checks passed!")

@nox.session(python=PYTHON_DEFAULT)
def auto_fix(session):
    """Automatically fix common issues."""
    session.install(
        "black>=23.3.0",
        "isort>=5.12.0", 
        "ruff>=0.1.0",
        "pre-commit>=3.3.0",
    )
    
    session.log("🔧 Auto-fixing code formatting...")
    session.run("black", "src/", "tests/")
    session.run("isort", "src/", "tests/")
    
    session.log("🔧 Auto-fixing linting issues...")
    session.run("ruff", "check", "src/", "tests/", "--fix")
    
    session.log("🔧 Updating pre-commit hooks...")
    session.run("pre-commit", "autoupdate")
    
    session.log("✅ Auto-fix completed!")

@nox.session(python=PYTHON_DEFAULT)
def clean(session):
    """Clean up build artifacts and cache."""
    import shutil
    import glob
    
    session.log("🧹 Cleaning up...")
    
    # Patterns to clean
    patterns = [
        "**/__pycache__",
        "**/.pytest_cache",
        "**/.mypy_cache",
        "**/.ruff_cache",
        ".coverage*",
        "htmlcov",
        "*.coverage",
        "build/",
        "dist/",
        "*.egg-info/",
        ".tox/",
        ".nox/",
    ]
    
    for pattern in patterns:
        for path in glob.glob(pattern, recursive=True):
            if Path(path).exists():
                if Path(path).is_dir():
                    shutil.rmtree(path)
                else:
                    Path(path).unlink()
                session.log(f"Removed: {path}")
    
    session.log("✅ Cleanup completed!")

@nox.session(python=PYTHON_DEFAULT)
def release_check(session):
    """Pre-release checks."""
    session.install("-e", ".[dev,test,docs]")
    session.install("twine>=4.0.2", "build>=0.10.0")
    
    session.log("🚀 Running pre-release checks...")
    
    # Run full test suite
    session.run("pytest", "tests/", "--tb=short")
    
    # Run quality checks
    session.run("ruff", "check", "src/", "tests/")
    session.run("mypy", "src/telegram_audio_downloader/")
    session.run("bandit", "-r", "src/")
    
    # Build and check package
    session.run("python", "-m", "build")
    session.run("twine", "check", "dist/*")
    
    # Check documentation
    session.run("sphinx-build", "-W", "-b", "html", "docs/sphinx", "docs/build")
    
    session.log("✅ Pre-release checks completed!")

@nox.session(python=PYTHON_DEFAULT, venv_backend="none")
def ci_info(session):
    """Display CI information."""
    import os
    import sys
    
    session.log("🔍 CI Environment Information:")
    session.log(f"Python: {sys.version}")
    session.log(f"Platform: {sys.platform}")
    session.log(f"Working Directory: {os.getcwd()}")
    
    # CI-specific environment variables
    ci_vars = [
        "CI", "GITHUB_ACTIONS", "GITHUB_WORKFLOW", "GITHUB_RUN_ID",
        "GITHUB_REF", "GITHUB_SHA", "RUNNER_OS", "RUNNER_ARCH"
    ]
    
    for var in ci_vars:
        value = os.environ.get(var, "Not set")
        session.log(f"{var}: {value}")

# Custom session for GitHub Actions
@nox.session(python=PYTHON_VERSIONS, tags=["ci"])
def ci_tests(session):
    """Optimized tests for CI environment."""
    session.install("-e", ".[test]")
    
    session.env.update({
        "PYTHONPATH": str(SRC_DIR),
        "TESTING": "true",
        "CI": "true",
    })
    
    # Run tests with minimal output for CI
    session.run(
        "pytest",
        "tests/",
        "--cov=telegram_audio_downloader",
        "--cov-report=xml",
        "--tb=short",
        "-q",
        "--disable-warnings",
        *session.posargs,
    )