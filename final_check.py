from app import create_app
from app.models import *

app = create_app()

with app.test_client() as c:
    pages = [
        ('/', 'Home Page'),
        ('/login', 'Login'),
        ('/register', 'Register (Admin option)'),
        ('/pharmacy/', 'Pharmacy (101 medicines + images)'),
        ('/api/specialties', 'Specialties API (42)'),
        ('/api/doctors', 'Doctors API'),
    ]
    print('PAGE LOAD RESULTS')
    print('-'*60)
    ok_count = 0
    for path, name in pages:
        r = c.get(path)
        ok = r.status_code in (200, 302)
        if ok:
            ok_count += 1
        status = 'OK  ' if ok else 'FAIL'
        print(f'[{r.status_code}] {status} - {name}')
    print('-'*60)
    print(f'{ok_count}/{len(pages)} pages OK')

with app.app_context():
    print()
    print('DATABASE SUMMARY')
    print('-'*60)
    active_specs = Specialty.query.filter_by(is_active=True).count()
    total_specs = Specialty.query.count()
    meds_with_img = Medicine.query.filter(Medicine.image_url.isnot(None)).count()
    print(f'Specialties  : {total_specs} total  ({active_specs} active)')
    print(f'Medicines    : {Medicine.query.count()} total  ({meds_with_img} with images)')
    print(f'Categories   : {MedicineCategory.query.count()}')
    print(f'Users        : {User.query.count()}')
    print()
    print('UPGRADED TEMPLATES')
    print('-'*60)
    import os
    templates = {
        'Patient Dashboard'  : 'app/templates/patient/dashboard.html',
        'Doctor Dashboard'   : 'app/templates/doctor/dashboard.html',
        'Doctor Profile'     : 'app/templates/doctor/profile.html',
        'Admin Dashboard'    : 'app/templates/admin/dashboard.html',
        'Pharmacy Catalog'   : 'app/templates/pharmacy/catalog.html',
    }
    for label, path in templates.items():
        exists = os.path.exists(path)
        size = os.path.getsize(path) if exists else 0
        print(f'{"OK  " if exists else "MISS"} {label:22} ({size:,} bytes)')
    print()
    print('ALL CHECKS COMPLETE - Server at http://127.0.0.1:5000')
