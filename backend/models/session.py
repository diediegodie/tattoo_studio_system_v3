from sqlalchemy import Integer, ForeignKey, Date, Time, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from . import Base
from typing import TYPE_CHECKING
from datetime import date as dt_date, time as dt_time

if TYPE_CHECKING:
    from .user import User
    from .client import Client


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    artist_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), nullable=False)
    date: Mapped[dt_date] = mapped_column(Date, nullable=False)
    start_time: Mapped[dt_time] = mapped_column(Time, nullable=False)
    end_time: Mapped[dt_time] = mapped_column(Time, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)

    artist: Mapped["User"] = relationship("User", back_populates="sessions_as_artist")
    client: Mapped["Client"] = relationship("Client", back_populates="sessions_as_client")
