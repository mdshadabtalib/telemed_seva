"""Database seeding utilities — specialties, categories, admin user."""
import click
from flask import current_app

from ..extensions import db
from ..models.user import User, UserRole, PatientProfile
from ..models.doctor import Specialty
from ..models.pharmacy import MedicineCategory
from ..utils.helpers import slugify


SPECIALTIES = [
    ('General Medicine', 'fa-stethoscope'),
    ('Cardiology', 'fa-heartbeat'),
    ('Dermatology', 'fa-hand-holding-medical'),
    ('Orthopedics', 'fa-bone'),
    ('Pediatrics', 'fa-baby'),
    ('Gynecology', 'fa-female'),
    ('Neurology', 'fa-brain'),
    ('Psychiatry', 'fa-head-side-virus'),
    ('ENT', 'fa-ear-listen'),
    ('Ophthalmology', 'fa-eye'),
    ('Dentistry', 'fa-tooth'),
    ('Endocrinology', 'fa-vial'),
    ('Gastroenterology', 'fa-stomach'),
    ('Pulmonology', 'fa-lungs'),
    ('Urology', 'fa-kidneys'),
    ('Oncology', 'fa-ribbon'),
]

MEDICINE_CATEGORIES = [
    ('Pain Relief', 'fa-pills'),
    ('Antibiotics', 'fa-capsules'),
    ('Antifungal', 'fa-disease'),
    ('Vitamins & Supplements', 'fa-apple-whole'),
    ('Diabetes Care', 'fa-syringe'),
    ('Heart & Blood Pressure', 'fa-heart-pulse'),
    ('Digestive Health', 'fa-stomach'),
    ('Respiratory Care', 'fa-lungs'),
    ('Skin Care', 'fa-hand-sparkles'),
    ('Eye & Ear Care', 'fa-eye'),
    ('Women\'s Health', 'fa-venus'),
    ('Baby & Mother Care', 'fa-baby-carriage'),
    ('First Aid', 'fa-kit-medical'),
    ('Personal Care', 'fa-pump-soap'),
]


def seed_database():
    """Seed specialties and medicine categories."""
    # Specialties
    for i, (name, icon) in enumerate(SPECIALTIES):
        existing = Specialty.query.filter_by(slug=slugify(name)).first()
        if not existing:
            db.session.add(Specialty(
                name=name, slug=slugify(name), icon=icon, display_order=i
            ))

    # Medicine categories
    for name, icon in MEDICINE_CATEGORIES:
        existing = MedicineCategory.query.filter_by(slug=slugify(name)).first()
        if not existing:
            db.session.add(MedicineCategory(
                name=name, slug=slugify(name), icon=icon
            ))

    db.session.commit()
    click.echo('✅ Database seeded with specialties and medicine categories.')


def create_admin_user():
    """Create a superadmin user interactively."""
    email = click.prompt('Admin email')
    existing = User.query.filter_by(email=email).first()
    if existing:
        click.echo(f'User {email} already exists.')
        return

    password = click.prompt('Password', hide_input=True, confirmation_prompt=True)

    admin = User(email=email, role=UserRole.ADMIN, is_active=True, email_verified=True)
    admin.set_password(password)
    db.session.add(admin)
    db.session.commit()
    click.echo(f'✅ Admin user {email} created.')
