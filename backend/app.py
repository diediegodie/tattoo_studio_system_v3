"""
Application factory for the Tattoo Studio System.

This module creates and configures the Flask application following
SOLID principles and dependency injection patterns.
"""

import os
import logging
from typing import Optional

# Allow OAuth over HTTP for local development
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

from flask import Flask, Blueprint, render_template, redirect, url_for
from .config.config import get_config
from .utils.database import init_database_manager
from backend.models import User, Client


def create_app(environment: Optional[str] = None) -> Flask:
    """
    Application factory for the Tattoo Studio System.

    Args:
        environment: Environment name (development, production, testing)

    Returns:
        Flask: Configured Flask application instance.
    """
    app = Flask(__name__, template_folder="../frontend/templates")

    # Load configuration
    config = get_config(environment)
    app.config.from_object(config)

    # Configure logging
    _configure_logging(app)

    # Initialize database manager
    init_database_manager(config.get_database_uri())

    # Initialize service container
    from .utils.service_container import init_services

    init_services()

    # Register blueprints
    _register_blueprints(app)  # Register error handlers
    _register_error_handlers(app)

    return app


def _configure_logging(app: Flask) -> None:
    """
    Configure application logging.

    Args:
        app: Flask application instance
    """
    import logging

    # Set log level based on debug mode
    log_level = logging.DEBUG if app.debug else logging.INFO

    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Set Flask app logger
    app.logger.setLevel(log_level)

    if not app.debug:
        # In production, log to file
        import logging.handlers

        file_handler = logging.handlers.RotatingFileHandler(
            "tattoo_studio.log", maxBytes=10240000, backupCount=10
        )
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
            )
        )
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)


def _register_blueprints(app: Flask) -> None:
    """
    Register all application blueprints.

    Args:
        app: Flask application instance
    """
    # Register clients blueprint
    try:
        from .routes.clients import clients_bp

        app.register_blueprint(clients_bp)
        app.logger.info("Clients blueprint registered successfully")
    except ImportError as e:
        app.logger.warning(f"Could not register clients blueprint: {e}")

    # Register auth blueprint if available
    auth_path = os.path.join(os.path.dirname(__file__), "auth")
    if os.path.isdir(auth_path) and os.path.isfile(
        os.path.join(auth_path, "__init__.py")
    ):
        try:
            from .auth import auth_bp  # type: ignore

            app.register_blueprint(auth_bp, url_prefix="/auth")
            app.logger.info("Auth blueprint registered successfully")
        except ImportError as e:
            app.logger.warning(f"Could not register auth blueprint: {e}")

    # Register API blueprint if available
    api_path = os.path.join(os.path.dirname(__file__), "api")
    if os.path.isdir(api_path) and os.path.isfile(
        os.path.join(api_path, "__init__.py")
    ):
        try:
            from .api import api_bp  # type: ignore

            app.register_blueprint(api_bp, url_prefix="/api")
            app.logger.info("API blueprint registered successfully")
        except ImportError as e:
            app.logger.warning(f"Could not register API blueprint: {e}")

    # Register main blueprint for frontend pages
    main_bp = _create_main_blueprint()
    app.register_blueprint(main_bp)
    app.logger.info("Main blueprint registered successfully")


def _create_main_blueprint() -> Blueprint:
    """
    Create main blueprint for frontend pages.

    Returns:
        Blueprint: Main blueprint
    """
    main_bp = Blueprint("main", __name__)

    @main_bp.route("/")
    def index():
        """Home page route."""
        return render_template("index.html")

    @main_bp.route("/login")
    def login_redirect():
        """Redirect to login page."""
        return redirect(url_for("auth.login"))

    @main_bp.route("/health")
    def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "message": "Tattoo Studio System is running"}

    return main_bp


def _register_error_handlers(app: Flask) -> None:
    """
    Register global error handlers.

    Args:
        app: Flask application instance
    """

    @app.errorhandler(404)
    def not_found_error(error):
        """Handle 404 errors."""
        app.logger.warning(f"404 error: {error}")
        return (
            render_template(
                "error.html", error_code=404, error_message="Página não encontrada"
            ),
            404,
        )

    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors."""
        app.logger.error(f"500 error: {error}")
        return (
            render_template(
                "error.html", error_code=500, error_message="Erro interno do servidor"
            ),
            500,
        )

    @app.errorhandler(Exception)
    def handle_exception(error):
        """Handle unhandled exceptions."""
        app.logger.error(f"Unhandled exception: {error}", exc_info=True)
        return (
            render_template(
                "error.html", error_code=500, error_message="Erro interno do servidor"
            ),
            500,
        )


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
