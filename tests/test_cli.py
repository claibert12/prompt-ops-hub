"""Tests for CLI interface."""

import os
import tempfile

from typer.testing import CliRunner as TyperCliRunner

from src.cli import app
from src.core.db import reset_db_manager


class TestCLI:
    """Test cases for CLI interface."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = TyperCliRunner()

        # Create temporary directory for test database
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

        # Set environment variable for test database
        os.environ["DATABASE_URL"] = f"sqlite:///{self.temp_dir}/test.db"

        # Reset database manager to pick up new environment variable
        reset_db_manager()

    def teardown_method(self):
        """Clean up test fixtures."""
        # Clear environment variable
        if "DATABASE_URL" in os.environ:
            del os.environ["DATABASE_URL"]

        # Reset database manager to close connections
        reset_db_manager()

        os.chdir(self.original_cwd)
        import shutil
        try:
            shutil.rmtree(self.temp_dir)
        except PermissionError:
            # On Windows, database files might be locked
            # This is acceptable for tests
            pass

    def test_task_command_creates_prompt(self):
        """Test that task command creates and prints a prompt."""
        result = self.runner.invoke(app, ["task", "Implement a test feature"])

        assert result.exit_code == 0
        assert "GENERATED PROMPT" in result.stdout
        assert "Task: Implement a test feature" in result.stdout
        assert "Acceptance Criteria" in result.stdout
        assert "Self-Check" in result.stdout

    def test_task_command_saves_to_database(self):
        """Test that task command saves task to database."""
        result = self.runner.invoke(app, ["task", "Test task for database"])

        assert result.exit_code == 0
        assert "Task saved with ID:" in result.stdout
        assert "Created at:" in result.stdout

    def test_task_command_without_save(self):
        """Test task command without saving to database."""
        result = self.runner.invoke(
            app,
            ["task", "Test task without save", "--no-save"]
        )

        assert result.exit_code == 0
        assert "GENERATED PROMPT" in result.stdout
        assert "Task saved with ID:" not in result.stdout

    def test_list_command_empty(self):
        """Test list command with no tasks."""
        result = self.runner.invoke(app, ["list"])

        assert result.exit_code == 0
        assert "No tasks found" in result.stdout

    def test_list_command_with_tasks(self):
        """Test list command with existing tasks."""
        # First create a task
        self.runner.invoke(app, ["task", "First test task"])

        # Then list tasks
        result = self.runner.invoke(app, ["list"])

        assert result.exit_code == 0
        assert "Found 1 task(s)" in result.stdout
        assert "First test task" in result.stdout
        assert "ID: 1" in result.stdout

    def test_list_command_with_limit(self):
        """Test list command with limit parameter."""
        # Create multiple tasks
        self.runner.invoke(app, ["task", "Task 1"])
        self.runner.invoke(app, ["task", "Task 2"])
        self.runner.invoke(app, ["task", "Task 3"])

        # List with limit
        result = self.runner.invoke(app, ["list", "--limit", "2"])

        assert result.exit_code == 0
        assert "Found 2 task(s)" in result.stdout

    def test_list_command_show_prompt(self):
        """Test list command with show-prompt flag."""
        # Create a task
        self.runner.invoke(app, ["task", "Task with prompt"])

        # List with show-prompt
        result = self.runner.invoke(app, ["list", "--show-prompt"])

        assert result.exit_code == 0
        assert "Task with prompt" in result.stdout
        # Should show more than just the first 80 characters
        assert "Acceptance Criteria" in result.stdout

    def test_show_command(self):
        """Test show command for specific task."""
        # Create a task
        create_result = self.runner.invoke(app, ["task", "Task to show"])

        # Extract task ID from the output
        import re
        match = re.search(r'Task saved with ID: (\d+)', create_result.stdout)
        assert match, "Task ID not found in output"
        task_id = match.group(1)

        # Show the task
        result = self.runner.invoke(app, ["show", task_id])

        assert result.exit_code == 0
        assert f"Task ID: {task_id}" in result.stdout
        assert "Task to show" in result.stdout
        assert "FULL PROMPT" in result.stdout

    def test_show_command_not_found(self):
        """Test show command with non-existent task."""
        result = self.runner.invoke(app, ["show", "999"])

        assert result.exit_code == 1
        assert "Task with ID 999 not found" in result.stdout

    def test_delete_command(self):
        """Test delete command."""
        # Create a task
        create_result = self.runner.invoke(app, ["task", "Task to delete"])

        # Extract task ID from the output
        import re
        match = re.search(r'Task saved with ID: (\d+)', create_result.stdout)
        assert match, "Task ID not found in output"
        task_id = match.group(1)

        # Delete the task
        result = self.runner.invoke(app, ["delete", task_id])

        assert result.exit_code == 0
        assert f"Task {task_id} deleted successfully" in result.stdout

        # Verify task is gone
        list_result = self.runner.invoke(app, ["list"])
        assert "No tasks found" in list_result.stdout

    def test_delete_command_not_found(self):
        """Test delete command with non-existent task."""
        result = self.runner.invoke(app, ["delete", "999"])

        assert result.exit_code == 1
        assert "Task 999 not found" in result.stdout

    def test_init_command(self):
        """Test init command."""
        result = self.runner.invoke(app, ["init"])

        assert result.exit_code == 0
        assert "Database initialized successfully" in result.stdout

    def test_help_command(self):
        """Test help command."""
        result = self.runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "Prompt Ops Hub CLI" in result.stdout
        assert "task" in result.stdout
        assert "list" in result.stdout
        assert "show" in result.stdout
        assert "delete" in result.stdout
        assert "init" in result.stdout

    def test_task_command_help(self):
        """Test task command help."""
        result = self.runner.invoke(app, ["task", "--help"])

        assert result.exit_code == 0
        assert "Create a task and build a prompt with context" in result.stdout
        assert "TASK_DESCRIPTION" in result.stdout
        assert "--capability" in result.stdout
        assert "--save" in result.stdout
