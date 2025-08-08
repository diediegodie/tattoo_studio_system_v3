"""
Repository factory utilities.

Provides centralized repository creation with dependency injection,
eliminating code duplication across the application.
"""

from typing import Dict, Type
from sqlalchemy.orm import Session
from .base import BaseRepository
from .client_repository import ClientRepository
from .user_repository import UserRepository
from ..models.client import Client
from ..models.user import User


class RepositoryFactory:
    """
    Factory for creating repository instances with dependency injection.

    Follows Single Responsibility and Dependency Inversion principles
    by centralizing repository creation logic.
    """

    _repository_mapping: Dict[Type, Type[BaseRepository]] = {
        Client: ClientRepository,
        User: UserRepository,
    }

    @classmethod
    def create_repository(cls, model_class: Type, session: Session) -> BaseRepository:
        """
        Create repository instance for given model class.

        Args:
            model_class: Model class to create repository for
            session: Database session

        Returns:
            BaseRepository: Repository instance

        Raises:
            ValueError: If no repository found for model class
        """
        if model_class not in cls._repository_mapping:
            raise ValueError(f"No repository found for model: {model_class.__name__}")

        repository_class = cls._repository_mapping[model_class]
        # Repository classes only need session parameter
        return repository_class(session)

    @classmethod
    def create_client_repository(cls, session: Session) -> ClientRepository:
        """Create client repository instance."""
        return ClientRepository(session)

    @classmethod
    def create_user_repository(cls, session: Session) -> UserRepository:
        """Create user repository instance."""
        return UserRepository(session)


def create_repository_container(session: Session) -> Dict[str, BaseRepository]:
    """
    Create a container with all repository instances.

    Args:
        session: Database session

    Returns:
        Dict[str, BaseRepository]: Repository container
    """
    return {
        "client_repository": RepositoryFactory.create_client_repository(session),
        "user_repository": RepositoryFactory.create_user_repository(session),
    }
