"""Prescription routes — create, view, list."""
from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import current_user, login_required

from . import prescriptions_bp
from ..extensions import db
from ..models.user import UserRole
from ..models.consultation import Consultation, ConsultationStatus
from ..models.prescription import Prescription, PrescriptionItem
from ..services.notification_service import notify_prescription_created
from ..utils.decorators import verified_doctor_required, role_required
from ..utils.helpers import paginate_query
from ..utils.security import log_audit


@prescriptions_bp.route('/create/<int:consultation_id>', methods=['GET', 'POST'])
@verified_doctor_required
def create(consultation_id):
    """Create a prescription for a completed consultation."""
    consultation = Consultation.query.get_or_404(consultation_id)
    appointment = consultation.appointment

    if current_user.doctor_profile.id != appointment.doctor_id:
        abort(403)

    if consultation.prescription:
        flash('A prescription already exists for this consultation.', 'info')
        return redirect(url_for('prescriptions.view', prescription_id=consultation.prescription.id))

    if request.method == 'POST':
        diagnosis = request.form.get('diagnosis', '').strip()
        advice = request.form.get('advice', '').strip()

        prescription = Prescription(
            consultation_id=consultation.id,
            patient_id=appointment.patient_id,
            doctor_id=current_user.doctor_profile.id,
            diagnosis=diagnosis,
            advice=advice,
        )
        db.session.add(prescription)
        db.session.flush()

        # Parse medicine items
        medicine_names = request.form.getlist('medicine_name[]')
        strengths = request.form.getlist('strength[]')
        dosages = request.form.getlist('dosage[]')
        frequencies = request.form.getlist('frequency[]')
        durations = request.form.getlist('duration[]')
        instructions = request.form.getlist('instructions[]')
        quantities = request.form.getlist('quantity[]')

        for i, name in enumerate(medicine_names):
            if not name.strip():
                continue
            item = PrescriptionItem(
                prescription_id=prescription.id,
                medicine_name=name.strip(),
                strength=strengths[i].strip() if i < len(strengths) else '',
                dosage=dosages[i].strip() if i < len(dosages) else '',
                frequency=frequencies[i].strip() if i < len(frequencies) else '',
                duration=durations[i].strip() if i < len(durations) else '',
                instructions=instructions[i].strip() if i < len(instructions) else '',
                quantity=int(quantities[i]) if i < len(quantities) and quantities[i].isdigit() else None,
            )
            db.session.add(item)

        notify_prescription_created(appointment.patient_id, prescription)
        log_audit(current_user.id, 'create_prescription', 'prescription', prescription.id)
        db.session.commit()

        flash('Prescription created successfully.', 'success')
        return redirect(url_for('prescriptions.view', prescription_id=prescription.id))

    return render_template(
        'prescriptions/create.html',
        title='Create Prescription',
        consultation=consultation,
        appointment=appointment,
    )


@prescriptions_bp.route('/<int:prescription_id>')
@login_required
def view(prescription_id):
    """View a prescription."""
    prescription = Prescription.query.get_or_404(prescription_id)

    # Authorization: patient who received it, doctor who issued it, or admin
    authorized = (
        current_user.id == prescription.patient_id
        or (current_user.role == UserRole.DOCTOR and
            current_user.doctor_profile and
            current_user.doctor_profile.id == prescription.doctor_id)
        or current_user.role == UserRole.ADMIN
    )
    if not authorized:
        abort(403)

    log_audit(current_user.id, 'view_prescription', 'prescription', prescription.id)
    db.session.commit()

    return render_template(
        'prescriptions/view.html',
        title=f'Prescription {prescription.prescription_uid}',
        prescription=prescription,
    )


@prescriptions_bp.route('/my')
@login_required
def my_prescriptions():
    """List prescriptions for the current user."""
    if current_user.role == UserRole.PATIENT:
        query = Prescription.query.filter_by(patient_id=current_user.id)
    elif current_user.role == UserRole.DOCTOR:
        query = Prescription.query.filter_by(doctor_id=current_user.doctor_profile.id)
    else:
        abort(403)

    prescriptions = paginate_query(
        query.order_by(Prescription.created_at.desc()),
        per_page=15,
    )

    return render_template(
        'prescriptions/list.html',
        title='My Prescriptions',
        prescriptions=prescriptions,
    )
