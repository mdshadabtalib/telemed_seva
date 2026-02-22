"""
Migration script to add new profile fields to User table
Run this once to update existing database
"""
from app import app, db

with app.app_context():
    # Add new columns using raw SQL
    try:
        with db.engine.connect() as conn:
            # Check if columns exist before adding
            result = conn.execute(db.text("PRAGMA table_info(user)"))
            existing_columns = [row[1] for row in result]
            
            # Add columns if they don't exist
            if 'phone' not in existing_columns:
                conn.execute(db.text("ALTER TABLE user ADD COLUMN phone VARCHAR(20)"))
                print("✅ Added 'phone' column")
            
            if 'address' not in existing_columns:
                conn.execute(db.text("ALTER TABLE user ADD COLUMN address VARCHAR(300)"))
                print("✅ Added 'address' column")
            
            if 'age' not in existing_columns:
                conn.execute(db.text("ALTER TABLE user ADD COLUMN age INTEGER"))
                print("✅ Added 'age' column")
            
            if 'gender' not in existing_columns:
                conn.execute(db.text("ALTER TABLE user ADD COLUMN gender VARCHAR(20)"))
                print("✅ Added 'gender' column")
            
            if 'license_number' not in existing_columns:
                conn.execute(db.text("ALTER TABLE user ADD COLUMN license_number VARCHAR(100)"))
                print("✅ Added 'license_number' column")
            
            if 'experience_years' not in existing_columns:
                conn.execute(db.text("ALTER TABLE user ADD COLUMN experience_years INTEGER"))
                print("✅ Added 'experience_years' column")
            
            conn.commit()
            print("\n🎉 Database migration completed successfully!")
            
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        print("Note: If columns already exist, this is normal.")
