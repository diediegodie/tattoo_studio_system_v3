"""
Unit, edge, and failure tests for GoogleAuthService methods.
"""
import pytest
from unittest.mock import patch, MagicMock
from backend.auth.services.google_service import GoogleAuthService

CLIENT_SECRET_PATH = "/tmp/fake_client_secret.json"
REDIRECT_URI = "http://localhost/callback"
SCOPES = ["openid", "email", "profile"]
CLIENT_ID = "fake-client-id"
JWT_SECRET = "supersecret"

@pytest.fixture
def service():
    return GoogleAuthService(
        client_secret_path=CLIENT_SECRET_PATH,
        redirect_uri=REDIRECT_URI,
        scopes=SCOPES,
        client_id=CLIENT_ID,
        jwt_secret=JWT_SECRET
    )

def test_get_authorization_url_success(service):
    with patch.object(service, '_create_flow') as mock_flow:
        mock_instance = MagicMock()
        mock_instance.authorization_url.return_value = ("http://auth", "state123")
        mock_flow.return_value = mock_instance
        url, state = service.get_authorization_url()
        assert url == "http://auth"
        assert state == "state123"

def test_get_authorization_url_failure(service):
    with patch.object(service, '_create_flow', side_effect=Exception("fail")):
        with pytest.raises(Exception):
            service.get_authorization_url()

def test_get_credentials_from_callback_success(service):
    with patch.object(service, '_create_flow') as mock_flow:
        mock_instance = MagicMock()
        mock_instance.credentials.token = "tok"
        mock_instance.credentials.refresh_token = "refresh"
        mock_instance.credentials.token_uri = "uri"
        mock_instance.credentials.client_id = "cid"
        mock_instance.credentials.client_secret = "csecret"
        mock_instance.credentials.scopes = SCOPES
        mock_instance.credentials.id_token = "idtok"
        mock_instance.fetch_token = MagicMock()
        mock_flow.return_value = mock_instance
        creds = service.get_credentials_from_callback("http://cb?code=123")
        assert creds["token"] == "tok"
        assert creds["refresh_token"] == "refresh"
        assert creds["token_uri"] == "uri"
        assert creds["client_id"] == "cid"
        assert creds["client_secret"] == "csecret"
        assert creds["scopes"] == SCOPES
        assert creds["id_token"] == "idtok"

def test_get_credentials_from_callback_failure(service):
    with patch.object(service, '_create_flow', side_effect=Exception("fail")):
        with pytest.raises(Exception):
            service.get_credentials_from_callback("badresp")

def test_verify_id_token_success(service):
    with patch("backend.auth.services.google_service.id_token.verify_oauth2_token") as mock_verify:
        mock_verify.return_value = {"email": "a@b.com"}
        result = service.verify_id_token("sometoken")
        assert result["email"] == "a@b.com"

def test_verify_id_token_missing(service):
    with pytest.raises(ValueError):
        service.verify_id_token("")

def test_create_jwt_token(service):
    user_info = {"email": "a@b.com", "name": "Test", "picture": "pic"}
    token = service.create_jwt_token(user_info)
    assert isinstance(token, str)
    # decode to check payload
    import jwt as pyjwt
    payload = pyjwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    assert payload["email"] == "a@b.com"
    assert payload["name"] == "Test"
    assert payload["picture"] == "pic"
    assert "exp" in payload

def test__create_flow_file_not_found(service):
    import os
    with patch("os.path.isfile", return_value=False):
        with pytest.raises(FileNotFoundError):
            service._create_flow()
