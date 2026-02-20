"""
Email Validation Service

Validates student and personnel emails against college patterns and whitelist.
"""

from app.extensions import db
from app.models.user import User
from app.models.college import College
from app.models.whitelisted_email import WhitelistedEmail
import re


class EmailValidationService:
    """Service for email validation and pattern matching"""
    
    @staticmethod
    def check_username_availability(username):
        """
        Check if username is available.
        
        Args:
            username (str): Username to check
            
        Returns:
            dict: {'available': bool, 'message': str}
        """
        if not username or len(username) < 3:
            return {
                'available': False,
                'message': 'Username must be at least 3 characters'
            }
        
        exists = User.query.filter_by(username=username).first()
        
        if exists:
            return {
                'available': False,
                'message': 'Username already taken'
            }
        
        return {
            'available': True,
            'message': 'Username available'
        }
    
    @staticmethod
    def validate_student_email(email):
        """
        Validate student email against college patterns and whitelist.
        
        Args:
            email (str): Student email to validate
            
        Returns:
            dict: {
                'valid': bool,
                'college_id': int or None,
                'college_name': str or None,
                'whitelisted': bool,
                'whitelist_entry_id': int or None,
                'error': str or None
            }
        """
        if not email:
            return {
                'valid': False,
                'college_id': None,
                'college_name': None,
                'whitelisted': False,
                'whitelist_entry_id': None,
                'error': 'Email is required'
            }
        
        # Check if email already registered
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return {
                'valid': False,
                'college_id': None,
                'college_name': None,
                'whitelisted': False,
                'whitelist_entry_id': None,
                'error': 'Email already registered'
            }
        
        # Extract domain from email
        domain = EmailValidationService.extract_domain(email)
        if not domain:
            return {
                'valid': False,
                'college_id': None,
                'college_name': None,
                'whitelisted': False,
                'whitelist_entry_id': None,
                'error': 'Invalid email format'
            }
        
        # Find college by domain
        college = EmailValidationService.find_college_by_domain(domain)
        if not college:
            return {
                'valid': False,
                'college_id': None,
                'college_name': None,
                'whitelisted': False,
                'whitelist_entry_id': None,
                'error': 'College not found for this email domain'
            }
        
        # Check pattern (optional for backward compatibility)
        if college.student_email_pattern:
            # Validate against pattern
            pattern_valid = EmailValidationService.matches_pattern(
                email, college.student_email_pattern
            )
            
            if not pattern_valid:
                return {
                    'valid': False,
                    'college_id': college.id,
                    'college_name': college.name,
                    'whitelisted': False,
                    'whitelist_entry_id': None,
                    'error': 'Email does not match college student pattern'
                }
        
        # Check if email is whitelisted
        whitelist_entry = WhitelistedEmail.query.filter_by(
            email=email,
            college_id=college.id
        ).first()
        
        if not whitelist_entry:
            return {
                'valid': False,
                'college_id': college.id,
                'college_name': college.name,
                'whitelisted': False,
                'whitelist_entry_id': None,
                'error': 'Email not whitelisted. Please contact your college administrator.'
            }
        
        if whitelist_entry.is_registered:
            return {
                'valid': False,
                'college_id': college.id,
                'college_name': college.name,
                'whitelisted': True,
                'whitelist_entry_id': whitelist_entry.id,
                'error': 'Email already registered'
            }
        
        # All checks passed
        return {
            'valid': True,
            'college_id': college.id,
            'college_name': college.name,
            'whitelisted': True,
            'whitelist_entry_id': whitelist_entry.id,
            'error': None
        }
    
    @staticmethod
    def validate_personnel_email(email, college_id):
        """
        Validate personnel email against college's personnel pattern.
        
        Args:
            email (str): Personnel email
            college_id (int): College ID
            
        Returns:
            dict: {
                'valid': bool,
                'role': str or None,
                'personnel_id': str or None,
                'error': str or None
            }
        """
        if not email:
            return {
                'valid': False,
                'role': None,
                'personnel_id': None,
                'error': 'Email is required'
            }
        
        college = db.session.get(College, college_id)
        if not college:
            return {
                'valid': False,
                'role': None,
                'personnel_id': None,
                'error': 'College not found'
            }
        
        # Check if email already exists
        from app.models.college_personnel import CollegePersonnel
        existing = CollegePersonnel.query.filter_by(email=email).first()
        if existing:
            return {
                'valid': False,
                'role': None,
                'personnel_id': None,
                'error': 'Email already registered'
            }
        
        # If no pattern configured, allow any email
        if not college.personnel_email_pattern:
            return {
                'valid': True,
                'role': None,
                'personnel_id': None,
                'error': None
            }
        
        # Validate against pattern
        pattern_valid = EmailValidationService.matches_pattern(
            email, college.personnel_email_pattern
        )
        
        if not pattern_valid:
            return {
                'valid': False,
                'role': None,
                'personnel_id': None,
                'error': 'Email does not match college personnel pattern'
            }
        
        # Try to extract role and personnel_id from pattern
        parsed = EmailValidationService.parse_email_with_pattern(
            college.personnel_email_pattern, email
        )
        
        return {
            'valid': True,
            'role': parsed.get('role'),
            'personnel_id': parsed.get('id') or parsed.get('personnel_id'),
            'error': None
        }
    
    @staticmethod
    def extract_domain(email):
        """
        Extract domain from email.
        
        Args:
            email (str): Email address
            
        Returns:
            str or None: Domain part of email
        """
        if not email or '@' not in email:
            return None
        
        parts = email.split('@')
        if len(parts) != 2:
            return None
        
        return parts[1].lower()
    
    @staticmethod
    def parse_email_with_pattern(pattern, email):
        """
        Parse email using pattern template.
        
        Args:
            pattern (str): Pattern like "{enrollment}@{domain}"
            email (str): Email to parse
            
        Returns:
            dict: Extracted values from email
        """
        # Convert pattern to regex
        # Find all {variable} placeholders
        placeholders = re.findall(r'\{(\w+)\}', pattern)
        
        # Escape special regex characters except { }
        regex_pattern = re.escape(pattern)
        
        # Replace escaped placeholders with capture groups
        for placeholder in placeholders:
            escaped_placeholder = re.escape(f'{{{placeholder}}}')
            regex_pattern = regex_pattern.replace(escaped_placeholder, r'([^@\-\.]+)')
        
        # Add anchors
        regex_pattern = '^' + regex_pattern + '$'
        
        # Match email against pattern
        match = re.match(regex_pattern, email, re.IGNORECASE)
        
        if not match:
            return {}
        
        # Extract values
        result = {}
        for i, placeholder in enumerate(placeholders):
            result[placeholder] = match.group(i + 1)
        
        return result
    
    @staticmethod
    def matches_pattern(email, pattern):
        """
        Check if email matches pattern.
        
        Args:
            email (str): Email to check
            pattern (str): Pattern to match against
            
        Returns:
            bool: True if matches, False otherwise
        """
        parsed = EmailValidationService.parse_email_with_pattern(pattern, email)
        return len(parsed) > 0
    
    @staticmethod
    def find_college_by_domain(domain):
        """
        Find college by domain.
        
        Args:
            domain (str): Email domain
            
        Returns:
            College or None: College object if found
        """
        # First try direct domain match
        college = College.query.filter_by(domain=domain).first()
        
        if college:
            return college
        
        # Try case-insensitive search
        college = College.query.filter(
            College.domain.ilike(domain)
        ).first()
        
        return college
    
    @staticmethod
    def generate_username_from_email(email):
        """
        Generate suggested username from email.
        
        Args:
            email (str): Email address
            
        Returns:
            str: Suggested username
        """
        if not email or '@' not in email:
            return 'user'
        
        # Extract local part before @
        local_part = email.split('@')[0]
        
        # Remove special characters
        username = re.sub(r'[^a-zA-Z0-9_]', '', local_part)
        
        # Ensure minimum length
        if len(username) < 3:
            username = 'user' + username
        
        # Check availability and add numbers if needed
        base_username = username
        counter = 1
        
        while User.query.filter_by(username=username).first():
            username = f"{base_username}{counter}"
            counter += 1
            
            # Prevent infinite loop
            if counter > 1000:
                break
        
        return username
