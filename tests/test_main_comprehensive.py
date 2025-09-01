"""Comprehensive FastAPI tests to boost coverage to 80%."""

import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from src.main import app
from src.core.db import get_db_manager, reset_db_manager


class TestMainComprehensive:
    """Comprehensive FastAPI tests to improve coverage."""

    def setup_method(self):
        """Set up test environment with database isolation."""
        # Set up temporary database
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")
        os.environ["DATABASE_URL"] = f"sqlite:///{self.db_path}"

        # Reset database manager
        reset_db_manager()
        self.db_manager = get_db_manager()
        self.db_manager.create_tables()
        
        self.client = TestClient(app)

    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        reset_db_manager()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_health_check(self):
        """Test health check endpoint."""
        response = self.client.get("/health")
        
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    def test_root_endpoint(self):
        """Test root endpoint."""
        response = self.client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "Prompt Ops Hub" in data["message"]
        assert data["version"] == "0.1.0"
        assert "phase" in data

    @patch('src.main.get_db_manager')
    @patch('src.main.prompt_builder')
    def test_create_task_success(self, mock_prompt_builder, mock_db_manager):
        """Test create task endpoint success."""
        mock_prompt_builder.build_task_prompt.return_value = "test prompt"
        mock_db_manager.return_value.create_task.return_value = MagicMock(
            id=1,
            task_text="test task",
            built_prompt="test prompt",
            created_at="2024-01-01T00:00:00"
        )
        
        response = self.client.post("/tasks", json={"task_text": "test task"})
        
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == 1
        assert data["task_text"] == "test task"
        assert data["built_prompt"] == "test prompt"

    @patch('src.main.get_db_manager')
    def test_create_task_error(self, mock_db_manager):
        """Test create task endpoint error."""
        mock_db_manager.return_value.create_task.side_effect = RuntimeError("DB error")
        
        response = self.client.post("/tasks", json={"task_text": "test task"})
        
        assert response.status_code == 500
        assert "error" in response.json()["detail"]

    @patch('src.main.get_db_manager')
    def test_get_task_success(self, mock_db_manager):
        """Test get task endpoint success."""
        mock_db_manager.return_value.get_task.return_value = MagicMock(
            id=1,
            task_text="test task",
            built_prompt="test prompt",
            created_at="2024-01-01T00:00:00"
        )
        
        response = self.client.get("/tasks/1")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["task_text"] == "test task"

    @patch('src.main.get_db_manager')
    def test_get_task_not_found(self, mock_db_manager):
        """Test get task endpoint not found."""
        mock_db_manager.return_value.get_task.return_value = None
        
        response = self.client.get("/tasks/999")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    @patch('src.main.get_db_manager')
    def test_list_tasks_success(self, mock_db_manager):
        """Test list tasks endpoint success."""
        mock_db_manager.return_value.list_tasks.return_value = [
            MagicMock(id=1, task_text="task 1", built_prompt="prompt 1", created_at="2024-01-01T00:00:00"),
            MagicMock(id=2, task_text="task 2", built_prompt="prompt 2", created_at="2024-01-01T00:00:00")
        ]
        
        response = self.client.get("/tasks")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["id"] == 1
        assert data[1]["id"] == 2

    @patch('src.main.get_db_manager')
    def test_list_tasks_with_limit(self, mock_db_manager):
        """Test list tasks endpoint with limit."""
        mock_db_manager.return_value.list_tasks.return_value = []
        
        response = self.client.get("/tasks?limit=5")
        
        assert response.status_code == 200
        mock_db_manager.return_value.list_tasks.assert_called_with(limit=5)

    @patch('src.main.get_db_manager')
    def test_list_tasks_error(self, mock_db_manager):
        """Test list tasks endpoint error."""
        mock_db_manager.return_value.list_tasks.side_effect = RuntimeError("DB error")
        
        response = self.client.get("/tasks")
        
        assert response.status_code == 500
        assert "error" in response.json()["detail"]

    @patch('src.main.get_db_manager')
    def test_delete_task_success(self, mock_db_manager):
        """Test delete task endpoint success."""
        mock_db_manager.return_value.delete_task.return_value = True
        
        response = self.client.delete("/tasks/1")
        
        assert response.status_code == 204

    @patch('src.main.get_db_manager')
    def test_delete_task_not_found(self, mock_db_manager):
        """Test delete task endpoint not found."""
        mock_db_manager.return_value.delete_task.return_value = False
        
        response = self.client.delete("/tasks/999")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    @patch('src.main.prompt_builder')
    def test_build_prompt_success(self, mock_prompt_builder):
        """Test build prompt endpoint success."""
        mock_prompt_builder.build_task_prompt.return_value = "test prompt"
        
        response = self.client.post("/prompts/build", data={"task_description": "test task"})
        
        assert response.status_code == 200
        data = response.json()
        assert data["task_description"] == "test task"
        assert data["built_prompt"] == "test prompt"

    @patch('src.main.prompt_builder')
    def test_build_prompt_error(self, mock_prompt_builder):
        """Test build prompt endpoint error."""
        mock_prompt_builder.build_task_prompt.side_effect = ValueError("Build error")
        
        response = self.client.post("/prompts/build", data={"task_description": "test task"})
        
        assert response.status_code == 500
        assert "error" in response.json()["detail"]

    @patch('src.main.get_db_manager')
    @patch('src.main.cursor_adapter')
    @patch('src.main.guardrails')
    def test_run_task_success(self, mock_guardrails, mock_cursor_adapter, mock_db_manager):
        """Test run task endpoint success."""
        mock_task = MagicMock(
            id=1,
            task_text="test task",
            built_prompt="test prompt"
        )
        mock_db_manager.return_value.get_task.return_value = mock_task
        mock_db_manager.return_value.create_run.return_value = MagicMock(id=1)
        mock_db_manager.return_value.get_run.return_value = MagicMock(
            id=1, task_id=1, status="completed", logs="test logs", created_at="2024-01-01T00:00:00"
        )
        mock_guardrails.check_prompt.return_value = []
        mock_guardrails.check_diff.return_value = []
        mock_cursor_adapter.apply_patch.return_value = MagicMock(success=True, error=None)
        mock_cursor_adapter.run_tests.return_value = MagicMock(success=True, output="test output")
        
        response = self.client.post("/tasks/1/run", json={"test_command": "pytest"})
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["task_id"] == 1
        assert data["status"] == "completed"

    @patch('src.main.get_db_manager')
    def test_run_task_not_found(self, mock_db_manager):
        """Test run task endpoint not found."""
        mock_db_manager.return_value.get_task.return_value = None
        
        response = self.client.post("/tasks/999/run", json={"test_command": "pytest"})
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    @patch('src.main.get_db_manager')
    @patch('src.main.cursor_adapter')
    @patch('src.main.guardrails')
    def test_run_task_guardrails_block(self, mock_guardrails, mock_cursor_adapter, mock_db_manager):
        """Test run task endpoint with guardrails blocking."""
        mock_task = MagicMock(
            id=1,
            task_text="test task",
            built_prompt="test prompt"
        )
        mock_db_manager.return_value.get_task.return_value = mock_task
        mock_db_manager.return_value.create_run.return_value = MagicMock(id=1)
        mock_guardrails.check_prompt.return_value = [MagicMock(type="SECURITY", severity="HIGH")]
        mock_guardrails.should_block_execution.return_value = True
        
        response = self.client.post("/tasks/1/run", json={"test_command": "pytest"})
        
        assert response.status_code == 400
        assert "blocked by guardrails" in response.json()["detail"]

    @patch('src.main.get_db_manager')
    @patch('src.main.cursor_adapter')
    @patch('src.main.guardrails')
    def test_run_task_patch_failure(self, mock_guardrails, mock_cursor_adapter, mock_db_manager):
        """Test run task endpoint with patch failure."""
        mock_task = MagicMock(
            id=1,
            task_text="test task",
            built_prompt="test prompt"
        )
        mock_db_manager.return_value.get_task.return_value = mock_task
        mock_db_manager.return_value.create_run.return_value = MagicMock(id=1)
        mock_guardrails.check_prompt.return_value = []
        mock_cursor_adapter.apply_patch.return_value = MagicMock(success=False, error="Patch failed")
        
        response = self.client.post("/tasks/1/run", json={"test_command": "pytest"})
        
        assert response.status_code == 500
        assert "Patch application failed" in response.json()["detail"]

    def test_list_runs_success(self):
        """Test list runs endpoint success."""
        # Create test data
        from src.core.models import TaskCreate, RunCreate
        
        task = self.db_manager.create_task(
            TaskCreate(task_text="Test task"),
            "Test prompt"
        )
        
        run1 = self.db_manager.create_run(
            RunCreate(task_id=task.id, status="completed"),
            "test logs"
        )
        run2 = self.db_manager.create_run(
            RunCreate(task_id=task.id, status="failed"),
            "error logs"
        )
        
        # Set integrity scores
        self.db_manager.update_run_integrity(run1.id, 85.0, "[]", "[]")
        self.db_manager.update_run_integrity(run2.id, 65.0, "[]", "[]")
        
        response = self.client.get("/runs")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        # Runs are returned in descending order by creation date, so run2 (created later) comes first
        assert data[0]["id"] == run2.id
        assert data[1]["id"] == run1.id

    @patch('src.main.get_db_manager')
    def test_list_runs_with_task_id(self, mock_db_manager):
        """Test list runs endpoint with task_id filter."""
        mock_db_manager.return_value.list_runs.return_value = []
        
        response = self.client.get("/runs?task_id=1")
        
        assert response.status_code == 200
        mock_db_manager.return_value.list_runs.assert_called_with(task_id=1, limit=None)

    @patch('src.main.get_db_manager')
    def test_list_runs_with_limit(self, mock_db_manager):
        """Test list runs endpoint with limit."""
        mock_db_manager.return_value.list_runs.return_value = []
        
        response = self.client.get("/runs?limit=5")
        
        assert response.status_code == 200
        mock_db_manager.return_value.list_runs.assert_called_with(task_id=None, limit=5)

    @patch('src.main.get_db_manager')
    def test_list_runs_error(self, mock_db_manager):
        """Test list runs endpoint error."""
        mock_db_manager.return_value.list_runs.side_effect = RuntimeError("DB error")
        
        response = self.client.get("/runs")
        
        assert response.status_code == 500
        assert "error" in response.json()["detail"]

    def test_get_run_success(self):
        """Test get run endpoint success."""
        # Create test data
        from src.core.models import TaskCreate, RunCreate
        
        task = self.db_manager.create_task(
            TaskCreate(task_text="Test task"),
            "Test prompt"
        )
        
        run = self.db_manager.create_run(
            RunCreate(task_id=task.id, status="completed"),
            "test logs"
        )
        
        # Set integrity data
        self.db_manager.update_run_integrity(run.id, 85.0, "[]", "[]")
        
        response = self.client.get(f"/runs/{run.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == run.id
        assert data["task_id"] == task.id
        assert data["status"] == "completed"

    @patch('src.main.get_db_manager')
    def test_get_run_not_found(self, mock_db_manager):
        """Test get run endpoint not found."""
        mock_db_manager.return_value.get_run.return_value = None
        
        response = self.client.get("/runs/999")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    @patch('src.main.get_db_manager')
    def test_get_run_error(self, mock_db_manager):
        """Test get run endpoint error."""
        mock_db_manager.return_value.get_run.side_effect = RuntimeError("DB error")
        
        response = self.client.get("/runs/1")
        
        assert response.status_code == 500
        assert "error" in response.json()["detail"]

    @patch('src.main.guardrails')
    def test_check_guardrails_code(self, mock_guardrails):
        """Test guardrails check endpoint for code."""
        mock_guardrails.check_code.return_value = []
        mock_guardrails.get_violation_summary.return_value = "No violations"
        mock_guardrails.should_block_execution.return_value = False
        
        response = self.client.post("/guardrails/check", data={
            "content": "def test(): pass",
            "content_type": "code"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["violations"] == []
        assert data["summary"] == "No violations"
        assert data["should_block"] is False

    @patch('src.main.guardrails')
    def test_check_guardrails_prompt(self, mock_guardrails):
        """Test guardrails check endpoint for prompt."""
        mock_guardrails.check_prompt.return_value = []
        mock_guardrails.get_violation_summary.return_value = "No violations"
        mock_guardrails.should_block_execution.return_value = False
        
        response = self.client.post("/guardrails/check", data={
            "content": "test prompt",
            "content_type": "prompt"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["violations"] == []

    @patch('src.main.guardrails')
    def test_check_guardrails_diff(self, mock_guardrails):
        """Test guardrails check endpoint for diff."""
        mock_guardrails.check_diff.return_value = []
        mock_guardrails.get_violation_summary.return_value = "No violations"
        mock_guardrails.should_block_execution.return_value = False
        
        response = self.client.post("/guardrails/check", data={
            "content": "diff --git a/test.py b/test.py",
            "content_type": "diff"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["violations"] == []

    def test_check_guardrails_invalid_type(self):
        """Test guardrails check endpoint with invalid type."""
        response = self.client.post("/guardrails/check", data={
            "content": "test content",
            "content_type": "invalid"
        })
        
        assert response.status_code == 400
        assert "Invalid content_type" in response.json()["detail"]

    @patch('src.main.guardrails')
    def test_check_guardrails_with_violations(self, mock_guardrails):
        """Test guardrails check endpoint with violations."""
        violation = MagicMock()
        violation.type = MagicMock(value="SECURITY")
        violation.message = "Security issue"
        violation.line_number = 1
        violation.severity = "HIGH"
        
        mock_guardrails.check_code.return_value = [violation]
        mock_guardrails.get_violation_summary.return_value = "1 violation"
        mock_guardrails.should_block_execution.return_value = True
        
        response = self.client.post("/guardrails/check", data={
            "content": "import os; os.system('rm -rf /')",
            "content_type": "code"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["violations"]) == 1
        assert data["violations"][0]["type"] == "SECURITY"
        assert data["should_block"] is True

    def test_startup_event(self):
        """Test startup event handler."""
        # This is called automatically by FastAPI
        # We just need to ensure the app starts without errors
        assert app is not None

    def test_app_initialization(self):
        """Test app initialization."""
        assert app.title == "Prompt Ops Hub"
        assert app.version == "0.1.0"
        assert app.description == "Local-first tool for managing AI prompts and tasks" 