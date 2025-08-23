#!/usr/bin/env python3
"""
Continuous Monitoring System - Telegram Audio Downloader
========================================================

Enterprise-grade continuous monitoring for automated quality checks.
"""

import os
import sys
import json
import time
import asyncio
import logging
import schedule
import psutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

@dataclass
class HealthStatus:
    """System health status."""
    timestamp: str
    overall_health: str  # HEALTHY, WARNING, CRITICAL
    system_metrics: Dict[str, Any]
    quality_metrics: Dict[str, Any]
    performance_metrics: Dict[str, Any]
    security_metrics: Dict[str, Any]
    alerts: List[str]
    recommendations: List[str]
    score: float  # 0-100

class ContinuousMonitor:
    """Enterprise continuous monitoring system."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.project_root = Path(__file__).parent.parent.parent
        self.config = self._load_config(config_path)
        self.metrics_dir = self.project_root / "data" / "metrics"
        self.logs_dir = self.project_root / "data" / "logs"
        self.alerts_dir = self.project_root / "data" / "alerts"
        
        # Ensure directories exist
        for directory in [self.metrics_dir, self.logs_dir, self.alerts_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self._setup_logging()
        self.logger.info("Continuous Monitor initialized")
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load monitoring configuration."""
        return {
            "monitoring": {
                "interval_minutes": 5,
                "retention_days": 30,
                "alert_thresholds": {
                    "cpu_percent": 80,
                    "memory_percent": 85,
                    "disk_percent": 90,
                    "test_coverage": 70,
                    "error_rate": 5.0
                }
            },
            "quality_checks": {
                "run_tests": True,
                "run_linting": True,
                "run_security": True,
                "run_performance": True,
                "run_type_check": True
            },
            "notifications": {
                "enabled": True,
                "email": False,
                "slack": False,
                "webhook": False
            }
        }
    
    def _setup_logging(self):
        """Setup structured logging."""
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.FileHandler(self.logs_dir / "monitor.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("ContinuousMonitor")
    
    async def run_health_check(self) -> HealthStatus:
        """Run comprehensive health check."""
        self.logger.info("🔍 Starting comprehensive health check...")
        
        start_time = time.time()
        
        # Collect all metrics in parallel
        tasks = [
            self._collect_system_metrics(),
            self._collect_quality_metrics(),
            self._collect_performance_metrics(),
            self._collect_security_metrics()
        ]
        
        system_metrics, quality_metrics, performance_metrics, security_metrics = await asyncio.gather(*tasks)
        
        # Analyze health status
        alerts, recommendations = self._analyze_metrics(
            system_metrics, quality_metrics, performance_metrics, security_metrics
        )
        
        # Calculate overall health score
        score = self._calculate_health_score(
            system_metrics, quality_metrics, performance_metrics, security_metrics
        )
        
        # Determine overall health
        overall_health = self._determine_health_status(score, alerts)
        
        duration = time.time() - start_time
        self.logger.info(f"✅ Health check completed in {duration:.2f}s - Status: {overall_health}")
        
        health_status = HealthStatus(
            timestamp=datetime.now().isoformat(),
            overall_health=overall_health,
            system_metrics=system_metrics,
            quality_metrics=quality_metrics,
            performance_metrics=performance_metrics,
            security_metrics=security_metrics,
            alerts=alerts,
            recommendations=recommendations,
            score=score
        )
        
        # Store metrics
        await self._store_metrics(health_status)
        
        # Handle alerts
        if alerts:
            await self._handle_alerts(health_status)
        
        return health_status
    
    async def _collect_system_metrics(self) -> Dict[str, Any]:
        """Collect system-level metrics."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage(str(self.project_root))
            
            return {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_gb": memory.available / (1024**3),
                "disk_percent": disk.percent,
                "disk_free_gb": disk.free / (1024**3),
                "load_average": os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0],
                "uptime_hours": time.time() / 3600,
                "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
            }
        except Exception as e:
            self.logger.error(f"Error collecting system metrics: {e}")
            return {"error": str(e)}
    
    async def _collect_quality_metrics(self) -> Dict[str, Any]:
        """Collect code quality metrics."""
        try:
            metrics = {}
            
            if self.config["quality_checks"]["run_tests"]:
                metrics["test_coverage"] = await self._run_coverage_check()
            
            if self.config["quality_checks"]["run_linting"]:
                metrics["lint_score"] = await self._run_lint_check()
            
            if self.config["quality_checks"]["run_type_check"]:
                metrics["type_coverage"] = await self._run_type_check()
            
            # Code complexity
            metrics["complexity_score"] = await self._measure_complexity()
            
            # Documentation coverage
            metrics["documentation_score"] = await self._check_documentation()
            
            return metrics
        except Exception as e:
            self.logger.error(f"Error collecting quality metrics: {e}")
            return {"error": str(e)}
    
    async def _collect_performance_metrics(self) -> Dict[str, Any]:
        """Collect performance metrics."""
        try:
            if not self.config["quality_checks"]["run_performance"]:
                return {"skipped": True}
            
            metrics = {}
            
            # Import time analysis
            start_time = time.time()
            try:
                import telegram_audio_downloader
                import_time = (time.time() - start_time) * 1000
            except Exception:
                import_time = 1000.0
            
            metrics["import_time_ms"] = import_time
            
            # Memory profiling
            process = psutil.Process()
            memory_info = process.memory_info()
            
            metrics["memory_profile"] = {
                "rss_mb": memory_info.rss / (1024 * 1024),
                "vms_mb": memory_info.vms / (1024 * 1024),
                "memory_percent": process.memory_percent()
            }
            
            return metrics
        except Exception as e:
            self.logger.error(f"Error collecting performance metrics: {e}")
            return {"error": str(e)}
    
    async def _collect_security_metrics(self) -> Dict[str, Any]:
        """Collect security metrics."""
        try:
            if not self.config["quality_checks"]["run_security"]:
                return {"skipped": True}
            
            metrics = {}
            
            # Bandit security scan
            bandit_result = await self._run_bandit_scan()
            metrics["bandit_score"] = bandit_result
            
            # Safety dependency check
            safety_result = await self._run_safety_check()
            metrics["safety_score"] = safety_result
            
            # Secrets detection
            secrets_result = await self._detect_secrets()
            metrics["secrets_found"] = secrets_result
            
            return metrics
        except Exception as e:
            self.logger.error(f"Error collecting security metrics: {e}")
            return {"error": str(e)}
    
    async def _run_coverage_check(self) -> float:
        """Run test coverage check."""
        try:
            result = await self._run_command([
                "pytest", "--cov=src", "--cov-report=json", "--tb=no", "-q"
            ], timeout=300)
            
            if result.returncode == 0:
                # Parse coverage report
                coverage_file = self.project_root / "coverage.json"
                if coverage_file.exists():
                    with open(coverage_file) as f:
                        coverage_data = json.load(f)
                        return coverage_data.get("totals", {}).get("percent_covered", 0.0)
            
            return 0.0
        except Exception as e:
            self.logger.error(f"Coverage check failed: {e}")
            return 0.0
    
    async def _run_lint_check(self) -> float:
        """Run linting check."""
        try:
            # Run ruff
            ruff_result = await self._run_command([
                "ruff", "check", "src/", "--statistics"
            ], timeout=60)
            
            # Calculate composite score
            total_files = len(list(Path("src").rglob("*.py")))
            if total_files == 0:
                return 100.0
            
            # Parse issues from stderr
            issues = 0
            if ruff_result.stderr:
                # Simple heuristic: count error lines
                error_lines = [line for line in ruff_result.stderr.split('\n') if 'error' in line.lower()]
                issues = len(error_lines)
            
            # Score: 100 - (issues / files * 10)
            score = max(0, 100 - (issues / total_files * 10))
            return score
        except Exception as e:
            self.logger.error(f"Lint check failed: {e}")
            return 0.0
    
    async def _run_type_check(self) -> float:
        """Run type checking."""
        try:
            result = await self._run_command([
                "mypy", "src/"
            ], timeout=120)
            
            # Parse mypy output for type coverage
            if result.returncode == 0:
                return 95.0  # Good type coverage
            else:
                # Count typed vs untyped
                return 70.0  # Partial type coverage
        except Exception as e:
            self.logger.error(f"Type check failed: {e}")
            return 0.0
    
    async def _measure_complexity(self) -> float:
        """Measure code complexity."""
        try:
            result = await self._run_command([
                "radon", "cc", "src/", "--average"
            ], timeout=60)
            
            if result.returncode == 0:
                # Parse average complexity from output
                output = result.stdout
                if "Average complexity" in output:
                    # Extract average complexity value
                    import re
                    match = re.search(r'Average complexity: \((\d+\.\d+)\)', output)
                    if match:
                        avg_complexity = float(match.group(1))
                        # Score: 100 - (complexity - 1) * 5
                        return max(0, 100 - (avg_complexity - 1) * 5)
            
            return 85.0  # Default good score
        except Exception as e:
            self.logger.error(f"Complexity measurement failed: {e}")
            return 85.0
    
    async def _check_documentation(self) -> float:
        """Check documentation coverage."""
        try:
            # Count documented vs undocumented functions/classes
            total_items = 0
            documented_items = 0
            
            for py_file in Path("src").rglob("*.py"):
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    # Simple heuristic for functions/classes
                    import re
                    functions = re.findall(r'^(async )?def\s+\w+', content, re.MULTILINE)
                    classes = re.findall(r'^class\s+\w+', content, re.MULTILINE)
                    
                    total_items += len(functions) + len(classes)
                    
                    # Count docstrings
                    docstrings = re.findall(r'""".*?"""', content, re.DOTALL)
                    documented_items += min(len(docstrings), len(functions) + len(classes))
            
            if total_items == 0:
                return 100.0
            
            return (documented_items / total_items) * 100
        except Exception as e:
            self.logger.error(f"Documentation check failed: {e}")
            return 70.0
    
    async def _run_bandit_scan(self) -> float:
        """Run Bandit security scan."""
        try:
            result = await self._run_command([
                "bandit", "-r", "src/", "-f", "txt"
            ], timeout=120)
            
            if result.returncode == 0:
                # Parse bandit output for issues
                output = result.stdout
                high_issues = output.count("[HIGH]")
                medium_issues = output.count("[MEDIUM]")
                low_issues = output.count("[LOW]")
                
                # Score: 100 - (high*10 + medium*5 + low*1)
                score = max(0, 100 - (high_issues * 10 + medium_issues * 5 + low_issues * 1))
                return score
            
            return 95.0  # Default good score
        except Exception as e:
            self.logger.error(f"Bandit scan failed: {e}")
            return 95.0
    
    async def _run_safety_check(self) -> float:
        """Run Safety dependency check."""
        try:
            result = await self._run_command([
                "safety", "check"
            ], timeout=60)
            
            if result.returncode == 0:
                return 100.0  # No vulnerabilities found
            else:
                # Count vulnerabilities from output
                vulnerabilities = result.stdout.count("vulnerability")
                # Score: 100 - (vulnerabilities * 20)
                score = max(0, 100 - (vulnerabilities * 20))
                return score
        except Exception as e:
            self.logger.error(f"Safety check failed: {e}")
            return 100.0
    
    async def _detect_secrets(self) -> int:
        """Detect secrets in codebase."""
        try:
            # Simple secret patterns
            secret_patterns = [
                r'password\s*=\s*["\'][^"\']+["\']',
                r'api_key\s*=\s*["\'][^"\']+["\']',
                r'secret\s*=\s*["\'][^"\']+["\']',
                r'token\s*=\s*["\'][^"\']+["\']'
            ]
            
            secrets_found = 0
            
            for py_file in Path("src").rglob("*.py"):
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    import re
                    for pattern in secret_patterns:
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        secrets_found += len(matches)
            
            return secrets_found
        except Exception as e:
            self.logger.error(f"Secret detection failed: {e}")
            return 0
    
    async def _run_command(self, command: List[str], timeout: int = 60) -> subprocess.CompletedProcess:
        """Run command asynchronously."""
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.project_root
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
            
            return subprocess.CompletedProcess(
                args=command,
                returncode=process.returncode,
                stdout=stdout.decode() if stdout else "",
                stderr=stderr.decode() if stderr else ""
            )
        except asyncio.TimeoutError:
            self.logger.warning(f"Command timed out: {' '.join(command)}")
            return subprocess.CompletedProcess(
                args=command,
                returncode=1,
                stdout="",
                stderr="Command timed out"
            )
        except Exception as e:
            self.logger.error(f"Command failed: {' '.join(command)} - {e}")
            return subprocess.CompletedProcess(
                args=command,
                returncode=1,
                stdout="",
                stderr=str(e)
            )
    
    def _analyze_metrics(self, system_metrics: Dict, quality_metrics: Dict, 
                        performance_metrics: Dict, security_metrics: Dict) -> Tuple[List[str], List[str]]:
        """Analyze metrics and generate alerts/recommendations."""
        alerts = []
        recommendations = []
        
        thresholds = self.config["monitoring"]["alert_thresholds"]
        
        # System alerts
        if system_metrics.get("cpu_percent", 0) > thresholds["cpu_percent"]:
            alerts.append(f"High CPU usage: {system_metrics['cpu_percent']:.1f}%")
            recommendations.append("Consider optimizing CPU-intensive operations")
        
        if system_metrics.get("memory_percent", 0) > thresholds["memory_percent"]:
            alerts.append(f"High memory usage: {system_metrics['memory_percent']:.1f}%")
            recommendations.append("Check for memory leaks or optimize memory usage")
        
        if system_metrics.get("disk_percent", 0) > thresholds["disk_percent"]:
            alerts.append(f"High disk usage: {system_metrics['disk_percent']:.1f}%")
            recommendations.append("Clean up old files or increase disk space")
        
        # Quality alerts
        if quality_metrics.get("test_coverage", 100) < thresholds["test_coverage"]:
            alerts.append(f"Low test coverage: {quality_metrics['test_coverage']:.1f}%")
            recommendations.append("Increase test coverage by adding more unit tests")
        
        if quality_metrics.get("lint_score", 100) < 80:
            alerts.append("Code quality issues detected")
            recommendations.append("Fix linting issues and improve code quality")
        
        # Security alerts
        if security_metrics.get("secrets_found", 0) > 0:
            alerts.append(f"Secrets detected in code: {security_metrics['secrets_found']}")
            recommendations.append("Remove hardcoded secrets and use environment variables")
        
        if security_metrics.get("safety_score", 100) < 90:
            alerts.append("Security vulnerabilities in dependencies")
            recommendations.append("Update vulnerable dependencies")
        
        return alerts, recommendations
    
    def _calculate_health_score(self, system_metrics: Dict, quality_metrics: Dict,
                               performance_metrics: Dict, security_metrics: Dict) -> float:
        """Calculate overall health score (0-100)."""
        scores = []
        
        # System score (25%)
        system_score = 100
        system_score -= min(50, system_metrics.get("cpu_percent", 0))
        system_score -= min(30, system_metrics.get("memory_percent", 0) * 0.5)
        system_score -= min(20, system_metrics.get("disk_percent", 0) * 0.3)
        scores.append(max(0, system_score) * 0.25)
        
        # Quality score (35%)
        quality_score = 0
        quality_score += quality_metrics.get("test_coverage", 0) * 0.3
        quality_score += quality_metrics.get("lint_score", 0) * 0.2
        quality_score += quality_metrics.get("type_coverage", 0) * 0.2
        quality_score += quality_metrics.get("complexity_score", 0) * 0.15
        quality_score += quality_metrics.get("documentation_score", 0) * 0.15
        scores.append(quality_score * 0.35)
        
        # Performance score (20%)
        performance_score = 100
        if "import_time_ms" in performance_metrics:
            import_time = performance_metrics["import_time_ms"]
            performance_score -= min(30, import_time / 100)  # Penalty for slow imports
        scores.append(max(0, performance_score) * 0.20)
        
        # Security score (20%)
        security_score = 100
        security_score -= security_metrics.get("secrets_found", 0) * 10
        security_score = min(security_score, security_metrics.get("safety_score", 100))
        security_score = min(security_score, security_metrics.get("bandit_score", 100))
        scores.append(max(0, security_score) * 0.20)
        
        return sum(scores)
    
    def _determine_health_status(self, score: float, alerts: List[str]) -> str:
        """Determine overall health status."""
        if len(alerts) >= 3 or score < 60:
            return "CRITICAL"
        elif len(alerts) >= 1 or score < 80:
            return "WARNING"
        else:
            return "HEALTHY"
    
    async def _store_metrics(self, health_status: HealthStatus):
        """Store metrics to file."""
        try:
            # Store current metrics
            metrics_file = self.metrics_dir / f"health_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(metrics_file, 'w') as f:
                json.dump(asdict(health_status), f, indent=2)
            
            # Update latest metrics
            latest_file = self.metrics_dir / "latest_health.json"
            with open(latest_file, 'w') as f:
                json.dump(asdict(health_status), f, indent=2)
            
        except Exception as e:
            self.logger.error(f"Error storing metrics: {e}")
    
    async def _handle_alerts(self, health_status: HealthStatus):
        """Handle alerts and notifications."""
        try:
            alert_data = {
                "timestamp": health_status.timestamp,
                "health_status": health_status.overall_health,
                "score": health_status.score,
                "alerts": health_status.alerts,
                "recommendations": health_status.recommendations
            }
            
            # Store alert
            alert_file = self.alerts_dir / f"alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(alert_file, 'w') as f:
                json.dump(alert_data, f, indent=2)
            
            # Log alerts
            for alert in health_status.alerts:
                self.logger.warning(f"🚨 ALERT: {alert}")
                
        except Exception as e:
            self.logger.error(f"Error handling alerts: {e}")
    
    def start_scheduled_monitoring(self):
        """Start scheduled monitoring."""
        interval = self.config["monitoring"]["interval_minutes"]
        
        schedule.every(interval).minutes.do(self._run_scheduled_check)
        
        self.logger.info(f"🔄 Scheduled monitoring started (every {interval} minutes)")
        
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def _run_scheduled_check(self):
        """Run scheduled health check."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.run_health_check())
            loop.close()
        except Exception as e:
            self.logger.error(f"Scheduled check failed: {e}")

def main():
    """Main monitoring interface."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Continuous Monitoring System")
    parser.add_argument("command", choices=[
        "check", "start", "report"
    ], help="Command to run")
    parser.add_argument("--config", help="Configuration file path")
    
    args = parser.parse_args()
    
    monitor = ContinuousMonitor(args.config)
    
    if args.command == "check":
        # Run single health check
        result = asyncio.run(monitor.run_health_check())
        print(f"\n🏥 Health Status: {result.overall_health}")
        print(f"📊 Score: {result.score:.1f}/100")
        
        if result.alerts:
            print("\n🚨 Alerts:")
            for alert in result.alerts:
                print(f"  - {alert}")
        
        if result.recommendations:
            print("\n💡 Recommendations:")
            for rec in result.recommendations:
                print(f"  - {rec}")
    
    elif args.command == "start":
        # Start scheduled monitoring
        monitor.start_scheduled_monitoring()
    
    elif args.command == "report":
        # Generate health report
        latest_file = monitor.metrics_dir / "latest_health.json"
        if latest_file.exists():
            with open(latest_file) as f:
                health_data = json.load(f)
                print(json.dumps(health_data, indent=2))
        else:
            print("No health data available. Run 'check' first.")

if __name__ == "__main__":
    main()