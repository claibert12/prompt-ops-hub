"""Regeneration loop for automatic task retry with failure analysis."""

import json
from dataclasses import dataclass
from datetime import datetime

from src.services.cursor_adapter import cursor_adapter
from src.observer.observer import observer

from .db import get_db_manager
from .guardrails import guardrails
from .patch_builder import patch_builder
from .prompt_builder import prompt_builder
from .spec_expander import ExpandedSpec, spec_expander


@dataclass
class RegenResult:
    """Result of a regeneration loop."""
    success: bool
    final_status: str
    loop_count: int
    final_run_id: int | None = None
    error_message: str | None = None
    escalation_payload: dict | None = None


class RegenLoop:
    """Handles automatic regeneration of failed tasks."""

    def __init__(self, max_loops: int = 3):
        """Initialize regeneration loop.
        
        Args:
            max_loops: Maximum number of regeneration attempts
        """
        self.max_loops = max_loops

    def run_with_regen(self, task_id: int) -> RegenResult:
        """Run a task with automatic regeneration on failure.
        
        Args:
            task_id: ID of the task to run
            
        Returns:
            RegenResult with final outcome
        """
        db_manager = get_db_manager()

        # Get the task
        task = db_manager.get_task(task_id)
        if not task:
            return RegenResult(
                success=False,
                final_status="error",
                loop_count=0,
                error_message=f"Task {task_id} not found"
            )

        # Check if task needs clarification
        expanded_spec = spec_expander.expand_task(task.task_text)
        if expanded_spec.needs_clarification:
            return self._handle_clarification_needed(task_id, expanded_spec, db_manager)

        # Run the regeneration loop
        return self._execute_regen_loop(task, expanded_spec, db_manager)

    def _handle_clarification_needed(self, task_id: int, expanded_spec: ExpandedSpec, db_manager) -> RegenResult:
        """Handle tasks that need clarification.
        
        Args:
            task_id: Task ID
            expanded_spec: Expanded specification
            db_manager: Database manager
            
        Returns:
            RegenResult indicating clarification needed
        """
        # Create a run record for clarification
        from .models import RunCreate
        run_create = RunCreate(
            task_id=task_id,
            status="needs_clarification"
        )
        run = db_manager.create_run(
            run_create,
            logs=json.dumps({
                "clarification_questions": expanded_spec.clarification_questions,
                "ambiguity_level": expanded_spec.ambiguity_level.value
            }),
            needs_clarification=True,
            clarification_questions=json.dumps(expanded_spec.clarification_questions)
        )

        return RegenResult(
            success=False,
            final_status="needs_clarification",
            loop_count=0,
            final_run_id=run.id,
            error_message="Task requires clarification before execution",
            escalation_payload={
                "clarification_questions": expanded_spec.clarification_questions,
                "ambiguity_level": expanded_spec.ambiguity_level.value
            }
        )

    def _execute_regen_loop(self, task, expanded_spec: ExpandedSpec, db_manager) -> RegenResult:
        """Execute the regeneration loop.
        
        Args:
            task: Task object
            expanded_spec: Expanded specification
            db_manager: Database manager
            
        Returns:
            RegenResult with final outcome
        """
        current_loop = 0
        last_error = None

        while current_loop < self.max_loops:
            current_loop += 1

            # Create run record for this attempt
            from .models import RunCreate
            run_create = RunCreate(
                task_id=task.id,
                status="pending"
            )
            run = db_manager.create_run(
                run_create,
                logs=f"Starting regeneration loop {current_loop}/{self.max_loops}"
            )

            try:
                # Step 1: Build enhanced prompt
                enhanced_prompt = self._build_enhanced_prompt(task, expanded_spec, current_loop, last_error)

                # Step 2: Call model (stub for now)
                llm_response = self._call_model(enhanced_prompt)

                # Step 3: Build patch from LLM response
                original_files = self._get_original_files()  # Stub - would get actual files
                patch_result = patch_builder.build_patch(original_files, llm_response)

                if not patch_result.success:
                    last_error = f"Patch building failed: {patch_result.error_message}"
                    db_manager.update_run_status(run.id, "error", last_error)
                    continue

                # Step 4: Check guardrails on patch
                patch_violations = guardrails.check_diff(patch_result.patch_content)

                if guardrails.should_block_execution(patch_violations):
                    last_error = f"Guardrails blocked execution: {guardrails.get_violation_summary(patch_violations)}"
                    db_manager.update_run_status(run.id, "error", last_error)
                    continue

                # Step 5: Apply patch via Cursor
                apply_result = cursor_adapter.apply_patch(patch_result.patch_content)

                if not apply_result.success:
                    last_error = f"Patch application failed: {apply_result.error_message}"
                    db_manager.update_run_status(run.id, "error", last_error)
                    continue

                # Step 6: Run tests
                test_result = cursor_adapter.run_tests("pytest")

                if test_result.success:
                    # Step 7: Run integrity check via Observer
                    integrity_report = self._run_integrity_check(run.id, test_result, llm_response)
                    
                    # Check if integrity score is too low
                    if integrity_report.score < 70:  # Minimum integrity threshold
                        last_error = f"Integrity check failed: score {integrity_report.score}/100 - {integrity_report.summary}"
                        db_manager.update_run_status(run.id, "integrity_failed", last_error)
                        continue
                    
                    # Check if approval is required
                    if integrity_report.score >= 70:
                        # High integrity - proceed to success
                        db_manager.update_run_status(
                            run.id,
                            "tests_passed",
                            f"Success on loop {current_loop}: {test_result.passed}/{test_result.test_count} tests passed, integrity score: {integrity_report.score}/100"
                        )

                        return RegenResult(
                            success=True,
                            final_status="tests_passed",
                            loop_count=current_loop,
                            final_run_id=run.id
                        )
                    else:
                        # Low integrity - require approval
                        db_manager.update_run_status(
                            run.id,
                            "awaiting_approval",
                            f"Awaiting approval on loop {current_loop}: {test_result.passed}/{test_result.test_count} tests passed, integrity score: {integrity_report.score}/100"
                        )

                        return RegenResult(
                            success=False,
                            final_status="awaiting_approval",
                            loop_count=current_loop,
                            final_run_id=run.id,
                            error_message=f"Integrity score {integrity_report.score}/100 requires human approval"
                        )
                else:
                    # Tests failed, prepare for next loop
                    last_error = f"Tests failed: {test_result.error_message}"
                    db_manager.update_run_status(
                        run.id,
                        "tests_failed",
                        f"Loop {current_loop} failed: {last_error}"
                    )

            except Exception as e:
                last_error = f"Unexpected error in loop {current_loop}: {str(e)}"
                db_manager.update_run_status(run.id, "error", last_error)

        # All loops failed, create escalation payload
        escalation_payload = self._create_escalation_payload(task, expanded_spec, current_loop, last_error)

        # Create final error run
        final_run_create = RunCreate(
            task_id=task.id,
            status="error"
        )
        final_run = db_manager.create_run(
            final_run_create,
            logs=f"All {self.max_loops} regeneration loops failed. Final error: {last_error}"
        )

        return RegenResult(
            success=False,
            final_status="error",
            loop_count=current_loop,
            final_run_id=final_run.id,
            error_message=last_error,
            escalation_payload=escalation_payload
        )

    def _run_integrity_check(self, run_id: int, test_result, llm_response: str):
        """Run integrity check via Observer.
        
        Args:
            run_id: Run ID
            test_result: Test execution result
            llm_response: LLM response content
            
        Returns:
            IntegrityReport
        """
        # Collect run data for integrity check
        run_data = {
            'coverage': 85,  # Would get from coverage report
            'baseline_coverage': 80,
            'diff_coverage': 100,  # Would get from diff coverage check
            'skipped_tests': 0,
            'deleted_test_files': [],
            'threshold_changed': False,
            'code_lines': 1000,  # Would count actual lines
            'test_lines': 200,   # Would count actual lines
            'content': llm_response,
            'claimed_success': True,
            'pytest_success': test_result.success
        }
        
        # Build integrity report
        integrity_report = observer.build_integrity_report(str(run_id), run_data)
        
        # Store integrity data in database
        import json
        db_manager = get_db_manager()
        db_manager.update_run_integrity(
            run_id,
            integrity_report.score,
            json.dumps([v.__dict__ for v in integrity_report.violations]),
            json.dumps(integrity_report.questions)
        )
        
        return integrity_report

    def _build_enhanced_prompt(self, task, expanded_spec: ExpandedSpec, loop_count: int, last_error: str | None) -> str:
        """Build an enhanced prompt for regeneration.
        
        Args:
            task: Task object
            expanded_spec: Expanded specification
            loop_count: Current loop number
            last_error: Error from previous attempt
            
        Returns:
            Enhanced prompt string
        """
        # Start with base prompt
        base_prompt = prompt_builder.build_task_prompt(task.task_text)

        # Add expanded specification details
        enhanced_prompt = f"""
{base_prompt}

## Expanded Specification
**Scope**: {expanded_spec.scope_summary}

**Acceptance Criteria**:
{chr(10).join(f"- {ac}" for ac in expanded_spec.acceptance_criteria)}

**Edge Cases to Consider**:
{chr(10).join(f"- {ec}" for ec in expanded_spec.edge_cases)}

**Rollback Considerations**:
{chr(10).join(f"- {rn}" for rn in expanded_spec.rollback_notes)}
"""

        # Add regeneration context if this is a retry
        if loop_count > 1 and last_error:
            enhanced_prompt += f"""

## Previous Attempt Analysis
This is regeneration attempt #{loop_count}. The previous attempt failed with the following error:

**Error**: {last_error}

**Instructions**: Please analyze the error above and provide a corrected implementation. Focus on:
1. Addressing the specific failure points mentioned in the error
2. Ensuring all acceptance criteria are met
3. Following the expanded specification more closely
4. Adding appropriate error handling and edge case coverage
"""

        return enhanced_prompt

    def _call_model(self, prompt: str) -> str:
        """Call the LLM model (stub implementation).
        
        Args:
            prompt: Prompt to send to model
            
        Returns:
            Model response
        """
        # This is a stub - in a real implementation, this would call the actual model
        # For now, return a mock response that would pass tests
        return """
Here's the implementation:

```python src/main.py
def new_feature():
    \"\"\"Implement the requested feature.\"\"\"
    # This is a mock implementation that would pass tests
    return "success"

def test_new_feature():
    \"\"\"Test the new feature.\"\"\"
    assert new_feature() == "success"
```
"""

    def _get_original_files(self) -> dict[str, str]:
        """Get original file contents (stub implementation).
        
        Returns:
            Dict of file_path -> file_content
        """
        # This is a stub - in a real implementation, this would read actual files
        return {
            "src/main.py": "# Original file content\n",
            "tests/test_main.py": "# Original test content\n"
        }

    def _create_escalation_payload(self, task, expanded_spec: ExpandedSpec, loop_count: int, last_error: str) -> dict:
        """Create escalation payload for failed regeneration.
        
        Args:
            task: Task object
            expanded_spec: Expanded specification
            loop_count: Number of loops attempted
            last_error: Final error message
            
        Returns:
            Escalation payload dictionary
        """
        return {
            "task_id": task.id,
            "task_text": task.task_text,
            "loop_count": loop_count,
            "max_loops": self.max_loops,
            "final_error": last_error,
            "expanded_spec": {
                "scope_summary": expanded_spec.scope_summary,
                "acceptance_criteria": expanded_spec.acceptance_criteria,
                "edge_cases": expanded_spec.edge_cases,
                "rollback_notes": expanded_spec.rollback_notes
            },
            "escalation_timestamp": datetime.utcnow().isoformat(),
            "recommended_action": "Manual intervention required - task needs human review and implementation"
        }

    def clarify_and_continue(self, task_id: int, answers: list[str]) -> RegenResult:
        """Continue execution after clarification answers are provided.
        
        Args:
            task_id: Task ID
            answers: List of answers to clarification questions
            
        Returns:
            RegenResult with outcome
        """
        db_manager = get_db_manager()

        # Get the task
        task = db_manager.get_task(task_id)
        if not task:
            return RegenResult(
                success=False,
                final_status="error",
                loop_count=0,
                error_message=f"Task {task_id} not found"
            )

        # Update the task with clarification answers
        enhanced_task_text = f"{task.task_text}\n\nClarification answers:\n" + "\n".join(f"- {answer}" for answer in answers)

        # Re-expand the specification
        expanded_spec = spec_expander.expand_task(enhanced_task_text)

        # Continue with regeneration loop
        return self._execute_regen_loop(task, expanded_spec, db_manager)


# Global regeneration loop instance
regen_loop = RegenLoop()
