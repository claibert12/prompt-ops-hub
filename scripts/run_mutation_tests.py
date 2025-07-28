#!/usr/bin/env python3
"""
Script to run mutation tests on critical modules.
Runs mutmut on spec_expander, patch_builder, regen, and guardrails.
"""

import subprocess
import sys
from pathlib import Path


def check_mutmut_installed() -> bool:
    """Check if mutmut is installed.
    
    Returns:
        True if mutmut is available
    """
    try:
        result = subprocess.run(
            ["mutmut", "--version"],
            capture_output=True,
            text=True,
            check=False
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def run_mutation_tests() -> int:
    """Run mutation tests on critical modules.
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    print("🧬 Running mutation tests on critical modules...")
    
    # Check if mutmut is installed
    if not check_mutmut_installed():
        print("❌ mutmut not installed. Install with: pip install mutmut")
        print("💡 TODO: Add mutmut to dev dependencies")
        return 1
    
    # Check if config exists
    config_path = Path("tools/mutation/mutmut.ini")
    if not config_path.exists():
        print("❌ Mutation config not found: tools/mutation/mutmut.ini")
        return 1
    
    try:
        # Run mutation tests
        print("Running mutmut with config: tools/mutation/mutmut.ini")
        
        result = subprocess.run(
            [
                "mutmut", 
                "run", 
                "--paths-to-mutate=src/core/spec_expander.py,src/core/patch_builder.py,src/core/regen.py,src/core/guardrails.py",
                "--test-command=python -m pytest tests/",
                "--backup-dir=.mutmut-cache",
                "--verbose"
            ],
            capture_output=False,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            print("\n✅ Mutation tests completed successfully")
            
            # Show results summary
            try:
                summary_result = subprocess.run(
                    ["mutmut", "results"],
                    capture_output=True,
                    text=True,
                    check=False
                )
                if summary_result.returncode == 0:
                    print("\n📊 Mutation test results:")
                    print(summary_result.stdout)
            except Exception:
                pass
            
            return 0
        else:
            print(f"\n❌ Mutation tests failed with exit code: {result.returncode}")
            return 1
    
    except Exception as e:
        print(f"❌ Error running mutation tests: {e}")
        return 1


def main() -> int:
    """Main function to run mutation tests.
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    print("🧬 Prompt Ops Hub - Mutation Testing")
    print("=" * 50)
    
    # Run mutation tests
    exit_code = run_mutation_tests()
    
    if exit_code == 0:
        print("\n💡 Note: Mutation tests are not yet enforced in CI")
        print("   TODO: Add to CI pipeline with appropriate thresholds")
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main()) 