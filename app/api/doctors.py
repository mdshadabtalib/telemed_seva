"""API — Doctor endpoints."""
from flask import jsonify, request

from . import api_bp
from ..models.user import DoctorProfile
from ..models.doctor import Specialty
from ..extensions import db


@api_bp.route('/doctors')
def api_doctors():
    """List verified doctors with optional filters."""
    query = DoctorProfile.query.filter_by(is_verified=True, is_available=True)

    specialty_id = request.args.get('specialty', type=int)
    if specialty_id:
        query = query.filter_by(specialty_id=specialty_id)

    name = request.args.get('name', '').strip()
    if name:
        query = query.filter(db.or_(
            DoctorProfile.first_name.ilike(f'%{name}%'),
            DoctorProfile.last_name.ilike(f'%{name}%'),
        ))

    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 50)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    doctors = [{
        'id': d.id,
        'name': f'Dr. {d.full_name}',
        'specialty': d.specialty.name if d.specialty else None,
        'qualifications': d.qualifications,
        'experience_years': d.experience_years,
        'consultation_fee': float(d.consultation_fee) if d.consultation_fee else 0,
        'rating': d.average_rating,
        'review_count': d.review_count,
        'languages': d.languages_list,
        'avatar_url': d.user.avatar_url,
    } for d in pagination.items]

    return jsonify({
        'doctors': doctors,
        'total': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages,
    })


@api_bp.route('/specialties')
def api_specialties():
    specs = Specialty.query.filter_by(is_active=True).order_by(Specialty.display_order).all()
    return jsonify({
        'specialties': [{
            'id': s.id,
            'name': s.name,
            'slug': s.slug,
            'icon': s.icon,
        } for s in specs]
    })
