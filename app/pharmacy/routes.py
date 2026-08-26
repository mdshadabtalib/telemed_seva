"""Pharmacy routes — catalog, cart, checkout, orders."""
from decimal import Decimal
from datetime import datetime, timezone

from flask import render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import current_user, login_required

from . import pharmacy_bp
from ..extensions import db
from ..models.user import UserRole
from ..models.pharmacy import Medicine, MedicineCategory, Inventory
from ..models.order import Cart, CartItem, Order, OrderItem, OrderStatus
from ..models.address import Address
from ..models.prescription import Prescription
from ..services.notification_service import notify_order_status
from ..utils.decorators import role_required
from ..utils.helpers import paginate_query, save_upload


# ---- Public Catalog ----

@pharmacy_bp.route('/')
def catalog():
    categories = MedicineCategory.query.filter_by(is_active=True).order_by(MedicineCategory.name).all()
    query = Medicine.query.filter_by(is_active=True)

    category_slug = request.args.get('category')
    if category_slug:
        cat = MedicineCategory.query.filter_by(slug=category_slug).first()
        if cat:
            query = query.filter_by(category_id=cat.id)

    search = request.args.get('q', '').strip()
    if search:
        query = query.filter(
            db.or_(
                Medicine.name.ilike(f'%{search}%'),
                Medicine.generic_name.ilike(f'%{search}%'),
            )
        )

    medicines = paginate_query(query.order_by(Medicine.name), per_page=16)
    return render_template(
        'pharmacy/catalog.html', title='Pharmacy',
        medicines=medicines, categories=categories, filters=request.args,
    )


@pharmacy_bp.route('/medicine/<int:medicine_id>')
def medicine_detail(medicine_id):
    medicine = Medicine.query.get_or_404(medicine_id)
    return render_template(
        'pharmacy/medicine_detail.html',
        title=medicine.name, medicine=medicine,
    )


# ---- Cart ----

def _get_or_create_cart():
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    if not cart:
        cart = Cart(user_id=current_user.id)
        db.session.add(cart)
        db.session.flush()
    return cart


@pharmacy_bp.route('/cart')
@role_required(UserRole.PATIENT)
def cart():
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    return render_template('pharmacy/cart.html', title='Shopping Cart', cart=cart)


@pharmacy_bp.route('/cart/add', methods=['POST'])
@role_required(UserRole.PATIENT)
def add_to_cart():
    medicine_id = request.form.get('medicine_id', type=int)
    quantity = request.form.get('quantity', 1, type=int)

    medicine = Medicine.query.get_or_404(medicine_id)
    if not medicine.is_active:
        flash('This medicine is no longer available.', 'warning')
        return redirect(url_for('pharmacy.catalog'))

    if not medicine.in_stock:
        flash('This medicine is out of stock.', 'warning')
        return redirect(url_for('pharmacy.medicine_detail', medicine_id=medicine_id))

    if quantity < 1:
        quantity = 1
    if quantity > medicine.stock_quantity:
        quantity = medicine.stock_quantity

    cart = _get_or_create_cart()

    item = CartItem.query.filter_by(cart_id=cart.id, medicine_id=medicine_id).first()
    if item:
        item.quantity = min(item.quantity + quantity, medicine.stock_quantity)
    else:
        item = CartItem(cart_id=cart.id, medicine_id=medicine_id, quantity=quantity)
        db.session.add(item)

    db.session.commit()
    flash(f'{medicine.name} added to cart.', 'success')

    next_url = request.form.get('next') or url_for('pharmacy.catalog')
    return redirect(next_url)


@pharmacy_bp.route('/cart/update', methods=['POST'])
@role_required(UserRole.PATIENT)
def update_cart():
    item_id = request.form.get('item_id', type=int)
    quantity = request.form.get('quantity', type=int)

    item = CartItem.query.get_or_404(item_id)
    if item.cart.user_id != current_user.id:
        abort(403)

    if quantity and quantity > 0:
        item.quantity = min(quantity, item.medicine.stock_quantity)
    else:
        db.session.delete(item)

    db.session.commit()
    return redirect(url_for('pharmacy.cart'))


@pharmacy_bp.route('/cart/remove/<int:item_id>', methods=['POST'])
@role_required(UserRole.PATIENT)
def remove_from_cart(item_id):
    item = CartItem.query.get_or_404(item_id)
    if item.cart.user_id != current_user.id:
        abort(403)
    db.session.delete(item)
    db.session.commit()
    flash('Item removed from cart.', 'info')
    return redirect(url_for('pharmacy.cart'))


# ---- Checkout ----

@pharmacy_bp.route('/checkout', methods=['GET', 'POST'])
@role_required(UserRole.PATIENT)
def checkout():
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    if not cart or not cart.items:
        flash('Your cart is empty.', 'warning')
        return redirect(url_for('pharmacy.catalog'))

    addresses = Address.query.filter_by(user_id=current_user.id).all()

    # Check prescription requirements
    rx_required = cart.requires_prescription

    if request.method == 'POST':
        address_id = request.form.get('address_id', type=int)
        if not address_id:
            flash('Please select a delivery address.', 'danger')
            return redirect(url_for('pharmacy.checkout'))

        address = Address.query.filter_by(id=address_id, user_id=current_user.id).first()
        if not address:
            flash('Invalid address.', 'danger')
            return redirect(url_for('pharmacy.checkout'))

        # Handle prescription upload if needed
        prescription_id = None
        prescription_image = None

        if rx_required:
            rx_id = request.form.get('prescription_id', type=int)
            rx_file = request.files.get('prescription_image')

            if rx_id:
                rx = Prescription.query.filter_by(id=rx_id, patient_id=current_user.id).first()
                if rx:
                    prescription_id = rx.id
            elif rx_file and rx_file.filename:
                filename = save_upload(rx_file, 'prescriptions')
                if filename:
                    prescription_image = filename

            if not prescription_id and not prescription_image:
                flash('Prescription is required for one or more items. '
                      'Please upload a prescription or select an existing one.', 'danger')
                return redirect(url_for('pharmacy.checkout'))

        # Validate stock and create order within a transaction
        subtotal = Decimal('0')
        order_items = []

        for ci in cart.items:
            inv = ci.medicine.inventory
            if not inv or inv.stock_quantity < ci.quantity:
                flash(f'{ci.medicine.name} is out of stock or has insufficient quantity.', 'danger')
                return redirect(url_for('pharmacy.cart'))

            line_total = Decimal(str(ci.medicine.selling_price)) * ci.quantity
            subtotal += line_total
            order_items.append({
                'medicine': ci.medicine,
                'quantity': ci.quantity,
                'unit_price': Decimal(str(ci.medicine.selling_price)),
                'total_price': line_total,
            })

        delivery_charge = Decimal('0') if subtotal >= 500 else Decimal('49')
        tax = (subtotal * Decimal('0.05')).quantize(Decimal('0.01'))  # 5% GST
        total = subtotal + delivery_charge + tax

        order = Order(
            user_id=current_user.id,
            address_id=address_id,
            subtotal=subtotal,
            delivery_charge=delivery_charge,
            tax=tax,
            total=total,
            prescription_id=prescription_id,
            prescription_image=prescription_image,
            status=OrderStatus.PRESCRIPTION_VERIFICATION if rx_required else OrderStatus.PAYMENT_PENDING,
        )
        db.session.add(order)
        db.session.flush()

        for oi_data in order_items:
            oi = OrderItem(
                order_id=order.id,
                medicine_id=oi_data['medicine'].id,
                medicine_name=oi_data['medicine'].name,
                quantity=oi_data['quantity'],
                unit_price=oi_data['unit_price'],
                total_price=oi_data['total_price'],
            )
            db.session.add(oi)

            # Decrement inventory
            oi_data['medicine'].inventory.stock_quantity -= oi_data['quantity']

        # Clear cart
        for ci in cart.items:
            db.session.delete(ci)

        notify_order_status(current_user.id, order, order.status.value)
        db.session.commit()

        if rx_required:
            flash('Order placed! Your prescription is pending verification.', 'success')
        else:
            flash('Order placed successfully!', 'success')

        return redirect(url_for('pharmacy.order_detail', order_id=order.id))

    prescriptions = Prescription.query.filter_by(
        patient_id=current_user.id, is_active=True
    ).order_by(Prescription.created_at.desc()).all()

    return render_template(
        'pharmacy/checkout.html', title='Checkout',
        cart=cart, addresses=addresses, rx_required=rx_required,
        prescriptions=prescriptions,
    )


# ---- Orders ----

@pharmacy_bp.route('/orders')
@role_required(UserRole.PATIENT)
def my_orders():
    orders = paginate_query(
        Order.query.filter_by(user_id=current_user.id)
        .order_by(Order.created_at.desc()),
        per_page=10,
    )
    return render_template('pharmacy/orders.html', title='My Orders', orders=orders)


@pharmacy_bp.route('/orders/<int:order_id>')
@login_required
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    if current_user.id != order.user_id and current_user.role not in (UserRole.ADMIN, UserRole.PHARMACY_ADMIN):
        abort(403)
    return render_template('pharmacy/order_detail.html', title=f'Order {order.order_number}', order=order)
