"""Pharmacy blueprint."""
from flask import Blueprint

pharmacy_bp = Blueprint('pharmacy', __name__, template_folder='../templates/pharmacy')
from . import routes  # noqa: E402, F401
