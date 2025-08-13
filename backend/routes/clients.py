"""
Client routes implementing HTTP request/response handling.

This module follows SOLID principles by:
- Single Responsibility: Only handles HTTP layer concerns
- Dependency Inversion: Uses service layer abstractions
- Interface Segregation: Clean separation of concerns
"""

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    jsonify,
)
from typing import Optional
from ..services.client_service import ClientService
from ..utils.database import get_db_session
from ..repositories.user_repository import UserRepository
from ..models.user import User
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from flask import current_app
from ..services.jotform_service import JotFormService
import logging

logger = logging.getLogger(__name__)

clients_bp = Blueprint("clients", __name__, url_prefix="/clients")


def get_current_user_id() -> Optional[str]:
    """
    Get current user ID from session.

    Returns:
        Optional[str]: User email if logged in, None otherwise
    """
    try:
        return session.get("user", {}).get("email")
    except Exception as e:
        logger.error(f"Error getting current user ID: {e}")
        return None


def get_current_user(db_session) -> Optional[User]:
    """
    Get current user object from database.

    Args:
        db_session: Database session

    Returns:
        Optional[User]: User object if found, None otherwise
    """
    try:
        user_email = get_current_user_id()
        if not user_email:
            return None

        user_repo = UserRepository(db_session)
        return user_repo.get_by_email(user_email)
    except Exception as e:
        logger.error(f"Error getting current user: {e}")
        return None


def require_authentication(f):
    """
    Decorator to require user authentication.

    Args:
        f: Function to wrap

    Returns:
        Wrapped function that redirects to login if not authenticated
    """

    def wrapper(*args, **kwargs):
        if not get_current_user_id():
            flash("Por favor, faça login para acessar esta página.", "warning")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)

    wrapper.__name__ = f.__name__
    return wrapper


@clients_bp.route("/", methods=["GET"])
@require_authentication
def list_clients():
    """
    List all clients for the current user.

    Returns:
        Rendered template with clients list
    """
    try:
        with get_db_session() as db_session:
            user = get_current_user(db_session)

            if not user:
                flash("Usuário não encontrado.", "danger")
                return redirect(url_for("auth.login"))

            client_service = ClientService(db_session)
            clients = client_service.get_all_clients(user.id)

            logger.info(f"Retrieved {len(clients)} clients for user {user.id}")
            return render_template("clients_list.html", clients=clients)

    except Exception as e:
        logger.error(f"Error listing clients: {e}")
        flash("Erro ao carregar lista de clientes.", "danger")
        return redirect(url_for("main.index"))


@clients_bp.route("/new", methods=["GET", "POST"])
@require_authentication
def new_client():
    """
    Create a new client.

    GET: Show client creation form
    POST: Process client creation

    Returns:
        Rendered template or redirect
    """
    try:
        with get_db_session() as db_session:
            user = get_current_user(db_session)

            if not user:
                flash("Usuário não encontrado.", "danger")
                return redirect(url_for("auth.login"))

            if request.method == "POST":
                return _handle_client_creation(db_session, user)

            # GET request - show form
            return render_template("client_form.html", client=None)

    except Exception as e:
        logger.error(f"Error in new_client: {e}")
        flash("Erro ao criar cliente.", "danger")
        return redirect(url_for("clients.list_clients"))


def _handle_client_creation(db_session, user):
    """
    Handle POST request for client creation.

    Args:
        db_session: Database session
        user: Current user object

    Returns:
        Redirect response
    """
    try:
        # Get form data
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        notes = request.form.get("notes", "").strip()

        # Validate required fields
        if not name or not email:
            flash("Nome e email são obrigatórios.", "danger")
            return render_template("client_form.html", client=None)

        # Create client using service
        client_service = ClientService(db_session)
        client = client_service.create_client(
            user_id=user.id, name=name, email=email, phone=phone, notes=notes
        )

        if client:
            flash("Cliente criado com sucesso!", "success")
            logger.info(f"Client {client.id} created for user {user.id}")
        else:
            flash("Erro ao criar cliente.", "danger")

        return redirect(url_for("clients.list_clients"))

    except Exception as e:
        logger.error(f"Error creating client: {e}")
        flash("Erro ao criar cliente.", "danger")
        return redirect(url_for("clients.list_clients"))


def _handle_client_update(db_session, user, client_id: int):
    """
    Handle POST request for client update.

    Args:
        db_session: Database session
        user: Current user object
        client_id: Client ID to update

    Returns:
        Redirect response
    """
    try:
        # Get form data
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        notes = request.form.get("notes", "").strip()

        # Validate required fields
        if not name or not email:
            flash("Nome e email são obrigatórios.", "danger")
            return redirect(url_for("clients.edit_client", client_id=client_id))

        # Update client using service
        client_service = ClientService(db_session)
        client = client_service.update_client(
            client_id=client_id,
            user_id=user.id,
            name=name,
            email=email,
            phone=phone,
            notes=notes,
        )

        if client:
            flash("Cliente atualizado com sucesso!", "success")
            logger.info(f"Client {client_id} updated for user {user.id}")
        else:
            flash("Erro ao atualizar cliente.", "danger")

        return redirect(url_for("clients.list_clients"))

    except Exception as e:
        logger.error(f"Error updating client {client_id}: {e}")
        flash("Erro ao atualizar cliente.", "danger")
        return redirect(url_for("clients.list_clients"))


@clients_bp.route("/<int:client_id>/delete", methods=["POST"])
@require_authentication
def delete_client(client_id: int):
    """
    Delete a client.

    Args:
        client_id: Client ID to delete

    Returns:
        Redirect response
    """
    try:
        with get_db_session() as db_session:
            user = get_current_user(db_session)

            if not user:
                flash("Usuário não encontrado.", "danger")
                return redirect(url_for("auth.login"))

            client_service = ClientService(db_session)
            success = client_service.delete_client(client_id, user.id)

            if success:
                flash("Cliente excluído com sucesso!", "success")
                logger.info(f"Client {client_id} deleted for user {user.id}")
            else:
                flash("Cliente não encontrado.", "warning")

            return redirect(url_for("clients.list_clients"))

    except Exception as e:
        logger.error(f"Error deleting client {client_id}: {e}")
        flash("Erro ao excluir cliente.", "danger")
        return redirect(url_for("clients.list_clients"))


@clients_bp.route("/search", methods=["GET"])
@require_authentication
def search_clients():
    """
    Search clients by name or email.

    Returns:
        JSON response with search results
    """
    try:
        search_term = request.args.get("q", "").strip()

        if not search_term:
            return jsonify({"clients": []})

        with get_db_session() as db_session:
            user = get_current_user(db_session)

            if not user:
                return jsonify({"error": "User not authenticated"}), 401

            client_service = ClientService(db_session)
            clients = client_service.search_clients(user.id, search_term)

            # Convert clients to dict for JSON response
            clients_data = [
                {
                    "id": client.id,
                    "name": client.name,
                    "email": client.email,
                    "phone": client.phone,
                    "notes": client.notes,
                }
                for client in clients
            ]

            return jsonify({"clients": clients_data})

    except Exception as e:
        logger.error(f"Error searching clients: {e}")
        return jsonify({"error": "Search failed"}), 500


@clients_bp.route("/sync_jotform", methods=["GET"])
@require_authentication
def sync_jotform_clients():
    """
    Fetch clients from JotForm and display them in the main client list template.
    """
    try:
        db_path = os.path.join(os.path.dirname(__file__), "../db/tattoo_studio.db")
        db_uri = current_app.config.get(
            "SQLALCHEMY_DATABASE_URI", f"sqlite:///{os.path.abspath(db_path)}"
        )
        engine = create_engine(db_uri)
        Session = sessionmaker(bind=engine)
        db_session = Session()
        user_email = get_current_user_id()
        from sqlalchemy import select

        user = db_session.scalars(select(User).where(User.email == user_email)).first()
        jotform_api_key = user.jotform_api_key if user is not None else None
        clients = []
        error = None
        if (
            jotform_api_key is not None
            and isinstance(jotform_api_key, str)
            and jotform_api_key.strip()
        ):
            jotform_service = JotFormService(jotform_api_key)
            clients = jotform_service.get_clients_from_first_form()
            if clients is None:
                error = "Erro ao buscar clientes do JotForm. Verifique sua chave API e conexão."
        else:
            error = "Nenhuma chave de API JotForm salva para este usuário."
        db_session.close()
        return render_template("clients_list.html", clients=clients, error=error)
    except Exception as e:
        logger.error(f"Error syncing JotForm clients: {e}")
        return render_template(
            "clients_list.html", clients=[], error="Erro ao sincronizar com JotForm."
        )


# Error handlers for the blueprint
@clients_bp.errorhandler(404)
def not_found(error):
    """Handle 404 errors in clients blueprint."""
    flash("Página não encontrada.", "warning")
    return redirect(url_for("clients.list_clients"))


@clients_bp.route("/<int:client_id>/edit", methods=["GET", "POST"])
@require_authentication
def edit_client(client_id: int):
    """
    Edit an existing client (GET shows form, POST updates).

    Args:
        client_id: Client ID to edit

    Returns:
        Rendered template or redirect
    """
    try:
        with get_db_session() as db_session:
            user = get_current_user(db_session)

            if not user:
                flash("Usuário não encontrado.", "danger")
                return redirect(url_for("auth.login"))

            if request.method == "POST":
                return _handle_client_update(db_session, user, client_id)

            client_service = ClientService(db_session)
            client = client_service.get_client_by_id(client_id, user.id)
            if not client:
                flash("Cliente não encontrado.", "warning")
                return redirect(url_for("clients.list_clients"))

            return render_template("client_form.html", client=client)
    except Exception as e:
        logger.error(f"Error editing client {client_id}: {e}")
        flash("Erro ao carregar cliente.", "danger")
        return redirect(url_for("clients.list_clients"))


@clients_bp.errorhandler(500)
def internal_error(error):
    """Handle 500 errors in clients blueprint."""
    logger.error(f"Internal error in clients blueprint: {error}")
    flash("Erro interno do sistema.", "danger")
    return redirect(url_for("clients.list_clients"))
