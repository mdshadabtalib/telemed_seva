"""Appointment service — slot generation, booking, conflict detection."""
from datetime import datetime, date, time, timedelta, timezone

from sqlalchemy import and_

from ..extensions import db
from ..models.appointment import Appointment, AppointmentStatus
from ..models.doctor import Availability, DayOfWeek


def get_available_slots(doctor_profile, target_date):
    """Generate available time slots for a doctor on a given date.

    Returns a list of dicts: [{'start': time, 'end': time, 'available': bool}]
    """
    day_of_week = DayOfWeek(target_date.weekday())

    availabilities = Availability.query.filter_by(
        doctor_id=doctor_profile.id,
        day_of_week=day_of_week,
        is_active=True,
    ).all()

    if not availabilities:
        return []

    # Get already booked slots for this doctor on this date
    booked = Appointment.query.filter(
        Appointment.doctor_id == doctor_profile.id,
        Appointment.appointment_date == target_date,
        Appointment.status.in_([
            AppointmentStatus.PENDING,
            AppointmentStatus.CONFIRMED,
        ]),
    ).all()
    booked_times = {(a.start_time, a.end_time) for a in booked}

    # Also check locked (not expired) slots
    now = datetime.now(timezone.utc)
    locked = Appointment.query.filter(
        Appointment.doctor_id == doctor_profile.id,
        Appointment.appointment_date == target_date,
        Appointment.locked_until > now,
        Appointment.status == AppointmentStatus.PENDING,
    ).all()
    locked_times = {(a.start_time, a.end_time) for a in locked}

    slots = []
    for avail in availabilities:
        duration = timedelta(minutes=avail.slot_duration or 30)
        current = datetime.combine(target_date, avail.start_time)
        end_boundary = datetime.combine(target_date, avail.end_time)

        while current + duration <= end_boundary:
            slot_start = current.time()
            slot_end = (current + duration).time()

            is_booked = (slot_start, slot_end) in booked_times
            is_locked = (slot_start, slot_end) in locked_times

            # Don't show past slots for today
            is_past = False
            if target_date == date.today():
                slot_dt = datetime.combine(target_date, slot_start).replace(tzinfo=timezone.utc)
                if slot_dt <= now:
                    is_past = True

            slots.append({
                'start': slot_start,
                'end': slot_end,
                'available': not is_booked and not is_locked and not is_past,
                'start_str': slot_start.strftime('%I:%M %p'),
                'end_str': slot_end.strftime('%I:%M %p'),
            })
            current += duration

    return sorted(slots, key=lambda s: s['start'])


def book_appointment(patient_id, doctor_profile, target_date, start_time, end_time,
                     appointment_type='video', patient_notes=None):
    """Book an appointment with double-booking prevention.

    Uses database unique constraint + optimistic approach.
    Returns (appointment, error_message).
    """
    # Validate date is not in the past
    if target_date < date.today():
        return None, 'Cannot book appointments in the past.'

    # Validate doctor is verified and available
    if not doctor_profile.is_verified:
        return None, 'This doctor is not yet verified.'
    if not doctor_profile.is_available:
        return None, 'This doctor is currently unavailable.'

    from ..models.appointment import AppointmentType
    try:
        appt_type = AppointmentType(appointment_type)
    except ValueError:
        appt_type = AppointmentType.VIDEO

    appointment = Appointment(
        patient_id=patient_id,
        doctor_id=doctor_profile.id,
        appointment_date=target_date,
        start_time=start_time,
        end_time=end_time,
        appointment_type=appt_type,
        status=AppointmentStatus.CONFIRMED,
        consultation_fee=doctor_profile.consultation_fee,
        patient_notes=patient_notes,
    )

    try:
        db.session.add(appointment)
        db.session.flush()  # triggers unique constraint check
    except Exception:
        db.session.rollback()
        return None, 'This slot is no longer available. Please select another.'

    return appointment, None
