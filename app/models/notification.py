"""Notification model."""
import enum
from datetime import datetime, timezone

from ..extensions import db


class NotificationType(enum.Enum):
    APPOINTMENT_BOOKED = 'appointment_booked'
    APPOINTMENT_CONFIRMED = 'appointment_confirmed'
    APPOINTMENT_CANCELLED = 'appointment_cancelled'
    APPOINTMENT_REMINDER = 'appointment_reminder'
    CONSULTATION_STARTED = 'consultation_started'
    PRESCRIPTION_CREATED = 'prescription_created'
    ORDER_PLACED = 'order_placed'
    ORDER_STATUS_CHANGED = 'order_status_changed'
    PAYMENT_RECEIVED = 'payment_received'
    PAYMENT_REFUNDED = 'payment_refunded'
    VERIFICATION_SUBMITTED = 'verification_submitted'
    VERIFICATION_APPROVED = 'verification_approved'
    VERIFICATION_REJECTED = 'verification_rejected'
    REVIEW_RECEIVED = 'review_received'
    SYSTEM = 'system'


class Notification(db.Model):
    """In-app notification for any user."""

    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True
    )
    notification_type = db.Column(db.Enum(NotificationType), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    link = db.Column(db.String(500), nullable=True)
    is_read = db.Column(db.Boolean, default=False, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def mark_read(self):
        self.is_read = True

    def __repr__(self):
        return f'<Notification {self.id} user={self.user_id} read={self.is_read}>'
