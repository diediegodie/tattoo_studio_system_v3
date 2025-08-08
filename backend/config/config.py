"""
Configuration module for the Tattoo Studio System.

This module handles all application configuration including
database settings, secret keys, and environment variables.
"""

import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration class with common settings."""

    SECRET_KEY: str = os.environ.get("FLASK_SECRET_KEY", "dev-secret-change-me")
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False

    # Database configuration
    DB_PATH: str = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "db", "tattoo_studio.db"
    )
    SQLALCHEMY_DATABASE_URI: str = f"sqlite:///{os.path.abspath(DB_PATH)}"

    # OAuth configuration
    OAUTHLIB_INSECURE_TRANSPORT: str = "1"  # For local development only

    @classmethod
    def get_database_uri(cls) -> str:
        """Get the database URI for SQLAlchemy."""
        return cls.SQLALCHEMY_DATABASE_URI

    @classmethod
    def get_secret_key(cls) -> str:
        """Get the application secret key."""
        return cls.SECRET_KEY


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG: bool = True
    TESTING: bool = False


class ProductionConfig(Config):
    """Production configuration."""

    DEBUG: bool = False
    TESTING: bool = False

    @classmethod
    def get_secret_key(cls) -> str:
        """Get the application secret key with validation."""
        secret = os.environ.get("FLASK_SECRET_KEY")
        if not secret or secret == "dev-secret-change-me":
            raise ValueError("SECRET_KEY must be set in production")
        return secret

    @classmethod
    def validate(cls) -> None:
        """Validate production configuration."""
        cls.get_secret_key()  # This will raise if invalid


class TestingConfig(Config):
    """Testing configuration."""

    DEBUG: bool = True
    TESTING: bool = True

    # Use in-memory database for testing
    SQLALCHEMY_DATABASE_URI: str = "sqlite:///:memory:"


def get_config(environment: Optional[str] = None) -> Config:
    """
    Get configuration based on environment.

    Args:
        environment: Environment name (development, production, testing)

    Returns:
        Config: Configuration instance
    """
    if environment is None:
        environment = os.environ.get("FLASK_ENV", "development")

    config_map = {
        "development": DevelopmentConfig,
        "production": ProductionConfig,
        "testing": TestingConfig,
    }

    config_class = config_map.get(environment.lower(), DevelopmentConfig)

    # Validate production config
    if environment.lower() == "production":
        config_class.validate()

    return config_class()
