"""Security utilities — headers, audit logging, sanitisation."""
from flask import request
from ..extensions import db
from ..models.audit import AuditLog


def add_security_headers(response):
    """Add security headers to every response."""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
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
