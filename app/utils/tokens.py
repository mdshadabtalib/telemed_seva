"""Signed token generation and verification for email flows.

Uses itsdangerous (bundled with Flask) — no extra dependency.
"""
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from flask import current_app


def _serializer(salt: str) -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'], salt=salt)


# --------------------------------------------------------------------------- #
# Email verification
# --------------------------------------------------------------------------- #

def generate_email_verification_token(user_id: int) -> str:
    """Create a signed token that encodes the user id for email verification."""
    return _serializer('email-verify').dumps(user_id)


def verify_email_token(token: str, max_age_seconds: int = 86_400) -> int | None:
    """Decode and validate an email verification token.

    Returns the user_id on success or None on failure/expiry.
    """
    try:
        user_id = _serializer('email-verify').loads(token, max_age=max_age_seconds)
        return user_id
    except (SignatureExpired, BadSignature):
        return None


# --------------------------------------------------------------------------- #
# Password reset
# --------------------------------------------------------------------------- #

def generate_password_reset_token(user_id: int) -> str:
    """Create a signed token for password reset (valid 1 hour)."""
    return _serializer('password-reset').dumps(user_id)


def verify_password_reset_token(token: str, max_age_seconds: int = 3_600) -> int | None:
    """Decode and validate a password-reset token.

    Returns the user_id on success or None on failure/expiry.
    """
    try:
        user_id = _serializer('password-reset').loads(token, max_age=max_age_seconds)
        return user_id
    except (SignatureExpired, BadSignature):
        return None
