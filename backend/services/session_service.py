from backend.repositories.session_repository import SessionRepository
from backend.schemas.session_schema import SessionSchema
from backend.models.client import Client
from backend.models.user import User
from backend.models.session import Session
from backend.utils.database import get_db_session
from datetime import datetime, time as dt_time
from typing import Any, Dict, List, Optional, cast
from marshmallow.exceptions import ValidationError as MMValidationError
from sqlalchemy import select


class SessionService:
    def __init__(self):
        self.repository = SessionRepository()
        self.schema = SessionSchema()

    def get_session(self, session_id: int) -> Optional[Dict[str, Any]]:
        session = self.repository.get(session_id)
        if session is None:
            return None
        return cast(Dict[str, Any], self.schema.dump(session))

    def get_all_sessions(self) -> List[Dict[str, Any]]:
        sessions = self.repository.get_all()
        return cast(List[Dict[str, Any]], self.schema.dump(sessions, many=True))

    def get_all_sessions_for_calendar(self) -> List[Dict[str, Any]]:
        sessions = self.repository.get_all()
        events: List[Dict[str, Any]] = []
        with get_db_session() as db:
            for session in sessions:
                client = db.get(Client, session.client_id)
                client_name = client.name if client else "Unknown Client"
                start_datetime = datetime.combine(session.date, session.start_time)
                end_datetime = datetime.combine(session.date, session.end_time)
                events.append(
                    {
                        "title": f"Tattoo with {client_name}",
                        "start": start_datetime.isoformat(),
                        "end": end_datetime.isoformat(),
                        "id": session.id,
                    }
                )
        return events

    def create_session(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new session with validation.

        Validates payload fields, time ranges, entity existence, and
        overlapping sessions for the same artist on the same date.

        Args:
            data: Raw request data (may contain strings for date/time)

        Returns:
            dict: Serialized session on success

        Raises:
            ValueError: When validation fails
        """
        # 1) Parse and basic-validate with Marshmallow (casts date/time)
        try:
            loaded = cast(Dict[str, Any], self.schema.load(data))
        except MMValidationError as e:
            raise ValueError({"field_errors": e.messages})

        # 2) Time integrity: end must be after start
        start_time: dt_time = loaded["start_time"]
        end_time: dt_time = loaded["end_time"]
        if end_time <= start_time:
            raise ValueError({"error": "End time must be after start time."})

        # 3) Existence checks for foreign keys
        with get_db_session() as db:
            artist = db.get(User, loaded["artist_id"])  # type: ignore[index]
            if artist is None:
                raise ValueError({"error": "Artist not found."})

            client = db.get(Client, loaded["client_id"])  # type: ignore[index]
            if client is None:
                raise ValueError({"error": "Client not found."})

            # 4) Overlap detection for same artist & date
            stmt = select(Session).where(
                (Session.artist_id == loaded["artist_id"])
                & (Session.date == loaded["date"])
                &
                # Overlap condition: start < existing.end and end > existing.start
                (Session.start_time < end_time)
                & (Session.end_time > start_time)
            )
            conflict = db.scalars(stmt).first()
            if conflict is not None:
                raise ValueError(
                    {
                        "error": "Scheduling conflict: artist already has a session in this time range.",
                        "conflict_session_id": conflict.id,
                    }
                )

        # 5) Persist
        session = self.repository.create(**loaded)
        return cast(Dict[str, Any], self.schema.dump(session))

    def update_session(
        self, session_id: int, data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        session = self.repository.update(session_id, **data)
        return cast(Dict[str, Any], self.schema.dump(session)) if session else None

    def delete_session(self, session_id: int) -> None:
        self.repository.delete(session_id)
