from backend.repositories.session_repository import SessionRepository
from backend.schemas.session_schema import SessionSchema

class SessionService:
    def __init__(self):
        self.repository = SessionRepository()
        self.schema = SessionSchema()

    def get_session(self, session_id: int):
        session = self.repository.get(session_id)
        if session is None:
            return None
        return self.schema.dump(session)

    def get_all_sessions(self):
        sessions = self.repository.get_all()
        return self.schema.dump(sessions, many=True)

    def create_session(self, data: dict):
        session = self.repository.create(**data)
        return self.schema.dump(session)

    def update_session(self, session_id: int, data: dict):
        session = self.repository.update(session_id, **data)
        return self.schema.dump(session) if session else None

    def delete_session(self, session_id: int):
        self.repository.delete(session_id)
