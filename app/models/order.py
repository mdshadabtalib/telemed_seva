"""Cart, CartItem, Order, and OrderItem models."""
import enum
import uuid
from datetime import datetime, timezone

from ..extensions import db


class Cart(db.Model):
    """Shopping cart for pharmacy orders."""

    __tablename__ = 'carts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False
    )
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    items = db.relationship('CartItem', backref='cart', cascade='all, delete-orphan')
    user = db.relationship('User', backref=db.backref('cart', uselist=False))

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items)

    @property
    def subtotal(self):
        return sum(item.line_total for item in self.items)

    @property
    def requires_prescription(self):
        return any(item.medicine.requires_prescription for item in self.items)

    def __repr__(self):
        return f'<Cart user={self.user_id} items={len(self.items)}>'


class CartItem(db.Model):
    """An item in the shopping cart."""

    __tablename__ = 'cart_items'

    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(
        db.Integer, db.ForeignKey('carts.id', ondelete='CASCADE'), nullable=False
    )
    medicine_id = db.Column(
        db.Integer, db.ForeignKey('medicines.id', ondelete='CASCADE'), nullable=False
    )
    quantity = db.Column(db.Integer, default=1, nullable=False)
    prescription_id = db.Column(
        db.Integer, db.ForeignKey('prescriptions.id'), nullable=True
    )

    medicine = db.relationship('Medicine')
    prescription = db.relationship('Prescription')

    __table_args__ = (
        db.UniqueConstraint('cart_id', 'medicine_id', name='uq_cart_medicine'),
    )

    @property
    def line_total(self):
        return self.medicine.selling_price * self.quantity

    def __repr__(self):
        return f'<CartItem medicine={self.medicine_id} qty={self.quantity}>'


class OrderStatus(enum.Enum):
    PENDING = 'pending'
    PRESCRIPTION_VERIFICATION = 'prescription_verification'
    PAYMENT_PENDING = 'payment_pending'
    PROCESSING = 'processing'
    PACKED = 'packed'
    SHIPPED = 'shipped'
    DELIVERED = 'delivered'
    CANCELLED = 'cancelled'
    REFUNDED = 'refunded'


def _generate_order_number():
    return f'ORD-{uuid.uuid4().hex[:10].upper()}'


class Order(db.Model):
    """A pharmacy order placed by a patient."""

    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(
        db.String(20), unique=True, nullable=False, default=_generate_order_number, index=True
    )
    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True
    )
    address_id = db.Column(
        db.Integer, db.ForeignKey('addresses.id'), nullable=True
    )

    # Pricing
    subtotal = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    delivery_charge = db.Column(db.Numeric(10, 2), default=0)
    discount = db.Column(db.Numeric(10, 2), default=0)
    tax = db.Column(db.Numeric(10, 2), default=0)
    total = db.Column(db.Numeric(10, 2), nullable=False, default=0)

    # Status
    status = db.Column(
        db.Enum(OrderStatus),
        default=OrderStatus.PENDING,
        nullable=False,
        index=True,
    )

    # Prescription
    prescription_id = db.Column(db.Integer, db.ForeignKey('prescriptions.id'), nullable=True)
    prescription_image = db.Column(db.String(500), nullable=True)
    prescription_verified = db.Column(db.Boolean, default=False)
    prescription_verified_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # Delivery
    tracking_number = db.Column(db.String(100), nullable=True)
    estimated_delivery = db.Column(db.Date, nullable=True)
    delivered_at = db.Column(db.DateTime, nullable=True)

    # Coupon
    coupon_code = db.Column(db.String(50), nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='orders')
    address = db.relationship('Address')
    items = db.relationship('OrderItem', backref='order', cascade='all, delete-orphan')
    prescription_ref = db.relationship('Prescription', foreign_keys=[prescription_id])

    def __repr__(self):
        return f'<Order {self.order_number} status={self.status.value}>'


class OrderItem(db.Model):
    """A line item within an order."""

    __tablename__ = 'order_items'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(
        db.Integer, db.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False
    )
    medicine_id = db.Column(
        db.Integer, db.ForeignKey('medicines.id'), nullable=False
    )
    medicine_name = db.Column(db.String(200), nullable=False)  # snapshot
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    total_price = db.Column(db.Numeric(10, 2), nullable=False)

    medicine = db.relationship('Medicine')

    def __repr__(self):
        return f'<OrderItem {self.medicine_name} x{self.quantity}>'
