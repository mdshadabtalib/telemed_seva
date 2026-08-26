"""Email sending helpers.

All emails go through this module so the rest of the app never calls
Flask-Mail directly.  If MAIL_USERNAME is not configured the function
logs a warning and returns gracefully — useful during development.
"""
import logging
from flask import current_app, url_for, render_template_string
from flask_mail import Message

from ..extensions import mail

logger = logging.getLogger(__name__)


def _send(subject: str, recipients: list[str], html_body: str, text_body: str = '') -> bool:
    """Low-level send helper.  Returns True on success, False otherwise."""
    if not current_app.config.get('MAIL_USERNAME'):
        logger.warning(
            'MAIL_USERNAME not configured — email to %s suppressed. '
            'Subject: %s', recipients, subject
        )
        return False
    try:
        msg = Message(
            subject=subject,
            recipients=recipients,
            html=html_body,
            body=text_body or 'Please view this email in an HTML-capable client.',
            sender=current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@telemedseva.com'),
        )
        mail.send(msg)
        return True
    except Exception as exc:
        logger.error('Failed to send email to %s: %s', recipients, exc)
        return False


# --------------------------------------------------------------------------- #
# Specific email senders
# --------------------------------------------------------------------------- #

def send_verification_email(user) -> bool:
    """Send an account email-verification link to the user."""
    from ..utils.tokens import generate_email_verification_token

    token = generate_email_verification_token(user.id)
    verify_url = url_for('auth.verify_email', token=token, _external=True)
    platform = current_app.config.get('PLATFORM_NAME', 'TeleMed Seva')

    html = _render_email_template(
        title='Verify your email address',
        greeting=f'Hello {user.display_name},',
        body=(
            f'Thank you for registering with <strong>{platform}</strong>. '
            'Please click the button below to verify your email address. '
            'This link expires in 24 hours.'
        ),
        cta_text='Verify Email',
        cta_url=verify_url,
        footer_note='If you did not create this account, you can safely ignore this email.',
    )
    return _send(
        subject=f'[{platform}] Verify your email',
        recipients=[user.email],
        html_body=html,
    )


def send_password_reset_email(user) -> bool:
    """Send a password-reset link to the user."""
    from ..utils.tokens import generate_password_reset_token

    token = generate_password_reset_token(user.id)
    reset_url = url_for('auth.reset_password', token=token, _external=True)
    platform = current_app.config.get('PLATFORM_NAME', 'TeleMed Seva')

    html = _render_email_template(
        title='Reset your password',
        greeting=f'Hello {user.display_name},',
        body=(
            f'We received a request to reset the password for your <strong>{platform}</strong> '
            'account. Click the button below to choose a new password. '
            'This link expires in 1 hour.'
        ),
        cta_text='Reset Password',
        cta_url=reset_url,
        footer_note='If you did not request a password reset, please ignore this email.',
    )
    return _send(
        subject=f'[{platform}] Reset your password',
        recipients=[user.email],
        html_body=html,
    )


def send_appointment_reminder(user, appointment) -> bool:
    """Send an appointment reminder email."""
    platform = current_app.config.get('PLATFORM_NAME', 'TeleMed Seva')
    appt_url = url_for('appointments.detail', appointment_id=appointment.id, _external=True)

    html = _render_email_template(
        title='Appointment Reminder',
        greeting=f'Hello {user.display_name},',
        body=(
            f'This is a reminder that you have an upcoming appointment on '
            f'<strong>{appointment.appointment_date.strftime("%d %b %Y")}</strong> '
            f'at <strong>{appointment.start_time.strftime("%I:%M %p")}</strong>.'
        ),
        cta_text='View Appointment',
        cta_url=appt_url,
        footer_note='',
    )
    return _send(
        subject=f'[{platform}] Appointment Reminder',
        recipients=[user.email],
        html_body=html,
    )


# --------------------------------------------------------------------------- #
# Simple reusable email template (inline, no Jinja2 file needed)
# --------------------------------------------------------------------------- #

def _render_email_template(title, greeting, body, cta_text, cta_url, footer_note='') -> str:
    platform = 'TeleMed Seva'
    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>{title}</title></head>
<body style="font-family:Arial,sans-serif;background:#f4f7f9;margin:0;padding:0;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f7f9;padding:40px 0;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0"
             style="background:#ffffff;border-radius:8px;overflow:hidden;
                    box-shadow:0 2px 8px rgba(0,0,0,0.08);">
        <!-- Header -->
        <tr>
          <td style="background:#0284c7;padding:24px 32px;">
            <span style="color:#ffffff;font-size:22px;font-weight:bold;">{platform}</span>
          </td>
        </tr>
        <!-- Body -->
        <tr>
          <td style="padding:32px;">
            <h2 style="color:#1e293b;margin:0 0 16px;">{title}</h2>
            <p style="color:#475569;margin:0 0 12px;">{greeting}</p>
            <p style="color:#475569;margin:0 0 24px;">{body}</p>
            <a href="{cta_url}"
               style="display:inline-block;background:#0284c7;color:#ffffff;
                      padding:12px 28px;border-radius:6px;text-decoration:none;
                      font-weight:bold;font-size:15px;">{cta_text}</a>
            <p style="color:#94a3b8;font-size:12px;margin:24px 0 0;">
              Or copy this link: <a href="{cta_url}" style="color:#0284c7;">{cta_url}</a>
            </p>
          </td>
        </tr>
        <!-- Footer -->
        <tr>
          <td style="background:#f8fafc;padding:16px 32px;border-top:1px solid #e2e8f0;">
            <p style="color:#94a3b8;font-size:12px;margin:0;">
              {footer_note}<br>
              &copy; {platform}. All rights reserved.
            </p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>
"""
