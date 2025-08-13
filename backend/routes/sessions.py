from flask import Blueprint, request, jsonify, render_template
from backend.services.session_service import SessionService
from backend.utils.database import get_db_session
from backend.models.user import User
from backend.models.client import Client
from sqlalchemy import select

bp = Blueprint("sessions", __name__, url_prefix="/sessions")
session_service = SessionService()


@bp.route("/", methods=["GET"])
def list_sessions():
    return jsonify(session_service.get_all_sessions_for_calendar())


@bp.route("/<int:session_id>", methods=["GET"])
def get_session(session_id):
    session = session_service.get_session(session_id)
    if session is None:
        return jsonify({"error": "Session not found"}), 404
    return jsonify(session)


@bp.route("/", methods=["POST"])
def create_session():
    data = request.get_json()
    try:
        session = session_service.create_session(data or {})
        return jsonify(session), 201
    except ValueError as e:
        # Our service raises ValueError with dict payloads
        payload = e.args[0] if e.args else {"error": "Invalid data"}
        return jsonify(payload), 400


@bp.route("/<int:session_id>", methods=["PUT"])
def update_session(session_id):
    data = request.get_json()
    session = session_service.update_session(session_id, data)
    if session is None:
        return jsonify({"error": "Session not found"}), 404
    return jsonify(session)


@bp.route("/<int:session_id>", methods=["DELETE"])
def delete_session(session_id):
    session_service.delete_session(session_id)
    return "", 204


@bp.route("/calendar", methods=["GET"])
def calendar():
    return render_template("calendar.html")


@bp.route("/options", methods=["GET"])
def options():
    """Return available artists and clients for form dropdowns.

    Optional scoping: pass query param `artist_ids=1,2,3` to limit artists.
    """
    with get_db_session() as db:
        # Scope artists if requested
        artist_ids_param = request.args.get("artist_ids", "").strip()
        if artist_ids_param:
            try:
                ids = [
                    int(x) for x in artist_ids_param.split(",") if x.strip().isdigit()
                ]
            except Exception:
                ids = []
        else:
            ids = []

        if ids:
            artist_iter = db.scalars(select(User).where(User.id.in_(ids)))
        else:
            artist_iter = db.scalars(select(User))

        artists = [{"id": u.id, "name": u.name, "email": u.email} for u in artist_iter]

        clients = [
            {"id": c.id, "name": c.name, "email": c.email}
            for c in db.scalars(select(Client))
        ]
    return jsonify({"artists": artists, "clients": clients})
