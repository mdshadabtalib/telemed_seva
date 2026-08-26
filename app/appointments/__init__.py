"""Appointments blueprint."""
from flask import Blueprint

appointments_bp = Blueprint('appointments', __name__, template_folder='../templates/appointments')
from . import routes  # noqa: E402, F401
