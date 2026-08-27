"""TeleMed Seva — Application factory.

Creates and configures the Flask application, registers blueprints,
error handlers, template context processors, and CLI commands.
"""
import os
import logging
from logging.handlers import RotatingFileHandler

from flask import Flask, render_template, request, send_from_directory
from werkzeug.exceptions import HTTPException

from .config import config
from .extensions import db, migrate, login_manager, csrf, limiter, mail
from .utils.security import add_security_headers


def create_app(config_name=None):
    """Application factory.

    Args:
        config_name: One of 'development', 'testing', 'production'.
                     Defaults to the FLASK_ENV env var or 'development'.
    """
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Call init_app if the config class defines it
    if hasattr(config[config_name], 'init_app'):
        config[config_name].init_app(app)

    _init_extensions(app)
    _register_blueprints(app)
    _register_error_handlers(app)
    _register_context_processors(app)
    _register_cli_commands(app)
    _ensure_directories(app)
    _configure_logging(app)

    # Security headers
    app.after_request(add_security_headers)

    # Static uploads route — authentication required; only known subfolders served
    ALLOWED_UPLOAD_FOLDERS = frozenset([
        'avatars', 'documents', 'prescriptions', 'medicines', 'reports',
    ])

    @app.route('/uploads/<folder>/<filename>')
    def uploaded_file(folder, filename):
        from flask_login import current_user
        if folder not in ALLOWED_UPLOAD_FOLDERS:
            from flask import abort
            abort(404)
        # Prescription and medical documents require login
        if folder in ('prescriptions', 'documents', 'reports'):
            if not current_user.is_authenticated:
                from flask import redirect, url_for
                return redirect(url_for('auth.login'))
        folder_path = os.path.join(app.config['UPLOAD_FOLDER'], folder)
        return send_from_directory(folder_path, filename)

    # Health-check — used by Docker/load-balancer probes
    @app.route('/health')
    def health():
        from flask import jsonify
        try:
            db.session.execute(db.text('SELECT 1'))
            return jsonify({'status': 'ok', 'db': 'ok'}), 200
        except Exception as exc:
            return jsonify({'status': 'error', 'db': str(exc)}), 503

    return app


def _init_extensions(app):
    """Bind extension instances to the app."""
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)

    # Limiter may be disabled in dev/test
    if app.config.get('RATELIMIT_ENABLED', True):
        limiter.init_app(app)
    else:
        limiter.enabled = False
        limiter.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        from .models.user import User
        return db.session.get(User, int(user_id))


def _register_blueprints(app):
    """Register all route blueprints."""
    from .auth import auth_bp
    from .patient import patient_bp
    from .doctor import doctor_bp
    from .appointments import appointments_bp
    from .consultation import consultation_bp
    from .prescriptions import prescriptions_bp
    from .pharmacy import pharmacy_bp
    from .payments import payments_bp
    from .admin import admin_bp
    from .notifications import notifications_bp
    from .api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(patient_bp, url_prefix='/patient')
    app.register_blueprint(doctor_bp, url_prefix='/doctor')
    app.register_blueprint(appointments_bp, url_prefix='/appointments')
    app.register_blueprint(consultation_bp, url_prefix='/consultation')
    app.register_blueprint(prescriptions_bp, url_prefix='/prescriptions')
    app.register_blueprint(pharmacy_bp, url_prefix='/pharmacy')
    app.register_blueprint(payments_bp, url_prefix='/payments')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(notifications_bp, url_prefix='/notifications')
    app.register_blueprint(api_bp, url_prefix='/api')


def _register_error_handlers(app):
    """Register custom error pages."""

    @app.errorhandler(400)
    def bad_request(e):
        if request.accept_mimetypes.accept_json and \
                not request.accept_mimetypes.accept_html:
            return {'error': 'Bad request'}, 400
        return render_template('errors/400.html'), 400

    @app.errorhandler(401)
    def unauthorized(e):
        if request.accept_mimetypes.accept_json and \
                not request.accept_mimetypes.accept_html:
            return {'error': 'Unauthorized'}, 401
        return render_template('errors/401.html'), 401

    @app.errorhandler(403)
    def forbidden(e):
        if request.accept_mimetypes.accept_json and \
                not request.accept_mimetypes.accept_html:
            return {'error': 'Forbidden'}, 403
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found(e):
        if request.accept_mimetypes.accept_json and \
                not request.accept_mimetypes.accept_html:
            return {'error': 'Not found'}, 404
        return render_template('errors/404.html'), 404

    @app.errorhandler(429)
    def too_many_requests(e):
        if request.accept_mimetypes.accept_json and \
                not request.accept_mimetypes.accept_html:
            return {'error': 'Too many requests'}, 429
        return render_template('errors/429.html'), 429

    @app.errorhandler(500)
    def internal_error(e):
        db.session.rollback()
        if request.accept_mimetypes.accept_json and \
                not request.accept_mimetypes.accept_html:
            return {'error': 'Internal server error'}, 500
        return render_template('errors/500.html'), 500


def _register_context_processors(app):
    """Inject common variables into all templates."""
    from datetime import datetime, timezone

    @app.context_processor
    def inject_platform():
        return {
            'platform_name': app.config['PLATFORM_NAME'],
            'currency': app.config['PLATFORM_CURRENCY_SYMBOL'],
            'now': lambda: datetime.now(timezone.utc),
        }

    @app.context_processor
    def inject_notification_count():
        from flask_login import current_user
        if current_user.is_authenticated:
            from .models.notification import Notification
            count = Notification.query.filter_by(
                user_id=current_user.id, is_read=False
            ).count()
            return {'unread_notification_count': count}
        return {'unread_notification_count': 0}


def _register_cli_commands(app):
    """Register custom Flask CLI commands."""

    @app.cli.command('seed-db')
    def seed_db():
        """Seed the database with initial data (specialties, categories, admin)."""
        from .utils.seed import seed_database
        seed_database()

    @app.cli.command('seed-medicines')
    def seed_medicines_cmd():
        """Seed comprehensive medicine database with 100+ medicines."""
        from .utils.seed_medicines import seed_medicines
        seed_medicines()

    @app.cli.command('create-admin')
    def create_admin():
        """Create a superadmin user."""
        from .utils.seed import create_admin_user
        create_admin_user()


def _ensure_directories(app):
    """Create required directories if they don't exist."""
    upload_dir = app.config['UPLOAD_FOLDER']
    for subdir in ['avatars', 'documents', 'prescriptions', 'medicines', 'reports']:
        path = os.path.join(upload_dir, subdir)
        os.makedirs(path, exist_ok=True)


def _configure_logging(app):
    """Set up file-based logging for non-debug mode."""
    if not app.debug and not app.testing:
        log_dir = os.path.join(os.path.dirname(app.root_path), 'logs')
        os.makedirs(log_dir, exist_ok=True)

        file_handler = RotatingFileHandler(
            os.path.join(log_dir, 'telemed_seva.log'),
            maxBytes=10 * 1024 * 1024,
            backupCount=10,
        )
        file_handler.setFormatter(logging.Formatter(
            '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('TeleMed Seva startup')
