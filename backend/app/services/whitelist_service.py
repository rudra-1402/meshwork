"""
Whitelist Service

Manages student email whitelist for college administrators.
"""

from app.extensions import db
from app.models.whitelisted_email import WhitelistedEmail
from app.models.college import College
from datetime import datetime
import csv
from io import StringIO


class WhitelistService:
    """Service for managing student email whitelist"""
    
    @staticmethod
    def add_email_to_whitelist(college_id, email, added_by_personnel_id, 
                                student_enrollment=None, student_name=None, notes=None):
        """
        Add single email to whitelist.
        
        Args:
            college_id (int): College ID
            email (str): Student email
            added_by_personnel_id (int): Personnel who added this
            student_enrollment (str, optional): Student enrollment number
            student_name (str, optional): Student name
            notes (str, optional): Additional notes
            
        Returns:
            tuple: (success: bool, message: str, whitelist_entry: WhitelistedEmail or None)
        """
        # Validate college exists
        college = College.query.get(college_id)
        if not college:
            return False, "College not found", None
        
        # Check if email already whitelisted
        existing = WhitelistedEmail.query.filter_by(email=email).first()
        if existing:
            return False, "Email already whitelisted", None
        
        # Create whitelist entry
        try:
            whitelist_entry = WhitelistedEmail(
                college_id=college_id,
                email=email,
                student_enrollment=student_enrollment,
                student_name=student_name,
                added_by_personnel_id=added_by_personnel_id,
                notes=notes
            )
            
            db.session.add(whitelist_entry)
            db.session.commit()
            
            return True, "Email added to whitelist successfully", whitelist_entry
        
        except Exception as e:
            db.session.rollback()
            return False, f"Error adding email: {str(e)}", None
    
    @staticmethod
    def bulk_add_emails(college_id, email_list, added_by_personnel_id):
        """
        Bulk add emails from list.
        
        Args:
            college_id (int): College ID
            email_list (list): List of dicts with keys: email, enrollment, name
            added_by_personnel_id (int): Personnel who added these
            
        Returns:
            dict: {
                'total': int,
                'successful': int,
                'failed': int,
                'errors': list
            }
        """
        result = {
            'total': len(email_list),
            'successful': 0,
            'failed': 0,
            'errors': []
        }
        
        for item in email_list:
            email = item.get('email', '').strip()
            enrollment = item.get('enrollment', '').strip() or None
            name = item.get('name', '').strip() or None
            
            if not email:
                result['failed'] += 1
                result['errors'].append("Empty email in list")
                continue
            
            success, message, _ = WhitelistService.add_email_to_whitelist(
                college_id=college_id,
                email=email,
                added_by_personnel_id=added_by_personnel_id,
                student_enrollment=enrollment,
                student_name=name
            )
            
            if success:
                result['successful'] += 1
            else:
                result['failed'] += 1
                result['errors'].append(f"{email}: {message}")
        
        return result
    
    @staticmethod
    def bulk_add_from_csv(college_id, csv_content, added_by_personnel_id):
        """
        Bulk add emails from CSV content.
        
        CSV format: email, enrollment, name
        
        Args:
            college_id (int): College ID
            csv_content (str): CSV file content
            added_by_personnel_id (int): Personnel who added these
            
        Returns:
            dict: Same as bulk_add_emails
        """
        try:
            # Parse CSV
            csv_file = StringIO(csv_content)
            reader = csv.DictReader(csv_file)
            
            email_list = []
            for row in reader:
                email_list.append({
                    'email': row.get('email', ''),
                    'enrollment': row.get('enrollment', ''),
                    'name': row.get('name', '')
                })
            
            return WhitelistService.bulk_add_emails(
                college_id, email_list, added_by_personnel_id
            )
        
        except Exception as e:
            return {
                'total': 0,
                'successful': 0,
                'failed': 0,
                'errors': [f"CSV parsing error: {str(e)}"]
            }
    
    @staticmethod
    def remove_from_whitelist(email_id):
        """
        Remove email from whitelist.
        
        Args:
            email_id (int): Whitelist entry ID
            
        Returns:
            tuple: (success: bool, message: str)
        """
        entry = WhitelistedEmail.query.get(email_id)
        
        if not entry:
            return False, "Whitelist entry not found"
        
        if entry.is_registered:
            return False, "Cannot remove registered email"
        
        try:
            db.session.delete(entry)
            db.session.commit()
            return True, "Email removed from whitelist"
        
        except Exception as e:
            db.session.rollback()
            return False, f"Error removing email: {str(e)}"
    
    @staticmethod
    def check_if_whitelisted(email):
        """
        Check if email is in whitelist.
        
        Args:
            email (str): Email to check
            
        Returns:
            tuple: (whitelisted: bool, entry: WhitelistedEmail or None)
        """
        entry = WhitelistedEmail.query.filter_by(email=email).first()
        
        if entry:
            return True, entry
        return False, None
    
    @staticmethod
    def mark_email_registered(email, user_id):
        """
        Mark whitelisted email as registered.
        
        Args:
            email (str): Email that was registered
            user_id (int): User ID who registered
            
        Returns:
            tuple: (success: bool, message: str)
        """
        entry = WhitelistedEmail.query.filter_by(email=email).first()
        
        if not entry:
            return False, "Email not in whitelist"
        
        if entry.is_registered:
            return False, "Email already marked as registered"
        
        try:
            entry.mark_as_registered(user_id)
            db.session.commit()
            return True, "Email marked as registered"
        
        except Exception as e:
            db.session.rollback()
            return False, f"Error updating registration status: {str(e)}"
    
    @staticmethod
    def get_college_whitelist(college_id, include_registered=True):
        """
        Get all whitelisted emails for a college.
        
        Args:
            college_id (int): College ID
            include_registered (bool): Include already registered emails
            
        Returns:
            list: List of WhitelistedEmail objects
        """
        query = WhitelistedEmail.query.filter_by(college_id=college_id)
        
        if not include_registered:
            query = query.filter_by(is_registered=False)
        
        return query.order_by(WhitelistedEmail.created_at.desc()).all()
    
    @staticmethod
    def get_pending_registrations(college_id):
        """
        Get emails that haven't registered yet.
        
        Args:
            college_id (int): College ID
            
        Returns:
            list: List of WhitelistedEmail objects
        """
        return WhitelistedEmail.query.filter_by(
            college_id=college_id,
            is_registered=False
        ).order_by(WhitelistedEmail.created_at.desc()).all()
    
    @staticmethod
    def get_whitelist_stats(college_id):
        """
        Get statistics about whitelist.
        
        Args:
            college_id (int): College ID
            
        Returns:
            dict: Statistics
        """
        total = WhitelistedEmail.query.filter_by(college_id=college_id).count()
        registered = WhitelistedEmail.query.filter_by(
            college_id=college_id, is_registered=True
        ).count()
        pending = total - registered
        
        return {
            'total': total,
            'registered': registered,
            'pending': pending,
            'registration_rate': (registered / total * 100) if total > 0 else 0
        }
