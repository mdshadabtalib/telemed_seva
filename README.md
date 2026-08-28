# TeleMed Seva

TeleMed Seva is a Flask-based telemedicine platform that helps patients find doctors, book consultations, receive prescriptions, and order medicines.

It is designed as a full-stack healthcare workflow rather than a collection of separate screens.

## What it does

- Patients can register, search for doctors, book appointments, and manage their profile.
- Doctors can manage their profile, availability, appointments, and prescriptions.
- Admins can verify doctors and manage specialties, orders, refunds, and support tickets.
- The pharmacy module supports medicines, carts, prescription uploads, and order tracking.
- A consultation room supports video-call integration and chat.

## Tech stack

- **Backend:** Python, Flask, SQLAlchemy
- **Database:** SQLite for local development; PostgreSQL can be used in production
- **Frontend:** Jinja templates, HTML, CSS, and vanilla JavaScript
- **Authentication:** Flask-Login with role-based access
- **Database migrations:** Flask-Migrate / Alembic

## Project structure

```text
app/
  auth/           Login, registration, password reset
  patient/        Patient dashboard and profile
  doctor/         Doctor profile, availability, and dashboard
  appointments/   Doctor search and appointment booking
  consultation/   Consultation room and chat
  prescriptions/  Prescription management
  pharmacy/       Medicines, cart, and orders
  admin/          Platform administration
  api/            JSON API endpoints
  models/         SQLAlchemy database models
  templates/      HTML templates
  static/         CSS, JavaScript, and images
migrations/       Database migration files
tests/            Automated tests
run.py            Application entry point
```

## Setup on a new device

### 1. Requirements

- Python 3.12 or newer
- Git

### 2. Clone and enter the project

```bash
git clone <repository-url>
cd telemed_seva
```

### 3. Create and activate a virtual environment

**Windows PowerShell**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Install dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 5. Configure environment values

Copy the example environment file and update values when needed.

```bash
copy .env.example .env
```

On macOS or Linux, use:

```bash
cp .env.example .env
```

For local development, the default SQLite database configuration works without any changes.

### 6. Create the database and starter data

```bash
python -m flask --app run db upgrade
python -m flask --app run seed-db
```

### 7. Run the application

```bash
python run.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser.

## Useful commands

```bash
# Run automated tests
python -m pytest

# Create an admin account
python -m flask --app run create-admin

# Add sample medicines
python -m flask --app run seed-medicines
```

## Key routes

| Route | Purpose |
| --- | --- |
| `/` | Home page |
| `/login` | Sign in |
| `/register` | Create an account |
| `/appointments` | Find and book doctors |
| `/pharmacy` | Browse medicines |
| `/health` | Application and database health check |

## Notes for interviewers

- The application uses Flask blueprints to keep each business area independent and easy to maintain.
- SQLAlchemy models represent users, doctors, appointments, prescriptions, payments, and pharmacy orders.
- Role-based access protects patient, doctor, and admin workflows.
- Flask-Migrate keeps database changes versioned and repeatable.
- The project separates routes, models, services, templates, and utility code to keep responsibilities clear.

## Local development notes

- The included configuration uses SQLite, so no database server is required to get started.
- Email, payment, and video-call providers are configured through environment variables and can be added when integrating real services.
- Never use the default development secret key in production.
