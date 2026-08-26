"""Medicine, MedicineCategory, and Inventory models."""
import enum
from datetime import datetime, timezone

from ..extensions import db


class DosageForm(enum.Enum):
    TABLET = 'tablet'
    CAPSULE = 'capsule'
    SYRUP = 'syrup'
    INJECTION = 'injection'
    CREAM = 'cream'
    OINTMENT = 'ointment'
    DROPS = 'drops'
    INHALER = 'inhaler'
    POWDER = 'powder'
    GEL = 'gel'
    SPRAY = 'spray'
    PATCH = 'patch'
    SUPPOSITORY = 'suppository'
    OTHER = 'other'


class MedicineCategory(db.Model):
    """Category for organising medicines (e.g. Pain Relief, Antibiotics)."""

    __tablename__ = 'medicine_categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    slug = db.Column(db.String(120), unique=True, nullable=False, index=True)
    description = db.Column(db.Text)
    icon = db.Column(db.String(50))
    is_active = db.Column(db.Boolean, default=True)

    medicines = db.relationship('Medicine', backref='category', lazy='dynamic')

    def __repr__(self):
        return f'<MedicineCategory {self.name}>'


class Medicine(db.Model):
    """A medicine available in the pharmacy catalogue."""

    __tablename__ = 'medicines'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, index=True)
    generic_name = db.Column(db.String(200), index=True)
    category_id = db.Column(
        db.Integer, db.ForeignKey('medicine_categories.id'), nullable=True
    )
    manufacturer = db.Column(db.String(200))
    description = db.Column(db.Text)
    dosage_form = db.Column(db.Enum(DosageForm))
    strength = db.Column(db.String(50))
    pack_size = db.Column(db.String(50))

    # Pricing
    price = db.Column(db.Numeric(10, 2), nullable=False)
    discount_percent = db.Column(db.Numeric(5, 2), default=0)

    # Prescription control
    requires_prescription = db.Column(db.Boolean, default=False, nullable=False)

    # Media
    image_url = db.Column(db.String(500))

    # Status
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    inventory = db.relationship('Inventory', backref='medicine', uselist=False, cascade='all, delete-orphan')

    @property
    def selling_price(self):
        """Price after discount."""
        if self.discount_percent and self.discount_percent > 0:
            return round(float(self.price) * (1 - float(self.discount_percent) / 100), 2)
        return float(self.price)

    @property
    def in_stock(self):
        return self.inventory is not None and self.inventory.stock_quantity > 0

    @property
    def stock_quantity(self):
        return self.inventory.stock_quantity if self.inventory else 0

    def __repr__(self):
        return f'<Medicine {self.name}>'


class Inventory(db.Model):
    """Stock tracking for a medicine."""

    __tablename__ = 'inventory'

    id = db.Column(db.Integer, primary_key=True)
    medicine_id = db.Column(
        db.Integer,
        db.ForeignKey('medicines.id', ondelete='CASCADE'),
        unique=True,
        nullable=False,
    )
    stock_quantity = db.Column(db.Integer, default=0, nullable=False)
    reorder_level = db.Column(db.Integer, default=10)
    last_restocked = db.Column(db.DateTime, nullable=True)

    @property
    def needs_reorder(self):
        return self.stock_quantity <= self.reorder_level

    def __repr__(self):
        return f'<Inventory medicine={self.medicine_id} stock={self.stock_quantity}>'
