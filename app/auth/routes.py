"""Authentication routes — register, login, logout, email verification, password reset."""
from datetime import datetime, timezone

from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user

from . import auth_bp
from .forms import LoginForm, RegistrationForm, ForgotPasswordForm, ResetPasswordForm
from ..extensions import db, limiter
from ..models.user import User, UserRole, PatientProfile, DoctorProfile
from ..utils.security import log_audit
from ..utils.tokens import verify_email_token, verify_password_reset_token
from ..utils.email import send_verification_email, send_password_reset_email


@auth_bp.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for(_dashboard_for(current_user)))
    return render_template('home.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
@limiter.limit('10 per hour')
def register():
    if current_user.is_authenticated:
        return redirect(url_for(_dashboard_for(current_user)))

    form = RegistrationForm()
    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        role = UserRole(form.role.data)

        user = User(email=email, role=role, is_active=True)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.flush()  # get user.id

        # Create role-specific profile
        if role == UserRole.PATIENT:
            profile = PatientProfile(
                user_id=user.id,
                first_name=form.first_name.data.strip(),
                last_name=form.last_name.data.strip(),
                phone=form.phone.data.strip() if form.phone.data else None,
            )
            db.session.add(profile)
        elif role == UserRole.DOCTOR:
            profile = DoctorProfile(
                user_id=user.id,
                first_name=form.first_name.data.strip(),
                last_name=form.last_name.data.strip(),
                phone=form.phone.data.strip() if form.phone.data else None,
            )
            db.session.add(profile)

        log_audit(user.id, 'register', 'user', user.id)
        db.session.commit()

        # Send verification email (non-blocking — failure is logged, not raised)
        send_verification_email(user)

        flash(
            'Account created! Check your email for a verification link, '
            'then log in.',
            'success',
        )
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', form=form, title='Create Account')


@auth_bp.route('/verify-email/<token>')
def verify_email(token):
    """Confirm a user's email address via signed token."""
    user_id = verify_email_token(token)
    if user_id is None:
        flash('The verification link is invalid or has expired.', 'danger')
        return redirect(url_for('auth.login'))

    user = db.session.get(User, user_id)
    if user is None:
        flash('Account not found.', 'danger')
        return redirect(url_for('auth.login'))

    if user.email_verified:
        flash('Your email is already verified. Please log in.', 'info')
        return redirect(url_for('auth.login'))

    user.email_verified = True
    log_audit(user.id, 'verify_email', 'user', user.id)
    db.session.commit()

    flash('Email verified successfully! You can now log in.', 'success')
    return redirect(url_for('auth.login'))


@auth_bp.route('/resend-verification')
@login_required
def resend_verification():
    """Resend the verification email for the current user."""
    if current_user.email_verified:
        flash('Your email is already verified.', 'info')
        return redirect(url_for(_dashboard_for(current_user)))

    sent = send_verification_email(current_user)
    if sent:
        flash('A new verification email has been sent.', 'success')
    else:
        flash(
            'Could not send verification email. '
            'Email is not configured — contact support.',
            'warning',
        )
    return redirect(url_for(_dashboard_for(current_user)))


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
@limiter.limit('5 per hour')
def forgot_password():
    """Request a password-reset email."""
    if current_user.is_authenticated:
        return redirect(url_for(_dashboard_for(current_user)))

    form = ForgotPasswordForm()
    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        user = User.query.filter_by(email=email).first()

        # Always show the same message to prevent email enumeration
        if user and user.is_active:
            send_password_reset_email(user)
            log_audit(user.id, 'request_password_reset', 'user', user.id)
            db.session.commit()

        flash(
            'If that email is registered, a reset link has been sent. '
            'Check your inbox (and spam folder).',
            'info',
        )
        return redirect(url_for('auth.login'))

    return render_template('auth/forgot_password.html', form=form, title='Forgot Password')


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
@limiter.limit('10 per hour')
def reset_password(token):
    """Reset a password using a signed token."""
    if current_user.is_authenticated:
        return redirect(url_for(_dashboard_for(current_user)))

    user_id = verify_password_reset_token(token)
    if user_id is None:
        flash('The reset link is invalid or has expired. Please request a new one.', 'danger')
        return redirect(url_for('auth.forgot_password'))

    user = db.session.get(User, user_id)
    if user is None or not user.is_active:
        flash('Account not found or deactivated.', 'danger')
        return redirect(url_for('auth.forgot_password'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        log_audit(user.id, 'reset_password', 'user', user.id)
        db.session.commit()
        flash('Password reset successfully. Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template(
        'auth/reset_password.html', form=form, token=token, title='Reset Password'
    )


@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit('20 per hour')
def login():
    if current_user.is_authenticated:
        return redirect(url_for(_dashboard_for(current_user)))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()

        if user is None or not user.check_password(form.password.data):
            flash('Invalid email or password.', 'danger')
            return render_template('auth/login.html', form=form, title='Log In')

        if not user.is_active:
            flash('Your account has been deactivated. Contact support.', 'danger')
            return render_template('auth/login.html', form=form, title='Log In')

        login_user(user, remember=form.remember_me.data)
        user.last_login_at = datetime.now(timezone.utc)
        user.last_login_ip = request.remote_addr
        log_audit(user.id, 'login', 'user', user.id)
        db.session.commit()

        next_page = request.args.get('next')
        if next_page and not _is_safe_url(next_page):
            next_page = None
        return redirect(next_page or url_for(_dashboard_for(user)))

    return render_template('auth/login.html', form=form, title='Log In')


@auth_bp.route('/logout')
@login_required
def logout():
    log_audit(current_user.id, 'logout', 'user', current_user.id)
    db.session.commit()
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


def _dashboard_for(user):
    """Return the dashboard endpoint for a user's role."""
    role_dashboards = {
        UserRole.PATIENT: 'patient.dashboard',
        UserRole.DOCTOR: 'doctor.dashboard',
        UserRole.PHARMACY_ADMIN: 'admin.pharmacy_dashboard',
        UserRole.ADMIN: 'admin.dashboard',
    }
    return role_dashboards.get(user.role, 'auth.login')


def _is_safe_url(target):
    """Basic open-redirect protection."""
    from urllib.parse import urlparse, urljoin
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

