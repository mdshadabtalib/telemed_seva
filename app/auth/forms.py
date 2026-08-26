"""Authentication forms."""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError

from ..models.user import User, UserRole
from ..utils.validators import StrongPassword


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Log In')


class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=255)])
    first_name = StringField('First Name', validators=[DataRequired(), Length(min=2, max=100)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(min=1, max=100)])
    phone = StringField('Phone Number', validators=[Length(max=20)])
    role = SelectField('I am a', choices=[
        (UserRole.PATIENT.value, 'Patient'),
        (UserRole.DOCTOR.value, 'Doctor'),
    ], validators=[DataRequired()])
    password = PasswordField('Password', validators=[
        DataRequired(), Length(min=8), StrongPassword()
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(), EqualTo('password', message='Passwords must match.')
    ])
    agree_terms = BooleanField('I agree to the Terms & Conditions and Privacy Policy',
                               validators=[DataRequired(message='You must agree to the terms.')])
    submit = SubmitField('Create Account')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.lower().strip()).first():
            raise ValidationError('This email is already registered.')


class ForgotPasswordForm(FlaskForm):
    """Request a password-reset link by email."""
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Send Reset Link')


class ResetPasswordForm(FlaskForm):
    """Set a new password using the reset token."""
    password = PasswordField('New Password', validators=[
        DataRequired(), Length(min=8), StrongPassword()
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(), EqualTo('password', message='Passwords must match.')
    ])
    submit = SubmitField('Reset Password')
