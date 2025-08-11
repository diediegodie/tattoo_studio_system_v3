import pytest
from unittest.mock import patch, MagicMock
from backend.services.jotform_service import JotFormService


def test_get_clients_from_first_form_normal_case():
    with patch.object(
        JotFormService,
        "get_clients_from_first_form",
        return_value=[{"name": "John Doe", "email": "john@example.com"}],
    ) as mock_method:
        service = JotFormService("fake_api_key")
        clients = service.get_clients_from_first_form()
        assert isinstance(clients, list)
        assert clients[0]["name"] == "John Doe"
        assert clients[0]["email"] == "john@example.com"
        mock_method.assert_called_once()


def test_get_clients_from_first_form_empty():
    with patch.object(
        JotFormService, "get_clients_from_first_form", return_value=[]
    ) as mock_method:
        service = JotFormService("fake_api_key")
        clients = service.get_clients_from_first_form()
        assert clients == []
        mock_method.assert_called_once()


def test_get_clients_from_first_form_failure():
    with patch.object(
        JotFormService,
        "get_clients_from_first_form",
        side_effect=Exception("API error"),
    ) as mock_method:
        service = JotFormService("fake_api_key")
        try:
            service.get_clients_from_first_form()
        except Exception as e:
            assert str(e) == "API error"
        mock_method.assert_called_once()
