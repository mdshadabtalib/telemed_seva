"""Comprehensive medicine database seeding for all disease categories."""
from ..extensions import db
from ..models.pharmacy import Medicine, MedicineCategory, Inventory, DosageForm


MEDICINES_BY_CATEGORY = {
    'Pain Relief': [
        ('Paracetamol 500mg', 'Acetaminophen', 'TABLET', '500mg', '10 Tablets', 30.0, 10, 'Various', False, 100),
        ('Paracetamol 650mg', 'Acetaminophen', 'TABLET', '650mg', '15 Tablets', 45.0, 10, 'Various', False, 150),
        ('Ibuprofen 400mg', 'Ibuprofen', 'TABLET', '400mg', '10 Tablets', 50.0, 15, 'Cipla', False, 120),
        ('Diclofenac 50mg', 'Diclofenac Sodium', 'TABLET', '50mg', '10 Tablets', 35.0, 10, 'Sun Pharma', True, 80),
        ('Aspirin 75mg', 'Acetylsalicylic Acid', 'TABLET', '75mg', '14 Tablets', 25.0, 5, 'Bayer', False, 200),
        ('Tramadol 50mg', 'Tramadol HCl', 'CAPSULE', '50mg', '10 Capsules', 120.0, 20, 'Dr Reddy', True, 50),
        ('Combiflam', 'Ibuprofen + Paracetamol', 'TABLET', '400mg+325mg', '20 Tablets', 60.0, 12, 'Sanofi', False, 180),
        ('Voveran 50mg', 'Diclofenac', 'TABLET', '50mg', '10 Tablets', 38.0, 10, 'Novartis', True, 90),
        ('Brufen 600mg', 'Ibuprofen', 'TABLET', '600mg', '10 Tablets', 75.0, 15, 'Abbott', False, 100),
        ('Flexon', 'Ibuprofen + Paracetamol', 'TABLET', '400mg+325mg', '15 Tablets', 55.0, 10, 'Aristo', False, 150),
    ],
    'Antibiotics': [
        ('Azithromycin 500mg', 'Azithromycin', 'TABLET', '500mg', '3 Tablets', 85.0, 10, 'Cipla', True, 60),
        ('Amoxicillin 500mg', 'Amoxicillin', 'CAPSULE', '500mg', '10 Capsules', 95.0, 15, 'GSK', True, 80),
        ('Ciprofloxacin 500mg', 'Ciprofloxacin', 'TABLET', '500mg', '10 Tablets', 65.0, 12, 'Ranbaxy', True, 70),
        ('Augmentin 625mg', 'Amoxicillin + Clavulanic Acid', 'TABLET', '625mg', '6 Tablets', 145.0, 18, 'GSK', True, 50),
        ('Cefixime 200mg', 'Cefixime', 'TABLET', '200mg', '10 Tablets', 180.0, 20, 'Lupin', True, 45),
        ('Doxycycline 100mg', 'Doxycycline', 'CAPSULE', '100mg', '10 Capsules', 55.0, 10, 'Alkem', True, 90),
        ('Levofloxacin 500mg', 'Levofloxacin', 'TABLET', '500mg', '5 Tablets', 95.0, 15, 'Dr Reddy', True, 60),
        ('Metronidazole 400mg', 'Metronidazole', 'TABLET', '400mg', '10 Tablets', 25.0, 8, 'Cipla', True, 120),
        ('Cephalexin 500mg', 'Cefalexin', 'CAPSULE', '500mg', '10 Capsules', 75.0, 12, 'Torrent', True, 70),
        ('Clarithromycin 500mg', 'Clarithromycin', 'TABLET', '500mg', '6 Tablets', 145.0, 18, 'Abbott', True, 40),
    ],
    'Antifungal': [
        ('Fluconazole 150mg', 'Fluconazole', 'CAPSULE', '150mg', '1 Capsule', 35.0, 10, 'Cipla', True, 100),
        ('Clotrimazole Cream', 'Clotrimazole', 'CREAM', '1%', '15g Tube', 45.0, 12, 'Candid', False, 150),
        ('Terbinafine 250mg', 'Terbinafine', 'TABLET', '250mg', '14 Tablets', 285.0, 20, 'Novartis', True, 50),
        ('Itraconazole 100mg', 'Itraconazole', 'CAPSULE', '100mg', '10 Capsules', 195.0, 22, 'Janssen', True, 40),
        ('Ketoconazole Shampoo', 'Ketoconazole', 'SHAMPOO', '2%', '110ml Bottle', 350.0, 15, 'Johnson', False, 80),
        ('Miconazole Cream', 'Miconazole', 'CREAM', '2%', '15g Tube', 55.0, 10, 'Cipla', False, 120),
    ],
    'Vitamins & Supplements': [
        ('Vitamin D3 60000 IU', 'Cholecalciferol', 'CAPSULE', '60000 IU', '4 Capsules', 85.0, 15, 'Sun Pharma', False, 200),
        ('Vitamin B12 1500mcg', 'Methylcobalamin', 'TABLET', '1500mcg', '30 Tablets', 125.0, 18, 'Mankind', False, 180),
        ('Vitamin C 500mg', 'Ascorbic Acid', 'TABLET', '500mg', '30 Tablets', 95.0, 12, 'HealthVit', False, 250),
        ('Multivitamin Tablets', 'Multivitamin + Minerals', 'TABLET', '—', '30 Tablets', 285.0, 20, 'HealthKart', False, 300),
        ('Calcium + Vitamin D3', 'Calcium Carbonate + Vit D3', 'TABLET', '500mg+250IU', '30 Tablets', 145.0, 18, 'Shelcal', False, 200),
        ('Omega-3 Capsules', 'Omega-3 Fatty Acids', 'CAPSULE', '1000mg', '30 Capsules', 395.0, 22, 'Nordic', False, 150),
        ('Iron + Folic Acid', 'Ferrous Sulfate + Folic Acid', 'TABLET', '100mg+0.5mg', '30 Tablets', 65.0, 10, 'Lupin', False, 180),
        ('Zinc 50mg', 'Zinc Sulfate', 'TABLET', '50mg', '30 Tablets', 95.0, 15, 'Mankind', False, 160),
        ('Biotin 10000mcg', 'Biotin', 'TABLET', '10000mcg', '30 Tablets', 485.0, 25, 'HealthVit', False, 120),
        ('Vitamin E 400 IU', 'Tocopherol', 'CAPSULE', '400 IU', '30 Capsules', 165.0, 18, 'Evion', False, 140),
    ],
    'Diabetes Care': [
        ('Metformin 500mg', 'Metformin HCl', 'TABLET', '500mg', '15 Tablets', 18.0, 8, 'USV', True, 300),
        ('Metformin 850mg', 'Metformin HCl', 'TABLET', '850mg', '10 Tablets', 22.0, 10, 'Cipla', True, 250),
        ('Glimepiride 1mg', 'Glimepiride', 'TABLET', '1mg', '10 Tablets', 35.0, 12, 'Sanofi', True, 200),
        ('Glimepiride 2mg', 'Glimepiride', 'TABLET', '2mg', '10 Tablets', 48.0, 15, 'Sanofi', True, 180),
        ('Sitagliptin 50mg', 'Sitagliptin', 'TABLET', '50mg', '10 Tablets', 485.0, 30, 'MSD', True, 100),
        ('Insulin Glargine', 'Insulin Glargine', 'INJECTION', '100 units/ml', '3ml Cartridge', 1250.0, 40, 'Lantus', True, 50),
        ('Glucometer Strips', 'Blood Glucose Test Strips', 'STRIPS', '—', '25 Strips', 425.0, 20, 'Accu-Chek', False, 200),
        ('Voglibose 0.3mg', 'Voglibose', 'TABLET', '0.3mg', '15 Tablets', 95.0, 18, 'Ranbaxy', True, 150),
    ],
    'Heart & Blood Pressure': [
        ('Amlodipine 5mg', 'Amlodipine', 'TABLET', '5mg', '10 Tablets', 22.0, 10, 'Pfizer', True, 200),
        ('Atenolol 50mg', 'Atenolol', 'TABLET', '50mg', '14 Tablets', 18.0, 8, 'AstraZeneca', True, 180),
        ('Losartan 50mg', 'Losartan Potassium', 'TABLET', '50mg', '10 Tablets', 75.0, 15, 'MSD', True, 160),
        ('Telmisartan 40mg', 'Telmisartan', 'TABLET', '40mg', '15 Tablets', 95.0, 18, 'Glenmark', True, 140),
        ('Atorvastatin 10mg', 'Atorvastatin', 'TABLET', '10mg', '10 Tablets', 48.0, 12, 'Pfizer', True, 200),
        ('Rosuvastatin 10mg', 'Rosuvastatin', 'TABLET', '10mg', '10 Tablets', 125.0, 20, 'AstraZeneca', True, 150),
        ('Clopidogrel 75mg', 'Clopidogrel', 'TABLET', '75mg', '10 Tablets', 35.0, 12, 'Sun Pharma', True, 180),
        ('Ramipril 5mg', 'Ramipril', 'TABLET', '5mg', '10 Tablets', 38.0, 10, 'Aventis', True, 160),
        ('Aspirin 75mg (Cardio)', 'Acetylsalicylic Acid', 'TABLET', '75mg', '30 Tablets', 55.0, 15, 'Bayer', True, 220),
    ],
    'Digestive Health': [
        ('Omeprazole 20mg', 'Omeprazole', 'CAPSULE', '20mg', '15 Capsules', 38.0, 10, 'Dr Reddy', False, 200),
        ('Pantoprazole 40mg', 'Pantoprazole', 'TABLET', '40mg', '15 Tablets', 65.0, 15, 'Sun Pharma', True, 180),
        ('Ranitidine 150mg', 'Ranitidine', 'TABLET', '150mg', '10 Tablets', 22.0, 8, 'GSK', False, 150),
        ('Domperidone 10mg', 'Domperidone', 'TABLET', '10mg', '10 Tablets', 18.0, 5, 'Cipla', False, 200),
        ('Ondansetron 4mg', 'Ondansetron', 'TABLET', '4mg', '10 Tablets', 35.0, 12, 'GSK', True, 120),
        ('Loperamide 2mg', 'Loperamide HCl', 'CAPSULE', '2mg', '10 Capsules', 28.0, 8, 'Johnson', False, 140),
        ('Lactulose Syrup', 'Lactulose', 'SYRUP', '10g/15ml', '200ml Bottle', 145.0, 18, 'Abbott', False, 100),
        ('Ispaghula Husk', 'Psyllium Husk', 'POWDER', '—', '100g Pack', 95.0, 15, 'Dabur', False, 180),
    ],
    'Respiratory Care': [
        ('Montelukast 10mg', 'Montelukast', 'TABLET', '10mg', '10 Tablets', 85.0, 15, 'MSD', True, 150),
        ('Cetirizine 10mg', 'Cetirizine', 'TABLET', '10mg', '10 Tablets', 22.0, 5, 'Cipla', False, 250),
        ('Salbutamol Inhaler', 'Salbutamol', 'INHALER', '100mcg', '200 doses', 145.0, 18, 'Cipla', True, 100),
        ('Budesonide Inhaler', 'Budesonide', 'INHALER', '200mcg', '200 doses', 485.0, 30, 'AstraZeneca', True, 80),
        ('Ambroxol 30mg', 'Ambroxol HCl', 'TABLET', '30mg', '10 Tablets', 28.0, 8, 'Cipla', False, 180),
        ('Bromhexine 8mg', 'Bromhexine HCl', 'TABLET', '8mg', '10 Tablets', 32.0, 10, 'Lupin', False, 160),
        ('Cough Syrup (Honey)', 'Honey + Tulsi', 'SYRUP', '—', '100ml Bottle', 95.0, 12, 'Dabur', False, 200),
    ],
    'Skin Care': [
        ('Betnovate Cream', 'Betamethasone', 'CREAM', '0.1%', '20g Tube', 75.0, 15, 'GSK', True, 120),
        ('Tretinoin Cream 0.025%', 'Tretinoin', 'CREAM', '0.025%', '20g Tube', 95.0, 18, 'Johnson', True, 80),
        ('Hydrocortisone Cream', 'Hydrocortisone', 'CREAM', '1%', '15g Tube', 45.0, 10, 'Cipla', False, 150),
        ('Calamine Lotion', 'Calamine', 'LOTION', '—', '100ml Bottle', 55.0, 8, 'Lacto', False, 200),
        ('Mupirocin Ointment', 'Mupirocin', 'OINTMENT', '2%', '5g Tube', 85.0, 15, 'GSK', True, 90),
        ('Adapalene Gel 0.1%', 'Adapalene', 'GEL', '0.1%', '15g Tube', 325.0, 25, 'Galderma', True, 70),
        ('Benzoyl Peroxide Gel', 'Benzoyl Peroxide', 'GEL', '2.5%', '20g Tube', 165.0, 18, 'Galderma', False, 100),
    ],
    'Eye & Ear Care': [
        ('Moxifloxacin Eye Drops', 'Moxifloxacin', 'EYE_DROPS', '0.5%', '5ml Bottle', 125.0, 20, 'Alcon', True, 100),
        ('Tobramycin Eye Drops', 'Tobramycin', 'EYE_DROPS', '0.3%', '5ml Bottle', 95.0, 15, 'Sun Pharma', True, 120),
        ('Refresh Tears', 'Carboxymethylcellulose', 'EYE_DROPS', '0.5%', '10ml Bottle', 145.0, 18, 'Allergan', False, 180),
        ('Ciprofloxacin Ear Drops', 'Ciprofloxacin', 'EAR_DROPS', '0.3%', '5ml Bottle', 38.0, 10, 'Cipla', True, 140),
        ('Wax Softener Drops', 'Docusate Sodium', 'EAR_DROPS', '—', '10ml Bottle', 85.0, 12, 'Mankind', False, 100),
    ],
    "Women's Health": [
        ('Folic Acid 5mg', 'Folic Acid', 'TABLET', '5mg', '30 Tablets', 28.0, 5, 'USV', False, 300),
        ('Mefenamic Acid 500mg', 'Mefenamic Acid', 'TABLET', '500mg', '10 Tablets', 45.0, 12, 'Blue Cross', True, 150),
        ('Tranexamic Acid 500mg', 'Tranexamic Acid', 'TABLET', '500mg', '10 Tablets', 85.0, 18, 'Cipla', True, 100),
        ('Iron + Calcium', 'Ferrous Fumarate + Calcium', 'TABLET', '100mg+500mg', '30 Tablets', 125.0, 20, 'Abbott', False, 180),
        ('Clotrimazole Vaginal Cream', 'Clotrimazole', 'CREAM', '2%', '30g Tube', 95.0, 15, 'Bayer', True, 80),
    ],
    'Baby & Mother Care': [
        ('Gripe Water', 'Dill Oil + Sarjikakshara', 'SYRUP', '—', '120ml Bottle', 75.0, 10, 'Woodward', False, 200),
        ('Multivitamin Drops (Baby)', 'Multivitamin', 'DROPS', '—', '30ml Bottle', 145.0, 18, 'Zincovit', False, 150),
        ('Paracetamol Drops (Baby)', 'Paracetamol', 'DROPS', '100mg/ml', '15ml Bottle', 55.0, 8, 'Calpol', False, 180),
        ('Calcium + Vitamin D (Baby)', 'Calcium + Vitamin D3', 'SYRUP', '—', '200ml Bottle', 125.0, 15, 'Ostocalcium', False, 120),
        ('Zinc Drops', 'Zinc Sulfate', 'DROPS', '20mg/ml', '30ml Bottle', 95.0, 12, 'Zinconia', False, 140),
    ],
    'First Aid': [
        ('Bandage Roll', 'Cotton Bandage', 'BANDAGE', '—', '1 Roll (4m)', 25.0, 5, 'Medicare', False, 500),
        ('Cotton Wool', 'Absorbent Cotton', 'COTTON', '—', '50g Pack', 35.0, 8, 'Johnson', False, 400),
        ('Dettol Antiseptic Liquid', 'Chloroxylenol', 'LIQUID', '4.8%', '125ml Bottle', 85.0, 10, 'Reckitt', False, 300),
        ('Betadine Solution', 'Povidone Iodine', 'SOLUTION', '10%', '100ml Bottle', 145.0, 18, 'Win Medicare', False, 200),
        ('Burnol Cream', 'Silver Sulfadiazine', 'CREAM', '1%', '20g Tube', 75.0, 12, 'Mankind', False, 180),
        ('Savlon Antiseptic Cream', 'Cetrimide + Chlorhexidine', 'CREAM', '—', '30g Tube', 55.0, 10, 'Johnson', False, 250),
        ('Band-Aid (Pack)', 'Adhesive Bandages', 'PLASTER', '—', '10 Strips', 45.0, 5, 'Johnson', False, 400),
    ],
    'Personal Care': [
        ('Hand Sanitizer', 'Isopropyl Alcohol', 'SANITIZER', '70%', '100ml Bottle', 45.0, 8, 'Lifebuoy', False, 500),
        ('Face Mask (Pack)', 'Surgical Masks', 'MASK', '—', '10 Masks', 75.0, 10, '3M', False, 300),
        ('Thermometer (Digital)', 'Digital Thermometer', 'DEVICE', '—', '1 Unit', 285.0, 20, 'Omron', False, 150),
        ('BP Monitor', 'Blood Pressure Monitor', 'DEVICE', '—', '1 Unit', 1450.0, 35, 'Omron', False, 80),
    ],
}


def seed_medicines():
    """Seed comprehensive medicine database."""
    print('Seeding medicines...')
    
    added_count = 0
    for category_name, medicines in MEDICINES_BY_CATEGORY.items():
        category = MedicineCategory.query.filter_by(name=category_name).first()
        if not category:
            print(f'  Warning: Category "{category_name}" not found, skipping...')
            continue
        
        for med_data in medicines:
            (name, generic, dosage_form_str, strength, pack_size, 
             price, discount, manufacturer, rx_required, stock_qty) = med_data
            
            # Check if already exists
            existing = Medicine.query.filter_by(name=name, generic_name=generic).first()
            if existing:
                continue
            
            # Parse dosage form
            try:
                dosage_form = DosageForm[dosage_form_str]
            except KeyError:
                dosage_form = DosageForm.TABLET
            
            medicine = Medicine(
                name=name,
                generic_name=generic,
                category_id=category.id,
                dosage_form=dosage_form,
                strength=strength,
                pack_size=pack_size,
                manufacturer=manufacturer,
                price=price,
                discount_percent=discount,
                requires_prescription=rx_required,
                is_active=True,
            )
            db.session.add(medicine)
            db.session.flush()
            
            # Add inventory
            inventory = Inventory(
                medicine_id=medicine.id,
                stock_quantity=stock_qty,
                reorder_level=20,
            )
            db.session.add(inventory)
            added_count += 1
    
    db.session.commit()
    print(f'✅ Added {added_count} medicines to database')
