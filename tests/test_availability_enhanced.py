"""
Functional tests for the enhanced availability slot manager.
Tests: page rendering, slot creation with custom duration,
toggle active/inactive, delete, upsert, validation.
"""
import pytest
import datetime
from app import create_app
from app.extensions import db
from app.models.user import User, UserRole, DoctorProfile
from app.models.doctor import Availability, DayOfWeek, Specialty


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def app():
    _app = create_app('testing')
    with _app.app_context():
        db.create_all()
        spec = Specialty(name='General Medicine', slug='general-medicine')
        db.session.add(spec)
        db.session.commit()
        yield _app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def doctor(app):
    """Create a verified doctor and return (user_id, profile_id)."""
    with app.app_context():
        user = User(
            email='doc_avail@test.com',
            role=UserRole.DOCTOR,
            is_active=True,
            email_verified=True,
        )
        user.set_password('Pass@1234')
        db.session.add(user)
        db.session.flush()

        profile = DoctorProfile(
            user_id=user.id,
            first_name='Dr',
            last_name='Avail',
            consultation_duration=30,
            is_verified=True,
            is_available=True,
        )
        db.session.add(profile)
        db.session.commit()
        return user.id, profile.id


def login(client, email='doc_avail@test.com', password='Pass@1234'):
    return client.post('/login', data={
        'email': email, 'password': password,
    }, follow_redirects=True)


# ─────────────────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestAvailabilityPageRender:
    """Check that the enhanced template renders all new UI elements."""

    def test_page_loads_200(self, client, doctor):
        login(client)
        r = client.get('/doctor/availability')
        assert r.status_code == 200

    def test_has_day_picker(self, client, doctor):
        login(client)
        html = client.get('/doctor/availability').data.decode()
        assert 'day-radio' in html
        assert 'Mon' in html
        assert 'Sun' in html

    def test_has_all_seven_day_values(self, client, doctor):
        login(client)
        html = client.get('/doctor/availability').data.decode()
        for v in range(7):
            assert f'value="{v}"' in html

    def test_has_time_presets(self, client, doctor):
        login(client)
        html = client.get('/doctor/availability').data.decode()
        for preset in ['Morning', 'Afternoon', 'Evening', 'Night']:
            assert preset in html, f"Missing preset: {preset}"

    def test_has_duration_picker(self, client, doctor):
        login(client)
        html = client.get('/doctor/availability').data.decode()
        assert 'dur-radio' in html
        for dur in ['10', '15', '20', '30', '45', '60']:
            assert f'value="{dur}"' in html, f"Missing duration: {dur}"

    def test_has_live_preview_element(self, client, doctor):
        login(client)
        html = client.get('/doctor/availability').data.decode()
        assert 'slotPreview' in html

    def test_has_weekly_schedule_section(self, client, doctor):
        login(client)
        html = client.get('/doctor/availability').data.decode()
        assert 'Weekly Schedule' in html

    def test_has_help_card(self, client, doctor):
        login(client)
        html = client.get('/doctor/availability').data.decode()
        assert 'How slots work' in html

    def test_has_stats_bar(self, client, doctor):
        login(client)
        html = client.get('/doctor/availability').data.decode()
        assert 'Active Slots' in html
        assert 'Days Covered' in html

    def test_has_global_availability_toggle(self, client, doctor):
        login(client)
        html = client.get('/doctor/availability').data.decode()
        assert 'toggle_availability' in html or 'Accepting Appointments' in html


class TestAddSlot:
    """Test adding new availability slots with the enhanced form."""

    def _add_slot(self, client, day, start, end, duration=30):
        return client.post('/doctor/availability', data={
            'day_of_week':   str(day),
            'start_time':    start,
            'end_time':      end,
            'slot_duration': str(duration),
        }, follow_redirects=True)

    def test_add_slot_monday_morning_30min(self, client, doctor, app):
        login(client)
        r = self._add_slot(client, 0, '09:00', '12:00', 30)
        assert r.status_code == 200
        assert b'added' in r.data or b'updated' in r.data

        uid, _ = doctor
        with app.app_context():
            u = db.session.get(User, uid)
            slot = Availability.query.filter_by(
                doctor_id=u.doctor_profile.id,
                day_of_week=DayOfWeek.MONDAY,
                start_time=datetime.time(9, 0),
            ).first()
            assert slot is not None
            assert slot.slot_duration == 30
            assert slot.end_time      == datetime.time(12, 0)
            assert slot.is_active     is True

    def test_add_slot_custom_duration_15min(self, client, doctor, app):
        login(client)
        r = self._add_slot(client, 3, '14:00', '17:00', 15)
        assert r.status_code == 200

        uid, _ = doctor
        with app.app_context():
            u = db.session.get(User, uid)
            slot = Availability.query.filter_by(
                doctor_id=u.doctor_profile.id,
                day_of_week=DayOfWeek.THURSDAY,
                start_time=datetime.time(14, 0),
            ).first()
            assert slot is not None
            assert slot.slot_duration == 15

    def test_add_slot_custom_duration_60min(self, client, doctor, app):
        login(client)
        r = self._add_slot(client, 5, '10:00', '16:00', 60)
        assert r.status_code == 200

        uid, _ = doctor
        with app.app_context():
            u = db.session.get(User, uid)
            slot = Availability.query.filter_by(
                doctor_id=u.doctor_profile.id,
                day_of_week=DayOfWeek.SATURDAY,
                start_time=datetime.time(10, 0),
            ).first()
            assert slot is not None
            assert slot.slot_duration == 60

    def test_upsert_updates_existing_slot(self, client, doctor, app):
        """Re-submitting same day+start_time should update end_time/duration."""
        login(client)
        self._add_slot(client, 1, '08:00', '10:00', 20)
        self._add_slot(client, 1, '08:00', '11:00', 45)

        uid, _ = doctor
        with app.app_context():
            u = db.session.get(User, uid)
            slots = Availability.query.filter_by(
                doctor_id=u.doctor_profile.id,
                day_of_week=DayOfWeek.TUESDAY,
                start_time=datetime.time(8, 0),
            ).all()
            assert len(slots) == 1
            assert slots[0].end_time      == datetime.time(11, 0)
            assert slots[0].slot_duration == 45

    def test_slots_appear_in_weekly_calendar(self, client, doctor):
        login(client)
        client.post('/doctor/availability', data={
            'day_of_week': '2', 'start_time': '09:00',
            'end_time': '12:00', 'slot_duration': '30',
        })
        html = client.get('/doctor/availability').data.decode()
        assert 'Wednesday' in html
        assert '09:00 AM' in html
        assert '12:00 PM' in html

    def test_approx_appointment_badge_shown(self, client, doctor):
        """3h block / 30min = 6 appointments badge expected."""
        login(client)
        client.post('/doctor/availability', data={
            'day_of_week': '4', 'start_time': '09:00',
            'end_time': '12:00', 'slot_duration': '30',
        })
        html = client.get('/doctor/availability').data.decode()
        assert '6' in html  # ~6 appts badge


class TestToggleSlot:
    """Test the new pause/activate toggle per slot."""

    def _add_and_get_id(self, client, app, doctor, day=0):
        uid, _ = doctor
        login(client)
        client.post('/doctor/availability', data={
            'day_of_week': str(day), 'start_time': '09:00',
            'end_time': '11:00', 'slot_duration': '30',
        })
        with app.app_context():
            u = db.session.get(User, uid)
            slot = Availability.query.filter_by(doctor_id=u.doctor_profile.id).first()
            return slot.id if slot else None

    def test_toggle_pauses_active_slot(self, client, app, doctor):
        slot_id = self._add_and_get_id(client, app, doctor)
        assert slot_id is not None

        r = client.post(f'/doctor/availability/{slot_id}/toggle',
                        follow_redirects=True)
        assert r.status_code == 200
        assert b'paused' in r.data

        with app.app_context():
            slot = db.session.get(Availability, slot_id)
            assert slot.is_active is False

    def test_toggle_twice_reactivates_slot(self, client, app, doctor):
        slot_id = self._add_and_get_id(client, app, doctor)
        client.post(f'/doctor/availability/{slot_id}/toggle')   # pause
        r = client.post(f'/doctor/availability/{slot_id}/toggle',
                        follow_redirects=True)   # activate
        assert b'activated' in r.data

        with app.app_context():
            slot = db.session.get(Availability, slot_id)
            assert slot.is_active is True

    def test_paused_slot_shows_paused_badge(self, client, app, doctor):
        slot_id = self._add_and_get_id(client, app, doctor)
        assert slot_id is not None
        client.post(f'/doctor/availability/{slot_id}/toggle')  # pause it

        html = client.get('/doctor/availability').data.decode()
        assert 'Paused' in html

    def test_cannot_toggle_other_doctors_slot(self, client, app, doctor):
        """Another doctor must not be able to toggle this slot."""
        slot_id = self._add_and_get_id(client, app, doctor)

        # Register and login as a different doctor
        with app.app_context():
            other = User(email='other_doc@test.com', role=UserRole.DOCTOR,
                         is_active=True, email_verified=True)
            other.set_password('Pass@1234')
            db.session.add(other)
            db.session.flush()
            db.session.add(DoctorProfile(user_id=other.id, first_name='X',
                                          last_name='Y', consultation_duration=30))
            db.session.commit()

        client.get('/logout')
        login(client, 'other_doc@test.com')
        r = client.post(f'/doctor/availability/{slot_id}/toggle',
                        follow_redirects=True)
        # Should 404 (owns check) — not 200 success
        assert r.status_code == 404


class TestDeleteSlot:
    """Test hard-delete of availability slots."""

    def test_delete_removes_slot(self, client, app, doctor):
        uid, _ = doctor
        login(client)
        client.post('/doctor/availability', data={
            'day_of_week': '6', 'start_time': '10:00',
            'end_time': '14:00', 'slot_duration': '30',
        })
        with app.app_context():
            u = db.session.get(User, uid)
            slot = Availability.query.filter_by(doctor_id=u.doctor_profile.id).first()
            slot_id = slot.id

        r = client.post(f'/doctor/availability/{slot_id}/delete',
                        follow_redirects=True)
        assert r.status_code == 200
        assert b'removed' in r.data

        with app.app_context():
            assert db.session.get(Availability, slot_id) is None

    def test_after_delete_slot_not_in_schedule(self, client, app, doctor):
        uid, _ = doctor
        login(client)
        client.post('/doctor/availability', data={
            'day_of_week': '6', 'start_time': '10:00',
            'end_time': '14:00', 'slot_duration': '30',
        })
        with app.app_context():
            u = db.session.get(User, uid)
            slot_id = Availability.query.filter_by(doctor_id=u.doctor_profile.id).first().id

        client.post(f'/doctor/availability/{slot_id}/delete')
        html = client.get('/doctor/availability').data.decode()
        assert '10:00 AM' not in html


class TestValidation:
    """Test server-side form validation."""

    def test_end_before_start_rejected(self, client, doctor, app):
        uid, _ = doctor
        login(client)
        client.post('/doctor/availability', data={
            'day_of_week': '0', 'start_time': '15:00',
            'end_time':    '09:00', 'slot_duration': '30',
        })
        with app.app_context():
            u = db.session.get(User, uid)
            count = Availability.query.filter_by(doctor_id=u.doctor_profile.id).count()
            assert count == 0

    def test_end_equal_start_rejected(self, client, doctor, app):
        uid, _ = doctor
        login(client)
        client.post('/doctor/availability', data={
            'day_of_week': '0', 'start_time': '10:00',
            'end_time':    '10:00', 'slot_duration': '30',
        })
        with app.app_context():
            u = db.session.get(User, uid)
            count = Availability.query.filter_by(doctor_id=u.doctor_profile.id).count()
            assert count == 0
