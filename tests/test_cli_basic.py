"""Basic CLI tests to boost coverage to 80%."""

import pytest
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner
from src.cli import app


class TestCLIBasic:
    """Basic CLI tests to improve coverage."""

    def setup_method(self):
        """Set up CLI runner."""
        self.runner = CliRunner()

    def test_cli_help(self):
        """Test CLI help command."""
        result = self.runner.invoke(app, ["--help"])
        
        assert result.exit_code == 0
        assert "Usage" in result.stdout

    @patch('src.cli.get_db_manager')
    def test_cli_init(self, mock_db):
        """Test CLI init command."""
        mock_db.return_value.create_tables.return_value = None
        
        result = self.runner.invoke(app, ["init"])
        
        assert result.exit_code == 0
        assert "Database initialized" in result.stdout

    @patch('src.cli.prompt_builder')
    def test_cli_task(self, mock_prompt_builder):
        """Test CLI task command."""
        mock_prompt_builder.build_task_prompt.return_value = "Built prompt"
        
        result = self.runner.invoke(app, ["task", "Test task description"])
        
        assert result.exit_code == 0
        assert "Built prompt" in result.stdout

    @patch('src.cli.get_db_manager')
    def test_cli_list(self, mock_db):
        """Test CLI list command."""
        mock_db.return_value.create_tables.return_value = None
        mock_db.return_value.list_tasks.return_value = []
        
        result = self.runner.invoke(app, ["list"])
        
        assert result.exit_code == 0
        assert "No tasks found" in result.stdout

    @patch('src.cli.get_db_manager')
    def test_cli_show(self, mock_db):
        """Test CLI show command."""
        mock_task = MagicMock(
            id=1,
            task_text="Test task",
            built_prompt="Test prompt",
            created_at="2024-01-01T00:00:00"
        )
        mock_db.return_value.get_task.return_value = mock_task
        
        result = self.runner.invoke(app, ["show", "1"])
        
        assert result.exit_code == 0
        assert "Test task" in result.stdout

    @patch('src.cli.get_db_manager')
    def test_cli_delete(self, mock_db):
        """Test CLI delete command."""
        mock_db.return_value.delete_task.return_value = True
        
        result = self.runner.invoke(app, ["delete", "1"])
        
        assert result.exit_code == 0
        assert "deleted" in result.stdout

    @patch('src.cli.spec_expander')
    def test_cli_expand(self, mock_expander):
        """Test CLI expand command."""
        mock_expander.expand_task.return_value = MagicMock(
            original_goal="Test goal",
            acceptance_criteria=["test"],
            edge_cases=["test"],
            rollback_notes=["test"]
        )
        
        result = self.runner.invoke(app, ["expand", "Test goal"])
        
        assert result.exit_code == 0
        assert "Test goal" in result.stdout

    def test_cli_invalid_command(self):
        """Test CLI invalid command."""
        result = self.runner.invoke(app, ["invalid"])
        
        assert result.exit_code == 2

    def test_cli_missing_argument(self):
        """Test CLI missing argument."""
        result = self.runner.invoke(app, ["task"])
        
        assert result.exit_code == 2

    def test_cli_extra_argument(self):
        """Test CLI extra argument."""
        result = self.runner.invoke(app, ["init", "extra"])
        
        assert result.exit_code == 2 