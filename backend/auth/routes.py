"""
Authentication routes for the Tattoo Studio System.

This module provides Google OAuth authentication functionality only.
Local authentication has been removed.
"""

import os
import secrets
from flask import (
    Blueprint,
    current_app,
    redirect,
    request,
    session,
    url_for,
    render_template,
    flash,
)
from functools import wraps
from .services.google_service import GoogleAuthService
from backend.models.user import User
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

# Ensure Blueprint is defined
try:
    from . import auth_bp
except ImportError:
    auth_bp = Blueprint("auth", __name__)


# --- Login Required Decorator ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)

    return decorated_function




# --- JotForm API Key Connect Route ---
@auth_bp.route("/jotform/connect", methods=["GET", "POST"])
@login_required
def connect_jotform():
    db_path = os.path.join(os.path.dirname(__file__), "../db/tattoo_studio.db")
    db_uri = current_app.config.get(
        "SQLALCHEMY_DATABASE_URI", f"sqlite:///{os.path.abspath(db_path)}"
    )
    engine = create_engine(db_uri)
    Session = sessionmaker(bind=engine)
    db_session = Session()
    user_email = session["user"]["email"]
    user = db_session.query(User).filter_by(email=user_email).first()
    jotform_api_key = user.jotform_api_key if user else None
    if request.method == "POST":
        api_key = request.form.get("jotform_api_key")
        if user and api_key:
            # Direct assignment to the column
            setattr(user, "jotform_api_key", api_key)
            db_session.commit()
            flash("JotForm API Key salva com sucesso!", "success")
            db_session.close()
            return redirect(url_for("auth.client_management"))
        flash("Erro ao salvar a chave.", "danger")
    db_session.close()
    return render_template("jotform_connect.html", jotform_api_key=jotform_api_key)


# --- Authentication Routes ---
@auth_bp.route("/login")
def login():
    """Entry point for authentication login (Google OAuth)."""
    # Redirect to the Google OAuth login flow
    return redirect(url_for("auth.login_google"))


@auth_bp.route("/login/google")
def login_google():
    """Google login route (actual OAuth flow)."""
    client_secret_path = os.path.join(os.path.dirname(__file__), "client_secret.json")
    client_id = os.environ.get("GOOGLE_CLIENT_ID")
    if not client_id:
        raise RuntimeError("GOOGLE_CLIENT_ID environment variable is not set")
    service = GoogleAuthService(
        client_secret_path=client_secret_path,
        redirect_uri=url_for("auth.callback", _external=True),
        scopes=[
            "openid",
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile",
            "https://www.googleapis.com/auth/calendar",
        ],
        client_id=client_id,
        jwt_secret=current_app.config["SECRET_KEY"],
    )
    auth_url, state = service.get_authorization_url()
    session["flow_state"] = state
    return redirect(auth_url)


@auth_bp.route("/login/google/callback")
def callback():
    """Google OAuth callback route"""
    client_secret_path = os.path.join(os.path.dirname(__file__), "client_secret.json")
    client_id = os.environ.get("GOOGLE_CLIENT_ID")
    if not client_id:
        raise RuntimeError("GOOGLE_CLIENT_ID environment variable is not set")
    service = GoogleAuthService(
        client_secret_path=client_secret_path,
        redirect_uri=url_for("auth.callback", _external=True),
        scopes=[
            "openid",
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile",
            "https://www.googleapis.com/auth/calendar",
        ],
        client_id=client_id,
        jwt_secret=current_app.config["SECRET_KEY"],
    )
    try:
        credentials = service.get_credentials_from_callback(request.url)
        session["credentials"] = credentials
        id_token_value = credentials.get("id_token")
        if not id_token_value:
            return "Error: ID token not found in credentials", 400
        user_info = service.verify_id_token(id_token_value)

        # --- Link Google login to local user table ---
        db_path = os.path.join(os.path.dirname(__file__), "../db/tattoo_studio.db")
        db_uri = current_app.config.get(
            "SQLALCHEMY_DATABASE_URI", f"sqlite:///{os.path.abspath(db_path)}"
        )
        engine = create_engine(db_uri)
        Session = sessionmaker(bind=engine)
        db_session = Session()
        email = user_info.get("email")
        name = user_info.get("name")
        picture = user_info.get("picture")
        user = db_session.query(User).filter_by(email=email).first()
        if not user:
            # Create new user with Google info, set a random password (not used for Google login)
            user = User(name=name or email, email=email)
            user.set_password(secrets.token_urlsafe(16))
            db_session.add(user)
            db_session.commit()
        else:
            # Optionally update name if changed
            if name and user.name != name:
                user.name = name
                db_session.commit()
        db_session.close()

        session["user"] = {
            "email": email,
            "name": name,
            "picture": picture,
        }
        jwt_token = service.create_jwt_token(user_info)
        session["jwt_token"] = jwt_token
        return redirect(url_for("auth.dashboard"))
    except Exception as e:
        current_app.logger.error(f"OAuth error: {str(e)}")
        return f"Authentication error: {str(e)}", 400


@auth_bp.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("auth.login"))
    return render_template("dashboard.html", user=session["user"])


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))



me = "all_in"
you = "missing_in_action"

if me and you:
    print("Could be us, but you're busy ignoring me.")
else:
    print("404: relationship not found.")
