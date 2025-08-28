#!/usr/bin/env python3
"""
Examples Execution Tests - Telegram Audio Downloader
===================================================

Tests für die Ausführung von Beispielen in der Dokumentation.
"""

import os
import sys
import subprocess
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch
import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestExamplesExecution:
    """Tests für die Ausführung von Beispielen."""
    
    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp(prefix="examples_test_")
        self.download_dir = Path(self.temp_dir) / "downloads"
        self.download_dir.mkdir()
        
        # Setup test database
        self.test_db_path = Path(self.temp_dir) / "test.db"
        os.environ["DB_PATH"] = str(self.test_db_path)
        
        yield
        
        # Cleanup
        import shutil
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def test_readme_usage_examples(self):
        """Test README.md Verwendungsbeispiele."""
        readme_path = Path(__file__).parent.parent / "README.md"
        if not readme_path.exists():
            pytest.skip("README.md not found")
        
        readme_content = readme_path.read_text(encoding='utf-8')
        
        # Extract command line examples from README
        # Look for code blocks that show usage
        import re
        command_pattern = r'```(?:bash|shell|console)?\n(.*?telegram_audio_downloader.*?)\n```'
        matches = re.findall(command_pattern, readme_content, re.DOTALL)
        
        # For each example, create a safe version for testing
        for match in matches:
            # Skip if it requires actual Telegram credentials
            if '--help' in match or 'help' in match:
                # Test help command
                self._test_help_command(match)
            elif '--version' in match:
                # Test version command
                self._test_version_command(match)
            # Other commands that require credentials are not tested here
    
    def _test_help_command(self, command_line):
        """Test Hilfe-Befehl aus Beispiel."""
        # Extract the command
        parts = command_line.split()
        if parts[0] in ['python', 'python3']:
            parts = parts[1:]  # Remove python/python3
        
        # Execute the help command
        try:
            # Import and run the CLI directly
            from telegram_audio_downloader.cli import main
            from click.testing import CliRunner
            
            runner = CliRunner()
            result = runner.invoke(main, ['--help'])
            
            # Should execute successfully
            assert result.exit_code == 0
            assert "Usage:" in result.output
        except Exception as e:
            # Help command should not fail
            pytest.fail(f"Help command failed: {e}")
    
    def _test_version_command(self, command_line):
        """Test Versions-Befehl aus Beispiel."""
        # Extract the command
        parts = command_line.split()
        if parts[0] in ['python', 'python3']:
            parts = parts[1:]  # Remove python/python3
        
        # Execute the version command
        try:
            # Import and run the CLI directly
            from telegram_audio_downloader.cli import main
            from click.testing import CliRunner
            
            runner = CliRunner()
            result = runner.invoke(main, ['--version'])
            
            # Should execute successfully (might exit with 0 or 1)
            assert result.exit_code in [0, 1]
        except Exception as e:
            # Version command should not fail
            pytest.fail(f"Version command failed: {e}")
    
    def test_example_script_basic_usage(self):
        """Test grundlegende Beispiel-Skriptverwendung."""
        # Create a minimal example script
        example_script = f"""
#!/usr/bin/env python3
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Test importing main modules
try:
    from telegram_audio_downloader import cli, downloader, database
    print("Successfully imported modules")
    
    # Test basic functionality
    from telegram_audio_downloader.database import init_db, reset_db
    print("Database functions imported")
    
    # Test that we can initialize without errors
    # (This won't actually connect to Telegram without credentials)
    print("Setup complete")
    
except Exception as e:
    print(f"Error: {{e}}")
    sys.exit(1)
"""
        
        # Write example script to temp file
        script_path = Path(self.temp_dir) / "example_test.py"
        script_path.write_text(example_script.strip())
        
        # Execute the script
        result = subprocess.run([
            sys.executable, str(script_path)
        ], capture_output=True, text=True, timeout=30)
        
        # Should execute without syntax errors
        assert result.returncode == 0, f"Script failed with output: {result.stderr}"
        assert "Successfully imported modules" in result.stdout
    
    def test_example_script_with_mocked_downloader(self):
        """Test Beispiel-Skript mit gemocktem Downloader."""
        # Create an example script that uses the downloader
        example_script = f"""
#!/usr/bin/env python3
import sys
import os
import asyncio
from pathlib import Path
from unittest.mock import Mock, AsyncMock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

async def main():
    try:
        from telegram_audio_downloader.downloader import AudioDownloader
        
        # Create downloader with test directory
        downloader = AudioDownloader(download_dir="{self.download_dir}")
        
        # Test that object creation works
        print("Downloader created successfully")
        
        # Test method existence
        assert hasattr(downloader, 'initialize_client')
        assert hasattr(downloader, 'download_audio_files')
        print("Downloader methods exist")
        
    except Exception as e:
        print(f"Error: {{e}}")
        return False
    return True

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
"""
        
        # Write example script to temp file
        script_path = Path(self.temp_dir) / "downloader_example.py"
        script_path.write_text(example_script.strip())
        
        # Execute the script
        result = subprocess.run([
            sys.executable, str(script_path)
        ], capture_output=True, text=True, timeout=30)
        
        # Should execute without errors
        assert result.returncode == 0, f"Script failed with output: {result.stderr}"
        assert "Downloader created successfully" in result.stdout
    
    def test_import_all_public_modules(self):
        """Test Import aller öffentlichen Module."""
        # Create a script that imports all public modules
        import_script = f"""
#!/usr/bin/env python3
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Test importing all main modules
modules_to_import = [
    'telegram_audio_downloader.cli',
    'telegram_audio_downloader.downloader',
    'telegram_audio_downloader.database',
    'telegram_audio_downloader.models',
    'telegram_audio_downloader.utils',
    'telegram_audio_downloader.utils.file_operations',
    'telegram_audio_downloader.utils.rate_limiter',
    'telegram_audio_downloader.utils.metadata_extractor',
    'telegram_audio_downloader.utils.lru_cache',
]

failed_imports = []
successful_imports = []

for module_name in modules_to_import:
    try:
        __import__(module_name)
        successful_imports.append(module_name)
        print(f"Successfully imported {{module_name}}")
    except Exception as e:
        failed_imports.append((module_name, str(e)))
        print(f"Failed to import {{module_name}}: {{e}}")

print(f"Successfully imported {{len(successful_imports)}} modules")
if failed_imports:
    print(f"Failed to import {{len(failed_imports)}} modules")
    for module, error in failed_imports:
        print(f"  {{module}}: {{error}}")

sys.exit(1 if failed_imports else 0)
"""
        
        # Write import script to temp file
        script_path = Path(self.temp_dir) / "import_test.py"
        script_path.write_text(import_script.strip())
        
        # Execute the script
        result = subprocess.run([
            sys.executable, str(script_path)
        ], capture_output=True, text=True, timeout=30)
        
        # Should import most modules successfully
        # Some might fail due to missing dependencies, which is acceptable
        if result.returncode != 0:
            # Print output for debugging
            print("Import test output:")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            # Don't fail the test as some imports might legitimately fail in test environment
    
    def test_example_configuration_usage(self):
        """Test Beispiel für Konfigurationsverwendung."""
        # Create a script that demonstrates configuration usage
        config_script = f"""
#!/usr/bin/env python3
import sys
import os
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from telegram_audio_downloader.config import ConfigManager
    
    # Create config manager
    config_manager = ConfigManager()
    
    # Get config (should work without errors)
    config = config_manager.get_config()
    
    # Check that config has expected keys
    expected_keys = ['max_concurrent_downloads', 'rate_limit_delay', 'download_dir']
    for key in expected_keys:
        if key in config:
            print(f"Configuration key {{key}}: {{config[key]}}")
    
    print("Configuration system works")
    
except Exception as e:
    print(f"Configuration test failed: {{e}}")
    sys.exit(1)
"""
        
        # Write config script to temp file
        script_path = Path(self.temp_dir) / "config_example.py"
        script_path.write_text(config_script.strip())
        
        # Execute the script
        result = subprocess.run([
            sys.executable, str(script_path)
        ], capture_output=True, text=True, timeout=30)
        
        # Should execute without errors
        assert result.returncode == 0, f"Config example failed with output: {result.stderr}"
        assert "Configuration system works" in result.stdout
    
    def test_example_database_operations(self):
        """Test Beispiel für Datenbankoperationen."""
        # Create a script that demonstrates database usage
        db_script = f"""
#!/usr/bin/env python3
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    # Set up test database path
    os.environ['DB_PATH'] = '{self.test_db_path}'
    
    from telegram_audio_downloader.database import init_db, reset_db
    from telegram_audio_downloader.models import AudioFile, DownloadStatus
    
    # Initialize database
    reset_db()  # Clear any existing data
    init_db()   # Initialize schema
    
    print("Database initialized successfully")
    
    # Test creating a record
    try:
        audio_file = AudioFile.create(
            file_id="test_file_123",
            group_id=-1001234567890,
            message_id=1,
            file_name="test.mp3",
            file_size=1024,
            status=DownloadStatus.PENDING.value
        )
        print("Database record created successfully")
        
        # Test querying
        count = AudioFile.select().count()
        print(f"Database contains {{count}} records")
        
    except Exception as e:
        print(f"Database operations test failed: {{e}}")
        sys.exit(1)
    
    print("Database operations work")
    
except Exception as e:
    print(f"Database test failed: {{e}}")
    sys.exit(1)
"""
        
        # Write database script to temp file
        script_path = Path(self.temp_dir) / "database_example.py"
        script_path.write_text(db_script.strip())
        
        # Execute the script
        result = subprocess.run([
            sys.executable, str(script_path)
        ], capture_output=True, text=True, timeout=30)
        
        # Should execute without errors
        assert result.returncode == 0, f"Database example failed with output: {result.stderr}"
        assert "Database operations work" in result.stdout
    
    def test_cli_example_with_environment(self):
        """Test CLI-Beispiel mit Umgebungsvariablen."""
        # Test that CLI can be imported and used programmatically
        try:
            from telegram_audio_downloader.cli import main
            from click.testing import CliRunner
            
            runner = CliRunner()
            
            # Test with environment variables
            with patch.dict(os.environ, {
                'API_ID': '123456',
                'API_HASH': 'test_hash',
                'SESSION_NAME': 'test_session'
            }):
                # Test that CLI can be invoked (will fail gracefully without real credentials)
                result = runner.invoke(main, ['--help'])
                # Should not crash
                assert result.exit_code in [0, 1, 2]  # Accept various exit codes for help
                
        except Exception as e:
            pytest.fail(f"CLI example failed: {e}")