"""Security utilities — headers, audit logging, sanitisation."""
from flask import request, current_app
from ..extensions import db
from ..models.audit import AuditLog


def add_security_headers(response):
    """Add security headers to every response."""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

    # Allow camera/microphone for the consultation room; geolocation not needed.
    response.headers['Permissions-Policy'] = (
        "camera=(self), microphone=(self), geolocation=()"
    )

    # Content-Security-Policy
    # Jitsi Meet is loaded from meet.jit.si in an iframe — allow that origin.
    csp_parts = [
        "default-src 'self'",
        "script-src 'self' 'unsafe-inline'",   # inline JS in templates (forms, modals)
        "style-src 'self' 'unsafe-inline'",    # inline styles
        "img-src 'self' data: https:",         # avatars, medicine images
        "font-src 'self' data:",
        "connect-src 'self'",                  # AJAX polling
        "frame-src 'self' https://meet.jit.si",  # Jitsi Meet iframe
        "object-src 'none'",
        "base-uri 'self'",
        "form-action 'self'",
    ]
    response.headers['Content-Security-Policy'] = '; '.join(csp_parts)

    return response


def log_audit(user_id, action, resource_type, resource_id=None, details=None):
    """Write an entry to the audit log."""
    entry = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=request.remote_addr if request else None,
        user_agent=str(request.user_agent) if request else None,
    )
    db.session.add(entry)
    # Don't commit — let the caller's transaction handle it
