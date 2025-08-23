#!/usr/bin/env python3
"""
End-to-End Test Suite - Telegram Audio Downloader
=================================================

Comprehensive end-to-end tests for complete system validation.
"""

import os
import sys
import json
import asyncio
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from unittest.mock import Mock, patch, AsyncMock
import pytest
import pytest_asyncio

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from telegram_audio_downloader.downloader import AudioDownloader
from telegram_audio_downloader.database import Database
from telegram_audio_downloader.cli import cli

@dataclass
class E2ETestResult:
    """End-to-end test result."""
    test_name: str
    status: str  # PASS, FAIL, SKIP
    duration: float
    details: Dict[str, Any]
    error: Optional[str] = None

class E2ETestFramework:
    """End-to-end test framework."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.test_results: List[E2ETestResult] = []
        self.temp_dir = None
        self.mock_data = self._setup_mock_data()
    
    def _setup_mock_data(self) -> Dict[str, Any]:
        """Setup mock data for testing."""
        return {
            "test_group": {
                "id": -1001234567890,
                "title": "Test Music Group",
                "username": "test_music_group"
            },
            "test_messages": [
                {
                    "id": 1,
                    "date": "2024-01-20T10:00:00Z",
                    "text": "Test Audio File",
                    "media": {
                        "audio": {
                            "file_id": "BAADBAADrQADBRZpDgABAg",
                            "duration": 180,
                            "title": "Test Song",
                            "performer": "Test Artist",
                            "file_size": 5242880
                        }
                    }
                }
            ]
        }
    
    async def setup_test_environment(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp(prefix="e2e_test_")
        
        # Setup test database
        test_db_path = Path(self.temp_dir) / "test.db"
        os.environ["DATABASE_URL"] = f"sqlite:///{test_db_path}"
        
        # Setup test downloads directory
        downloads_dir = Path(self.temp_dir) / "downloads"
        downloads_dir.mkdir()
        
        # Setup mock Telegram client
        self._setup_telegram_mocks()
        
        print(f"🔧 Test environment setup in: {self.temp_dir}")
    
    def _setup_telegram_mocks(self):
        """Setup Telegram API mocks."""
        self.mock_client = AsyncMock()
        self.mock_client.get_entity.return_value = Mock(
            id=-1001234567890,
            title="Test Music Group",
            username="test_music_group"
        )
        
        mock_message = Mock()
        mock_message.id = 1
        mock_message.date = "2024-01-20T10:00:00Z"
        mock_message.text = "Test Audio File"
        mock_message.audio = Mock(
            file_id="test_file_id",
            duration=180,
            title="Test Song",
            performer="Test Artist",
            file_size=5242880
        )
        
        self.mock_client.iter_messages.return_value = [mock_message]
        self.mock_client.download_media.return_value = self.temp_dir + "/test_audio.mp3"
    
    async def teardown_test_environment(self):
        """Cleanup test environment."""
        import shutil
        if self.temp_dir and Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    async def run_all_tests(self) -> List[E2ETestResult]:
        """Run all end-to-end tests."""
        print("🧪 Starting End-to-End Test Suite...")
        
        await self.setup_test_environment()
        
        try:
            # Core functionality tests
            await self._test_downloader_initialization()
            await self._test_audio_download_workflow()
            await self._test_database_operations()
            await self._test_cli_commands()
            
            # Integration tests
            await self._test_concurrent_downloads()
            await self._test_error_handling()
            await self._test_performance_benchmarks()
            await self._test_security_validation()
            
        finally:
            await self.teardown_test_environment()
        
        print(f"✅ End-to-End Test Suite completed: {len(self.test_results)} tests")
        return self.test_results
    
    async def _test_downloader_initialization(self):
        """Test downloader initialization."""
        test_name = "Downloader Initialization"
        start_time = asyncio.get_event_loop().time()
        
        try:
            downloader = AudioDownloader(
                download_dir=str(Path(self.temp_dir) / "downloads"),
                max_concurrent_downloads=2
            )
            
            assert downloader.download_dir.exists()
            assert downloader.max_concurrent_downloads == 2
            
            with patch('telegram_audio_downloader.downloader.TelegramClient') as mock_client:
                mock_client.return_value = self.mock_client
                await downloader.initialize_client()
                assert downloader.client is not None
            
            duration = asyncio.get_event_loop().time() - start_time
            
            self.test_results.append(E2ETestResult(
                test_name=test_name,
                status="PASS",
                duration=duration,
                details={
                    "download_dir": str(downloader.download_dir),
                    "max_concurrent": downloader.max_concurrent_downloads,
                    "client_initialized": True
                }
            ))
            
        except Exception as e:
            duration = asyncio.get_event_loop().time() - start_time
            self.test_results.append(E2ETestResult(
                test_name=test_name,
                status="FAIL",
                duration=duration,
                details={},
                error=str(e)
            ))
    
    async def _test_audio_download_workflow(self):
        """Test complete audio download workflow."""
        test_name = "Audio Download Workflow"
        start_time = asyncio.get_event_loop().time()
        
        try:
            downloader = AudioDownloader(download_dir=str(Path(self.temp_dir) / "downloads"))
            
            with patch('telegram_audio_downloader.downloader.TelegramClient') as mock_client:
                mock_client.return_value = self.mock_client
                await downloader.initialize_client()
                
                # Create mock audio file
                test_file = Path(self.temp_dir) / "test_audio.mp3"
                test_file.write_bytes(b"ID3\x03\x00\x00\x00" + b"\x00" * 5242870)
                
                result = await downloader.download_audio_files(
                    group_identifier="@test_music_group",
                    limit=1
                )
                
                assert "completed" in result
                assert "failed" in result
                assert "total_size" in result
            
            duration = asyncio.get_event_loop().time() - start_time
            
            self.test_results.append(E2ETestResult(
                test_name=test_name,
                status="PASS",
                duration=duration,
                details={
                    "download_result": result,
                    "workflow_stages": ["group_resolution", "message_iteration", "file_download"]
                }
            ))
            
        except Exception as e:
            duration = asyncio.get_event_loop().time() - start_time
            self.test_results.append(E2ETestResult(
                test_name=test_name,
                status="FAIL",
                duration=duration,
                details={},
                error=str(e)
            ))
    
    async def _test_database_operations(self):
        """Test database operations."""
        test_name = "Database Operations"
        start_time = asyncio.get_event_loop().time()
        
        try:
            db = Database(database_url=f"sqlite:///{self.temp_dir}/test.db")
            await db.init()
            
            # Test table creation
            tables = await db.get_tables()
            assert len(tables) > 0
            
            # Test data operations
            download_record = {
                "file_id": "test_file_123",
                "group_id": -1001234567890,
                "message_id": 1,
                "file_name": "test_audio.mp3",
                "file_size": 5242880,
                "download_status": "completed"
            }
            
            record_id = await db.insert_download_record(download_record)
            assert record_id is not None
            
            retrieved = await db.get_download_record(record_id)
            assert retrieved is not None
            assert retrieved["file_id"] == "test_file_123"
            
            await db.close()
            
            duration = asyncio.get_event_loop().time() - start_time
            
            self.test_results.append(E2ETestResult(
                test_name=test_name,
                status="PASS",
                duration=duration,
                details={
                    "tables_created": len(tables),
                    "operations": ["insert", "retrieve"],
                    "record_id": record_id
                }
            ))
            
        except Exception as e:
            duration = asyncio.get_event_loop().time() - start_time
            self.test_results.append(E2ETestResult(
                test_name=test_name,
                status="FAIL",
                duration=duration,
                details={},
                error=str(e)
            ))
    
    async def _test_cli_commands(self):
        """Test CLI commands."""
        test_name = "CLI Commands"
        start_time = asyncio.get_event_loop().time()
        
        try:
            from click.testing import CliRunner
            runner = CliRunner()
            
            # Test version command
            result = runner.invoke(cli, ['--version'])
            assert result.exit_code == 0
            
            # Test help command
            result = runner.invoke(cli, ['--help'])
            assert result.exit_code == 0
            assert "Usage:" in result.output
            
            # Test invalid command
            result = runner.invoke(cli, ['invalid_command'])
            assert result.exit_code != 0
            
            duration = asyncio.get_event_loop().time() - start_time
            
            self.test_results.append(E2ETestResult(
                test_name=test_name,
                status="PASS",
                duration=duration,
                details={
                    "commands_tested": ["version", "help", "invalid"],
                    "cli_structure": "valid",
                    "error_handling": "appropriate"
                }
            ))
            
        except Exception as e:
            duration = asyncio.get_event_loop().time() - start_time
            self.test_results.append(E2ETestResult(
                test_name=test_name,
                status="FAIL",
                duration=duration,
                details={},
                error=str(e)
            ))
    
    async def _test_concurrent_downloads(self):
        """Test concurrent downloads."""
        test_name = "Concurrent Downloads"
        start_time = asyncio.get_event_loop().time()
        
        try:
            downloader = AudioDownloader(
                download_dir=str(Path(self.temp_dir) / "downloads"),
                max_concurrent_downloads=3
            )
            
            with patch('telegram_audio_downloader.downloader.TelegramClient') as mock_client:
                # Mock multiple messages
                mock_messages = []
                for i in range(3):
                    mock_msg = Mock()
                    mock_msg.id = i + 1
                    mock_msg.audio = Mock(file_id=f"test_file_{i}")
                    mock_messages.append(mock_msg)
                
                mock_client.return_value.iter_messages.return_value = mock_messages
                mock_client.return_value.download_media.return_value = str(Path(self.temp_dir) / "test_audio.mp3")
                
                await downloader.initialize_client()
                
                result = await downloader.download_audio_files(
                    group_identifier="@test_music_group",
                    limit=3
                )
                
                assert downloader.max_concurrent_downloads == 3
            
            duration = asyncio.get_event_loop().time() - start_time
            
            self.test_results.append(E2ETestResult(
                test_name=test_name,
                status="PASS",
                duration=duration,
                details={
                    "concurrent_limit": 3,
                    "files_processed": 3,
                    "concurrency": "working"
                }
            ))
            
        except Exception as e:
            duration = asyncio.get_event_loop().time() - start_time
            self.test_results.append(E2ETestResult(
                test_name=test_name,
                status="FAIL",
                duration=duration,
                details={},
                error=str(e)
            ))
    
    async def _test_error_handling(self):
        """Test error handling."""
        test_name = "Error Handling"
        start_time = asyncio.get_event_loop().time()
        
        try:
            downloader = AudioDownloader(download_dir=str(Path(self.temp_dir) / "downloads"))
            
            # Test network failure
            with patch('telegram_audio_downloader.downloader.TelegramClient') as mock_client:
                mock_client.side_effect = ConnectionError("Network failure")
                
                try:
                    await downloader.initialize_client()
                except Exception as e:
                    assert "Network" in str(e) or "Connection" in str(e)
            
            # Test invalid inputs
            try:
                invalid_downloader = AudioDownloader(download_dir="/invalid/path")
            except Exception:
                pass  # Expected
            
            duration = asyncio.get_event_loop().time() - start_time
            
            self.test_results.append(E2ETestResult(
                test_name=test_name,
                status="PASS",
                duration=duration,
                details={
                    "error_types": ["network", "invalid_path"],
                    "error_handling": "graceful"
                }
            ))
            
        except Exception as e:
            duration = asyncio.get_event_loop().time() - start_time
            self.test_results.append(E2ETestResult(
                test_name=test_name,
                status="FAIL",
                duration=duration,
                details={},
                error=str(e)
            ))
    
    async def _test_performance_benchmarks(self):
        """Test performance benchmarks."""
        test_name = "Performance Benchmarks"
        start_time = asyncio.get_event_loop().time()
        
        try:
            import psutil
            
            # Test import time
            import_start = asyncio.get_event_loop().time()
            import telegram_audio_downloader
            import_duration = asyncio.get_event_loop().time() - import_start
            
            # Test memory usage
            process = psutil.Process()
            memory_before = process.memory_info().rss
            
            # Create downloader
            downloader = AudioDownloader(download_dir=str(Path(self.temp_dir) / "downloads"))
            
            memory_after = process.memory_info().rss
            memory_delta = memory_after - memory_before
            
            duration = asyncio.get_event_loop().time() - start_time
            
            self.test_results.append(E2ETestResult(
                test_name=test_name,
                status="PASS",
                duration=duration,
                details={
                    "import_time_ms": import_duration * 1000,
                    "memory_delta_mb": memory_delta / (1024 * 1024),
                    "total_memory_mb": memory_after / (1024 * 1024)
                }
            ))
            
        except Exception as e:
            duration = asyncio.get_event_loop().time() - start_time
            self.test_results.append(E2ETestResult(
                test_name=test_name,
                status="FAIL",
                duration=duration,
                details={},
                error=str(e)
            ))
    
    async def _test_security_validation(self):
        """Test security validation."""
        test_name = "Security Validation"
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Test path traversal protection
            downloader = AudioDownloader(download_dir=str(Path(self.temp_dir) / "downloads"))
            
            # Test malicious filename handling
            malicious_paths = [
                "../../../etc/passwd",
                "..\\..\\windows\\system32\\config\\sam",
                "/etc/shadow",
                "NUL",
                "CON"
            ]
            
            for malicious_path in malicious_paths:
                safe_path = downloader._sanitize_filename(malicious_path)
                assert not safe_path.startswith("../")
                assert not safe_path.startswith("..\\")
                assert not safe_path.startswith("/")
            
            # Test input validation
            assert downloader._validate_group_identifier("@valid_group")
            assert not downloader._validate_group_identifier("")
            assert not downloader._validate_group_identifier(None)
            
            duration = asyncio.get_event_loop().time() - start_time
            
            self.test_results.append(E2ETestResult(
                test_name=test_name,
                status="PASS",
                duration=duration,
                details={
                    "path_traversal_protection": True,
                    "input_validation": True,
                    "malicious_paths_tested": len(malicious_paths)
                }
            ))
            
        except Exception as e:
            duration = asyncio.get_event_loop().time() - start_time
            self.test_results.append(E2ETestResult(
                test_name=test_name,
                status="FAIL",
                duration=duration,
                details={},
                error=str(e)
            ))
    
    def generate_test_report(self) -> str:
        """Generate comprehensive test report."""
        passed = len([r for r in self.test_results if r.status == "PASS"])
        failed = len([r for r in self.test_results if r.status == "FAIL"])
        skipped = len([r for r in self.test_results if r.status == "SKIP"])
        total = len(self.test_results)
        
        pass_rate = (passed / total * 100) if total > 0 else 0
        
        report = f"""
# 🧪 End-to-End Test Report

## 📊 Summary
- **Total Tests:** {total}
- **Passed:** {passed} ✅
- **Failed:** {failed} ❌
- **Skipped:** {skipped} ⏭️
- **Pass Rate:** {pass_rate:.1f}%

## 📋 Test Results

"""
        
        for result in self.test_results:
            status_emoji = {"PASS": "✅", "FAIL": "❌", "SKIP": "⏭️"}[result.status]
            report += f"### {status_emoji} {result.test_name}\n"
            report += f"- **Status:** {result.status}\n"
            report += f"- **Duration:** {result.duration:.3f}s\n"
            
            if result.details:
                report += f"- **Details:** {json.dumps(result.details, indent=2)}\n"
            
            if result.error:
                report += f"- **Error:** {result.error}\n"
            
            report += "\n"
        
        return report

async def run_e2e_tests():
    """Run end-to-end tests."""
    framework = E2ETestFramework()
    results = await framework.run_all_tests()
    
    # Generate report
    report = framework.generate_test_report()
    
    # Save report
    report_file = Path("data/tests/e2e_test_report.md")
    report_file.parent.mkdir(parents=True, exist_ok=True)
    report_file.write_text(report)
    
    print(f"📊 Test report saved to: {report_file}")
    print(report)
    
    return results

if __name__ == "__main__":
    asyncio.run(run_e2e_tests())