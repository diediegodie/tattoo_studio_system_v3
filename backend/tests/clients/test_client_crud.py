import pytest
from unittest.mock import MagicMock
from backend.services.client_service import ClientService
from backend.models.client import Client


@pytest.fixture
def mock_db_session():
    return MagicMock()


@pytest.fixture
def client_service(mock_db_session):
    service = ClientService(mock_db_session)
    service.user_repo = MagicMock()
    service.client_repo = MagicMock()
    return service


def test_create_client_normal_case(client_service):
    client_service.user_repo.get_by_id.return_value = MagicMock(id=1)
    client_service.client_repo.create.return_value = Client(
        id=1, name="John Doe", email="john@example.com"
    )
    client = client_service.create_client(
        1, "John Doe", "john@example.com", "123456789", "notes"
    )
    assert client is not None
    assert client.name == "John Doe"
    assert client.email == "john@example.com"


def test_create_client_missing_required_field(client_service):
    client_service.user_repo.get_by_id.return_value = MagicMock(id=1)
    client = client_service.create_client(1, "", "", "", "")
    assert client is None


def test_create_client_db_failure(client_service):
    client_service.user_repo.get_by_id.return_value = MagicMock(id=1)
    client_service.client_repo.create.side_effect = Exception("DB error")
    client = client_service.create_client(
        1, "John Doe", "john@example.com", "123456789", "notes"
    )
    assert client is None


def test_update_client_normal_case(client_service):
    mock_client = MagicMock(id=1, name="Old Name", email="old@example.com")
    client_service.client_repo.get_by_id_and_user.return_value = mock_client
    client_service.client_repo.update.return_value = Client(
        id=1, name="New Name", email="new@example.com"
    )
    updated = client_service.update_client(1, 1, "New Name", "new@example.com", "", "")
    assert updated is not None
    assert updated.name == "New Name"
    assert updated.email == "new@example.com"


def test_update_client_not_found(client_service):
    client_service.client_repo.get_by_id_and_user.return_value = None
    updated = client_service.update_client(1, 1, "New Name", "new@example.com", "", "")
    assert updated is None


def test_delete_client_normal_case(client_service):
    client_service.client_repo.get_by_id_and_user.return_value = MagicMock(id=1)
    client_service.client_repo.delete_by_user.return_value = True
    result = client_service.delete_client(1, 1)
    assert result is True


def test_delete_client_not_found(client_service):
    client_service.client_repo.get_by_id_and_user.return_value = None
    client_service.client_repo.delete_by_user.return_value = False
    result = client_service.delete_client(1, 1)
    assert result is False
