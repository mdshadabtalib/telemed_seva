"""Patient routes — dashboard, profile, medical records, addresses, reviews, support."""
from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import current_user, login_required

from . import patient_bp
from ..extensions import db
from ..models.user import UserRole, PatientProfile, Gender, BloodGroup
from ..models.appointment import Appointment, AppointmentStatus
from ..models.prescription import Prescription
from ..models.medical_record import MedicalRecord, RecordType
from ..models.order import Order
from ..models.notification import Notification
from ..models.address import Address
from ..models.review import Review
from ..models.support import SupportTicket, TicketPriority
from ..utils.decorators import role_required
from ..utils.helpers import save_upload, paginate_query
from ..utils.forms import PatientProfileForm, AddressForm, SupportTicketForm
from ..services.notification_service import notify
from ..models.notification import NotificationType


@patient_bp.route('/dashboard')
@role_required(UserRole.PATIENT)
def dashboard():
    profile = current_user.patient_profile
    upcoming = Appointment.query.filter(
        Appointment.patient_id == current_user.id,
        Appointment.status.in_([AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED]),
    ).order_by(Appointment.appointment_date, Appointment.start_time).limit(5).all()

    recent_prescriptions = Prescription.query.filter_by(
        patient_id=current_user.id
    ).order_by(Prescription.created_at.desc()).limit(5).all()

    recent_orders = Order.query.filter_by(
        user_id=current_user.id
    ).order_by(Order.created_at.desc()).limit(5).all()

    return render_template(
        'patient/dashboard.html',
        title='Patient Dashboard',
        profile=profile,
        upcoming_appointments=upcoming,
        recent_prescriptions=recent_prescriptions,
        recent_orders=recent_orders,
    )


@patient_bp.route('/profile', methods=['GET', 'POST'])
@role_required(UserRole.PATIENT)
def profile():
    patient_profile = current_user.patient_profile
    form = PatientProfileForm(obj=patient_profile)

    if form.validate_on_submit():
        patient_profile.first_name = form.first_name.data.strip()
        patient_profile.last_name  = form.last_name.data.strip()
        patient_profile.phone      = form.phone.data.strip() if form.phone.data else None
        patient_profile.date_of_birth = form.date_of_birth.data

        if form.gender.data:
            try:
                patient_profile.gender = Gender(form.gender.data)
            except ValueError:
                pass

        if form.blood_group.data:
            try:
                patient_profile.blood_group = BloodGroup(form.blood_group.data)
            except ValueError:
                pass

        patient_profile.allergies                = form.allergies.data.strip()
        patient_profile.medical_history          = form.medical_history.data.strip()
        patient_profile.emergency_contact_name   = form.emergency_contact_name.data.strip()
        patient_profile.emergency_contact_phone  = form.emergency_contact_phone.data.strip()

        if form.avatar.data:
            filename = save_upload(form.avatar.data, 'avatars',
                                   allowed_extensions={'png', 'jpg', 'jpeg', 'webp'})
            if filename:
                patient_profile.avatar = filename

        db.session.commit()
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('patient.profile'))

    return render_template(
        'patient/profile.html',
        title='My Profile',
        profile=patient_profile,
        form=form,
        genders=Gender,
        blood_groups=BloodGroup,
    )


@patient_bp.route('/medical-records')
@role_required(UserRole.PATIENT)
def medical_records():
    records = paginate_query(
        MedicalRecord.query.filter_by(patient_id=current_user.id)
        .order_by(MedicalRecord.created_at.desc())
    )
    return render_template(
        'patient/medical_records.html',
        title='Medical Records',
        records=records,
        record_types=RecordType,
    )


@patient_bp.route('/medical-records/upload', methods=['POST'])
@role_required(UserRole.PATIENT)
def upload_record():
    file = request.files.get('file')
    if not file or file.filename == '':
        flash('Please select a file.', 'warning')
        return redirect(url_for('patient.medical_records'))

    filename = save_upload(file, 'reports')
    if not filename:
        flash('Invalid file type. Allowed: PDF, PNG, JPG, DOC, DOCX.', 'danger')
        return redirect(url_for('patient.medical_records'))

    record_type = request.form.get('record_type', 'other')
    try:
        rtype = RecordType(record_type)
    except ValueError:
        rtype = RecordType.OTHER

    record = MedicalRecord(
        patient_id=current_user.id,
        record_type=rtype,
        title=request.form.get('title', file.filename),
        description=request.form.get('description', ''),
        file_url=f'/uploads/reports/{filename}',
        file_name=file.filename,
        file_size=0,
        uploaded_by=current_user.id,
    )
    db.session.add(record)
    db.session.commit()
    flash('Medical record uploaded.', 'success')
    return redirect(url_for('patient.medical_records'))


@patient_bp.route('/addresses')
@role_required(UserRole.PATIENT)
def addresses():
    addrs = Address.query.filter_by(user_id=current_user.id).all()
    form = AddressForm()
    return render_template('patient/addresses.html', title='My Addresses',
                           addresses=addrs, form=form)


@patient_bp.route('/addresses/add', methods=['POST'])
@role_required(UserRole.PATIENT)
def add_address():
    form = AddressForm()
    if form.validate_on_submit():
        addr = Address(
            user_id=current_user.id,
            label=form.label.data,
            full_name=form.full_name.data.strip(),
            phone=form.phone.data.strip(),
            line1=form.line1.data.strip(),
            line2=form.line2.data.strip() if form.line2.data else '',
            city=form.city.data.strip(),
            state=form.state.data.strip(),
            pincode=form.pincode.data.strip(),
            is_default=not Address.query.filter_by(user_id=current_user.id).first(),
        )
        db.session.add(addr)
        db.session.commit()
        flash('Address added.', 'success')
    else:
        for field, errs in form.errors.items():
            for e in errs:
                flash(f'{field}: {e}', 'danger')
    return redirect(url_for('patient.addresses'))


@patient_bp.route('/addresses/<int:addr_id>/delete', methods=['POST'])
@role_required(UserRole.PATIENT)
def delete_address(addr_id):
    addr = Address.query.filter_by(id=addr_id, user_id=current_user.id).first_or_404()
    db.session.delete(addr)
    db.session.commit()
    flash('Address deleted.', 'info')
    return redirect(url_for('patient.addresses'))


# ─────────────────────────────────────────────────────────────────────────────
# Reviews
# ─────────────────────────────────────────────────────────────────────────────

@patient_bp.route('/appointments/<int:appointment_id>/review', methods=['GET', 'POST'])
@role_required(UserRole.PATIENT)
def submit_review(appointment_id):
    """Submit a rating + comment for a completed consultation."""
    appointment = Appointment.query.get_or_404(appointment_id)

    # Must be this patient's appointment
    if appointment.patient_id != current_user.id:
        abort(403)

    # Only completable after the appointment is done
    if appointment.status != AppointmentStatus.COMPLETED:
        flash('You can only review a completed appointment.', 'warning')
        return redirect(url_for('appointments.detail', appointment_id=appointment_id))

    # One review per appointment
    existing = Review.query.filter_by(appointment_id=appointment_id).first()
    if existing:
        flash('You have already reviewed this consultation.', 'info')
        return redirect(url_for('doctor.public_profile',
                                doctor_id=appointment.doctor_id))

    if request.method == 'POST':
        try:
            rating = int(request.form.get('rating', 0))
        except (ValueError, TypeError):
            rating = 0

        if rating < 1 or rating > 5:
            flash('Please select a rating between 1 and 5.', 'danger')
            return redirect(url_for('patient.submit_review',
                                    appointment_id=appointment_id))

        comment = request.form.get('comment', '').strip()

        review = Review(
            patient_id=current_user.id,
            doctor_id=appointment.doctor_id,
            appointment_id=appointment_id,
            rating=rating,
            comment=comment,
        )
        db.session.add(review)

        # Notify the doctor
        notify(
            appointment.doctor.user_id,
            NotificationType.REVIEW_RECEIVED,
            'New Review',
            f'{current_user.display_name} left a {rating}★ review.',
            link=f'/doctor/view/{appointment.doctor_id}',
        )

        db.session.commit()
        flash('Thank you! Your review has been submitted.', 'success')
        return redirect(url_for('doctor.public_profile',
                                doctor_id=appointment.doctor_id))

    return render_template(
        'patient/submit_review.html',
        title='Rate Your Consultation',
        appointment=appointment,
    )


@patient_bp.route('/reviews')
@role_required(UserRole.PATIENT)
def my_reviews():
    """List all reviews the patient has submitted."""
    reviews = Review.query.filter_by(patient_id=current_user.id)\
        .order_by(Review.created_at.desc()).all()
    return render_template('patient/my_reviews.html',
                           title='My Reviews', reviews=reviews)


# ─────────────────────────────────────────────────────────────────────────────
# Support Tickets
# ─────────────────────────────────────────────────────────────────────────────

@patient_bp.route('/support', methods=['GET', 'POST'])
@role_required(UserRole.PATIENT)
def support():
    """Create a new support ticket or list existing ones."""
    form = SupportTicketForm()
    if form.validate_on_submit():
        try:
            priority = TicketPriority(form.priority.data)
        except ValueError:
            priority = TicketPriority.MEDIUM

        ticket = SupportTicket(
            user_id=current_user.id,
            subject=form.subject.data.strip(),
            description=form.description.data.strip(),
            priority=priority,
        )
        db.session.add(ticket)
        db.session.commit()
        flash('Support ticket submitted. Our team will respond shortly.', 'success')
        return redirect(url_for('patient.support'))

    tickets = paginate_query(
        SupportTicket.query.filter_by(user_id=current_user.id)
        .order_by(SupportTicket.created_at.desc()),
        per_page=15,
    )
    return render_template('patient/support.html',
                           title='Support', tickets=tickets,
                           form=form, priorities=TicketPriority)

