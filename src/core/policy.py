"""
Policy evaluation module for Prompt Ops Hub.
Evaluates code changes against defined policies using Rego rules.
"""

import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Any, Optional


@dataclass
class PolicyResult:
    """Result of policy evaluation."""
    allowed: bool
    violations: List[str]
    violation_count: int
    details: Dict[str, Any]
    error: Optional[str] = None


class PolicyEngine:
    """Policy engine for evaluating code changes."""
    
    def __init__(self, policy_file: str = "policy/rules.rego"):
        """Initialize policy engine.
        
        Args:
            policy_file: Path to Rego policy file
        """
        self.policy_file = Path(policy_file)
        
    def evaluate_policy(self, input_data: Dict[str, Any]) -> PolicyResult:
        """Evaluate policy against input data.
        
        Args:
            input_data: Data to evaluate (diff_loc, acceptance_criteria, etc.)
            
        Returns:
            PolicyResult with evaluation outcome
        """
        try:
            # Check if opa is available
            if not self._check_opa_available():
                return PolicyResult(
                    allowed=False,
                    violations=["opa_not_available"],
                    violation_count=1,
                    details={},
                    error="OPA (Open Policy Agent) not found. Install with: brew install opa"
                )
            
            # Check if policy file exists
            if not self.policy_file.exists():
                return PolicyResult(
                    allowed=False,
                    violations=["policy_file_not_found"],
                    violation_count=1,
                    details={},
                    error=f"Policy file not found: {self.policy_file}"
                )
            
            # Run OPA evaluation
            result = self._run_opa_eval(input_data)
            
            if result.get("error"):
                return PolicyResult(
                    allowed=False,
                    violations=["opa_evaluation_error"],
                    violation_count=1,
                    details=result,
                    error=result.get("error")
                )
            
            # Parse OPA output
            summary = result.get("summary", {})
            
            return PolicyResult(
                allowed=summary.get("allowed", False),
                violations=summary.get("violations", []),
                violation_count=summary.get("violation_count", 0),
                details=result
            )
            
        except Exception as e:
            return PolicyResult(
                allowed=False,
                violations=["evaluation_error"],
                violation_count=1,
                details={},
                error=f"Policy evaluation failed: {str(e)}"
            )
    
    def _check_opa_available(self) -> bool:
        """Check if OPA is available in PATH.
        
        Returns:
            True if OPA is available
        """
        try:
            result = subprocess.run(
                ["opa", "version"],
                capture_output=True,
                text=True,
                check=False
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def _run_opa_eval(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run OPA evaluation with input data.
        
        Args:
            input_data: Data to evaluate
            
        Returns:
            Dictionary with OPA evaluation results
        """
        try:
            # Prepare input as JSON
            input_json = json.dumps(input_data)
            
            # Run OPA eval
            cmd = [
                "opa", "eval",
                "--data", str(self.policy_file),
                "--input", "-",
                "data.promptops.policy.summary"
            ]
            
            result = subprocess.run(
                cmd,
                input=input_json,
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode != 0:
                return {
                    "error": f"OPA evaluation failed: {result.stderr}"
                }
            
            # Parse OPA output
            try:
                opa_output = json.loads(result.stdout)
                # Extract the actual result from OPA's output format
                if "result" in opa_output and opa_output["result"]:
                    return opa_output["result"][0]
                else:
                    return {
                        "error": "No result from OPA evaluation"
                    }
            except json.JSONDecodeError:
                return {
                    "error": f"Invalid JSON from OPA: {result.stdout}"
                }
                
        except Exception as e:
            return {
                "error": f"OPA execution failed: {str(e)}"
            }
    
    def evaluate_run(self, run_id: int, db_manager) -> PolicyResult:
        """Evaluate policy for a specific run.
        
        Args:
            run_id: Run ID to evaluate
            db_manager: Database manager instance
            
        Returns:
            PolicyResult for the run
        """
        try:
            # Get run data
            run = db_manager.get_run(run_id)
            if not run:
                return PolicyResult(
                    allowed=False,
                    violations=["run_not_found"],
                    violation_count=1,
                    details={},
                    error=f"Run {run_id} not found"
                )
            
            # Get task data
            task = db_manager.get_task(run.task_id)
            if not task:
                return PolicyResult(
                    allowed=False,
                    violations=["task_not_found"],
                    violation_count=1,
                    details={},
                    error=f"Task {run.task_id} not found"
                )
            
            # Build input data for policy evaluation
            input_data = {
                "run_id": run_id,
                "task_id": run.task_id,
                "diff_loc": self._estimate_diff_size(run.logs),
                "acceptance_criteria": self._extract_acceptance_criteria(task.built_prompt),
                "new_dependencies": [],  # Would need to parse requirements.txt changes
                "dependency_justification": [],  # Would need to parse commit messages
                "security_findings": [],  # Would come from semgrep
                "performance_findings": [],  # Would come from semgrep
                "test_files": self._extract_test_files(run.logs),
                "large_files": [],  # Would need to analyze file sizes
                "secret_findings": [],  # Would come from semgrep
                "coverage_threshold": 80,  # Default threshold
                "baseline_threshold": 80,  # Baseline threshold
                "test_changes": [],  # Would need to analyze diff
                "deleted_test_files": [],  # Would need to analyze diff
                "integrity_violations": []  # Would come from integrity checks
            }
            
            return self.evaluate_policy(input_data)
            
        except Exception as e:
            return PolicyResult(
                allowed=False,
                violations=["evaluation_error"],
                violation_count=1,
                details={},
                error=f"Run evaluation failed: {str(e)}"
            )
    
    def _estimate_diff_size(self, logs: str) -> int:
        """Estimate diff size from run logs.
        
        Args:
            logs: Run logs containing diff information
            
        Returns:
            Estimated diff size in lines
        """
        # Simple estimation - count lines that look like diff additions
        if not logs:
            return 0
        
        lines = logs.split('\n')
        diff_lines = [line for line in lines if line.startswith('+') and not line.startswith('+++')]
        return len(diff_lines)
    
    def _extract_acceptance_criteria(self, prompt: str) -> List[str]:
        """Extract acceptance criteria from prompt.
        
        Args:
            prompt: Task prompt
            
        Returns:
            List of acceptance criteria
        """
        if not prompt:
            return []
        
        # Simple extraction - look for lines starting with common AC patterns
        lines = prompt.split('\n')
        ac_lines = []
        
        for line in lines:
            line = line.strip()
            if any(line.startswith(prefix) for prefix in ['- ', '• ', '* ', '✓ ', '✅ ']):
                ac_lines.append(line)
        
        return ac_lines
    
    def _extract_test_files(self, logs: str) -> List[str]:
        """Extract test files from run logs.
        
        Args:
            logs: Run logs
            
        Returns:
            List of test file paths
        """
        if not logs:
            return []
        
        # Simple extraction - look for test file patterns
        lines = logs.split('\n')
        test_files = []
        
        for line in lines:
            if 'test_' in line and (line.endswith('.py') or '/test' in line):
                test_files.append(line.strip())
        
        return test_files


# Global policy engine instance
policy_engine = PolicyEngine() 