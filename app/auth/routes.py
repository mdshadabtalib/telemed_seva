"""Authentication routes — register, login, logout."""
from datetime import datetime, timezone

from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user

from . import auth_bp
from .forms import LoginForm, RegistrationForm
from ..extensions import db
from ..models.user import User, UserRole, PatientProfile, DoctorProfile
from ..utils.security import log_audit


@auth_bp.route('/register', methods=['GET', 'POST'])
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

        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', form=form, title='Create Account')


@auth_bp.route('/login', methods=['GET', 'POST'])
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
