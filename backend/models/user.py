"""
User model for authentication and user management.

This module defines the User SQLAlchemy model with proper type annotations
following SOLID principles.
"""

from sqlalchemy import Column, Integer, String, DateTime
from . import Base
from sqlalchemy.orm import relationship, Mapped, mapped_column
from passlib.hash import bcrypt
from typing import Optional, TYPE_CHECKING
import datetime

if TYPE_CHECKING:
    from .client import Client


class User(Base):
    """
    SQLAlchemy User model for Google OAuth authentication.

    Attributes:
        id (int): Primary key identifier
        name (str): User's display name
        email (str): User's email address (unique)
        password_hash (str): Hashed password (optional, used only for Google OAuth integration)
        created_at (datetime): Account creation timestamp
        jotform_api_key (Optional[str]): JotForm API key for integration
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    email: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    password_hash: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )  # Made optional since only Google login is used
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow
    )
    jotform_api_key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relationship to Client
    clients: Mapped[list["Client"]] = relationship("Client", back_populates="user")

    def set_password(self, password: str) -> None:
        """
        Set user password with hashing.

        Args:
            password: Plain text password to hash and store
        """
        self.password_hash = bcrypt.hash(password)

    def check_password(self, password: str) -> bool:
        """
        Verify password against stored hash.

        Args:
            password: Plain text password to verify

        Returns:
            bool: True if password matches, False otherwise
        """
        return bcrypt.verify(
            password,
            (
                self.password_hash
                if isinstance(self.password_hash, str)
                else str(self.password_hash)
            ),
        )

    def __repr__(self) -> str:
        """String representation of user."""
        return f"<User(id={self.id}, email='{self.email}', name='{self.name}')>"
