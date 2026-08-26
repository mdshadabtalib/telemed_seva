"""Payment service — provider abstraction layer."""
import abc
import uuid
from datetime import datetime, timezone

from flask import current_app

from ..extensions import db
from ..models.payment import Payment, PaymentStatus, PaymentType, PaymentMethod


class PaymentProvider(abc.ABC):
    """Abstract base for payment providers."""

    @abc.abstractmethod
    def create_order(self, amount, currency, reference_type, reference_id, notes=None):
        """Create a payment order. Returns a dict with provider-specific data."""

    @abc.abstractmethod
    def verify_payment(self, payment_id, provider_data):
        """Verify a payment callback/webhook. Returns True if valid."""

    @abc.abstractmethod
    def initiate_refund(self, payment, amount, reason=None):
        """Initiate a refund. Returns refund reference or None."""


class MockPaymentProvider(PaymentProvider):
    """Development payment provider — always succeeds."""

    def create_order(self, amount, currency, reference_type, reference_id, notes=None):
        order_id = f'mock_order_{uuid.uuid4().hex[:12]}'
        return {
            'provider': 'mock',
            'order_id': order_id,
            'amount': float(amount),
            'currency': currency,
            'key': 'mock_key',
        }

    def verify_payment(self, payment_id, provider_data):
        return True

    def initiate_refund(self, payment, amount, reason=None):
        return f'mock_refund_{uuid.uuid4().hex[:8]}'


class RazorpayPaymentProvider(PaymentProvider):
    """Razorpay integration — requires RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET."""

    def __init__(self):
        self.key_id = current_app.config.get('RAZORPAY_KEY_ID')
        self.key_secret = current_app.config.get('RAZORPAY_KEY_SECRET')
        if not self.key_id or not self.key_secret:
            raise RuntimeError(
                'Razorpay credentials not configured. '
                'Set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET in .env'
            )

    def create_order(self, amount, currency, reference_type, reference_id, notes=None):
        # TODO: Integrate with razorpay Python SDK
        # import razorpay
        # client = razorpay.Client(auth=(self.key_id, self.key_secret))
        # order = client.order.create({
        #     'amount': int(amount * 100),
        #     'currency': currency,
        #     'notes': notes or {},
        # })
        raise NotImplementedError(
            'Razorpay integration requires the razorpay package. '
            'Install it and uncomment the implementation above.'
        )

    def verify_payment(self, payment_id, provider_data):
        raise NotImplementedError('Configure Razorpay SDK for payment verification.')

    def initiate_refund(self, payment, amount, reason=None):
        raise NotImplementedError('Configure Razorpay SDK for refunds.')


def get_payment_provider():
    """Factory: return the configured payment provider."""
    razorpay_key = current_app.config.get('RAZORPAY_KEY_ID')
    if razorpay_key:
        try:
            return RazorpayPaymentProvider()
        except RuntimeError:
            pass
    return MockPaymentProvider()


def create_payment(user_id, payment_type, reference_type, reference_id, amount, currency='INR'):
    """Create a payment record and initiate with the provider.

    Returns (payment, provider_data) or (None, error_message).
    """
    provider = get_payment_provider()

    try:
        provider_data = provider.create_order(
            amount=amount,
            currency=currency,
            reference_type=reference_type,
            reference_id=reference_id,
        )
    except Exception as e:
        current_app.logger.error(f'Payment creation failed: {e}')
        return None, str(e)

    method = PaymentMethod.MOCK
    if isinstance(provider, RazorpayPaymentProvider):
        method = PaymentMethod.RAZORPAY

    payment = Payment(
        user_id=user_id,
        payment_type=payment_type,
        reference_type=reference_type,
        reference_id=reference_id,
        amount=amount,
        currency=currency,
        status=PaymentStatus.PENDING,
        method=method,
        provider_order_id=provider_data.get('order_id'),
    )
    db.session.add(payment)
    db.session.flush()

    provider_data['payment_db_id'] = payment.id
    provider_data['payment_ref'] = payment.payment_ref

    return payment, provider_data


def complete_payment(payment_id, provider_data=None):
    """Mark a payment as completed after provider verification."""
    payment = db.session.get(Payment, payment_id)
    if not payment:
        return None, 'Payment not found.'

    provider = get_payment_provider()

    if not isinstance(provider, MockPaymentProvider):
        if not provider.verify_payment(payment_id, provider_data):
            payment.status = PaymentStatus.FAILED
            payment.failure_reason = 'Payment verification failed.'
            db.session.commit()
            return None, 'Payment verification failed.'

    if provider_data:
        payment.provider_payment_id = provider_data.get('payment_id')
        payment.provider_signature = provider_data.get('signature')

    payment.status = PaymentStatus.COMPLETED
    # Caller should commit the transaction
    return payment, None
