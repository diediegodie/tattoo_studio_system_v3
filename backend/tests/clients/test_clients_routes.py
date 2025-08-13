import pytest
from flask import Flask, Blueprint
from unittest.mock import MagicMock, patch
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

from backend.models import Base
from backend.models.user import User
from backend.models.client import Client
from backend.routes.clients import clients_bp


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config.update(SECRET_KEY="testsecret", TESTING=True)

    # minimal auth blueprint so url_for('auth.login') resolves
    auth_bp = Blueprint("auth", __name__)

    @auth_bp.route("/login")
    def login():  # pragma: no cover - trivial stub
        return "login"

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(clients_bp)
    return app


@pytest.fixture
def client(app):
    with app.test_client() as c:
        yield c


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def seed_user_and_clients(session):
    user = User(name="Tester", email="tester@example.com")
    session.add(user)
    session.commit()
    c1 = Client(user_id=user.id, name="Alice", email="alice@example.com")
    c2 = Client(user_id=user.id, name="Bob", email="bob@example.com")
    session.add_all([c1, c2])
    session.commit()
    return user, [c1, c2]


def _patch_db_ctx(monkeypatch, db_session):
    @contextmanager
    def _ctx():
        yield db_session

    monkeypatch.setattr("backend.routes.clients.get_db_session", _ctx)


def _login_session(client, email, name="Tester"):
    with client.session_transaction() as sess:
        sess["user"] = {"email": email, "name": name}


def test_list_clients_happy_path(client, db_session, monkeypatch):
    user, clients = seed_user_and_clients(db_session)
    _patch_db_ctx(monkeypatch, db_session)

    _login_session(client, user.email, user.name)

    with patch("backend.routes.clients.render_template") as mock_render:
        mock_render.return_value = "ok"
        resp = client.get("/clients/")
        assert resp.status_code == 200
        # Verify template call received our clients
        assert mock_render.call_count == 1
        args, kwargs = mock_render.call_args
        assert args[0] == "clients_list.html"
        assert isinstance(kwargs.get("clients"), list)
        assert len(kwargs.get("clients")) == 2


def test_search_clients_happy_path(client, db_session, monkeypatch):
    user, clients = seed_user_and_clients(db_session)
    _patch_db_ctx(monkeypatch, db_session)

    _login_session(client, user.email, user.name)

    resp = client.get("/clients/search?q=Ali")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "clients" in data
    names = [c["name"] for c in data["clients"]]
    assert names == ["Alice"]


def test_delete_client_happy_path(client, db_session, monkeypatch):
    user, clients = seed_user_and_clients(db_session)
    _patch_db_ctx(monkeypatch, db_session)

    _login_session(client, user.email, user.name)

    target_id = clients[0].id
    resp = client.post(f"/clients/{target_id}/delete")
    assert resp.status_code == 302
    assert "/clients" in resp.location

    # Confirm deletion in DB
    remaining = db_session.scalars(select(Client).where(Client.id == target_id)).first()
    assert remaining is None


def test_unauthenticated_redirects_to_login(client):
    resp = client.get("/clients/", follow_redirects=False)
    assert resp.status_code == 302
    assert "/auth/login" in resp.location


def test_edit_client_flow_get_and_post(client, db_session, monkeypatch):
    # Seed and login
    user, clients = seed_user_and_clients(db_session)
    _patch_db_ctx(monkeypatch, db_session)
    _login_session(client, user.email, user.name)

    target = clients[0]

    # GET edit page renders form with client
    with patch("backend.routes.clients.render_template") as mock_render:
        mock_render.return_value = "ok"
        resp = client.get(f"/clients/{target.id}/edit")
        assert resp.status_code == 200
        args, kwargs = mock_render.call_args
        assert args[0] == "client_form.html"
        assert kwargs.get("client").id == target.id

    # POST update and expect redirect, then verify DB updated
    new_name = "Alice Updated"
    new_email = "alice.updated@example.com"
    resp = client.post(
        f"/clients/{target.id}/edit",
        data={"name": new_name, "email": new_email, "phone": "", "notes": ""},
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert "/clients" in resp.location

    refreshed = db_session.get(Client, target.id)
    assert refreshed is not None
    assert refreshed.name == new_name
    assert refreshed.email == new_email


def test_sync_jotform_no_api_key_renders_error(client, monkeypatch):
    # Logged in
    _login_session(client, "tester@example.com")

    # Mock DB session to return user without API key
    mock_db = MagicMock()
    mock_user = MagicMock()
    mock_user.jotform_api_key = None
    mock_db.scalars().first.return_value = mock_user
    mock_db.close = MagicMock()

    monkeypatch.setattr("backend.routes.clients.create_engine", MagicMock())
    monkeypatch.setattr(
        "backend.routes.clients.sessionmaker", lambda bind: (lambda: mock_db)
    )

    with patch("backend.routes.clients.render_template") as mock_render:
        mock_render.return_value = "ok"
        resp = client.get("/clients/sync_jotform")
        assert resp.status_code == 200
        args, kwargs = mock_render.call_args
        assert args[0] == "clients_list.html"
        assert kwargs.get("clients") == []
        assert "Nenhuma chave de API JotForm" in kwargs.get("error")


def test_sync_jotform_success_renders_clients(client, monkeypatch):
    # Logged in
    _login_session(client, "tester@example.com")

    # Mock DB session to return user with API key
    mock_db = MagicMock()
    mock_user = MagicMock()
    mock_user.jotform_api_key = "abc123"
    mock_db.scalars().first.return_value = mock_user
    mock_db.close = MagicMock()

    monkeypatch.setattr("backend.routes.clients.create_engine", MagicMock())
    monkeypatch.setattr(
        "backend.routes.clients.sessionmaker", lambda bind: (lambda: mock_db)
    )

    # Mock JotFormService to return clients
    fake_clients = [
        {"name": "Form Client", "email": "form@example.com"},
    ]
    mock_service = MagicMock()
    mock_service.get_clients_from_first_form.return_value = fake_clients
    monkeypatch.setattr(
        "backend.routes.clients.JotFormService", lambda key: mock_service
    )

    with patch("backend.routes.clients.render_template") as mock_render:
        mock_render.return_value = "ok"
        resp = client.get("/clients/sync_jotform")
        assert resp.status_code == 200
        args, kwargs = mock_render.call_args
        assert args[0] == "clients_list.html"
        assert kwargs.get("clients") == fake_clients
        assert kwargs.get("error") is None
