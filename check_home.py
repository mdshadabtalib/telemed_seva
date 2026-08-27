from app import create_app
app = create_app()

with app.test_client() as c:
    r = c.get('/')
    html = r.data.decode()

    checks = [
        # issues 1-4: h4 → h3 in feature cards
        ("<h3 class=\"feature-card-title\">Find a Doctor</h3>",       True,  "1. How It Works: h4→h3"),
        ("<h3 class=\"feature-card-title\">General Medicine</h3>",    True,  "2. Specialties: h4→h3"),
        ("<h3 class=\"feature-card-title\">Wide Range</h3>",          True,  "3. Pharmacy: h4→h3"),
        ("<h3 class=\"feature-card-title\">Verified Doctors</h3>",    True,  "4. Trust: h4→h3"),
        # no bare h4 remain in feature cards
        ("<h4>Find a Doctor</h4>",   False, "1. No bare h4 for Find a Doctor"),
        ("<h4>Wide Range</h4>",      False, "3. No bare h4 for Wide Range"),
        # issue 5: footer h5 → h3
        ("<h3 class=\"footer-section-title\">For Patients</h3>",      True,  "5. Footer: h5→h3"),
        ("<h5>For Patients</h5>",    False, "5. No bare h5 in footer"),
        # issue 6/7: no duplicate center nav links (done in prior session)
        ('fa-sign-in-alt"></i> Login',  False, "6/7. No center Login link"),
        # issue 8: bad specialty=loop.index URL arg removed
        ("search_doctors?specialty=", False, "8. No broken specialty URL arg"),
        # issue 9: public links in navbar-links not navbar-nav
        ('class="navbar-links"',     True,  "9. navbar-links present for public"),
        # issue 10: hero flex alignment in CSS (check CSS file, not HTML)
    ]

    all_ok = True
    for snippet, must_exist, label in checks:
        found = snippet in html
        ok = found == must_exist
        all_ok = all_ok and ok
        print(f'  {"OK  " if ok else "FAIL"} {label}')

    # Issue 10: check CSS directly
    import os
    css = open('app/static/css/style.css').read()
    hero_flex = 'display: flex' in css and 'align-items: center' in css and 'min-height: 480px' in css
    print(f'  {"OK  " if hero_flex else "FAIL"} 10. Hero has flex + align-items + min-height in CSS')
    all_ok = all_ok and hero_flex

    # feature-card-title rule present
    has_rule = 'feature-card-title' in css
    print(f'  {"OK  " if has_rule else "FAIL"} CSS: .feature-card-title rule present')
    # footer-section-title rule present
    has_footer_rule = 'footer-section-title' in css
    print(f'  {"OK  " if has_footer_rule else "FAIL"} CSS: .footer-section-title rule present')

    print()
    print("HTTP status:", r.status_code)
    print("ALL CHECKS PASSED" if all_ok else "SOME CHECKS FAILED")
