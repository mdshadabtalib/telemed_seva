"""API — Cart endpoints for pharmacy shopping."""
from flask import jsonify, request
from flask_login import login_required, current_user

from . import api_bp
from ..models.order import Cart, CartItem
from ..models.pharmacy import Medicine
from ..models.user import UserRole
from ..extensions import db


def _get_or_create_cart():
    """Helper to get or create cart for current user."""
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    if not cart:
        cart = Cart(user_id=current_user.id)
        db.session.add(cart)
        db.session.commit()
    return cart


def _serialize_cart(cart):
    """Serialize cart object to JSON."""
    if not cart:
        return {
            'items': [],
            'total_items': 0,
            'subtotal': 0,
            'requires_prescription': False,
        }
    
    return {
        'id': cart.id,
        'items': [{
            'id': item.id,
            'medicine': {
                'id': item.medicine.id,
                'name': item.medicine.name,
                'generic_name': item.medicine.generic_name,
                'manufacturer': item.medicine.manufacturer,
                'dosage_form': item.medicine.dosage_form.value,
                'strength': item.medicine.strength,
                'price': float(item.medicine.price),
                'discount_percent': float(item.medicine.discount_percent),
                'selling_price': float(item.medicine.selling_price),
                'image_url': item.medicine.image_url,
                'requires_prescription': item.medicine.requires_prescription,
                'in_stock': item.medicine.in_stock,
                'stock_quantity': item.medicine.stock_quantity,
            },
            'quantity': item.quantity,
            'line_total': float(item.line_total),
        } for item in cart.items],
        'total_items': cart.total_items,
        'subtotal': float(cart.subtotal),
        'requires_prescription': cart.requires_prescription,
        'created_at': cart.created_at.isoformat(),
        'updated_at': cart.updated_at.isoformat(),
    }


@api_bp.route('/cart', methods=['GET'])
@login_required
def api_get_cart():
    """Get current user's shopping cart."""
    if current_user.role != UserRole.PATIENT:
        return jsonify({'error': 'Only patients can access cart'}), 403
    
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    return jsonify(_serialize_cart(cart))


@api_bp.route('/cart/add', methods=['POST'])
@login_required
def api_add_to_cart():
    """Add a medicine to the cart."""
    if current_user.role != UserRole.PATIENT:
        return jsonify({'error': 'Only patients can add to cart'}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid request data'}), 400
    
    medicine_id = data.get('medicine_id')
    quantity = data.get('quantity', 1)
    
    if not medicine_id:
        return jsonify({'error': 'medicine_id is required'}), 400
    
    medicine = Medicine.query.get(medicine_id)
    if not medicine:
        return jsonify({'error': 'Medicine not found'}), 404
    
    if not medicine.is_active:
        return jsonify({'error': 'This medicine is no longer available'}), 400
    
    if not medicine.in_stock:
        return jsonify({'error': 'This medicine is out of stock'}), 400
    
    if quantity < 1:
        quantity = 1
    if quantity > medicine.stock_quantity:
        return jsonify({'error': f'Only {medicine.stock_quantity} units available'}), 400
    
    cart = _get_or_create_cart()
    
    # Check if item already exists in cart
    item = CartItem.query.filter_by(cart_id=cart.id, medicine_id=medicine_id).first()
    if item:
        new_quantity = item.quantity + quantity
        if new_quantity > medicine.stock_quantity:
            return jsonify({'error': f'Cannot add more. Only {medicine.stock_quantity} units available'}), 400
        item.quantity = new_quantity
    else:
        item = CartItem(cart_id=cart.id, medicine_id=medicine_id, quantity=quantity)
        db.session.add(item)
    
    db.session.commit()
    
    return jsonify({
        'message': f'{medicine.name} added to cart',
        'cart': _serialize_cart(cart),
    }), 200


@api_bp.route('/cart/update', methods=['PUT', 'PATCH'])
@login_required
def api_update_cart_item():
    """Update quantity of a cart item."""
    if current_user.role != UserRole.PATIENT:
        return jsonify({'error': 'Only patients can update cart'}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid request data'}), 400
    
    item_id = data.get('item_id')
    quantity = data.get('quantity')
    
    if not item_id or quantity is None:
        return jsonify({'error': 'item_id and quantity are required'}), 400
    
    item = CartItem.query.get(item_id)
    if not item:
        return jsonify({'error': 'Cart item not found'}), 404
    
    if item.cart.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if quantity < 1:
        # Remove item if quantity is 0 or negative
        db.session.delete(item)
        message = 'Item removed from cart'
    else:
        if quantity > item.medicine.stock_quantity:
            return jsonify({'error': f'Only {item.medicine.stock_quantity} units available'}), 400
        item.quantity = quantity
        message = 'Cart updated'
    
    db.session.commit()
    
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    return jsonify({
        'message': message,
        'cart': _serialize_cart(cart),
    })


@api_bp.route('/cart/remove/<int:item_id>', methods=['DELETE'])
@login_required
def api_remove_from_cart(item_id):
    """Remove an item from the cart."""
    if current_user.role != UserRole.PATIENT:
        return jsonify({'error': 'Only patients can modify cart'}), 403
    
    item = CartItem.query.get(item_id)
    if not item:
        return jsonify({'error': 'Cart item not found'}), 404
    
    if item.cart.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    medicine_name = item.medicine.name
    db.session.delete(item)
    db.session.commit()
    
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    return jsonify({
        'message': f'{medicine_name} removed from cart',
        'cart': _serialize_cart(cart),
    })


@api_bp.route('/cart/clear', methods=['POST', 'DELETE'])
@login_required
def api_clear_cart():
    """Clear all items from the cart."""
    if current_user.role != UserRole.PATIENT:
        return jsonify({'error': 'Only patients can clear cart'}), 403
    
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    if cart:
        for item in cart.items:
            db.session.delete(item)
        db.session.commit()
    
    return jsonify({
        'message': 'Cart cleared',
        'cart': _serialize_cart(cart),
    })
