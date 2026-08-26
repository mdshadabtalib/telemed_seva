"""Patient routes — dashboard, profile, medical records, addresses."""
from flask import render_template, redirect, url_for, flash, request
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
from ..utils.decorators import role_required
from ..utils.helpers import save_upload, paginate_query


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
    profile = current_user.patient_profile
    if request.method == 'POST':
        profile.first_name = request.form.get('first_name', '').strip()
        profile.last_name = request.form.get('last_name', '').strip()
        profile.phone = request.form.get('phone', '').strip()
        dob = request.form.get('date_of_birth')
        if dob:
            from datetime import datetime
            try:
                profile.date_of_birth = datetime.strptime(dob, '%Y-%m-%d').date()
            except ValueError:
                pass
        gender = request.form.get('gender')
        if gender:
            try:
                profile.gender = Gender(gender)
            except ValueError:
                pass
        bg = request.form.get('blood_group')
        if bg:
            try:
                profile.blood_group = BloodGroup(bg)
            except ValueError:
                pass
        profile.allergies = request.form.get('allergies', '').strip()
        profile.medical_history = request.form.get('medical_history', '').strip()
        profile.emergency_contact_name = request.form.get('emergency_contact_name', '').strip()
        profile.emergency_contact_phone = request.form.get('emergency_contact_phone', '').strip()

        # Avatar upload
        avatar = request.files.get('avatar')
        if avatar and avatar.filename:
            filename = save_upload(avatar, 'avatars',
                                   allowed_extensions={'png', 'jpg', 'jpeg', 'webp'})
            if filename:
                profile.avatar = filename

        db.session.commit()
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('patient.profile'))

    return render_template(
        'patient/profile.html',
        title='My Profile',
        profile=profile,
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
    return render_template('patient/addresses.html', title='My Addresses', addresses=addrs)


@patient_bp.route('/addresses/add', methods=['POST'])
@role_required(UserRole.PATIENT)
def add_address():
    addr = Address(
        user_id=current_user.id,
        label=request.form.get('label', 'Home'),
        full_name=request.form.get('full_name', '').strip(),
        phone=request.form.get('phone', '').strip(),
        line1=request.form.get('line1', '').strip(),
        line2=request.form.get('line2', '').strip(),
        city=request.form.get('city', '').strip(),
        state=request.form.get('state', '').strip(),
        pincode=request.form.get('pincode', '').strip(),
        is_default=not Address.query.filter_by(user_id=current_user.id).first(),
    )
    db.session.add(addr)
    db.session.commit()
    flash('Address added.', 'success')
    return redirect(url_for('patient.addresses'))


@patient_bp.route('/addresses/<int:addr_id>/delete', methods=['POST'])
@role_required(UserRole.PATIENT)
def delete_address(addr_id):
    addr = Address.query.filter_by(id=addr_id, user_id=current_user.id).first_or_404()
    db.session.delete(addr)
    db.session.commit()
    flash('Address deleted.', 'info')
    return redirect(url_for('patient.addresses'))
