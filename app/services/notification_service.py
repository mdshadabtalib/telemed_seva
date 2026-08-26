"""Notification service — abstraction for creating notifications with future channel support."""
from ..extensions import db
from ..models.notification import Notification, NotificationType


def notify(user_id, notification_type, title, message, link=None):
    """Create an in-app notification.

    This is the central notification function. Future email/SMS/push
    channels can be added here without changing callers.
    """
    notification = Notification(
        user_id=user_id,
        notification_type=notification_type,
        title=title,
        message=message,
        link=link,
    )
    db.session.add(notification)
    # Caller is responsible for committing the transaction

    # TODO: Send email notification if user preferences allow
    # TODO: Send push notification
    # TODO: Send SMS for critical notifications


def notify_appointment_booked(patient_id, doctor_user_id, appointment):
    """Notify both patient and doctor about a new appointment."""
    notify(
        patient_id,
        NotificationType.APPOINTMENT_BOOKED,
        'Appointment Booked',
        f'Your appointment on {appointment.appointment_date.strftime("%d %b %Y")} '
        f'at {appointment.start_time.strftime("%I:%M %p")} has been booked.',
        link=f'/appointments/{appointment.id}',
    )
    notify(
        doctor_user_id,
        NotificationType.APPOINTMENT_BOOKED,
        'New Appointment',
        f'You have a new appointment on {appointment.appointment_date.strftime("%d %b %Y")} '
        f'at {appointment.start_time.strftime("%I:%M %p")}.',
        link=f'/appointments/{appointment.id}',
    )


def notify_appointment_cancelled(user_id, appointment):
    notify(
        user_id,
        NotificationType.APPOINTMENT_CANCELLED,
        'Appointment Cancelled',
        f'Your appointment on {appointment.appointment_date.strftime("%d %b %Y")} '
        f'has been cancelled.',
        link=f'/appointments/{appointment.id}',
    )


def notify_prescription_created(patient_id, prescription):
    notify(
        patient_id,
        NotificationType.PRESCRIPTION_CREATED,
        'New Prescription',
        f'A new prescription ({prescription.prescription_uid}) has been issued for you.',
        link=f'/prescriptions/{prescription.id}',
    )


def notify_order_status(user_id, order, new_status):
    notify(
        user_id,
        NotificationType.ORDER_STATUS_CHANGED,
        f'Order {order.order_number} Update',
        f'Your order status has been updated to: {new_status.replace("_", " ").title()}',
        link=f'/pharmacy/orders/{order.id}',
    )


def notify_verification_update(doctor_user_id, status):
    ntype = (NotificationType.VERIFICATION_APPROVED
             if status == 'approved'
             else NotificationType.VERIFICATION_REJECTED)
    notify(
        doctor_user_id,
        ntype,
        f'Verification {status.title()}',
        f'Your doctor verification has been {status}.',
        link='/doctor/verification',
    )
