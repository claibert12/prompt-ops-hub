"""Tests for regeneration loop functionality."""
import os
import tempfile
from unittest.mock import MagicMock, patch

from src.core.db import get_db_manager, reset_db_manager
from src.core.regen import regen_loop


class TestRegenLoop:
    """Test cases for RegenLoop."""

    def setup_method(self):
        """Set up test environment."""
        # Set up temporary database
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")
        os.environ["DATABASE_URL"] = f"sqlite:///{self.db_path}"

        # Reset database manager
        reset_db_manager()
        self.db_manager = get_db_manager()
        self.db_manager.create_tables()

        # Create a test task
        from src.core.models import TaskCreate
        task_create = TaskCreate(
            task_text="Update the main function to print hello world"
        )
        self.task = self.db_manager.create_task(task_create, "Test prompt")

    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        reset_db_manager()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch('src.core.regen.regen_loop._call_model')
    @patch('src.core.regen.regen_loop._get_original_files')
    @patch('src.services.cursor_adapter.cursor_adapter.apply_patch')
    @patch('src.services.cursor_adapter.cursor_adapter.run_tests')
    def test_run_with_regen_success_first_try(self, mock_run_tests, mock_apply_patch,
                                            mock_get_files, mock_call_model):
        """Test successful regeneration on first try."""
        # Mock model response
        mock_call_model.return_value = """
Here's the updated code:

```python src/main.py
def main():
    print("Hello, World!")
```
"""

        # Mock original files
        mock_get_files.return_value = {"src/main.py": "def main():\n    pass\n"}

        # Mock successful patch application
        mock_apply_patch.return_value = MagicMock(success=True, logs="Patch applied successfully")

        # Mock successful tests
        mock_run_tests.return_value = MagicMock(success=True, output="1 passed")

        result = regen_loop.run_with_regen(self.task.id)

        assert result.success
        assert result.final_status == "tests_passed"
        assert result.loop_count == 1
        assert result.error_message is None
        assert result.escalation_payload is None

    @patch('src.core.regen.regen_loop._call_model')
    @patch('src.core.regen.regen_loop._get_original_files')
    @patch('src.services.cursor_adapter.cursor_adapter.apply_patch')
    @patch('src.services.cursor_adapter.cursor_adapter.run_tests')
    def test_run_with_regen_fail_then_succeed(self, mock_run_tests, mock_apply_patch,
                                            mock_get_files, mock_call_model):
        """Test regeneration that fails first, then succeeds."""
        # Mock model responses (first fails, second succeeds)
        mock_call_model.side_effect = [
            """
Here's the updated code:

```python src/main.py
def main():
    print("Hello")  # Missing World
```
""",
            """
Here's the corrected code:

```python src/main.py
def main():
    print("Hello, World!")
```
"""
        ]

        # Mock original files
        mock_get_files.return_value = {"src/main.py": "def main():\n    pass\n"}

        # Mock successful patch application
        mock_apply_patch.return_value = MagicMock(success=True, logs="Patch applied successfully")

        # Mock tests (first fails, second succeeds)
        mock_run_tests.side_effect = [
            MagicMock(success=False, output="AssertionError: expected 'Hello, World!' but got 'Hello'"),
            MagicMock(success=True, output="1 passed")
        ]

        result = regen_loop.run_with_regen(self.task.id)

        assert result.success
        assert result.final_status == "tests_passed"
        assert result.loop_count == 2
        assert result.error_message is None
        assert result.escalation_payload is None

        # Verify model was called twice
        assert mock_call_model.call_count == 2

    @patch('src.core.regen.regen_loop._call_model')
    @patch('src.core.regen.regen_loop._get_original_files')
    @patch('src.services.cursor_adapter.cursor_adapter.apply_patch')
    @patch('src.services.cursor_adapter.cursor_adapter.run_tests')
    def test_run_with_regen_max_loops_exceeded(self, mock_run_tests, mock_apply_patch,
                                             mock_get_files, mock_call_model):
        """Test regeneration that exceeds max loops and escalates."""
        # Mock model responses (all fail)
        mock_call_model.return_value = """
Here's the updated code:

```python src/main.py
def main():
    print("Wrong output")
```
"""

        # Mock original files
        mock_get_files.return_value = {"src/main.py": "def main():\n    pass\n"}

        # Mock successful patch application
        mock_apply_patch.return_value = MagicMock(success=True, logs="Patch applied successfully")

        # Mock failing tests
        mock_run_tests.return_value = MagicMock(success=False, output="AssertionError: test failed")

        result = regen_loop.run_with_regen(self.task.id)

        assert not result.success
        assert result.final_status == "error"
        assert result.loop_count == 3
        assert result.error_message is not None
        assert result.escalation_payload is not None

        # Verify escalation payload contains relevant info
        escalation = result.escalation_payload
        assert "task_id" in escalation
        assert "loop_count" in escalation
        assert "final_error" in escalation

    @patch('src.core.regen.regen_loop._call_model')
    @patch('src.core.regen.regen_loop._get_original_files')
    @patch('src.services.cursor_adapter.cursor_adapter.apply_patch')
    def test_run_with_regen_patch_application_fails(self, mock_apply_patch,
                                                  mock_get_files, mock_call_model):
        """Test regeneration when patch application fails."""
        # Mock model response
        mock_call_model.return_value = """
Here's the updated code:

```python src/main.py
def main():
    print("Hello, World!")
```
"""

        # Mock original files
        mock_get_files.return_value = {"src/main.py": "def main():\n    pass\n"}

        # Mock failed patch application
        mock_apply_patch.return_value = MagicMock(success=False, error_message="Patch failed to apply")

        result = regen_loop.run_with_regen(self.task.id)

        assert not result.success
        assert result.final_status == "error"
        assert result.loop_count == 3
        assert "Patch failed to apply" in result.error_message

    @patch('src.core.regen.regen_loop._call_model')
    @patch('src.core.regen.regen_loop._get_original_files')
    @patch('src.services.cursor_adapter.cursor_adapter.apply_patch')
    @patch('src.services.cursor_adapter.cursor_adapter.run_tests')
    @patch('src.core.guardrails.guardrails.check_diff')
    def test_run_with_regen_guardrails_violation(self, mock_check_diff, mock_run_tests,
                                               mock_apply_patch, mock_get_files, mock_call_model):
        """Test regeneration when guardrails detect violations."""
        # Mock model response
        mock_call_model.return_value = """
Here's the updated code:

```python src/main.py
def main():
    print("Hello, World!")
```
"""

        # Mock original files
        mock_get_files.return_value = {"src/main.py": "def main():\n    pass\n"}

        # Mock guardrails violation
        from src.core.guardrails import Violation, ViolationType
        mock_check_diff.return_value = [
            Violation(type=ViolationType.SECRETS_DETECTED, message="Secret found", line_number=1, severity="critical")
        ]

        # Mock successful patch application
        mock_apply_patch.return_value = MagicMock(success=True, logs="Patch applied successfully")

        # Mock successful tests (so guardrails violation is the actual error)
        mock_run_tests.return_value = MagicMock(success=True, passed=10, test_count=10)

        result = regen_loop.run_with_regen(self.task.id)

        assert not result.success
        assert result.final_status == "error"
        assert result.loop_count == 3
        assert "Secret found" in result.error_message

    def test_handle_clarification_needed(self):
        """Test handling when task needs clarification."""
        # Create a task that needs clarification
        from src.core.models import TaskCreate
        task_create = TaskCreate(task_text="Vague task description")
        clarification_task = self.db_manager.create_task(task_create, "Do something with the data")

        # Mock spec expander to return clarification needed
        with patch('src.core.regen.spec_expander.expand_task') as mock_expand:
            from src.core.spec_expander import AmbiguityLevel, ExpandedSpec
            mock_expand.return_value = ExpandedSpec(
                original_goal="Vague task description",
                scope_summary="Goal requires clarification",
                acceptance_criteria=[],
                edge_cases=[],
                rollback_notes=[],
                needs_clarification=True,
                clarification_questions=["What data?", "What operation?"],
                ambiguity_level=AmbiguityLevel.BLOCKING
            )

            result = regen_loop.run_with_regen(clarification_task.id)

        assert not result.success
        assert result.final_status == "needs_clarification"
        assert result.loop_count == 0

        # Verify clarification questions are stored
        runs = self.db_manager.list_runs()
        assert len(runs) == 1
        run = runs[0]
        assert run.needs_clarification
        assert "What data?" in run.clarification_questions

    def test_clarify_and_continue(self):
        """Test providing clarification and continuing task execution."""
        # Create a run that needs clarification
        from src.core.models import RunCreate
        run_create = RunCreate(task_id=self.task.id, status="needs_clarification")
        run = self.db_manager.create_run(run_create, needs_clarification=True, clarification_questions='["What data?", "What operation?"]')

        # Mock spec expander to return clear spec after clarification
        with patch('src.core.regen.spec_expander.expand_task') as mock_expand:
            mock_expand.return_value = MagicMock(
                needs_clarification=False,
                scope_summary="Update main function",
                acceptance_criteria=["Function prints hello world"],
                edge_cases=["Empty input"],
                rollback_notes=["Revert to original function"]
            )

            # Mock successful execution after clarification
            with patch('src.core.regen.regen_loop._execute_regen_loop') as mock_execute:
                mock_execute.return_value = MagicMock(success=True, final_status="tests_passed")

                result = regen_loop.clarify_and_continue(
                    self.task.id,
                    answers=["Use test data", "Print operation"]
                )

        assert result.success
        assert result.final_status == "tests_passed"

    @patch('src.core.regen.regen_loop._call_model')
    def test_build_enhanced_prompt_with_failure_context(self, mock_call_model):
        """Test building enhanced prompt with failure context."""
        # Mock initial model call
        mock_call_model.return_value = "Initial response"

        # Create a run with failure context
        from src.core.models import RunCreate
        run_create = RunCreate(task_id=self.task.id, status="tests_failed")
        run = self.db_manager.create_run(run_create, loop_count=1, last_error="Test assertion failed")

        # Test building enhanced prompt
        from src.core.spec_expander import ExpandedSpec
        expanded_spec = ExpandedSpec(
            original_goal="Test goal",
            scope_summary="Test scope",
            acceptance_criteria=["Test criteria"],
            edge_cases=["Test edge case"],
            rollback_notes=["Test rollback"],
            needs_clarification=False,
            clarification_questions=None,
            ambiguity_level=None
        )
        enhanced_prompt = regen_loop._build_enhanced_prompt(self.task, expanded_spec, 2, "Test assertion failed")

        assert "Expanded Specification" in enhanced_prompt
        assert "Previous Attempt Analysis" in enhanced_prompt
        assert "Test assertion failed" in enhanced_prompt

    def test_create_escalation_payload(self):
        """Test creating escalation payload."""
        # Create a run with failure context
        from src.core.models import RunCreate
        run_create = RunCreate(task_id=self.task.id, status="error")
        run = self.db_manager.create_run(run_create, loop_count=2, last_error="Max loops exceeded")

        # Mock model responses
        model_responses = ["Response 1", "Response 2"]

        from src.core.spec_expander import ExpandedSpec
        expanded_spec = ExpandedSpec(
            original_goal="Test goal",
            scope_summary="Test scope",
            acceptance_criteria=["Test criteria"],
            edge_cases=["Test edge case"],
            rollback_notes=["Test rollback"],
            needs_clarification=False,
            clarification_questions=None,
            ambiguity_level=None
        )
        payload = regen_loop._create_escalation_payload(self.task, expanded_spec, 2, "Max loops exceeded")

        assert payload["task_id"] == self.task.id
        assert payload["loop_count"] == 2
        assert payload["final_error"] == "Max loops exceeded"
        assert "escalation_timestamp" in payload

    @patch('src.core.regen.regen_loop._call_model')
    def test_call_model_stub(self, mock_call_model):
        """Test the stub model call implementation."""
        # Mock the method to return a string
        mock_call_model.return_value = "Mock model response"

        # The stub should return a basic response
        response = regen_loop._call_model("Test prompt")

        # Should be a string response
        assert isinstance(response, str)
        assert len(response) > 0

    def test_get_original_files_stub(self):
        """Test the stub original files implementation."""
        # The stub should return a basic file structure
        files = regen_loop._get_original_files()

        # Should be a dict with file paths and contents
        assert isinstance(files, dict)
        assert len(files) > 0

        # Should contain basic file structure
        assert "src/main.py" in files
        assert isinstance(files["src/main.py"], str)

    def test_execute_regen_loop_success(self):
        """Test successful execution of regen loop."""
        with patch('src.core.regen.regen_loop._call_model') as mock_call_model:
            mock_call_model.return_value = "Successful response"

            with patch('src.core.regen.patch_builder.build_patch') as mock_build_patch:
                mock_build_patch.return_value = MagicMock(success=True, patch_content="patch")

                with patch('src.services.cursor_adapter.cursor_adapter.apply_patch') as mock_apply:
                    mock_apply.return_value = MagicMock(success=True)

                    with patch('src.services.cursor_adapter.cursor_adapter.run_tests') as mock_tests:
                        mock_tests.return_value = MagicMock(success=True)

                        # Mock expanded spec
                        from src.core.spec_expander import ExpandedSpec
                        expanded_spec = ExpandedSpec(
                            original_goal="Test goal",
                            scope_summary="Test scope",
                            acceptance_criteria=["Test criteria"],
                            edge_cases=["Test edge case"],
                            rollback_notes=["Test rollback"],
                            needs_clarification=False,
                            clarification_questions=None,
                            ambiguity_level=None
                        )
                        result = regen_loop._execute_regen_loop(self.task, expanded_spec, self.db_manager)

                        assert result.success
                        assert result.final_status == "tests_passed"

    def test_execute_regen_loop_with_guardrails_violation(self):
        """Test regen loop with guardrails violation."""
        with patch('src.core.regen.regen_loop._call_model') as mock_call_model:
            mock_call_model.return_value = "Response with violation"

            with patch('src.core.regen.patch_builder.build_patch') as mock_build_patch:
                mock_build_patch.return_value = MagicMock(success=True, patch_content="patch")

                with patch('src.services.cursor_adapter.cursor_adapter.apply_patch') as mock_apply:
                    mock_apply.return_value = MagicMock(success=True)

                    with patch('src.services.cursor_adapter.cursor_adapter.run_tests') as mock_tests:
                        mock_tests.return_value = MagicMock(success=True, passed=10, test_count=10)

                        with patch('src.core.guardrails.guardrails.check_diff') as mock_check:
                            from src.core.guardrails import Violation, ViolationType
                            mock_check.return_value = [
                                Violation(type=ViolationType.SECRETS_DETECTED, message="Secret found", line_number=1, severity="critical")
                            ]

                            # Mock expanded spec
                            from src.core.spec_expander import ExpandedSpec
                            expanded_spec = ExpandedSpec(
                                original_goal="Test goal",
                                scope_summary="Test scope",
                                acceptance_criteria=["Test criteria"],
                                edge_cases=["Test edge case"],
                                rollback_notes=["Test rollback"],
                                needs_clarification=False,
                                clarification_questions=None,
                                ambiguity_level=None
                            )
                            result = regen_loop._execute_regen_loop(self.task, expanded_spec, self.db_manager)

                            assert not result.success
                            assert result.final_status == "error"
                            assert "Secret found" in result.error_message
