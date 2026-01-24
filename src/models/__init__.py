"""
SQLAlchemy models for TOEFL Speaking Rater.

This module provides all database models for the application:
- User: Authentication and user management
- Task: TOEFL Speaking questions and prompts
- Job: Async scoring pipeline jobs
- JobArtifact: Intermediate pipeline results
- Report: Final user-facing feedback and scores
"""

from .base import Base, BaseModel, TimestampMixin, UUIDMixin
from .job import Job, JobStatus
from .job_artifact import JobArtifact
from .report import Report
from .task import Task, TaskType
from .user import User

__all__ = [
    # Base classes
    "Base",
    "BaseModel",
    "UUIDMixin",
    "TimestampMixin",
    # Models
    "User",
    "Task",
    "Job",
    "JobArtifact",
    "Report",
    # Enums
    "TaskType",
    "JobStatus",
]
