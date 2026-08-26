"""Doctor routes — dashboard, profile, verification, availability, public profile."""
from datetime import datetime, timezone, time

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
from ..utils.helpers import save_upload


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
    specialties = Specialty.query.filter_by(is_active=True).order_by(Specialty.name).all()

    if request.method == 'POST':
        p.first_name = request.form.get('first_name', '').strip()
        p.last_name = request.form.get('last_name', '').strip()
        p.phone = request.form.get('phone', '').strip()
        p.bio = request.form.get('bio', '').strip()
        p.qualifications = request.form.get('qualifications', '').strip()
        p.registration_number = request.form.get('registration_number', '').strip()
        p.languages = request.form.get('languages', '').strip()

        exp = request.form.get('experience_years', 0)
        try:
            p.experience_years = int(exp)
        except (ValueError, TypeError):
            pass

        fee = request.form.get('consultation_fee', 0)
        try:
            p.consultation_fee = float(fee)
        except (ValueError, TypeError):
            pass

        duration = request.form.get('consultation_duration', 30)
        try:
            p.consultation_duration = int(duration)
        except (ValueError, TypeError):
            pass

        spec_id = request.form.get('specialty_id')
        if spec_id:
            p.specialty_id = int(spec_id)

        avatar = request.files.get('avatar')
        if avatar and avatar.filename:
            filename = save_upload(avatar, 'avatars',
                                   allowed_extensions={'png', 'jpg', 'jpeg', 'webp'})
            if filename:
                p.avatar = filename

        db.session.commit()
        flash('Profile updated.', 'success')
        return redirect(url_for('doctor.profile'))

    return render_template(
        'doctor/profile.html', title='Doctor Profile',
        profile=p, specialties=specialties,
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

    if request.method == 'POST':
        day = request.form.get('day_of_week')
        start = request.form.get('start_time')
        end = request.form.get('end_time')

        if not all([day, start, end]):
            flash('All fields are required.', 'danger')
            return redirect(url_for('doctor.availability'))

        try:
            day_enum = DayOfWeek(int(day))
            start_time = time.fromisoformat(start)
            end_time = time.fromisoformat(end)
        except (ValueError, TypeError):
            flash('Invalid input.', 'danger')
            return redirect(url_for('doctor.availability'))

        if start_time >= end_time:
            flash('Start time must be before end time.', 'danger')
            return redirect(url_for('doctor.availability'))

        existing = Availability.query.filter_by(
            doctor_id=p.id, day_of_week=day_enum, start_time=start_time
        ).first()

        if existing:
            existing.end_time = end_time
            existing.slot_duration = p.consultation_duration
            existing.is_active = True
        else:
            avail = Availability(
                doctor_id=p.id,
                day_of_week=day_enum,
                start_time=start_time,
                end_time=end_time,
                slot_duration=p.consultation_duration,
            )
            db.session.add(avail)

        db.session.commit()
        flash('Availability updated.', 'success')
        return redirect(url_for('doctor.availability'))

    slots = Availability.query.filter_by(doctor_id=p.id).order_by(
        Availability.day_of_week, Availability.start_time
    ).all()

    return render_template(
        'doctor/availability.html', title='Manage Availability',
        profile=p, slots=slots, days=DayOfWeek,
    )


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
