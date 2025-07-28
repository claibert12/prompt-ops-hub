"""Unit tests for agent worker."""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from src.agent.worker import AgentWorker
from src.core.models import Task


class TestAgentWorker:
    """Test cases for AgentWorker class."""

    def test_worker_initialization(self):
        """Test worker initialization."""
        worker = AgentWorker(poll_interval=60, max_retries=5)
        assert worker.poll_interval == 60
        assert worker.max_retries == 5
        assert worker.running is False
        assert worker.db_manager is not None

    @pytest.mark.asyncio
    async def test_signal_handler(self):
        """Test signal handler sets running to False."""
        worker = AgentWorker()
        worker.running = True
        
        # Simulate signal
        worker._signal_handler(2, None)  # SIGINT
        
        assert worker.running is False

    @pytest.mark.asyncio
    async def test_process_pending_tasks_no_tasks(self):
        """Test processing when no pending tasks exist."""
        worker = AgentWorker()
        
        # Mock database to return no tasks
        worker.db_manager.list_tasks = Mock(return_value=[])
        
        # Should not raise any exceptions
        await worker._process_pending_tasks()

    @pytest.mark.asyncio
    async def test_process_pending_tasks_with_tasks(self):
        """Test processing with pending tasks."""
        worker = AgentWorker()
        
        # Create mock task
        mock_task = Mock(spec=Task)
        mock_task.id = 1
        mock_task.task_text = "Test task"
        
        # Mock database to return tasks
        worker.db_manager.list_tasks = Mock(return_value=[mock_task])
        
        # Mock the process_task method
        worker._process_task = AsyncMock()
        
        await worker._process_pending_tasks()
        
        # Verify process_task was called
        worker._process_task.assert_called_once_with(mock_task)

    @pytest.mark.asyncio
    async def test_process_task_success(self):
        """Test successful task processing."""
        worker = AgentWorker()
        
        # Create mock task
        mock_task = Mock(spec=Task)
        mock_task.id = 1
        mock_task.task_text = "Test task"
        
        # Mock database operations
        worker.db_manager.update_task_status = Mock()
        
        # Mock regen loop to return success
        mock_result = Mock()
        mock_result.success = True
        mock_result.final_status = "tests_passed"
        mock_result.error_message = None
        
        with patch('src.agent.worker.regen_loop') as mock_regen:
            mock_regen.run_with_regen.return_value = mock_result
            
            await worker._process_task(mock_task)
            
            # Verify status was updated to running
            worker.db_manager.update_task_status.assert_called_with(
                1, "running", "Task picked up by agent"
            )

    @pytest.mark.asyncio
    async def test_process_task_failure(self):
        """Test task processing failure."""
        worker = AgentWorker()
        
        # Create mock task
        mock_task = Mock(spec=Task)
        mock_task.id = 1
        mock_task.task_text = "Test task"
        
        # Mock database operations
        worker.db_manager.update_task_status = Mock()
        
        # Mock regen loop to return failure
        mock_result = Mock()
        mock_result.success = False
        mock_result.final_status = "error"
        mock_result.error_message = "Test error"
        
        with patch('src.agent.worker.regen_loop') as mock_regen:
            mock_regen.run_with_regen.return_value = mock_result
            
            await worker._process_task(mock_task)
            
            # Verify status was updated to running (only call made for non-exception failures)
            worker.db_manager.update_task_status.assert_called_once_with(
                1, "running", "Task picked up by agent"
            )

    @pytest.mark.asyncio
    async def test_process_task_exception(self):
        """Test task processing with exception."""
        worker = AgentWorker()
        
        # Create mock task
        mock_task = Mock(spec=Task)
        mock_task.id = 1
        mock_task.task_text = "Test task"
        
        # Mock database operations
        worker.db_manager.update_task_status = Mock()
        
        # Mock regen loop to raise exception
        with patch('src.agent.worker.regen_loop') as mock_regen:
            mock_regen.run_with_regen.side_effect = Exception("Test exception")
            
            await worker._process_task(mock_task)
            
            # Verify error status was set
            worker.db_manager.update_task_status.assert_called_with(
                1, "error", "Agent processing error: Test exception"
            )

    @pytest.mark.asyncio
    async def test_start_and_shutdown(self):
        """Test worker start and shutdown."""
        worker = AgentWorker(poll_interval=0.1)  # Short interval for testing
        
        # Mock the process method
        worker._process_pending_tasks = AsyncMock()
        
        # Start worker in background
        task = asyncio.create_task(worker.start())
        
        # Let it run for a short time
        await asyncio.sleep(0.2)
        
        # Stop the worker
        worker.running = False
        
        # Wait for shutdown
        await task
        
        # Verify process was called
        assert worker._process_pending_tasks.called 