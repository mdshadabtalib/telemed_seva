"""Admin routes — dashboard, verification, user/order/medicine management."""
from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import current_user

from . import admin_bp
from ..extensions import db
from ..models.user import User, UserRole, DoctorProfile
from ..models.doctor import DoctorVerification, VerificationStatus, Specialty
from ..models.appointment import Appointment, AppointmentStatus
from ..models.pharmacy import Medicine, MedicineCategory, Inventory, DosageForm
from ..models.order import Order, OrderStatus
from ..models.payment import Payment
from ..models.support import SupportTicket, TicketStatus
from ..models.audit import AuditLog
from ..services.notification_service import notify_verification_update, notify_order_status
from ..utils.decorators import admin_required
from ..utils.helpers import paginate_query, slugify, save_upload
from ..utils.security import log_audit
from datetime import datetime, timezone


@admin_bp.route('/')
@admin_required
def dashboard():
    stats = {
        'total_patients': User.query.filter_by(role=UserRole.PATIENT).count(),
        'total_doctors': User.query.filter_by(role=UserRole.DOCTOR).count(),
        'pending_verifications': DoctorVerification.query.filter_by(
            status=VerificationStatus.PENDING
        ).count(),
        'total_appointments': Appointment.query.count(),
        'active_appointments': Appointment.query.filter(
            Appointment.status.in_([AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED])
        ).count(),
        'total_orders': Order.query.count(),
        'pending_orders': Order.query.filter(
            Order.status.in_([OrderStatus.PENDING, OrderStatus.PRESCRIPTION_VERIFICATION, OrderStatus.PROCESSING])
        ).count(),
        'total_revenue': db.session.query(
            db.func.coalesce(db.func.sum(Payment.amount), 0)
        ).filter_by(status='completed').scalar(),
        'open_tickets': SupportTicket.query.filter_by(status=TicketStatus.OPEN).count(),
    }
    return render_template('admin/dashboard.html', title='Admin Dashboard', stats=stats)


# ---- Doctor Verification ----

@admin_bp.route('/verifications')
@admin_required
def verifications():
    status_filter = request.args.get('status', 'pending')
    try:
        st = VerificationStatus(status_filter)
    except ValueError:
        st = VerificationStatus.PENDING

    query = DoctorVerification.query.filter_by(status=st)\
        .order_by(DoctorVerification.submitted_at.desc())
    verifications = paginate_query(query, per_page=20)

    return render_template(
        'admin/verifications.html', title='Doctor Verifications',
        verifications=verifications, current_status=status_filter,
    )


@admin_bp.route('/verifications/<int:v_id>', methods=['GET', 'POST'])
@admin_required
def verification_detail(v_id):
    v = DoctorVerification.query.get_or_404(v_id)

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'approve':
            v.status = VerificationStatus.APPROVED
            v.reviewed_by = current_user.id
            v.reviewed_at = datetime.now(timezone.utc)
            v.doctor.is_verified = True
            notify_verification_update(v.doctor.user_id, 'approved')
            log_audit(current_user.id, 'approve_verification', 'doctor_verification', v.id)
            flash(f'Dr. {v.doctor.full_name} has been verified.', 'success')
        elif action == 'reject':
            v.status = VerificationStatus.REJECTED
            v.reviewed_by = current_user.id
            v.reviewed_at = datetime.now(timezone.utc)
            v.rejection_reason = request.form.get('reason', '')
            v.doctor.is_verified = False
            notify_verification_update(v.doctor.user_id, 'rejected')
            log_audit(current_user.id, 'reject_verification', 'doctor_verification', v.id)
            flash(f'Dr. {v.doctor.full_name} verification rejected.', 'info')

        db.session.commit()
        return redirect(url_for('admin.verifications'))

    return render_template(
        'admin/verification_detail.html', title='Verification Review', verification=v,
    )


# ---- User Management ----

@admin_bp.route('/users')
@admin_required
def users():
    role_filter = request.args.get('role')
    query = User.query

    if role_filter:
        try:
            query = query.filter_by(role=UserRole(role_filter))
        except ValueError:
            pass

    users = paginate_query(query.order_by(User.created_at.desc()), per_page=25)
    return render_template('admin/users.html', title='User Management', users=users, roles=UserRole)


@admin_bp.route('/users/<int:user_id>/toggle', methods=['POST'])
@admin_required
def toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot deactivate yourself.', 'danger')
        return redirect(url_for('admin.users'))
    user.is_active = not user.is_active
    status = 'activated' if user.is_active else 'deactivated'
    log_audit(current_user.id, f'{status}_user', 'user', user.id)
    db.session.commit()
    flash(f'User {user.email} has been {status}.', 'info')
    return redirect(url_for('admin.users'))


# ---- Medicine Management ----

@admin_bp.route('/medicines')
@admin_required
def medicines():
    query = Medicine.query.order_by(Medicine.name)
    medicines = paginate_query(query, per_page=25)
    return render_template('admin/medicines.html', title='Medicine Management', medicines=medicines)


@admin_bp.route('/medicines/add', methods=['GET', 'POST'])
@admin_required
def add_medicine():
    categories = MedicineCategory.query.filter_by(is_active=True).order_by(MedicineCategory.name).all()

    if request.method == 'POST':
        med = Medicine(
            name=request.form.get('name', '').strip(),
            generic_name=request.form.get('generic_name', '').strip(),
            category_id=request.form.get('category_id', type=int),
            manufacturer=request.form.get('manufacturer', '').strip(),
            description=request.form.get('description', '').strip(),
            dosage_form=DosageForm(request.form.get('dosage_form', 'tablet')),
            strength=request.form.get('strength', '').strip(),
            pack_size=request.form.get('pack_size', '').strip(),
            price=float(request.form.get('price', 0)),
            discount_percent=float(request.form.get('discount_percent', 0)),
            requires_prescription='requires_prescription' in request.form,
        )

        image = request.files.get('image')
        if image and image.filename:
            filename = save_upload(image, 'medicines',
                                   allowed_extensions={'png', 'jpg', 'jpeg', 'webp'})
            if filename:
                med.image_url = f'/uploads/medicines/{filename}'

        db.session.add(med)
        db.session.flush()

        # Create inventory entry
        inv = Inventory(
            medicine_id=med.id,
            stock_quantity=int(request.form.get('stock', 0)),
            reorder_level=int(request.form.get('reorder_level', 10)),
        )
        db.session.add(inv)
        db.session.commit()

        flash(f'Medicine "{med.name}" added.', 'success')
        return redirect(url_for('admin.medicines'))

    return render_template(
        'admin/medicine_form.html', title='Add Medicine',
        categories=categories, dosage_forms=DosageForm, medicine=None,
    )


@admin_bp.route('/medicines/<int:med_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_medicine(med_id):
    med = Medicine.query.get_or_404(med_id)
    categories = MedicineCategory.query.filter_by(is_active=True).order_by(MedicineCategory.name).all()

    if request.method == 'POST':
        med.name = request.form.get('name', '').strip()
        med.generic_name = request.form.get('generic_name', '').strip()
        med.category_id = request.form.get('category_id', type=int)
        med.manufacturer = request.form.get('manufacturer', '').strip()
        med.description = request.form.get('description', '').strip()
        med.dosage_form = DosageForm(request.form.get('dosage_form', 'tablet'))
        med.strength = request.form.get('strength', '').strip()
        med.pack_size = request.form.get('pack_size', '').strip()
        med.price = float(request.form.get('price', 0))
        med.discount_percent = float(request.form.get('discount_percent', 0))
        med.requires_prescription = 'requires_prescription' in request.form
        med.is_active = 'is_active' in request.form

        image = request.files.get('image')
        if image and image.filename:
            filename = save_upload(image, 'medicines',
                                   allowed_extensions={'png', 'jpg', 'jpeg', 'webp'})
            if filename:
                med.image_url = f'/uploads/medicines/{filename}'

        if med.inventory:
            med.inventory.stock_quantity = int(request.form.get('stock', med.inventory.stock_quantity))
            med.inventory.reorder_level = int(request.form.get('reorder_level', med.inventory.reorder_level))

        db.session.commit()
        flash(f'Medicine "{med.name}" updated.', 'success')
        return redirect(url_for('admin.medicines'))

    return render_template(
        'admin/medicine_form.html', title='Edit Medicine',
        categories=categories, dosage_forms=DosageForm, medicine=med,
    )


# ---- Order Management ----

@admin_bp.route('/orders')
@admin_required
def orders():
    status_filter = request.args.get('status')
    query = Order.query

    if status_filter:
        try:
            query = query.filter_by(status=OrderStatus(status_filter))
        except ValueError:
            pass

    orders = paginate_query(query.order_by(Order.created_at.desc()), per_page=20)
    return render_template(
        'admin/orders.html', title='Order Management',
        orders=orders, statuses=OrderStatus,
    )


@admin_bp.route('/orders/<int:order_id>/status', methods=['POST'])
@admin_required
def update_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('status')

    try:
        order.status = OrderStatus(new_status)
    except ValueError:
        flash('Invalid status.', 'danger')
        return redirect(url_for('admin.orders'))

    if order.status == OrderStatus.DELIVERED:
        order.delivered_at = datetime.now(timezone.utc)

    # Verify prescription if that's the status change
    if new_status == 'processing' and order.prescription_image:
        order.prescription_verified = True
        order.prescription_verified_by = current_user.id

    notify_order_status(order.user_id, order, new_status)
    log_audit(current_user.id, 'update_order_status', 'order', order.id, f'Status → {new_status}')
    db.session.commit()

    flash(f'Order {order.order_number} status updated to {new_status}.', 'success')
    return redirect(url_for('admin.orders'))


# ---- Support Tickets ----

@admin_bp.route('/tickets')
@admin_required
def tickets():
    status_filter = request.args.get('status', 'open')
    try:
        st = TicketStatus(status_filter)
    except ValueError:
        st = TicketStatus.OPEN

    query = SupportTicket.query.filter_by(status=st).order_by(SupportTicket.created_at.desc())
    tickets = paginate_query(query, per_page=20)
    return render_template('admin/tickets.html', title='Support Tickets', tickets=tickets, statuses=TicketStatus)


@admin_bp.route('/tickets/<int:ticket_id>/resolve', methods=['POST'])
@admin_required
def resolve_ticket(ticket_id):
    ticket = SupportTicket.query.get_or_404(ticket_id)
    ticket.status = TicketStatus.RESOLVED
    ticket.resolution_notes = request.form.get('resolution', '')
    ticket.assigned_to = current_user.id
    db.session.commit()
    flash('Ticket resolved.', 'success')
    return redirect(url_for('admin.tickets'))


# ---- Pharmacy Dashboard (for pharmacy_admin role) ----

@admin_bp.route('/pharmacy-dashboard')
def pharmacy_dashboard():
    if current_user.role not in (UserRole.ADMIN, UserRole.PHARMACY_ADMIN):
        abort(403)
    return redirect(url_for('admin.orders'))


# ---- Audit Logs ----

@admin_bp.route('/audit-logs')
@admin_required
def audit_logs():
    logs = paginate_query(
        AuditLog.query.order_by(AuditLog.created_at.desc()),
        per_page=50,
    )
    return render_template('admin/audit_logs.html', title='Audit Logs', logs=logs)
