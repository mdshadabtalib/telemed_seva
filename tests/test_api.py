"""API and Doctor search tests."""
from app.models.user import DoctorProfile


def test_api_doctor_search(client, doctor_user):
    """Test public API doctor search endpoint."""
    res = client.get('/api/doctors')
    assert res.status_code == 200
    data = res.get_json()
    assert 'doctors' in data
    assert len(data['doctors']) >= 1
    assert data['doctors'][0]['name'] == 'Dr. John Smith'


def test_api_specialties(client):
    """Test public API specialties list."""
    res = client.get('/api/specialties')
    assert res.status_code == 200
    data = res.get_json()
    assert 'specialties' in data
    assert len(data['specialties']) >= 1
