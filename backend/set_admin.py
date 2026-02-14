"""
Admin Setup Script

This script helps you promote users to admin status.
Run this after migrating the database to add is_admin field.

Usage:
    python set_admin.py <user_email> [--remove]
    
Examples:
    python set_admin.py admin@college.edu
    python set_admin.py admin@college.edu --remove
"""

import sys
from app import create_app
from app.extensions import db
from app.models.user import User


def set_admin_status(email, is_admin=True):
    """Set admin status for a user by email"""
    app = create_app()
    
    with app.app_context():
        user = User.query.filter_by(email=email).first()
        
        if not user:
            print(f"❌ Error: User with email '{email}' not found.")
            return False
        
        user.is_admin = is_admin
        db.session.commit()
        
        status = "GRANTED" if is_admin else "REVOKED"
        print(f"✅ Success: Admin privileges {status} for user:")
        print(f"   - Email: {user.email}")
        print(f"   - Username: {user.username}")
        print(f"   - Name: {user.get_full_name()}")
        print(f"   - Admin Status: {user.is_admin}")
        
        return True


def list_admins():
    """List all users with admin privileges"""
    app = create_app()
    
    with app.app_context():
        admins = User.query.filter_by(is_admin=True).all()
        
        if not admins:
            print("ℹ️  No admin users found.")
            return
        
        print(f"\n👥 Admin Users ({len(admins)}):")
        print("-" * 60)
        for admin in admins:
            print(f"   📧 {admin.email}")
            print(f"      Username: {admin.username}")
            print(f"      Name: {admin.get_full_name()}")
            print(f"      Level: {admin.level} | XP: {admin.xp}")
            print()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python set_admin.py <user_email> [--remove]")
        print("       python set_admin.py --list")
        sys.exit(1)
    
    if sys.argv[1] == "--list":
        list_admins()
    else:
        email = sys.argv[1]
        remove = "--remove" in sys.argv
        
        set_admin_status(email, is_admin=not remove)
