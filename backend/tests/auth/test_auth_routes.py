"""
Unit, edge, and failure tests for authentication routes (login_local, register, login_google, callback, request_password_reset, reset_password).
"""

import pytest
from flask import session
from unittest.mock import patch, MagicMock
from backend.auth.routes import auth_bp
from backend.models.user import User


@pytest.fixture
def client(app):
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.config["SECRET_KEY"] = "testsecret"
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    with app.test_client() as client:
        yield client


@pytest.fixture
def app():
    from flask import Flask

    app = Flask(__name__)
    return app


# --- login_local ---
def test_login_local_success(client, app):
    with patch("backend.auth.routes.create_engine"), patch(
        "backend.auth.routes.sessionmaker"
    ) as mock_sessionmaker:
        mock_db = MagicMock()
        user = User(name="Test", email="test@example.com")
        user.set_password("pw123")
        mock_db.query().filter_by().first.return_value = user
        mock_sessionmaker.return_value = lambda: mock_db
        resp = client.post(
            "/auth/login/local",
            data={"email": "test@example.com", "password": "pw123"},
            follow_redirects=False,
        )
        # Should redirect to dashboard
        assert resp.status_code == 302
        assert "/dashboard" in resp.location
        # Check session user set
        with client.session_transaction() as sess:
            assert sess.get("user")


def test_login_local_failure(client, app):
    with patch("backend.auth.routes.create_engine"), patch(
        "backend.auth.routes.sessionmaker"
    ) as mock_sessionmaker:
        mock_db = MagicMock()
        mock_db.query().filter_by().first.return_value = None
        mock_sessionmaker.return_value = lambda: mock_db
        resp = client.post(
            "/auth/login/local", data={"email": "fail@example.com", "password": "wrong"}
        )
        assert b"Invalid email or password" in resp.data


def test_login_local_missing_fields(client):
    resp = client.post("/auth/login/local", data={"email": ""})
    assert b"Email and password are required" in resp.data


# --- register ---
def test_register_success(client, app):
    with patch("backend.auth.routes.create_engine"), patch(
        "backend.auth.routes.sessionmaker"
    ) as mock_sessionmaker:
        mock_db = MagicMock()
        mock_db.query().filter_by().first.return_value = None
        mock_sessionmaker.return_value = lambda: mock_db
        with patch.dict("os.environ", {"GOOGLE_CLIENT_ID": "test-client-id"}):
            resp = client.post(
                "/auth/register",
                data={"name": "Test", "email": "test@example.com", "password": "pw123"},
                follow_redirects=False,
            )
            # Should redirect to login
            assert resp.status_code == 302
            assert "/login" in resp.location


def test_register_existing_email(client, app):
    with patch("backend.auth.routes.create_engine"), patch(
        "backend.auth.routes.sessionmaker"
    ) as mock_sessionmaker:
        mock_db = MagicMock()
        mock_db.query().filter_by().first.return_value = User(
            name="Test", email="test@example.com"
        )
        mock_sessionmaker.return_value = lambda: mock_db
        resp = client.post(
            "/auth/register",
            data={"name": "Test", "email": "test@example.com", "password": "pw123"},
        )
        assert b"Email already registered" in resp.data


def test_register_missing_fields(client):
    resp = client.post("/auth/register", data={"name": "", "email": "", "password": ""})
    assert b"All fields are required" in resp.data


# --- login_google ---
def test_login_google_success(client, app):
    with patch("backend.auth.routes.GoogleAuthService") as mock_service, patch.dict(
        "os.environ", {"GOOGLE_CLIENT_ID": "test-client-id"}
    ):
        instance = mock_service.return_value
        instance.get_authorization_url.return_value = ("http://auth", "state123")
        with client.session_transaction() as sess:
            sess.clear()
        resp = client.get("/auth/login/google")
        assert resp.status_code == 302
        assert resp.location.startswith("http://auth")
        with client.session_transaction() as sess:
            assert sess.get("flow_state") == "state123"


def test_login_google_missing_client_id(client, app):
    with patch.dict("os.environ", {}):
        with pytest.raises(RuntimeError):
            client.get("/auth/login/google")


# --- callback ---
def test_callback_success(client, app):
    with patch("backend.auth.routes.GoogleAuthService") as mock_service, patch(
        "backend.auth.routes.create_engine"
    ), patch("backend.auth.routes.sessionmaker") as mock_sessionmaker, patch.dict(
        "os.environ", {"GOOGLE_CLIENT_ID": "cid"}
    ):
        instance = mock_service.return_value
        instance.get_credentials_from_callback.return_value = {"id_token": "idtok"}
        instance.verify_id_token.return_value = {
            "email": "a@b.com",
            "name": "Test",
            "picture": "pic",
        }
        instance.create_jwt_token.return_value = "jwt"
        mock_db = MagicMock()
        mock_db.query().filter_by().first.return_value = None
        mock_sessionmaker.return_value = lambda: mock_db
        with client.session_transaction() as sess:
            sess.clear()
        app.config["SECRET_KEY"] = "testsecret"
        resp = client.get("/auth/login/google/callback", follow_redirects=False)
        # Should redirect to dashboard
        assert resp.status_code == 302
        assert "/dashboard" in resp.location
        with client.session_transaction() as sess:
            assert sess.get("user")
            assert sess.get("jwt_token") == "jwt"


def test_callback_missing_id_token(client, app):
    with patch("backend.auth.routes.GoogleAuthService") as mock_service, patch.dict(
        "os.environ", {"GOOGLE_CLIENT_ID": "cid"}
    ):
        instance = mock_service.return_value
        instance.get_credentials_from_callback.return_value = {"id_token": None}
        instance.verify_id_token.return_value = {}
        with client.session_transaction() as sess:
            sess.clear()
        resp = client.get("/auth/login/google/callback")
        assert b"Error: ID token not found" in resp.data or resp.status_code == 400


# --- Google callback edge/failure cases ---
def test_callback_missing_credentials(client, app):
    with patch("backend.auth.routes.GoogleAuthService") as mock_service, patch.dict(
        "os.environ", {"GOOGLE_CLIENT_ID": "cid"}
    ):
        instance = mock_service.return_value
        # Simulate get_credentials_from_callback raising an Exception
        instance.get_credentials_from_callback.side_effect = Exception("No credentials")
        with client.session_transaction() as sess:
            sess.clear()
        app.config["SECRET_KEY"] = "testsecret"
        resp = client.get("/auth/login/google/callback")
        assert resp.status_code == 400
        assert b"Authentication error" in resp.data


def test_callback_service_error(client, app):
    with patch("backend.auth.routes.GoogleAuthService") as mock_service, patch.dict(
        "os.environ", {"GOOGLE_CLIENT_ID": "cid"}
    ):
        instance = mock_service.return_value
        # Simulate verify_id_token raising an Exception
        instance.get_credentials_from_callback.return_value = {"id_token": "idtok"}
        instance.verify_id_token.side_effect = Exception("Token error")
        with client.session_transaction() as sess:
            sess.clear()
        app.config["SECRET_KEY"] = "testsecret"
        resp = client.get("/auth/login/google/callback")
        assert resp.status_code == 400
        assert b"Authentication error" in resp.data


# --- request_password_reset ---
def test_request_password_reset_success(client, app):
    with patch("backend.auth.routes.create_engine"), patch(
        "backend.auth.routes.sessionmaker"
    ) as mock_sessionmaker:
        mock_db = MagicMock()
        user = User(name="Test", email="test@example.com")
        mock_db.query().filter_by().first.return_value = user
        mock_sessionmaker.return_value = lambda: mock_db
        resp = client.post(
            "/auth/request_password_reset", data={"email": "test@example.com"}
        )
        assert b"Password reset link" in resp.data


def test_request_password_reset_no_user(client, app):
    with patch("backend.auth.routes.create_engine"), patch(
        "backend.auth.routes.sessionmaker"
    ) as mock_sessionmaker:
        mock_db = MagicMock()
        mock_db.query().filter_by().first.return_value = None
        mock_sessionmaker.return_value = lambda: mock_db
        resp = client.post(
            "/auth/request_password_reset", data={"email": "notfound@example.com"}
        )
        assert b"If this email is registered" in resp.data


# --- reset_password ---
def test_reset_password_success(client, app):
    from itsdangerous import URLSafeTimedSerializer

    serializer = URLSafeTimedSerializer("testsecret")
    token = serializer.dumps({"email": "test@example.com"}, salt="password-reset-salt")
    with patch("backend.auth.routes.create_engine"), patch(
        "backend.auth.routes.sessionmaker"
    ) as mock_sessionmaker:
        mock_db = MagicMock()
        user = User(name="Test", email="test@example.com")
        mock_db.query().filter_by().first.return_value = user
        mock_sessionmaker.return_value = lambda: mock_db
        resp = client.post(
            f"/auth/reset_password/{token}",
            data={"password": "pw123", "confirm_password": "pw123"},
            follow_redirects=True,
        )
        assert b"Your password has been updated" in resp.data


def test_reset_password_expired_token(client):
    from itsdangerous import URLSafeTimedSerializer, SignatureExpired

    serializer = URLSafeTimedSerializer("testsecret")
    token = serializer.dumps({"email": "test@example.com"}, salt="password-reset-salt")
    with patch(
        "backend.auth.routes.URLSafeTimedSerializer.loads",
        side_effect=SignatureExpired("expired"),
    ):
        resp = client.post(
            f"/auth/reset_password/{token}",
            data={"password": "pw123", "confirm_password": "pw123"},
            follow_redirects=True,
        )
        # Should render reset form with error message
        assert b"expired" in resp.data or b"password reset" in resp.data


def test_reset_password_invalid_token(client):
    from itsdangerous import URLSafeTimedSerializer, BadSignature

    serializer = URLSafeTimedSerializer("testsecret")
    token = serializer.dumps({"email": "test@example.com"}, salt="password-reset-salt")
    with patch(
        "backend.auth.routes.URLSafeTimedSerializer.loads",
        side_effect=BadSignature("bad"),
    ):
        resp = client.post(
            f"/auth/reset_password/{token}",
            data={"password": "pw123", "confirm_password": "pw123"},
            follow_redirects=True,
        )
        # Should render reset form with error message
        assert (
            b"Invalid password reset token" in resp.data
            or b"password reset" in resp.data
        )


def test_reset_password_mismatch(client):
    from itsdangerous import URLSafeTimedSerializer

    serializer = URLSafeTimedSerializer("testsecret")
    token = serializer.dumps({"email": "test@example.com"}, salt="password-reset-salt")
    resp = client.post(
        f"/auth/reset_password/{token}",
        data={"password": "pw1", "confirm_password": "pw2"},
    )
    assert b"Passwords do not match" in resp.data


def test_reset_password_missing_fields(client):
    from itsdangerous import URLSafeTimedSerializer

    serializer = URLSafeTimedSerializer("testsecret")
    token = serializer.dumps({"email": "test@example.com"}, salt="password-reset-salt")
    resp = client.post(
        f"/auth/reset_password/{token}", data={"password": "", "confirm_password": ""}
    )
    assert b"All fields are required" in resp.data


# --- logout ---
def test_logout_clears_session_and_redirects(client):
    with client.session_transaction() as sess:
        sess["user"] = {"email": "test@example.com", "name": "Test"}
        sess["jwt_token"] = "sometoken"
    resp = client.get("/auth/logout", follow_redirects=False)
    # Should redirect to login
    assert resp.status_code == 302
    assert "/login" in resp.location
    # Session should be cleared
    with client.session_transaction() as sess:
        assert "user" not in sess
        assert "jwt_token" not in sess


# --- dashboard access control ---
def test_dashboard_requires_authentication(client):
    # No user in session
    resp = client.get("/auth/dashboard", follow_redirects=False)
    assert resp.status_code == 302
    assert "/login" in resp.location

    # With user in session
    with client.session_transaction() as sess:
        sess["user"] = {"email": "test@example.com", "name": "Test"}
    resp = client.get("/auth/dashboard", follow_redirects=False)
    assert resp.status_code == 200
    assert b"Test" in resp.data


# --- session persistence ---
def test_session_persistence_across_requests(client):
    # Simulate login by setting session
    with client.session_transaction() as sess:
        sess["user"] = {"email": "persist@example.com", "name": "Persist"}
    # First request
    resp1 = client.get("/auth/dashboard")
    assert resp1.status_code == 200
    assert b"Persist" in resp1.data
    # Second request (should still be authenticated)
    resp2 = client.get("/auth/dashboard")
    assert resp2.status_code == 200
    assert b"Persist" in resp2.data


# --- JWT token in session ---
def test_jwt_token_in_session_after_google_login(client, app):
    import jwt as pyjwt

    with patch("backend.auth.routes.GoogleAuthService") as mock_service, patch(
        "backend.auth.routes.create_engine"
    ), patch("backend.auth.routes.sessionmaker") as mock_sessionmaker, patch.dict(
        "os.environ", {"GOOGLE_CLIENT_ID": "cid"}
    ):
        instance = mock_service.return_value
        instance.get_credentials_from_callback.return_value = {"id_token": "idtok"}
        user_info = {
            "email": "jwtuser@example.com",
            "name": "JWT User",
            "picture": "pic",
        }
        instance.verify_id_token.return_value = user_info
        # Use a real JWT for this test
        secret = "testsecret"
        app.config["SECRET_KEY"] = secret
        token = pyjwt.encode(
            {
                "email": user_info["email"],
                "name": user_info["name"],
                "picture": user_info["picture"],
            },
            secret,
            algorithm="HS256",
        )
        instance.create_jwt_token.return_value = token
        mock_db = MagicMock()
        mock_db.query().filter_by().first.return_value = None
        mock_sessionmaker.return_value = lambda: mock_db
        with client.session_transaction() as sess:
            sess.clear()
        resp = client.get("/auth/login/google/callback", follow_redirects=False)
        assert resp.status_code == 302
        with client.session_transaction() as sess:
            jwt_token = sess.get("jwt_token")
            assert jwt_token is not None
            payload = pyjwt.decode(jwt_token, secret, algorithms=["HS256"])
            assert payload["email"] == user_info["email"]
            assert payload["name"] == user_info["name"]
            assert payload["picture"] == user_info["picture"]


# --- Database error handling ---
def test_register_db_connection_error(client, app):
    with patch(
        "backend.auth.routes.create_engine", side_effect=Exception("DB connect fail")
    ):
        resp = client.post(
            "/auth/register",
            data={"name": "Test", "email": "fail@example.com", "password": "pw123"},
        )
        # Should not crash, should render the form again (could be improved to show error)
        assert resp.status_code == 200
        assert b"register" in resp.data.lower()


def test_register_db_commit_error(client, app):
    with patch("backend.auth.routes.create_engine"), patch(
        "backend.auth.routes.sessionmaker"
    ) as mock_sessionmaker:
        mock_db = MagicMock()
        mock_db.query().filter_by().first.return_value = None
        mock_db.add.side_effect = None
        mock_db.commit.side_effect = Exception("DB commit fail")
        mock_sessionmaker.return_value = lambda: mock_db
        resp = client.post(
            "/auth/register",
            data={"name": "Test", "email": "fail2@example.com", "password": "pw123"},
        )
        # Should not crash, should render the form again (could be improved to show error)
        assert resp.status_code == 200
        assert b"register" in resp.data.lower()


def test_reset_password_db_commit_error(client, app):
    from itsdangerous import URLSafeTimedSerializer

    serializer = URLSafeTimedSerializer("testsecret")
    token = serializer.dumps({"email": "test@example.com"}, salt="password-reset-salt")
    with patch("backend.auth.routes.create_engine"), patch(
        "backend.auth.routes.sessionmaker"
    ) as mock_sessionmaker:
        mock_db = MagicMock()
        user = User(name="Test", email="test@example.com")
        mock_db.query().filter_by().first.return_value = user
        mock_db.commit.side_effect = Exception("DB commit fail")
        mock_sessionmaker.return_value = lambda: mock_db
        resp = client.post(
            f"/auth/reset_password/{token}",
            data={"password": "pw123", "confirm_password": "pw123"},
        )
        # Should not crash, should render the form
