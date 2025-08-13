import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from datetime import date, time

from backend.models import Base
from backend.models.user import User
from backend.models.client import Client
from backend.services.session_service import SessionService


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def monkeypatch_db(monkeypatch, db_session):
    @contextmanager
    def _ctx():
        yield db_session

    monkeypatch.setattr("backend.repositories.session_repository.get_db_session", _ctx)
    monkeypatch.setattr("backend.services.session_service.get_db_session", _ctx)


@pytest.fixture()
def seeded(db_session):
    # Create a user (artist) and a client
    artist = User(name="Artist", email="artist@example.com")
    db_session.add(artist)
    db_session.commit()

    client = Client(user_id=artist.id, name="Client A", email="c@example.com")
    db_session.add(client)
    db_session.commit()
    return artist, client


def test_create_session_and_detect_conflict(monkeypatch, db_session, seeded):
    monkeypatch_db(monkeypatch, db_session)
    artist, client = seeded
    service = SessionService()

    # Create a valid session
    created = service.create_session(
        {
            "artist_id": artist.id,
            "client_id": client.id,
            "date": date(2025, 1, 1).isoformat(),
            "start_time": time(10, 0).isoformat(timespec="minutes"),
            "end_time": time(11, 0).isoformat(timespec="minutes"),
            "notes": "Initial session",
        }
    )
    assert created["id"] is not None

    # Attempt overlapping session for same artist & date
    with pytest.raises(ValueError) as exc:
        service.create_session(
            {
                "artist_id": artist.id,
                "client_id": client.id,
                "date": date(2025, 1, 1).isoformat(),
                "start_time": time(10, 30).isoformat(timespec="minutes"),
                "end_time": time(11, 30).isoformat(timespec="minutes"),
                "notes": "Overlap",
            }
        )
    msg = exc.value.args[0]
    assert isinstance(msg, dict)
    assert "error" in msg and "conflict" in msg["error"].lower()

    # Non-overlapping later session should succeed
    created2 = service.create_session(
        {
            "artist_id": artist.id,
            "client_id": client.id,
            "date": date(2025, 1, 1).isoformat(),
            "start_time": time(11, 0).isoformat(timespec="minutes"),
            "end_time": time(12, 0).isoformat(timespec="minutes"),
            "notes": None,
        }
    )
    assert created2["id"] != created["id"]
