from app import create_app
app = create_app()
with app.test_client() as c:
    r = c.get('/login')
    html = r.data.decode()

    results = [
        # (label, snippet, must_exist)
        ("1. <h1> present",                     "<h1",                                        True),
        ("1. Welcome Back in h1",               "<h1 ",                                       True),
        ("3. Duplicate logo removed",           'logo.svg" alt="TeleMed Seva" style="height: 50px', False),
        ("2. Center nav Login link removed",    'fa-sign-in-alt"></i> Login',                 False),
        ("2. Center nav Register link removed", 'fa-user-plus"></i> Register',                False),
        ("4. Header Log In = btn-primary",      'btn btn-primary btn-sm">Log In',             True),
        ("4. Header Sign Up = btn-outline",     'btn btn-outline btn-sm">Sign Up',            True),
    ]

    all_ok = True
    for label, snippet, must_exist in results:
        found = snippet in html
        ok = found == must_exist
        all_ok = all_ok and ok
        print(f'  {"OK  " if ok else "FAIL"} {label}')

    print()
    print("HTTP status:", r.status_code)
    print("ALL CHECKS PASSED" if all_ok else "SOME CHECKS FAILED")
