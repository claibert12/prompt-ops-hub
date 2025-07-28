#!/usr/bin/env python3
"""Automation agent worker for processing pending tasks."""

import asyncio
import signal
import sys
import time
import logging
from typing import Optional
from src.core.db import get_db_manager
from src.core.regen import regen_loop
from src.core.models import Task

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AgentWorker:
    """Worker that polls for pending tasks and executes them."""
    
    def __init__(self, poll_interval: int = 30, max_retries: int = 3):
        self.poll_interval = poll_interval
        self.max_retries = max_retries
        self.running = False
        self.db_manager = get_db_manager()
        
    async def start(self):
        """Start the worker loop."""
        logger.info("Starting agent worker...")
        self.running = True
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        try:
            while self.running:
                await self._process_pending_tasks()
                await asyncio.sleep(self.poll_interval)
        except KeyboardInterrupt:
            logger.info("Received interrupt signal, shutting down...")
        finally:
            await self._shutdown()
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, initiating shutdown...")
        self.running = False
    
    async def _shutdown(self):
        """Graceful shutdown."""
        logger.info("Agent worker shutdown complete.")
    
    async def _process_pending_tasks(self):
        """Process all pending tasks."""
        try:
            # Get pending tasks
            pending_tasks = self.db_manager.list_tasks(status_filter="pending")
            
            if not pending_tasks:
                logger.debug("No pending tasks found")
                return
            
            logger.info(f"Found {len(pending_tasks)} pending tasks")
            
            for task in pending_tasks:
                await self._process_task(task)
                
        except Exception as e:
            logger.error(f"Error processing pending tasks: {e}")
    
    async def _process_task(self, task: Task):
        """Process a single task."""
        logger.info(f"Processing task {task.id}: {task.task_text[:50]}...")
        
        try:
            # Update task status to running
            self.db_manager.update_task_status(task.id, "running", "Task picked up by agent")
            
            # Run the regeneration loop
            result = regen_loop.run_with_regen(task.id)
            
            if result.success:
                if result.final_status == "tests_passed":
                    logger.info(f"Task {task.id} completed successfully")
                elif result.final_status == "awaiting_approval":
                    logger.info(f"Task {task.id} awaiting human approval (integrity score too low)")
                else:
                    logger.warning(f"Task {task.id} completed with status: {result.final_status}")
            else:
                logger.error(f"Task {task.id} failed: {result.error_message}")
                
        except Exception as e:
            logger.error(f"Error processing task {task.id}: {e}")
            # Update task status to error
            self.db_manager.update_task_status(
                task.id, 
                "error", 
                f"Agent processing error: {str(e)}"
            )


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Prompt Ops Hub Agent Worker")
    parser.add_argument(
        "--poll-interval", 
        type=int, 
        default=30, 
        help="Polling interval in seconds (default: 30)"
    )
    parser.add_argument(
        "--max-retries", 
        type=int, 
        default=3, 
        help="Maximum retries per task (default: 3)"
    )
    
    args = parser.parse_args()
    
    worker = AgentWorker(
        poll_interval=args.poll_interval,
        max_retries=args.max_retries
    )
    
    await worker.start()


if __name__ == "__main__":
    asyncio.run(main()) 