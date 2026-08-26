"""Authentication & authorization unit tests."""
import pytest
from app.models.user import User, UserRole
from app.extensions import db


def test_password_hashing(app):
    """Test password hashing and verification."""
    with app.app_context():
        u = User(email='test@example.com', role=UserRole.PATIENT)
        u.set_password('SecurePass123!')
        assert u.check_password('SecurePass123!') is True
        assert u.check_password('WrongPass') is False
        assert u.password_hash != 'SecurePass123!'


def test_user_registration(client, app):
    """Test user registration flow for patient."""
    response = client.post('/register', data={
        'role': 'patient',
        'first_name': 'Alice',
        'last_name': 'Wonder',
        'email': 'alice@example.com',
        'phone': '9999888877',
        'password': 'Password123!',
        'confirm_password': 'Password123!',
        'agree_terms': 'y',
    }, follow_redirects=True)

    assert response.status_code == 200
    with app.app_context():
        user = User.query.filter_by(email='alice@example.com').first()
        assert user is not None
        assert user.role == UserRole.PATIENT
        assert user.patient_profile.first_name == 'Alice'


def test_user_login_and_logout(client, patient_user):
    """Test login and logout flow."""
    # Login
    res = client.post('/login', data={
        'email': 'patient@example.com',
        'password': 'Password123!',
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b'patient@example.com' in res.data or b'Jane' in res.data or b'Dashboard' in res.data

    # Logout
    res = client.get('/logout', follow_redirects=True)
    assert res.status_code == 200
    assert b'logged out' in res.data.lower() or b'log in' in res.data.lower()


def test_login_invalid_password(client, patient_user):
    """Test login failure with wrong password."""
    res = client.post('/login', data={
        'email': 'patient@example.com',
        'password': 'WrongPassword!',
    }, follow_redirects=True)
    assert b'Invalid email or password' in res.data


def test_rbac_patient_cannot_access_admin(client, patient_user):
    """Patients must be forbidden from accessing admin endpoints."""
    # Login as patient
    client.post('/login', data={'email': 'patient@example.com', 'password': 'Password123!'})
    res = client.get('/admin/', follow_redirects=True)
    # Should get 403 or redirect
    assert res.status_code in (403, 302)
