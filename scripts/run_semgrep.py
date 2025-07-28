#!/usr/bin/env python3
"""
Semgrep runner script for Prompt Ops Hub.
Runs semgrep rules and outputs JSON summary with proper exit codes.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Any


def run_semgrep(target_path: str = "src/", rules_path: str = "semgrep/rules/") -> Dict[str, Any]:
    """Run semgrep on the target path with specified rules.
    
    Args:
        target_path: Path to scan (default: src/)
        rules_path: Path to semgrep rules (default: semgrep/rules/)
        
    Returns:
        Dictionary with semgrep results
    """
    try:
        # Run semgrep with JSON output
        cmd = [
            "semgrep",
            "--json",
            "--config", rules_path,
            target_path
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False  # Don't raise exception on non-zero exit
        )
        
        if result.returncode == 0:
            # No findings
            return {
                "success": True,
                "findings": [],
                "summary": {
                    "total_findings": 0,
                    "high_severity": 0,
                    "medium_severity": 0,
                    "low_severity": 0
                }
            }
        
        # Parse JSON output
        try:
            semgrep_output = json.loads(result.stdout)
        except json.JSONDecodeError:
            # If stdout is not valid JSON, semgrep might have failed
            return {
                "success": False,
                "error": f"Semgrep failed: {result.stderr}",
                "findings": [],
                "summary": {
                    "total_findings": 0,
                    "high_severity": 0,
                    "medium_severity": 0,
                    "low_severity": 0
                }
            }
        
        # Extract findings
        findings = semgrep_output.get("results", [])
        
        # Count by severity
        high_count = sum(1 for f in findings if f.get("extra", {}).get("severity") == "HIGH")
        medium_count = sum(1 for f in findings if f.get("extra", {}).get("severity") == "MEDIUM")
        low_count = sum(1 for f in findings if f.get("extra", {}).get("severity") == "LOW")
        
        return {
            "success": True,
            "findings": findings,
            "summary": {
                "total_findings": len(findings),
                "high_severity": high_count,
                "medium_severity": medium_count,
                "low_severity": low_count
            }
        }
        
    except FileNotFoundError:
        return {
            "success": False,
            "error": "Semgrep not found. Please install semgrep: pip install semgrep",
            "findings": [],
            "summary": {
                "total_findings": 0,
                "high_severity": 0,
                "medium_severity": 0,
                "low_severity": 0
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "findings": [],
            "summary": {
                "total_findings": 0,
                "high_severity": 0,
                "medium_severity": 0,
                "low_severity": 0
            }
        }


def format_findings(findings: List[Dict[str, Any]]) -> str:
    """Format findings for human-readable output.
    
    Args:
        findings: List of semgrep findings
        
    Returns:
        Formatted string
    """
    if not findings:
        return "✅ No findings detected"
    
    output = []
    for finding in findings:
        extra = finding.get("extra", {})
        path = finding.get("path", "unknown")
        line = finding.get("start", {}).get("line", "?")
        message = extra.get("message", "No message")
        severity = extra.get("severity", "UNKNOWN")
        
        output.append(f"  {severity}: {path}:{line} - {message}")
    
    return "\n".join(output)


def main() -> int:
    """Main function to run semgrep and output results.
    
    Returns:
        Exit code (0 for success, 1 for HIGH severity findings, 2 for errors)
    """
    print("🔍 Running Semgrep static analysis...")
    
    # Run semgrep
    result = run_semgrep()
    
    if not result["success"]:
        print(f"❌ Semgrep failed: {result.get('error', 'Unknown error')}")
        return 2
    
    # Print summary
    summary = result["summary"]
    print(f"📊 Semgrep Summary:")
    print(f"  Total findings: {summary['total_findings']}")
    print(f"  High severity: {summary['high_severity']}")
    print(f"  Medium severity: {summary['medium_severity']}")
    print(f"  Low severity: {summary['low_severity']}")
    
    # Print findings
    if result["findings"]:
        print(f"\n🔍 Findings:")
        print(format_findings(result["findings"]))
    
    # Output JSON for CI consumption
    print(f"\n📋 JSON Output:")
    print(json.dumps(result, indent=2))
    
    # Exit with appropriate code
    if summary["high_severity"] > 0:
        print(f"\n❌ Found {summary['high_severity']} HIGH severity issues. Failing.")
        return 1
    elif summary["total_findings"] > 0:
        print(f"\n⚠️  Found {summary['total_findings']} issues (none HIGH severity).")
        return 0
    else:
        print(f"\n✅ No issues found.")
        return 0


if __name__ == "__main__":
    sys.exit(main()) 