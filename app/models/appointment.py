"""Appointment model with status state-machine and slot locking."""
import enum
from datetime import datetime, timezone

from ..extensions import db


class AppointmentStatus(enum.Enum):
    PENDING = 'pending'
    CONFIRMED = 'confirmed'
    CANCELLED = 'cancelled'
    COMPLETED = 'completed'
    NO_SHOW = 'no_show'
    RESCHEDULED = 'rescheduled'


class AppointmentType(enum.Enum):
    VIDEO = 'video'
    CHAT = 'chat'


class Appointment(db.Model):
    """A scheduled consultation between a patient and a doctor."""

    __tablename__ = 'appointments'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    doctor_id = db.Column(
        db.Integer,
        db.ForeignKey('doctor_profiles.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )

    # Scheduling
    appointment_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    appointment_type = db.Column(
        db.Enum(AppointmentType), default=AppointmentType.VIDEO, nullable=False
    )

    # Status
    status = db.Column(
        db.Enum(AppointmentStatus),
        default=AppointmentStatus.PENDING,
        nullable=False,
        index=True,
    )
    cancellation_reason = db.Column(db.Text)
    cancelled_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # Slot locking — prevents race conditions during booking
    locked_until = db.Column(db.DateTime, nullable=True)
    locked_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # Notes
    patient_notes = db.Column(db.Text)

    # Fees (snapshot at booking time)
    consultation_fee = db.Column(db.Numeric(10, 2), nullable=False, default=0)

    # Rescheduling link
    rescheduled_from = db.Column(db.Integer, db.ForeignKey('appointments.id'), nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    patient = db.relationship('User', foreign_keys=[patient_id], backref='patient_appointments')
    doctor = db.relationship('DoctorProfile', backref='appointments')
    consultation = db.relationship(
        'Consultation', backref='appointment', uselist=False, cascade='all, delete-orphan'
    )
    payment = db.relationship(
        'Payment',
        primaryjoin="and_(Payment.reference_type=='appointment', "
                    "foreign(Payment.reference_id)==Appointment.id)",
        viewonly=True,
        uselist=False,
    )

    # Unique constraint: no double booking for a doctor at a given date+time
    __table_args__ = (
        db.UniqueConstraint(
            'doctor_id', 'appointment_date', 'start_time',
            name='uq_doctor_date_slot',
        ),
    )

    # Valid status transitions
    VALID_TRANSITIONS = {
        AppointmentStatus.PENDING: {
            AppointmentStatus.CONFIRMED,
            AppointmentStatus.CANCELLED,
        },
        AppointmentStatus.CONFIRMED: {
            AppointmentStatus.COMPLETED,
            AppointmentStatus.CANCELLED,
            AppointmentStatus.NO_SHOW,
            AppointmentStatus.RESCHEDULED,
        },
        AppointmentStatus.CANCELLED: set(),
        AppointmentStatus.COMPLETED: set(),
        AppointmentStatus.NO_SHOW: set(),
        AppointmentStatus.RESCHEDULED: set(),
    }

    def can_transition_to(self, new_status):
        return new_status in self.VALID_TRANSITIONS.get(self.status, set())

    def transition_to(self, new_status, reason=None, by_user_id=None):
        """Attempt a status transition; raises ValueError if invalid."""
        if not self.can_transition_to(new_status):
            raise ValueError(
                f'Cannot transition from {self.status.value} to {new_status.value}'
            )
        self.status = new_status
        if new_status == AppointmentStatus.CANCELLED:
            self.cancellation_reason = reason
            self.cancelled_by = by_user_id

    @property
    def is_upcoming(self):
        now = datetime.now(timezone.utc)
        appt_dt = datetime.combine(self.appointment_date, self.start_time).replace(
            tzinfo=timezone.utc
        )
        return appt_dt > now and self.status in (
            AppointmentStatus.PENDING,
            AppointmentStatus.CONFIRMED,
        )

    def __repr__(self):
        return (
            f'<Appointment {self.id} patient={self.patient_id} '
            f'doctor={self.doctor_id} {self.appointment_date} {self.status.value}>'
        )
