# Removed reference to non-existent '../../frontend/pages' folder
from flask import Blueprint

# Use the correct template folder for Flask
auth_bp = Blueprint('auth', __name__, template_folder='../../frontend/templates')

# Import views at the bottom to avoid circular imports
from . import routes