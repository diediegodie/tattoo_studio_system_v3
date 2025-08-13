# Single declarative base for all models (SQLAlchemy 2.0 style)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
	pass

# Ensure both User and Client models are imported and registered with SQLAlchemy
from .user import User
from .client import Client
from .session import Session
