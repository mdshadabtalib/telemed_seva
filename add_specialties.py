#!/usr/bin/env python
"""Add comprehensive medical specialties to the database"""

from app import create_app
from app.extensions import db
from app.models.doctor import Specialty

app = create_app()

# Comprehensive list of medical specialties with icons
SPECIALTIES = [
    # Primary Care
    {"name": "General Medicine", "description": "General health checkups, diagnosis and treatment of common conditions", "icon": "stethoscope"},
    {"name": "Family Medicine", "description": "Comprehensive healthcare for all ages and genders", "icon": "users"},
    {"name": "Internal Medicine", "description": "Adult medicine, diagnosis and non-surgical treatment", "icon": "activity"},
    
    # Surgical Specialties
    {"name": "General Surgery", "description": "Surgical procedures for various conditions", "icon": "scissors"},
    {"name": "Orthopedics", "description": "Bone, joint, muscle and ligament treatments", "icon": "bone"},
    {"name": "Neurosurgery", "description": "Brain and nervous system surgery", "icon": "brain"},
    {"name": "Cardiothoracic Surgery", "description": "Heart and chest surgery", "icon": "heart-pulse"},
    {"name": "Plastic Surgery", "description": "Reconstructive and cosmetic surgery", "icon": "sparkles"},
    
    # Medical Specialties
    {"name": "Cardiology", "description": "Heart and cardiovascular system care", "icon": "heart"},
    {"name": "Neurology", "description": "Brain and nervous system disorders", "icon": "brain"},
    {"name": "Dermatology", "description": "Skin, hair and nail conditions", "icon": "droplet"},
    {"name": "Gastroenterology", "description": "Digestive system and liver care", "icon": "pill"},
    {"name": "Pulmonology", "description": "Respiratory system and lung care", "icon": "wind"},
    {"name": "Nephrology", "description": "Kidney diseases and dialysis", "icon": "droplets"},
    {"name": "Endocrinology", "description": "Hormone disorders, diabetes and thyroid", "icon": "activity"},
    {"name": "Rheumatology", "description": "Arthritis and autoimmune diseases", "icon": "zap"},
    {"name": "Hematology", "description": "Blood disorders and diseases", "icon": "droplet"},
    {"name": "Oncology", "description": "Cancer diagnosis and treatment", "icon": "shield"},
    {"name": "Infectious Diseases", "description": "Infections and communicable diseases", "icon": "alert-circle"},
    
    # Women's Health
    {"name": "Obstetrics & Gynecology", "description": "Women's reproductive health and pregnancy", "icon": "baby"},
    {"name": "Fertility & IVF", "description": "Fertility treatments and assisted reproduction", "icon": "heart-handshake"},
    
    # Children's Health
    {"name": "Pediatrics", "description": "Child health and development", "icon": "baby"},
    {"name": "Neonatology", "description": "Newborn and premature infant care", "icon": "baby"},
    
    # Mental Health
    {"name": "Psychiatry", "description": "Mental health and behavioral disorders", "icon": "brain"},
    {"name": "Psychology", "description": "Counseling and psychotherapy", "icon": "heart"},
    
    # Eye & ENT
    {"name": "Ophthalmology", "description": "Eye care and vision problems", "icon": "eye"},
    {"name": "ENT (Otolaryngology)", "description": "Ear, nose and throat conditions", "icon": "ear"},
    
    # Dental
    {"name": "Dentistry", "description": "Dental care and oral health", "icon": "smile"},
    {"name": "Orthodontics", "description": "Teeth alignment and braces", "icon": "align-center"},
    
    # Other Specialties
    {"name": "Urology", "description": "Urinary system and male reproductive health", "icon": "droplet"},
    {"name": "Anesthesiology", "description": "Anesthesia and pain management", "icon": "syringe"},
    {"name": "Radiology", "description": "Medical imaging and diagnostics", "icon": "scan"},
    {"name": "Pathology", "description": "Laboratory diagnosis and disease analysis", "icon": "microscope"},
    {"name": "Physical Medicine", "description": "Rehabilitation and physical therapy", "icon": "dumbbell"},
    {"name": "Sports Medicine", "description": "Sports injuries and athlete care", "icon": "trophy"},
    {"name": "Emergency Medicine", "description": "Critical care and emergency treatment", "icon": "ambulance"},
    {"name": "Geriatrics", "description": "Elderly care and age-related conditions", "icon": "accessibility"},
    {"name": "Nutrition & Dietetics", "description": "Diet planning and nutritional counseling", "icon": "apple"},
    {"name": "Ayurveda", "description": "Traditional Indian medicine and wellness", "icon": "leaf"},
    {"name": "Homeopathy", "description": "Homeopathic treatment and natural remedies", "icon": "flower"},
]

def generate_slug(name):
    """Generate URL-friendly slug from specialty name"""
    import re
    slug = name.lower()
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    slug = slug.strip('-')
    return slug

with app.app_context():
    print("Adding comprehensive medical specialties...")
    print("=" * 80)
    
    added = 0
    updated = 0
    
    for spec_data in SPECIALTIES:
        slug = generate_slug(spec_data["name"])
        existing = Specialty.query.filter_by(name=spec_data["name"]).first()
        
        if existing:
            # Update existing specialty
            existing.description = spec_data["description"]
            existing.icon = spec_data["icon"]
            existing.is_active = True
            if not existing.slug:
                existing.slug = slug
            updated += 1
            print(f"✓ Updated: {spec_data['name']}")
        else:
            # Add new specialty
            new_spec = Specialty(
                name=spec_data["name"],
                slug=slug,
                description=spec_data["description"],
                icon=spec_data["icon"],
                is_active=True
            )
            db.session.add(new_spec)
            added += 1
            print(f"+ Added: {spec_data['name']}")
    
    db.session.commit()
    
    total = Specialty.query.count()
    active = Specialty.query.filter_by(is_active=True).count()
    
    print("=" * 80)
    print(f"✅ Complete!")
    print(f"   Added: {added} new specialties")
    print(f"   Updated: {updated} existing specialties")
    print(f"   Total: {total} specialties in database")
    print(f"   Active: {active} specialties available")
