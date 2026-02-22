# Telemed Pro - Complete Features & Setup Guide

## 🎉 New Features Added

### 1. 🔐 Email Verification & Password Reset
- **Password Reset**: Users can reset forgotten passwords via email
- **Email Verification**: New users receive verification emails (optional)
- **Token-based Security**: Secure, time-limited tokens for all email operations

### 2. 💬 Real-Time Chat
- **WebSocket-based**: Instant messaging between doctors and patients
- **Per-Appointment Chat**: Each appointment has its own chat room
- **Message History**: All messages are saved to the database
- **Real-time Updates**: Messages appear instantly for both parties

### 3. 🏥 PostgreSQL Support
- **Cloud-Ready**: Easily switch to PostgreSQL for production
- **Environment-based Config**: Configure via DATABASE_URL environment variable
- **Heroku-compatible**: Automatic postgres:// to postgresql:// conversion

### 4. 📱 Mobile-Responsive Design
- **Tailwind CSS**: Already mobile-friendly with responsive breakpoints
- **Touch-optimized**: Works great on tablets and phones
- **Adaptive Layout**: Tables and cards adjust for small screens

### 5. ☁️ Cloudinary Integration
- **Image Uploads**: Support for profile pictures and medicine images
- **Cloud Storage**: No local file storage needed
- **Easy Setup**: Configure via environment variables

## 📦 Installation

### 1. Install Dependencies

```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install new packages
pip install -r requirements.txt
```

### 2. Delete Old Database (Important!)

```powershell
Remove-Item C:\Users\mdsha\Desktop\telemed_pro\instance\telemed.db -Force
```

This is necessary because we added new columns to the database.

## ⚙️ Configuration

### Email Setup (Gmail Example)

Create a `.env` file or set environment variables:

```bash
# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password
MAIL_DEFAULT_SENDER=noreply@telemed.com
```

**For Gmail:**
1. Enable 2-Factor Authentication
2. Generate an [App Password](https://myaccount.google.com/apppasswords)
3. Use the app password (not your regular password)

### PostgreSQL Setup (Optional - for Production)

```bash
# Local PostgreSQL
DATABASE_URL=postgresql://username:password@localhost/telemed_db

# Heroku (automatically set)
DATABASE_URL=postgres://...
```

### Cloudinary Setup (Optional)

1. Sign up at [Cloudinary](https://cloudinary.com) (free tier available)
2. Get your credentials from the dashboard
3. Set environment variables:

```bash
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
```

## 🚀 Running the Application

```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Run the app
python app.py
```

Visit: `http://localhost:5000`

## 📋 Feature Usage

### Password Reset
1. Click "Forgot password?" on login page
2. Enter your email
3. Check email for reset link
4. Click link and set new password

**Note**: If email is not configured, the reset link will be printed to console.

### Real-Time Chat
1. Doctor or patient goes to appointment details
2. Click "💬 Chat" button
3. Messages appear in real-time
4. Both parties see the same conversation

### Using PostgreSQL

#### Local PostgreSQL:
```powershell
# Install PostgreSQL locally
# Create database
createdb telemed_db

# Set environment variable
$env:DATABASE_URL="postgresql://username:password@localhost/telemed_db"

# Run app
python app.py
```

#### On Heroku:
```bash
# Heroku automatically provides DATABASE_URL
# Just deploy and it works!
git push heroku main
```

### Image Uploads with Cloudinary

Example code to upload images (add to your routes):

```python
import cloudinary
import cloudinary.uploader

# Configure (already done in app.py)
cloudinary.config(
    cloud_name=app.config['CLOUDINARY_CLOUD_NAME'],
    api_key=app.config['CLOUDINARY_API_KEY'],
    api_secret=app.config['CLOUDINARY_API_SECRET']
)

# Upload file
if 'image' in request.files:
    file = request.files['image']
    result = cloudinary.uploader.upload(file)
    image_url = result['secure_url']
    # Save image_url to database
```

## 🎨 Mobile Responsiveness

The app already uses Tailwind's responsive classes:
- `sm:` - Small screens (640px+)
- `md:` - Medium screens (768px+)
- `lg:` - Large screens (1024px+)

Key responsive features:
- **Navigation**: Hamburger menu on mobile (can be enhanced)
- **Tables**: Horizontal scroll on small screens
- **Forms**: Stack vertically on mobile
- **Dashboard**: Single column on mobile, multi-column on desktop

## 🔒 Security Best Practices

1. **Never commit secrets**: Use environment variables
2. **Use HTTPS in production**: Required for secure cookies
3. **Email App Passwords**: Don't use regular Gmail passwords
4. **Database Backups**: Regular backups for PostgreSQL
5. **CORS Configuration**: Restrict in production

## 📊 Database Models

### New Models Added:

**ChatMessage**
- `id`: Primary key
- `appointment_id`: Foreign key to Appointment
- `sender_id`: Foreign key to User
- `message`: Text content
- `created_at`: Timestamp

**User (Updated)**
- Added: `email_verified` (Boolean)
- Added: `profile_image` (String)

**Medicine (Updated)**
- Added: `image_url` (String)

## 🐛 Troubleshooting

### Chat Not Working
- Check that Flask-SocketIO is installed
- Verify Socket.IO CDN is loading
- Check browser console for errors

### Email Not Sending
- Verify MAIL_USERNAME and MAIL_PASSWORD are set
- Check if using Gmail App Password
- Look at console output for error messages

### Database Errors
- Delete old database: `Remove-Item instance\telemed.db -Force`
- Run migrations if using Alembic
- Check DATABASE_URL format

## 🌐 Deployment

### Deploy to Heroku:

```bash
# Install Heroku CLI
# Login
heroku login

# Create app
heroku create your-app-name

# Add PostgreSQL
heroku addons:create heroku-postgresql:mini

# Set environment variables
heroku config:set MAIL_USERNAME=your_email@gmail.com
heroku config:set MAIL_PASSWORD=your_app_password
heroku config:set FLASK_SECRET=random_secret_key

# Deploy
git push heroku main

# Open app
heroku open
```

### Deploy to Render:

1. Connect GitHub repository
2. Set environment variables in dashboard
3. Deploy automatically on push

## 📝 TODO / Future Enhancements

- [ ] Add file upload for prescriptions
- [ ] Implement email verification requirement
- [ ] Add SMS notifications (Twilio)
- [ ] Admin panel for user management
- [ ] Appointment reminders via email
- [ ] Video call recording
- [ ] Payment integration
- [ ] Multi-language support

## 💡 Tips

1. **Testing Email Locally**: Use [Mailtrap](https://mailtrap.io) for development
2. **Free PostgreSQL**: [ElephantSQL](https://elephantsql.com) offers free tier
3. **Image Optimization**: Cloudinary automatically optimizes images
4. **Chat Persistence**: Messages are saved even if users disconnect

## 📞 Support

For issues or questions:
- Check console logs for errors
- Verify all environment variables are set
- Ensure all dependencies are installed
- Test with sample accounts first

---

**Happy Coding!** 🚀
