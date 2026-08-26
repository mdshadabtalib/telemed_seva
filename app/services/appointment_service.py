"""Appointment service — slot generation, booking, conflict detection."""
from datetime import datetime, date, time, timedelta, timezone

from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError

from ..extensions import db
from ..models.appointment import Appointment, AppointmentStatus
from ..models.doctor import Availability, DayOfWeek

# How long a slot lock is held while the patient completes payment (minutes)
SLOT_LOCK_MINUTES = 10


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

    now = datetime.now(timezone.utc)

    # Booked and confirmed/pending slots
    booked = Appointment.query.filter(
        Appointment.doctor_id == doctor_profile.id,
        Appointment.appointment_date == target_date,
        Appointment.status.in_([
            AppointmentStatus.PENDING,
            AppointmentStatus.CONFIRMED,
        ]),
    ).all()
    booked_times = {(a.start_time, a.end_time) for a in booked}

    # Actively locked slots (lock not expired, slot not yet booked/paid)
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
    """Reserve an appointment slot with optimistic locking.

    The appointment is created in PENDING status with a slot lock so the
    patient can complete payment.  The slot lock prevents another patient
    from booking the same slot for SLOT_LOCK_MINUTES.

    Status transitions:
        book_appointment()   → PENDING  (slot locked)
        confirm_appointment() → CONFIRMED (after successful payment)
        cancel / timeout     → CANCELLED / lock expired (slot freed)

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

    lock_expiry = datetime.now(timezone.utc) + timedelta(minutes=SLOT_LOCK_MINUTES)

    appointment = Appointment(
        patient_id=patient_id,
        doctor_id=doctor_profile.id,
        appointment_date=target_date,
        start_time=start_time,
        end_time=end_time,
        appointment_type=appt_type,
        # Start PENDING — transitions to CONFIRMED only after payment
        status=AppointmentStatus.PENDING,
        consultation_fee=doctor_profile.consultation_fee,
        patient_notes=patient_notes,
        # Lock this slot so no-one else can book it during payment
        locked_until=lock_expiry,
        locked_by=patient_id,
    )

    try:
        db.session.add(appointment)
        db.session.flush()  # triggers unique constraint check immediately
    except IntegrityError:
        db.session.rollback()
        return None, 'This slot is no longer available. Please select another.'

    return appointment, None


def confirm_appointment(appointment):
    """Transition an appointment from PENDING to CONFIRMED after payment.

    Clears the slot lock.  Raises ValueError if the transition is invalid.
    """
    appointment.transition_to(AppointmentStatus.CONFIRMED)
    appointment.locked_until = None
    appointment.locked_by = None


def release_expired_locks():
    """Release slot locks that have passed their expiry without payment.

    This is called opportunistically — no Celery required, though a
    scheduled task would be cleaner in a larger deployment.
    """
    now = datetime.now(timezone.utc)
    expired = Appointment.query.filter(
        Appointment.status == AppointmentStatus.PENDING,
        Appointment.locked_until < now,
        Appointment.locked_by.isnot(None),
    ).all()

    for appt in expired:
        # Only cancel if the slot was locked for payment (locked_by set)
        # and payment was never completed.
        from ..models.payment import Payment, PaymentStatus
        paid = Payment.query.filter_by(
            reference_type='appointment',
            reference_id=appt.id,
        ).filter(Payment.status == PaymentStatus.COMPLETED).first()

        if not paid:
            appt.status = AppointmentStatus.CANCELLED
            appt.cancellation_reason = 'Payment not completed within the allowed time.'
            appt.locked_until = None
            appt.locked_by = None

    if expired:
        db.session.commit()
