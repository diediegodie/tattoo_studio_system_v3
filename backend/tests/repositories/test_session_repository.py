import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

from backend.models import Base
from backend.models.user import User
from backend.models.client import Client
from backend.models.session import Session
from backend.repositories.session_repository import SessionRepository


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


def seed_user_and_client(session):
    u = User(name="Artist", email="artist@example.com")
    c = Client(user_id=1, name="Client", email="c@example.com")
    session.add(u)
    session.add(c)
    session.commit()
    return u, c


def test_session_repository_crud(db_session, monkeypatch):
    # Force repository to use the same in-memory session as the test
    @contextmanager
    def _ctx():
        yield db_session

    monkeypatch.setattr("backend.repositories.session_repository.get_db_session", _ctx)
    # Seed minimal user and client rows for FKs
    u = User(name="Artist", email="artist@example.com")
    db_session.add(u)
    db_session.commit()
    c = Client(user_id=u.id, name="Client", email="c@example.com")
    db_session.add(c)
    db_session.commit()

    repo = SessionRepository()

    # Create
    s = repo.create(
        artist_id=u.id,
        client_id=c.id,
        date=__import__("datetime").date.today(),
        start_time=__import__("datetime").time(10, 0),
        end_time=__import__("datetime").time(11, 0),
        notes="test",
    )
    assert s.id is not None

    # Get
    fetched = repo.get(s.id)
    assert fetched is not None
    assert fetched.client_id == c.id

    # Update
    updated = repo.update(s.id, notes="updated")
    assert updated is not None
    assert updated.notes == "updated"

    # List
    all_sessions = repo.get_all()
    assert any(sess.id == s.id for sess in all_sessions)

    # Delete
    assert repo.delete(s.id) is True
    assert repo.get(s.id) is None
