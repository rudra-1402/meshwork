"""
Demo Data Setup Script

Run this script to set up demo data for the Enhanced Authentication System.
"""

from app import create_app
from app.extensions import db
from app.models.college import College
from app.services.college_personnel_services import create_personnel
from app.services.whitelist_service import WhitelistService

app = create_app()

with app.app_context():
    print("\n=== ENHANCED AUTH SYSTEM - DEMO DATA SETUP ===\n")
    
    # Step 1: Get or create college
    college = College.query.first()
    
    if not college:
        print("⚠ No college found. Creating test college...")
        college = College(
            name="MIT India",
            email="admin@mitindia.edu",
            city="Mumbai",
            state="Maharashtra"
        )
        college.set_password("password123")
        db.session.add(college)
        db.session.commit()
        print(f"✓ Created college: {college.name} (ID: {college.id})")
    else:
        print(f"✓ Using existing college: {college.name} (ID: {college.id})")
    
    # Step 2: Set email patterns for college
    if not college.domain:
        print("\n📧 Setting up email patterns...")
        college.domain = "mitindia.edu"
        college.student_email_pattern = "{enrollment}@mitindia.edu"
        college.personnel_email_pattern = "{id}-{role}@mitindia.edu"
        college.address = "MIT Campus, Powai, Mumbai"
        college.registration_number = "MIT-2024-001"
        db.session.commit()
        print("✓ Email patterns configured")
    else:
        print(f"✓ Email patterns already configured (domain: {college.domain})")
    
    # Step 3: Create HOD/Admin personnel
    from app.models.college_personnel import CollegePersonnel
    existing_personnel = CollegePersonnel.query.filter_by(college_id=college.id).count()
    
    if existing_personnel == 0:
        print("\n👤 Creating HOD account...")
        success, msg, personnel = create_personnel(
            first_name="Dr. Rajesh",
            last_name="Kumar",
            email="hod001-hod@mitindia.edu",
            password="hod123",
            college_id=college.id,
            role="hod",
            personnel_id="HOD001"
        )
        
        if success:
            print(f"✓ HOD created: {personnel.get_full_name()}")
            print(f"  Email: {personnel.email}")
            print(f"  Password: hod123")
            print(f"  Role: {personnel.get_role_display()}")
        else:
            print(f"✗ Error creating HOD: {msg}")
    else:
        print(f"✓ {existing_personnel} personnel already exist")
    
    # Step 4: Whitelist sample student emails
    from app.models.whitelisted_email import WhitelistedEmail
    existing_whitelist = WhitelistedEmail.query.filter_by(college_id=college.id).count()
    
    if existing_whitelist == 0:
        print("\n📋 Whitelisting sample student emails...")
        
        # Get first personnel for added_by
        first_personnel = CollegePersonnel.query.filter_by(college_id=college.id).first()
        
        if first_personnel:
            sample_emails = [
                {"email": "2024001@mitindia.edu", "enrollment": "2024001", "name": "Amit Sharma"},
                {"email": "2024002@mitindia.edu", "enrollment": "2024002", "name": "Priya Patel"},
                {"email": "2024003@mitindia.edu", "enrollment": "2024003", "name": "Rahul Verma"},
                {"email": "2024004@mitindia.edu", "enrollment": "2024004", "name": "Sneha Reddy"},
                {"email": "2024005@mitindia.edu", "enrollment": "2024005", "name": "Vikram Singh"},
            ]
            
            result = WhitelistService.bulk_add_emails(
                college_id=college.id,
                email_list=sample_emails,
                added_by_personnel_id=first_personnel.id
            )
            
            print(f"✓ Whitelisted {result['successful']} emails")
            if result['failed'] > 0:
                print(f"⚠ Failed: {result['failed']}")
        else:
            print("⚠ No personnel found to attribute whitelisting")
    else:
        print(f"✓ {existing_whitelist} emails already whitelisted")
    
    # Final summary
    print("\n=== DEMO DATA SETUP COMPLETE ===\n")
    print("📌 College Information:")
    print(f"   Name: {college.name}")
    print(f"   Domain: {college.domain}")
    print(f"   Student Pattern: {college.student_email_pattern}")
    print(f"   Personnel Pattern: {college.personnel_email_pattern}")
    
    print("\n📌 Personnel Login:")
    hod = CollegePersonnel.query.filter_by(college_id=college.id).first()
    if hod:
        print(f"   Email: {hod.email}")
        print(f"   Password: hod123")
        print(f"   URL: http://localhost:5000/login/personnel")
    
    print("\n📌 Sample Student Emails (Whitelisted):")
    whitelist = WhitelistedEmail.query.filter_by(college_id=college.id, is_registered=False).limit(5).all()
    for entry in whitelist:
        print(f"   - {entry.email} ({entry.student_name})")
    
    print("\n📌 Next Steps:")
    print("   1. Start server: flask run")
    print("   2. Login as personnel: http://localhost:5000/login/personnel")
    print("   3. Manage whitelist: http://localhost:5000/personnel/whitelist")
    print("   4. Test student signup: http://localhost:5000/signup/user")
    print("\n🎉 Ready for demo!\n")
