
# --- Imports and Blueprint definition ---
import os
from flask import (
    current_app,
    redirect,
    request,
    session,
    url_for,
    render_template,
    flash,
)
from . import auth_bp
from .services.google_service import GoogleAuthService
from backend.models.user import User
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import time

# --- Local Login Route ---
@auth_bp.route("/login/local", methods=["GET", "POST"])
def login_local():
    """Local (offline) login with email and password."""
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        if not all([email, password]):
            flash("Email and password are required.", "danger")
            return render_template("login_local.html")

        db_path = os.path.join(os.path.dirname(__file__), "../db/tattoo_studio.db")
        db_uri = current_app.config.get(
            "SQLALCHEMY_DATABASE_URI", f"sqlite:///{os.path.abspath(db_path)}"
        )
        engine = create_engine(db_uri)
        Session = sessionmaker(bind=engine)
        db_session = Session()
        user = db_session.query(User).filter_by(email=email).first()
        if user and password is not None and user.check_password(password):
            session["user"] = {"email": user.email, "name": user.name, "picture": None}
            # Optionally, generate a JWT for offline use
            # session["jwt_token"] = ...
            db_session.close()
            flash("Login successful!", "success")
            return redirect(url_for("auth.dashboard"))
        else:
            db_session.close()
            flash("Invalid email or password.", "danger")
            return render_template("login_local.html")
    return render_template("login_local.html")


# --- Imports and Blueprint definition ---
import os
from flask import (
    current_app,
    redirect,
    request,
    session,
    url_for,
    render_template,
    flash,
)
from . import auth_bp
from .services.google_service import GoogleAuthService
from backend.models.user import User
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine


# --- Registration Route ---
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """User registration page and handler."""
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        if not all([name, email, password]):
            flash("All fields are required.", "danger")
            return render_template("register.html")

        # Setup DB session (for demo, use SQLite file; in prod, use app config)
        db_path = os.path.join(os.path.dirname(__file__), "../db/tattoo_studio.db")
        db_uri = current_app.config.get(
            "SQLALCHEMY_DATABASE_URI", f"sqlite:///{os.path.abspath(db_path)}"
        )
        engine = create_engine(db_uri)
        Session = sessionmaker(bind=engine)
        db_session = Session()

        # Check if user exists
        if db_session.query(User).filter_by(email=email).first():
            flash("Email already registered.", "warning")
            db_session.close()
            return render_template("register.html")

        user = User(name=name, email=email)
        if password is not None:
            user.set_password(password)
        else:
            flash("Password is required.", "danger")
            db_session.close()
            return render_template("register.html")
        db_session.add(user)
        db_session.commit()
        db_session.close()
        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("auth.login"))
    return render_template("register.html")


# --- Routes ---
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
    time.sleep(1) # Remove or comment out time.sleep(1) before deploying to production.
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
            import secrets

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
