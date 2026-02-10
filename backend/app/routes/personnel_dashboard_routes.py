"""
Personnel Dashboard Routes

Routes for college personnel (HOD, faculty, staff) to manage students and college operations.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.college_personnel_services import get_personnel_by_id
from app.services.whitelist_service import WhitelistService
from app.models.user import User
from functools import wraps


personnel_dashboard_routes = Blueprint("personnel", __name__, url_prefix="/personnel")


# ===== HELPER DECORATORS =====

def personnel_required(f):
    """Decorator to ensure user is authenticated personnel"""
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        identity = get_jwt_identity()
        
        # Check if identity is personnel
        if not identity.startswith('personnel_'):
            flash("Access denied. Personnel login required.", "error")
            return redirect(url_for("college_auth.personnel_login"))
        
        # Extract personnel ID
        personnel_id = int(identity.replace('personnel_', ''))
        personnel = get_personnel_by_id(personnel_id)
        
        if not personnel or not personnel.is_active:
            flash("Invalid or inactive personnel account.", "error")
            return redirect(url_for("college_auth.personnel_login"))
        
        # Pass personnel to route
        return f(personnel=personnel, *args, **kwargs)
    
    return decorated_function


def can_manage_students_required(f):
    """Decorator to ensure personnel can manage students"""
    @wraps(f)
    @personnel_required
    def decorated_function(personnel=None, *args, **kwargs):
        if not personnel.can_manage_students:
            flash("You don't have permission to manage students.", "error")
            return redirect(url_for("personnel.personnel_dashboard"))
        
        return f(personnel=personnel, *args, **kwargs)
    
    return decorated_function


# ===== ROUTES =====

@personnel_dashboard_routes.route("/dashboard")
@personnel_required
def personnel_dashboard(personnel=None):
    """Personnel main dashboard"""
    # Get statistics
    whitelist_stats = WhitelistService.get_whitelist_stats(personnel.college_id)
    
    # Get recent whitelist entries
    recent_whitelist = WhitelistService.get_college_whitelist(
        personnel.college_id, 
        include_registered=True
    )[:10]  # Last 10 entries
    
    return render_template(
        "personnel/dashboard.html",
        personnel=personnel,
        whitelist_stats=whitelist_stats,
        recent_whitelist=recent_whitelist
    )


@personnel_dashboard_routes.route("/students")
@personnel_required
def view_students(personnel=None):
    """View all students in college"""
    students = User.query.filter_by(college_id=personnel.college_id).all()
    
    return render_template(
        "personnel/students.html",
        personnel=personnel,
        students=students
    )


@personnel_dashboard_routes.route("/whitelist")
@can_manage_students_required
def manage_whitelist(personnel=None):
    """Manage student email whitelist"""
    include_registered = request.args.get('include_registered', 'true').lower() == 'true'
    
    whitelist = WhitelistService.get_college_whitelist(
        personnel.college_id,
        include_registered=include_registered
    )
    
    stats = WhitelistService.get_whitelist_stats(personnel.college_id)
    
    return render_template(
        "personnel/manage_whitelist.html",
        personnel=personnel,
        whitelist=whitelist,
        stats=stats,
        include_registered=include_registered
    )


@personnel_dashboard_routes.route("/whitelist/add-single", methods=["POST"])
@can_manage_students_required
def add_student_email(personnel=None):
    """Add single student email to whitelist"""
    email = request.form.get("email")
    enrollment = request.form.get("enrollment", "").strip() or None
    name = request.form.get("name", "").strip() or None
    notes = request.form.get("notes", "").strip() or None
    
    if not email:
        flash("Email is required.", "error")
        return redirect(url_for("personnel.manage_whitelist"))
    
    success, message, entry = WhitelistService.add_email_to_whitelist(
        college_id=personnel.college_id,
        email=email,
        added_by_personnel_id=personnel.id,
        student_enrollment=enrollment,
        student_name=name,
        notes=notes
    )
    
    if success:
        flash(message, "success")
    else:
        flash(message, "error")
    
    return redirect(url_for("personnel.manage_whitelist"))


@personnel_dashboard_routes.route("/whitelist/bulk-add", methods=["POST"])
@can_manage_students_required
def bulk_add_emails(personnel=None):
    """Bulk upload student emails from CSV"""
    if 'csv_file' not in request.files:
        flash("No file uploaded.", "error")
        return redirect(url_for("personnel.manage_whitelist"))
    
    file = request.files['csv_file']
    
    if file.filename == '':
        flash("No file selected.", "error")
        return redirect(url_for("personnel.manage_whitelist"))
    
    if not file.filename.endswith('.csv'):
        flash("File must be a CSV.", "error")
        return redirect(url_for("personnel.manage_whitelist"))
    
    try:
        # Read CSV content
        csv_content = file.read().decode('utf-8')
        
        # Bulk add
        result = WhitelistService.bulk_add_from_csv(
            college_id=personnel.college_id,
            csv_content=csv_content,
            added_by_personnel_id=personnel.id
        )
        
        if result['successful'] > 0:
            flash(f"Successfully added {result['successful']} emails. Failed: {result['failed']}", "success")
        else:
            flash(f"Failed to add emails. Errors: {', '.join(result['errors'][:3])}", "error")
    
    except Exception as e:
        flash(f"Error processing file: {str(e)}", "error")
    
    return redirect(url_for("personnel.manage_whitelist"))


@personnel_dashboard_routes.route("/whitelist/remove/<int:email_id>", methods=["POST"])
@can_manage_students_required
def remove_email(personnel=None, email_id=None):
    """Remove email from whitelist"""
    success, message = WhitelistService.remove_from_whitelist(email_id)
    
    if success:
        flash(message, "success")
    else:
        flash(message, "error")
    
    return redirect(url_for("personnel.manage_whitelist"))


@personnel_dashboard_routes.route("/profile")
@personnel_required
def personnel_profile(personnel=None):
    """Personnel profile page"""
    return render_template(
        "personnel/profile.html",
        personnel=personnel
    )
