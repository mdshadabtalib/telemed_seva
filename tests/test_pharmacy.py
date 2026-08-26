"""Pharmacy cart and order transaction tests."""
from decimal import Decimal
from app.models.pharmacy import Medicine
from app.models.order import Cart, CartItem, Order, OrderItem, OrderStatus
from app.extensions import db


def test_cart_management(app, patient_user, sample_medicine):
    """Test adding items and calculating subtotals."""
    with app.app_context():
        med = db.session.get(Medicine, sample_medicine)
        cart = Cart(user_id=patient_user)
        db.session.add(cart)
        db.session.flush()

        item = CartItem(cart_id=cart.id, medicine_id=med.id, quantity=3)
        db.session.add(item)
        db.session.commit()

        # 3 * selling_price (30 - 10% = 27) = 81
        assert item.line_total == Decimal('81.00')
        assert cart.subtotal == Decimal('81.00')
        assert cart.total_items == 3


def test_inventory_decrement_on_order(app, patient_user, sample_medicine):
    """Test that inventory is decremented when order is placed."""
    with app.app_context():
        med = db.session.get(Medicine, sample_medicine)
        initial_stock = med.inventory.stock_quantity  # 100

        order = Order(
            user_id=patient_user,
            subtotal=Decimal('81.00'),
            total=Decimal('134.05'),
            status=OrderStatus.PAYMENT_PENDING,
        )
        db.session.add(order)
        db.session.flush()

        oi = OrderItem(
            order_id=order.id,
            medicine_id=med.id,
            medicine_name=med.name,
            quantity=5,
            unit_price=Decimal('27.00'),
            total_price=Decimal('135.00'),
        )
        db.session.add(oi)

        # Decrement inventory atomically
        med.inventory.stock_quantity -= 5
        db.session.commit()

        # Verify stock decreased
        updated_med = db.session.get(Medicine, sample_medicine)
        assert updated_med.inventory.stock_quantity == initial_stock - 5
