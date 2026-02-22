# ✨ Profile Picture & Appointment Booking Enhancements

## 🎯 Features Added:

### 1. 📷 **Profile Picture Upload (All User Types)**

#### **Route Added:**
- `/profile` - Profile settings page with picture upload

#### **Features:**
- ✅ Upload profile pictures (JPG, PNG, GIF up to 16MB)
- ✅ Auto-submit form on file selection
- ✅ Old pictures automatically deleted when new one uploaded
- ✅ Fallback to gradient avatar with initials if no picture
- ✅ Works for Patients, Doctors, and Pharmacies

#### **Where Profile Pictures Appear:**
1. **Navigation Bar** - Top right, clickable to go to profile
2. **Dashboard Sidebar** - Patient dashboard with large avatar
3. **Profile Settings Page** - Extra large display with upload button

#### **Profile Settings Page Shows:**
- Profile picture with upload button
- Full name
- Email
- Role (with emojis)
- Specialization (for doctors)
- Shop details (for pharmacies)

#### **File Handling:**
- Files saved to: `uploads/profile_TIMESTAMP_filename.ext`
- Secure filename sanitization
- Automatic old file deletion

---

### 2. 📅 **Enhanced Appointment Booking**

#### **Datetime Picker Features:**
- ✅ HTML5 `datetime-local` input
- ✅ Pre-filled with current time + 2 hours
- ✅ Minimum time: Current time + 1 hour (prevents past bookings)
- ✅ Native OS datetime picker (calendar + time)
- ✅ Format: `YYYY-MM-DDTHH:MM`

#### **UI Improvements:**
- 📅 Date & Time picker with emoji label
- 🎥 Consultation mode display (Video Call - Jitsi Meet)
- 💡 Helper text under each field
- 🎨 Modern styling with focus rings

#### **User Experience:**
1. Select doctor from dropdown
2. Pick date and time using native picker
3. Add optional notes/symptoms
4. Submit to book appointment

---

## 🎨 Visual Enhancements:

### **Avatar Styles:**
- **Small** (navigation): 32px × 32px
- **Large** (sidebar): 48px × 48px  
- **Extra Large** (profile): 120px × 120px

### **Gradient Fallback:**
```css
background: linear-gradient(to-br, #14b8a6, #06b6d4)
```
- Shows user initials (first + last)
- Colorful teal-to-cyan gradient
- Professional rounded shadow

### **Profile Link Added:**
- Sidebar navigation: "⚙️ Profile Settings"
- Click avatar/name in top nav to access profile

---

## 🔧 Technical Details:

### **Backend (app.py):**
```python
# New helper function
def save_profile_image(file):
    # Saves with prefix and timestamp
    # Returns filename or None

# New route
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    # Handles picture upload
    # Deletes old picture
    # Updates user.profile_image
```

### **Database:**
- Uses existing `profile_image` field in User model
- Stores filename only (not full path)

### **Template Context:**
```python
{
    'datetime': datetime,   # For year in footer
    'timedelta': timedelta  # For datetime calculations
}
```

---

## 📱 How to Use:

### **Upload Profile Picture:**
1. Login as any user type
2. Click your name/avatar in top navigation (or sidebar)
3. Click "📷 Choose Photo" button
4. Select image file
5. Picture uploads instantly

### **Book Appointment with Datetime Picker:**
1. Login as patient
2. Click "📍 Book New Appointment"
3. Select doctor
4. Click date/time field - native picker opens
5. Choose date and time
6. Add notes
7. Click "📍 Book Appointment"

---

## ✅ Tested Features:

- ✅ Profile picture upload (all user types)
- ✅ Avatar display in navigation
- ✅ Avatar display in sidebar
- ✅ Default gradient avatar fallback
- ✅ Datetime picker with minimum time
- ✅ Pre-filled datetime (+2 hours from now)
- ✅ Profile settings page layout
- ✅ Old picture deletion on new upload

---

## 🌟 Benefits:

### **Profile Pictures:**
- Personalizes the experience
- Easy user identification
- Professional appearance
- Instant visual recognition

### **Datetime Picker:**
- No more typing datetime manually
- Prevents typos and format errors
- Native OS experience
- Prevents booking in the past
- User-friendly calendar interface

---

## 🚀 Access:

**Profile Settings:** http://localhost:5000/profile (when logged in)

**Book Appointment:** http://localhost:5000/book (patient only)

**Hard refresh (Ctrl+Shift+R)** to see all changes!

---

## 🎨 Color Scheme:

- Profile avatars: Teal-Cyan gradient (#14b8a6 → #06b6d4)
- Upload button: Purple gradient (matches site theme)
- Datetime input: Indigo focus ring
- Page backgrounds: Light sea/sky colors

**Your telemedicine platform now has professional profile management and modern appointment booking!** 🎉
