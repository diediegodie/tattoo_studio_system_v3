"""
Client repository implementation.

Implements data access layer for Client entities following
the Repository pattern and Dependency Inversion Principle.
"""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..models.client import Client
from .base import UserOwnedRepository
from ..utils.validation import EntityValidator, safe_entity_update, ValidationError
import logging

logger = logging.getLogger(__name__)


class ClientRepository(UserOwnedRepository[Client, int]):
    """
    Repository for Client entities.

    Implements all client-specific data access operations
    while following SOLID principles.
    """

    def __init__(self, session: Session):
        """
        Initialize client repository.

        Args:
            session: SQLAlchemy session
        """
        super().__init__(session, Client)

    def get_by_id(self, id: int) -> Optional[Client]:
        """
        Get client by ID.

        Args:
            id: Client ID

        Returns:
            Optional[Client]: Client if found, None otherwise
        """
        try:
            return self.session.get(Client, id)
        except Exception as e:
            logger.error(f"Error getting client by ID {id}: {e}")
            return None

    def get_all(self) -> List[Client]:
        """
        Get all clients.

        Returns:
            List[Client]: All clients
        """
        try:
            return list(self.session.scalars(select(Client)))
        except Exception as e:
            logger.error(f"Error getting all clients: {e}")
            return []

    def get_by_user(self, user_id: int) -> List[Client]:
        """
        Get all clients owned by user.

        Args:
            user_id: User ID

        Returns:
            List[Client]: Clients owned by user
        """
        try:
            stmt = select(Client).where(Client.user_id == user_id)
            return list(self.session.scalars(stmt))
        except Exception as e:
            logger.error(f"Error getting clients for user {user_id}: {e}")
            return []

    def get_by_id_and_user(self, id: int, user_id: int) -> Optional[Client]:
        """
        Get client by ID if owned by user.

        Args:
            id: Client ID
            user_id: User ID

        Returns:
            Optional[Client]: Client if found and owned by user, None otherwise
        """
        try:
            stmt = select(Client).where(Client.id == id, Client.user_id == user_id)
            return self.session.scalars(stmt).first()
        except Exception as e:
            logger.error(f"Error getting client {id} for user {user_id}: {e}")
            return None

    def create(self, **kwargs) -> Client:
        """
        Create new client.

        Args:
            **kwargs: Client attributes

        Returns:
            Client: Created client

        Raises:
            ValidationError: If required fields are missing
        """
        EntityValidator.validate_client_data(**kwargs)

        try:
            client = Client(**kwargs)
            return self.save(client)
        except Exception as e:
            logger.error(f"Error creating client: {e}")
            raise

    def update(self, entity: Client, **kwargs) -> Client:
        """
        Update client.

        Args:
            entity: Client entity to update
            **kwargs: Fields to update

        Returns:
            Client: Updated client
        """
        try:
            safe_entity_update(entity, **kwargs)

            self.session.commit()
            logger.info(f"Client {entity.id} updated successfully")
            return entity
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error updating client {entity.id}: {e}")
            raise

    def delete(self, entity: Client) -> bool:
        """
        Delete client.

        Args:
            entity: Client entity to delete

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.session.delete(entity)
            self.session.commit()
            logger.info(f"Client {entity.id} deleted successfully")
            return True
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error deleting client {entity.id}: {e}")
            return False

    def delete_by_user(self, id: int, user_id: int) -> bool:
        """
        Delete client if owned by user.

        Args:
            id: Client ID
            user_id: User ID

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            client = self.get_by_id_and_user(id, user_id)
            if not client:
                return False

            self.session.delete(client)
            self.session.commit()
            logger.info(f"Client {id} deleted by user {user_id}")
            return True
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error deleting client {id} for user {user_id}: {e}")
            return False

    def get_by_email(self, email: str, user_id: Optional[int] = None) -> List[Client]:
        """
        Get clients by email.

        Args:
            email: Client email
            user_id: Optional user ID to filter by

        Returns:
            List[Client]: Clients with matching email
        """
        try:
            stmt = select(Client).where(Client.email == email)
            if user_id is not None:
                stmt = stmt.where(Client.user_id == user_id)
            return list(self.session.scalars(stmt))
        except Exception as e:
            logger.error(f"Error getting clients by email {email}: {e}")
            return []

    def search_by_name(
        self, name_pattern: str, user_id: Optional[int] = None
    ) -> List[Client]:
        """
        Search clients by name pattern.

        Args:
            name_pattern: Name pattern to search
            user_id: Optional user ID to filter by

        Returns:
            List[Client]: Clients matching name pattern
        """
        try:
            stmt = select(Client).where(Client.name.ilike(f"%{name_pattern}%"))
            if user_id is not None:
                stmt = stmt.where(Client.user_id == user_id)
            return list(self.session.scalars(stmt))
        except Exception as e:
            logger.error(f"Error searching clients by name {name_pattern}: {e}")
            return []
