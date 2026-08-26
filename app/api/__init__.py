"""REST API blueprint."""
from flask import Blueprint

api_bp = Blueprint('api', __name__)

from . import doctors, appointments, cart  # noqa: E402, F401
