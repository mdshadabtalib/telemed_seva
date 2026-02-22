# Quick Start Guide

## 🚀 Get Started in 3 Steps

### Step 1: Install New Dependencies
```powershell
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Step 2: Delete Old Database
```powershell
Remove-Item instance\telemed.db -Force
```

### Step 3: Run the App
```powershell
python app.py
```

Visit: **http://localhost:5000**

---

## ✨ What's New?

### 1. 🔐 Password Reset
- Click "Forgot password?" on login page
- No email config needed for testing (link prints to console)

### 2. 💬 Real-Time Chat
- Book an appointment
- Go to consultation page
- Click "💬 Chat" button
- Open in two browsers to see real-time messaging!

### 3. 📱 Mobile-Friendly
- Already responsive with Tailwind CSS
- Works great on phones and tablets

### 4. 🏥 PostgreSQL Ready
- Set `DATABASE_URL` environment variable
- Deploy to Heroku or Render easily

### 5. ☁️ Cloudinary Support
- Upload profile pictures
- Add medicine images
- Set environment variables to enable

---

## 📧 Optional: Email Configuration

For actual email sending (Gmail):

```powershell
$env:MAIL_USERNAME="your_email@gmail.com"
$env:MAIL_PASSWORD="your_app_password"
```

**Get Gmail App Password:**
1. Enable 2FA on your Google account
2. Visit: https://myaccount.google.com/apppasswords
3. Create app password for "Mail"

---

## 🎯 Quick Test

1. **Password Reset**:
   - Go to login → "Forgot password?"
   - Enter: `sita@example.com`
   - Check console for reset link
   - Copy link to browser

2. **Real-Time Chat**:
   - Login as patient: `sita@example.com` / `patient123`
   - Book appointment
   - Logout, login as doctor: `dr.sharma@example.com` / `doc123`
   - Open appointment → Click "💬 Chat"
   - Open another browser, login as patient, go to same appointment chat
   - Send messages - they appear instantly!

3. **Pharmacy**:
   - Register as pharmacy
   - Add medicines
   - Use "🔍 Find Medicine" to search

---

## 🆘 Troubleshooting

**Chat not working?**
- Check console for errors
- Ensure Flask-SocketIO installed: `pip show flask-socketio`

**Email not sending?**
- That's OK! Links print to console for testing
- Set MAIL_USERNAME/PASSWORD for real emails

**Database errors?**
- Delete database: `Remove-Item instance\telemed.db -Force`
- Restart app: `python app.py`

---

## 📚 Full Documentation

See `FEATURES_SETUP.md` for complete details on:
- Email configuration
- PostgreSQL setup
- Cloudinary integration
- Deployment guides
- Security best practices

---

**All features are working! Email config is optional for testing.**
