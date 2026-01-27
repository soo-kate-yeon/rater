"""
SQLAlchemy models for TOEFL Speaking Rater.

This module provides all database models for the application:
- User: Authentication and user management
- Task: TOEFL Speaking questions and prompts (Deprecated - use Item)
- Job: Async scoring pipeline jobs
- JobArtifact: Intermediate pipeline results
- Report: Final user-facing feedback and scores
- Set: Problem sets containing multiple items
- Item: Individual speaking questions
- Stimulus: Source materials (reading, audio, image, direction)
- AnswerKey: Sample responses and scoring blueprints
"""

from .answer_key import AnswerKey
from .base import Base, BaseModel, TimestampMixin, UUIDMixin
from .enums import (
    AnswerKeyLevel,
    AnswerKeyType,
    Difficulty,
    StimulusKind,
    TopicCategory,
    TopicType,
)
from .item import Item
from .job import Job, JobStatus
from .job_artifact import JobArtifact
from .report import Report
from .set import Set
from .stimulus import Stimulus
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
    # New normalized models
    "Set",
    "Item",
    "Stimulus",
    "AnswerKey",
    # Task-related Enums
    "TaskType",
    "JobStatus",
    # New Enums
    "TopicType",
    "TopicCategory",
    "StimulusKind",
    "AnswerKeyType",
    "AnswerKeyLevel",
    "Difficulty",
]
