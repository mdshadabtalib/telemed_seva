"""User, PatientProfile, and DoctorProfile models."""
import enum
from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from ..extensions import db


class UserRole(enum.Enum):
    PATIENT = 'patient'
    DOCTOR = 'doctor'
    PHARMACY_ADMIN = 'pharmacy_admin'
    ADMIN = 'admin'


class User(UserMixin, db.Model):
    """Core user account — one per login, role-differentiated."""

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.Enum(UserRole), nullable=False, default=UserRole.PATIENT)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    email_verified = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    last_login_at = db.Column(db.DateTime)
    last_login_ip = db.Column(db.String(45))

    # Relationships
    patient_profile = db.relationship(
        'PatientProfile', backref='user', uselist=False, cascade='all, delete-orphan'
    )
    doctor_profile = db.relationship(
        'DoctorProfile', backref='user', uselist=False, cascade='all, delete-orphan'
    )
    addresses = db.relationship('Address', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='user', lazy='dynamic', cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def display_name(self):
        if self.role == UserRole.PATIENT and self.patient_profile:
            return self.patient_profile.full_name
        if self.role == UserRole.DOCTOR and self.doctor_profile:
            return f'Dr. {self.doctor_profile.full_name}'
        return self.email.split('@')[0]

    @property
    def avatar_url(self):
        profile = self.patient_profile or self.doctor_profile
        if profile and profile.avatar:
            return f'/uploads/avatars/{profile.avatar}'
        return None

    def __repr__(self):
        return f'<User {self.email} ({self.role.value})>'


class Gender(enum.Enum):
    MALE = 'male'
    FEMALE = 'female'
    OTHER = 'other'
    PREFER_NOT_TO_SAY = 'prefer_not_to_say'


class BloodGroup(enum.Enum):
    A_POSITIVE = 'A+'
    A_NEGATIVE = 'A-'
    B_POSITIVE = 'B+'
    B_NEGATIVE = 'B-'
    AB_POSITIVE = 'AB+'
    AB_NEGATIVE = 'AB-'
    O_POSITIVE = 'O+'
    O_NEGATIVE = 'O-'


class PatientProfile(db.Model):
    """Extended profile for patients — medical info, demographics."""

    __tablename__ = 'patient_profiles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.Enum(Gender))
    blood_group = db.Column(db.Enum(BloodGroup))
    avatar = db.Column(db.String(255))
    allergies = db.Column(db.Text)
    medical_history = db.Column(db.Text)
    emergency_contact_name = db.Column(db.String(200))
    emergency_contact_phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    @property
    def age(self):
        if self.date_of_birth:
            today = datetime.now(timezone.utc).date()
            return (
                today.year - self.date_of_birth.year
                - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
            )
        return None

    def __repr__(self):
        return f'<PatientProfile {self.full_name}>'


class DoctorProfile(db.Model):
    """Extended profile for doctors — professional info, verification status."""

    __tablename__ = 'doctor_profiles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    avatar = db.Column(db.String(255))

    # Professional
    specialty_id = db.Column(db.Integer, db.ForeignKey('specialties.id'), nullable=True)
    qualifications = db.Column(db.String(500))
    registration_number = db.Column(db.String(100))
    experience_years = db.Column(db.Integer, default=0)
    bio = db.Column(db.Text)
    languages = db.Column(db.String(300))

    # Consultation settings
    consultation_fee = db.Column(db.Numeric(10, 2), default=0)
    consultation_duration = db.Column(db.Integer, default=30)  # minutes

    # Status
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    is_available = db.Column(db.Boolean, default=True, nullable=False)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    specialty = db.relationship('Specialty', backref='doctors')
    verification = db.relationship(
        'DoctorVerification', backref='doctor', uselist=False, cascade='all, delete-orphan'
    )
    availabilities = db.relationship('Availability', backref='doctor', cascade='all, delete-orphan')
    reviews = db.relationship('Review', backref='doctor', lazy='dynamic')

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    @property
    def average_rating(self):
        from .review import Review
        result = db.session.query(db.func.avg(Review.rating)).filter(
            Review.doctor_id == self.id
        ).scalar()
        return round(float(result), 1) if result else 0.0

    @property
    def review_count(self):
        from .review import Review
        return Review.query.filter_by(doctor_id=self.id).count()

    @property
    def verification_status(self):
        if self.verification:
            return self.verification.status.value
        return 'not_submitted'

    @property
    def languages_list(self):
        if self.languages:
            return [lang.strip() for lang in self.languages.split(',')]
        return []

    def __repr__(self):
        return f'<DoctorProfile Dr. {self.full_name}>'
