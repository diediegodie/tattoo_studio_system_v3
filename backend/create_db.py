"""
Run this script once to create the users table in your SQLite database.
"""

import os
from sqlalchemy import create_engine
from backend.models.user import Base

if __name__ == "__main__":
    db_path = os.path.join(os.path.dirname(__file__), "db/tattoo_studio.db")
    engine = create_engine(f"sqlite:///{os.path.abspath(db_path)}")
    Base.metadata.create_all(engine)
    print("Database and users table created (if not already present).")
