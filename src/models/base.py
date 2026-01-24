"""
Base model and common mixins for SQLAlchemy models.
"""
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """
    SQLAlchemy declarative base for all models.
    """

    pass


class UUIDMixin:
    """
    Mixin that provides UUID primary key.
    """

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )


class TimestampMixin:
    """
    Mixin that provides created_at and updated_at timestamp fields.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class BaseModel(Base, UUIDMixin, TimestampMixin):
    """
    Base model that combines Base, UUIDMixin, and TimestampMixin.
    Abstract class for common model patterns.
    """

    __abstract__ = True

    def dict(self) -> dict[str, Any]:
        """
        Convert model instance to dictionary.
        """
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def __repr__(self) -> str:
        """
        String representation of the model.
        """
        attrs = ", ".join(
            f"{k}={v!r}" for k, v in self.dict().items() if not k.startswith("_")
        )
        return f"{self.__class__.__name__}({attrs})"
