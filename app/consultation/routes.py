"""Consultation routes — room, chat, file sharing, completion."""
from datetime import datetime, timezone

from flask import render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import current_user, login_required

from . import consultation_bp
from ..extensions import db
from ..models.user import UserRole
from ..models.appointment import Appointment, AppointmentStatus
from ..models.consultation import Consultation, ConsultationStatus, ConsultationMessage, MessageType
from ..utils.helpers import save_upload
from ..utils.security import log_audit


@consultation_bp.route('/room/<int:consultation_id>')
@login_required
def room(consultation_id):
    """Consultation room — text chat + video placeholder."""
    consultation = Consultation.query.get_or_404(consultation_id)
    appointment = consultation.appointment

    # Authorization: only the patient and doctor can enter
    is_patient = current_user.id == appointment.patient_id
    is_doctor = (current_user.role == UserRole.DOCTOR and
                 current_user.doctor_profile and
                 current_user.doctor_profile.id == appointment.doctor_id)

    if not is_patient and not is_doctor:
        abort(403)

    # Verify appointment is confirmed
    if appointment.status not in (AppointmentStatus.CONFIRMED, AppointmentStatus.PENDING):
        flash('This consultation is not active.', 'warning')
        return redirect(url_for('appointments.detail', appointment_id=appointment.id))

    # Auto-start consultation when doctor enters
    if is_doctor and consultation.status == ConsultationStatus.WAITING:
        consultation.start()
        db.session.commit()

    messages = consultation.messages

    return render_template(
        'consultation/room.html',
        title='Consultation Room',
        consultation=consultation,
        appointment=appointment,
        messages=messages,
        is_doctor=is_doctor,
    )


@consultation_bp.route('/send-message/<int:consultation_id>', methods=['POST'])
@login_required
def send_message(consultation_id):
    """Send a chat message (text or file)."""
    consultation = Consultation.query.get_or_404(consultation_id)
    appointment = consultation.appointment

    # Authorization
    is_patient = current_user.id == appointment.patient_id
    is_doctor = (current_user.role == UserRole.DOCTOR and
                 current_user.doctor_profile and
                 current_user.doctor_profile.id == appointment.doctor_id)
    if not is_patient and not is_doctor:
        return jsonify({'error': 'Unauthorized'}), 403

    if consultation.status == ConsultationStatus.COMPLETED:
        return jsonify({'error': 'Consultation has ended'}), 400

    content = request.form.get('message', '').strip()
    file = request.files.get('file')

    if not content and not file:
        return jsonify({'error': 'Message or file required'}), 400

    msg_type = MessageType.TEXT
    file_url = None
    file_name = None

    if file and file.filename:
        filename = save_upload(file, 'documents')
        if filename:
            msg_type = MessageType.FILE
            file_url = f'/uploads/documents/{filename}'
            file_name = file.filename
            if not content:
                content = f'Shared file: {file.filename}'

    message = ConsultationMessage(
        consultation_id=consultation_id,
        sender_id=current_user.id,
        message_type=msg_type,
        content=content,
        file_url=file_url,
        file_name=file_name,
    )
    db.session.add(message)
    db.session.commit()

    return jsonify({
        'id': message.id,
        'sender': current_user.display_name,
        'sender_id': current_user.id,
        'content': message.content,
        'message_type': msg_type.value,
        'file_url': file_url,
        'file_name': file_name,
        'sent_at': message.sent_at.strftime('%I:%M %p'),
    })


@consultation_bp.route('/messages/<int:consultation_id>')
@login_required
def get_messages(consultation_id):
    """Fetch messages for polling-based chat refresh."""
    consultation = Consultation.query.get_or_404(consultation_id)
    appointment = consultation.appointment

    is_patient = current_user.id == appointment.patient_id
    is_doctor = (current_user.role == UserRole.DOCTOR and
                 current_user.doctor_profile and
                 current_user.doctor_profile.id == appointment.doctor_id)
    if not is_patient and not is_doctor:
        return jsonify({'error': 'Unauthorized'}), 403

    after_id = request.args.get('after', 0, type=int)
    messages = ConsultationMessage.query.filter(
        ConsultationMessage.consultation_id == consultation_id,
        ConsultationMessage.id > after_id,
    ).order_by(ConsultationMessage.sent_at).all()

    return jsonify({
        'messages': [{
            'id': m.id,
            'sender': m.sender.display_name,
            'sender_id': m.sender_id,
            'content': m.content,
            'message_type': m.message_type.value,
            'file_url': m.file_url,
            'file_name': m.file_name,
            'sent_at': m.sent_at.strftime('%I:%M %p'),
        } for m in messages],
        'status': consultation.status.value,
    })


@consultation_bp.route('/complete/<int:consultation_id>', methods=['POST'])
@login_required
def complete(consultation_id):
    """Complete a consultation (doctor only)."""
    consultation = Consultation.query.get_or_404(consultation_id)
    appointment = consultation.appointment

    if current_user.role != UserRole.DOCTOR or \
            current_user.doctor_profile.id != appointment.doctor_id:
        abort(403)

    # Save diagnosis and notes
    consultation.diagnosis = request.form.get('diagnosis', '').strip()
    consultation.notes = request.form.get('notes', '').strip()
    consultation.complete()

    # Complete the appointment
    appointment.transition_to(AppointmentStatus.COMPLETED)

    log_audit(
        current_user.id, 'complete_consultation', 'consultation',
        consultation.id, f'Appointment {appointment.id} completed.'
    )
    db.session.commit()

    flash('Consultation completed. You can now create a prescription.', 'success')
    return redirect(url_for('prescriptions.create', consultation_id=consultation.id))
