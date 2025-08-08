"""
Tests for the refactored SOLID architecture.

This module tests the key components of the refactored codebase
to ensure SOLID principles are properly implemented.
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch


# Test Configuration
def test_config_creation():
    """Test configuration creation and validation."""
    from backend.config.config import get_config, DevelopmentConfig, ProductionConfig

    # Test development config
    dev_config = get_config("development")
    assert isinstance(dev_config, DevelopmentConfig)
    assert dev_config.DEBUG is True

    # Test production config validation
    with patch.dict(os.environ, {"FLASK_SECRET_KEY": "test-secret"}):
        prod_config = get_config("production")
        assert isinstance(prod_config, ProductionConfig)
        assert prod_config.DEBUG is False


# Test Database Manager
def test_database_manager():
    """Test database manager context management."""
    from backend.utils.database import DatabaseManager

    # Create temporary database for testing
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_uri = f"sqlite:///{tmp.name}"

    try:
        db_manager = DatabaseManager(db_uri)

        # Test context manager
        with db_manager.get_session() as session:
            assert session is not None
            # Session should be automatically closed after context

        # Test session creation
        session = db_manager.create_session()
        assert session is not None
        session.close()

    finally:
        # Clean up
        if os.path.exists(tmp.name):
            os.unlink(tmp.name)


# Test Repository Pattern
def test_repository_abstraction():
    """Test repository base classes follow SOLID principles."""
    from backend.repositories.base import BaseRepository, UserOwnedRepository
    from backend.repositories.client_repository import ClientRepository
    from sqlalchemy.orm import Session

    # Test that ClientRepository implements required interfaces
    mock_session = Mock(spec=Session)
    client_repo = ClientRepository(mock_session)

    # Should implement BaseRepository interface
    assert hasattr(client_repo, "get_by_id")
    assert hasattr(client_repo, "get_all")
    assert hasattr(client_repo, "create")
    assert hasattr(client_repo, "update")
    assert hasattr(client_repo, "delete")

    # Should implement UserOwnedRepository interface
    assert hasattr(client_repo, "get_by_user")
    assert hasattr(client_repo, "get_by_id_and_user")
    assert hasattr(client_repo, "delete_by_user")


# Test Service Layer
def test_service_layer():
    """Test service layer follows SOLID principles."""
    from backend.services.client_service import ClientService
    from backend.services.jotform_service import JotFormService, BaseFormService
    from sqlalchemy.orm import Session

    # Test ClientService initialization
    mock_session = Mock(spec=Session)
    client_service = ClientService(mock_session)
    assert client_service.session == mock_session

    # Test JotFormService follows interface
    jotform_service = JotFormService("test-api-key")
    assert isinstance(jotform_service, BaseFormService)
    assert hasattr(jotform_service, "get_forms")
    assert hasattr(jotform_service, "get_submissions")
    assert hasattr(jotform_service, "parse_client_data")


# Test Service Factory
def test_service_factory():
    """Test factory pattern implementation."""
    from backend.services.jotform_service import FormServiceFactory, JotFormService

    # Test JotForm service creation
    service = FormServiceFactory.create_jotform_service("test-api-key")
    assert isinstance(service, JotFormService)

    # Test generic service creation
    service = FormServiceFactory.create_form_service("jotform", "test-api-key")
    assert isinstance(service, JotFormService)

    # Test unsupported provider
    with pytest.raises(ValueError):
        FormServiceFactory.create_form_service("unsupported", "test-api-key")


# Test Service Container
def test_service_container():
    """Test dependency injection container."""
    from backend.utils.service_container import ServiceContainer

    container = ServiceContainer()

    # Test singleton registration
    test_service = Mock()
    container.register_singleton("test_service", test_service)
    assert container.get("test_service") == test_service
    assert container.has("test_service")

    # Test factory registration
    def factory():
        return Mock()

    container.register_factory("factory_service", factory)
    service1 = container.get("factory_service")
    service2 = container.get("factory_service")
    # Factory should create new instances
    assert service1 != service2

    # Test service class registration
    class TestService:
        def __init__(self, value):
            self.value = value

    container.register_service("class_service", TestService, "test_value")
    service = container.get("class_service")
    assert isinstance(service, TestService)
    assert service.value == "test_value"

    # Test non-existent service
    with pytest.raises(KeyError):
        container.get("non_existent")

    assert container.get_or_none("non_existent") is None


# Test Model Improvements
def test_model_improvements():
    """Test model enhancements."""
    from backend.models.user import User
    from backend.models.client import Client

    # Test User model methods
    user = User()
    user.set_password("test_password")
    assert user.password_hash is not None
    assert user.check_password("test_password")
    assert not user.check_password("wrong_password")

    # Test Client model methods
    client = Client(id=1, name="Test Client", email="test@example.com")

    client_dict = client.to_dict()
    assert client_dict["id"] == 1
    assert client_dict["name"] == "Test Client"
    assert client_dict["email"] == "test@example.com"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
