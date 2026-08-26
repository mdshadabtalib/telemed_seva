"""Appointment routes — search, booking, management."""
from datetime import datetime, date, time as dt_time, timezone

from flask import render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import current_user, login_required

from . import appointments_bp
from ..extensions import db
from ..models.user import UserRole, DoctorProfile
from ..models.doctor import Specialty
from ..models.appointment import Appointment, AppointmentStatus
from ..models.consultation import Consultation
from ..services.appointment_service import get_available_slots, book_appointment
from ..services.notification_service import notify_appointment_booked, notify_appointment_cancelled
from ..utils.decorators import role_required
from ..utils.helpers import paginate_query


@appointments_bp.route('/search')
def search_doctors():
    """Search and filter doctors."""
    specialties = Specialty.query.filter_by(is_active=True).order_by(Specialty.name).all()

    query = DoctorProfile.query.filter_by(is_verified=True, is_available=True)

    # Filters
    specialty_id = request.args.get('specialty', type=int)
    if specialty_id:
        query = query.filter_by(specialty_id=specialty_id)

    name = request.args.get('name', '').strip()
    if name:
        query = query.filter(
            db.or_(
                DoctorProfile.first_name.ilike(f'%{name}%'),
                DoctorProfile.last_name.ilike(f'%{name}%'),
            )
        )

    max_fee = request.args.get('max_fee', type=float)
    if max_fee:
        query = query.filter(DoctorProfile.consultation_fee <= max_fee)

    language = request.args.get('language', '').strip()
    if language:
        query = query.filter(DoctorProfile.languages.ilike(f'%{language}%'))

    sort = request.args.get('sort', 'experience')
    if sort == 'fee_low':
        query = query.order_by(DoctorProfile.consultation_fee.asc())
    elif sort == 'fee_high':
        query = query.order_by(DoctorProfile.consultation_fee.desc())
    elif sort == 'experience':
        query = query.order_by(DoctorProfile.experience_years.desc())
    else:
        query = query.order_by(DoctorProfile.first_name)

    doctors = paginate_query(query, per_page=12)

    # Bulk-load rating stats to avoid N+1 queries on the list page
    DoctorProfile.load_rating_stats([d.id for d in doctors.items])

    return render_template(
        'appointments/search.html',
        title='Find a Doctor',
        doctors=doctors,
        specialties=specialties,
        filters=request.args,
    )


@appointments_bp.route('/book/<int:doctor_id>', methods=['GET', 'POST'])
@role_required(UserRole.PATIENT)
def book(doctor_id):
    """Book an appointment with a doctor."""
    doctor = DoctorProfile.query.get_or_404(doctor_id)

    if not doctor.is_verified or not doctor.is_available:
        flash('This doctor is not available for booking.', 'warning')
        return redirect(url_for('appointments.search_doctors'))

    if request.method == 'POST':
        appt_date_str = request.form.get('date')
        start_time_str = request.form.get('start_time')
        end_time_str = request.form.get('end_time')
        notes = request.form.get('notes', '').strip()

        if not all([appt_date_str, start_time_str, end_time_str]):
            flash('Please select a date and time slot.', 'danger')
            return redirect(url_for('appointments.book', doctor_id=doctor_id))

        try:
            appt_date = date.fromisoformat(appt_date_str)
            start_time = dt_time.fromisoformat(start_time_str)
            end_time = dt_time.fromisoformat(end_time_str)
        except ValueError:
            flash('Invalid date or time.', 'danger')
            return redirect(url_for('appointments.book', doctor_id=doctor_id))

        appointment, error = book_appointment(
            patient_id=current_user.id,
            doctor_profile=doctor,
            target_date=appt_date,
            start_time=start_time,
            end_time=end_time,
            patient_notes=notes,
        )

        if error:
            flash(error, 'danger')
            return redirect(url_for('appointments.book', doctor_id=doctor_id))

        # Create consultation room
        import uuid
        consultation = Consultation(
            appointment_id=appointment.id,
            room_id=uuid.uuid4().hex[:16],
        )
        db.session.add(consultation)

        notify_appointment_booked(current_user.id, doctor.user_id, appointment)
        db.session.commit()

        flash('Appointment slot reserved for 10 minutes. Please complete payment to confirm.', 'info')
        return redirect(url_for('payments.pay_appointment', appointment_id=appointment.id))

    # GET: show booking page with available dates
    selected_date_str = request.args.get('date')
    selected_date = None
    slots = []

    if selected_date_str:
        try:
            selected_date = date.fromisoformat(selected_date_str)
            if selected_date >= date.today():
                slots = get_available_slots(doctor, selected_date)
        except ValueError:
            pass

    return render_template(
        'appointments/book.html',
        title=f'Book with Dr. {doctor.full_name}',
        doctor=doctor,
        selected_date=selected_date,
        slots=slots,
    )


@appointments_bp.route('/api/slots/<int:doctor_id>/<appt_date>')
def api_slots(doctor_id, appt_date):
    """API endpoint to fetch available slots for a date (AJAX)."""
    doctor = DoctorProfile.query.get_or_404(doctor_id)
    try:
        target_date = date.fromisoformat(appt_date)
    except ValueError:
        return jsonify({'error': 'Invalid date'}), 400

    if target_date < date.today():
        return jsonify({'slots': []})

    slots = get_available_slots(doctor, target_date)
    serialised = [{
        'start': s['start'].isoformat(),
        'end': s['end'].isoformat(),
        'start_str': s['start_str'],
        'end_str': s['end_str'],
        'available': s['available'],
    } for s in slots]

    return jsonify({'slots': serialised, 'date': target_date.isoformat()})


@appointments_bp.route('/<int:appointment_id>')
@login_required
def detail(appointment_id):
    """View appointment details."""
    appointment = Appointment.query.get_or_404(appointment_id)

    # Authorization: patient or doctor of this appointment
    if current_user.role == UserRole.PATIENT and appointment.patient_id != current_user.id:
        abort(403)
    if current_user.role == UserRole.DOCTOR and appointment.doctor_id != current_user.doctor_profile.id:
        abort(403)

    return render_template(
        'appointments/detail.html',
        title=f'Appointment #{appointment.id}',
        appointment=appointment,
    )


@appointments_bp.route('/<int:appointment_id>/cancel', methods=['POST'])
@login_required
def cancel(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)

    # Authorization
    if current_user.role == UserRole.PATIENT and appointment.patient_id != current_user.id:
        abort(403)
    if current_user.role == UserRole.DOCTOR and appointment.doctor_id != current_user.doctor_profile.id:
        abort(403)

    reason = request.form.get('reason', 'Cancelled by user')
    try:
        appointment.transition_to(
            AppointmentStatus.CANCELLED,
            reason=reason,
            by_user_id=current_user.id,
        )
    except ValueError as e:
        flash(str(e), 'danger')
        return redirect(url_for('appointments.detail', appointment_id=appointment_id))

    # Notify the other party
    if current_user.id == appointment.patient_id:
        notify_appointment_cancelled(appointment.doctor.user_id, appointment)
    else:
        notify_appointment_cancelled(appointment.patient_id, appointment)

    db.session.commit()
    flash('Appointment cancelled.', 'info')
    return redirect(url_for('appointments.my_appointments'))


@appointments_bp.route('/my')
@login_required
def my_appointments():
    """List current user's appointments."""
    if current_user.role == UserRole.PATIENT:
        query = Appointment.query.filter_by(patient_id=current_user.id)
    elif current_user.role == UserRole.DOCTOR:
        query = Appointment.query.filter_by(doctor_id=current_user.doctor_profile.id)
    else:
        abort(403)

    status_filter = request.args.get('status')
    if status_filter:
        try:
            query = query.filter_by(status=AppointmentStatus(status_filter))
        except ValueError:
            pass

    appointments = paginate_query(
        query.order_by(Appointment.appointment_date.desc(), Appointment.start_time.desc()),
        per_page=15,
    )

    return render_template(
        'appointments/list.html',
        title='My Appointments',
        appointments=appointments,
        statuses=AppointmentStatus,
    )
