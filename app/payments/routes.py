"""Payment routes — initiate, verify, history."""
from flask import render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import current_user, login_required

from . import payments_bp
from ..extensions import db
from ..models.user import UserRole
from ..models.payment import Payment, PaymentStatus, PaymentType
from ..models.appointment import Appointment, AppointmentStatus
from ..models.order import Order, OrderStatus
from ..services.payment_service import create_payment, complete_payment
from ..services.notification_service import notify
from ..models.notification import NotificationType
from ..utils.decorators import role_required
from ..utils.helpers import paginate_query


@payments_bp.route('/pay/appointment/<int:appointment_id>', methods=['GET', 'POST'])
@role_required(UserRole.PATIENT)
def pay_appointment(appointment_id):
    """Initiate payment for a consultation appointment."""
    appointment = Appointment.query.get_or_404(appointment_id)
    if appointment.patient_id != current_user.id:
        abort(403)

    if request.method == 'POST':
        payment, result = create_payment(
            user_id=current_user.id,
            payment_type=PaymentType.CONSULTATION,
            reference_type='appointment',
            reference_id=appointment.id,
            amount=float(appointment.consultation_fee),
        )

        if payment is None:
            flash(f'Payment error: {result}', 'danger')
            return redirect(url_for('appointments.detail', appointment_id=appointment_id))

        # For mock provider, auto-complete payment
        if result.get('provider') == 'mock':
            payment, err = complete_payment(payment.id)
            if payment:
                appointment.status = AppointmentStatus.CONFIRMED
                notify(current_user.id, NotificationType.PAYMENT_RECEIVED,
                       'Payment Successful',
                       f'Payment of ₹{appointment.consultation_fee} received for appointment.',
                       link=f'/appointments/{appointment.id}')
                db.session.commit()
                flash('Payment successful! Appointment confirmed.', 'success')
                return redirect(url_for('appointments.detail', appointment_id=appointment_id))

        # For real providers, render payment page with provider data
        db.session.commit()
        return render_template(
            'payments/checkout.html',
            title='Payment',
            payment=payment,
            provider_data=result,
        )

    return render_template(
        'payments/pay_appointment.html',
        title='Pay for Appointment',
        appointment=appointment,
    )


@payments_bp.route('/pay/order/<int:order_id>', methods=['GET', 'POST'])
@role_required(UserRole.PATIENT)
def pay_order(order_id):
    """Initiate payment for a pharmacy order."""
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        abort(403)

    if request.method == 'POST':
        payment, result = create_payment(
            user_id=current_user.id,
            payment_type=PaymentType.PHARMACY,
            reference_type='order',
            reference_id=order.id,
            amount=float(order.total),
        )

        if payment is None:
            flash(f'Payment error: {result}', 'danger')
            return redirect(url_for('pharmacy.order_detail', order_id=order_id))

        if result.get('provider') == 'mock':
            payment, err = complete_payment(payment.id)
            if payment:
                order.status = OrderStatus.PROCESSING
                notify(current_user.id, NotificationType.PAYMENT_RECEIVED,
                       'Payment Successful',
                       f'Payment of ₹{order.total} received for order {order.order_number}.',
                       link=f'/pharmacy/orders/{order.id}')
                db.session.commit()
                flash('Payment successful! Order is being processed.', 'success')
                return redirect(url_for('pharmacy.order_detail', order_id=order_id))

        db.session.commit()
        return render_template(
            'payments/checkout.html', title='Payment',
            payment=payment, provider_data=result,
        )

    return render_template(
        'payments/pay_order.html', title='Pay for Order', order=order,
    )


@payments_bp.route('/verify', methods=['POST'])
@login_required
def verify():
    """Webhook/callback for payment verification."""
    payment_id = request.form.get('payment_id', type=int)
    if not payment_id:
        return jsonify({'error': 'Missing payment_id'}), 400

    provider_data = {
        'payment_id': request.form.get('provider_payment_id'),
        'signature': request.form.get('provider_signature'),
    }

    payment, error = complete_payment(payment_id, provider_data)
    if error:
        return jsonify({'error': error}), 400

    db.session.commit()
    return jsonify({'status': 'success', 'payment_ref': payment.payment_ref})


@payments_bp.route('/history')
@login_required
def history():
    """Payment history for current user."""
    payments = paginate_query(
        Payment.query.filter_by(user_id=current_user.id)
        .order_by(Payment.created_at.desc()),
        per_page=15,
    )
    return render_template('payments/history.html', title='Payment History', payments=payments)
