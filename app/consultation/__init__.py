"""Consultation blueprint."""
from flask import Blueprint

consultation_bp = Blueprint('consultation', __name__, template_folder='../templates/consultation')
from . import routes  # noqa: E402, F401
