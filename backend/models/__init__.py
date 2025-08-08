# Single declarative base for all models
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# Ensure both User and Client models are imported and registered with SQLAlchemy
from .user import User
from .client import Client
