"""API — Appointment endpoints."""
from datetime import date

from flask import jsonify, request
from flask_login import current_user, login_required

from . import api_bp
from ..models.user import DoctorProfile
from ..services.appointment_service import get_available_slots


@api_bp.route('/appointments/slots/<int:doctor_id>')
def api_appointment_slots(doctor_id):
    """Get available slots for a doctor on a given date."""
    doctor = DoctorProfile.query.get_or_404(doctor_id)
    date_str = request.args.get('date')

    if not date_str:
        return jsonify({'error': 'date parameter required'}), 400

    try:
        target_date = date.fromisoformat(date_str)
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD.'}), 400

    if target_date < date.today():
        return jsonify({'slots': [], 'date': date_str})

    slots = get_available_slots(doctor, target_date)
    return jsonify({
        'slots': [{
            'start': s['start'].isoformat(),
            'end': s['end'].isoformat(),
            'start_str': s['start_str'],
            'end_str': s['end_str'],
            'available': s['available'],
        } for s in slots],
        'date': date_str,
    })
