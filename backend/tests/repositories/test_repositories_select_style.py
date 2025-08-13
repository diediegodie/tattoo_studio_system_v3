import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from backend.models import Base
from backend.models.user import User
from backend.models.client import Client
from backend.repositories.user_repository import UserRepository
from backend.repositories.client_repository import ClientRepository


@pytest.fixture
def db_session(tmp_path):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_user_repository_select_style(db_session):
    repo = UserRepository(db_session)

    # create
    u = User(name="Alice", email="alice@example.com")
    repo.save(u)
    db_session.commit()

    # get_by_id -> Session.get
    fetched = repo.get_by_id(u.id)
    assert fetched is not None
    assert fetched.email == "alice@example.com"

    # get_by_email -> select + scalars
    by_email = repo.get_by_email("alice@example.com")
    assert by_email is not None
    assert by_email.id == u.id

    # get_all -> select + scalars
    all_users = repo.get_all()
    assert isinstance(all_users, list)
    assert len(all_users) == 1


def test_client_repository_select_style(db_session):
    # Seed a user
    user_repo = UserRepository(db_session)
    user = User(name="Bob", email="bob@example.com")
    user_repo.save(user)
    db_session.commit()

    repo = ClientRepository(db_session)

    # create
    c = Client(user_id=user.id, name="John", email="john@e.com")
    repo.save(c)
    db_session.commit()

    # get_by_id -> Session.get
    fetched = repo.get_by_id(c.id)
    assert fetched is not None
    assert fetched.name == "John"

    # get_by_user -> select + where
    by_user = repo.get_by_user(user.id)
    assert len(by_user) == 1

    # get_by_id_and_user -> select + where
    by_id_user = repo.get_by_id_and_user(c.id, user.id)
    assert by_id_user is not None
    assert by_id_user.id == c.id

    # get_by_email
    by_email = repo.get_by_email("john@e.com", user.id)
    assert len(by_email) == 1

    # search_by_name
    search = repo.search_by_name("Jo", user.id)
    assert len(search) == 1
