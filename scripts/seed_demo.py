#!/usr/bin/env python3
"""Seed script for demo data."""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.db import get_db_manager
from src.core.models import TaskCreate, RunCreate
from src.core.prompt_builder import prompt_builder
import json
from datetime import datetime, timedelta

def seed_demo_data():
    """Seed the database with demo data."""
    print("🌱 Seeding demo data...")
    
    db_manager = get_db_manager()
    
    # Create demo tasks
    demo_tasks = [
        {
            "task_text": "Add a new API endpoint for user authentication",
            "description": "Create a POST /auth/login endpoint with JWT token generation"
        },
        {
            "task_text": "Implement a caching layer for database queries",
            "description": "Add Redis caching for frequently accessed data"
        },
        {
            "task_text": "Create a dashboard component for analytics",
            "description": "Build a React component to display user activity metrics"
        },
        {
            "task_text": "Add input validation to the contact form",
            "description": "Implement client-side and server-side validation for the contact form"
        },
        {
            "task_text": "Optimize database queries for the user list page",
            "description": "Add proper indexing and query optimization for better performance"
        }
    ]
    
    created_tasks = []
    for task_data in demo_tasks:
        # Build prompt
        built_prompt = prompt_builder.build_task_prompt(task_data["task_text"])
        
        # Create task
        task_create = TaskCreate(
            task_text=task_data["task_text"],
            description=task_data["description"]
        )
        
        task = db_manager.create_task(task_create, built_prompt)
        created_tasks.append(task)
        print(f"✅ Created task: {task.task_text[:50]}...")
    
    # Create demo runs with different statuses
    run_statuses = [
        ("tests_passed", 85, []),
        ("awaiting_approval", 65, [{"type": "coverage", "message": "Coverage below 80%", "severity": "medium"}]),
        ("tests_failed", 45, [{"type": "test_failure", "message": "2 tests failed", "severity": "high"}]),
        ("running", None, []),
        ("pending", None, [])
    ]
    
    for i, (status, integrity_score, violations) in enumerate(run_statuses):
        if i < len(created_tasks):
            task = created_tasks[i]
            
            # Create run
            run_create = RunCreate(task_id=task.id, status=status)
            
            # Add some time variation
            created_at = datetime.now() - timedelta(hours=i*2)
            
            run = db_manager.create_run(
                run_create,
                logs=f"Demo run for task {task.id}",
                created_at=created_at
            )
            
            # Update integrity data if available
            if integrity_score is not None:
                violations_json = json.dumps(violations) if violations else "[]"
                db_manager.update_run_integrity(
                    run.id,
                    integrity_score,
                    violations_json,
                    "[]"  # No questions for demo
                )
            
            print(f"✅ Created run {run.id} with status: {status}")
    
    print(f"🎉 Seeded {len(created_tasks)} tasks and {len(run_statuses)} runs")
    print("Demo data ready! You can now explore the system.")

if __name__ == "__main__":
    seed_demo_data() 