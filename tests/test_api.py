"""Tests for API endpoints."""

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


class TestAPIEndpoints:
    """Test API endpoints."""

    @patch('src.main.get_db_manager')
    def test_get_runs_success(self, mock_db):
        """Test GET /runs endpoint success."""
        mock_runs = [
            MagicMock(
                id=1,
                task_id=1,
                status="completed",
                integrity_score=85.0,
                pr_number=123,
                pr_url="https://github.com/owner/repo/pull/123",
                pr_branch="feature-branch",
                approved_by="user1",
                role="operator"
            ),
            MagicMock(
                id=2,
                task_id=2,
                status="failed",
                integrity_score=45.0,
                pr_number=None,
                pr_url=None,
                pr_branch=None,
                approved_by=None,
                role="operator"
            )
        ]
        mock_db.return_value.list_runs.return_value = mock_runs
        
        response = client.get("/runs")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["id"] == 1
        assert data[0]["integrity_score"] == 85.0
        assert data[1]["id"] == 2
        assert data[1]["integrity_score"] == 45.0

    @patch('src.main.get_db_manager')
    def test_get_runs_with_filters(self, mock_db):
        """Test GET /runs endpoint with filters."""
        mock_runs = [
            MagicMock(
                id=1,
                task_id=1,
                status="completed",
                integrity_score=85.0,
                pr_number=123,
                pr_url="https://github.com/owner/repo/pull/123",
                pr_branch="feature-branch",
                approved_by="user1",
                role="operator"
            )
        ]
        mock_db.return_value.list_runs.return_value = mock_runs
        
        response = client.get("/runs?status=completed&integrity_min=80")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["status"] == "completed"

    @patch('src.main.get_db_manager')
    def test_get_run_success(self, mock_db):
        """Test GET /runs/{id} endpoint success."""
        mock_run = MagicMock(
            id=1,
            task_id=1,
            status="completed",
            integrity_score=85.0,
            integrity_violations='["coverage too low"]',
            integrity_questions='["Is this change safe?"]',
            pr_number=123,
            pr_url="https://github.com/owner/repo/pull/123",
            pr_branch="feature-branch",
            approved_by="user1",
            approved_at="2024-01-01T00:00:00Z",
            role="operator"
        )
        mock_db.return_value.get_run.return_value = mock_run
        
        response = client.get("/runs/1")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["integrity_score"] == 85.0
        assert data["pr_number"] == 123

    @patch('src.main.get_db_manager')
    def test_get_run_not_found(self, mock_db):
        """Test GET /runs/{id} endpoint not found."""
        mock_db.return_value.get_run.return_value = None
        
        response = client.get("/runs/999")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    @patch('src.main.get_db_manager')
    def test_approve_run_success(self, mock_db):
        """Test POST /runs/{id}/approve endpoint success."""
        mock_run = MagicMock(
            id=1,
            task_id=1,
            status="awaiting_approval",
            integrity_score=85.0
        )
        mock_db.return_value.get_run.return_value = mock_run
        mock_db.return_value.update_run.return_value = None
        
        response = client.post("/runs/1/approve", json={"justification": "Looks good"})
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pr_opened"
        assert data["message"] == "Run approved and PR created successfully"

    @patch('src.main.get_db_manager')
    def test_approve_run_not_found(self, mock_db):
        """Test POST /runs/{id}/approve endpoint not found."""
        mock_db.return_value.get_run.return_value = None
        
        response = client.post("/runs/999/approve", json={"justification": "test"})
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    @patch('src.main.get_db_manager')
    def test_reject_run_success(self, mock_db):
        """Test POST /runs/{id}/reject endpoint success."""
        mock_run = MagicMock(
            id=1,
            task_id=1,
            status="awaiting_approval",
            integrity_score=45.0
        )
        mock_db.return_value.get_run.return_value = mock_run
        mock_db.return_value.update_run.return_value = None
        
        response = client.post("/runs/1/reject", json={"reason": "Low integrity score"})
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "rejected"
        assert data["message"] == "Run rejected successfully"

    @patch('src.main.get_db_manager')
    def test_reject_run_not_found(self, mock_db):
        """Test POST /runs/{id}/reject endpoint not found."""
        mock_db.return_value.get_run.return_value = None
        
        response = client.post("/runs/999/reject", json={"reason": "Low integrity"})
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    @patch('src.main.get_db_manager')
    def test_get_metrics_integrity(self, mock_db):
        """Test GET /metrics/integrity endpoint."""
        mock_runs = [
            MagicMock(integrity_score=85.0, status="completed"),
            MagicMock(integrity_score=90.0, status="completed"),
            MagicMock(integrity_score=75.0, status="pending"),
            MagicMock(integrity_score=95.0, status="completed")
        ]
        mock_db.return_value.list_runs.return_value = mock_runs
        
        response = client.get("/metrics/integrity")
        
        assert response.status_code == 200
        data = response.json()
        assert "avg_integrity_score" in data
        assert "total_runs" in data
        assert "violations_by_type" in data
        assert "coverage_trend" in data

    def test_get_integrity_rules(self):
        """Test GET /integrity/rules endpoint."""
        response = client.get("/integrity/rules")
        
        assert response.status_code == 200
        data = response.json()
        assert "coverage_threshold" in data
        assert "diff_coverage_threshold" in data
        assert "allow_trivial_tests" in data
        assert "min_integrity_score" in data

    @patch('src.main.get_db_manager')
    def test_create_task_success(self, mock_db):
        """Test POST /tasks endpoint success."""
        mock_task = MagicMock(
            id=1,
            task_text="Test task",
            built_prompt="Test prompt",
            created_at="2024-01-01T00:00:00Z"
        )
        mock_db.return_value.create_task.return_value = mock_task
        
        response = client.post("/tasks", json={
            "task_text": "Test task",
            "built_prompt": "Test prompt"
        })
        
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == 1
        assert data["task_text"] == "Test task"

    @patch('src.main.get_db_manager')
    def test_list_tasks_success(self, mock_db):
        """Test GET /tasks endpoint success."""
        mock_tasks = [
            MagicMock(
                id=1,
                task_text="Task 1",
                built_prompt="Prompt 1",
                created_at="2024-01-01T00:00:00Z"
            ),
            MagicMock(
                id=2,
                task_text="Task 2",
                built_prompt="Prompt 2",
                created_at="2024-01-02T00:00:00Z"
            )
        ]
        mock_db.return_value.list_tasks.return_value = mock_tasks
        
        response = client.get("/tasks")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["id"] == 1
        assert data[1]["id"] == 2

    @patch('src.main.get_db_manager')
    def test_get_task_success(self, mock_db):
        """Test GET /tasks/{id} endpoint success."""
        mock_task = MagicMock(
            id=1,
            task_text="Test task",
            built_prompt="Test prompt",
            created_at="2024-01-01T00:00:00Z"
        )
        mock_db.return_value.get_task.return_value = mock_task
        
        response = client.get("/tasks/1")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["task_text"] == "Test task"

    @patch('src.main.get_db_manager')
    def test_get_task_not_found(self, mock_db):
        """Test GET /tasks/{id} endpoint not found."""
        mock_db.return_value.get_task.return_value = None
        
        response = client.get("/tasks/999")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    @patch('src.main.get_db_manager')
    def test_delete_task_success(self, mock_db):
        """Test DELETE /tasks/{id} endpoint success."""
        mock_db.return_value.delete_task.return_value = True
        
        response = client.delete("/tasks/1")
        
        assert response.status_code == 204

    @patch('src.main.get_db_manager')
    def test_delete_task_not_found(self, mock_db):
        """Test DELETE /tasks/{id} endpoint not found."""
        mock_db.return_value.delete_task.return_value = False
        
        response = client.delete("/tasks/999")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"] 