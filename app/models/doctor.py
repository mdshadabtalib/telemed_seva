"""Doctor verification, specialty, and availability models."""
import enum
from datetime import datetime, timezone

from ..extensions import db


class VerificationStatus(enum.Enum):
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    REVOKED = 'revoked'


class DoctorVerification(db.Model):
    """Document-based verification workflow for doctors."""

    __tablename__ = 'doctor_verifications'

    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(
        db.Integer,
        db.ForeignKey('doctor_profiles.id', ondelete='CASCADE'),
        unique=True,
        nullable=False,
    )
    status = db.Column(
        db.Enum(VerificationStatus),
        default=VerificationStatus.PENDING,
        nullable=False,
    )

    # Uploaded documents
    medical_license_doc = db.Column(db.String(255))
    id_proof_doc = db.Column(db.String(255))
    degree_certificate_doc = db.Column(db.String(255))
    additional_doc = db.Column(db.String(255))

    submitted_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    reviewed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    rejection_reason = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)

    reviewer = db.relationship('User', foreign_keys=[reviewed_by])

    def __repr__(self):
        return f'<DoctorVerification doctor_id={self.doctor_id} status={self.status.value}>'


class Specialty(db.Model):
    """Medical specialty (e.g., Cardiology, Dermatology)."""

    __tablename__ = 'specialties'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    slug = db.Column(db.String(120), unique=True, nullable=False, index=True)
    description = db.Column(db.Text)
    icon = db.Column(db.String(50))  # icon class name, e.g. 'fa-heart'
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    display_order = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f'<Specialty {self.name}>'


class DayOfWeek(enum.Enum):
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6


class Availability(db.Model):
    """Recurring weekly availability slots for a doctor."""

    __tablename__ = 'availabilities'

    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(
        db.Integer,
        db.ForeignKey('doctor_profiles.id', ondelete='CASCADE'),
        nullable=False,
    )
    day_of_week = db.Column(db.Enum(DayOfWeek), nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    slot_duration = db.Column(db.Integer, default=30)  # minutes
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('doctor_id', 'day_of_week', 'start_time', name='uq_doctor_day_time'),
    )

    def __repr__(self):
        return (
            f'<Availability doctor_id={self.doctor_id} '
            f'{self.day_of_week.name} {self.start_time}-{self.end_time}>'
        )
