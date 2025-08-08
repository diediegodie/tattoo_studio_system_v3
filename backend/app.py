from flask import Flask
import os


def create_app():
    """
    Application factory for the Tattoo Studio System.
    Returns:
        Flask: Configured Flask application instance.
    """
    app = Flask(__name__, template_folder="../frontend/templates")
    app.config["SECRET_KEY"] = os.environ.get(
        "FLASK_SECRET_KEY", "dev-secret-change-me"
    )

    # Load configuration if config.py exists
    config_path = os.path.join(os.path.dirname(__file__), "config", "config.py")
    if os.path.isfile(config_path):
        app.config.from_pyfile(config_path)

    # Register blueprints if api/ exists and has __init__.py
    api_path = os.path.join(os.path.dirname(__file__), "api")
    if os.path.isdir(api_path) and os.path.isfile(
        os.path.join(api_path, "__init__.py")
    ):
        try:
            from .api import api_bp  # type: ignore

            app.register_blueprint(api_bp)
        except ImportError:
            pass  # No blueprint yet, skip

    # Register auth blueprint if available (must be before main_bp)
    auth_path = os.path.join(os.path.dirname(__file__), "auth")
    if os.path.isdir(auth_path) and os.path.isfile(
        os.path.join(auth_path, "__init__.py")
    ):
        try:
            from .auth import auth_bp  # type: ignore

            app.register_blueprint(auth_bp, url_prefix="/auth")
        except Exception as e:
            pass

    # Register main blueprint for frontend pages
    from flask import Blueprint, render_template, redirect, url_for

    main_bp = Blueprint("main", __name__)

    @main_bp.route("/")
    def index():
        return render_template("index.html")

    @main_bp.route("/login")
    def login_redirect():
        return redirect(url_for("auth.login"))

    @main_bp.route("/register")
    def register():
        # Placeholder for future registration page
        return "Registration coming soon!"

    app.register_blueprint(main_bp)

    # ...existing code...
    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
