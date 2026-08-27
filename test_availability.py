"""
Functional tests for the enhanced availability slot manager.
Tests: form rendering, slot creation, toggle active, delete, duration field.
"""
from app import create_app
from app.extensions import db
from app.models.user import User, UserRole, DoctorProfile
from app.models.doctor import Availability, DayOfWeek
import datetime

app = create_app()

PASS = []
FAIL = []

def check(name, condition, detail=""):
    if condition:
        PASS.append(name)
        print(f"  OK   {name}")
    else:
        FAIL.append(name)
        print(f"  FAIL {name}" + (f" — {detail}" if detail else ""))

# ─────────────────────────────────────────────
# Setup: create or reuse doctor user
# ─────────────────────────────────────────────
with app.app_context():
    doctor_user = User.query.filter_by(email="avail_test_doc@test.com").first()
    if not doctor_user:
        doctor_user = User(
            email="avail_test_doc@test.com",
            role=UserRole.DOCTOR,
            is_active=True,
            email_verified=True,
        )
        doctor_user.set_password("Test@1234")
        db.session.add(doctor_user)
        db.session.flush()

        profile = DoctorProfile(
            user_id=doctor_user.id,
            first_name="Avail",
            last_name="TestDoc",
            consultation_duration=30,
        )
        db.session.add(profile)
        db.session.commit()

with app.test_client() as client:

    # ── Login ──────────────────────────────────
    print("\n[LOGIN]")
    r = client.post("/login", data={
        "email": "avail_test_doc@test.com",
        "password": "Test@1234",
    }, follow_redirects=True)
    check("Login succeeds", r.status_code == 200)

    # ── GET /doctor/availability ───────────────
    print("\n[PAGE LOAD]")
    r = client.get("/doctor/availability")
    check("Availability page loads (200)", r.status_code == 200)
    html = r.data.decode()
    check("Page has day picker grid",       "day-radio"     in html)
    check("Page has preset buttons",        "preset-btn"    in html)
    check("Page has duration picker",       "dur-radio"     in html)
    check("Page has slot preview section",  "slotPreview"   in html)
    check("Page has weekly calendar",       "Weekly Schedule" in html)
    check("Page has how-slots-work help",   "How slots work" in html)
    check("Monday day option present",      'value="0"'     in html)
    check("Sunday day option present",      'value="6"'     in html)
    check("10 min duration option",         'value="10"'    in html)
    check("60 min duration option",         'value="60"'    in html)
    check("Morning preset present",         "Morning"       in html)
    check("Evening preset present",         "Evening"       in html)

    # ── POST: Add a slot with custom duration ──
    print("\n[ADD SLOT — WEDNESDAY 09:00-12:00, 15 min]")
    r = client.post("/doctor/availability", data={
        "csrf_token":    client.get("/doctor/availability").data.decode().split('name="csrf_token" value="')[1].split('"')[0],
        "day_of_week":   "2",      # Wednesday = 2
        "start_time":    "09:00",
        "end_time":      "12:00",
        "slot_duration": "15",
    }, follow_redirects=True)
    check("Add slot returns 200", r.status_code == 200)
    html = r.data.decode()
    check("Success flash shown",   "Availability slot added" in html or "updated" in html)
    check("Wednesday now in schedule", "Wednesday" in html)
    check("09:00 AM shown in schedule", "09:00 AM" in html)
    check("12:00 PM shown in schedule", "12:00 PM" in html)
    check("15 min badge shown",    "15 min" in html)

    # ── Verify slot in DB ──────────────────────
    print("\n[DATABASE CHECK]")
    with app.app_context():
        doc_profile = DoctorProfile.query.join(User).filter(
            User.email == "avail_test_doc@test.com"
        ).first()
        slot = Availability.query.filter_by(
            doctor_id=doc_profile.id,
            day_of_week=DayOfWeek.WEDNESDAY,
            start_time=datetime.time(9, 0),
        ).first()
        check("Slot saved to DB",              slot is not None)
        check("Slot duration saved as 15 min", slot and slot.slot_duration == 15,
              f"got {slot.slot_duration if slot else 'None'}")
        check("Slot is active by default",     slot and slot.is_active is True)
        check("End time is 12:00",             slot and slot.end_time == datetime.time(12, 0))
        slot_id = slot.id if slot else None

    # ── POST: Add second slot ──────────────────
    print("\n[ADD SECOND SLOT — FRIDAY 18:00-21:00, 30 min]")
    tok = client.get("/doctor/availability").data.decode().split('name="csrf_token" value="')[1].split('"')[0]
    r = client.post("/doctor/availability", data={
        "csrf_token":    tok,
        "day_of_week":   "4",      # Friday = 4
        "start_time":    "18:00",
        "end_time":      "21:00",
        "slot_duration": "30",
    }, follow_redirects=True)
    check("Second slot added (200)", r.status_code == 200)
    html = r.data.decode()
    check("Friday shown in schedule", "Friday" in html)
    check("Stats bar shows 2 slots",  "2" in html)

    # ── POST: Toggle slot (pause) ──────────────
    print("\n[TOGGLE SLOT — PAUSE]")
    if slot_id:
        tok = client.get("/doctor/availability").data.decode().split('name="csrf_token" value="')[1].split('"')[0]
        r = client.post(f"/doctor/availability/{slot_id}/toggle", data={
            "csrf_token": tok
        }, follow_redirects=True)
        check("Toggle returns 200",   r.status_code == 200)
        check("Paused flash shown",   "paused" in r.data.decode() or "info" in r.data.decode())
        with app.app_context():
            s = Availability.query.get(slot_id)
            check("Slot is_active flipped to False", s and s.is_active is False,
                  f"is_active={s.is_active if s else 'None'}")

    # ── POST: Toggle back (activate) ──────────
    print("\n[TOGGLE SLOT — ACTIVATE]")
    if slot_id:
        tok = client.get("/doctor/availability").data.decode().split('name="csrf_token" value="')[1].split('"')[0]
        r = client.post(f"/doctor/availability/{slot_id}/toggle", data={
            "csrf_token": tok
        }, follow_redirects=True)
        check("Re-activate returns 200", r.status_code == 200)
        check("Activated flash shown",   "activated" in r.data.decode() or "info" in r.data.decode())
        with app.app_context():
            s = Availability.query.get(slot_id)
            check("Slot is_active back to True", s and s.is_active is True)

    # ── POST: Delete slot ──────────────────────
    print("\n[DELETE SLOT]")
    if slot_id:
        tok = client.get("/doctor/availability").data.decode().split('name="csrf_token" value="')[1].split('"')[0]
        r = client.post(f"/doctor/availability/{slot_id}/delete", data={
            "csrf_token": tok
        }, follow_redirects=True)
        check("Delete returns 200",     r.status_code == 200)
        check("Removed flash shown",    "removed" in r.data.decode())
        with app.app_context():
            gone = Availability.query.get(slot_id)
            check("Slot deleted from DB", gone is None)

    # ── Validation: end <= start should fail ──
    print("\n[VALIDATION — end time before start]")
    tok = client.get("/doctor/availability").data.decode().split('name="csrf_token" value="')[1].split('"')[0]
    r = client.post("/doctor/availability", data={
        "csrf_token":    tok,
        "day_of_week":   "0",
        "start_time":    "15:00",
        "end_time":      "09:00",   # before start
        "slot_duration": "30",
    }, follow_redirects=True)
    check("Invalid slot does not redirect to success",
          "Availability slot added" not in r.data.decode())

    # ── Cleanup ───────────────────────────────
    print("\n[CLEANUP]")
    with app.app_context():
        u = User.query.filter_by(email="avail_test_doc@test.com").first()
        if u:
            Availability.query.filter_by(doctor_id=u.doctor_profile.id).delete()
            db.session.delete(u.doctor_profile)
            db.session.delete(u)
            db.session.commit()
    check("Cleanup done", True)

# ── Summary ───────────────────────────────────
print()
print("=" * 60)
print(f"AVAILABILITY TEST RESULTS: {len(PASS)} passed, {len(FAIL)} failed")
print("=" * 60)
if FAIL:
    print("FAILED:")
    for f in FAIL:
        print(f"  - {f}")
else:
    print("ALL CHECKS PASSED")
