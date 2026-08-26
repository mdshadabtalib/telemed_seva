"""Pytest fixtures for TeleMed Seva."""
import pytest
from app import create_app
from app.extensions import db
from app.models.user import User, UserRole, PatientProfile, DoctorProfile
from app.models.doctor import Specialty, Availability, DayOfWeek
from app.models.pharmacy import Medicine, MedicineCategory, Inventory, DosageForm
from datetime import time, date


@pytest.fixture
def app():
    """Create and configure a clean testing app instance."""
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        # Seed basic lookup data
        spec = Specialty(name='General Physician', slug='general-physician')
        cat = MedicineCategory(name='Pain Relief', slug='pain-relief')
        db.session.add_all([spec, cat])
        db.session.commit()

        yield app

        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Test client."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """CLI test runner."""
    return app.test_cli_runner()


@pytest.fixture
def patient_user(app):
    """Create a test patient."""
    with app.app_context():
        user = User(email='patient@example.com', role=UserRole.PATIENT, is_active=True)
        user.set_password('Password123!')
        db.session.add(user)
        db.session.flush()

        profile = PatientProfile(
            user_id=user.id,
            first_name='Jane',
            last_name='Doe',
            phone='9876543210',
        )
        db.session.add(profile)
        db.session.commit()
        return user.id


@pytest.fixture
def doctor_user(app):
    """Create a verified test doctor with availability."""
    with app.app_context():
        user = User(email='doctor@example.com', role=UserRole.DOCTOR, is_active=True)
        user.set_password('Password123!')
        db.session.add(user)
        db.session.flush()

        spec = Specialty.query.first()
        profile = DoctorProfile(
            user_id=user.id,
            first_name='John',
            last_name='Smith',
            phone='9876543211',
            specialty_id=spec.id if spec else None,
            registration_number='MCI-12345',
            experience_years=10,
            consultation_fee=500.0,
            consultation_duration=30,
            is_verified=True,
            is_available=True,
        )
        db.session.add(profile)
        db.session.flush()

        # Add availability for all days 9:00 - 17:00
        for day in DayOfWeek:
            avail = Availability(
                doctor_id=profile.id,
                day_of_week=day,
                start_time=time(9, 0),
                end_time=time(17, 0),
                slot_duration=30,
            )
            db.session.add(avail)

        db.session.commit()
        return user.id


@pytest.fixture
def admin_user(app):
    """Create a test admin user."""
    with app.app_context():
        user = User(email='admin@example.com', role=UserRole.ADMIN, is_active=True)
        user.set_password('AdminPass123!')
        db.session.add(user)
        db.session.commit()
        return user.id


@pytest.fixture
def sample_medicine(app):
    """Create a test medicine."""
    with app.app_context():
        cat = MedicineCategory.query.first()
        med = Medicine(
            name='Paracetamol 500mg',
            generic_name='Acetaminophen',
            category_id=cat.id if cat else None,
            dosage_form=DosageForm.TABLET,
            strength='500mg',
            pack_size='10 Tablets',
            price=30.0,
            discount_percent=10.0,
            requires_prescription=False,
            is_active=True,
        )
        db.session.add(med)
        db.session.flush()

        inv = Inventory(
            medicine_id=med.id,
            stock_quantity=100,
            reorder_level=10,
        )
        db.session.add(inv)
        db.session.commit()
        return med.id
