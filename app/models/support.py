"""Support ticket model."""
import enum
from datetime import datetime, timezone

from ..extensions import db


class TicketStatus(enum.Enum):
    OPEN = 'open'
    IN_PROGRESS = 'in_progress'
    RESOLVED = 'resolved'
    CLOSED = 'closed'


class TicketPriority(enum.Enum):
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    URGENT = 'urgent'


class SupportTicket(db.Model):
    """A support request from a user."""

    __tablename__ = 'support_tickets'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True
    )
    subject = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(
        db.Enum(TicketStatus), default=TicketStatus.OPEN, nullable=False
    )
    priority = db.Column(
        db.Enum(TicketPriority), default=TicketPriority.MEDIUM, nullable=False
    )
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    resolution_notes = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user = db.relationship('User', foreign_keys=[user_id], backref='tickets')
    assignee = db.relationship('User', foreign_keys=[assigned_to])

    def __repr__(self):
        return f'<SupportTicket {self.id} status={self.status.value}>'
