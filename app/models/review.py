"""Review / Rating model."""
from datetime import datetime, timezone

from ..extensions import db


class Review(db.Model):
    """Patient review of a doctor after a completed consultation."""

    __tablename__ = 'reviews'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(
        db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False
    )
    doctor_id = db.Column(
        db.Integer,
        db.ForeignKey('doctor_profiles.id', ondelete='CASCADE'),
        nullable=False,
    )
    appointment_id = db.Column(
        db.Integer,
        db.ForeignKey('appointments.id', ondelete='SET NULL'),
        nullable=True,
        unique=True,
    )
    rating = db.Column(db.Integer, nullable=False)  # 1-5
    comment = db.Column(db.Text)
    is_visible = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    patient = db.relationship('User', backref='written_reviews')

    __table_args__ = (
        db.CheckConstraint('rating >= 1 AND rating <= 5', name='ck_review_rating'),
    )

    def __repr__(self):
        return f'<Review doctor={self.doctor_id} rating={self.rating}>'
