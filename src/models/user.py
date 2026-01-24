"""
User model for authentication and authorization.
"""
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel


class User(BaseModel):
    """
    User model for storing user credentials and metadata.

    Attributes:
        id: UUID primary key (inherited from BaseModel)
        email: Unique email address for login
        hashed_password: Bcrypt hashed password
        created_at: Account creation timestamp (inherited)
        updated_at: Last update timestamp (inherited)
    """

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # Relationships
    jobs: Mapped[list["Job"]] = relationship(  # noqa: F821
        "Job",
        back_populates="user",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, email={self.email!r})"
