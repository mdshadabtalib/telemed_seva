#!/usr/bin/env python
"""Add professional medicine images to all medicines in the database"""

from app import create_app
from app.extensions import db
from app.models.pharmacy import Medicine, DosageForm

app = create_app()

# Medicine-themed image mappings using Unsplash for professional pharma images
# Using specific keywords for each dosage form for relevant images
IMAGE_THEMES = {
    DosageForm.TABLET: 'pills-tablets-medication',
    DosageForm.CAPSULE: 'capsules-medicine',
    DosageForm.SYRUP: 'syrup-bottle-medicine',
    DosageForm.INJECTION: 'syringe-injection-medical',
    DosageForm.CREAM: 'cream-tube-skincare',
    DosageForm.OINTMENT: 'ointment-medical-tube',
    DosageForm.DROPS: 'eye-drops-bottle',
    DosageForm.INHALER: 'inhaler-asthma',
    DosageForm.POWDER: 'powder-medicine',
    DosageForm.GEL: 'gel-tube-medical',
    DosageForm.SPRAY: 'spray-bottle-medicine',
    DosageForm.PATCH: 'medical-patch',
    DosageForm.SUPPOSITORY: 'medicine-pharmaceutical',
    DosageForm.OTHER: 'pharmacy-medicine',
}

# Color schemes for different dosage forms (for fallback gradient backgrounds)
COLOR_SCHEMES = {
    DosageForm.TABLET: '#4F46E5',      # Indigo
    DosageForm.CAPSULE: '#0891B2',     # Cyan
    DosageForm.SYRUP: '#DC2626',       # Red
    DosageForm.INJECTION: '#7C3AED',   # Purple
    DosageForm.CREAM: '#F59E0B',       # Amber
    DosageForm.OINTMENT: '#10B981',    # Green
    DosageForm.DROPS: '#3B82F6',       # Blue
    DosageForm.INHALER: '#06B6D4',     # Cyan
    DosageForm.POWDER: '#8B5CF6',      # Violet
    DosageForm.GEL: '#14B8A6',         # Teal
    DosageForm.SPRAY: '#6366F1',       # Indigo
    DosageForm.PATCH: '#EC4899',       # Pink
    DosageForm.SUPPOSITORY: '#F97316', # Orange
    DosageForm.OTHER: '#6B7280',       # Gray
}

def generate_medicine_image_url(medicine):
    """Generate appropriate image URL for a medicine"""
    # Use Unsplash Source API for high-quality pharma/medical images
    # Format: https://source.unsplash.com/400x300/?medicine,pills,pharmacy
    
    if medicine.dosage_form and medicine.dosage_form in IMAGE_THEMES:
        theme = IMAGE_THEMES[medicine.dosage_form]
    else:
        theme = 'medicine-pharmacy-pills'
    
    # Use the medicine ID as seed for consistent images
    # Unsplash random with sig parameter ensures same image for same medicine
    return f'https://source.unsplash.com/400x300/?{theme}&sig={medicine.id}'

def generate_fallback_svg(medicine):
    """Generate inline SVG fallback with medicine icon and gradient"""
    if medicine.dosage_form and medicine.dosage_form in COLOR_SCHEMES:
        color = COLOR_SCHEMES[medicine.dosage_form]
    else:
        color = '#6366F1'
    
    # Create data URI for inline SVG
    svg = f'''data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='400' height='300'%3E%3Cdefs%3E%3ClinearGradient id='g' x1='0%25' y1='0%25' x2='100%25' y2='100%25'%3E%3Cstop offset='0%25' style='stop-color:{color};stop-opacity:0.2'/%3E%3Cstop offset='100%25' style='stop-color:{color};stop-opacity:0.05'/%3E%3C/linearGradient%3E%3C/defs%3E%3Crect fill='url(%23g)' width='400' height='300'/%3E%3Ctext x='50%25' y='50%25' text-anchor='middle' dy='.3em' style='fill:{color};font-size:48px;font-family:Arial'%3E💊%3C/text%3E%3C/svg%3E'''
    return svg

with app.app_context():
    print("=" * 80)
    print("ADDING MEDICINE IMAGES")
    print("=" * 80)
    
    medicines = Medicine.query.all()
    updated = 0
    
    for med in medicines:
        if not med.image_url:
            # Add Unsplash image URL
            med.image_url = generate_medicine_image_url(med)
            updated += 1
            print(f"✓ {med.name[:50]:50} → {med.dosage_form.value if med.dosage_form else 'general'}")
    
    db.session.commit()
    
    print("=" * 80)
    print(f"✅ Added images to {updated} medicines")
    print(f"   Total medicines with images: {Medicine.query.filter(Medicine.image_url.isnot(None)).count()}")
    print("=" * 80)
    print("\nImage Source: Unsplash (Free high-quality medical/pharmacy images)")
    print("Fallback: Gradient backgrounds with medicine icons")
