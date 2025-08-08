"""
Base repository interface following Interface Segregation Principle.

This module defines abstract base classes for repository patterns,
ensuring consistent data access interfaces across the application.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, TypeVar, Generic, Type
from sqlalchemy.orm import Session

# Generic type for model classes
ModelType = TypeVar("ModelType")
IDType = TypeVar("IDType")


class BaseRepository(Generic[ModelType, IDType], ABC):
    """
    Abstract base repository interface.

    Follows Interface Segregation Principle by providing
    only essential CRUD operations that all repositories need.
    """

    def __init__(self, session: Session, model_class: Type[ModelType]):
        """
        Initialize repository.

        Args:
            session: SQLAlchemy session
            model_class: Model class this repository manages
        """
        self.session = session
        self.model_class = model_class

    @abstractmethod
    def get_by_id(self, id: IDType) -> Optional[ModelType]:
        """Get entity by ID."""
        pass

    @abstractmethod
    def get_all(self) -> List[ModelType]:
        """Get all entities."""
        pass

    @abstractmethod
    def create(self, **kwargs) -> ModelType:
        """Create new entity."""
        pass

    @abstractmethod
    def update(self, entity: ModelType, **kwargs) -> ModelType:
        """Update existing entity."""
        pass

    @abstractmethod
    def delete(self, entity: ModelType) -> bool:
        """Delete entity."""
        pass

    def save(self, entity: ModelType) -> ModelType:
        """
        Save entity to database.

        Args:
            entity: Entity to save

        Returns:
            ModelType: Saved entity
        """
        self.session.add(entity)
        self.session.flush()  # Flush to get ID without committing
        return entity

    def refresh(self, entity: ModelType) -> ModelType:
        """
        Refresh entity from database.

        Args:
            entity: Entity to refresh

        Returns:
            ModelType: Refreshed entity
        """
        self.session.refresh(entity)
        return entity


class UserOwnedRepository(BaseRepository[ModelType, IDType], ABC):
    """
    Abstract repository for user-owned entities.

    Extends BaseRepository with user-specific operations,
    following Interface Segregation Principle.
    """

    @abstractmethod
    def get_by_user(self, user_id: int) -> List[ModelType]:
        """Get all entities owned by user."""
        pass

    @abstractmethod
    def get_by_id_and_user(self, id: IDType, user_id: int) -> Optional[ModelType]:
        """Get entity by ID if owned by user."""
        pass

    @abstractmethod
    def delete_by_user(self, id: IDType, user_id: int) -> bool:
        """Delete entity if owned by user."""
        pass
