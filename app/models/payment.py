"""Payment and Refund models."""
import enum
import uuid
from datetime import datetime, timezone

from ..extensions import db


class PaymentType(enum.Enum):
    CONSULTATION = 'consultation'
    PHARMACY = 'pharmacy'


class PaymentStatus(enum.Enum):
    PENDING = 'pending'
    COMPLETED = 'completed'
    FAILED = 'failed'
    REFUNDED = 'refunded'
    PARTIALLY_REFUNDED = 'partially_refunded'


class PaymentMethod(enum.Enum):
    MOCK = 'mock'
    RAZORPAY = 'razorpay'
    STRIPE = 'stripe'


def _generate_payment_ref():
    return f'PAY-{uuid.uuid4().hex[:10].upper()}'


class Payment(db.Model):
    """A payment transaction for consultation or pharmacy order."""

    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    payment_ref = db.Column(
        db.String(20), unique=True, nullable=False, default=_generate_payment_ref, index=True
    )
    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True
    )
    payment_type = db.Column(db.Enum(PaymentType), nullable=False)
    reference_type = db.Column(db.String(50), nullable=False)  # 'appointment' or 'order'
    reference_id = db.Column(db.Integer, nullable=False)

    amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), default='INR')
    status = db.Column(
        db.Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False
    )

    # Provider details
    method = db.Column(db.Enum(PaymentMethod), default=PaymentMethod.MOCK)
    provider_order_id = db.Column(db.String(200), nullable=True)
    provider_payment_id = db.Column(db.String(200), nullable=True)
    provider_signature = db.Column(db.String(500), nullable=True)

    # Metadata
    notes = db.Column(db.Text, nullable=True)
    failure_reason = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user = db.relationship('User', backref='payments')

    def __repr__(self):
        return f'<Payment {self.payment_ref} {self.amount} {self.status.value}>'


class Refund(db.Model):
    """A refund linked to a payment."""

    __tablename__ = 'refunds'

    id = db.Column(db.Integer, primary_key=True)
    payment_id = db.Column(
        db.Integer, db.ForeignKey('payments.id', ondelete='CASCADE'), nullable=False
    )
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    reason = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')
    provider_refund_id = db.Column(db.String(200), nullable=True)
    processed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    payment = db.relationship('Payment', backref='refunds')

    def __repr__(self):
        return f'<Refund {self.id} payment={self.payment_id} amount={self.amount}>'
