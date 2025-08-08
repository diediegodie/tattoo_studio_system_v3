# --- Imports and Blueprint definition ---
import os
from flask import current_app, redirect, request, session, url_for, render_template
from . import auth_bp
from .services.google_service import GoogleAuthService


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
        session["user"] = {
            "email": user_info.get("email"),
            "name": user_info.get("name"),
            "picture": user_info.get("picture"),
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
