from sqlalchemy import Column, Integer, ForeignKey, Date, Time, Text
from sqlalchemy.orm import relationship
from . import Base


class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    artist_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    notes = Column(Text)

    artist = relationship("User", back_populates="sessions_as_artist")
    client = relationship("Client", back_populates="sessions_as_client")
