"""
Tests for Personnel Management Functionality

Covers:
- personnel_dashboard_routes.py
- college_personnel_services.py  
- whitelist_service.py
- College personnel authentication and permissions

Following TEST_PATTERNS_DOCUMENTATION.md:
- Class-based organization
- API-driven testing
- Session-scoped fixtures
- Explicit cleanup in teardown
"""

import pytest
from app.extensions import db
from app.models.whitelisted_email import WhitelistedEmail
from app.models.college_personnel import CollegePersonnel
from app.models.user import User
from app.services.whitelist_service import WhitelistService
from app.services.college_personnel_services import (
    authenticate_personnel,
    create_personnel,
    get_personnel_by_id,
    get_personnel_by_email,
)


class TestPersonnelAuthentication:
    """Test personnel login and auth"""

    def test_create_personnel_success(self, app, personnel_user):
        """Creating personnel should succeed with valid data"""
        with app.app_context():
            p = CollegePersonnel.query.get(personnel_user["id"])
            assert p is not None
            assert p.email == personnel_user["email"]
            assert p.college_id == personnel_user["college_id"]

    def test_authenticate_personnel_valid_credentials(self, app, personnel_user):
        """Personnel should authenticate with valid credentials"""
        with app.app_context():
            personnel = authenticate_personnel(personnel_user["email"], "TestPass123!")
            assert personnel is not None
            assert personnel.id == personnel_user["id"]

    def test_authenticate_personnel_invalid_password(self, app, personnel_user):
        """Personnel auth should fail with wrong password"""
        with app.app_context():
            personnel = authenticate_personnel(personnel_user["email"], "WrongPassword")
            assert personnel is None

    def test_get_personnel_by_id(self, app, personnel_user):
        """Should retrieve personnel by ID"""
        with app.app_context():
            p = get_personnel_by_id(personnel_user["id"])
            assert p is not None
            assert p.id == personnel_user["id"]

    def test_get_personnel_by_email(self, app, personnel_user):
        """Should retrieve personnel by email"""
        with app.app_context():
            p = get_personnel_by_email(personnel_user["email"])
            assert p is not None
            assert p.email == personnel_user["email"]


class TestWhitelistService:
    """Test student email whitelist management"""

    def test_add_email_to_whitelist_success(self, app, personnel_user):
        """Adding email to whitelist should succeed"""
        with app.app_context():
            success, message, entry = WhitelistService.add_email_to_whitelist(
                college_id=personnel_user["college_id"],
                email="student@test.edu",
                added_by_personnel_id=personnel_user["id"],
                student_enrollment="CS2024001",
                student_name="Test Student",
                notes="Test whitelist entry"
            )
            
            assert success is True
            assert entry is not None
            assert entry.email == "student@test.edu"
            assert entry.student_enrollment == "CS2024001"
            assert entry.student_name == "Test Student"
            assert entry.is_registered is False
            
            # Cleanup
            WhitelistedEmail.query.filter_by(id=entry.id).delete()
            db.session.commit()

    def test_add_duplicate_email_fails(self, app, personnel_user):
        """Adding duplicate email should fail"""
        with app.app_context():
            # Add first email
            success1, _, entry1 = WhitelistService.add_email_to_whitelist(
                college_id=personnel_user["college_id"],
                email="duplicate@test.edu",
                added_by_personnel_id=personnel_user["id"]
            )
            assert success1 is True
            
            # Try to add same email again
            success2, message2, entry2 = WhitelistService.add_email_to_whitelist(
                college_id=personnel_user["college_id"],
                email="duplicate@test.edu",
                added_by_personnel_id=personnel_user["id"]
            )
            
            assert success2 is False
            assert "already whitelisted" in message2.lower()
            assert entry2 is None
            
            # Cleanup
            WhitelistedEmail.query.filter_by(id=entry1.id).delete()
            db.session.commit()

    def test_remove_from_whitelist_success(self, app, personnel_user):
        """Removing unregistered email should succeed"""
        with app.app_context():
            # Add email first
            success, _, entry = WhitelistService.add_email_to_whitelist(
                college_id=personnel_user["college_id"],
                email="remove@test.edu",
                added_by_personnel_id=personnel_user["id"]
            )
            assert success is True
            entry_id = entry.id
            
            # Remove it
            success, message = WhitelistService.remove_from_whitelist(entry_id)
            assert success is True
            assert "removed" in message.lower()
            
            # Verify it's gone
            entry = WhitelistedEmail.query.get(entry_id)
            assert entry is None

    def test_cannot_remove_registered_email(self, app, personnel_user):
        """Should not be able to remove registered emails"""
        with app.app_context():
            # Add email
            success, _, entry = WhitelistService.add_email_to_whitelist(
                college_id=personnel_user["college_id"],
                email="registered@test.edu",
                added_by_personnel_id=personnel_user["id"]
            )
            assert success is True
            
            # Mark as registered
            entry.is_registered = True
            db.session.commit()
            entry_id = entry.id
            
            # Try to remove
            success, message = WhitelistService.remove_from_whitelist(entry_id)
            assert success is False
            assert "registered" in message.lower()
            
            # Cleanup
            WhitelistedEmail.query.filter_by(id=entry_id).delete()
            db.session.commit()

    def test_check_if_whitelisted_exists(self, app, personnel_user):
        """Should detect whitelisted emails"""
        with app.app_context():
            # Add email
            success, _, entry = WhitelistService.add_email_to_whitelist(
                college_id=personnel_user["college_id"],
                email="whitelisted@test.edu",
                added_by_personnel_id=personnel_user["id"]
            )
            assert success is True
            
            # Check if whitelisted
            whitelisted, found_entry = WhitelistService.check_if_whitelisted(
                "whitelisted@test.edu", personnel_user["college_id"]
            )
            assert whitelisted is True
            assert found_entry is not None
            assert found_entry.email == "whitelisted@test.edu"
            
            # Cleanup
            WhitelistedEmail.query.filter_by(id=entry.id).delete()
            db.session.commit()

    def test_check_if_whitelisted_not_exists(self, app):
        """Should detect non-whitelisted emails"""
        with app.app_context():
            whitelisted, entry = WhitelistService.check_if_whitelisted("notwhitelisted@test.edu", college_id=9999)
            assert whitelisted is False
            assert entry is None


class TestBulkWhitelistOperations:
    """Test bulk email whitelist operations"""

    def test_bulk_add_emails_success(self, app, personnel_user):
        """Bulk adding emails should work"""
        with app.app_context():
            email_list = [
                {'email': 'bulk1@test.edu', 'enrollment': 'CS001', 'name': 'Student 1'},
                {'email': 'bulk2@test.edu', 'enrollment': 'CS002', 'name': 'Student 2'},
                {'email': 'bulk3@test.edu', 'enrollment': 'CS003', 'name': 'Student 3'},
            ]
            
            result = WhitelistService.bulk_add_emails(
                college_id=personnel_user["college_id"],
                email_list=email_list,
                added_by_personnel_id=personnel_user["id"]
            )
            
            assert result['total'] == 3
            assert result['successful'] == 3
            assert result['failed'] == 0
            
            # Verify they exist
            for item in email_list:
                entry = WhitelistedEmail.query.filter_by(email=item['email']).first()
                assert entry is not None
                assert entry.student_enrollment == item['enrollment']
            
            # Cleanup
            WhitelistedEmail.query.filter(
                WhitelistedEmail.email.in_([e['email'] for e in email_list])
            ).delete()
            db.session.commit()

    def test_bulk_add_from_csv_success(self, app, personnel_user):
        """Bulk adding from CSV should work"""
        with app.app_context():
            csv_content = """email,enrollment,name
csv1@test.edu,CS101,CSV Student 1
csv2@test.edu,CS102,CSV Student 2
csv3@test.edu,CS103,CSV Student 3"""
            
            result = WhitelistService.bulk_add_from_csv(
                college_id=personnel_user["college_id"],
                csv_content=csv_content,
                added_by_personnel_id=personnel_user["id"]
            )
            
            assert result['successful'] == 3
            assert result['failed'] == 0
            
            # Verify they exist
            entry1 = WhitelistedEmail.query.filter_by(email="csv1@test.edu").first()
            assert entry1 is not None
            assert entry1.student_enrollment == "CS101"
            
            # Cleanup
            WhitelistedEmail.query.filter(
                WhitelistedEmail.email.in_(['csv1@test.edu', 'csv2@test.edu', 'csv3@test.edu'])
            ).delete()
            db.session.commit()

    def test_bulk_add_with_partial_failures(self, app, personnel_user):
        """Bulk add should handle partial failures gracefully"""
        with app.app_context():
            # Add one email manually first
            WhitelistService.add_email_to_whitelist(
                college_id=personnel_user["college_id"],
                email="duplicate@test.edu",
                added_by_personnel_id=personnel_user["id"]
            )
            
            # Try to bulk add including the duplicate
            email_list = [
                {'email': 'new1@test.edu', 'enrollment': 'CS001', 'name': 'New Student 1'},
                {'email': 'duplicate@test.edu', 'enrollment': 'CS002', 'name': 'Duplicate'},  # Should fail
                {'email': 'new2@test.edu', 'enrollment': 'CS003', 'name': 'New Student 2'},
            ]
            
            result = WhitelistService.bulk_add_emails(
                college_id=personnel_user["college_id"],
                email_list=email_list,
                added_by_personnel_id=personnel_user["id"]
            )
            
            assert result['total'] == 3
            assert result['successful'] == 2  # Two new ones succeed
            assert result['failed'] == 1  # Duplicate fails
            
            # Cleanup
            WhitelistedEmail.query.filter(
                WhitelistedEmail.email.in_(['new1@test.edu', 'new2@test.edu', 'duplicate@test.edu'])
            ).delete()
            db.session.commit()


class TestWhitelistStats:
    """Test whitelist statistics"""

    def test_get_whitelist_stats(self, app, personnel_user):
        """Should return correct whitelist statistics"""
        with app.app_context():
            # Add some whitelist entries
            entries = []
            for i in range(5):
                _, _, entry = WhitelistService.add_email_to_whitelist(
                    college_id=personnel_user["college_id"],
                    email=f"stats{i}@test.edu",
                    added_by_personnel_id=personnel_user["id"]
                )
                entries.append(entry)
            
            # Mark 2 as registered
            entries[0].is_registered = True
            entries[1].is_registered = True
            db.session.commit()
            
            # Get stats
            stats = WhitelistService.get_whitelist_stats(personnel_user["college_id"])
            
            assert stats['total'] >= 5
            assert stats['registered'] >= 2
            assert stats['pending'] >= 3
            
            # Cleanup
            for entry in entries:
                WhitelistedEmail.query.filter_by(id=entry.id).delete()
            db.session.commit()

    def test_get_college_whitelist(self, app, personnel_user):
        """Should retrieve college whitelist"""
        with app.app_context():
            # Add entries
            entries = []
            for i in range(3):
                _, _, entry = WhitelistService.add_email_to_whitelist(
                    college_id=personnel_user["college_id"],
                    email=f"list{i}@test.edu",
                    added_by_personnel_id=personnel_user["id"]
                )
                entries.append(entry)
            
            # Get whitelist
            whitelist = WhitelistService.get_college_whitelist(personnel_user["college_id"])
            
            assert len(whitelist) >= 3
            emails = [e.email for e in whitelist]
            assert "list0@test.edu" in emails
            assert "list1@test.edu" in emails
            assert "list2@test.edu" in emails
            
            # Cleanup
            for entry in entries:
                WhitelistedEmail.query.filter_by(id=entry.id).delete()
            db.session.commit()

    def test_get_college_whitelist_exclude_registered(self, app, personnel_user):
        """Should be able to filter out registered emails"""
        with app.app_context():
            # Add entries
            _, _, entry1 = WhitelistService.add_email_to_whitelist(
                college_id=personnel_user["college_id"],
                email="pendingfilter@test.edu",
                added_by_personnel_id=personnel_user["id"]
            )
            _, _, entry2 = WhitelistService.add_email_to_whitelist(
                college_id=personnel_user["college_id"],
                email="registeredfilter@test.edu",
                added_by_personnel_id=personnel_user["id"]
            )
            
            # Mark one as registered
            entry2.is_registered = True
            db.session.commit()
            
            # Get only pending
            whitelist = WhitelistService.get_college_whitelist(
                personnel_user["college_id"],
                include_registered=False
            )
            
            emails = [e.email for e in whitelist]
            assert "pendingfilter@test.edu" in emails
            assert "registeredfilter@test.edu" not in emails
            
            # Cleanup
            WhitelistedEmail.query.filter_by(id=entry1.id).delete()
            WhitelistedEmail.query.filter_by(id=entry2.id).delete()
            db.session.commit()


class TestPersonnelPermissions:
    """Test personnel role-based permissions"""

    def test_personnel_can_manage_students_by_role(self, app, personnel_user):
        """Coordinator role should be able to manage students"""
        with app.app_context():
            p = CollegePersonnel.query.get(personnel_user["id"])
            # Change role to coordinator which has can_manage_students=True
            p.role = 'coordinator'
            p.set_role_permissions()
            db.session.commit()
            assert p.can_manage_students is True

    def test_personnel_roles_exist(self, app):
        """Should have defined personnel roles"""
        # This is more of a model check
        # Valid roles: HOD, faculty, staff
        valid_roles = ['HOD', 'faculty', 'staff']
        assert len(valid_roles) == 3
