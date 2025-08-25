"""
🛡️ Security Audit System for Telegram Audio Downloader

Enterprise-level security auditing with comprehensive vulnerability scanning,
dependency analysis, secret detection, and security best practices validation.
"""

import os
import re
import hashlib
import subprocess
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import tempfile


@dataclass
class SecurityFinding:
    """Data class for storing security findings."""
    severity: str  # 'critical', 'high', 'medium', 'low', 'info'
    category: str  # 'secrets', 'dependencies', 'permissions', 'code', 'config'
    title: str
    description: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    remediation: Optional[str] = None
    cve_id: Optional[str] = None
    confidence: str = 'medium'  # 'high', 'medium', 'low'


@dataclass
class SecurityReport:
    """Data class for storing complete security audit report."""
    scan_timestamp: datetime
    project_path: str
    total_findings: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    info_count: int
    findings: List[SecurityFinding]
    summary: Dict[str, Any]


class SecurityAuditor:
    """
    Enterprise-level security auditing system.
    
    Features:
    - Secret detection and credential scanning
    - Dependency vulnerability analysis
    - File permission auditing
    - Code pattern security analysis
    - Configuration security validation
    - Automated remediation suggestions
    """
    
    def __init__(self, project_path: str = "."):
        self.project_path = Path(project_path)
        self.findings: List[SecurityFinding] = []
        
        # Common secret patterns
        self.secret_patterns = {
            'api_key': r'(?i)(api[_-]?key|apikey)\s*[:=]\s*["\']?([a-zA-Z0-9_-]{20,})["\']?',
            'password': r'(?i)(password|passwd|pwd)\s*[:=]\s*["\']?([^"\'\s]{8,})["\']?',
            'private_key': r'-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----',
            'aws_access': r'AKIA[0-9A-Z]{16}',
            'aws_secret': r'(?i)aws[_-]?secret[_-]?access[_-]?key\s*[:=]\s*["\']?([a-zA-Z0-9/+=]{40})["\']?',
            'github_token': r'(?i)github[_-]?token\s*[:=]\s*["\']?(ghp_[a-zA-Z0-9]{36})["\']?',
            'jwt_token': r'eyJ[a-zA-Z0-9_-]+\.eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+',
            'database_url': r'(?i)(database[_-]?url|db[_-]?url)\s*[:=]\s*["\']?(postgresql://|mysql://|mongodb://)[^"\'\s]+["\']?',
            'telegram_token': r'(?i)(bot[_-]?token|telegram[_-]?token)\s*[:=]\s*["\']?(\d{8,10}:[a-zA-Z0-9_-]{35})["\']?'
        }
        
        # Insecure code patterns
        self.insecure_patterns = {
            'eval_usage': r'\beval\s*\(',
            'exec_usage': r'\bexec\s*\(',
            'shell_injection': r'subprocess\.(call|run|Popen)\s*\([^)]*shell\s*=\s*True',
            'sql_injection': r'\.execute\s*\([^)]*%s|\.execute\s*\([^)]*\+',
            'hardcoded_secret': r'(?i)(secret|password|key)\s*=\s*["\'][^"\']{8,}["\']',
            'insecure_random': r'random\.random\(\)|random\.choice\(',
            'debug_true': r'(?i)debug\s*=\s*True',
            'insecure_hash': r'hashlib\.(md5|sha1)\(',
        }
        
    def scan_secrets(self) -> List[SecurityFinding]:
        """Scan for exposed secrets and credentials."""
        findings = []
        
        # Scan text files for secret patterns
        for file_path in self.project_path.rglob('*'):
            if file_path.is_file() and self._should_scan_file(file_path):
                try:
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    lines = content.split('\n')
                    
                    for line_num, line in enumerate(lines, 1):
                        for pattern_name, pattern in self.secret_patterns.items():
                            matches = re.finditer(pattern, line)
                            for match in matches:
                                finding = SecurityFinding(
                                    severity='critical',
                                    category='secrets',
                                    title=f'Potential {pattern_name.replace("_", " ").title()} Exposure',
                                    description=f'Possible {pattern_name} found in source code',
                                    file_path=str(file_path.relative_to(self.project_path)),
                                    line_number=line_num,
                                    remediation='Move sensitive data to environment variables or secure configuration',
                                    confidence='medium'
                                )
                                findings.append(finding)
                                
                except Exception as e:
                    # Skip files that can't be read
                    continue  # nosec B112
                    
        return findings
        
    def scan_dependencies(self) -> List[SecurityFinding]:
        """Scan dependencies for known vulnerabilities."""
        findings = []
        
        # Check requirements.txt
        requirements_file = self.project_path / 'requirements.txt'
        if requirements_file.exists():
            findings.extend(self._scan_requirements_file(requirements_file))
            
        # Check setup.py
        setup_file = self.project_path / 'setup.py'
        if setup_file.exists():
            findings.extend(self._scan_setup_file(setup_file))
            
        return findings
        
    def _scan_requirements_file(self, requirements_file: Path) -> List[SecurityFinding]:
        """Scan requirements.txt for security issues."""
        findings = []
        
        try:
            content = requirements_file.read_text()
            lines = content.split('\n')
            
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if line and not line.startswith('#'):
                    # Check for unpinned versions
                    if '==' not in line and '>=' not in line and '~=' not in line:
                        finding = SecurityFinding(
                            severity='medium',
                            category='dependencies',
                            title='Unpinned Dependency Version',
                            description=f'Dependency "{line}" does not have a pinned version',
                            file_path=str(requirements_file.relative_to(self.project_path)),
                            line_number=line_num,
                            remediation='Pin dependency versions to ensure reproducible builds',
                            confidence='high'
                        )
                        findings.append(finding)
                        
                    # Check for known vulnerable patterns
                    if 'django<' in line.lower() or 'flask<' in line.lower():
                        finding = SecurityFinding(
                            severity='high',
                            category='dependencies',
                            title='Potentially Vulnerable Framework Version',
                            description=f'Framework dependency may be using a vulnerable version: {line}',
                            file_path=str(requirements_file.relative_to(self.project_path)),
                            line_number=line_num,
                            remediation='Update to the latest secure version of the framework',
                            confidence='medium'
                        )
                        findings.append(finding)
                        
        except Exception as e:
            finding = SecurityFinding(
                severity='low',
                category='dependencies',
                title='Could not scan requirements.txt',
                description=f'Error reading requirements file: {str(e)}',
                file_path=str(requirements_file.relative_to(self.project_path)),
                remediation='Ensure requirements.txt is readable and properly formatted'
            )
            findings.append(finding)
            
        return findings
        
    def _scan_setup_file(self, setup_file: Path) -> List[SecurityFinding]:
        """Scan setup.py for security issues."""
        findings = []
        
        try:
            content = setup_file.read_text()
            
            # Check for download_url or dependency_links (deprecated and insecure)
            if 'download_url' in content:
                finding = SecurityFinding(
                    severity='medium',
                    category='dependencies',
                    title='Deprecated download_url Usage',
                    description='setup.py uses deprecated download_url which may be insecure',
                    file_path=str(setup_file.relative_to(self.project_path)),
                    remediation='Remove download_url and use PyPI for distribution',
                    confidence='high'
                )
                findings.append(finding)
                
            if 'dependency_links' in content:
                finding = SecurityFinding(
                    severity='high',
                    category='dependencies',
                    title='Insecure dependency_links Usage',
                    description='setup.py uses dependency_links which can be insecure',
                    file_path=str(setup_file.relative_to(self.project_path)),
                    remediation='Remove dependency_links and use standard PyPI dependencies',
                    confidence='high'
                )
                findings.append(finding)
                
        except Exception as e:
            pass  # nosec B110
            
        return findings
        
    def scan_code_patterns(self) -> List[SecurityFinding]:
        """Scan for insecure code patterns."""
        findings = []
        
        for file_path in self.project_path.rglob('*.py'):
            if file_path.is_file():
                try:
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    lines = content.split('\n')
                    
                    for line_num, line in enumerate(lines, 1):
                        for pattern_name, pattern in self.insecure_patterns.items():
                            if re.search(pattern, line):
                                severity = self._get_pattern_severity(pattern_name)
                                finding = SecurityFinding(
                                    severity=severity,
                                    category='code',
                                    title=f'Insecure Code Pattern: {pattern_name.replace("_", " ").title()}',
                                    description=f'Potentially insecure code pattern detected: {pattern_name}',
                                    file_path=str(file_path.relative_to(self.project_path)),
                                    line_number=line_num,
                                    remediation=self._get_pattern_remediation(pattern_name),
                                    confidence='medium'
                                )
                                findings.append(finding)
                                
                except Exception as e:
                    continue  # nosec B112
                    
        return findings
        
    def scan_file_permissions(self) -> List[SecurityFinding]:
        """Scan for insecure file permissions."""
        findings = []
        
        sensitive_files = [
            '.env', '.env.local', '.env.production',
            'config.ini', 'settings.py', 'secrets.json',
            'private.key', '*.pem', 'id_rsa'
        ]
        
        for file_pattern in sensitive_files:
            for file_path in self.project_path.rglob(file_pattern):
                if file_path.is_file():
                    try:
                        # Check if file is readable by others (on Unix systems)
                        if os.name == 'posix':
                            stat_info = file_path.stat()
                            permissions = oct(stat_info.st_mode)[-3:]
                            
                            # Check if file is readable by group or others
                            if permissions[1] != '0' or permissions[2] != '0':
                                finding = SecurityFinding(
                                    severity='high',
                                    category='permissions',
                                    title='Insecure File Permissions',
                                    description=f'Sensitive file has overly permissive permissions: {permissions}',
                                    file_path=str(file_path.relative_to(self.project_path)),
                                    remediation='Set file permissions to 600 (owner read/write only)',
                                    confidence='high'
                                )
                                findings.append(finding)
                                
                    except Exception as e:
                        continue  # nosec B112
                        
        return findings
        
    def scan_configuration(self) -> List[SecurityFinding]:
        """Scan configuration files for security issues."""
        findings = []
        
        # Check .env files
        for env_file in self.project_path.rglob('.env*'):
            if env_file.is_file():
                finding = SecurityFinding(
                    severity='medium',
                    category='config',
                    title='Environment File Present',
                    description='Environment file contains sensitive configuration',
                    file_path=str(env_file.relative_to(self.project_path)),
                    remediation='Ensure .env files are included in .gitignore',
                    confidence='high'
                )
                findings.append(finding)
                
        # Check if .env files are in .gitignore
        gitignore_file = self.project_path / '.gitignore'
        if gitignore_file.exists():
            try:
                gitignore_content = gitignore_file.read_text()
                if '.env' not in gitignore_content:
                    finding = SecurityFinding(
                        severity='high',
                        category='config',
                        title='Environment Files Not Ignored',
                        description='.env files are not included in .gitignore',
                        file_path='.gitignore',
                        remediation='Add .env* to .gitignore to prevent committing secrets',
                        confidence='high'
                    )
                    findings.append(finding)
            except Exception as e:
                pass  # nosec B110
                
        return findings
        
    def _should_scan_file(self, file_path: Path) -> bool:
        """Determine if a file should be scanned for secrets."""
        # Skip binary files and common non-text files
        skip_extensions = {'.pyc', '.pyo', '.jpg', '.png', '.gif', '.pdf', '.zip', '.tar', '.gz'}
        if file_path.suffix.lower() in skip_extensions:
            return False
            
        # Skip large files (>10MB)
        try:
            if file_path.stat().st_size > 10 * 1024 * 1024:
                return False
        except OSError:
            return False
            
        return True
        
    def _get_pattern_severity(self, pattern_name: str) -> str:
        """Get severity level for a code pattern."""
        critical_patterns = ['eval_usage', 'exec_usage', 'shell_injection', 'sql_injection']
        high_patterns = ['hardcoded_secret', 'debug_true']
        medium_patterns = ['insecure_random', 'insecure_hash']
        
        if pattern_name in critical_patterns:
            return 'critical'
        elif pattern_name in high_patterns:
            return 'high'
        elif pattern_name in medium_patterns:
            return 'medium'
        else:
            return 'low'
            
    def _get_pattern_remediation(self, pattern_name: str) -> str:
        """Get remediation advice for a code pattern."""
        remediations = {
            'eval_usage': 'Avoid using eval(). Use ast.literal_eval() for safe evaluation',
            'exec_usage': 'Avoid using exec(). Consider alternative approaches',
            'shell_injection': 'Use shell=False and pass arguments as a list',
            'sql_injection': 'Use parameterized queries instead of string concatenation',
            'hardcoded_secret': 'Move secrets to environment variables',
            'insecure_random': 'Use secrets module for cryptographically secure random values',
            'debug_true': 'Set debug=False in production',
            'insecure_hash': 'Use SHA-256 or stronger hashing algorithms'
        }
        return remediations.get(pattern_name, 'Review code for security implications')
        
    def run_full_audit(self) -> SecurityReport:
        """Run complete security audit."""
        print("🛡️ Starting Comprehensive Security Audit...")
        
        # Clear previous findings
        self.findings = []
        
        # Run all scans
        print("🔍 Scanning for secrets...")
        self.findings.extend(self.scan_secrets())
        
        print("📦 Scanning dependencies...")
        self.findings.extend(self.scan_dependencies())
        
        print("🐍 Scanning code patterns...")
        self.findings.extend(self.scan_code_patterns())
        
        print("🔐 Scanning file permissions...")
        self.findings.extend(self.scan_file_permissions())
        
        print("⚙️ Scanning configuration...")
        self.findings.extend(self.scan_configuration())
        
        # Generate summary
        severity_counts = {
            'critical': len([f for f in self.findings if f.severity == 'critical']),
            'high': len([f for f in self.findings if f.severity == 'high']),
            'medium': len([f for f in self.findings if f.severity == 'medium']),
            'low': len([f for f in self.findings if f.severity == 'low']),
            'info': len([f for f in self.findings if f.severity == 'info'])
        }
        
        category_counts = {}
        for finding in self.findings:
            category_counts[finding.category] = category_counts.get(finding.category, 0) + 1
            
        summary = {
            'total_files_scanned': len(list(self.project_path.rglob('*'))),
            'severity_distribution': severity_counts,
            'category_distribution': category_counts,
            'high_confidence_findings': len([f for f in self.findings if f.confidence == 'high']),
            'scan_duration': 'completed',
            'recommendations': self._generate_recommendations()
        }
        
        report = SecurityReport(
            scan_timestamp=datetime.now(),
            project_path=str(self.project_path),
            total_findings=len(self.findings),
            critical_count=severity_counts['critical'],
            high_count=severity_counts['high'],
            medium_count=severity_counts['medium'],
            low_count=severity_counts['low'],
            info_count=severity_counts['info'],
            findings=self.findings,
            summary=summary
        )
        
        print(f"✅ Security Audit Complete! Found {len(self.findings)} issues.")
        return report
        
    def _generate_recommendations(self) -> List[str]:
        """Generate security recommendations based on findings."""
        recommendations = []
        
        if any(f.category == 'secrets' for f in self.findings):
            recommendations.append("Implement secret management solution (e.g., environment variables, Azure Key Vault)")
            
        if any(f.category == 'dependencies' for f in self.findings):
            recommendations.append("Set up automated dependency vulnerability scanning")
            
        if any(f.severity == 'critical' for f in self.findings):
            recommendations.append("Address critical security issues immediately before deployment")
            
        if any(f.category == 'permissions' for f in self.findings):
            recommendations.append("Review and restrict file permissions for sensitive files")
            
        recommendations.extend([
            "Implement security linting in CI/CD pipeline",
            "Regular security audits and penetration testing",
            "Security awareness training for development team"
        ])
        
        return recommendations
        
    def export_report(self, report: SecurityReport, format: str = 'json') -> str:
        """Export security report in specified format."""
        if format.lower() == 'json':
            return self._export_json(report)
        elif format.lower() == 'html':
            return self._export_html(report)
        else:
            raise ValueError("Supported formats: 'json', 'html'")
            
    def _export_json(self, report: SecurityReport) -> str:
        """Export report as JSON."""
        def json_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
            
        return json.dumps(asdict(report), indent=2, default=json_serializer)
        
    def _export_html(self, report: SecurityReport) -> str:
        """Export report as HTML."""
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Security Audit Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .critical { color: #d32f2f; }
                .high { color: #f57c00; }
                .medium { color: #fbc02d; }
                .low { color: #388e3c; }
                .finding { margin: 10px 0; padding: 10px; border-left: 4px solid #ccc; }
            </style>
        </head>
        <body>
            <h1>🛡️ Security Audit Report</h1>
            <p><strong>Scan Date:</strong> {scan_date}</p>
            <p><strong>Project:</strong> {project_path}</p>
            <p><strong>Total Findings:</strong> {total_findings}</p>
            
            <h2>Summary</h2>
            <ul>
                <li>Critical: {critical_count}</li>
                <li>High: {high_count}</li>
                <li>Medium: {medium_count}</li>
                <li>Low: {low_count}</li>
            </ul>
            
            <h2>Findings</h2>
            {findings_html}
        </body>
        </html>
        """
        
        findings_html = ""
        for finding in report.findings:
            findings_html += f"""
            <div class="finding {finding.severity}">
                <h3>{finding.title}</h3>
                <p><strong>Severity:</strong> {finding.severity.upper()}</p>
                <p><strong>Category:</strong> {finding.category}</p>
                <p>{finding.description}</p>
                {f'<p><strong>File:</strong> {finding.file_path}:{finding.line_number}</p>' if finding.file_path else ''}
                {f'<p><strong>Remediation:</strong> {finding.remediation}</p>' if finding.remediation else ''}
            </div>
            """
            
        return html_template.format(
            scan_date=report.scan_timestamp.isoformat(),
            project_path=report.project_path,
            total_findings=report.total_findings,
            critical_count=report.critical_count,
            high_count=report.high_count,
            medium_count=report.medium_count,
            low_count=report.low_count,
            findings_html=findings_html
        )


# Example usage and demo
async def demo_security_audit():
    """Demonstrate the security audit system."""
    print("🛡️ Security Audit Demo")
    print("=" * 50)
    
    # Initialize auditor
    auditor = SecurityAuditor(".")
    
    # Run full audit
    report = auditor.run_full_audit()
    
    # Print summary
    print(f"\n📊 Audit Summary:")
    print(f"Total Issues: {report.total_findings}")
    print(f"Critical: {report.critical_count}")
    print(f"High: {report.high_count}")
    print(f"Medium: {report.medium_count}")
    print(f"Low: {report.low_count}")
    
    # Export report
    json_report = auditor.export_report(report, 'json')
    print(f"\n💾 JSON Report Generated ({len(json_report)} characters)")
    
    return report


if __name__ == "__main__":
    # Run demo if script is executed directly
    import asyncio
    asyncio.run(demo_security_audit())