from flask import Flask
import os

def create_app():
    """
    Application factory for the Tattoo Studio System.
    Returns:
        Flask: Configured Flask application instance.
    """
    app = Flask(__name__)

    # Load configuration if config.py exists
    config_path = os.path.join(os.path.dirname(__file__), "config", "config.py")
    if os.path.isfile(config_path):
        app.config.from_pyfile(config_path)

    # Register blueprints if api/ exists and has __init__.py
    api_path = os.path.join(os.path.dirname(__file__), "api")
    if os.path.isdir(api_path) and os.path.isfile(os.path.join(api_path, "__init__.py")):
        try:
            from .api import api_bp  # type: ignore
            app.register_blueprint(api_bp)
        except ImportError:
            pass  # No blueprint yet, skip

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)