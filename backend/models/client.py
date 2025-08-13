"""
Client model for customer management.

This module defines the Client SQLAlchemy model following SOLID principles.
"""

from sqlalchemy import String, Text, ForeignKey, DateTime, Integer
from sqlalchemy.orm import relationship, Mapped, mapped_column
from . import Base
from typing import Optional, List, TYPE_CHECKING
import datetime

if TYPE_CHECKING:
    from .user import User
    from .session import Session


class Client(Base):
    """
    SQLAlchemy Client model for customer management.

    Attributes:
        id (int): Primary key identifier
        user_id (int): Foreign key to User who owns this client
        name (str): Client's full name
        email (Optional[str]): Client's email address
        phone (Optional[str]): Client's phone number
        notes (Optional[str]): Additional notes about the client
        created_at (datetime): Record creation timestamp
    """

    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow
    )

    # Relationship to User
    user: Mapped["User"] = relationship("User", back_populates="clients")
    # Relationship to Session (as client)
    sessions_as_client: Mapped[List["Session"]] = relationship(
        "Session", back_populates="client", foreign_keys="Session.client_id"
    )

    def __repr__(self) -> str:
        """String representation of client."""
        return f"<Client(id={self.id}, name='{self.name}', email='{self.email}')>"

    def to_dict(self) -> dict:
        """
        Convert client to dictionary.

        Returns:
            dict: Client data as dictionary
        """
        try:
            created_at_str = self.created_at.isoformat()
        except (AttributeError, TypeError):
            created_at_str = None

        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "notes": self.notes,
            "created_at": created_at_str,
        }
