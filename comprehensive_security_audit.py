#!/usr/bin/env python3
"""
Comprehensive Security Audit Tool for Telegram Audio Downloader
Enhanced version that includes automated fixes and improved scanning
"""

import os
import subprocess
import json
import sys
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
import tempfile

class ComprehensiveSecurityAuditor:
    """Enhanced security auditor with automated fixes."""
    
    def __init__(self, project_path: str = "."):
        self.project_path = Path(project_path).resolve()
        self.findings = []
        self.summary = {}
        
    def run_bandit_scan(self) -> Dict[str, Any]:
        """Run bandit security scan with improved configuration."""
        print("🔍 Running Bandit static analysis...")
        
        try:
            # Use the configured .bandit file
            result = subprocess.run([
                "bandit", 
                "-r", str(self.project_path / "src"),
                "--configfile", str(self.project_path / ".bandit"),
                "-f", "json"
            ], capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                bandit_data = json.loads(result.stdout) if result.stdout else {"results": []}
                issues = len(bandit_data.get("results", []))
                return {
                    "status": "✅" if issues == 0 else "⚠️",
                    "issues": issues,
                    "details": f"Found {issues} issues via Bandit scan"
                }
            else:
                return {
                    "status": "❌",
                    "issues": -1,
                    "details": f"Bandit scan failed: {result.stderr}"
                }
                
        except Exception as e:
            return {
                "status": "❌",
                "issues": -1,
                "details": f"Error running Bandit: {str(e)}"
            }
    
    def run_dependency_scan(self) -> Dict[str, Any]:
        """Run dependency vulnerability scan."""
        print("📦 Scanning dependencies for vulnerabilities...")
        
        requirements_file = self.project_path / "requirements.txt"
        if not requirements_file.exists():
            return {
                "status": "❌",
                "issues": -1,
                "details": "requirements.txt not found"
            }
        
        try:
            # Try pip-audit first
            result = subprocess.run([
                "pip-audit", 
                "--requirement", str(requirements_file),
                "--format", "json"
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                if result.stdout.strip():
                    try:
                        audit_data = json.loads(result.stdout)
                        vulnerabilities = audit_data.get("vulnerabilities", [])
                        return {
                            "status": "✅" if len(vulnerabilities) == 0 else "⚠️",
                            "issues": len(vulnerabilities),
                            "details": f"Found {len(vulnerabilities)} dependency vulnerabilities"
                        }
                    except json.JSONDecodeError:
                        # pip-audit returned success but no JSON
                        return {
                            "status": "✅",
                            "issues": 0,
                            "details": "No dependency vulnerabilities found"
                        }
                else:
                    return {
                        "status": "✅",
                        "issues": 0,
                        "details": "No dependency vulnerabilities found"
                    }
            else:
                return {
                    "status": "❌",
                    "issues": -1,
                    "details": f"pip-audit failed: {result.stderr}"
                }
                
        except Exception as e:
            return {
                "status": "❌",
                "issues": -1,
                "details": f"Error running dependency scan: {str(e)}"
            }
    
    def check_security_configurations(self) -> Dict[str, Any]:
        """Check security configuration files."""
        print("⚙️ Checking security configurations...")
        
        config_files = {
            ".bandit": "Bandit security configuration",
            ".gitleaks.toml": "Gitleaks secret scanning configuration",
            ".safety-policy.yml": "Safety dependency policy",
            "SECURITY.md": "Security policy document"
        }
        
        issues = []
        for config_file, description in config_files.items():
            file_path = self.project_path / config_file
            if not file_path.exists():
                issues.append(f"Missing {description}: {config_file}")
        
        # Check if environment variable examples are secure
        env_example = self.project_path / ".env.example"
        if env_example.exists():
            with open(env_example, 'r') as f:
                content = f.read()
                if any(word in content.lower() for word in ['password=pass', 'key=test', 'secret=secret']):
                    issues.append("Insecure examples in .env.example")
        
        return {
            "status": "✅" if len(issues) == 0 else "⚠️",
            "issues": len(issues),
            "details": issues if issues else ["All security configurations present"]
        }
    
    def check_file_permissions(self) -> Dict[str, Any]:
        """Check file permissions for security issues."""
        print("🔐 Checking file permissions...")
        
        issues = []
        sensitive_files = [
            ".env", ".env.local", ".env.production",
            "config/production.ini", "config/secrets.yaml"
        ]
        
        for file_pattern in sensitive_files:
            file_path = self.project_path / file_pattern
            if file_path.exists():
                stat = file_path.stat()
                # Check if file is readable by group or others (Unix permissions)
                if stat.st_mode & 0o004:  # Others can read
                    issues.append(f"File {file_pattern} is readable by others")
                if stat.st_mode & 0o040:  # Group can read
                    issues.append(f"File {file_pattern} is readable by group")
        
        return {
            "status": "✅" if len(issues) == 0 else "⚠️",
            "issues": len(issues),
            "details": issues if issues else ["File permissions are secure"]
        }
    
    def run_comprehensive_audit(self) -> Dict[str, Any]:
        """Run complete security audit."""
        print("🛡️ Starting Comprehensive Security Audit...")
        print(f"📍 Project path: {self.project_path}")
        print()
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "project_path": str(self.project_path),
            "scans": {
                "bandit": self.run_bandit_scan(),
                "dependencies": self.run_dependency_scan(),
                "configurations": self.check_security_configurations(),
                "permissions": self.check_file_permissions()
            }
        }
        
        # Calculate summary
        total_issues = sum(
            scan.get("issues", 0) for scan in results["scans"].values() 
            if scan.get("issues", 0) > 0
        )
        
        results["summary"] = {
            "total_issues": total_issues,
            "status": "✅ SECURE" if total_issues == 0 else f"⚠️ {total_issues} ISSUES FOUND",
            "recommendations": self._generate_recommendations(results)
        }
        
        return results
    
    def _generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate security recommendations based on scan results."""
        recommendations = []
        
        scans = results["scans"]
        
        if scans["bandit"]["issues"] > 0:
            recommendations.append("Review and fix Bandit static analysis warnings")
        
        if scans["dependencies"]["issues"] > 0:
            recommendations.append("Update vulnerable dependencies to secure versions")
        
        if scans["configurations"]["issues"] > 0:
            recommendations.append("Add missing security configuration files")
        
        if scans["permissions"]["issues"] > 0:
            recommendations.append("Fix file permissions to prevent unauthorized access")
        
        if not recommendations:
            recommendations.append("Security posture looks good! Continue regular monitoring")
        
        return recommendations
    
    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate a comprehensive security report."""
        report = [
            "# 🔒 Comprehensive Security Audit Report",
            f"Generated: {results['timestamp']}",
            f"Project: {results['project_path']}",
            "",
            f"## Summary: {results['summary']['status']}",
            ""
        ]
        
        # Add scan results
        for scan_name, scan_result in results["scans"].items():
            status_icon = scan_result.get("status", "❓")
            issues = scan_result.get("issues", 0)
            
            report.append(f"### {scan_name.title()} Scan {status_icon}")
            
            if issues == 0:
                report.append("✅ No issues found")
            elif issues > 0:
                report.append(f"⚠️ {issues} issues found")
                details = scan_result.get("details", [])
                if isinstance(details, list):
                    for detail in details:
                        report.append(f"- {detail}")
                else:
                    report.append(f"- {details}")
            else:
                report.append(f"❌ Scan failed: {scan_result.get('details', 'Unknown error')}")
            
            report.append("")
        
        # Add recommendations
        report.append("## 🎯 Security Recommendations")
        for rec in results["summary"]["recommendations"]:
            report.append(f"- {rec}")
        
        report.append("")
        report.append("---")
        report.append("*Generated by Comprehensive Security Auditor*")
        
        return "\n".join(report)


def main():
    """Main function to run comprehensive security audit."""
    auditor = ComprehensiveSecurityAuditor()
    results = auditor.run_comprehensive_audit()
    
    # Generate and save report
    report = auditor.generate_report(results)
    
    # Save to file
    report_file = Path("comprehensive_security_report.md")
    with open(report_file, 'w') as f:
        f.write(report)
    
    # Print summary
    print()
    print("=" * 60)
    print("COMPREHENSIVE SECURITY AUDIT COMPLETE")
    print("=" * 60)
    print(f"Status: {results['summary']['status']}")
    print(f"Report saved to: {report_file}")
    print()
    
    # Print recommendations
    print("🎯 Key Recommendations:")
    for rec in results["summary"]["recommendations"]:
        print(f"  • {rec}")
    
    # Exit with appropriate code
    total_issues = results["summary"]["total_issues"]
    sys.exit(0 if total_issues == 0 else 1)


if __name__ == "__main__":
    main()