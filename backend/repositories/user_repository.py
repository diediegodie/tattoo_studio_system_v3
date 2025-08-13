"""
User repository implementation.

Implements data access layer for User entities following
the Repository pattern and Dependency Inversion Principle.
"""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..models.user import User
from .base import BaseRepository
from ..utils.validation import EntityValidator, safe_entity_update, ValidationError
import logging

logger = logging.getLogger(__name__)


class UserRepository(BaseRepository[User, int]):
    """
    Repository for User entities.

    Implements all user-specific data access operations
    while following SOLID principles.
    """

    def __init__(self, session: Session):
        """
        Initialize user repository.

        Args:
            session: SQLAlchemy session
        """
        super().__init__(session, User)

    def get_by_id(self, id: int) -> Optional[User]:
        """
        Get user by ID.

        Args:
            id: User ID

        Returns:
            Optional[User]: User if found, None otherwise
        """
        try:
            return self.session.get(User, id)
        except Exception as e:
            logger.error(f"Error getting user by ID {id}: {e}")
            return None

    def get_all(self) -> List[User]:
        """
        Get all users.

        Returns:
            List[User]: All users
        """
        try:
            return list(self.session.scalars(select(User)))
        except Exception as e:
            logger.error(f"Error getting all users: {e}")
            return []

    def create(self, **kwargs) -> User:
        """
        Create new user.

        Args:
            **kwargs: User attributes

        Returns:
            User: Created user

        Raises:
            ValidationError: If required fields are missing
        """
        EntityValidator.validate_user_data(**kwargs)

        try:
            user = User(**kwargs)
            return self.save(user)
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            raise

    def update(self, entity: User, **kwargs) -> User:
        """
        Update existing user.

        Args:
            entity: User to update
            **kwargs: Fields to update

        Returns:
            User: Updated user
        """
        try:
            safe_entity_update(entity, **kwargs)

            return self.save(entity)
        except Exception as e:
            logger.error(f"Error updating user {entity.id}: {e}")
            raise

    def delete(self, entity: User) -> bool:
        """
        Delete user.

        Args:
            entity: User to delete

        Returns:
            bool: True if deleted successfully
        """
        try:
            self.session.delete(entity)
            self.session.flush()
            return True
        except Exception as e:
            logger.error(f"Error deleting user {entity.id}: {e}")
            return False

    def get_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email.

        Args:
            email: User email

        Returns:
            Optional[User]: User if found, None otherwise
        """
        try:
            stmt = select(User).where(User.email == email)
            return self.session.scalars(stmt).first()
        except Exception as e:
            logger.error(f"Error getting user by email {email}: {e}")
            return None

    def email_exists(self, email: str) -> bool:
        """
        Check if email exists.

        Args:
            email: Email to check

        Returns:
            bool: True if email exists
        """
        try:
            user = self.get_by_email(email)
            return user is not None
        except Exception as e:
            logger.error(f"Error checking email existence {email}: {e}")
            return False

    def update_jotform_api_key(self, user_id: int, api_key: str) -> bool:
        """
        Update user's JotForm API key.

        Args:
            user_id: User ID
            api_key: JotForm API key

        Returns:
            bool: True if updated successfully
        """
        try:
            user = self.get_by_id(user_id)
            if user:
                self.update(user, jotform_api_key=api_key)
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating JotForm API key for user {user_id}: {e}")
            return False
