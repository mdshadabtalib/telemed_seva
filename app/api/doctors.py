"""API — Doctor endpoints."""
from flask import jsonify, request

from . import api_bp
from ..models.user import DoctorProfile
from ..models.doctor import Specialty
from ..extensions import db


@api_bp.route('/doctors')
def api_doctors():
    """List verified doctors with optional filters and pagination."""
    query = DoctorProfile.query.filter_by(is_verified=True, is_available=True)

    # Filter by specialty
    specialty_id = request.args.get('specialty', type=int)
    if specialty_id:
        query = query.filter_by(specialty_id=specialty_id)

    # Filter by name (first or last name)
    name = request.args.get('name', '').strip()
    if name:
        query = query.filter(db.or_(
            DoctorProfile.first_name.ilike(f'%{name}%'),
            DoctorProfile.last_name.ilike(f'%{name}%'),
        ))

    # Filter by consultation fee range
    min_fee = request.args.get('min_fee', type=float)
    max_fee = request.args.get('max_fee', type=float)
    if min_fee is not None:
        query = query.filter(DoctorProfile.consultation_fee >= min_fee)
    if max_fee is not None:
        query = query.filter(DoctorProfile.consultation_fee <= max_fee)

    # Filter by minimum experience years
    min_experience = request.args.get('min_experience', type=int)
    if min_experience is not None:
        query = query.filter(DoctorProfile.experience_years >= min_experience)

    # Filter by language
    language = request.args.get('language', '').strip()
    if language:
        query = query.filter(DoctorProfile.languages.ilike(f'%{language}%'))

    # Sorting
    sort_by = request.args.get('sort', 'name')
    if sort_by == 'fee_low':
        query = query.order_by(DoctorProfile.consultation_fee.asc())
    elif sort_by == 'fee_high':
        query = query.order_by(DoctorProfile.consultation_fee.desc())
    elif sort_by == 'experience':
        query = query.order_by(DoctorProfile.experience_years.desc())
    else:  # default: sort by name
        query = query.order_by(DoctorProfile.first_name, DoctorProfile.last_name)

    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 50)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    # Bulk-load rating stats — prevents N+1 on the doctor list
    DoctorProfile.load_rating_stats([d.id for d in pagination.items])

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
        'per_page': per_page,
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
