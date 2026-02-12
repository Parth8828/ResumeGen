"""
Manual database migration to add languages and hobbies columns to user_profiles table
"""
import sqlite3
import os

# Get the database path
db_path = "resume_gen.db"

if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
    exit(1)

# Connect to database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Check if columns already exist
    cursor.execute("PRAGMA table_info(user_profiles)")
    columns = [row[1] for row in cursor.fetchall()]
    
    # Add languages column if it doesn't exist
    if 'languages' not in columns:
        print("Adding 'languages' column...")
        cursor.execute("ALTER TABLE user_profiles ADD COLUMN languages TEXT")
        print("✓ Added 'languages' column")
    else:
        print("'languages' column already exists")
    
    # Add hobbies column if it doesn't exist
    if 'hobbies' not in columns:
        print("Adding 'hobbies' column...")
        cursor.execute("ALTER TABLE user_profiles ADD COLUMN hobbies TEXT")
        print("✓ Added 'hobbies' column")
    else:
        print("'hobbies' column already exists")
    
    # Commit changes
    conn.commit()
    print("\n✓ Migration completed successfully!")
    
except Exception as e:
    print(f"Error during migration: {e}")
    conn.rollback()
finally:
    conn.close()
