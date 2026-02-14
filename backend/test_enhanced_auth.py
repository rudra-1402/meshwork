"""
Quick test script for enhanced authentication system
"""

from app import create_app
from app.extensions import db
from app.models.college import College
from app.models.college_personnel import CollegePersonnel
from app.models.whitelisted_email import WhitelistedEmail
from app.models.user import User

app = create_app()

with app.app_context():
    print("\n=== ENHANCED AUTH SYSTEM - DATABASE VERIFICATION ===\n")
    
    # Check tables exist
    tables = [table.name for table in db.metadata.sorted_tables]
    print("✓ Total tables:", len(tables))
    print("✓ New tables created:")
    if 'college_personnel' in tables:
        print("  - college_personnel ✓")
    if 'whitelisted_emails' in tables:
        print("  - whitelisted_emails ✓")
    
    # Check User model columns
    print("\n✓ User model columns:")
    user_columns = [col.name for col in User.__table__.columns]
    if 'first_name' in user_columns:
        print("  - first_name ✓")
    if 'last_name' in user_columns:
        print("  - last_name ✓")
    if 'username' in user_columns:
        # Check if unique
        username_col = [col for col in User.__table__.columns if col.name == 'username'][0]
        if username_col.unique:
            print("  - username (unique) ✓")
        else:
            print("  - username (not unique yet - check constraints)")
    
    # Check College model columns
    print("\n✓ College model columns:")
    college_columns = [col.name for col in College.__table__.columns]
    new_cols = ['address', 'domain', 'student_email_pattern', 'personnel_email_pattern', 'registration_number']
    for col in new_cols:
        if col in college_columns:
            print(f"  - {col} ✓")
    
    # Count records
    print("\n✓ Current record counts:")
    print(f"  - Users: {User.query.count()}")
    print(f"  - Colleges: {College.query.count()}")
    print(f"  - Personnel: {CollegePersonnel.query.count()}")
    print(f"  - Whitelisted Emails: {WhitelistedEmail.query.count()}")
    
    print("\n=== ALL CHECKS COMPLETE ===\n")
