#!/usr/bin/env python3
"""
CI Self-Verification Script

This script runs all integrity checks and provides a comprehensive summary.
It hard-fails on any drift or shortcut attempts.
"""

import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Tuple, List, Dict
import os


class CISelfCheck:
    """CI Self-Verification orchestrator."""
    
    def __init__(self):
        self.repo_root = Path.cwd()
        self.results: List[Dict] = []
        
    def run_check(self, name: str, check_func) -> Tuple[bool, str]:
        """Run a check and return (success, details)."""
        try:
            success, details = check_func()
            self.results.append({
                'name': name,
                'success': success,
                'details': details
            })
            return success, details
        except Exception as e:
            error_msg = f"Check '{name}' failed with exception: {e}"
            self.results.append({
                'name': name,
                'success': False,
                'details': error_msg
            })
            return False, error_msg
    
    def check_pytest(self) -> Tuple[bool, str]:
        """Run pytest with coverage."""
        try:
            result = subprocess.run([
                'python', '-m', 'pytest', 
                '--cov=src', 
                '--cov-report=xml', 
                '--cov-report=term-missing',
                '-q'
            ], capture_output=True, text=True, cwd=self.repo_root)
            
            if result.returncode != 0:
                return False, f"pytest failed with exit code {result.returncode}\n{result.stdout}\n{result.stderr}"
            
            # Check for skipped/xfail tests
            if "skipped" in result.stdout or "xfail" in result.stdout:
                return False, "Found skipped or xfail tests - all tests must pass or fail"
            
            return True, "All tests passed"
            
        except Exception as e:
            return False, f"pytest execution failed: {e}"
    
    def check_coverage_threshold(self) -> Tuple[bool, str]:
        """Check coverage meets 80% threshold."""
        try:
            coverage_file = self.repo_root / "coverage.xml"
            if not coverage_file.exists():
                return False, "coverage.xml not found - run pytest with --cov-report=xml first"
            
            tree = ET.parse(coverage_file)
            root = tree.getroot()
            line_rate = float(root.attrib.get('line-rate', 0))
            coverage_percent = line_rate * 100
            
            if coverage_percent < 80:
                return False, f"Coverage {coverage_percent:.1f}% < 80% threshold"
            
            return True, f"Coverage {coverage_percent:.1f}% >= 80% threshold"
            
        except Exception as e:
            return False, f"Coverage check failed: {e}"
    
    def check_diff_coverage(self) -> Tuple[bool, str]:
        """Check diff coverage is 100%."""
        try:
            result = subprocess.run([
                'python', 'scripts/diff_coverage_check.py'
            ], capture_output=True, text=True, cwd=self.repo_root)
            
            if result.returncode != 0:
                return False, f"Diff coverage check failed:\n{result.stdout}\n{result.stderr}"
            
            return True, "Diff coverage = 100%"
            
        except Exception as e:
            return False, f"Diff coverage check failed: {e}"
    
    def check_thresholds(self) -> Tuple[bool, str]:
        """Check coverage thresholds."""
        try:
            result = subprocess.run([
                'python', 'scripts/check_thresholds.py'
            ], capture_output=True, text=True, cwd=self.repo_root)
            
            if result.returncode != 0:
                return False, f"Threshold check failed:\n{result.stdout}\n{result.stderr}"
            
            return True, "Coverage thresholds maintained"
            
        except Exception as e:
            return False, f"Threshold check failed: {e}"
    
    def check_test_tamper(self) -> Tuple[bool, str]:
        """Check for test tampering."""
        try:
            result = subprocess.run([
                'python', 'scripts/test_tamper_check.py'
            ], capture_output=True, text=True, cwd=self.repo_root)
            
            if result.returncode != 0:
                return False, f"Test tamper check failed:\n{result.stdout}\n{result.stderr}"
            
            return True, "No test tampering detected"
            
        except Exception as e:
            return False, f"Test tamper check failed: {e}"
    
    def check_trivial_tests(self) -> Tuple[bool, str]:
        """Check for trivial tests."""
        try:
            result = subprocess.run([
                'python', 'scripts/trivial_test_check.py'
            ], capture_output=True, text=True, cwd=self.repo_root)
            
            if result.returncode != 0:
                return False, f"Trivial test check failed:\n{result.stdout}\n{result.stderr}"
            
            return True, "No trivial tests detected"
            
        except Exception as e:
            return False, f"Trivial test check failed: {e}"
    
    def check_ci_snippet(self) -> Tuple[bool, str]:
        """Check CI workflow drift."""
        try:
            result = subprocess.run([
                'python', '-m', 'src.cli', 'ci-snippet', '--check'
            ], capture_output=True, text=True, cwd=self.repo_root)
            
            if result.returncode != 0:
                return False, f"CI snippet check failed:\n{result.stdout}\n{result.stderr}"
            
            return True, "CI workflow matches canonical version"
            
        except Exception as e:
            return False, f"CI snippet check failed: {e}"
    
    def check_policy(self) -> Tuple[bool, str]:
        """Check policy engine (OPA or fallback)."""
        try:
            sys.path.insert(0, str(self.repo_root))
            from src.core.policy import policy_engine
            from src.core.guardrails import guardrails
            # Try OPA
            opa_available = False
            try:
                opa_available = policy_engine._check_opa_available()
            except Exception:
                opa_available = False
            # Gather context
            coverage = self._get_coverage_percent()
            diff_coverage = self._get_diff_coverage_percent()
            test_deletions = False  # TODO: wire up real check
            threshold_lowered = False  # TODO: wire up real check
            from integrity_core.observer import Observer
            observer = Observer()
            integrity_score = observer.calculate_integrity_score()
            context = {
                'coverage': coverage,
                'diff_coverage': diff_coverage,
                'test_deletions': test_deletions,
                'threshold_lowered': threshold_lowered,
                'integrity_score': integrity_score,
            }
            if opa_available:
                result = policy_engine.evaluate_policy(context)
                engine_used = 'opa'
            else:
                from src.core.policy_fallback import evaluate_policy_fallback
                result = evaluate_policy_fallback(context)
                engine_used = 'fallback'
            violations = getattr(result, 'violations', [])
            allowed = getattr(result, 'allowed', False)
            if not allowed or violations:
                return False, f"Policy check failed (engine={engine_used}): allowed={allowed}, violations={violations}"
            return True, f"Policy check passed (engine={engine_used})"
        except Exception as e:
            return False, f"Policy check failed: {e}"

    def _get_coverage_percent(self) -> float:
        coverage_file = self.repo_root / "coverage.xml"
        if not coverage_file.exists():
            return 0.0
        import xml.etree.ElementTree as ET
        tree = ET.parse(coverage_file)
        root = tree.getroot()
        line_rate = float(root.attrib.get('line-rate', 0))
        return line_rate * 100

    def _get_diff_coverage_percent(self) -> float:
        # TODO: Implement real diff coverage percent extraction
        # For now, assume 100% if diff_coverage_check.py passes
        result = subprocess.run([
            'python', 'scripts/diff_coverage_check.py'
        ], capture_output=True, text=True, cwd=self.repo_root)
        if result.returncode == 0:
            return 100.0
        return 0.0
    
    def check_observer(self) -> Tuple[bool, str]:
        """Check observer integrity score."""
        try:
            # Import observer module
            sys.path.insert(0, str(self.repo_root))
            from integrity_core.observer import Observer
            
            observer = Observer()
            score = observer.calculate_integrity_score()
            
            if score < 70:
                return False, f"Observer integrity score {score} < 70 threshold"
            
            return True, f"Observer integrity score {score} >= 70"
            
        except Exception as e:
            return False, f"Observer check failed: {e}"
    
    def print_summary(self):
        """Print a formatted summary of all checks."""
        print("\n" + "="*80)
        print("CI SELF-VERIFICATION SUMMARY")
        print("="*80)
        
        all_passed = True
        for result in self.results:
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"{status} {result['name']}")
            if not result['success']:
                print(f"    Details: {result['details']}")
                all_passed = False
        
        print("="*80)
        if all_passed:
            print("🎉 ALL CHECKS PASSED - CI SELF-VERIFICATION SUCCESSFUL")
        else:
            print("💥 CI SELF-VERIFICATION FAILED - FIX ISSUES ABOVE")
        print("="*80)
        
        return all_passed
    
    def run_all_checks(self) -> bool:
        """Run all integrity checks."""
        print("🔍 Running CI self-verification...")
        
        checks = [
            ("pytest", self.check_pytest),
            ("coverage_threshold", self.check_coverage_threshold),
            ("diff_coverage", self.check_diff_coverage),
            ("thresholds", self.check_thresholds),
            ("test_tamper", self.check_test_tamper),
            ("trivial_tests", self.check_trivial_tests),
            ("ci_snippet", self.check_ci_snippet),
            ("policy", self.check_policy),
            ("observer", self.check_observer),
        ]
        
        for name, check_func in checks:
            print(f"  Running {name}...")
            self.run_check(name, check_func)
        
        return self.print_summary()


def main():
    """Main entry point."""
    checker = CISelfCheck()
    success = checker.run_all_checks()
    
    if not success:
        sys.exit(1)
    
    print("✅ CI self-verification completed successfully")


if __name__ == "__main__":
    main() 