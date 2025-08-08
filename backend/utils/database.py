"""
Database utilities for session management and context handling.

This module provides context managers and utilities for proper
database session lifecycle management following SOLID principles.
"""

from contextlib import contextmanager
from typing import Generator, Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from flask import current_app
import logging

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Database manager following Dependency Inversion Principle.

    Provides abstract interface for database operations and session management.
    """

    def __init__(self, database_uri: str):
        """
        Initialize database manager.

        Args:
            database_uri: SQLAlchemy database URI
        """
        self.database_uri = database_uri
        self.engine = create_engine(database_uri)
        self.SessionLocal = sessionmaker(bind=self.engine)

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Context manager for database sessions.

        Ensures proper session cleanup and transaction handling.

        Yields:
            Session: SQLAlchemy session

        Example:
            with db_manager.get_session() as session:
                user = session.query(User).first()
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            session.close()

    def create_session(self) -> Session:
        """
        Create a new database session.

        Note: Caller is responsible for closing the session.
        Prefer using get_session() context manager.

        Returns:
            Session: SQLAlchemy session
        """
        return self.SessionLocal()


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


def init_database_manager(database_uri: str) -> None:
    """
    Initialize the global database manager.

    Args:
        database_uri: SQLAlchemy database URI
    """
    global _db_manager
    _db_manager = DatabaseManager(database_uri)


def get_database_manager() -> DatabaseManager:
    """
    Get the global database manager instance.

    Returns:
        DatabaseManager: Database manager instance

    Raises:
        RuntimeError: If database manager is not initialized
    """
    global _db_manager

    if _db_manager is None:
        # Try to initialize from Flask app context
        try:
            from ..config.config import get_config

            config = get_config()
            init_database_manager(config.get_database_uri())
        except Exception:
            raise RuntimeError(
                "Database manager not initialized. Call init_database_manager() first."
            )

    # After potential initialization, _db_manager should not be None
    if _db_manager is None:
        raise RuntimeError("Failed to initialize database manager")

    return _db_manager


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Convenience context manager for database sessions.

    Yields:
        Session: SQLAlchemy session

    Example:
        with get_db_session() as session:
            clients = session.query(Client).all()
    """
    db_manager = get_database_manager()
    with db_manager.get_session() as session:
        yield session


def create_db_session() -> Session:
    """
    Create a new database session.

    Note: Caller is responsible for closing the session.
    Prefer using get_db_session() context manager.

    Returns:
        Session: SQLAlchemy session
    """
    db_manager = get_database_manager()
    return db_manager.create_session()
