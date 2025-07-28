"""Tests for utility scripts to improve coverage."""

import pytest
from unittest.mock import patch, MagicMock
import json


class TestDepScanScript:
    """Test dependency scan script functionality."""

    def test_run_pip_audit_no_vulnerabilities(self):
        """Test pip-audit with no vulnerabilities."""
        from scripts.dep_scan import run_pip_audit
        
        with patch('scripts.dep_scan.subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = '{"vulnerabilities": []}'
            
            result = run_pip_audit()
            
            assert result["success"] is True
            assert result["summary"]["total_vulnerabilities"] == 0
            assert result["summary"]["critical"] == 0

    def test_run_pip_audit_with_critical_vulnerability(self):
        """Test pip-audit with critical vulnerability."""
        from scripts.dep_scan import run_pip_audit
        
        with patch('scripts.dep_scan.subprocess.run') as mock_run:
            mock_run.return_value.returncode = 1
            mock_run.return_value.stdout = json.dumps({
                "vulnerabilities": [
                    {
                        "severity": "CRITICAL",
                        "package": {"name": "requests", "version": "2.25.1"},
                        "description": "Critical CVE-2021-33503"
                    }
                ]
            })
            
            result = run_pip_audit()
            
            assert result["success"] is True
            assert result["summary"]["total_vulnerabilities"] == 1
            assert result["summary"]["critical"] == 1

    def test_parse_pip_audit_output(self):
        """Test parsing pip-audit output."""
        from scripts.dep_scan import parse_pip_audit_output
        
        output = json.dumps({
            "vulnerabilities": [
                {
                    "severity": "HIGH",
                    "package": {"name": "urllib3", "version": "1.26.5"},
                    "description": "High severity CVE"
                }
            ]
        })
        
        result = parse_pip_audit_output(output)
        
        assert result["success"] is True
        assert result["summary"]["high"] == 1


class TestSemgrepScript:
    """Test semgrep script functionality."""

    def test_run_semgrep_no_findings(self):
        """Test semgrep with no findings."""
        from scripts.run_semgrep import run_semgrep
        
        with patch('scripts.run_semgrep.subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = '{"results": []}'
            
            result = run_semgrep()
            
            assert result["success"] is True
            assert result["summary"]["total_findings"] == 0
            assert result["summary"]["high_severity"] == 0

    def test_run_semgrep_with_high_finding(self):
        """Test semgrep with high severity finding."""
        from scripts.run_semgrep import run_semgrep
        
        with patch('scripts.run_semgrep.subprocess.run') as mock_run:
            mock_run.return_value.returncode = 1
            mock_run.return_value.stdout = json.dumps({
                "results": [
                    {
                        "extra": {
                            "severity": "HIGH",
                            "message": "Dangerous eval() usage",
                            "metadata": {"category": "security"}
                        },
                        "path": "src/test.py",
                        "start": {"line": 42}
                    }
                ]
            })
            
            result = run_semgrep()
            
            assert result["success"] is True
            assert result["summary"]["total_findings"] == 1
            assert result["summary"]["high_severity"] == 1

    def test_format_findings(self):
        """Test formatting findings."""
        from scripts.run_semgrep import format_findings
        
        findings = [
            {
                "extra": {
                    "severity": "HIGH",
                    "message": "Security issue"
                },
                "path": "src/test.py",
                "start": {"line": 10}
            }
        ]
        
        formatted = format_findings(findings)
        
        assert "HIGH: src/test.py:10" in formatted
        assert "Security issue" in formatted 