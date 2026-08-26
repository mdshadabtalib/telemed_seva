"""Address model."""
from datetime import datetime, timezone

from ..extensions import db


class Address(db.Model):
    """Delivery address for a user."""

    __tablename__ = 'addresses'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True
    )
    label = db.Column(db.String(50), default='Home')  # Home / Office / Other
    full_name = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    line1 = db.Column(db.String(300), nullable=False)
    line2 = db.Column(db.String(300))
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=False)
    pincode = db.Column(db.String(10), nullable=False)
    is_default = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    @property
    def full_address(self):
        parts = [self.line1]
        if self.line2:
            parts.append(self.line2)
        parts.extend([self.city, self.state, self.pincode])
        return ', '.join(parts)

    def __repr__(self):
        return f'<Address {self.label} user={self.user_id}>'
