"""
Base model and common mixins for SQLAlchemy models.
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, func
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import CHAR, TypeDecorator


class JSONType(TypeDecorator):
    """
    Platform-independent JSON type.
    Uses JSONB for PostgreSQL, JSON (stored as TEXT) for SQLite.
    """

    impl = JSON
    cache_ok = True


class GUID(TypeDecorator):
    """
    Platform-independent GUID type.
    Uses PostgreSQL's UUID type when available, otherwise uses CHAR(32).
    Stores as string without hyphens for SQLite compatibility.
    """

    impl = CHAR(32)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PostgreSQLUUID(as_uuid=True))
        else:
            return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value

        # Convert to UUID if it's a string
        if isinstance(value, str):
            try:
                value = uuid.UUID(value)
            except ValueError:
                # Already a valid UUID string without hyphens, add them back
                if len(value) == 32:
                    value = uuid.UUID(
                        f"{value[:8]}-{value[8:12]}-{value[12:16]}-{value[16:20]}-{value[20:]}"
                    )

        # For PostgreSQL, return as is (UUID object or string)
        if dialect.name == "postgresql":
            return value
        # For other databases (SQLite), return without hyphens
        else:
            return str(value).replace("-", "")

    def process_result_value(self, value, dialect):
        if value is None:
            return value

        # If already a UUID, return it
        if isinstance(value, uuid.UUID):
            return value

        # Convert string to UUID
        if isinstance(value, str):
            # SQLite stores without hyphens (32 chars)
            if len(value) == 32:
                value = f"{value[:8]}-{value[8:12]}-{value[12:16]}-{value[16:20]}-{value[20:]}"
            return uuid.UUID(value)

        return value


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
        GUID,
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
        attrs = ", ".join(f"{k}={v!r}" for k, v in self.dict().items() if not k.startswith("_"))
        return f"{self.__class__.__name__}({attrs})"
