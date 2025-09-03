"""Database operations for Prompt Ops Hub."""

import os
import hashlib

from sqlmodel import Session, SQLModel, create_engine, select

from .models import Run, RunCreate, Task, TaskCreate, User, UserCreate


class DatabaseManager:
    """Manages database operations."""

    def __init__(self, database_url: str | None = None):
        """Initialize database manager.
        
        Args:
            database_url: SQLite database URL. Defaults to sqlite:///./prompt_ops.db
        """
        if database_url is None:
            database_url = os.getenv("DATABASE_URL", "sqlite:///./prompt_ops.db")

        self.engine = create_engine(
            database_url,
            echo=False,  # Set to True for SQL debugging
            connect_args={"check_same_thread": False} if "sqlite" in database_url else {}
        )

    def create_tables(self):
        """Create all database tables."""
        SQLModel.metadata.create_all(self.engine)

    def get_session(self) -> Session:
        """Get database session.
        
        Returns:
            Database session
        """
        return Session(self.engine)

    def create_task(self, task_create: TaskCreate, built_prompt: str) -> Task:
        """Create a new task.
        
        Args:
            task_create: Task creation data
            built_prompt: Generated prompt with context
            
        Returns:
            Created task
        """
        task = Task(
            task_text=task_create.task_text,
            built_prompt=built_prompt
        )

        with self.get_session() as session:
            session.add(task)
            session.commit()
            session.refresh(task)
            return task

    def get_task(self, task_id: int) -> Task | None:
        """Get task by ID.
        
        Args:
            task_id: Task ID
            
        Returns:
            Task if found, None otherwise
        """
        with self.get_session() as session:
            statement = select(Task).where(Task.id == task_id)
            return session.exec(statement).first()

    def list_tasks(self, limit: int | None = None) -> list[Task]:
        """List all tasks.
        
        Args:
            limit: Maximum number of tasks to return
            
        Returns:
            List of tasks
        """
        with self.get_session() as session:
            statement = select(Task).order_by(Task.created_at.desc())
            if limit:
                statement = statement.limit(limit)
            return session.exec(statement).all()

    def delete_task(self, task_id: int) -> bool:
        """Delete a task.
        
        Args:
            task_id: Task ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        with self.get_session() as session:
            task = session.get(Task, task_id)
            if task:
                session.delete(task)
                session.commit()
                return True
            return False

    def create_run(self, run_create: RunCreate, logs: str = "", loop_count: int = 0,
                   last_error: str = "", needs_clarification: bool = False,
                   clarification_questions: str = "") -> Run:
        """Create a new run.
        
        Args:
            run_create: Run creation data
            logs: Execution logs
            loop_count: Number of regeneration loops
            last_error: Last error message
            needs_clarification: Whether task needs clarification
            clarification_questions: JSON string of clarification questions
            
        Returns:
            Created run
        """
        run = Run(
            task_id=run_create.task_id,
            status=run_create.status,
            logs=logs,
            loop_count=loop_count,
            last_error=last_error,
            needs_clarification=needs_clarification,
            clarification_questions=clarification_questions
        )

        with self.get_session() as session:
            session.add(run)
            session.commit()
            session.refresh(run)
            return run

    def get_run(self, run_id: int) -> Run | None:
        """Get run by ID.
        
        Args:
            run_id: Run ID
            
        Returns:
            Run if found, None otherwise
        """
        with self.get_session() as session:
            statement = select(Run).where(Run.id == run_id)
            return session.exec(statement).first()

    def list_runs(self, task_id: int | None = None, limit: int | None = None) -> list[Run]:
        """List runs, optionally filtered by task ID.
        
        Args:
            task_id: Filter by task ID (optional)
            limit: Maximum number of runs to return
            
        Returns:
            List of runs
        """
        with self.get_session() as session:
            if task_id:
                statement = select(Run).where(Run.task_id == task_id).order_by(Run.created_at.desc())
            else:
                statement = select(Run).order_by(Run.created_at.desc())

            if limit:
                statement = statement.limit(limit)
            return session.exec(statement).all()

    def update_run_status(self, run_id: int, status: str, logs: str = "") -> Run | None:
        """Update run status and logs.
        
        Args:
            run_id: Run ID to update
            status: New status
            logs: Additional logs to append
            
        Returns:
            Updated run if found, None otherwise
        """
        with self.get_session() as session:
            run = session.get(Run, run_id)
            if run:
                run.status = status
                if logs:
                    run.logs += f"\n{logs}"
                session.commit()
                session.refresh(run)
                return run
            return None

    def update_run_integrity(self, run_id: int, integrity_score: float, integrity_violations: str, integrity_questions: str) -> Run | None:
        """Update run integrity data.
        
        Args:
            run_id: Run ID to update
            integrity_score: Integrity score (0-100)
            integrity_violations: JSON string of integrity violations
            integrity_questions: JSON string of integrity questions
            
        Returns:
            Updated run if found, None otherwise
        """
        with self.get_session() as session:
            run = session.get(Run, run_id)
            if run:
                run.integrity_score = integrity_score
                run.integrity_violations = integrity_violations
                run.integrity_questions = integrity_questions
                session.commit()
                session.refresh(run)
                return run
            return None
    
    def update_run_pr_metadata(self, run_id: int, pr_url: str = None, pr_state: str = None, commit_sha: str = None) -> Run | None:
        """Update run PR metadata.
        
        Args:
            run_id: Run ID to update
            pr_url: GitHub PR URL
            pr_state: PR state (opened|merged|closed)
            commit_sha: Git commit SHA
            
        Returns:
            Updated run if found, None otherwise
        """
        with self.get_session() as session:
            run = session.get(Run, run_id)
            if run:
                if pr_url is not None:
                    run.pr_url = pr_url
                if pr_state is not None:
                    run.pr_state = pr_state
                if commit_sha is not None:
                    run.commit_sha = commit_sha
                session.commit()
                session.refresh(run)
                return run
            return None

    def update_run(self, run_id: int, run_data: Run) -> Run | None:
        """Update run with new data.
        
        Args:
            run_id: Run ID to update
            run_data: Run object with updated fields
            
        Returns:
            Updated run if found, None otherwise
        """
        with self.get_session() as session:
            run = session.get(Run, run_id)
            if run:
                # Update all fields from run_data
                for field, value in run_data.dict(exclude={'id'}).items():
                    if hasattr(run, field):
                        setattr(run, field, value)
                session.commit()
                session.refresh(run)
                return run
            return None

    def delete_run(self, run_id: int) -> bool:
        """Delete a run.
        
        Args:
            run_id: Run ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        with self.get_session() as session:
            run = session.get(Run, run_id)
            if run:
                session.delete(run)
                session.commit()
                return True
            return False

    def clear_all_data(self):
        """Clear all data from the database (for testing)."""
        with self.get_session() as session:
            session.query(Run).delete()
            session.query(Task).delete()
            session.query(User).delete()
            session.commit()
    
    # User management methods
    def create_user(self, user_create: UserCreate) -> User:
        """Create a new user.
        
        Args:
            user_create: User creation data
            
        Returns:
            Created user
        """
        # Hash the token
        token_hash = hashlib.sha256(user_create.token.encode()).hexdigest()
        
        user = User(
            email=user_create.email,
            role=user_create.role,
            token_hash=token_hash
        )

        with self.get_session() as session:
            session.add(user)
            session.commit()
            session.refresh(user)
            return user
    
    def get_user_by_token(self, token: str) -> User | None:
        """Get user by authentication token.
        
        Args:
            token: Authentication token
            
        Returns:
            User if found, None otherwise
        """
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        with self.get_session() as session:
            statement = select(User).where(
                User.token_hash == token_hash,
                User.is_active == True
            )
            return session.exec(statement).first()
    
    def get_user_by_email(self, email: str) -> User | None:
        """Get user by email address.
        
        Args:
            email: User email address
            
        Returns:
            User if found, None otherwise
        """
        with self.get_session() as session:
            statement = select(User).where(User.email == email)
            return session.exec(statement).first()
    
    def list_users(self, limit: int | None = None) -> list[User]:
        """List all users.
        
        Args:
            limit: Maximum number of users to return
            
        Returns:
            List of users
        """
        with self.get_session() as session:
            statement = select(User).order_by(User.created_at.desc())
            if limit:
                statement = statement.limit(limit)
            return session.exec(statement).all()
    
    def update_user_role(self, user_id: int, role: str) -> User | None:
        """Update user role.
        
        Args:
            user_id: User ID to update
            role: New role (operator|reviewer|admin)
            
        Returns:
            Updated user if found, None otherwise
        """
        with self.get_session() as session:
            user = session.get(User, user_id)
            if user:
                user.role = role
                session.commit()
                session.refresh(user)
                return user
            return None
    
    def deactivate_user(self, user_id: int) -> bool:
        """Deactivate a user.
        
        Args:
            user_id: User ID to deactivate
            
        Returns:
            True if deactivated, False if not found
        """
        with self.get_session() as session:
            user = session.get(User, user_id)
            if user:
                user.is_active = False
                session.commit()
                return True
            return False


def get_db_manager() -> DatabaseManager:
    """Create a new database manager instance.

    This avoids module-level globals to ensure thread safety when used in
    web applications. Each caller receives an isolated manager that can
    create sessions as needed.
    """
    return DatabaseManager()


def reset_db_manager():
    """Compatibility function for previous API; no-op now."""
    return None
