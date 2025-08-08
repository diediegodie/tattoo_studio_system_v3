
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from passlib.hash import bcrypt
import datetime

Base = declarative_base()

class User(Base):
	"""
	SQLAlchemy User model for authentication.
	"""
	__tablename__ = "users"

	id = Column(Integer, primary_key=True)
	name = Column(String(128), nullable=False)
	email = Column(String(128), unique=True, nullable=False)
	password_hash = Column(String(255), nullable=False)
	created_at = Column(DateTime, default=datetime.datetime.utcnow)

	def set_password(self, password: str):
		self.password_hash = bcrypt.hash(password)

	def check_password(self, password: str) -> bool:
		return bcrypt.verify(password, self.password_hash if isinstance(self.password_hash, str) else str(self.password_hash))
