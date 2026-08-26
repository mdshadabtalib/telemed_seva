"""Authorization decorators for role-based access control."""
from functools import wraps

from flask import abort, flash, redirect, url_for
from flask_login import current_user, login_required

from ..models.user import UserRole


def role_required(*roles):
    """Restrict access to users with one of the specified roles.

    Usage:
        @role_required(UserRole.PATIENT)
        @role_required(UserRole.DOCTOR, UserRole.ADMIN)
    """
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if current_user.role not in roles:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f):
    """Restrict access to admin users."""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if current_user.role != UserRole.ADMIN:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def verified_doctor_required(f):
    """Restrict access to verified doctors only."""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if current_user.role != UserRole.DOCTOR:
            abort(403)
        if not current_user.doctor_profile or not current_user.doctor_profile.is_verified:
            flash('Your account must be verified before you can access this feature.', 'warning')
            return redirect(url_for('doctor.verification'))
        return f(*args, **kwargs)
    return decorated_function


def patient_required(f):
    """Restrict access to patients."""
    return role_required(UserRole.PATIENT)(f)


def pharmacy_admin_required(f):
    """Restrict access to pharmacy admins or platform admins."""
    return role_required(UserRole.PHARMACY_ADMIN, UserRole.ADMIN)(f)
