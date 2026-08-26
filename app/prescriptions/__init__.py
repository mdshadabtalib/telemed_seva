"""Prescriptions blueprint."""
from flask import Blueprint

prescriptions_bp = Blueprint('prescriptions', __name__, template_folder='../templates/prescriptions')
from . import routes  # noqa: E402, F401
