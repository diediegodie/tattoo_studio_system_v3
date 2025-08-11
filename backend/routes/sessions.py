from flask import Blueprint, request, jsonify
from backend.services.session_service import SessionService

bp = Blueprint("sessions", __name__, url_prefix="/sessions")
session_service = SessionService()


@bp.route("/", methods=["GET"])
def list_sessions():
    return jsonify(session_service.get_all_sessions())


@bp.route("/<int:session_id>", methods=["GET"])
def get_session(session_id):
    session = session_service.get_session(session_id)
    if session is None:
        return jsonify({"error": "Session not found"}), 404
    return jsonify(session)


@bp.route("/", methods=["POST"])
def create_session():
    data = request.get_json()
    session = session_service.create_session(data)
    return jsonify(session), 201


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
