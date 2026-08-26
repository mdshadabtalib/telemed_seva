"""Custom WTForms validators."""
import re

from wtforms.validators import ValidationError


class StrongPassword:
    """Validate password strength."""

    def __init__(self, min_length=8, message=None):
        self.min_length = min_length
        self.message = message

    def __call__(self, form, field):
        password = field.data or ''
        errors = []
        if len(password) < self.min_length:
            errors.append(f'at least {self.min_length} characters')
        if not re.search(r'[A-Z]', password):
            errors.append('an uppercase letter')
        if not re.search(r'[a-z]', password):
            errors.append('a lowercase letter')
        if not re.search(r'\d', password):
            errors.append('a digit')
        if errors:
            msg = self.message or f'Password must contain {", ".join(errors)}.'
            raise ValidationError(msg)


class IndianPhone:
    """Validate Indian phone number format."""

    def __init__(self, message=None):
        self.message = message or 'Enter a valid 10-digit phone number.'

    def __call__(self, form, field):
        if field.data:
            cleaned = re.sub(r'[\s\-\+]', '', field.data)
            if cleaned.startswith('91'):
                cleaned = cleaned[2:]
            if not re.match(r'^[6-9]\d{9}$', cleaned):
                raise ValidationError(self.message)


class Pincode:
    """Validate Indian pincode."""

    def __init__(self, message=None):
        self.message = message or 'Enter a valid 6-digit pincode.'

    def __call__(self, form, field):
        if field.data:
            if not re.match(r'^\d{6}$', field.data.strip()):
                raise ValidationError(self.message)
