"""CLI interface for Prompt Ops Hub."""


import typer
import os
from pathlib import Path

from src.core.db import get_db_manager
from src.core.guardrails import guardrails
from src.core.models import RunCreate, TaskCreate
from src.core.policy import policy_engine
from src.core.prompt_builder import prompt_builder
from src.core.regen import regen_loop
from src.core.spec_expander import spec_expander
from src.services.cursor_adapter import cursor_adapter
from src.services.github_adapter import get_github_adapter
from src.cli_init.project_scaffold import ProjectScaffold
from src.cli_snippet.ci_snippet import CISnippetGenerator

app = typer.Typer(help="Prompt Ops Hub CLI")


@app.command()
def task(
    task_description: str = typer.Argument(..., help="Task description"),
    capability: str = typer.Option("reasoning", help="Model capability (reasoning, fast, cheap, embedding)"),
    save: bool = typer.Option(True, "--save/--no-save", help="Save task to database"),
):
    """Create a task and build a prompt with context."""
    try:
        # Build the prompt
        built_prompt = prompt_builder.build_task_prompt(task_description)

        # Print the prompt
        typer.echo("=" * 80)
        typer.echo("GENERATED PROMPT")
        typer.echo("=" * 80)
        typer.echo(built_prompt)
        typer.echo("=" * 80)

        # Save to database if requested
        if save:
            # Ensure database tables exist
            db_manager = get_db_manager()
            db_manager.create_tables()

            # Create task
            task_create = TaskCreate(task_text=task_description)
            task = db_manager.create_task(task_create, built_prompt)

            typer.echo(f"\nTask saved with ID: {task.id}")
            typer.echo(f"Created at: {task.created_at}")

    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def list(
    limit: int | None = typer.Option(None, help="Maximum number of tasks to show"),
    show_prompt: bool = typer.Option(False, help="Show full prompt content"),
):
    """List saved tasks."""
    try:
        # Ensure database tables exist
        db_manager = get_db_manager()
        db_manager.create_tables()

        # Get tasks
        tasks = db_manager.list_tasks(limit=limit)

        if not tasks:
            typer.echo("No tasks found.")
            return

        typer.echo(f"Found {len(tasks)} task(s):\n")

        for task in tasks:
            typer.echo(f"ID: {task.id}")
            typer.echo(f"Created: {task.created_at}")
            typer.echo(f"Task: {task.task_text}")

            if show_prompt:
                typer.echo(f"Prompt: {task.built_prompt}")
            else:
                # Show first 80 characters of prompt
                prompt_preview = task.built_prompt[:80]
                if len(task.built_prompt) > 80:
                    prompt_preview += "..."
                typer.echo(f"Prompt: {prompt_preview}")

            typer.echo("-" * 40)

    except Exception as e:
        typer.echo(f"❌ Error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def show(
    task_id: int = typer.Argument(..., help="Task ID to show"),
):
    """Show details of a specific task."""
    try:
        # Ensure database tables exist
        db_manager = get_db_manager()
        db_manager.create_tables()

        # Get task
        task = db_manager.get_task(task_id)

        if not task:
            typer.echo(f"❌ Task with ID {task_id} not found.")
            raise typer.Exit(1)

        typer.echo(f"Task ID: {task.id}")
        typer.echo(f"Created: {task.created_at}")
        typer.echo(f"Task: {task.task_text}")
        typer.echo("\n" + "=" * 80)
        typer.echo("FULL PROMPT")
        typer.echo("=" * 80)
        typer.echo(task.built_prompt)
        typer.echo("=" * 80)

    except Exception as e:
        typer.echo(f"❌ Error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def delete(
    task_id: int = typer.Argument(..., help="Task ID to delete"),
):
    """Delete a task."""
    try:
        # Ensure database tables exist
        db_manager = get_db_manager()
        db_manager.create_tables()

        # Delete task
        deleted = db_manager.delete_task(task_id)

        if deleted:
            typer.echo(f"✅ Task {task_id} deleted successfully.")
        else:
            typer.echo(f"❌ Task {task_id} not found.")
            raise typer.Exit(1)

    except Exception as e:
        typer.echo(f"❌ Error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def init():
    """Initialize the database."""
    try:
        db_manager = get_db_manager()
        db_manager.create_tables()
        typer.echo("Database initialized successfully")
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def run_task(
    task_id: int = typer.Argument(..., help="Task ID to run"),
    test_command: str = typer.Option("pytest", help="Test command to run"),
):
    """Execute a task through Cursor adapter and run tests."""
    try:
        # Ensure database tables exist
        db_manager = get_db_manager()
        db_manager.create_tables()

        # Get task
        task = db_manager.get_task(task_id)
        if not task:
            typer.echo(f"❌ Task with ID {task_id} not found.")
            raise typer.Exit(1)

        typer.echo(f"🚀 Running task {task_id}: {task.task_text}")

        # Create run record
        run_create = RunCreate(task_id=task_id, status="pending")
        run = db_manager.create_run(run_create, "Starting task execution...")

        try:
            # Check guardrails on the prompt
            prompt_violations = guardrails.check_prompt(task.built_prompt)
            if prompt_violations:
                typer.echo("⚠️  Guardrails violations detected:")
                typer.echo(guardrails.get_violation_summary(prompt_violations))

                if guardrails.should_block_execution(prompt_violations):
                    db_manager.update_run_status(run.id, "error", "Execution blocked by guardrails")
                    typer.echo("❌ Execution blocked due to critical violations.")
                    raise typer.Exit(1)

            # Simulate patch application (stub for now)
            typer.echo("📝 Applying patch via Cursor...")
            dummy_patch = f"# Patch for task {task_id}\n# This is a simulated patch\n"

            # Check guardrails on the patch
            patch_violations = guardrails.check_diff(dummy_patch)
            if patch_violations:
                typer.echo("⚠️  Patch violations detected:")
                typer.echo(guardrails.get_violation_summary(patch_violations))

            # Apply patch via Cursor adapter
            apply_result = cursor_adapter.apply_patch(dummy_patch)
            if not apply_result.success:
                db_manager.update_run_status(run.id, "error", f"Patch application failed: {apply_result.error_message}")
                typer.echo(f"❌ Patch application failed: {apply_result.error_message}")
                raise typer.Exit(1)

            db_manager.update_run_status(run.id, "applied", "Patch applied successfully")
            typer.echo("✅ Patch applied successfully")

            # Run tests
            typer.echo(f"🧪 Running tests: {test_command}")
            test_result = cursor_adapter.run_tests(test_command)

            if test_result.success:
                db_manager.update_run_status(run.id, "tests_passed",
                    f"Tests passed: {test_result.passed}/{test_result.test_count}")
                typer.echo(f"✅ Tests passed: {test_result.passed}/{test_result.test_count}")
            else:
                db_manager.update_run_status(run.id, "tests_failed",
                    f"Tests failed: {test_result.error_message}")
                typer.echo(f"❌ Tests failed: {test_result.error_message}")
                raise typer.Exit(1)

        except Exception as e:
            db_manager.update_run_status(run.id, "error", f"Execution error: {str(e)}")
            typer.echo(f"❌ Execution error: {str(e)}")
            raise typer.Exit(1)

    except Exception as e:
        typer.echo(f"❌ Error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def pr(
    task_id: int = typer.Argument(..., help="Task ID to create PR for"),
    title: str | None = typer.Option(None, help="PR title (defaults to task text)"),
    base: str = typer.Option("main", help="Base branch for PR"),
):
    """Create a pull request for a task."""
    try:
        # Ensure database tables exist
        db_manager = get_db_manager()
        db_manager.create_tables()

        # Get task
        task = db_manager.get_task(task_id)
        if not task:
            typer.echo(f"❌ Task with ID {task_id} not found.")
            raise typer.Exit(1)

        # Get latest run for this task
        runs = db_manager.list_runs(task_id=task_id, limit=1)
        if not runs:
            typer.echo(f"❌ No runs found for task {task_id}. Run 'po-cli run-task {task_id}' first.")
            raise typer.Exit(1)

        latest_run = runs[0]
        if latest_run.status != "tests_passed":
            typer.echo(f"❌ Task {task_id} has not passed tests (status: {latest_run.status})")
            raise typer.Exit(1)

        typer.echo(f"🔀 Creating PR for task {task_id}: {task.task_text}")

        # Create branch name
        branch_name = f"task-{task_id}-{int(task.created_at.timestamp())}"

        # Create branch
        github_adapter = get_github_adapter()
        if not github_adapter.create_branch(branch_name):
            typer.echo("❌ Failed to create branch")
            raise typer.Exit(1)

        typer.echo(f"✅ Created branch: {branch_name}")

        # Simulate committing changes
        dummy_files = ["src/main.py"]  # This would be the actual changed files
        commit_message = f"Implement task {task_id}: {task.task_text}"

        if not github_adapter.commit_and_push(dummy_files, commit_message):
            typer.echo("❌ Failed to commit and push changes")
            raise typer.Exit(1)

        typer.echo("✅ Committed and pushed changes")

        # Create PR
        pr_title = title or f"Task {task_id}: {task.task_text}"
        pr_body = f"""
## Task Implementation

**Task ID**: {task_id}
**Description**: {task.task_text}

## Changes Made
- Implemented the requested functionality
- Added appropriate tests
- Followed coding standards

## Testing
- All tests pass: {latest_run.logs}

## Acceptance Criteria
- [x] Task implementation follows the specified rules and constraints
- [x] Code changes are properly tested with unit and integration tests
- [x] No hardcoded secrets or sensitive information
- [x] Configuration uses environment variables where appropriate
        """

        pr_result = github_adapter.open_pr(pr_title, pr_body, branch_name, base)

        if pr_result.success:
            db_manager.update_run_status(latest_run.id, "pr_opened",
                f"PR created: {pr_result.pr_url}")
            typer.echo("✅ PR created successfully!")
            typer.echo(f"🔗 PR URL: {pr_result.pr_url}")
            typer.echo(f"📊 PR Number: {pr_result.pr_number}")
        else:
            typer.echo(f"❌ Failed to create PR: {pr_result.error_message}")
            raise typer.Exit(1)

    except Exception as e:
        typer.echo(f"❌ Error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def runs(
    task_id: int | None = typer.Option(None, help="Filter runs by task ID"),
    limit: int | None = typer.Option(None, help="Maximum number of runs to show"),
):
    """List task runs."""
    try:
        # Ensure database tables exist
        db_manager = get_db_manager()
        db_manager.create_tables()

        # Get runs
        runs = db_manager.list_runs(task_id=task_id, limit=limit)

        if not runs:
            typer.echo("No runs found.")
            return

        typer.echo(f"Found {len(runs)} run(s):\n")

        for run in runs:
            typer.echo(f"Run ID: {run.id}")
            typer.echo(f"Task ID: {run.task_id}")
            typer.echo(f"Status: {run.status}")
            typer.echo(f"Created: {run.created_at}")

            if run.logs:
                logs_preview = run.logs[:100]
                if len(run.logs) > 100:
                    logs_preview += "..."
                typer.echo(f"Logs: {logs_preview}")

            typer.echo("-" * 40)

    except Exception as e:
        typer.echo(f"❌ Error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def expand(
    goal: str = typer.Argument(..., help="Goal to expand"),
):
    """Expand a goal into a detailed specification."""
    try:
        expanded_spec = spec_expander.expand_task(goal)

        typer.echo("=" * 80)
        typer.echo("EXPANDED SPECIFICATION")
        typer.echo("=" * 80)
        typer.echo(f"Original Goal: {expanded_spec.original_goal}")
        typer.echo(f"Ambiguity Level: {expanded_spec.ambiguity_level.value}")
        typer.echo(f"Needs Clarification: {expanded_spec.needs_clarification}")

        if expanded_spec.needs_clarification:
            typer.echo("\n🔍 CLARIFICATION NEEDED")
            typer.echo("Please answer the following questions:")
            for i, question in enumerate(expanded_spec.clarification_questions, 1):
                typer.echo(f"{i}. {question}")
        else:
            typer.echo(f"\n📋 Scope: {expanded_spec.scope_summary}")

            typer.echo("\n✅ Acceptance Criteria:")
            for ac in expanded_spec.acceptance_criteria:
                typer.echo(f"  - {ac}")

            typer.echo("\n⚠️  Edge Cases:")
            for ec in expanded_spec.edge_cases:
                typer.echo(f"  - {ec}")

            typer.echo("\n🔄 Rollback Notes:")
            for rn in expanded_spec.rollback_notes:
                typer.echo(f"  - {rn}")

        typer.echo("=" * 80)

    except Exception as e:
        typer.echo(f"❌ Error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def run_auto(
    task_id: int = typer.Argument(..., help="Task ID to run with auto-regeneration"),
    max_loops: int = typer.Option(3, help="Maximum number of regeneration loops"),
):
    """Run a task with automatic regeneration on failure."""
    try:
        typer.echo(f"🚀 Starting auto-regeneration for task {task_id} (max {max_loops} loops)")

        # Create regen loop with specified max loops
        regen = regen_loop.__class__(max_loops=max_loops)
        result = regen.run_with_regen(task_id)

        if result.success:
            typer.echo(f"✅ Success! Completed in {result.loop_count} loop(s)")
            typer.echo(f"📊 Final status: {result.final_status}")
            if result.final_run_id:
                typer.echo(f"🆔 Run ID: {result.final_run_id}")
        else:
            typer.echo(f"❌ Failed after {result.loop_count} loop(s)")
            typer.echo(f"📊 Final status: {result.final_status}")
            if result.error_message:
                typer.echo(f"💥 Error: {result.error_message}")

            if result.escalation_payload:
                typer.echo("\n📋 ESCALATION PAYLOAD:")
                typer.echo(f"  - Task: {result.escalation_payload.get('task_text', 'Unknown')}")
                typer.echo(f"  - Loops attempted: {result.escalation_payload.get('loop_count', 0)}")
                typer.echo(f"  - Final error: {result.escalation_payload.get('final_error', 'Unknown')}")
                typer.echo(f"  - Recommended action: {result.escalation_payload.get('recommended_action', 'Unknown')}")

    except Exception as e:
        typer.echo(f"❌ Error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def clarify(
    task_id: int = typer.Argument(..., help="Task ID to clarify"),
    answers: str = typer.Argument(..., help="Comma-separated answers to clarification questions"),
):
    """Provide clarification answers for a task."""
    try:
        typer.echo(f"Providing clarification for task {task_id}")

        # Parse answers
        answer_list = [answer.strip() for answer in answers.split(',')]

        # Ensure database tables exist
        db_manager = get_db_manager()
        db_manager.create_tables()

        # Get task data
        task = db_manager.get_task(task_id)
        if not task:
            typer.echo(f"Task {task_id} not found")
            raise typer.Exit(1)

        typer.echo(f"Answers: {answer_list}")

        # Store answers (in a real implementation, this would update the task)
        typer.echo("Success!")

    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def policy_check(
    run_id: int = typer.Argument(..., help="Run ID to check policy for"),
):
    """Check policy compliance for a specific run."""
    try:
        typer.echo(f"🔍 Checking policy compliance for run {run_id}")

        # Ensure database tables exist
        db_manager = get_db_manager()
        db_manager.create_tables()

        # Evaluate policy
        result = policy_engine.evaluate_run(run_id, db_manager)

        if result.error:
            typer.echo(f"❌ Policy evaluation failed: {result.error}")
            raise typer.Exit(1)

        typer.echo("=" * 80)
        typer.echo("POLICY EVALUATION RESULTS")
        typer.echo("=" * 80)

        if result.allowed:
            typer.echo("✅ Policy: ALLOWED")
        else:
            typer.echo("❌ Policy: DENIED")

        typer.echo(f"📊 Violations: {result.violation_count}")

        if result.violations:
            typer.echo("\n🚨 VIOLATIONS:")
            for violation in result.violations:
                typer.echo(f"  - {violation}")

        typer.echo("=" * 80)

        # Exit with appropriate code
        if not result.allowed:
            raise typer.Exit(1)

    except Exception as e:
        typer.echo(f"❌ Error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def integrity(
    run_id: int = typer.Argument(..., help="Run ID to check integrity for"),
):
    """Check integrity for a specific run."""
    try:
        typer.echo(f"🔍 Checking integrity for run {run_id}")

        # Ensure database tables exist
        db_manager = get_db_manager()
        db_manager.create_tables()

        # Get run data
        run = db_manager.get_run(run_id)
        if not run:
            typer.echo(f"❌ Run {run_id} not found")
            raise typer.Exit(1)

        # Parse integrity data
        import json
        violations = json.loads(run.integrity_violations) if run.integrity_violations else []
        questions = json.loads(run.integrity_questions) if run.integrity_questions else []

        typer.echo("=" * 80)
        typer.echo("INTEGRITY REPORT")
        typer.echo("=" * 80)
        typer.echo(f"📊 Integrity Score: {run.integrity_score}/100")
        typer.echo(f"🚨 Violations: {len(violations)}")
        typer.echo(f"❓ Questions: {len(questions)}")

        if violations:
            typer.echo("\n🚨 VIOLATIONS:")
            for violation in violations:
                typer.echo(f"  - {violation.get('message', 'Unknown violation')}")

        if questions:
            typer.echo("\n❓ INTEGRITY QUESTIONS:")
            for i, question in enumerate(questions, 1):
                typer.echo(f"  {i}. {question}")

        typer.echo("=" * 80)

    except Exception as e:
        typer.echo(f"❌ Error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def answer(
    run_id: int = typer.Argument(..., help="Run ID to answer questions for"),
    answers: str = typer.Argument(..., help="Comma-separated answers to integrity questions"),
):
    """Provide answers to integrity questions."""
    try:
        typer.echo(f"Providing answers for run {run_id}")

        # Parse answers
        answer_list = [answer.strip() for answer in answers.split(',')]

        # Ensure database tables exist
        db_manager = get_db_manager()
        db_manager.create_tables()

        # Get run data
        run = db_manager.get_run(run_id)
        if not run:
            typer.echo(f"Run {run_id} not found")
            raise typer.Exit(1)

        # Parse existing questions
        import json
        questions = json.loads(run.integrity_questions) if run.integrity_questions else []

        if len(answer_list) != len(questions):
            typer.echo(f"Expected {len(questions)} answers, got {len(answer_list)}")
            raise typer.Exit(1)

        typer.echo(f"Answers: {answer_list}")

        # Store answers (in a real implementation, this would update the run)
        typer.echo("answered")

    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def init_project(
    project_name: str = typer.Argument(..., help="Name of the project to create"),
    project_path: str = typer.Option(None, help="Path where to create the project (defaults to current directory)"),
):
    """Initialize a new project with integrity gates."""
    try:
        if project_path is None:
            project_path = os.getcwd()
        
        typer.echo(f"Creating project '{project_name}' at {project_path}")
        
        # Create project scaffold
        scaffold = ProjectScaffold(project_name, project_path)
        results = scaffold.scaffold_project()
        
        if results["success"]:
            typer.echo("Project created successfully!")
            typer.echo(f"Project path: {results['project_path']}")
            typer.echo(f"Created directories: {len(results['structure']['created_dirs'])}")
            typer.echo(f"Created files: {len(results['structure']['created_files'])}")
            typer.echo("Success!")
            
            typer.echo("\nNext steps:")
            typer.echo("1. cd " + results['project_path'])
            typer.echo("2. pip install -e '.[dev]'")
            typer.echo("3. pytest")
            typer.echo("4. Start coding!")
        else:
            typer.echo("Project creation failed!")
            for error in results["errors"]:
                typer.echo(f"  - {error}")
            raise typer.Exit(1)
    
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def ci_snippet(
    check: bool = typer.Option(False, "--check", help="Check if current CI workflow matches canonical version"),
    update: bool = typer.Option(False, "--update", help="Update CI workflow to match canonical version"),
    workflow_path: str = typer.Option(".github/workflows/ci.yml", help="Path to CI workflow file"),
):
    """Generate or manage CI workflow snippets."""
    try:
        generator = CISnippetGenerator()
        
        if check:
            typer.echo("Checking CI workflow drift...")
            matches, differences = generator.check_snippet()
            
            if not matches:
                for diff in differences:
                    typer.echo(f"Missing step: {diff}")
                raise typer.Exit(1)
            else:
                typer.echo("CI workflow matches canonical version")
        
        elif update:
            typer.echo("Updating CI workflow...")
            success = generator.update_snippet()
            
            if not success:
                typer.echo("Error updating CI workflow")
                raise typer.Exit(1)
            
            typer.echo("CI workflow updated successfully")
        
        else:
            # Print the canonical workflow
            typer.echo("Canonical CI Workflow:")
            typer.echo("=" * 80)
            typer.echo(generator.generate_snippet())
            typer.echo("=" * 80)
            
            summary = generator.get_workflow_summary()
            typer.echo(f"\nWorkflow Summary:")
            typer.echo(f"   Name: {summary['name']}")
            typer.echo(f"   Triggers: {', '.join(summary['triggers'])}")
            typer.echo(f"   Python versions: {', '.join(summary['python_versions'])}")
            typer.echo(f"   Integrity gates: {len(summary['integrity_gates'])}")
            typer.echo(f"   Hash: {summary['hash']}")
    
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
