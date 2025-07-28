"""Tests for policy evaluation functionality."""

import json
import pytest
from unittest.mock import patch, MagicMock
from src.core.policy import PolicyEngine, PolicyResult


class TestPolicyEngine:
    """Test policy engine functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.engine = PolicyEngine("policy/rules.rego")

    def test_evaluate_policy_allowed(self):
        """Test policy evaluation that should be allowed."""
        input_data = {
            "diff_loc": 100,
            "acceptance_criteria": ["Test passes", "Code is clean"],
            "new_dependencies": [],
            "dependency_justification": [],
            "security_findings": [],
            "performance_findings": [],
            "test_files": ["test_file.py"],
            "large_files": [],
            "secret_findings": []
        }

        with patch.object(self.engine, '_check_opa_available', return_value=True):
            with patch('pathlib.Path.exists', return_value=True):
                with patch.object(self.engine, '_run_opa_eval') as mock_opa:
                    mock_opa.return_value = {
                        "summary": {
                            "allowed": True,
                            "violations": [],
                            "violation_count": 0
                        }
                    }
                    result = self.engine.evaluate_policy(input_data)

                    assert result.allowed is True
                    assert result.violations == []
                    assert result.violation_count == 0
                    assert result.error is None

    def test_evaluate_policy_denied(self):
        """Test policy evaluation that should be denied."""
        input_data = {
            "diff_loc": 400,  # Too large
            "acceptance_criteria": [],
            "new_dependencies": [],
            "dependency_justification": [],
            "security_findings": [],
            "performance_findings": [],
            "test_files": [],
            "large_files": [],
            "secret_findings": []
        }

        with patch.object(self.engine, '_check_opa_available', return_value=True):
            with patch('pathlib.Path.exists', return_value=True):
                with patch.object(self.engine, '_run_opa_eval') as mock_opa:
                    mock_opa.return_value = {
                        "summary": {
                            "allowed": False,
                            "violations": [{"id": "DIFF_TOO_LARGE", "severity": "error"}],
                            "violation_count": 1
                        }
                    }

                    result = self.engine.evaluate_policy(input_data)

                    assert result.allowed is False
                    assert any(v["id"] == "DIFF_TOO_LARGE" for v in result.violations)
                    assert result.violation_count == 1
                    assert result.error is None

    def test_evaluate_policy_opa_not_available(self):
        """Test policy evaluation when OPA is not available."""
        with patch.object(self.engine, '_check_opa_available', return_value=False):
            result = self.engine.evaluate_policy({})

            assert result.allowed is False
            assert "opa_not_available" in result.violations
            assert result.error is not None
            assert "OPA" in result.error

    def test_evaluate_policy_file_not_found(self):
        """Test policy evaluation when policy file is not found."""
        with patch.object(self.engine, '_check_opa_available', return_value=True):
            with patch('pathlib.Path.exists', return_value=False):
                result = self.engine.evaluate_policy({})

                assert result.allowed is False
                assert "policy_file_not_found" in result.violations
                assert result.error is not None
                assert "Policy file not found" in result.error

    def test_evaluate_policy_opa_error(self):
        """Test policy evaluation when OPA returns an error."""
        with patch.object(self.engine, '_check_opa_available', return_value=True):
            with patch('pathlib.Path.exists', return_value=True):
                with patch.object(self.engine, '_run_opa_eval') as mock_opa:
                    mock_opa.return_value = {"error": "OPA evaluation failed"}

                    result = self.engine.evaluate_policy({})

                    assert result.allowed is False
                    assert "opa_evaluation_error" in result.violations
                    assert result.error is not None

    def test_evaluate_run_success(self):
        """Test evaluating policy for a specific run."""
        mock_db = MagicMock()
        mock_run = MagicMock()
        mock_run.task_id = 1
        mock_run.logs = "+ def test_function():\n+     pass"
        mock_task = MagicMock()
        mock_task.built_prompt = "- Test passes\n- Code is clean"

        mock_db.get_run.return_value = mock_run
        mock_db.get_task.return_value = mock_task

        with patch.object(self.engine, 'evaluate_policy') as mock_eval:
            mock_eval.return_value = PolicyResult(
                allowed=True,
                violations=[],
                violation_count=0,
                details={}
            )

            result = self.engine.evaluate_run(1, mock_db)

            assert result.allowed is True
            assert result.violations == []
            assert result.violation_count == 0

    def test_evaluate_run_not_found(self):
        """Test evaluating policy for a non-existent run."""
        mock_db = MagicMock()
        mock_db.get_run.return_value = None

        result = self.engine.evaluate_run(999, mock_db)

        assert result.allowed is False
        assert "run_not_found" in result.violations
        assert result.error is not None

    def test_evaluate_run_task_not_found(self):
        """Test evaluating policy when task is not found."""
        mock_db = MagicMock()
        mock_run = MagicMock()
        mock_run.task_id = 1
        mock_db.get_run.return_value = mock_run
        mock_db.get_task.return_value = None

        result = self.engine.evaluate_run(1, mock_db)

        assert result.allowed is False
        assert "task_not_found" in result.violations
        assert result.error is not None

    def test_estimate_diff_size(self):
        """Test diff size estimation."""
        logs = "+ def new_function():\n+     return True\n- def old_function():\n-     return False"
        size = self.engine._estimate_diff_size(logs)
        assert size == 2  # Only + lines count

    def test_extract_acceptance_criteria(self):
        """Test acceptance criteria extraction."""
        prompt = """
        Task: Add retry logic
        
        - Test passes
        - Code is clean
        - No hardcoded secrets
        """
        ac = self.engine._extract_acceptance_criteria(prompt)
        assert len(ac) == 3
        assert "- Test passes" in ac[0]
        assert "- Code is clean" in ac[1]
        assert "- No hardcoded secrets" in ac[2]

    def test_extract_test_files(self):
        """Test test file extraction."""
        logs = """
        Running tests...
        test_file.py: PASS
        src/main.py: modified
        tests/test_other.py: PASS
        """
        test_files = self.engine._extract_test_files(logs)
        assert len(test_files) == 1  # Only tests/test_other.py matches the logic
        assert "tests/test_other.py: PASS" in test_files[0]

    def test_check_opa_available(self):
        """Test OPA availability check."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            assert self.engine._check_opa_available() is True

            mock_run.return_value.returncode = 1
            assert self.engine._check_opa_available() is False

            mock_run.side_effect = FileNotFoundError()
            assert self.engine._check_opa_available() is False

    def test_run_opa_eval_success(self):
        """Test successful OPA evaluation."""
        input_data = {"test": "data"}
        expected_output = {
            "result": [{
                "summary": {
                    "allowed": True,
                    "violations": [],
                    "violation_count": 0
                }
            }]
        }

        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = json.dumps(expected_output)

            result = self.engine._run_opa_eval(input_data)

            assert "summary" in result
            assert result["summary"]["allowed"] is True

    def test_run_opa_eval_failure(self):
        """Test OPA evaluation failure."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 1
            mock_run.return_value.stderr = "OPA error"

            result = self.engine._run_opa_eval({})

            assert "error" in result
            assert "OPA evaluation failed" in result.get("error", "")

    def test_run_opa_eval_invalid_json(self):
        """Test OPA evaluation with invalid JSON output."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "invalid json"

            result = self.engine._run_opa_eval({})

            assert "error" in result
            assert "Invalid JSON" in result.get("error", "") 