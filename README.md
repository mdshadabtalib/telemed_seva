<div align="center">

<img src="app/static/images/logo.svg" alt="TeleMed Seva" width="280" />

# TeleMed Seva

**A production-oriented telemedicine platform built with Flask**

Connect patients with verified doctors for online video consultations,
digital prescriptions, and integrated pharmacy services.

[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://python.org)
[![Flask 3.1](https://img.shields.io/badge/Flask-3.1-000000?logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00)](https://sqlalchemy.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Setup on a New Device](#setup-on-a-new-device)
  - [Prerequisites](#prerequisites)
  - [1 — Clone the repository](#1--clone-the-repository)
  - [2 — Create a virtual environment](#2--create-a-virtual-environment)
  - [3 — Install dependencies](#3--install-dependencies)
  - [4 — Configure environment variables](#4--configure-environment-variables)
  - [5 — Initialize the database](#5--initialize-the-database)
  - [6 — Seed lookup data](#6--seed-lookup-data)
  - [7 — Create an admin account](#7--create-an-admin-account)
  - [8 — Run the development server](#8--run-the-development-server)
- [Docker Setup](#docker-setup)
- [User Roles & Workflows](#user-roles--workflows)
- [URL Reference](#url-reference)
- [REST API](#rest-api)
- [CLI Commands](#cli-commands)
- [Running Tests](#running-tests)
- [Environment Variables Reference](#environment-variables-reference)
- [Production Deployment](#production-deployment)
- [Security Notes](#security-notes)
- [Troubleshooting](#troubleshooting)

---

## Overview

TeleMed Seva is built as a serious healthcare platform, not a simple prototype.
Every module is connected end-to-end — appointment booking flows into payment,
payment confirms the consultation room, the doctor completes the consultation and
writes a prescription, and that prescription can be used directly in the pharmacy.

**What works right now:**

- Patients book slots with verified doctors, pay online, then join a live Jitsi Meet video call
- Doctors write digital prescriptions inside the consultation room
- Patients order prescribed medicines from the integrated pharmacy
- Admins approve doctor credentials, manage refunds, and monitor the entire platform
- Email notifications are sent at every key step (configurable via SMTP)

---

## Features

| Area | What is implemented |
|---|---|
| **Auth** | Email + password registration, email verification, forgot/reset password, rate-limited login, role-based access control |
| **Doctors** | Registration, credential upload, admin verification, specialty assignment, availability scheduling, profile with bio and languages |
| **Appointments** | Slot generation, 10-minute payment lock, PENDING → CONFIRMED → COMPLETED state machine, cancellation |
| **Video Consultation** | Jitsi Meet WebRTC room per appointment, in-room text chat with file sharing, polling-based message refresh |
| **Prescriptions** | Verified doctors write multi-medicine prescriptions post-consultation, patients download as PDF |
| **Pharmacy** | Medicine catalog with categories, shopping cart, prescription upload for restricted medicines, order tracking |
| **Payments** | Mock payment gateway (Razorpay/Stripe integration points ready), payment history, refund requests |
| **Reviews** | One star rating + text review per completed appointment, aggregate rating on doctor profiles |
| **Notifications** | In-app notification bell with unread count, mark-read, email notifications via Flask-Mail |
| **Support** | Patient support tickets, admin helpdesk with ticket resolution |
| **Admin** | Doctor verifications, user management, order fulfilment, refund approval, specialty and category management, audit logs |
| **REST API** | Doctor search with filters, specialties list, appointment slots, full cart management |
| **Security** | CSRF on all forms, CSP + Permissions-Policy headers, rate limiting, secure file uploads, audit trail |
| **Infrastructure** | Docker + Docker Compose, Gunicorn, Flask-Migrate, health check endpoint |

---

## Tech Stack

### Backend
| Package | Version | Purpose |
|---|---|---|
| Flask | 3.1.1 | Web framework |
| SQLAlchemy | 2.0.40 | ORM |
| Flask-SQLAlchemy | 3.1.1 | SQLAlchemy integration |
| Flask-Migrate | 4.1.0 | Database migrations (Alembic) |
| Flask-Login | 0.6.3 | Session management |
| Flask-WTF | 1.2.2 | Forms + CSRF protection |
| Flask-Limiter | 3.12 | Rate limiting |
| Flask-Mail | 0.10.0 | Email sending |
| psycopg2-binary | 2.9.10 | PostgreSQL driver |
| python-dotenv | 1.1.0 | `.env` file loading |
| bleach | 6.2.0 | HTML sanitisation |
| Pillow | 11.2.1 | Image processing |
| gunicorn | 23.0.0 | Production WSGI server |
| redis | 5.3.0 | Rate-limit storage |

### Frontend
| Technology | Purpose |
|---|---|
| Jinja2 | Server-side templates |
| Custom CSS (CSS variables) | Design system |
| Font Awesome 6.5.1 | Icons |
| Vanilla JavaScript | Interactivity (no framework) |
| Jitsi Meet External API | WebRTC video calls |

### Database
- **Development:** SQLite (no setup required, file `telemed_seva.db`)
- **Production:** PostgreSQL 16

---

## Project Structure

```
telemed_seva/
│
├── app/
│   ├── __init__.py                  # Application factory
│   ├── config.py                    # DevelopmentConfig, TestingConfig, ProductionConfig
│   ├── extensions.py                # db, migrate, login_manager, csrf, limiter, mail
│   │
│   ├── models/
│   │   ├── __init__.py              # Exports every model for Alembic discovery
│   │   ├── user.py                  # User, PatientProfile, DoctorProfile
│   │   ├── doctor.py                # DoctorVerification, Specialty, Availability
│   │   ├── appointment.py           # Appointment (state machine)
│   │   ├── consultation.py          # Consultation, ConsultationMessage
│   │   ├── prescription.py          # Prescription, PrescriptionItem
│   │   ├── pharmacy.py              # Medicine, MedicineCategory, Inventory
│   │   ├── order.py                 # Cart, CartItem, Order, OrderItem
│   │   ├── payment.py               # Payment, Refund
│   │   ├── notification.py          # Notification, NotificationType
│   │   ├── review.py                # Review
│   │   ├── support.py               # SupportTicket
│   │   ├── address.py               # Address
│   │   ├── medical_record.py        # MedicalRecord
│   │   └── audit.py                 # AuditLog
│   │
│   ├── auth/                        # /login  /register  /verify-email  /reset-password
│   ├── patient/                     # /patient/*  — dashboard, profile, reviews, support
│   ├── doctor/                      # /doctor/*  — dashboard, profile, availability, earnings
│   ├── appointments/                # /appointments/*  — search, book, detail, cancel
│   ├── consultation/                # /consultation/*  — room, chat, complete
│   ├── prescriptions/               # /prescriptions/*  — create, view, list
│   ├── pharmacy/                    # /pharmacy/*  — catalog, cart, checkout, orders
│   ├── payments/                    # /payments/*  — pay, verify, history
│   ├── admin/                       # /admin/*  — dashboard, verifications, refunds, …
│   ├── notifications/               # /notifications/*  — list, mark-read
│   │
│   ├── api/                         # /api/*  — REST endpoints
│   │   ├── doctors.py               # GET /api/doctors
│   │   ├── appointments.py          # GET /api/appointments/slots/<doctor_id>
│   │   └── cart.py                  # CRUD /api/cart
│   │
│   ├── services/
│   │   ├── appointment_service.py   # Slot generation, locking, confirmation
│   │   ├── notification_service.py  # notify(), notify_appointment_booked(), …
│   │   └── payment_service.py       # Mock gateway, refund processing
│   │
│   ├── utils/
│   │   ├── decorators.py            # @admin_required, @verified_doctor_required, …
│   │   ├── email.py                 # send_verification_email(), send_password_reset_email()
│   │   ├── forms.py                 # WTForms: PatientProfileForm, DoctorProfileForm, …
│   │   ├── helpers.py               # paginate_query(), save_upload(), slugify()
│   │   ├── security.py              # add_security_headers(), log_audit()
│   │   ├── seed.py                  # seed_database(), create_admin_user()
│   │   ├── tokens.py                # itsdangerous signed tokens for email/reset
│   │   └── validators.py            # Custom WTForms validators
│   │
│   ├── templates/
│   │   ├── base.html                # Layout: navbar (with SVG logo), flash messages, footer
│   │   ├── home.html                # Landing / redirect
│   │   ├── auth/                    # login, register, forgot_password, reset_password
│   │   ├── patient/                 # dashboard, profile, reviews, support
│   │   ├── doctor/                  # dashboard, profile, availability, earnings
│   │   ├── appointments/            # search, list, detail, book
│   │   ├── consultation/            # room (Jitsi + chat)
│   │   ├── prescriptions/           # create, detail, list
│   │   ├── pharmacy/                # catalog, cart, checkout, order detail
│   │   ├── admin/                   # dashboard, verifications, users, orders,
│   │   │                            #   refunds, specialties, categories, tickets
│   │   ├── notifications/           # list
│   │   └── errors/                  # 400, 401, 403, 404, 429, 500
│   │
│   └── static/
│       ├── css/style.css            # Full design system (CSS variables)
│       ├── js/app.js                # Modal helpers, notification polling, cart JS
│       └── images/
│           ├── logo.svg             # Full horizontal brand logo
│           ├── logo-icon.svg        # Standalone icon (60×60)
│           ├── favicon.svg          # Browser tab icon (32×32)
│           └── illustrations/       # doctor-consultation.svg, appointment.svg, pharmacy.svg
│
├── migrations/                      # Flask-Migrate / Alembic migration files
├── tests/
│   ├── conftest.py                  # App fixture, test users, sample medicine
│   ├── test_auth.py                 # Registration, login, logout, RBAC
│   ├── test_appointments.py         # Slot generation, booking, double-booking
│   ├── test_pharmacy.py             # Cart management, inventory decrement
│   └── test_api.py                  # Doctor search API, specialties API
│
├── uploads/                         # User-uploaded files (gitignored)
│   ├── avatars/
│   ├── documents/
│   ├── prescriptions/
│   ├── medicines/
│   └── reports/
│
├── logs/                            # Application logs (gitignored)
├── .env.example                     # Template — copy to .env
├── .gitignore
├── .dockerignore
├── Dockerfile                       # Multi-stage production image (Python 3.12-slim)
├── docker-compose.yml               # PostgreSQL 16 + Redis 7 + web
├── gunicorn.conf.py                 # Workers, threads, logging, hooks
├── requirements.txt
├── run.py                           # Development entry point
└── README.md
```

---

## Setup on a New Device

### Prerequisites

Install these before you start:

| Tool | Minimum version | Download |
|---|---|---|
| Python | 3.12 | https://python.org/downloads |
| Git | any | https://git-scm.com |
| pip | bundled with Python | — |

> **SQLite** is the default database for development and is included with Python —
> no separate database installation is needed.
>
> Redis is used only for rate-limiting in development and falls back to an
> in-memory store automatically, so Redis is optional locally.

---

### 1 — Clone the repository

```bash
git clone https://github.com/yourusername/telemed_seva.git
cd telemed_seva
```

---

### 2 — Create a virtual environment

**Windows (PowerShell)**
```powershell
python -m venv venv
venv\Scripts\activate
```

**macOS / Linux**
```bash
python3 -m venv venv
source venv/bin/activate
```

You should see `(venv)` at the start of your terminal prompt.

---

### 3 — Install dependencies

```bash
pip install -r requirements.txt
```

This installs Flask, SQLAlchemy, Flask-Login, Flask-WTF, and all other packages
listed in `requirements.txt`. It takes about 30–60 seconds.

---

### 4 — Configure environment variables

```bash
# Copy the example file
cp .env.example .env
```

Open `.env` in any text editor. The minimum required changes for local
development are:

```env
# Generate a proper secret key — run this once and paste the output
# python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=paste-your-generated-key-here

# SQLite works out of the box — leave this line as-is
DATABASE_URL=sqlite:///telemed_seva.db

# Email is optional for development.
# If left blank, verification tokens are printed to the terminal instead.
MAIL_USERNAME=
MAIL_PASSWORD=
```

> **Generating a secret key**
>
> Run this once in your terminal and copy the output into `.env`:
> ```bash
> python -c "import secrets; print(secrets.token_hex(32))"
> ```

---

### 5 — Initialize the database

```bash
# Apply all migrations to create the schema
python -m flask db upgrade
```

Expected output:
```
INFO  [alembic.runtime.migration] Running upgrade  -> d6200e909466, initial schema
```

This creates `telemed_seva.db` in the project root with all 27 tables.

---

### 6 — Seed lookup data

```bash
python -m flask seed-db
```

This populates:
- **16 medical specialties** (General Medicine, Cardiology, Dermatology, …)
- **14 medicine categories** (Pain Relief, Antibiotics, Vitamins, …)

You only need to run this once.

---

### 7 — Create an admin account

```bash
python -m flask create-admin
```

You will be prompted for an email and password. This creates a verified admin
user that can immediately log in.

Alternatively, create one non-interactively:

```bash
python -c "
from app import create_app
from app.extensions import db
from app.models.user import User, UserRole

app = create_app()
with app.app_context():
    u = User(email='admin@example.com', role=UserRole.ADMIN,
             is_active=True, email_verified=True)
    u.set_password('Admin@1234')
    db.session.add(u)
    db.session.commit()
    print('Admin created.')
"
```

---

### 8 — Run the development server

```bash
python run.py
```

Expected output:
```
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
 * Restarting with watchdog (windowsapi)
 * Debugger is active!
 * Debugger PIN: XXX-XXX-XXX
```

Open **http://127.0.0.1:5000** in your browser.

The server hot-reloads on every file save — no restart needed during development.

---

### Quick-start checklist

```
[ ] git clone + cd into project
[ ] python -m venv venv  &&  activate it
[ ] pip install -r requirements.txt
[ ] cp .env.example .env  &&  set SECRET_KEY
[ ] python -m flask db upgrade
[ ] python -m flask seed-db
[ ] python -m flask create-admin
[ ] python run.py
[ ] Open http://127.0.0.1:5000
```

---

## Docker Setup

Docker sets up PostgreSQL, Redis, and the app in isolated containers with a
single command.

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop) (includes Docker Compose)

### Steps

**1. Configure `.env`**

```bash
cp .env.example .env
```

Set at minimum:
```env
SECRET_KEY=your-generated-secret-key
POSTGRES_USER=telemed
POSTGRES_PASSWORD=changeme
POSTGRES_DB=telemed_seva
FLASK_ENV=development
```

**2. Build and start all services**

```bash
docker compose up -d
```

This starts:
- `db` — PostgreSQL 16 on port 5432
- `redis` — Redis 7 on port 6379
- `web` — Flask app on port 8000

**3. Run migrations and seed**

```bash
docker compose exec web python -m flask db upgrade
docker compose exec web python -m flask seed-db
docker compose exec web python -m flask create-admin
```

**4. Open the app**

Visit **http://localhost:8000**

**Useful Docker commands**

```bash
# View live logs
docker compose logs -f web

# Open a shell inside the container
docker compose exec web bash

# Stop all services
docker compose down

# Stop and delete volumes (full reset)
docker compose down -v
```

---

## User Roles & Workflows

### Patient

1. Register at `/register` (select **Patient**)
2. Verify email (check terminal if SMTP not configured — token is printed)
3. Search for a doctor at `/appointments/search`
4. Choose a date and time slot, confirm booking
5. Pay on the payment page (mock payment — click Pay to confirm)
6. On appointment day, open the appointment detail and click **Join Consultation**
7. Participate in the Jitsi Meet video call
8. After the call, the doctor issues a prescription — view it at `/prescriptions/my`
9. Add prescribed medicines to cart and order from `/pharmacy/`
10. Leave a review at `/patient/appointments/<id>/review`

### Doctor

1. Register at `/register` (select **Doctor**)
2. Go to `/doctor/verification` and upload medical license and credentials
3. Wait for admin approval (admin visits `/admin/verifications`)
4. Once verified, set availability at `/doctor/availability`
5. View upcoming appointments at `/appointments/my`
6. On appointment time, click **Start Consultation** — this opens the Jitsi room
7. After the call, fill in diagnosis and click **Complete Consultation**
8. Write the prescription on the prescription creation page
9. Check earnings at `/doctor/earnings`

### Admin

1. Log in with the admin account created via `flask create-admin`
2. Visit `/admin/` for the full dashboard
3. Approve or reject doctor credentials at `/admin/verifications`
4. Manage users at `/admin/users` (activate / deactivate accounts)
5. Process refund requests at `/admin/refunds`
6. Manage pharmacy orders at `/admin/orders`
7. Add/edit specialties at `/admin/specialties`
8. Add/edit medicine categories at `/admin/medicine-categories`
9. Resolve support tickets at `/admin/tickets`
10. View the full audit log at `/admin/audit-logs`

---

## URL Reference

### Public (no login required)

| Method | URL | Description |
|---|---|---|
| GET | `/` | Home — redirects to dashboard if logged in |
| GET/POST | `/login` | Login form |
| GET/POST | `/register` | Registration form |
| GET/POST | `/forgot-password` | Request password reset email |
| GET/POST | `/reset-password/<token>` | Set new password |
| GET | `/verify-email/<token>` | Confirm email address |
| GET | `/health` | Health check (`{"status":"ok","db":"ok"}`) |
| GET | `/appointments/search` | Doctor search (browsable without login) |
| GET | `/pharmacy/` | Medicine catalog |

### Patient (`/patient/*`)

| URL | Description |
|---|---|
| `/patient/dashboard` | Overview — upcoming appointments, recent prescriptions |
| `/patient/profile` | Edit name, phone, DOB, blood group, allergies |
| `/patient/addresses` | Manage delivery addresses |
| `/patient/medical-records` | Upload and view medical records |
| `/patient/reviews` | View all reviews you have written |
| `/patient/support` | Create and track support tickets |
| `/patient/appointments/<id>/review` | Submit a review for a completed appointment |

### Appointments

| URL | Description |
|---|---|
| `/appointments/my` | All your appointments |
| `/appointments/<id>` | Appointment detail with payment timer / join button |
| `/appointments/book/<doctor_id>` | Choose date + slot, confirm booking |
| `/appointments/<id>/cancel` | Cancel an appointment |

### Consultation

| URL | Description |
|---|---|
| `/consultation/room/<id>` | Jitsi Meet video room + text chat |
| `/consultation/start/<id>` | Mark consultation as in-progress (POST) |
| `/consultation/complete/<id>` | Doctor completes consultation with diagnosis (POST) |

### Doctor (`/doctor/*`)

| URL | Description |
|---|---|
| `/doctor/dashboard` | Stats — today's appointments, pending tasks |
| `/doctor/profile` | Edit professional info, bio, languages, fee |
| `/doctor/verification` | Upload credentials for admin review |
| `/doctor/availability` | Set weekly schedule and slot duration |
| `/doctor/earnings` | Revenue breakdown by month and transaction |
| `/doctor/view/<id>` | Public doctor profile page |

### Pharmacy (`/pharmacy/*`)

| URL | Description |
|---|---|
| `/pharmacy/` | Medicine catalog with category filter and search |
| `/pharmacy/medicine/<id>` | Medicine detail page |
| `/pharmacy/cart` | Shopping cart |
| `/pharmacy/checkout` | Address selection and order confirmation |
| `/pharmacy/orders` | Order history |
| `/pharmacy/orders/<id>` | Order detail and tracking |

### Admin (`/admin/*`)

| URL | Description |
|---|---|
| `/admin/` | Dashboard with platform-wide KPIs |
| `/admin/verifications` | Doctor credential review queue |
| `/admin/users` | User list — activate/deactivate accounts |
| `/admin/orders` | Pharmacy order fulfilment |
| `/admin/refunds` | Pending and processed refund requests |
| `/admin/specialties` | Add/edit/disable medical specialties |
| `/admin/medicine-categories` | Add/edit/disable pharmacy categories |
| `/admin/medicines` | Add and edit medicine listings |
| `/admin/tickets` | Support ticket queue |
| `/admin/audit-logs` | Security and action audit trail |

---

## REST API

All API endpoints are under `/api/`. They return JSON and require no authentication
unless noted.

### `GET /api/doctors`

List verified doctors with filtering, sorting, and pagination.

**Query parameters**

| Parameter | Type | Description |
|---|---|---|
| `name` | string | Partial match on first or last name |
| `specialty` | integer | Filter by specialty ID |
| `min_fee` | float | Minimum consultation fee |
| `max_fee` | float | Maximum consultation fee |
| `min_experience` | integer | Minimum years of experience |
| `language` | string | Partial match on languages spoken |
| `sort` | string | `name` (default), `fee_low`, `fee_high`, `experience` |
| `page` | integer | Page number (default: 1) |
| `per_page` | integer | Results per page (default: 20, max: 50) |

**Response**

```json
{
  "doctors": [
    {
      "id": 1,
      "name": "Dr. Priya Sharma",
      "specialty": "Cardiology",
      "qualifications": "MBBS, MD (Cardiology)",
      "experience_years": 12,
      "consultation_fee": 600.0,
      "rating": 4.7,
      "review_count": 38,
      "languages": ["English", "Hindi", "Tamil"],
      "avatar_url": "/uploads/avatars/abc123.jpg"
    }
  ],
  "total": 42,
  "page": 1,
  "pages": 3,
  "per_page": 20
}
```

### `GET /api/specialties`

```json
{
  "specialties": [
    { "id": 1, "name": "General Medicine", "slug": "general-medicine", "icon": "fa-stethoscope" }
  ]
}
```

### `GET /api/appointments/slots/<doctor_id>?date=YYYY-MM-DD`

Returns available time slots for a doctor on a given date.

```json
{
  "slots": [
    { "start": "09:00", "end": "09:30", "available": true },
    { "start": "09:30", "end": "10:00", "available": false }
  ]
}
```

### Cart API (requires patient login)

| Method | URL | Body | Description |
|---|---|---|---|
| GET | `/api/cart` | — | Fetch full cart with item details |
| POST | `/api/cart/add` | `{"medicine_id": 1, "quantity": 2}` | Add medicine to cart |
| PUT | `/api/cart/update` | `{"item_id": 5, "quantity": 3}` | Update item quantity |
| DELETE | `/api/cart/remove/<item_id>` | — | Remove a single item |
| POST | `/api/cart/clear` | — | Clear entire cart |

**Cart response shape**

```json
{
  "id": 3,
  "items": [
    {
      "id": 5,
      "medicine": {
        "id": 1,
        "name": "Paracetamol 500mg",
        "selling_price": 27.0,
        "requires_prescription": false,
        "in_stock": true
      },
      "quantity": 2,
      "line_total": 54.0
    }
  ],
  "total_items": 2,
  "subtotal": 54.0,
  "requires_prescription": false
}
```

---

## CLI Commands

Run these from the project root with the virtual environment active.

```bash
# Apply all pending database migrations
python -m flask db upgrade

# Generate a new migration after changing a model
python -m flask db migrate -m "describe what changed"

# Roll back the last migration
python -m flask db downgrade

# Seed specialties and medicine categories
python -m flask seed-db

# Create an admin user interactively
python -m flask create-admin

# Open a Python shell with app context loaded
python -m flask shell
```

---

## Running Tests

```bash
# Run the full test suite
python -m pytest tests/ -v

# Run with coverage report
python -m pytest tests/ -v --cov=app --cov-report=term-missing

# Run a single test file
python -m pytest tests/test_auth.py -v

# Run a single test by name
python -m pytest tests/test_auth.py::test_user_login_and_logout -v
```

**Current results:** 12 tests, 12 passing, ~54% code coverage.

Test files and what they cover:

| File | Tests |
|---|---|
| `test_auth.py` | Password hashing, registration, login/logout, invalid credentials, RBAC enforcement |
| `test_appointments.py` | Slot generation algorithm, successful booking, double-booking prevention via slot lock |
| `test_pharmacy.py` | Cart add/update/remove, inventory decrement when an order is placed |
| `test_api.py` | Doctor search API with filters, specialties endpoint |

---

## Environment Variables Reference

All variables live in `.env`. Copy `.env.example` as a starting point.

### Required

| Variable | Example | Description |
|---|---|---|
| `SECRET_KEY` | `a3f8...` (32+ random hex chars) | Flask session signing key — **must be changed in production** |
| `DATABASE_URL` | `sqlite:///telemed_seva.db` | Database connection string |

### Optional (development works without these)

| Variable | Default | Description |
|---|---|---|
| `FLASK_ENV` | `development` | `development` / `production` / `testing` |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis for rate limiting; falls back to `memory://` |
| `MAIL_SERVER` | `smtp.gmail.com` | SMTP server hostname |
| `MAIL_PORT` | `587` | SMTP port |
| `MAIL_USE_TLS` | `true` | Enable STARTTLS |
| `MAIL_USERNAME` | — | SMTP login username |
| `MAIL_PASSWORD` | — | SMTP login password or app-password |
| `MAIL_DEFAULT_SENDER` | `noreply@telemedseva.com` | From address on outgoing emails |
| `UPLOAD_FOLDER` | `uploads` | Relative path for file uploads |
| `MAX_CONTENT_LENGTH` | `16777216` | Max upload size in bytes (16 MB) |
| `RAZORPAY_KEY_ID` | — | Razorpay public key (leave blank for mock gateway) |
| `RAZORPAY_KEY_SECRET` | — | Razorpay secret key |
| `PLATFORM_NAME` | `TeleMed Seva` | Displayed in browser titles and emails |
| `PLATFORM_CURRENCY_SYMBOL` | `₹` | Currency symbol shown in the UI |
| `DEFAULT_CONSULTATION_DURATION` | `30` | Default slot length in minutes |

### Email setup (Gmail)

1. Enable 2-Factor Authentication on your Google account
2. Go to **Google Account → Security → App Passwords**
3. Create an app password for "Mail"
4. Set in `.env`:
   ```env
   MAIL_USERNAME=your-gmail@gmail.com
   MAIL_PASSWORD=xxxx-xxxx-xxxx-xxxx   # the 16-char app password
   ```

If email is not configured, verification tokens and reset links are printed
directly to the terminal so development still works.

---

## Production Deployment

### Using Docker Compose (recommended)

**1. Harden `.env` for production**

```env
FLASK_ENV=production
SECRET_KEY=<long-random-hex-64-chars>
DATABASE_URL=postgresql://telemed:strongpassword@db:5432/telemed_seva
REDIS_URL=redis://redis:6379/0
SESSION_COOKIE_SECURE=true
MAIL_SERVER=smtp.your-provider.com
MAIL_USERNAME=your-email
MAIL_PASSWORD=your-password
POSTGRES_USER=telemed
POSTGRES_PASSWORD=strongpassword
POSTGRES_DB=telemed_seva
```

**2. Remove development port exposures**

In `docker-compose.yml`, remove the `ports` lines from `db` and `redis`
so they are not publicly accessible.

**3. Build and deploy**

```bash
docker compose up -d --build
docker compose exec web python -m flask db upgrade
docker compose exec web python -m flask seed-db
docker compose exec web python -m flask create-admin
```

**4. Reverse proxy with Nginx**

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    # Redirect all HTTP to HTTPS
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name yourdomain.com;

    ssl_certificate     /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    client_max_body_size 20M;

    location / {
        proxy_pass         http://localhost:8000;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /path/to/telemed_seva/app/static/;
        expires 7d;
    }
}
```

**5. Get a free SSL certificate**

```bash
sudo certbot --nginx -d yourdomain.com
```

### Manual (without Docker)

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment
export FLASK_ENV=production
export DATABASE_URL=postgresql://user:pass@localhost/telemed_seva
export SECRET_KEY=<your-key>

# Migrate and seed
flask db upgrade
flask seed-db
flask create-admin

# Start with Gunicorn (uses gunicorn.conf.py automatically)
gunicorn --config gunicorn.conf.py run:app
```

Gunicorn configuration defaults:
- Workers: `(2 × CPU cores) + 1`
- Threads: 2 per worker
- Timeout: 120 seconds
- Port: 8000 (override with `PORT` env var)

---

## Security Notes

The following protections are active by default:

| Protection | Implementation |
|---|---|
| CSRF | Flask-WTF — all forms include a hidden CSRF token |
| Rate limiting | Login: 20/hour · Register: 10/hour · Password reset: 5/hour |
| Content Security Policy | `script-src`, `style-src`, `frame-src` (Jitsi Meet), `img-src` |
| Permissions Policy | Camera and microphone gated to `self` and `meet.jit.si` only |
| Secure sessions | `HttpOnly`, `SameSite=Lax`; `Secure` flag enabled in production |
| File uploads | Extension whitelist, upload size limit, auth required for sensitive paths |
| Audit logging | Every sensitive action (login, registration, verification, payment) is logged to `audit_logs` |
| Password hashing | Werkzeug `generate_password_hash` with PBKDF2-SHA256 |

**Before going to production:**

- [ ] Set `SECRET_KEY` to a 64-character random hex string
- [ ] Set `SESSION_COOKIE_SECURE=true` and serve over HTTPS
- [ ] Point `DATABASE_URL` at PostgreSQL — do not use SQLite in production
- [ ] Configure real SMTP credentials
- [ ] Set up daily database backups
- [ ] Remove or restrict the `5432` and `6379` port bindings in `docker-compose.yml`

---

## Troubleshooting

### `ModuleNotFoundError: No module named 'app'`

Make sure your virtual environment is activated and run with `python -m`:

```bash
# Wrong
pytest tests/

# Right
python -m pytest tests/
```

Or set `PYTHONPATH` first:

```bash
# Windows PowerShell
$env:PYTHONPATH="."; python -m pytest tests/

# macOS / Linux
PYTHONPATH=. python -m pytest tests/
```

---

### `flask` command not found

If `flask` is not on your PATH, use the module form:

```bash
# Instead of:   flask db upgrade
python -m flask db upgrade

# Instead of:   flask seed-db
python -m flask seed-db
```

---

### Database errors on first run

If you see `no such table`, you forgot to run migrations:

```bash
python -m flask db upgrade
```

If you see `Target database is not up to date`:

```bash
python -m flask db stamp head
python -m flask db upgrade
```

---

### Email verification link not arriving

If you have not configured SMTP, the verification token is printed to the
terminal where `python run.py` is running. Look for a line like:

```
[DEV] Verification link: http://127.0.0.1:5000/verify-email/<token>
```

Copy and paste that URL into your browser.

---

### Port 5000 already in use

```bash
# Windows — find and kill the process on port 5000
netstat -ano | findstr :5000
taskkill /PID <pid> /F

# macOS / Linux
lsof -i :5000
kill -9 <pid>
```

Or run on a different port:

```bash
python -m flask run --port 5001
```

---

### Static files (CSS/JS) not loading

Make sure you are accessing via `http://127.0.0.1:5000` and not opening the
HTML file directly. Flask must be running to serve `/static/` assets.

---

### Docker: `web` container exits immediately

Check the logs for the exact error:

```bash
docker compose logs web
```

Common causes:
- `DATABASE_URL` is wrong or the `db` container is not healthy yet
- `SECRET_KEY` is not set in `.env`
- A Python import error in one of the route files

---

## License

This project is released under the **MIT License**.
See the [LICENSE](LICENSE) file for the full text.

---

<div align="center">

Built with care for accessible healthcare · TeleMed Seva © 2024

</div>
