"""WTForms form definitions for all non-auth flows.

Centralised here so every POST handler has server-side validation
rather than raw request.form access.
"""
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileSize
from wtforms import (
    StringField, TextAreaField, IntegerField, SelectField,
    DecimalField, BooleanField, SubmitField, HiddenField,
    TimeField, PasswordField,
)
from wtforms.fields import DateField
from wtforms.validators import (
    DataRequired, Optional, Length, NumberRange, Email, ValidationError, InputRequired,
)

from .validators import StrongPassword, IndianPhone, Pincode
from ..models.user import Gender, BloodGroup
from ..models.doctor import DayOfWeek
from ..models.pharmacy import DosageForm
from ..models.support import TicketPriority


# ─────────────────────────────────────────────────────────────────────────────
# Patient profile
# ─────────────────────────────────────────────────────────────────────────────

class PatientProfileForm(FlaskForm):
    first_name  = StringField('First Name',  validators=[DataRequired(), Length(max=100)])
    last_name   = StringField('Last Name',   validators=[DataRequired(), Length(max=100)])
    phone       = StringField('Phone',       validators=[Optional(), IndianPhone(), Length(max=20)])
    date_of_birth = DateField('Date of Birth', validators=[Optional()])
    gender      = SelectField(
        'Gender',
        choices=[('', 'Select…')] + [(g.value, g.value.replace('_', ' ').title()) for g in Gender],
        validators=[Optional()],
    )
    blood_group = SelectField(
        'Blood Group',
        choices=[('', 'Select…')] + [(b.value, b.value) for b in BloodGroup],
        validators=[Optional()],
    )
    allergies           = TextAreaField('Allergies',         validators=[Optional(), Length(max=1000)])
    medical_history     = TextAreaField('Medical History',   validators=[Optional(), Length(max=2000)])
    emergency_contact_name  = StringField('Emergency Contact Name',  validators=[Optional(), Length(max=200)])
    emergency_contact_phone = StringField('Emergency Contact Phone', validators=[Optional(), Length(max=20)])
    avatar = FileField('Profile Photo', validators=[
        Optional(),
        FileAllowed(['png', 'jpg', 'jpeg', 'webp'], 'Images only.'),
        FileSize(max_size=5 * 1024 * 1024, message='Max file size is 5 MB.'),
    ])
    submit = SubmitField('Save Profile')


# ─────────────────────────────────────────────────────────────────────────────
# Doctor profile
# ─────────────────────────────────────────────────────────────────────────────

class DoctorProfileForm(FlaskForm):
    first_name           = StringField('First Name',   validators=[DataRequired(), Length(max=100)])
    last_name            = StringField('Last Name',    validators=[DataRequired(), Length(max=100)])
    phone                = StringField('Phone',        validators=[Optional(), IndianPhone(), Length(max=20)])
    bio                  = TextAreaField('About Me',   validators=[Optional(), Length(max=2000)])
    qualifications       = StringField('Qualifications', validators=[Optional(), Length(max=500)])
    registration_number  = StringField('Registration No.', validators=[Optional(), Length(max=100)])
    languages            = StringField('Languages (comma-separated)', validators=[Optional(), Length(max=300)])
    experience_years     = IntegerField('Years of Experience', validators=[Optional(), NumberRange(min=0, max=60)])
    consultation_fee     = DecimalField('Consultation Fee (₹)', places=2, validators=[Optional(), NumberRange(min=0)])
    consultation_duration = IntegerField('Consultation Duration (min)', validators=[Optional(), NumberRange(min=10, max=120)])
    specialty_id         = SelectField('Specialty', coerce=int, validators=[Optional()])
    avatar = FileField('Profile Photo', validators=[
        Optional(),
        FileAllowed(['png', 'jpg', 'jpeg', 'webp'], 'Images only.'),
        FileSize(max_size=5 * 1024 * 1024, message='Max file size is 5 MB.'),
    ])
    submit = SubmitField('Save Profile')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate specialty choices at form instantiation time
        from ..models.doctor import Specialty
        specs = Specialty.query.filter_by(is_active=True).order_by(Specialty.name).all()
        self.specialty_id.choices = [(0, 'Select specialty…')] + [(s.id, s.name) for s in specs]


# ─────────────────────────────────────────────────────────────────────────────
# Doctor availability
# ─────────────────────────────────────────────────────────────────────────────

class AvailabilityForm(FlaskForm):
    day_of_week = SelectField(
        'Day',
        coerce=int,
        choices=[(d.value, d.name.title()) for d in DayOfWeek],
        validators=[InputRequired()],  # InputRequired allows 0 (Monday)
    )
    start_time    = TimeField('Start Time',    validators=[DataRequired()])
    end_time      = TimeField('End Time',      validators=[DataRequired()])
    slot_duration = SelectField(
        'Slot Duration',
        coerce=int,
        choices=[(10,'10 min'),(15,'15 min'),(20,'20 min'),(30,'30 min'),
                 (45,'45 min'),(60,'60 min')],
        default=30,
        validators=[InputRequired()],  # InputRequired allows integer values including edge cases
    )
    submit = SubmitField('Add Slot')

    def validate_end_time(self, field):
        if self.start_time.data and field.data:
            if field.data <= self.start_time.data:
                raise ValidationError('End time must be after start time.')


# ─────────────────────────────────────────────────────────────────────────────
# Address
# ─────────────────────────────────────────────────────────────────────────────

class AddressForm(FlaskForm):
    label      = SelectField('Label', choices=[('Home', 'Home'), ('Office', 'Office'), ('Other', 'Other')])
    full_name  = StringField('Full Name',    validators=[DataRequired(), Length(max=200)])
    phone      = StringField('Phone',        validators=[DataRequired(), IndianPhone(), Length(max=20)])
    line1      = StringField('Address Line 1', validators=[DataRequired(), Length(max=300)])
    line2      = StringField('Address Line 2', validators=[Optional(), Length(max=300)])
    city       = StringField('City',         validators=[DataRequired(), Length(max=100)])
    state      = StringField('State',        validators=[DataRequired(), Length(max=100)])
    pincode    = StringField('PIN Code',     validators=[DataRequired(), Pincode()])
    submit = SubmitField('Save Address')


# ─────────────────────────────────────────────────────────────────────────────
# Prescription
# ─────────────────────────────────────────────────────────────────────────────

class PrescriptionForm(FlaskForm):
    """Header-level prescription data. Medicine rows are handled as field arrays."""
    diagnosis  = TextAreaField('Diagnosis / Clinical Notes', validators=[Optional(), Length(max=2000)])
    advice     = TextAreaField('Additional Advice',          validators=[Optional(), Length(max=1000)])
    submit = SubmitField('Save Prescription')


# ─────────────────────────────────────────────────────────────────────────────
# Pharmacy checkout
# ─────────────────────────────────────────────────────────────────────────────

class CheckoutForm(FlaskForm):
    address_id      = SelectField('Delivery Address', coerce=int, validators=[DataRequired()])
    prescription_id = SelectField('Select Existing Prescription',
                                   coerce=int, validators=[Optional()])
    prescription_image = FileField('Upload Prescription', validators=[
        Optional(),
        FileAllowed(['pdf', 'png', 'jpg', 'jpeg'], 'PDF or image only.'),
        FileSize(max_size=8 * 1024 * 1024, message='Max file size is 8 MB.'),
    ])
    submit = SubmitField('Place Order')

    def __init__(self, user_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from ..models.address import Address
        from ..models.prescription import Prescription
        addrs = Address.query.filter_by(user_id=user_id).all()
        self.address_id.choices = [(a.id, f'{a.label} — {a.full_address}') for a in addrs]
        rxs = Prescription.query.filter_by(patient_id=user_id, is_active=True).all()
        self.prescription_id.choices = [(0, 'None')] + [
            (r.id, f'{r.prescription_uid} ({r.created_at.strftime("%d %b %Y")})') for r in rxs
        ]


# ─────────────────────────────────────────────────────────────────────────────
# Support ticket
# ─────────────────────────────────────────────────────────────────────────────

class SupportTicketForm(FlaskForm):
    subject     = StringField('Subject',     validators=[DataRequired(), Length(max=200)])
    priority    = SelectField(
        'Priority',
        choices=[(p.value, p.value.title()) for p in TicketPriority],
        default='medium',
    )
    description = TextAreaField('Description', validators=[DataRequired(), Length(max=3000)])
    submit = SubmitField('Submit Ticket')


# ─────────────────────────────────────────────────────────────────────────────
# Change password (authenticated)
# ─────────────────────────────────────────────────────────────────────────────

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password     = PasswordField('New Password', validators=[
        DataRequired(), Length(min=8), StrongPassword()
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
    ])
    submit = SubmitField('Change Password')

    def validate_confirm_password(self, field):
        if field.data != self.new_password.data:
            raise ValidationError('Passwords must match.')
