from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.services.college_auth_services import authenticate_college, create_college
from app.services.college_personnel_services import authenticate_personnel, create_personnel
from app.services.email_validation_service import EmailValidationService
from flask_jwt_extended import create_access_token, unset_jwt_cookies, set_access_cookies

college_auth_routes = Blueprint("college_auth", __name__)

# ================= COLLEGE LOGIN =================
@college_auth_routes.route("/login/college", methods=["GET", "POST"])
def college_login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        result = authenticate_college(email, password)

        if result["success"]:
            college = result["college"]

            # Create JWT access token with college ID (prefixed with 'college_')
            access_token = create_access_token(identity=f"college_{college.id}")
            
            # Store token in HTTP-only cookie
            response = redirect(url_for("dashboard.college_dashboard"))
            set_access_cookies(response, access_token)

            flash("College logged in successfully!", "success")
            return response

        flash(result["message"], "error")
        return redirect(url_for("college_auth.college_login"))

    return render_template("colleges/login_college.html")


# ================= COLLEGE SIGNUP =================
@college_auth_routes.route("/signup/college", methods=["GET", "POST"])
def college_signup():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        city = request.form.get("city")
        state = request.form.get("state")

        # ---- validations ----
        if not name or not email or not password or not confirm_password:
            flash("All fields are required", "error")
            return redirect(url_for("college_auth.college_signup"))

        if password != confirm_password:
            flash("Passwords do not match", "error")
            return redirect(url_for("college_auth.college_signup"))

        college = create_college(
            name=name,
            email=email,
            password=password,
            city=city,
            state=state
        )

        if not college:
            flash("College already exists", "error")
            return redirect(url_for("college_auth.college_signup"))

        flash("College account created! Please login.", "success")
        return redirect(url_for("college_auth.college_login"))

    return render_template("colleges/signup_college.html")

# ================= COLLEGE LOGOUT =================
@college_auth_routes.route("/logout/college")
def college_logout():
    response = redirect(url_for("main_routes.landing"))
    unset_jwt_cookies(response)  # Clear JWT cookies
    flash("College logged out", "success")
    return response


# ================= PERSONNEL LOGIN =================
@college_auth_routes.route("/login/personnel", methods=["GET", "POST"])
def personnel_login():
    """College personnel login (HOD, faculty, staff, etc.)"""
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        # Validate inputs
        if not email or not password:
            flash("Email and password are required.", "error")
            return redirect(url_for("college_auth.personnel_login"))

        # Authenticate personnel
        personnel = authenticate_personnel(email, password)

        if not personnel:
            flash("Invalid email or password.", "error")
            return redirect(url_for("college_auth.personnel_login"))

        # Create JWT access token with personnel ID (prefixed with 'personnel_')
        access_token = create_access_token(identity=f"personnel_{personnel.id}")
        
        # Store token in HTTP-only cookie
        response = redirect(url_for("personnel.personnel_dashboard"))
        set_access_cookies(response, access_token)

        flash(f"Welcome {personnel.first_name}! Logged in as {personnel.get_role_display()}.", "success")
        return response

    return render_template("colleges/login_personnel.html")


# ================= PERSONNEL SIGNUP =================
@college_auth_routes.route("/signup/personnel/<int:college_id>", methods=["GET", "POST"])
def personnel_signup(college_id):
    """College personnel signup - requires college to exist first"""
    from app.models.college import College
    
    college = College.query.get_or_404(college_id)
    
    if request.method == "POST":
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        role = request.form.get("role")
        personnel_id = request.form.get("personnel_id", "").strip() or None

        # Validate required fields
        if not all([first_name, last_name, email, password, confirm_password, role]):
            flash("All fields except Personnel ID are required.", "error")
            return redirect(url_for("college_auth.personnel_signup", college_id=college_id))

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return redirect(url_for("college_auth.personnel_signup", college_id=college_id))

        # Validate email against personnel pattern
        email_validation = EmailValidationService.validate_personnel_email(email, college_id)
        
        if not email_validation['valid']:
            flash(email_validation['error'], "error")
            return redirect(url_for("college_auth.personnel_signup", college_id=college_id))

        # Create personnel
        success, message, personnel = create_personnel(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password,
            college_id=college_id,
            role=role,
            personnel_id=personnel_id
        )

        if not success:
            flash(message, "error")
            return redirect(url_for("college_auth.personnel_signup", college_id=college_id))

        flash(f"Personnel account created for {personnel.get_full_name()}! Please login.", "success")
        return redirect(url_for("college_auth.personnel_login"))

    # Pass valid roles to template
    valid_roles = ['admin', 'hod', 'faculty', 'staff', 'assistant', 'coordinator']
    
    return render_template("colleges/signup_personnel.html", 
                          college=college, 
                          valid_roles=valid_roles)


# ================= PERSONNEL LOGOUT =================
@college_auth_routes.route("/logout/personnel")
def personnel_logout():
    """Personnel logout - clears JWT and redirects to landing page"""
    response = redirect(url_for("main_routes.landing"))
    unset_jwt_cookies(response)  # Clear JWT cookies
    flash("Logged out successfully.", "success")
    return response
