"""Tests for approval API endpoints."""

import pytest
import json
import tempfile
import os
from fastapi.testclient import TestClient
from src.main import app
from src.core.db import get_db_manager, reset_db_manager
from src.core.models import TaskCreate, RunCreate

client = TestClient(app)


class TestApprovalAPI:
    """Test approval API endpoints."""

    def setup_method(self):
        """Set up test database with isolation."""
        # Set up temporary database
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")
        os.environ["DATABASE_URL"] = f"sqlite:///{self.db_path}"

        # Reset database manager
        reset_db_manager()
        self.db_manager = get_db_manager()
        self.db_manager.create_tables()

    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        reset_db_manager()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_list_runs(self):
        """Test listing runs with filters."""
        # Create test runs
        db_manager = get_db_manager()
        
        task = db_manager.create_task(
            TaskCreate(task_text="Test task", phase="test"),
            "Test prompt"
        )
        
        run1 = db_manager.create_run(
            RunCreate(task_id=task.id, status="tests_passed"),
            "Test run 1"
        )
        run2 = db_manager.create_run(
            RunCreate(task_id=task.id, status="awaiting_approval"),
            "Test run 2"
        )
        
        # Set integrity scores
        db_manager.update_run_integrity(run1.id, 85.0, "[]", "[]")
        db_manager.update_run_integrity(run2.id, 65.0, '[{"type": "test", "message": "test"}]', "[]")
        
        # Test list runs
        response = client.get("/runs")
        assert response.status_code == 200
        runs = response.json()
        assert len(runs) == 2
        
        # Test filter by status
        response = client.get("/runs?status=awaiting_approval")
        assert response.status_code == 200
        runs = response.json()
        assert len(runs) == 1
        assert runs[0]["status"] == "awaiting_approval"
        
        # Test filter by integrity minimum
        response = client.get("/runs?integrity_min=80")
        assert response.status_code == 200
        runs = response.json()
        assert len(runs) == 1
        assert runs[0]["integrity_score"] >= 80

    def test_get_run_detail(self):
        """Test getting run details."""
        db_manager = get_db_manager()
        
        task = db_manager.create_task(
            TaskCreate(task_text="Test task", phase="test"),
            "Test prompt"
        )
        
        run = db_manager.create_run(
            RunCreate(task_id=task.id, status="awaiting_approval"),
            "Test run"
        )
        
        db_manager.update_run_integrity(
            run.id, 
            75.0, 
            '[{"type": "coverage_drop", "message": "Coverage dropped", "severity": "warning"}]',
            '["Why did coverage drop?"]'
        )
        
        response = client.get(f"/runs/{run.id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == run.id
        assert data["status"] == "awaiting_approval"
        assert data["integrity"]["score"] == 75.0
        assert len(data["integrity"]["violations"]) == 1
        assert len(data["integrity"]["questions"]) == 1

    def test_approve_run(self):
        """Test approving a run."""
        db_manager = get_db_manager()
        
        task = db_manager.create_task(
            TaskCreate(task_text="Test task", phase="test"),
            "Test prompt"
        )
        
        run = db_manager.create_run(
            RunCreate(task_id=task.id, status="awaiting_approval"),
            "Test run"
        )
        
        db_manager.update_run_integrity(run.id, 75.0, "[]", "[]")
        
        response = client.post(
            f"/runs/{run.id}/approve",
            json={"justification": "Looks good"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["message"] == "Run approved and PR created successfully"
        assert data["status"] == "pr_opened"
        
        # Check database was updated
        updated_run = db_manager.get_run(run.id)
        assert updated_run.status == "pr_opened"

    def test_approve_run_low_integrity(self):
        """Test that low integrity runs cannot be approved."""
        db_manager = get_db_manager()
        
        task = db_manager.create_task(
            TaskCreate(task_text="Test task", phase="test"),
            "Test prompt"
        )
        
        run = db_manager.create_run(
            RunCreate(task_id=task.id, status="awaiting_approval"),
            "Test run"
        )
        
        db_manager.update_run_integrity(run.id, 50.0, "[]", "[]")
        
        response = client.post(
            f"/runs/{run.id}/approve",
            json={"justification": "Looks good"}
        )
        assert response.status_code == 400
        assert "Integrity score too low" in response.json()["detail"]

    def test_approve_run_wrong_status(self):
        """Test that only awaiting_approval runs can be approved."""
        db_manager = get_db_manager()
        
        task = db_manager.create_task(
            TaskCreate(task_text="Test task", phase="test"),
            "Test prompt"
        )
        
        run = db_manager.create_run(
            RunCreate(task_id=task.id, status="tests_passed"),
            "Test run"
        )
        
        db_manager.update_run_integrity(run.id, 85.0, "[]", "[]")
        
        response = client.post(
            f"/runs/{run.id}/approve",
            json={"justification": "Looks good"}
        )
        assert response.status_code == 400
        assert "not awaiting approval" in response.json()["detail"]

    def test_reject_run(self):
        """Test rejecting a run."""
        db_manager = get_db_manager()
        
        task = db_manager.create_task(
            TaskCreate(task_text="Test task", phase="test"),
            "Test prompt"
        )
        
        run = db_manager.create_run(
            RunCreate(task_id=task.id, status="awaiting_approval"),
            "Test run"
        )
        
        response = client.post(
            f"/runs/{run.id}/reject",
            json={"reason": "Not good enough", "regenerate": "true"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["message"] == "Run rejected successfully"
        assert data["status"] == "rejected"
        
        # Check database was updated
        updated_run = db_manager.get_run(run.id)
        assert updated_run.status == "rejected"

    def test_reject_run_wrong_status(self):
        """Test that only awaiting_approval runs can be rejected."""
        db_manager = get_db_manager()
        
        task = db_manager.create_task(
            TaskCreate(task_text="Test task", phase="test"),
            "Test prompt"
        )
        
        run = db_manager.create_run(
            RunCreate(task_id=task.id, status="tests_passed"),
            "Test run"
        )
        
        response = client.post(
            f"/runs/{run.id}/reject",
            json={"reason": "Not good enough"}
        )
        assert response.status_code == 400
        assert "not awaiting approval" in response.json()["detail"]

    def test_get_integrity_metrics(self):
        """Test getting integrity metrics."""
        db_manager = get_db_manager()
        
        task = db_manager.create_task(
            TaskCreate(task_text="Test task", phase="test"),
            "Test prompt"
        )
        
        # Create runs with different integrity scores
        run1 = db_manager.create_run(
            RunCreate(task_id=task.id, status="tests_passed"),
            "Test run 1"
        )
        run2 = db_manager.create_run(
            RunCreate(task_id=task.id, status="tests_passed"),
            "Test run 2"
        )
        
        db_manager.update_run_integrity(
            run1.id, 
            85.0, 
            '[{"type": "coverage_drop", "message": "test"}]',
            "[]"
        )
        db_manager.update_run_integrity(
            run2.id, 
            75.0, 
            '[{"type": "test_skips", "message": "test"}]',
            "[]"
        )
        
        response = client.get("/metrics/integrity")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_runs"] == 2
        assert data["avg_integrity_score"] == 80.0
        assert "coverage_drop" in data["violations_by_type"]
        assert "test_skips" in data["violations_by_type"]
        assert len(data["coverage_trend"]) == 2 