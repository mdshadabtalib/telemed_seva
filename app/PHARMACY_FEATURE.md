# Pharmacy Feature Documentation

## Overview
The pharmacy feature has been added to the telemedicine platform, allowing pharmacy shops to register, manage their medicine inventory, and enabling users to search for medicines across all registered pharmacies.

## Features

### 1. Pharmacy Registration
- Pharmacy shops can register as a new user type alongside patients and doctors
- Registration fields include:
  - Full Name (Owner/Manager name)
  - Email & Password
  - Shop Name
  - Shop Address
  - Phone Number

### 2. Pharmacy Dashboard
- View all medicines in inventory
- Medicine listing with:
  - Medicine name and description
  - Category
  - Price
  - Stock levels (color-coded: green for good stock, yellow for low stock, red for out of stock)
  - Edit and Delete actions

### 3. Medicine Management
- **Add Medicine**: Form to add new medicines with name, description, category, price, and stock
- **Edit Medicine**: Update existing medicine details
- **Delete Medicine**: Remove medicines from inventory (with confirmation)

### 4. Public Medicine Search
- Available to all users (no login required)
- Search by medicine name or category
- Results display:
  - Medicine details (name, description, category)
  - Current price
  - Stock availability
  - Pharmacy information (shop name, address, phone)

## How to Use

### For Pharmacy Owners:
1. Go to the registration page
2. Select "Pharmacy" as the role
3. Fill in your shop details
4. Login and navigate to the pharmacy dashboard
5. Add medicines using the "Add Medicine" button
6. Manage your inventory through edit/delete options

### For Users (Patients/Visitors):
1. Click "🔍 Find Medicine" in the navigation bar (available on all pages)
2. Enter medicine name or category
3. View search results with pharmacy contact information
4. Contact the pharmacy directly via the displayed phone number

## Database Schema

### Updated User Model
- Added fields: `shop_name`, `shop_address`, `shop_phone`
- Role now supports: 'patient', 'doctor', 'pharmacy'

### New Medicine Model
- `id`: Primary key
- `pharmacy_id`: Foreign key to User (pharmacy owner)
- `name`: Medicine name
- `description`: Optional description
- `price`: Price in rupees
- `stock`: Stock quantity
- `category`: Medicine category
- `created_at`: Timestamp

## Routes

### Pharmacy Routes (Login Required)
- `/pharmacy` - Pharmacy dashboard
- `/pharmacy/add-medicine` - Add new medicine
- `/pharmacy/edit-medicine/<id>` - Edit existing medicine
- `/pharmacy/delete-medicine/<id>` - Delete medicine

### Public Routes
- `/search-medicine` - Search medicines (accessible to all)

## Technical Details
- Built with Flask and SQLAlchemy
- Uses the existing authentication system (Flask-Login)
- Styled with Tailwind CSS for consistency
- Responsive design for mobile and desktop

## Testing
To test the pharmacy feature:
1. Register a new pharmacy account
2. Add 2-3 sample medicines
3. Logout and use the medicine search to find them
4. Test edit and delete functionality
