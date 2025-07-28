"""Database models for Prompt Ops Hub."""

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Task(SQLModel, table=True):
    """Task model for storing prompt tasks."""

    id: int | None = Field(default=None, primary_key=True)
    task_text: str = Field(description="Original task description")
    built_prompt: str = Field(description="Generated prompt with context")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Task creation timestamp")

    class Config:
        """Pydantic config."""
        arbitrary_types_allowed = True


class Run(SQLModel, table=True):
    """Run model for storing task execution results."""

    id: int | None = Field(default=None, primary_key=True)
    task_id: int = Field(foreign_key="task.id", description="Associated task ID")
    status: str = Field(description="Execution status: pending|applied|tests_failed|pr_opened|error|needs_clarification")
    logs: str = Field(default="", description="Execution logs and output")
    loop_count: int = Field(default=0, description="Number of regeneration loops attempted")
    last_error: str = Field(default="", description="Last error message from failed attempt")
    needs_clarification: bool = Field(default=False, description="Whether task needs clarification")
    clarification_questions: str = Field(default="", description="JSON string of clarification questions")
    integrity_score: float = Field(default=100.0, description="Integrity score (0-100)")
    integrity_violations: str = Field(default="", description="JSON string of integrity violations")
    integrity_questions: str = Field(default="", description="JSON string of integrity questions")
    # PR metadata
    pr_url: Optional[str] = Field(default=None, description="GitHub PR URL")
    pr_number: Optional[int] = Field(default=None, description="GitHub PR number")
    pr_branch: Optional[str] = Field(default=None, description="GitHub PR branch")
    pr_state: Optional[str] = Field(default=None, description="PR state: opened|merged|closed")
    commit_sha: Optional[str] = Field(default=None, description="Git commit SHA")
    # Approval metadata
    approved_by: Optional[str] = Field(default=None, description="User who approved the run")
    approved_at: Optional[datetime] = Field(default=None, description="Approval timestamp")
    rejected_by: Optional[str] = Field(default=None, description="User who rejected the run")
    rejected_at: Optional[datetime] = Field(default=None, description="Rejection timestamp")
    rejection_reason: Optional[str] = Field(default=None, description="Reason for rejection")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Run creation timestamp")

    class Config:
        """Pydantic config."""
        arbitrary_types_allowed = True


class User(SQLModel, table=True):
    """User model for authentication and authorization."""

    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(unique=True, description="User email address")
    role: str = Field(default="operator", description="User role: operator|reviewer|admin")
    token_hash: str = Field(description="Hashed authentication token")
    is_active: bool = Field(default=True, description="Whether user account is active")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="User creation timestamp")

    class Config:
        """Pydantic config."""
        arbitrary_types_allowed = True


class TaskCreate(SQLModel):
    """Schema for creating a new task."""

    task_text: str = Field(description="Task description")


class TaskResponse(SQLModel):
    """Schema for task response."""

    id: int = Field(description="Task ID")
    task_text: str = Field(description="Original task description")
    built_prompt: str = Field(description="Generated prompt with context")
    created_at: datetime = Field(description="Task creation timestamp")


class RunCreate(SQLModel):
    """Schema for creating a new run."""

    task_id: int = Field(description="Associated task ID")
    status: str = Field(description="Execution status")


class RunResponse(SQLModel):
    """Schema for run response."""

    id: int = Field(description="Run ID")
    task_id: int = Field(description="Associated task ID")
    status: str = Field(description="Execution status")
    logs: str = Field(description="Execution logs and output")
    pr_url: Optional[str] = Field(default=None, description="GitHub PR URL")
    pr_state: Optional[str] = Field(default=None, description="PR state")
    commit_sha: Optional[str] = Field(default=None, description="Git commit SHA")
    created_at: datetime = Field(description="Run creation timestamp")


class UserCreate(SQLModel):
    """Schema for creating a new user."""

    email: str = Field(description="User email address")
    role: str = Field(default="operator", description="User role")
    token: str = Field(description="Authentication token")


class UserResponse(SQLModel):
    """Schema for user response."""

    id: int = Field(description="User ID")
    email: str = Field(description="User email address")
    role: str = Field(description="User role")
    is_active: bool = Field(description="Whether user account is active")
    created_at: datetime = Field(description="User creation timestamp")
