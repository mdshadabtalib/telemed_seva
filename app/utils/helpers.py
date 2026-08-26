"""General helper utilities — file uploads, pagination, slugs."""
import os
import re
import uuid
from datetime import datetime, timezone

from flask import current_app, request
from werkzeug.utils import secure_filename


def allowed_file(filename, allowed_extensions=None):
    """Check if a filename has an allowed extension."""
    if allowed_extensions is None:
        allowed_extensions = current_app.config.get(
            'ALLOWED_DOCUMENT_EXTENSIONS', {'pdf', 'png', 'jpg', 'jpeg'}
        )
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


def save_upload(file, subfolder='documents', allowed_extensions=None):
    """Save an uploaded file and return the filename (not full path).

    Returns None if the file is invalid.
    """
    if not file or file.filename == '':
        return None
    if not allowed_file(file.filename, allowed_extensions):
        return None

    filename = secure_filename(file.filename)
    # Prefix with UUID to prevent collisions
    unique_name = f'{uuid.uuid4().hex[:12]}_{filename}'

    upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], subfolder)
    os.makedirs(upload_dir, exist_ok=True)

    file.save(os.path.join(upload_dir, unique_name))
    return unique_name


def delete_upload(filename, subfolder='documents'):
    """Delete an uploaded file by name."""
    if not filename:
        return
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], subfolder, filename)
    if os.path.exists(filepath):
        os.remove(filepath)


def slugify(text):
    """Convert text to a URL-safe slug."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')


def paginate_query(query, page=None, per_page=20, max_per_page=100):
    """Apply pagination to a SQLAlchemy query.

    Returns a Flask-SQLAlchemy pagination object.
    """
    if page is None:
        page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', per_page, type=int), max_per_page)
    return query.paginate(page=page, per_page=per_page, error_out=False)


def format_currency(amount, symbol=None):
    """Format a numeric amount as currency."""
    if symbol is None:
        symbol = current_app.config.get('PLATFORM_CURRENCY_SYMBOL', '₹')
    if amount is None:
        return f'{symbol}0.00'
    return f'{symbol}{float(amount):,.2f}'


def utcnow():
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(timezone.utc)
