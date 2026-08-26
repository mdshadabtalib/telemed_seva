"""Prescription and PrescriptionItem models."""
import uuid
from datetime import datetime, timezone

from ..extensions import db


def _generate_prescription_uid():
    """Generate a unique prescription identifier like RX-XXXXXX."""
    return f'RX-{uuid.uuid4().hex[:8].upper()}'


class Prescription(db.Model):
    """A digital prescription issued by a doctor after consultation."""

    __tablename__ = 'prescriptions'

    id = db.Column(db.Integer, primary_key=True)
    prescription_uid = db.Column(
        db.String(20), unique=True, nullable=False, default=_generate_prescription_uid, index=True
    )
    consultation_id = db.Column(
        db.Integer,
        db.ForeignKey('consultations.id', ondelete='SET NULL'),
        nullable=True,
        unique=True,
    )
    patient_id = db.Column(
        db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True
    )
    doctor_id = db.Column(
        db.Integer, db.ForeignKey('doctor_profiles.id', ondelete='CASCADE'), nullable=False
    )

    # Clinical
    diagnosis = db.Column(db.Text)
    advice = db.Column(db.Text)

    # Validity
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    valid_until = db.Column(db.Date, nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    patient = db.relationship('User', backref='prescriptions')
    doctor = db.relationship('DoctorProfile', backref='prescriptions')
    items = db.relationship(
        'PrescriptionItem', backref='prescription', cascade='all, delete-orphan'
    )

    def __repr__(self):
        return f'<Prescription {self.prescription_uid}>'


class PrescriptionItem(db.Model):
    """A single medicine entry within a prescription."""

    __tablename__ = 'prescription_items'

    id = db.Column(db.Integer, primary_key=True)
    prescription_id = db.Column(
        db.Integer,
        db.ForeignKey('prescriptions.id', ondelete='CASCADE'),
        nullable=False,
    )
    medicine_name = db.Column(db.String(200), nullable=False)
    strength = db.Column(db.String(50))
    dosage = db.Column(db.String(100))
    frequency = db.Column(db.String(100))  # e.g. "Twice daily"
    duration = db.Column(db.String(100))   # e.g. "7 days"
    instructions = db.Column(db.Text)      # e.g. "After meals"
    quantity = db.Column(db.Integer)

    def __repr__(self):
        return f'<PrescriptionItem {self.medicine_name}>'
