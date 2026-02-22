# app.py - Final (includes context processor to expose datetime to templates)
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
try:
    from flask_mail import Mail, Message
    MAIL_AVAILABLE = True
except ImportError:
    MAIL_AVAILABLE = False
    print("Warning: Flask-Mail not installed. Email features will be disabled.")
    # Create dummy classes to prevent errors
    class Mail:
        def __init__(self, app): pass
    class Message:
        def __init__(self, *args, **kwargs): pass
from flask_socketio import SocketIO, emit, join_room, leave_room
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from datetime import datetime, timedelta
import os, uuid
from werkzeug.utils import secure_filename

# -----------------------
# App & DB config
# -----------------------
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET', 'supersecret_demo_key')

# Database config - supports both SQLite and PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///telemed.db')
if app.config['SQLALCHEMY_DATABASE_URI'].startswith('postgres://'):
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Email config
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', '[email protected]')

# Cloudinary config
app.config['CLOUDINARY_CLOUD_NAME'] = os.environ.get('CLOUDINARY_CLOUD_NAME')
app.config['CLOUDINARY_API_KEY'] = os.environ.get('CLOUDINARY_API_KEY')
app.config['CLOUDINARY_API_SECRET'] = os.environ.get('CLOUDINARY_API_SECRET')

# Upload config
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Create upload folder if it doesn't exist
if not os.path.exists('uploads'):
    os.makedirs('uploads')

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
mail = Mail(app)
socketio = SocketIO(app, cors_allowed_origins="*")
serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

# -----------------------
# Models
# -----------------------
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'patient', 'doctor', or 'pharmacy'
    
    # Common fields for doctors and patients
    phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.String(300), nullable=True)
    age = db.Column(db.Integer, nullable=True)
    gender = db.Column(db.String(20), nullable=True)  # Male, Female, Other
    
    # Doctor-specific fields
    specialization = db.Column(db.String(120), nullable=True)
    license_number = db.Column(db.String(100), nullable=True)
    experience_years = db.Column(db.Integer, nullable=True)
    
    # Pharmacy-specific fields
    shop_name = db.Column(db.String(200), nullable=True)
    shop_address = db.Column(db.String(300), nullable=True)
    shop_phone = db.Column(db.String(20), nullable=True)
    
    # System fields
    email_verified = db.Column(db.Boolean, default=False)
    profile_image = db.Column(db.String(300), nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    datetime = db.Column(db.String(80), nullable=False)
    status = db.Column(db.String(30), default='Scheduled')
    notes = db.Column(db.Text, nullable=True)
    room = db.Column(db.String(250), nullable=True)

class Prescription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointment.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    text = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(300), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Medicine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pharmacy_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)
    category = db.Column(db.String(100), nullable=True)
    image_url = db.Column(db.String(300), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointment.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    pharmacy_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicine.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(30), default='Pending')  # Pending, Confirmed, Completed, Cancelled
    delivery_address = db.Column(db.Text, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    patient = db.relationship('User', foreign_keys=[patient_id])
    pharmacy = db.relationship('User', foreign_keys=[pharmacy_id])
    medicine = db.relationship('Medicine')

class Disease(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(100), nullable=True)  # e.g., Infectious, Chronic, Respiratory
    description = db.Column(db.Text, nullable=True)
    symptoms = db.Column(db.Text, nullable=False)  # Store as comma-separated or multiline
    remedies = db.Column(db.Text, nullable=False)
    prevention = db.Column(db.Text, nullable=True)
    youtube_link = db.Column(db.String(300), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# -----------------------
# Login manager
# -----------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# -----------------------
# Context processors
# -----------------------
# Expose python's datetime module to all templates (so {{ datetime.utcnow().year }} works)
@app.context_processor
def inject_datetime():
    return {'datetime': datetime, 'timedelta': timedelta}

# -----------------------
# Helpers
# -----------------------
def create_jitsi_room():
    rid = uuid.uuid4().hex[:12]
    return f"https://meet.jit.si/telemed-{rid}"

def generate_token(email):
    return serializer.dumps(email, salt='email-verification')

def verify_token(token, max_age=3600):
    try:
        email = serializer.loads(token, salt='email-verification', max_age=max_age)
        return email
    except (SignatureExpired, BadSignature):
        return None

def send_email(to, subject, body):
    if not MAIL_AVAILABLE:
        print(f"Email not configured (Flask-Mail not installed). Would send to {to}: {subject}")
        print(f"Email body: {body}")
        return False
    if not app.config['MAIL_USERNAME']:
        print(f"Email credentials not configured. Would send to {to}: {subject}")
        print(f"Email body: {body}")
        return False
    try:
        msg = Message(subject, recipients=[to])
        msg.body = body
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending email to {to}: {e}")
        print(f"Email subject was: {subject}")
        return False

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_prescription_image(file):
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Add timestamp to avoid filename collisions
        filename = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return filename
    return None

def save_profile_image(file):
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Add timestamp and prefix to avoid collisions
        filename = f"profile_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return filename
    return None

# -----------------------
# Routes
# -----------------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        fullname = request.form['fullname'].strip()
        email = request.form['email'].strip().lower()
        password = request.form['password']
        role = request.form['role']
        specialization = request.form.get('specialization') or None
        shop_name = request.form.get('shop_name') or None
        shop_address = request.form.get('shop_address') or None
        shop_phone = request.form.get('shop_phone') or None

        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return redirect(url_for('register'))

        u = User(fullname=fullname, email=email, role=role, specialization=specialization,
                 shop_name=shop_name, shop_address=shop_address, shop_phone=shop_phone)
        u.set_password(password)
        db.session.add(u)
        db.session.commit()
        flash('Registered successfully. Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password']
        u = User.query.filter_by(email=email).first()
        if u and u.check_password(password):
            login_user(u)
            flash('Logged in successfully', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid credentials', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out', 'info')
    return redirect(url_for('index'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        # Handle profile picture upload
        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file.filename != '':
                # Delete old profile picture if exists
                if current_user.profile_image:
                    old_file_path = os.path.join(app.config['UPLOAD_FOLDER'], current_user.profile_image)
                    if os.path.exists(old_file_path):
                        os.remove(old_file_path)
                
                # Save new profile picture
                filename = save_profile_image(file)
                if filename:
                    current_user.profile_image = filename
                    db.session.commit()
                    flash('Profile picture updated successfully!', 'success')
                else:
                    flash('Invalid file type. Please upload PNG, JPG, JPEG, or GIF.', 'danger')
        
        # Handle profile information update
        elif 'update_profile' in request.form:
            # Common fields
            current_user.phone = request.form.get('phone') or None
            current_user.address = request.form.get('address') or None
            current_user.age = int(request.form.get('age')) if request.form.get('age') else None
            current_user.gender = request.form.get('gender') or None
            
            # Doctor-specific fields
            if current_user.role == 'doctor':
                current_user.license_number = request.form.get('license_number') or None
                current_user.experience_years = int(request.form.get('experience_years')) if request.form.get('experience_years') else None
            
            db.session.commit()
            flash('Profile updated successfully!', 'success')
        
        return redirect(url_for('profile'))
    return render_template('profile.html')

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        user = User.query.filter_by(email=email).first()
        if user:
            token = generate_token(email)
            reset_url = url_for('reset_password', token=token, _external=True)
            body = f"""Hello {user.fullname},

Click the link below to reset your password:
{reset_url}

This link will expire in 1 hour.

If you didn't request this, please ignore this email.
"""
            send_email(email, 'Reset Your Password - Telemed', body)
            flash('Password reset link sent to your email', 'success')
        else:
            flash('If an account exists with this email, you will receive a password reset link', 'info')
        return redirect(url_for('login'))
    return render_template('forgot_password.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    email = verify_token(token, max_age=3600)
    if not email:
        flash('Invalid or expired reset link', 'danger')
        return redirect(url_for('forgot_password'))
    
    if request.method == 'POST':
        password = request.form['password']
        confirm = request.form['confirm_password']
        if password != confirm:
            flash('Passwords do not match', 'danger')
            return render_template('reset_password.html', token=token)
        
        user = User.query.filter_by(email=email).first()
        if user:
            user.set_password(password)
            db.session.commit()
            flash('Password reset successfully. Please login.', 'success')
            return redirect(url_for('login'))
        flash('User not found', 'danger')
        return redirect(url_for('forgot_password'))
    return render_template('reset_password.html', token=token)

@app.route('/verify-email/<token>')
def verify_email(token):
    email = verify_token(token, max_age=86400)  # 24 hours
    if not email:
        flash('Invalid or expired verification link', 'danger')
        return redirect(url_for('index'))
    
    user = User.query.filter_by(email=email).first()
    if user:
        user.email_verified = True
        db.session.commit()
        flash('Email verified successfully!', 'success')
        return redirect(url_for('login'))
    flash('User not found', 'danger')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'patient':
        return redirect(url_for('patient_dashboard'))
    elif current_user.role == 'pharmacy':
        return redirect(url_for('pharmacy_dashboard'))
    return redirect(url_for('doctor_dashboard'))

# -----------------------
# Patient views
# -----------------------
@app.route('/patient')
@login_required
def patient_dashboard():
    if current_user.role != 'patient':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    appts = Appointment.query.filter_by(patient_id=current_user.id).order_by(Appointment.id.desc()).all()
    doctors = User.query.filter_by(role='doctor').all()
    doctor_map = {d.id: d for d in doctors}
    return render_template('patient_dashboard.html', appts=appts, doctors=doctors, doctor_map=doctor_map)

@app.route('/book', methods=['GET','POST'])
@login_required
def book_appointment():
    if current_user.role != 'patient':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        try:
            doctor_id = int(request.form['doctor_id'])
        except ValueError:
            flash('Invalid doctor selection', 'danger')
            return redirect(url_for('book_appointment'))
        dt = request.form['datetime']
        notes = request.form.get('notes','')
        room = create_jitsi_room()
        a = Appointment(patient_id=current_user.id, doctor_id=doctor_id, datetime=dt, notes=notes, room=room)
        db.session.add(a)
        db.session.commit()
        flash('Appointment booked', 'success')
        return redirect(url_for('patient_dashboard'))
    doctors = User.query.filter_by(role='doctor').all()
    return render_template('book_appointment.html', doctors=doctors)

# -----------------------
# Doctor views
# -----------------------
@app.route('/doctor')
@login_required
def doctor_dashboard():
    if current_user.role != 'doctor':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    appts = Appointment.query.filter_by(doctor_id=current_user.id).order_by(Appointment.id.desc()).all()
    patient_ids = {a.patient_id for a in appts}
    patients = User.query.filter(User.id.in_(patient_ids)).all() if patient_ids else []
    patient_map = {p.id: p for p in patients}
    return render_template('doctor_dashboard.html', appts=appts, patient_map=patient_map)

@app.route('/consult/<int:appt_id>', methods=['GET','POST'])
@login_required
def consult(appt_id):
    appt = Appointment.query.get_or_404(appt_id)
    # access control
    if current_user.role == 'doctor' and appt.doctor_id != current_user.id:
        flash('Not allowed', 'danger')
        return redirect(url_for('dashboard'))
    if current_user.role == 'patient' and appt.patient_id != current_user.id:
        flash('Not allowed', 'danger')
        return redirect(url_for('dashboard'))

    if request.method == 'POST' and current_user.role == 'doctor':
        text = request.form.get('prescription', '').strip()
        image_file = request.files.get('prescription_image')
        
        # At least one should be provided
        if not text and not image_file:
            flash('Please provide prescription text or upload an image', 'danger')
            prescriptions = Prescription.query.filter_by(appointment_id=appt.id).order_by(Prescription.created_at.desc()).all()
            return render_template('consult.html', appt=appt, prescriptions=prescriptions)
        
        image_url = None
        if image_file and image_file.filename:
            image_url = save_prescription_image(image_file)
            if not image_url:
                flash('Invalid image file. Allowed formats: PNG, JPG, JPEG, GIF', 'danger')
                prescriptions = Prescription.query.filter_by(appointment_id=appt.id).order_by(Prescription.created_at.desc()).all()
                return render_template('consult.html', appt=appt, prescriptions=prescriptions)
        
        p = Prescription(appointment_id=appt.id, doctor_id=current_user.id, patient_id=appt.patient_id, 
                        text=text if text else None, image_url=image_url)
        appt.status = 'Completed'
        db.session.add(p)
        db.session.commit()
        flash('Prescription saved successfully', 'success')
        return redirect(url_for('doctor_dashboard'))

    prescriptions = Prescription.query.filter_by(appointment_id=appt.id).order_by(Prescription.created_at.desc()).all()
    return render_template('consult.html', appt=appt, prescriptions=prescriptions)

@app.route('/prescriptions/<int:patient_id>')
@login_required
def view_prescriptions(patient_id):
    # patients can view their own; doctors can view any patient's prescriptions
    if current_user.role == 'patient' and current_user.id != patient_id:
        flash('Not allowed', 'danger')
        return redirect(url_for('dashboard'))
    pres = Prescription.query.filter_by(patient_id=patient_id).order_by(Prescription.created_at.desc()).all()
    patient = User.query.get(patient_id)
    return render_template('prescriptions.html', pres=pres, patient=patient)

# -----------------------
# Pharmacy views
# -----------------------
@app.route('/pharmacy')
@login_required
def pharmacy_dashboard():
    if current_user.role != 'pharmacy':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    medicines = Medicine.query.filter_by(pharmacy_id=current_user.id).order_by(Medicine.created_at.desc()).all()
    return render_template('pharmacy_dashboard.html', medicines=medicines)

@app.route('/pharmacy/add-medicine', methods=['GET','POST'])
@login_required
def add_medicine():
    if current_user.role != 'pharmacy':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        name = request.form['name'].strip()
        description = request.form.get('description', '').strip()
        price = float(request.form['price'])
        stock = int(request.form.get('stock', 0))
        category = request.form.get('category', '').strip()
        
        med = Medicine(pharmacy_id=current_user.id, name=name, description=description, 
                       price=price, stock=stock, category=category)
        db.session.add(med)
        db.session.commit()
        flash('Medicine added successfully', 'success')
        return redirect(url_for('pharmacy_dashboard'))
    return render_template('add_medicine.html')

@app.route('/pharmacy/edit-medicine/<int:med_id>', methods=['GET','POST'])
@login_required
def edit_medicine(med_id):
    if current_user.role != 'pharmacy':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    med = Medicine.query.get_or_404(med_id)
    if med.pharmacy_id != current_user.id:
        flash('Not allowed', 'danger')
        return redirect(url_for('pharmacy_dashboard'))
    
    if request.method == 'POST':
        med.name = request.form['name'].strip()
        med.description = request.form.get('description', '').strip()
        med.price = float(request.form['price'])
        med.stock = int(request.form.get('stock', 0))
        med.category = request.form.get('category', '').strip()
        db.session.commit()
        flash('Medicine updated successfully', 'success')
        return redirect(url_for('pharmacy_dashboard'))
    return render_template('edit_medicine.html', med=med)

@app.route('/pharmacy/delete-medicine/<int:med_id>', methods=['POST'])
@login_required
def delete_medicine(med_id):
    if current_user.role != 'pharmacy':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    med = Medicine.query.get_or_404(med_id)
    if med.pharmacy_id != current_user.id:
        flash('Not allowed', 'danger')
        return redirect(url_for('pharmacy_dashboard'))
    
    db.session.delete(med)
    db.session.commit()
    flash('Medicine deleted successfully', 'success')
    return redirect(url_for('pharmacy_dashboard'))

# -----------------------
# Medicine Search (for all users)
# -----------------------
@app.route('/search-medicine', methods=['GET'])
def search_medicine():
    query = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()
    
    medicines = []
    pharmacies_map = {}
    
    if query or category:
        filters = []
        if query:
            filters.append(Medicine.name.ilike(f'%{query}%'))
        if category:
            filters.append(Medicine.category.ilike(f'%{category}%'))
        
        medicines = Medicine.query.filter(*filters).order_by(Medicine.name).all()
        pharmacy_ids = {m.pharmacy_id for m in medicines}
        pharmacies = User.query.filter(User.id.in_(pharmacy_ids)).all() if pharmacy_ids else []
        pharmacies_map = {p.id: p for p in pharmacies}
    
    return render_template('search_medicine.html', medicines=medicines, pharmacies_map=pharmacies_map, 
                         query=query, category=category)

# -----------------------
# Medicine Ordering System
# -----------------------
@app.route('/order-medicine/<int:med_id>', methods=['GET', 'POST'])
@login_required
def order_medicine(med_id):
    if current_user.role != 'patient':
        flash('Only patients can order medicines', 'danger')
        return redirect(url_for('dashboard'))
    
    medicine = Medicine.query.get_or_404(med_id)
    pharmacy = User.query.get(medicine.pharmacy_id)
    
    if request.method == 'POST':
        quantity = int(request.form['quantity'])
        delivery_address = request.form['delivery_address'].strip()
        phone = request.form['phone'].strip()
        
        if quantity <= 0:
            flash('Quantity must be greater than 0', 'danger')
            return render_template('order_medicine.html', medicine=medicine, pharmacy=pharmacy)
        
        if quantity > medicine.stock:
            flash(f'Only {medicine.stock} units available in stock', 'danger')
            return render_template('order_medicine.html', medicine=medicine, pharmacy=pharmacy)
        
        total_price = medicine.price * quantity
        
        order = Order(
            patient_id=current_user.id,
            pharmacy_id=medicine.pharmacy_id,
            medicine_id=medicine.id,
            quantity=quantity,
            total_price=total_price,
            delivery_address=delivery_address,
            phone=phone
        )
        
        # Update medicine stock
        medicine.stock -= quantity
        
        db.session.add(order)
        db.session.commit()
        
        flash('Order placed successfully!', 'success')
        return redirect(url_for('my_orders'))
    
    return render_template('order_medicine.html', medicine=medicine, pharmacy=pharmacy)

@app.route('/my-orders')
@login_required
def my_orders():
    if current_user.role != 'patient':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    orders = Order.query.filter_by(patient_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('my_orders.html', orders=orders)

@app.route('/pharmacy/orders')
@login_required
def pharmacy_orders():
    if current_user.role != 'pharmacy':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    orders = Order.query.filter_by(pharmacy_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('pharmacy_orders.html', orders=orders)

@app.route('/pharmacy/update-order/<int:order_id>', methods=['POST'])
@login_required
def update_order_status(order_id):
    if current_user.role != 'pharmacy':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    order = Order.query.get_or_404(order_id)
    if order.pharmacy_id != current_user.id:
        flash('Not allowed', 'danger')
        return redirect(url_for('pharmacy_orders'))
    
    new_status = request.form.get('status')
    if new_status in ['Pending', 'Confirmed', 'Completed', 'Cancelled']:
        order.status = new_status
        db.session.commit()
        flash(f'Order status updated to {new_status}', 'success')
    
    return redirect(url_for('pharmacy_orders'))

# -----------------------
# File serving
# -----------------------
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# -----------------------
# Health Library / Disease Information
# -----------------------
@app.route('/health-library')
def health_library():
    search = request.args.get('search', '').strip()
    category = request.args.get('category', '').strip()
    
    query = Disease.query
    if search:
        query = query.filter(Disease.name.ilike(f'%{search}%'))
    if category:
        query = query.filter(Disease.category == category)
    
    diseases = query.order_by(Disease.name).all()
    categories = db.session.query(Disease.category).distinct().filter(Disease.category.isnot(None)).all()
    categories = [c[0] for c in categories]
    
    return render_template('health_library.html', diseases=diseases, categories=categories, search=search, selected_category=category)

@app.route('/health-library/<int:disease_id>')
def disease_detail(disease_id):
    disease = Disease.query.get_or_404(disease_id)
    return render_template('disease_detail.html', disease=disease)

@app.route('/doctor/manage-diseases')
@login_required
def manage_diseases():
    if current_user.role != 'doctor':
        flash('Access denied. Only doctors can manage health information.', 'danger')
        return redirect(url_for('dashboard'))
    
    diseases = Disease.query.order_by(Disease.created_at.desc()).all()
    return render_template('manage_diseases.html', diseases=diseases)

@app.route('/doctor/add-disease', methods=['GET', 'POST'])
@login_required
def add_disease():
    if current_user.role != 'doctor':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        name = request.form['name'].strip()
        category = request.form.get('category', '').strip()
        description = request.form.get('description', '').strip()
        symptoms = request.form['symptoms'].strip()
        remedies = request.form['remedies'].strip()
        prevention = request.form.get('prevention', '').strip()
        youtube_link = request.form.get('youtube_link', '').strip()
        
        disease = Disease(
            name=name,
            category=category if category else None,
            description=description if description else None,
            symptoms=symptoms,
            remedies=remedies,
            prevention=prevention if prevention else None,
            youtube_link=youtube_link if youtube_link else None
        )
        
        db.session.add(disease)
        db.session.commit()
        flash('Disease information added successfully!', 'success')
        return redirect(url_for('manage_diseases'))
    
    return render_template('add_disease.html')

@app.route('/doctor/edit-disease/<int:disease_id>', methods=['GET', 'POST'])
@login_required
def edit_disease(disease_id):
    if current_user.role != 'doctor':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    disease = Disease.query.get_or_404(disease_id)
    
    if request.method == 'POST':
        disease.name = request.form['name'].strip()
        disease.category = request.form.get('category', '').strip() or None
        disease.description = request.form.get('description', '').strip() or None
        disease.symptoms = request.form['symptoms'].strip()
        disease.remedies = request.form['remedies'].strip()
        disease.prevention = request.form.get('prevention', '').strip() or None
        disease.youtube_link = request.form.get('youtube_link', '').strip() or None
        
        db.session.commit()
        flash('Disease information updated successfully!', 'success')
        return redirect(url_for('manage_diseases'))
    
    return render_template('edit_disease.html', disease=disease)

@app.route('/doctor/delete-disease/<int:disease_id>', methods=['POST'])
@login_required
def delete_disease(disease_id):
    if current_user.role != 'doctor':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    disease = Disease.query.get_or_404(disease_id)
    db.session.delete(disease)
    db.session.commit()
    flash('Disease information deleted successfully!', 'success')
    return redirect(url_for('manage_diseases'))

# -----------------------
# Chat functionality
# -----------------------
@app.route('/chat/<int:appt_id>')
@login_required
def chat(appt_id):
    appt = Appointment.query.get_or_404(appt_id)
    # access control
    if current_user.role == 'doctor' and appt.doctor_id != current_user.id:
        flash('Not allowed', 'danger')
        return redirect(url_for('dashboard'))
    if current_user.role == 'patient' and appt.patient_id != current_user.id:
        flash('Not allowed', 'danger')
        return redirect(url_for('dashboard'))
    
    messages = ChatMessage.query.filter_by(appointment_id=appt_id).order_by(ChatMessage.created_at).all()
    doctor = User.query.get(appt.doctor_id)
    patient = User.query.get(appt.patient_id)
    return render_template('chat.html', appt=appt, messages=messages, doctor=doctor, patient=patient)

# WebSocket events
@socketio.on('join')
def on_join(data):
    room = str(data['appointment_id'])
    join_room(room)
    emit('status', {'msg': f'{current_user.fullname} has joined the chat.'}, room=room)

@socketio.on('leave')
def on_leave(data):
    room = str(data['appointment_id'])
    leave_room(room)
    emit('status', {'msg': f'{current_user.fullname} has left the chat.'}, room=room)

@socketio.on('send_message')
def handle_message(data):
    appointment_id = data['appointment_id']
    message_text = data['message']
    
    # Save to database
    msg = ChatMessage(appointment_id=appointment_id, sender_id=current_user.id, message=message_text)
    db.session.add(msg)
    db.session.commit()
    
    # Broadcast to room
    room = str(appointment_id)
    emit('receive_message', {
        'sender_id': current_user.id,
        'sender_name': current_user.fullname,
        'message': message_text,
        'timestamp': msg.created_at.strftime('%H:%M')
    }, room=room)

# -----------------------
# Optional one-time init route (kept for convenience)
# -----------------------
@app.route('/initdb')
def initdb():
    # only create sample users if db has been created properly
    with app.app_context():
        db.create_all()

        def ensure_user(fullname, email, password, role, specialization=None):
            if not User.query.filter_by(email=email).first():
                u = User(fullname=fullname, email=email, role=role, specialization=specialization)
                u.set_password(password)
                db.session.add(u)
                return True
            return False

        created = False
        created |= ensure_user('Dr. A Sharma', 'dr.sharma@example.com', 'doc123', 'doctor', 'General Physician')
        created |= ensure_user('Dr. R Gupta', 'dr.gupta@example.com', 'doc123', 'doctor', 'Dermatology')
        created |= ensure_user('Sita Verma', 'sita@example.com', 'patient123', 'patient')
        created |= ensure_user('Ravi Kumar', 'ravi@example.com', 'patient123', 'patient')

        if created:
            db.session.commit()
            return 'DB initialized and sample users created.'
        return 'DB already initialized.'

# -----------------------
# Run (safe startup)
# -----------------------
if __name__ == '__main__':
    # ensure tables exist and create sample users (if missing)
    with app.app_context():
        db.create_all()

        def ensure_user(fullname, email, password, role, specialization=None):
            if not User.query.filter_by(email=email).first():
                u = User(fullname=fullname, email=email, role=role, specialization=specialization)
                u.set_password(password)
                db.session.add(u)
                return True
            return False

        created = False
        created |= ensure_user('Dr. A Sharma', 'dr.sharma@example.com', 'doc123', 'doctor', 'General Physician')
        created |= ensure_user('Dr. R Gupta', 'dr.gupta@example.com', 'doc123', 'doctor', 'Dermatology')
        created |= ensure_user('Sita Verma', 'sita@example.com', 'patient123', 'patient')
        created |= ensure_user('Ravi Kumar', 'ravi@example.com', 'patient123', 'patient')

        if created:
            db.session.commit()
            print("Sample users created (if they were missing).")
        
        # Add sample disease data if none exists
        if Disease.query.count() == 0:
            sample_diseases = [
                Disease(
                    name="Common Cold",
                    category="Infectious",
                    description="A viral infection of the upper respiratory tract affecting nose and throat.",
                    symptoms="Runny nose\nSneez ing\nSore throat\nCough\nMild headache\nFever (sometimes)\nBody aches",
                    remedies="Rest and plenty of sleep\nDrink warm fluids (tea, soup)\nGargle with salt water\nUse over-the-counter cold medicines\nStay hydrated\nUse humidifier",
                    prevention="Wash hands frequently\nAvoid close contact with sick people\nDon't touch face\nBoost immune system with vitamins\nGet adequate sleep",
                    youtube_link="https://www.youtube.com/watch?v=LxfCXYT8CBE"
                ),
                Disease(
                    name="Diabetes Type 2",
                    category="Metabolic",
                    description="A chronic condition affecting how your body processes blood sugar (glucose).",
                    symptoms="Increased thirst\nFrequent urination\nUnexplained weight loss\nFatigue\nBlurred vision\nSlow-healing sores\nFrequent infections",
                    remedies="Regular blood sugar monitoring\nHealthy diet (low sugar, high fiber)\nRegular exercise\nMedications as prescribed\nWeight management\nRegular check-ups with doctor",
                    prevention="Maintain healthy weight\nExercise regularly (30 min daily)\nEat balanced diet\nAvoid sugary drinks\nLimit processed foods\nRegular health screenings",
                    youtube_link="https://www.youtube.com/watch?v=wZAjVQWbMlE"
                ),
                Disease(
                    name="Hypertension (High Blood Pressure)",
                    category="Cardiovascular",
                    description="A condition where blood pressure against artery walls is consistently too high.",
                    symptoms="Headaches\nShortness of breath\nNosebleeds\nFlushing\nDizziness\nChest pain\n(Often no symptoms)",
                    remedies="Take prescribed medications regularly\nReduce salt intake\nRegular exercise\nLimit alcohol\nStress management\nQuit smoking\nMaintain healthy weight",
                    prevention="Healthy diet (DASH diet)\nRegular physical activity\nMaintain healthy weight\nLimit sodium\nLimit alcohol\nManage stress\nRegular blood pressure checks",
                    youtube_link="https://www.youtube.com/watch?v=zHXEVdNAYHI"
                ),
                Disease(
                    name="Asthma",
                    category="Respiratory",
                    description="A condition in which airways narrow and swell, producing extra mucus.",
                    symptoms="Shortness of breath\nChest tightness\nWheezing\nCoughing (especially at night)\nDifficulty sleeping due to breathing\nWorsens with cold or exercise",
                    remedies="Use prescribed inhalers\nAvoid triggers\nTake controller medications daily\nKeep rescue inhaler handy\nUse peak flow meter\nFollow asthma action plan",
                    prevention="Identify and avoid triggers\nGet vaccinated (flu, pneumonia)\nMonitor breathing\nTake medications as prescribed\nMaintain healthy weight\nAvoid smoke and air pollution",
                    youtube_link="https://www.youtube.com/watch?v=B_ozVdltoOA"
                ),
                Disease(
                    name="Influenza (Flu)",
                    category="Infectious",
                    description="A contagious respiratory illness caused by influenza viruses.",
                    symptoms="Sudden fever\nCough\nSore throat\nBody aches\nFatigue\nHeadache\nChills\nNasal congestion",
                    remedies="Rest and fluids\nAntiviral medications (if prescribed early)\nPain relievers for fever\nStay home to avoid spreading\nWarm fluids and soup\nHumidifier use",
                    prevention="Annual flu vaccine\nWash hands frequently\nAvoid touching face\nStay away from sick people\nBoost immune system\nClean surfaces regularly",
                    youtube_link="https://www.youtube.com/watch?v=Xe7I6aFAt-w"
                )
            ]
            
            for disease in sample_diseases:
                db.session.add(disease)
            
            db.session.commit()
            print("Sample disease data added to health library.")

    # run the app with SocketIO
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
