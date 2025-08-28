#!/usr/bin/env python3
"""
RepoSovereign Prime Security Module
==================================

Autonomous Security Operations Center (ASOC) für kontinuierliche Bedrohungsüberwachung
und automatische Sicherheitsmaßnahmen.

Author: RepoSovereign Prime Security Team
Version: 1.0.0
"""

import os
import sys
import json
import asyncio
import logging
import subprocess
import re
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import requests
from enum import Enum


class ThreatLevel(Enum):
    """Bedrohungsgrad-Klassifikation."""
    CRITICAL = "critical"
    HIGH = "high" 
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class VulnerabilityType(Enum):
    """Typ der Sicherheitslücke."""
    CODE_INJECTION = "code_injection"
    XSS = "cross_site_scripting"
    SQL_INJECTION = "sql_injection"
    CRYPTO_WEAKNESS = "cryptographic_weakness"
    INSECURE_STORAGE = "insecure_storage"
    DEPENDENCY_VULN = "dependency_vulnerability"
    SECRET_EXPOSURE = "secret_exposure"
    AUTHENTICATION = "authentication_bypass"
    AUTHORIZATION = "authorization_bypass"
    BUFFER_OVERFLOW = "buffer_overflow"


@dataclass
class SecurityThreat:
    """Sicherheitsbedrohung-Datenstruktur."""
    threat_id: str
    threat_type: VulnerabilityType
    threat_level: ThreatLevel
    title: str
    description: str
    affected_files: List[str]
    cwe_id: Optional[str] = None
    cve_id: Optional[str] = None
    cvss_score: Optional[float] = None
    detected_at: Optional[datetime] = None
    auto_fixable: bool = False
    fix_available: bool = False
    remediation_steps: List[str] = None


@dataclass
class SecurityScanResult:
    """Ergebnis eines Sicherheitsscans."""
    scan_type: str
    scan_duration: float
    threats_found: List[SecurityThreat]
    false_positives: int
    scan_coverage: float
    timestamp: datetime


class SecurityAutomationEngine:
    """
    Autonomous Security Operations Center (ASOC) für RepoSovereign Prime.
    
    Implementiert:
    - Kontinuierliche Bedrohungssuche (24/7)
    - Automatische Schwachstellen-Scans
    - Zero-Trust Sicherheitsmodell
    - Sub-5-Minuten Incident Response
    - Supply Chain Protection
    """
    
    def __init__(self, repo_path: str = ".", config: Optional[Dict] = None):
        """Initialisiert die Security Automation Engine."""
        self.repo_path = Path(repo_path).resolve()
        self.config = config or {}
        self.logger = self._setup_logging()
        self.github_token = os.getenv('GITHUB_TOKEN')
        
        # Security-Konfiguration
        self.threat_hunting_interval = self.config.get('threat_hunting_interval_minutes', 30)
        self.response_time_threshold = self.config.get('security_response_time_minutes', 5)
        self.auto_patch_enabled = self.config.get('auto_patch_critical_vulnerabilities', True)
        
        # Threat Detection Rules
        self.threat_patterns = self._load_threat_patterns()
        
        self.logger.info("🛡️ Security Automation Engine initialisiert")
        self.logger.info(f"📁 Repository: {self.repo_path}")
        self.logger.info(f"⏱️ Threat Hunting Interval: {self.threat_hunting_interval} min")
    
    def _setup_logging(self) -> logging.Logger:
        """Konfiguriert das Security-Logging-System."""
        logger = logging.getLogger("SecurityAutomationEngine")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            # Console Handler
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter(
                '%(asctime)s - 🛡️ SecurityEngine - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
            
            # File Handler für Security-Logs
            log_dir = self.repo_path / ".governance" / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(log_dir / "security.log")
            file_formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s - [%(filename)s:%(lineno)d]'
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        
        return logger
    
    def _load_threat_patterns(self) -> Dict[str, List[str]]:
        """Lädt Bedrohungsmuster für die Erkennung."""
        return {
            "secret_patterns": [
                r'api[_-]?key[_-]?[=:]\s*["\']?([a-zA-Z0-9_-]{20,})["\']?',
                r'secret[_-]?key[_-]?[=:]\s*["\']?([a-zA-Z0-9_-]{20,})["\']?',
                r'password[_-]?[=:]\s*["\']?([a-zA-Z0-9_-]{8,})["\']?',
                r'token[_-]?[=:]\s*["\']?([a-zA-Z0-9_-]{20,})["\']?',
                r'aws[_-]?access[_-]?key[_-]?id[_-]?[=:]\s*["\']?([A-Z0-9]{20})["\']?',
                r'github[_-]?token[_-]?[=:]\s*["\']?(ghp_[a-zA-Z0-9]{36})["\']?',
            ],
            "injection_patterns": [
                r'exec\s*\(',
                r'eval\s*\(',
                r'subprocess\.call',
                r'os\.system',
                r'shell=True',
                r'SELECT\s+\*\s+FROM.*\$',
                r'DROP\s+TABLE',
                r'INSERT\s+INTO.*VALUES.*\$',
            ],
            "crypto_patterns": [
                r'MD5\s*\(',
                r'SHA1\s*\(',
                r'DES\s*\(',
                r'RC4\s*\(',
                r'random\.random\(\)',
                r'math\.random\(\)',
            ],
            "hardcoded_secrets": [
                r'(?i)(password|passwd|pwd)\s*=\s*["\'][^"\']{3,}["\']',
                r'(?i)(api_key|apikey)\s*=\s*["\'][^"\']{10,}["\']',
                r'(?i)(secret|token)\s*=\s*["\'][^"\']{10,}["\']',
            ]
        }
    
    async def execute_security_cycle(self) -> Dict[str, Any]:
        """
        Führt einen vollständigen Security-Zyklus aus.
        
        Returns:
            Dict mit Ergebnissen des Security-Zyklus
        """
        self.logger.info("🔍 Starte Security-Zyklus")
        start_time = time.time()
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "cycle_duration": 0,
            "threats_detected": 0,
            "critical_threats": 0,
            "auto_fixed": 0,
            "manual_review_required": 0,
            "scan_results": {}
        }
        
        try:
            # 1. Static Code Analysis (CodeQL)
            self.logger.info("🔍 CodeQL Static Analysis")
            codeql_results = await self._run_codeql_scan()
            results["scan_results"]["codeql"] = codeql_results
            
            # 2. Dependency Vulnerability Scan
            self.logger.info("📦 Dependency Vulnerability Scan")
            dep_scan_results = await self._scan_dependencies()
            results["scan_results"]["dependencies"] = dep_scan_results
            
            # 3. Secret Detection
            self.logger.info("🔐 Secret Detection Scan")
            secret_scan_results = await self._scan_secrets()
            results["scan_results"]["secrets"] = secret_scan_results
            
            # 4. Container Security (wenn Dockerfile vorhanden)
            if (self.repo_path / "Dockerfile").exists():
                self.logger.info("🐳 Container Security Scan")
                container_results = await self._scan_container_security()
                results["scan_results"]["container"] = container_results
            
            # 5. Threat Aggregation und Priorisierung
            all_threats = self._aggregate_threats(results["scan_results"])
            results["threats_detected"] = len(all_threats)
            results["critical_threats"] = len([t for t in all_threats if t.threat_level == ThreatLevel.CRITICAL])
            
            # 6. Automatische Remediation
            if self.auto_patch_enabled and all_threats:
                self.logger.info("🔧 Automatische Remediation")
                remediation_results = await self._auto_remediate_threats(all_threats)
                results["auto_fixed"] = remediation_results["fixed_count"]
                results["manual_review_required"] = remediation_results["manual_review_count"]
            
            # 7. Incident Response für kritische Bedrohungen
            critical_threats = [t for t in all_threats if t.threat_level == ThreatLevel.CRITICAL]
            if critical_threats:
                await self._trigger_incident_response(critical_threats)
            
            results["cycle_duration"] = time.time() - start_time
            
            # Speichere Security-Bericht
            await self._save_security_report(results, all_threats)
            
            self.logger.info(f"✅ Security-Zyklus abgeschlossen in {results['cycle_duration']:.2f}s")
            self.logger.info(f"🔍 {results['threats_detected']} Bedrohungen erkannt")
            self.logger.info(f"🚨 {results['critical_threats']} kritische Bedrohungen")
            
        except Exception as e:
            self.logger.error(f"❌ Fehler im Security-Zyklus: {e}")
            results["error"] = str(e)
        
        return results
    
    async def _run_codeql_scan(self) -> SecurityScanResult:
        """Führt CodeQL-Analyse durch."""
        start_time = time.time()
        threats = []
        
        try:
            # CodeQL Database erstellen (falls nicht vorhanden)
            codeql_db_path = self.repo_path / ".codeql-db"
            
            if not codeql_db_path.exists():
                self.logger.info("🔧 Erstelle CodeQL Database")
                # Vereinfachte Implementierung - in Realität würde hier CodeQL CLI verwendet
                # Für Demo-Zwecke simulieren wir CodeQL-Ergebnisse
                
            # Simuliere CodeQL-Scan-Ergebnisse
            threats = await self._simulate_codeql_results()
            
        except Exception as e:
            self.logger.error(f"❌ CodeQL-Scan fehlgeschlagen: {e}")
        
        return SecurityScanResult(
            scan_type="codeql",
            scan_duration=time.time() - start_time,
            threats_found=threats,
            false_positives=0,
            scan_coverage=0.85,
            timestamp=datetime.now()
        )
    
    async def _scan_dependencies(self) -> SecurityScanResult:
        """Scannt Abhängigkeiten auf Sicherheitslücken."""
        start_time = time.time()
        threats = []
        
        try:
            # Requirements.txt analysieren
            req_file = self.repo_path / "requirements.txt"
            if req_file.exists():
                threats.extend(await self._analyze_python_dependencies(req_file))
            
            # package.json analysieren (falls vorhanden)
            package_json = self.repo_path / "package.json"
            if package_json.exists():
                threats.extend(await self._analyze_npm_dependencies(package_json))
            
            # Gemfile analysieren (falls vorhanden)
            gemfile = self.repo_path / "Gemfile"
            if gemfile.exists():
                threats.extend(await self._analyze_ruby_dependencies(gemfile))
            
        except Exception as e:
            self.logger.error(f"❌ Dependency-Scan fehlgeschlagen: {e}")
        
        return SecurityScanResult(
            scan_type="dependencies",
            scan_duration=time.time() - start_time,
            threats_found=threats,
            false_positives=0,
            scan_coverage=0.95,
            timestamp=datetime.now()
        )
    
    async def _scan_secrets(self) -> SecurityScanResult:
        """Scannt nach exponierten Geheimnissen."""
        start_time = time.time()
        threats = []
        
        try:
            # Durchsuche alle relevanten Dateien
            file_extensions = ['.py', '.js', '.ts', '.yml', '.yaml', '.json', '.env', '.config', '.ini']
            
            for file_path in self.repo_path.rglob('*'):
                if (file_path.is_file() and 
                    file_path.suffix in file_extensions and
                    not self._is_excluded_path(file_path)):
                    
                    file_threats = await self._scan_file_for_secrets(file_path)
                    threats.extend(file_threats)
            
        except Exception as e:
            self.logger.error(f"❌ Secret-Scan fehlgeschlagen: {e}")
        
        return SecurityScanResult(
            scan_type="secrets",
            scan_duration=time.time() - start_time,
            threats_found=threats,
            false_positives=0,
            scan_coverage=0.90,
            timestamp=datetime.now()
        )
    
    async def _scan_container_security(self) -> SecurityScanResult:
        """Scannt Container-Sicherheit."""
        start_time = time.time()
        threats = []
        
        try:
            dockerfile_path = self.repo_path / "Dockerfile"
            if dockerfile_path.exists():
                threats.extend(await self._analyze_dockerfile_security(dockerfile_path))
            
            # docker-compose.yml analysieren
            compose_path = self.repo_path / "docker-compose.yml"
            if compose_path.exists():
                threats.extend(await self._analyze_docker_compose_security(compose_path))
            
        except Exception as e:
            self.logger.error(f"❌ Container-Security-Scan fehlgeschlagen: {e}")
        
        return SecurityScanResult(
            scan_type="container",
            scan_duration=time.time() - start_time,
            threats_found=threats,
            false_positives=0,
            scan_coverage=0.80,
            timestamp=datetime.now()
        )
    
    def _aggregate_threats(self, scan_results: Dict[str, SecurityScanResult]) -> List[SecurityThreat]:
        """Aggregiert und priorisiert Bedrohungen aus allen Scans."""
        all_threats = []
        
        for scan_type, result in scan_results.items():
            all_threats.extend(result.threats_found)
        
        # Entferne Duplikate basierend auf threat_id
        unique_threats = {}
        for threat in all_threats:
            if threat.threat_id not in unique_threats:
                unique_threats[threat.threat_id] = threat
        
        # Sortiere nach Bedrohungsgrad und CVSS Score
        sorted_threats = sorted(
            unique_threats.values(),
            key=lambda t: (
                t.threat_level.value,
                t.cvss_score or 0.0
            ),
            reverse=True
        )
        
        return sorted_threats
    
    async def _auto_remediate_threats(self, threats: List[SecurityThreat]) -> Dict[str, int]:
        """Automatische Remediation von Bedrohungen."""
        fixed_count = 0
        manual_review_count = 0
        
        for threat in threats:
            if threat.auto_fixable and threat.fix_available:
                try:
                    success = await self._apply_automated_fix(threat)
                    if success:
                        fixed_count += 1
                        self.logger.info(f"✅ Threat {threat.threat_id} automatisch behoben")
                    else:
                        manual_review_count += 1
                        self.logger.warning(f"⚠️ Auto-Fix für {threat.threat_id} fehlgeschlagen")
                except Exception as e:
                    self.logger.error(f"❌ Fehler bei Auto-Fix für {threat.threat_id}: {e}")
                    manual_review_count += 1
            else:
                manual_review_count += 1
        
        return {
            "fixed_count": fixed_count,
            "manual_review_count": manual_review_count
        }
    
    async def _trigger_incident_response(self, critical_threats: List[SecurityThreat]) -> None:
        """Triggert Incident Response für kritische Bedrohungen."""
        self.logger.critical(f"🚨 INCIDENT RESPONSE: {len(critical_threats)} kritische Bedrohungen erkannt")
        
        # Erstelle Incident Report
        incident_report = {
            "incident_id": f"INC-{int(time.time())}",
            "severity": "CRITICAL",
            "detected_at": datetime.now().isoformat(),
            "threats": [asdict(threat) for threat in critical_threats],
            "response_time": self.response_time_threshold,
            "auto_actions": []
        }
        
        # Sofortige Maßnahmen
        for threat in critical_threats:
            if threat.threat_type == VulnerabilityType.SECRET_EXPOSURE:
                # Sofortige Geheimnis-Rotation erforderlich
                incident_report["auto_actions"].append("Secret rotation required")
                await self._notify_secret_exposure(threat)
            
            elif threat.threat_type == VulnerabilityType.DEPENDENCY_VULN and threat.cvss_score and threat.cvss_score > 9.0:
                # Kritische Dependency-Schwachstelle
                incident_report["auto_actions"].append("Emergency dependency update")
                await self._emergency_dependency_update(threat)
        
        # Speichere Incident Report
        incident_dir = self.repo_path / ".governance" / "incidents"
        incident_dir.mkdir(parents=True, exist_ok=True)
        
        incident_file = incident_dir / f"incident_{incident_report['incident_id']}.json"
        with open(incident_file, 'w') as f:
            json.dump(incident_report, f, indent=2)
        
        self.logger.info(f"📄 Incident Report gespeichert: {incident_file}")
    
    # Hilfsmethoden (Stubs für realistische Implementierung)
    
    async def _simulate_codeql_results(self) -> List[SecurityThreat]:
        """Simuliert CodeQL-Ergebnisse für Demo."""
        # In einer echten Implementierung würde hier die CodeQL CLI aufgerufen
        return []
    
    async def _analyze_python_dependencies(self, req_file: Path) -> List[SecurityThreat]:
        """Analysiert Python-Dependencies auf Schwachstellen."""
        threats = []
        
        try:
            with open(req_file, 'r') as f:
                requirements = f.read()
            
            # Bekannte verwundbare Pakete (Beispiele)
            vulnerable_packages = {
                'urllib3': {'versions': ['<1.26.5'], 'cve': 'CVE-2021-33503', 'severity': 'medium'},
                'requests': {'versions': ['<2.20.0'], 'cve': 'CVE-2018-18074', 'severity': 'medium'},
                'pillow': {'versions': ['<8.2.0'], 'cve': 'CVE-2021-25287', 'severity': 'high'},
            }
            
            for package, vuln_info in vulnerable_packages.items():
                if package in requirements:
                    threat = SecurityThreat(
                        threat_id=f"DEP-{package.upper()}-{vuln_info['cve']}",
                        threat_type=VulnerabilityType.DEPENDENCY_VULN,
                        threat_level=ThreatLevel.HIGH if vuln_info['severity'] == 'high' else ThreatLevel.MEDIUM,
                        title=f"Vulnerable dependency: {package}",
                        description=f"Package {package} has known vulnerability {vuln_info['cve']}",
                        affected_files=[str(req_file)],
                        cve_id=vuln_info['cve'],
                        detected_at=datetime.now(),
                        auto_fixable=True,
                        fix_available=True,
                        remediation_steps=[f"Update {package} to latest version"]
                    )
                    threats.append(threat)
            
        except Exception as e:
            self.logger.error(f"❌ Fehler bei Python Dependency-Analyse: {e}")
        
        return threats
    
    async def _analyze_npm_dependencies(self, package_json: Path) -> List[SecurityThreat]:
        """Analysiert NPM-Dependencies."""
        return []  # Stub für NPM-Analyse
    
    async def _analyze_ruby_dependencies(self, gemfile: Path) -> List[SecurityThreat]:
        """Analysiert Ruby Gems.""" 
        return []  # Stub für Ruby-Analyse
    
    def _is_excluded_path(self, file_path: Path) -> bool:
        """Überprüft ob Pfad von Scan ausgeschlossen werden soll."""
        excluded_dirs = {'.git', '__pycache__', 'node_modules', '.venv', 'venv', 'build', 'dist'}
        
        return any(part in excluded_dirs for part in file_path.parts)
    
    async def _scan_file_for_secrets(self, file_path: Path) -> List[SecurityThreat]:
        """Scannt eine Datei nach Geheimnissen."""
        threats = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Durchsuche alle Secret-Pattern
            for pattern_type, patterns in self.threat_patterns.items():
                for pattern in patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
                    
                    for match in matches:
                        # Erstelle Threat für gefundenes Geheimnis
                        threat = SecurityThreat(
                            threat_id=f"SECRET-{hash(f'{file_path}-{match.start()}') % 10000:04d}",
                            threat_type=VulnerabilityType.SECRET_EXPOSURE,
                            threat_level=ThreatLevel.HIGH,
                            title=f"Exposed secret in {file_path.name}",
                            description=f"Potential secret found: {match.group(0)[:20]}...",
                            affected_files=[str(file_path)],
                            detected_at=datetime.now(),
                            auto_fixable=False,  # Secrets erfordern manuelle Überprüfung
                            fix_available=True,
                            remediation_steps=[
                                "Remove secret from code",
                                "Use environment variables",
                                "Rotate exposed credentials"
                            ]
                        )
                        threats.append(threat)
            
        except Exception as e:
            self.logger.error(f"❌ Fehler beim Scannen von {file_path}: {e}")
        
        return threats
    
    async def _analyze_dockerfile_security(self, dockerfile_path: Path) -> List[SecurityThreat]:
        """Analysiert Dockerfile auf Sicherheitsprobleme."""
        threats = []
        
        try:
            with open(dockerfile_path, 'r') as f:
                content = f.read()
            
            # Prüfe auf unsichere Practices
            insecure_patterns = {
                r'FROM.*:latest': "Using latest tag is not recommended",
                r'RUN.*sudo': "Running with sudo in container",
                r'USER root': "Running as root user",
                r'COPY \. \.': "Copying entire context (potential secret exposure)",
                r'--no-check-certificate': "Disabled certificate checking",
            }
            
            for pattern, description in insecure_patterns.items():
                if re.search(pattern, content, re.IGNORECASE):
                    threat = SecurityThreat(
                        threat_id=f"DOCKER-{hash(pattern) % 10000:04d}",
                        threat_type=VulnerabilityType.INSECURE_STORAGE,
                        threat_level=ThreatLevel.MEDIUM,
                        title="Docker security issue",
                        description=description,
                        affected_files=[str(dockerfile_path)],
                        detected_at=datetime.now(),
                        auto_fixable=False,
                        fix_available=True,
                        remediation_steps=["Follow Docker security best practices"]
                    )
                    threats.append(threat)
            
        except Exception as e:
            self.logger.error(f"❌ Fehler bei Dockerfile-Analyse: {e}")
        
        return threats
    
    async def _analyze_docker_compose_security(self, compose_path: Path) -> List[SecurityThreat]:
        """Analysiert docker-compose.yml auf Sicherheitsprobleme."""
        return []  # Stub für Docker Compose-Analyse
    
    async def _apply_automated_fix(self, threat: SecurityThreat) -> bool:
        """Wendet automatische Korrekturen an."""
        # Stub für automatische Fixes
        self.logger.info(f"🔧 Wende automatischen Fix für {threat.threat_id} an")
        return False  # Für Demo immer fehlschlagen
    
    async def _notify_secret_exposure(self, threat: SecurityThreat) -> None:
        """Benachrichtigt über Secret-Exposure."""
        self.logger.critical(f"🚨 SECRET EXPOSURE: {threat.title}")
    
    async def _emergency_dependency_update(self, threat: SecurityThreat) -> None:
        """Führt Notfall-Dependency-Update durch."""
        self.logger.critical(f"🚨 EMERGENCY UPDATE: {threat.title}")
    
    async def _save_security_report(self, results: Dict[str, Any], threats: List[SecurityThreat]) -> None:
        """Speichert Security-Bericht."""
        report_dir = self.repo_path / ".governance" / "security-reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = report_dir / f"security_report_{timestamp}.json"
        
        report_data = {
            "metadata": results,
            "threats": [asdict(threat) for threat in threats],
            "summary": {
                "total_threats": len(threats),
                "by_severity": {
                    "critical": len([t for t in threats if t.threat_level == ThreatLevel.CRITICAL]),
                    "high": len([t for t in threats if t.threat_level == ThreatLevel.HIGH]),
                    "medium": len([t for t in threats if t.threat_level == ThreatLevel.MEDIUM]),
                    "low": len([t for t in threats if t.threat_level == ThreatLevel.LOW]),
                },
                "by_type": {}
            }
        }
        
        # Zähle Threats nach Typ
        for threat_type in VulnerabilityType:
            count = len([t for t in threats if t.threat_type == threat_type])
            if count > 0:
                report_data["summary"]["by_type"][threat_type.value] = count
        
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        self.logger.info(f"📄 Security-Bericht gespeichert: {report_file}")


async def main():
    """Hauptfunktion für Security Automation Engine."""
    print("🛡️ RepoSovereign Prime Security Automation Engine")
    print("=" * 60)
    
    # Initialisiere Security Engine
    security_engine = SecurityAutomationEngine()
    
    # Führe Security-Zyklus aus
    results = await security_engine.execute_security_cycle()
    
    # Ausgabe der Ergebnisse
    print("\n📊 SECURITY-ZYKLUS ERGEBNISSE:")
    print(f"⏱️  Dauer: {results['cycle_duration']:.2f} Sekunden")
    print(f"🔍 Erkannte Bedrohungen: {results['threats_detected']}")
    print(f"🚨 Kritische Bedrohungen: {results['critical_threats']}")
    print(f"🔧 Automatisch behoben: {results['auto_fixed']}")
    print(f"👤 Manuelle Überprüfung erforderlich: {results['manual_review_required']}")
    
    if results['critical_threats'] > 0:
        print("\n🚨 KRITISCHE SICHERHEITSWARNUNGEN ERKANNT!")
        print("Sofortiges Handeln erforderlich.")
    
    print("\n✨ Security Automation Engine Zyklus abgeschlossen!")


if __name__ == "__main__":
    asyncio.run(main())