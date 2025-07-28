#!/usr/bin/env python3
"""
Dependency scanning script for Prompt Ops Hub.
Uses pip-audit to check for CVEs in Python dependencies.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Any


def run_pip_audit() -> Dict[str, Any]:
    """Run pip-audit to check for CVEs.
    
    Returns:
        Dictionary with pip-audit results
    """
    try:
        # Run pip-audit with JSON output
        cmd = [
            "pip-audit",
            "--format", "json",
            "--output", "-"
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            # No vulnerabilities found
            return {
                "success": True,
                "vulnerabilities": [],
                "summary": {
                    "total_vulnerabilities": 0,
                    "critical": 0,
                    "high": 0,
                    "medium": 0,
                    "low": 0
                }
            }
        
        # Parse JSON output
        try:
            audit_output = json.loads(result.stdout)
        except json.JSONDecodeError:
            # If stdout is not valid JSON, pip-audit might have failed
            return {
                "success": False,
                "error": f"pip-audit failed: {result.stderr}",
                "vulnerabilities": [],
                "summary": {
                    "total_vulnerabilities": 0,
                    "critical": 0,
                    "high": 0,
                    "medium": 0,
                    "low": 0
                }
            }
        
        # Extract vulnerabilities
        vulnerabilities = audit_output.get("vulnerabilities", [])
        
        # Count by severity
        critical_count = sum(1 for v in vulnerabilities if v.get("severity") == "CRITICAL")
        high_count = sum(1 for v in vulnerabilities if v.get("severity") == "HIGH")
        medium_count = sum(1 for v in vulnerabilities if v.get("severity") == "MEDIUM")
        low_count = sum(1 for v in vulnerabilities if v.get("severity") == "LOW")
        
        return {
            "success": True,
            "vulnerabilities": vulnerabilities,
            "summary": {
                "total_vulnerabilities": len(vulnerabilities),
                "critical": critical_count,
                "high": high_count,
                "medium": medium_count,
                "low": low_count
            }
        }
        
    except FileNotFoundError:
        return {
            "success": False,
            "error": "pip-audit not found. Please install: pip install pip-audit",
            "vulnerabilities": [],
            "summary": {
                "total_vulnerabilities": 0,
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "vulnerabilities": [],
            "summary": {
                "total_vulnerabilities": 0,
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0
            }
        }


def format_vulnerabilities(vulnerabilities: List[Dict[str, Any]]) -> str:
    """Format vulnerabilities for human-readable output.
    
    Args:
        vulnerabilities: List of vulnerability findings
        
    Returns:
        Formatted string
    """
    if not vulnerabilities:
        return "✅ No vulnerabilities detected"
    
    output = []
    for vuln in vulnerabilities:
        package = vuln.get("package", {}).get("name", "unknown")
        version = vuln.get("package", {}).get("version", "unknown")
        severity = vuln.get("severity", "UNKNOWN")
        description = vuln.get("description", "No description")
        
        output.append(f"  {severity}: {package}@{version} - {description}")
    
    return "\n".join(output)


def parse_pip_audit_output(output: str) -> Dict[str, Any]:
    """Parse pip-audit output for testing purposes.
    
    Args:
        output: Raw pip-audit output
        
    Returns:
        Parsed vulnerability data
    """
    try:
        data = json.loads(output)
        vulnerabilities = data.get("vulnerabilities", [])
        
        # Count by severity
        critical_count = sum(1 for v in vulnerabilities if v.get("severity") == "CRITICAL")
        high_count = sum(1 for v in vulnerabilities if v.get("severity") == "HIGH")
        medium_count = sum(1 for v in vulnerabilities if v.get("severity") == "MEDIUM")
        low_count = sum(1 for v in vulnerabilities if v.get("severity") == "LOW")
        
        return {
            "success": True,
            "vulnerabilities": vulnerabilities,
            "summary": {
                "total_vulnerabilities": len(vulnerabilities),
                "critical": critical_count,
                "high": high_count,
                "medium": medium_count,
                "low": low_count
            }
        }
    except json.JSONDecodeError:
        return {
            "success": False,
            "error": "Invalid JSON output",
            "vulnerabilities": [],
            "summary": {
                "total_vulnerabilities": 0,
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0
            }
        }


def main() -> int:
    """Main function to run dependency scan and output results.
    
    Returns:
        Exit code (0 for success, 1 for critical/high vulnerabilities, 2 for errors)
    """
    print("🔍 Running dependency vulnerability scan...")
    
    # Run pip-audit
    result = run_pip_audit()
    
    if not result["success"]:
        print(f"❌ Dependency scan failed: {result.get('error', 'Unknown error')}")
        return 2
    
    # Print summary
    summary = result["summary"]
    print(f"📊 Vulnerability Summary:")
    print(f"  Total vulnerabilities: {summary['total_vulnerabilities']}")
    print(f"  Critical: {summary['critical']}")
    print(f"  High: {summary['high']}")
    print(f"  Medium: {summary['medium']}")
    print(f"  Low: {summary['low']}")
    
    # Print vulnerabilities
    if result["vulnerabilities"]:
        print(f"\n🔍 Vulnerabilities:")
        print(format_vulnerabilities(result["vulnerabilities"]))
    
    # Output JSON for CI consumption
    print(f"\n📋 JSON Output:")
    print(json.dumps(result, indent=2))
    
    # Exit with appropriate code
    if summary["critical"] > 0 or summary["high"] > 0:
        print(f"\n❌ Found {summary['critical']} critical and {summary['high']} high severity vulnerabilities. Failing.")
        return 1
    elif summary["total_vulnerabilities"] > 0:
        print(f"\n⚠️  Found {summary['total_vulnerabilities']} vulnerabilities (none critical/high).")
        return 0
    else:
        print(f"\n✅ No vulnerabilities found.")
        return 0


if __name__ == "__main__":
    sys.exit(main()) 