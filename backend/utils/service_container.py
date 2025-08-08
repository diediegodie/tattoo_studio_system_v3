"""
Dependency injection container for the Tattoo Studio System.

This module provides a simple service locator pattern implementation
following Dependency Inversion Principle.
"""

from typing import Dict, Any, Type, TypeVar, Optional, Callable
from flask import g
import logging

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ServiceContainer:
    """
    Simple service container implementing dependency injection.

    Follows Dependency Inversion Principle by providing abstraction
    for service creation and management.
    """

    def __init__(self):
        """Initialize service container."""
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable[[], Any]] = {}
        self._singletons: Dict[str, Any] = {}

    def register_singleton(self, name: str, instance: Any) -> None:
        """
        Register a singleton service instance.

        Args:
            name: Service name
            instance: Service instance
        """
        self._singletons[name] = instance
        logger.debug(f"Registered singleton service: {name}")

    def register_factory(self, name: str, factory: Callable[[], Any]) -> None:
        """
        Register a factory function for service creation.

        Args:
            name: Service name
            factory: Factory function that creates service instances
        """
        self._factories[name] = factory
        logger.debug(f"Registered factory for service: {name}")

    def register_service(
        self, name: str, service_class: Type[T], *args, **kwargs
    ) -> None:
        """
        Register a service class with constructor arguments.

        Args:
            name: Service name
            service_class: Service class
            *args: Constructor arguments
            **kwargs: Constructor keyword arguments
        """

        def factory():
            return service_class(*args, **kwargs)

        self.register_factory(name, factory)

    def get(self, name: str) -> Any:
        """
        Get service instance by name.

        Args:
            name: Service name

        Returns:
            Service instance

        Raises:
            KeyError: If service is not registered
        """
        # Check singletons first
        if name in self._singletons:
            return self._singletons[name]

        # Check factories
        if name in self._factories:
            instance = self._factories[name]()
            logger.debug(f"Created service instance: {name}")
            return instance

        # Check regular services
        if name in self._services:
            return self._services[name]

        raise KeyError(f"Service '{name}' not registered")

    def get_or_none(self, name: str) -> Optional[Any]:
        """
        Get service instance or None if not found.

        Args:
            name: Service name

        Returns:
            Service instance or None
        """
        try:
            return self.get(name)
        except KeyError:
            return None

    def has(self, name: str) -> bool:
        """
        Check if service is registered.

        Args:
            name: Service name

        Returns:
            bool: True if service is registered
        """
        return (
            name in self._singletons
            or name in self._factories
            or name in self._services
        )

    def clear(self) -> None:
        """Clear all registered services."""
        self._services.clear()
        self._factories.clear()
        self._singletons.clear()
        logger.debug("Service container cleared")


# Global service container instance
_container: Optional[ServiceContainer] = None


def get_container() -> ServiceContainer:
    """
    Get the global service container.

    Returns:
        ServiceContainer: Global service container instance
    """
    global _container
    if _container is None:
        _container = ServiceContainer()
    return _container


def init_services() -> None:
    """
    Initialize default services in the container.

    This function registers commonly used services with the container.
    """
    container = get_container()

    # Register database-related services
    from ..utils.database import get_database_manager

    try:
        db_manager = get_database_manager()
        container.register_singleton("database_manager", db_manager)
    except RuntimeError:
        logger.warning(
            "Database manager not initialized, skipping service registration"
        )

    # Register service factories
    from ..services.client_service import ClientService
    from ..services.jotform_service import FormServiceFactory

    def client_service_factory():
        """Factory for ClientService."""
        from ..utils.database import create_db_session

        session = create_db_session()
        return ClientService(session)

    container.register_factory("client_service", client_service_factory)

    def jotform_service_factory():
        """Factory for JotFormService - requires API key."""

        def create_jotform_service(api_key: str):
            return FormServiceFactory.create_jotform_service(api_key)

        return create_jotform_service

    container.register_factory("jotform_service_factory", jotform_service_factory)

    logger.info("Default services initialized in container")


# Flask integration
def get_service(name: str) -> Any:
    """
    Get service from Flask application context.

    Args:
        name: Service name

    Returns:
        Service instance
    """
    if not hasattr(g, "service_container"):
        g.service_container = get_container()

    return g.service_container.get(name)


def register_service_in_app_context(name: str, service: Any) -> None:
    """
    Register service in Flask application context.

    Args:
        name: Service name
        service: Service instance
    """
    if not hasattr(g, "service_container"):
        g.service_container = get_container()

    g.service_container.register_singleton(name, service)
