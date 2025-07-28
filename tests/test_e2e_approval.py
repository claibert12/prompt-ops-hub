"""End-to-end test for the approval flow."""

import pytest
import asyncio
import tempfile
import os
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from src.main import app
from src.core.db import get_db_manager, reset_db_manager
from src.core.models import TaskCreate, RunCreate
import json

client = TestClient(app)


class TestApprovalFlow:
    """Test the complete approval flow."""

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

    def test_approval_flow_e2e(self):
        """Test complete approval flow from task creation to approval."""
        
        # 1. Create a task
        task_data = {
            "task_text": "Add input validation to user registration",
            "description": "Implement comprehensive validation for user registration form"
        }
        
        response = client.post("/tasks", json=task_data)
        assert response.status_code == 201
        task = response.json()
        task_id = task["id"]
        
        # 2. Create a run by calling the run endpoint
        response = client.post(f"/tasks/{task_id}/run")
        if response.status_code != 200:
            print(f"Run endpoint failed with status {response.status_code}")
            print(f"Response: {response.text}")
        assert response.status_code == 200
        run_response = response.json()
        run_id = run_response["id"]
        
        # 3. Update the run to have low integrity score (needs approval)
        self.db_manager.update_run_status(run_id, "awaiting_approval", "Run completed, awaiting approval")
        self.db_manager.update_run_integrity(run_id, 75.0, '[{"type": "coverage_drop", "message": "Coverage dropped"}]', '["Why did coverage drop?"]')
        
        # 4. Get the list of runs
        response = client.get("/runs")
        assert response.status_code == 200
        runs = response.json()
        assert len(runs) > 0
        
        # Find our run
        run = next((r for r in runs if r["id"] == run_id), None)
        assert run is not None
        assert run["status"] == "awaiting_approval"
        
        # 5. Get run details
        response = client.get(f"/runs/{run_id}")
        assert response.status_code == 200
        run_detail = response.json()
        assert run_detail["task_id"] == task_id
        assert "integrity" in run_detail
        
        # 6. Approve the run
        approval_data = {
            "justification": "Code looks good, tests pass, ready for production"
        }
        
        response = client.post(f"/runs/{run_id}/approve", json=approval_data)
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "pr_opened"
        
        # 7. Verify run status was updated
        response = client.get(f"/runs/{run_id}")
        assert response.status_code == 200
        updated_run = response.json()
        assert updated_run["status"] == "pr_opened"

    def test_rejection_flow_e2e(self):
        """Test rejection flow."""
        
        # 1. Create a task
        task_data = {
            "task_text": "Fix memory leak in data processing",
            "description": "Identify and fix memory leak in data processing module"
        }
        
        response = client.post("/tasks", json=task_data)
        assert response.status_code == 201
        task = response.json()
        task_id = task["id"]
        
        # 2. Create a run
        response = client.post(f"/tasks/{task_id}/run")
        assert response.status_code == 200
        run_response = response.json()
        run_id = run_response["id"]
        
        # 3. Update the run to need approval
        self.db_manager.update_run_status(run_id, "awaiting_approval", "Run completed, awaiting approval")
        self.db_manager.update_run_integrity(run_id, 60.0, '[{"type": "test_skips", "message": "Tests skipped"}]', '["Why were tests skipped?"]')
        
        # 4. Reject the run
        rejection_data = {
            "reason": "Code quality issues need to be addressed",
            "regenerate": "true"
        }
        
        response = client.post(f"/runs/{run_id}/reject", json=rejection_data)
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "rejected"
        
        # 5. Verify run status was updated
        response = client.get(f"/runs/{run_id}")
        assert response.status_code == 200
        updated_run = response.json()
        assert updated_run["status"] == "rejected"

    def test_integrity_metrics_e2e(self):
        """Test integrity metrics endpoint."""
        
        # Create some test data
        task_data = {
            "task_text": "Add unit tests for authentication",
            "description": "Add comprehensive unit tests for authentication service"
        }
        
        response = client.post("/tasks", json=task_data)
        assert response.status_code == 201
        
        # Get integrity metrics
        response = client.get("/metrics/integrity")
        assert response.status_code == 200
        metrics = response.json()
        
        # Verify metrics structure
        assert "total_runs" in metrics
        assert "avg_integrity_score" in metrics
        assert "violations_by_type" in metrics
        assert "coverage_trend" in metrics
        
        # Verify data types
        assert isinstance(metrics["total_runs"], int)
        assert isinstance(metrics["avg_integrity_score"], (int, float))
        assert isinstance(metrics["violations_by_type"], dict)
        assert isinstance(metrics["coverage_trend"], list)

    def test_run_filtering_e2e(self):
        """Test run filtering functionality."""
        
        # Create multiple tasks and runs
        for i in range(3):
            task_data = {
                "task_text": f"Task {i+1}",
                "description": f"Description for task {i+1}"
            }
            response = client.post("/tasks", json=task_data)
            assert response.status_code == 201
        
        # Test filtering by status
        response = client.get("/runs?status=awaiting_approval")
        assert response.status_code == 200
        runs = response.json()
        # All runs should have the specified status
        for run in runs:
            assert run["status"] == "awaiting_approval"
        
        # Test filtering by minimum integrity score
        response = client.get("/runs?integrity_min=70")
        assert response.status_code == 200
        runs = response.json()
        # All runs should have integrity score >= 70
        for run in runs:
            if run["integrity_score"] is not None:
                assert run["integrity_score"] >= 70

    def test_error_handling_e2e(self):
        """Test error handling in approval flow."""
        
        # Try to approve a non-existent run
        response = client.post("/runs/99999/approve", json={"justification": "test"})
        assert response.status_code == 404
        
        # Try to approve a run that's not awaiting approval
        # First create a task and run
        task_data = {
            "task_text": "Test task",
            "description": "Test description"
        }
        response = client.post("/tasks", json=task_data)
        assert response.status_code == 201
        task = response.json()
        
        # Create a run
        response = client.post(f"/tasks/{task['id']}/run")
        assert response.status_code == 200
        run_response = response.json()
        run_id = run_response["id"]
        
        # Update run to have passed tests (not awaiting approval)
        self.db_manager.update_run_status(run_id, "tests_passed", "Tests passed")
        self.db_manager.update_run_integrity(run_id, 85.0, "[]", "[]")
        
        # Try to approve a run that's not awaiting approval
        response = client.post(f"/runs/{run_id}/approve", json={"justification": "test"})
        assert response.status_code == 400
        assert "not awaiting approval" in response.json()["detail"]
        
        # Try to approve a run with low integrity score
        self.db_manager.update_run_status(run_id, "awaiting_approval", "Awaiting approval")
        self.db_manager.update_run_integrity(run_id, 50.0, '[{"type": "coverage_drop", "message": "Coverage dropped"}]', "[]")
        
        response = client.post(f"/runs/{run_id}/approve", json={"justification": "test"})
        assert response.status_code == 400
        assert "Integrity score too low" in response.json()["detail"] 