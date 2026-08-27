"""Doctor routes — dashboard, profile, verification, availability, public profile."""
from datetime import datetime, timezone

from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import current_user, login_required

from . import doctor_bp
from ..extensions import db
from ..models.user import UserRole, DoctorProfile
from ..models.doctor import (
    DoctorVerification, VerificationStatus, Specialty, Availability, DayOfWeek,
)
from ..models.appointment import Appointment, AppointmentStatus
from ..models.review import Review
from ..utils.decorators import role_required, verified_doctor_required
from ..utils.helpers import save_upload, paginate_query
from ..utils.forms import DoctorProfileForm, AvailabilityForm


@doctor_bp.route('/dashboard')
@role_required(UserRole.DOCTOR)
def dashboard():
    profile = current_user.doctor_profile
    today_appointments = Appointment.query.filter(
        Appointment.doctor_id == profile.id,
        Appointment.appointment_date == datetime.now(timezone.utc).date(),
        Appointment.status.in_([AppointmentStatus.CONFIRMED, AppointmentStatus.PENDING]),
    ).order_by(Appointment.start_time).all()

    total_appointments = Appointment.query.filter_by(doctor_id=profile.id).count()
    completed = Appointment.query.filter_by(
        doctor_id=profile.id, status=AppointmentStatus.COMPLETED
    ).count()

    return render_template(
        'doctor/dashboard.html',
        title='Doctor Dashboard',
        profile=profile,
        today_appointments=today_appointments,
        total_appointments=total_appointments,
        completed_consultations=completed,
    )


@doctor_bp.route('/profile', methods=['GET', 'POST'])
@role_required(UserRole.DOCTOR)
def profile():
    p = current_user.doctor_profile
    form = DoctorProfileForm(obj=p)
    
    # Populate specialty choices
    from ..models.doctor import Specialty
    specialties = Specialty.query.filter_by(is_active=True).order_by(Specialty.name).all()
    form.specialty_id.choices = [('', 'Select Specialty...')] + [(s.id, s.name) for s in specialties]

    if form.validate_on_submit():
        p.first_name          = form.first_name.data.strip()
        p.last_name           = form.last_name.data.strip()
        p.phone               = form.phone.data.strip() if form.phone.data else None
        p.bio                 = form.bio.data.strip() if form.bio.data else None
        p.qualifications      = form.qualifications.data.strip() if form.qualifications.data else None
        p.registration_number = form.registration_number.data.strip() if form.registration_number.data else None
        p.languages           = form.languages.data.strip() if form.languages.data else None
        p.experience_years    = form.experience_years.data or 0
        p.consultation_fee    = form.consultation_fee.data or 0
        p.consultation_duration = form.consultation_duration.data or 30
        if form.specialty_id.data:
            p.specialty_id = form.specialty_id.data

        if form.avatar.data:
            filename = save_upload(form.avatar.data, 'avatars',
                                   allowed_extensions={'png', 'jpg', 'jpeg', 'webp'})
            if filename:
                p.avatar = filename

        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('doctor.profile'))

    return render_template(
        'doctor/profile.html', title='Doctor Profile',
        profile=p, form=form,
    )


@doctor_bp.route('/verification', methods=['GET', 'POST'])
@role_required(UserRole.DOCTOR)
def verification():
    p = current_user.doctor_profile
    v = p.verification

    if request.method == 'POST':
        if v and v.status == VerificationStatus.APPROVED:
            flash('You are already verified.', 'info')
            return redirect(url_for('doctor.verification'))

        # Save uploaded documents
        license_doc = request.files.get('medical_license')
        id_doc = request.files.get('id_proof')
        degree_doc = request.files.get('degree_certificate')

        if not license_doc or not license_doc.filename:
            flash('Medical license document is required.', 'danger')
            return redirect(url_for('doctor.verification'))

        license_name = save_upload(license_doc, 'documents')
        id_name = save_upload(id_doc, 'documents') if id_doc and id_doc.filename else None
        degree_name = save_upload(degree_doc, 'documents') if degree_doc and degree_doc.filename else None

        if v:
            v.medical_license_doc = license_name or v.medical_license_doc
            v.id_proof_doc = id_name or v.id_proof_doc
            v.degree_certificate_doc = degree_name or v.degree_certificate_doc
            v.status = VerificationStatus.PENDING
            v.submitted_at = datetime.now(timezone.utc)
            v.rejection_reason = None
        else:
            v = DoctorVerification(
                doctor_id=p.id,
                medical_license_doc=license_name,
                id_proof_doc=id_name,
                degree_certificate_doc=degree_name,
            )
            db.session.add(v)

        db.session.commit()
        flash('Verification documents submitted. An admin will review them.', 'success')
        return redirect(url_for('doctor.verification'))

    return render_template(
        'doctor/verification.html', title='Verification', profile=p, verification=v,
    )


@doctor_bp.route('/availability', methods=['GET', 'POST'])
@role_required(UserRole.DOCTOR)
def availability():
    p = current_user.doctor_profile
    form = AvailabilityForm()

    # Pre-populate slot_duration default from doctor profile
    if request.method == 'GET':
        form.slot_duration.data = p.consultation_duration or 30

    if form.validate_on_submit():
        day_enum      = DayOfWeek(form.day_of_week.data)
        start_time    = form.start_time.data
        end_time      = form.end_time.data
        slot_duration = form.slot_duration.data

        existing = Availability.query.filter_by(
            doctor_id=p.id, day_of_week=day_enum, start_time=start_time
        ).first()

        if existing:
            existing.end_time      = end_time
            existing.slot_duration = slot_duration
            existing.is_active     = True
            flash('Availability slot updated.', 'success')
        else:
            avail = Availability(
                doctor_id=p.id,
                day_of_week=day_enum,
                start_time=start_time,
                end_time=end_time,
                slot_duration=slot_duration,
            )
            db.session.add(avail)
            flash('Availability slot added.', 'success')

        db.session.commit()
        return redirect(url_for('doctor.availability'))

    # Group slots by day for the weekly calendar view
    all_slots = Availability.query.filter_by(doctor_id=p.id).order_by(
        Availability.day_of_week, Availability.start_time
    ).all()

    # Build dict: day_value -> list of slots
    slots_by_day = {d: [] for d in DayOfWeek}
    for slot in all_slots:
        slots_by_day[slot.day_of_week].append(slot)

    return render_template(
        'doctor/availability.html', title='Manage Availability',
        profile=p, slots=all_slots, slots_by_day=slots_by_day,
        days=DayOfWeek, form=form,
    )


@doctor_bp.route('/availability/<int:avail_id>/toggle', methods=['POST'])
@role_required(UserRole.DOCTOR)
def toggle_slot(avail_id):
    """Toggle a slot between active and inactive."""
    avail = Availability.query.filter_by(
        id=avail_id, doctor_id=current_user.doctor_profile.id
    ).first_or_404()
    avail.is_active = not avail.is_active
    db.session.commit()
    state = 'activated' if avail.is_active else 'paused'
    flash(f'Slot {state}.', 'info')
    return redirect(url_for('doctor.availability'))


@doctor_bp.route('/availability/<int:avail_id>/delete', methods=['POST'])
@role_required(UserRole.DOCTOR)
def delete_availability(avail_id):
    avail = Availability.query.filter_by(
        id=avail_id, doctor_id=current_user.doctor_profile.id
    ).first_or_404()
    db.session.delete(avail)
    db.session.commit()
    flash('Availability slot removed.', 'info')
    return redirect(url_for('doctor.availability'))


@doctor_bp.route('/toggle-availability', methods=['POST'])
@role_required(UserRole.DOCTOR)
def toggle_availability():
    p = current_user.doctor_profile
    p.is_available = not p.is_available
    db.session.commit()
    status = 'available' if p.is_available else 'unavailable'
    flash(f'You are now {status} for new appointments.', 'info')
    return redirect(url_for('doctor.dashboard'))


@doctor_bp.route('/view/<int:doctor_id>')
def public_profile(doctor_id):
    """Public-facing doctor profile page."""
    doc = DoctorProfile.query.get_or_404(doctor_id)
    reviews = Review.query.filter_by(doctor_id=doc.id, is_visible=True)\
        .order_by(Review.created_at.desc()).limit(10).all()
    return render_template(
        'doctor/public_profile.html', title=f'Dr. {doc.full_name}',
        doctor=doc, reviews=reviews,
    )


@doctor_bp.route('/earnings')
@role_required(UserRole.DOCTOR)
def earnings():
    """Doctor earnings and payment summary."""
    from ..models.payment import Payment, PaymentStatus, PaymentType
    from ..models.appointment import AppointmentStatus
    from sqlalchemy import func

    profile = current_user.doctor_profile

    # Confirmed/completed appointments
    completed_appts = Appointment.query.filter_by(
        doctor_id=profile.id,
        status=AppointmentStatus.COMPLETED,
    ).order_by(Appointment.appointment_date.desc()).all()

    # Aggregate earnings from completed payments linked to these appointments
    appointment_ids = [a.id for a in completed_appts]

    # Total earned — sum of completed consultation payments for this doctor's appointments
    total_earned = db.session.query(
        func.coalesce(func.sum(Payment.amount), 0)
    ).filter(
        Payment.reference_type == 'appointment',
        Payment.reference_id.in_(appointment_ids) if appointment_ids else db.false(),
        Payment.status == PaymentStatus.COMPLETED,
        Payment.payment_type == PaymentType.CONSULTATION,
    ).scalar()

    # Monthly breakdown (last 6 months)
    from datetime import date, timedelta
    from collections import defaultdict

    monthly = defaultdict(float)
    for appt in completed_appts:
        key = appt.appointment_date.strftime('%b %Y')
        monthly[key] += float(appt.consultation_fee)

    # Recent payments (paginated)
    payments = paginate_query(
        Payment.query.filter(
            Payment.reference_type == 'appointment',
            Payment.reference_id.in_(appointment_ids) if appointment_ids else db.false(),
            Payment.status == PaymentStatus.COMPLETED,
        ).order_by(Payment.created_at.desc()),
        per_page=15,
    )

    return render_template(
        'doctor/earnings.html',
        title='My Earnings',
        profile=profile,
        total_earned=float(total_earned),
        completed_count=len(completed_appts),
        monthly_breakdown=dict(list(monthly.items())[:6]),
        payments=payments,
    )
