"""
Unit tests for Google OAuth authentication routes only.
Local authentication tests have been removed as the functionality no longer exists.
"""

import pytest
from flask import session
from unittest.mock import patch, MagicMock
from backend.auth.routes import auth_bp
from backend.models.user import User


@pytest.fixture
def test_client(test_app):
    test_app.register_blueprint(auth_bp, url_prefix="/auth")
    test_app.config["SECRET_KEY"] = "testsecret"
    test_app.config["TESTING"] = True
    test_app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    with test_app.test_client() as client:
        yield client


@pytest.fixture
def test_app():
    from flask import Flask

    app = Flask(__name__)
    return app


# --- login redirect ---
def test_login_redirects_to_google(test_client):
    """Test that /auth/login redirects to Google OAuth."""
    resp = test_client.get("/auth/login", follow_redirects=False)
    assert resp.status_code == 302
    assert "/auth/login/google" in resp.location


# --- login_required decorator ---
def test_login_required_decorator(test_client):
    """Test that login_required decorator redirects unauthenticated users."""
    resp = test_client.get("/auth/dashboard", follow_redirects=False)
    assert resp.status_code == 302
    assert "/auth/login" in resp.location


def test_login_required_allows_authenticated_users(test_client):
    """Test that login_required allows authenticated users."""
    with test_client.session_transaction() as sess:
        sess["user"] = {"email": "test@example.com", "name": "Test User"}

    with patch("backend.auth.routes.render_template") as mock_render:
        mock_render.return_value = "dashboard content"
        resp = test_client.get("/auth/dashboard")
        assert resp.status_code == 200
        mock_render.assert_called_once_with(
            "dashboard.html", user={"email": "test@example.com", "name": "Test User"}
        )


# --- logout ---
def test_logout_clears_session_and_redirects(test_client):
    """Test that logout clears session and redirects to login."""
    with test_client.session_transaction() as sess:
        sess["user"] = {"email": "test@example.com", "name": "Test User"}
        sess["credentials"] = {"some": "data"}

    resp = test_client.get("/auth/logout", follow_redirects=False)
    assert resp.status_code == 302
    assert "/auth/login" in resp.location

    with test_client.session_transaction() as sess:
        assert "user" not in sess
        assert "credentials" not in sess


# --- Google OAuth flow tests ---
@patch.dict("os.environ", {"GOOGLE_CLIENT_ID": "test_client_id"})
def test_login_google_redirects_to_oauth(test_client):
    """Test that Google login initiates OAuth flow."""
    with patch("backend.auth.routes.GoogleAuthService") as mock_service_class:
        mock_service = MagicMock()
        mock_service.get_authorization_url.return_value = (
            "https://oauth.url",
            "state123",
        )
        mock_service_class.return_value = mock_service

        resp = test_client.get("/auth/login/google", follow_redirects=False)

        assert resp.status_code == 302
        assert resp.location == "https://oauth.url"

        with test_client.session_transaction() as sess:
            assert sess["flow_state"] == "state123"


def test_login_google_without_client_id_raises_error(test_client):
    """Test that Google login raises error without GOOGLE_CLIENT_ID."""
    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(
            RuntimeError, match="GOOGLE_CLIENT_ID environment variable is not set"
        ):
            test_client.get("/auth/login/google")


@patch.dict("os.environ", {"GOOGLE_CLIENT_ID": "test_client_id"})
def test_callback_success_creates_new_user(test_client):
    """Test successful OAuth callback creates new user."""
    with patch("backend.auth.routes.GoogleAuthService") as mock_service_class, patch(
        "backend.auth.routes.create_engine"
    ), patch("backend.auth.routes.sessionmaker") as mock_sessionmaker:

        # Mock service
        mock_service = MagicMock()
        mock_service.get_credentials_from_callback.return_value = {
            "id_token": "mock_token"
        }
        mock_service.verify_id_token.return_value = {
            "email": "newuser@example.com",
            "name": "New User",
            "picture": "https://photo.url",
        }
        mock_service.create_jwt_token.return_value = "jwt_token"
        mock_service_class.return_value = mock_service

        # Mock database
        mock_db = MagicMock()
        mock_db.query().filter_by().first.return_value = None  # No existing user
        mock_sessionmaker.return_value = lambda: mock_db

        resp = test_client.get(
            "/auth/login/google/callback?code=test&state=test", follow_redirects=False
        )

        assert resp.status_code == 302
        assert "/auth/dashboard" in resp.location

        # Verify new user was added
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called()

        # Verify session was set
        with test_client.session_transaction() as sess:
            assert sess["user"]["email"] == "newuser@example.com"
            assert sess["user"]["name"] == "New User"
            assert sess["jwt_token"] == "jwt_token"


@patch.dict("os.environ", {"GOOGLE_CLIENT_ID": "test_client_id"})
def test_callback_success_updates_existing_user(test_client):
    """Test successful OAuth callback updates existing user."""
    with patch("backend.auth.routes.GoogleAuthService") as mock_service_class, patch(
        "backend.auth.routes.create_engine"
    ), patch("backend.auth.routes.sessionmaker") as mock_sessionmaker:

        # Mock service
        mock_service = MagicMock()
        mock_service.get_credentials_from_callback.return_value = {
            "id_token": "mock_token"
        }
        mock_service.verify_id_token.return_value = {
            "email": "existing@example.com",
            "name": "Updated Name",
            "picture": "https://photo.url",
        }
        mock_service.create_jwt_token.return_value = "jwt_token"
        mock_service_class.return_value = mock_service

        # Mock existing user
        existing_user = MagicMock()
        existing_user.name = "Old Name"
        existing_user.email = "existing@example.com"

        # Mock database
        mock_db = MagicMock()
        mock_db.query().filter_by().first.return_value = existing_user
        mock_sessionmaker.return_value = lambda: mock_db

        resp = test_client.get(
            "/auth/login/google/callback?code=test&state=test", follow_redirects=False
        )

        assert resp.status_code == 302
        assert "/auth/dashboard" in resp.location

        # Verify user name was updated
        assert existing_user.name == "Updated Name"
        mock_db.commit.assert_called()

        # Verify no new user was added
        mock_db.add.assert_not_called()


@patch.dict("os.environ", {"GOOGLE_CLIENT_ID": "test_client_id"})
def test_callback_handles_oauth_error(test_client):
    """Test that OAuth callback handles errors gracefully."""
    with patch("backend.auth.routes.GoogleAuthService") as mock_service_class:
        mock_service = MagicMock()
        mock_service.get_credentials_from_callback.side_effect = Exception(
            "OAuth Error"
        )
        mock_service_class.return_value = mock_service

        resp = test_client.get("/auth/login/google/callback?error=access_denied")

        assert resp.status_code == 400
        assert "Authentication error" in resp.get_data(as_text=True)


@patch.dict("os.environ", {"GOOGLE_CLIENT_ID": "test_client_id"})
def test_callback_missing_id_token(test_client):
    """Test callback handles missing ID token."""
    with patch("backend.auth.routes.GoogleAuthService") as mock_service_class:
        mock_service = MagicMock()
        mock_service.get_credentials_from_callback.return_value = {}  # No id_token
        mock_service_class.return_value = mock_service

        resp = test_client.get("/auth/login/google/callback?code=test")

        assert resp.status_code == 400
        assert "ID token not found" in resp.get_data(as_text=True)


# --- JotForm integration tests ---
def test_jotform_connect_requires_login(test_client):
    """Test that JotForm connect requires authentication."""
    resp = test_client.get("/auth/jotform/connect", follow_redirects=False)
    assert resp.status_code == 302
    assert "/auth/login" in resp.location


def test_jotform_connect_saves_api_key(test_client):
    """Test that JotForm connect saves API key for authenticated user."""
    with test_client.session_transaction() as sess:
        sess["user"] = {"email": "test@example.com", "name": "Test User"}

    with patch("backend.auth.routes.create_engine"), patch(
        "backend.auth.routes.sessionmaker"
    ) as mock_sessionmaker, patch("backend.auth.routes.render_template") as mock_render:

        # Mock user and database
        mock_user = MagicMock()
        mock_db = MagicMock()
        mock_db.query().filter_by().first.return_value = mock_user
        mock_sessionmaker.return_value = lambda: mock_db
        mock_render.return_value = "redirect response"

        resp = test_client.post(
            "/auth/jotform/connect",
            data={"jotform_api_key": "test_api_key"},
            follow_redirects=False,
        )

        # Verify API key was set
        assert hasattr(mock_user, "jotform_api_key")
        mock_db.commit.assert_called_once()

        assert resp.status_code == 302
        assert "/auth/clients" in resp.location


# --- Client management tests ---
def test_client_management_requires_login(test_client):
    """Test that client management requires authentication."""
    resp = test_client.get("/auth/clients", follow_redirects=False)
    assert resp.status_code == 302
    assert "/auth/login" in resp.location
