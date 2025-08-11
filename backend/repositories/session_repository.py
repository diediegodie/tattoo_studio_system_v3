from backend.models.session import Session
from backend.utils.database import get_db_session
from typing import Optional

class SessionRepository:
    def get(self, session_id: int) -> Optional[Session]:
            with get_db_session() as db:
                return db.query(Session).get(session_id)

    def get_all(self) -> list[Session]:
        with get_db_session() as db:
            return db.query(Session).all()

    def create(self, **kwargs) -> Session:
        with get_db_session() as db:
            session_obj = Session(**kwargs)
            db.add(session_obj)
            db.commit()
            db.refresh(session_obj)
            return session_obj

    def update(self, session_id: int, **kwargs) -> Optional[Session]:
        with get_db_session() as db:
            session_obj = db.query(Session).get(session_id)
            if session_obj is None:
                return None  # or raise an exception
            for key, value in kwargs.items():
                setattr(session_obj, key, value)
            db.commit()
            db.refresh(session_obj)
            return session_obj

    def delete(self, session_id: int) -> bool:
        with get_db_session() as db:
            session_obj = db.query(Session).get(session_id)
            if session_obj is None:
                return False  # or raise an exception
            db.delete(session_obj)
            db.commit()
            return True
