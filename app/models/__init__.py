"""Model package — import all models so Alembic and the app can discover them."""
from .user import User, PatientProfile, DoctorProfile, UserRole, Gender, BloodGroup
from .doctor import DoctorVerification, Specialty, Availability, VerificationStatus, DayOfWeek
from .appointment import Appointment, AppointmentStatus, AppointmentType
from .consultation import Consultation, ConsultationMessage, ConsultationStatus, MessageType
from .prescription import Prescription, PrescriptionItem
from .medical_record import MedicalRecord, RecordType
from .pharmacy import Medicine, MedicineCategory, Inventory, DosageForm
from .order import Cart, CartItem, Order, OrderItem, OrderStatus
from .payment import Payment, Refund, PaymentStatus, PaymentType, PaymentMethod
from .notification import Notification, NotificationType
from .review import Review
from .support import SupportTicket, TicketStatus, TicketPriority
from .address import Address
from .audit import AuditLog

__all__ = [
    'User', 'PatientProfile', 'DoctorProfile', 'UserRole', 'Gender', 'BloodGroup',
    'DoctorVerification', 'Specialty', 'Availability', 'VerificationStatus', 'DayOfWeek',
    'Appointment', 'AppointmentStatus', 'AppointmentType',
    'Consultation', 'ConsultationMessage', 'ConsultationStatus', 'MessageType',
    'Prescription', 'PrescriptionItem',
    'MedicalRecord', 'RecordType',
    'Medicine', 'MedicineCategory', 'Inventory', 'DosageForm',
    'Cart', 'CartItem', 'Order', 'OrderItem', 'OrderStatus',
    'Payment', 'Refund', 'PaymentStatus', 'PaymentType', 'PaymentMethod',
    'Notification', 'NotificationType',
    'Review',
    'SupportTicket', 'TicketStatus', 'TicketPriority',
    'Address',
    'AuditLog',
]
