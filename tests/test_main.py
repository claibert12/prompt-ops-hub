"""Simple test for main.py to improve coverage."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from src.main import app


class TestMain:
    """Test main FastAPI app."""

    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)

    def test_root_endpoint(self):
        """Test root endpoint."""
        response = self.client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Prompt Ops Hub API"
        assert "version" in data

    def test_health_check(self):
        """Test health check endpoint."""
        response = self.client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    @patch('src.main.prompt_builder')
    def test_build_prompt(self, mock_prompt_builder):
        """Test build prompt endpoint."""
        mock_prompt_builder.build_task_prompt.return_value = "Built prompt"
        
        response = self.client.post("/prompts/build", data={"task_description": "Test task"})
        
        assert response.status_code == 200
        data = response.json()
        assert data["built_prompt"] == "Built prompt" 