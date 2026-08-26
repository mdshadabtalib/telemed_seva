"""Appointment service and booking tests."""
from datetime import date, timedelta, time
from app.models.user import DoctorProfile
from app.models.appointment import Appointment, AppointmentStatus
from app.services.appointment_service import get_available_slots, book_appointment
from app.extensions import db


def test_slot_generation(app, doctor_user):
    """Test generating appointment slots from doctor availability."""
    with app.app_context():
        doc = DoctorProfile.query.filter_by(user_id=doctor_user).first()
        tomorrow = date.today() + timedelta(days=1)
        slots = get_available_slots(doc, tomorrow)

        # 9:00 to 17:00 with 30 min slots = 16 slots
        assert len(slots) == 16
        assert all(s['available'] is True for s in slots)


def test_book_appointment_success(app, patient_user, doctor_user):
    """Test booking an appointment."""
    with app.app_context():
        doc = DoctorProfile.query.filter_by(user_id=doctor_user).first()
        target_date = date.today() + timedelta(days=2)
        start_t = time(10, 0)
        end_t = time(10, 30)

        appt, err = book_appointment(
            patient_id=patient_user,
            doctor_profile=doc,
            target_date=target_date,
            start_time=start_t,
            end_time=end_t,
            patient_notes='Routine checkup',
        )

        assert err is None
        assert appt is not None
        assert appt.status in (AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED)
        assert appt.patient_notes == 'Routine checkup'


def test_double_booking_prevention(app, patient_user, doctor_user):
    """Test that the same slot cannot be double-booked."""
    with app.app_context():
        doc = DoctorProfile.query.filter_by(user_id=doctor_user).first()
        target_date = date.today() + timedelta(days=2)
        start_t = time(11, 0)
        end_t = time(11, 30)

        # First booking succeeds
        appt1, err1 = book_appointment(
            patient_id=patient_user,
            doctor_profile=doc,
            target_date=target_date,
            start_time=start_t,
            end_time=end_t,
        )
        assert err1 is None
        assert appt1 is not None

        # Second booking for the same slot must fail
        appt2, err2 = book_appointment(
            patient_id=patient_user,
            doctor_profile=doc,
            target_date=target_date,
            start_time=start_t,
            end_time=end_t,
        )
        assert appt2 is None
        assert 'slot is no longer available' in err2.lower()
