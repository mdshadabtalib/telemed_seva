"""Consultation and ConsultationMessage models."""
import enum
from datetime import datetime, timezone

from ..extensions import db


class ConsultationStatus(enum.Enum):
    WAITING = 'waiting'
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'


class Consultation(db.Model):
    """An active consultation session linked to an appointment."""

    __tablename__ = 'consultations'

    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(
        db.Integer,
        db.ForeignKey('appointments.id', ondelete='CASCADE'),
        unique=True,
        nullable=False,
    )
    status = db.Column(
        db.Enum(ConsultationStatus),
        default=ConsultationStatus.WAITING,
        nullable=False,
    )
    started_at = db.Column(db.DateTime, nullable=True)
    ended_at = db.Column(db.DateTime, nullable=True)

    # Doctor's clinical notes — visible only to the doctor
    diagnosis = db.Column(db.Text)
    notes = db.Column(db.Text)

    # WebRTC room ID (for video integration)
    room_id = db.Column(db.String(100), unique=True, nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    messages = db.relationship(
        'ConsultationMessage', backref='consultation',
        order_by='ConsultationMessage.sent_at', cascade='all, delete-orphan',
    )
    prescription = db.relationship(
        'Prescription', backref='consultation', uselist=False, cascade='all, delete-orphan'
    )

    def start(self):
        self.status = ConsultationStatus.IN_PROGRESS
        self.started_at = datetime.now(timezone.utc)

    def complete(self):
        self.status = ConsultationStatus.COMPLETED
        self.ended_at = datetime.now(timezone.utc)

    @property
    def duration_minutes(self):
        if self.started_at and self.ended_at:
            delta = self.ended_at - self.started_at
            return int(delta.total_seconds() / 60)
        return None

    def __repr__(self):
        return f'<Consultation {self.id} appointment={self.appointment_id} {self.status.value}>'


class MessageType(enum.Enum):
    TEXT = 'text'
    FILE = 'file'
    SYSTEM = 'system'


class ConsultationMessage(db.Model):
    """Chat messages exchanged during a consultation."""

    __tablename__ = 'consultation_messages'

    id = db.Column(db.Integer, primary_key=True)
    consultation_id = db.Column(
        db.Integer,
        db.ForeignKey('consultations.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message_type = db.Column(
        db.Enum(MessageType), default=MessageType.TEXT, nullable=False
    )
    content = db.Column(db.Text, nullable=False)
    file_url = db.Column(db.String(500), nullable=True)
    file_name = db.Column(db.String(255), nullable=True)
    sent_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    sender = db.relationship('User', backref='sent_messages')

    def __repr__(self):
        return f'<ConsultationMessage {self.id} consultation={self.consultation_id}>'
