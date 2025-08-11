"""
Client service layer implementing business logic.

This service follows SOLID principles by:
- Single Responsibility: Only handles client business logic
- Dependency Inversion: Depends on repository abstractions
- Open/Closed: Extensible without modifying existing code
"""


from typing import List, Optional
from sqlalchemy.orm import Session
from ..models.client import Client
from ..repositories.client_repository import ClientRepository
from ..repositories.user_repository import UserRepository
from ..schemas.client_schema import ClientSchema
import logging

logger = logging.getLogger(__name__)


class ClientService:
    """
    Service class for client business logic.

    Follows Dependency Inversion Principle by depending on
    repository abstractions rather than concrete implementations.
    """

    def __init__(self, session: Session):
        """
        Initialize client service.

        Args:
            session: SQLAlchemy session
        """
        self.session = session
        self.client_repo = ClientRepository(session)
        self.user_repo = UserRepository(session)

    def get_all_clients(self, user_id: int) -> List[Client]:
        """
        Get all clients for a user.

        Args:
            user_id: User ID

        Returns:
            List[Client]: User's clients
        """
        try:
            logger.info(f"Getting all clients for user {user_id}")
            return self.client_repo.get_by_user(user_id)
        except Exception as e:
            logger.error(f"Error getting clients for user {user_id}: {e}")
            return []

    def get_client_by_id(self, client_id: int, user_id: int) -> Optional[Client]:
        """
        Get client by ID if owned by user.

        Args:
            client_id: Client ID
            user_id: User ID

        Returns:
            Optional[Client]: Client if found and owned by user
        """
        try:
            logger.info(f"Getting client {client_id} for user {user_id}")
            return self.client_repo.get_by_id_and_user(client_id, user_id)
        except Exception as e:
            logger.error(f"Error getting client {client_id} for user {user_id}: {e}")
            return None


    def create_client(
        self, user_id: int, name: str, email: str, phone: str = "", notes: str = ""
    ) -> Optional[Client]:
        """
        Create a new client with centralized schema validation.
        """
        try:
            # Validate user exists
            user = self.user_repo.get_by_id(user_id)
            if not user:
                logger.warning(f"User {user_id} not found when creating client")
                return None

            # Centralized validation using Marshmallow schema
            schema = ClientSchema()
            input_data = {
                "name": name,
                "email": email,
                "phone": phone,
                # Add notes if you want to validate it as well
            }
            errors = schema.validate(input_data)
            if errors:
                logger.warning(f"Client validation failed: {errors}")
                return None

            logger.info(f"Creating client {name} for user {user_id}")
            client = self.client_repo.create(
                user_id=user_id, name=name, email=email, phone=phone, notes=notes
            )

            logger.info(f"Client {client.id} created successfully")
            return client

        except Exception as e:
            logger.error(f"Error creating client for user {user_id}: {e}")
            return None


    def update_client(
        self,
        client_id: int,
        user_id: int,
        name: str,
        email: str,
        phone: str = "",
        notes: str = "",
    ) -> Optional[Client]:
        """
        Update an existing client with centralized schema validation.
        """
        try:
            # Get client and verify ownership
            client = self.client_repo.get_by_id_and_user(client_id, user_id)
            if not client:
                logger.warning(f"Client {client_id} not found for user {user_id}")
                return None

            # Centralized validation using Marshmallow schema
            schema = ClientSchema()
            input_data = {
                "name": name,
                "email": email,
                "phone": phone,
                # Add notes if you want to validate it as well
            }
            errors = schema.validate(input_data)
            if errors:
                logger.warning(f"Client validation failed: {errors}")
                return None

            logger.info(f"Updating client {client_id} for user {user_id}")
            updated_client = self.client_repo.update(
                client, name=name, email=email, phone=phone, notes=notes
            )

            logger.info(f"Client {client_id} updated successfully")
            return updated_client

        except Exception as e:
            logger.error(f"Error updating client {client_id} for user {user_id}: {e}")
            return None

    def delete_client(self, client_id: int, user_id: int) -> bool:
        """
        Delete a client.

        Args:
            client_id: Client ID
            user_id: User ID

        Returns:
            bool: True if deleted successfully
        """
        try:
            logger.info(f"Deleting client {client_id} for user {user_id}")
            success = self.client_repo.delete_by_user(client_id, user_id)

            if success:
                logger.info(f"Client {client_id} deleted successfully")
            else:
                logger.warning(f"Client {client_id} not found for user {user_id}")

            return success

        except Exception as e:
            logger.error(f"Error deleting client {client_id} for user {user_id}: {e}")
            return False

    def search_clients(self, user_id: int, search_term: str) -> List[Client]:
        """
        Search clients by name or email.

        Args:
            user_id: User ID
            search_term: Search term

        Returns:
            List[Client]: Matching clients
        """
        try:
            logger.info(
                f"Searching clients for user {user_id} with term: {search_term}"
            )

            # Search by name
            name_results = self.client_repo.search_by_name(search_term, user_id)

            # Search by email
            email_results = self.client_repo.get_by_email(search_term, user_id)

            # Combine and deduplicate results
            all_results = list(
                {client.id: client for client in name_results + email_results}.values()
            )

            logger.info(f"Found {len(all_results)} clients matching '{search_term}'")
            return all_results

        except Exception as e:
            logger.error(f"Error searching clients for user {user_id}: {e}")
            return []
