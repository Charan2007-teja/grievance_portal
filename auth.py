# auth.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from models import User
from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from extensions import login_manager
from datetime import datetime

auth = Blueprint('auth', __name__, template_folder='templates')


# ============================================================
# LOAD USER SESSION
# ============================================================
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ============================================================
# REGISTER (STUDENT ONLY)
# ============================================================
@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':

        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        pin = request.form.get('pin', '').strip().upper()
        department = request.form.get('department', '').strip().upper()
        password = request.form.get('password', '').strip()

        # Empty fields check
        if not all([name, email, pin, department, password]):
            flash('Please fill all fields.', 'danger')
            return redirect(url_for('auth.register'))

        # Duplicate email or PIN
        if User.query.filter_by(email=email).first() or User.query.filter_by(pin=pin).first():
            flash("Email or PIN already registered.", "danger")
            return redirect(url_for('auth.register'))

        # -------------------------------
        # PIN VALIDATION
        # -------------------------------
        try:
            parts = pin.split('-')
            if len(parts) != 3:
                raise ValueError("PIN format must be 23189-CS-020")

            yearcode = parts[0]
            if len(yearcode) != 5:
                raise ValueError("Invalid year/college code")

            year2 = int(yearcode[:2])
            college = yearcode[2:]

            if college != "189":
                raise ValueError("College code must be 189")

            year_full = 2000 + year2
            if year_full > datetime.now().year:
                raise ValueError("Future year not allowed")

            dept_code = parts[1]
            if dept_code not in ["CS", "EC"]:
                raise ValueError("Department must be CS or EC")

            roll = parts[2]
            if not roll.isdigit() or len(roll) != 3:
                raise ValueError("Roll must be 3 digits")

            # Map PIN → Department
            if dept_code == "CS" and department != "CSE":
                raise ValueError("PIN dept CS → Must select CSE")

            if dept_code == "EC" and department != "ECE":
                raise ValueError("PIN dept EC → Must select ECE")

        except ValueError as e:
            flash(str(e), "danger")
            return redirect(url_for("auth.register"))

        # -------------------------------
        # CREATE STUDENT ACCOUNT
        # -------------------------------
        user = User(
            name=name,
            email=email,
            pin=pin,
            password=generate_password_hash(password),
            role="student",
            department=department,
            approved=False
        )

        db.session.add(user)
        db.session.commit()

        flash("Registration successful! Awaiting HOD approval.", "success")
        return redirect(url_for("index"))

    return render_template("auth/register.html")


# ============================================================
# LOGIN (STUDENT + STAFF)
# ============================================================
@auth.route('/login', methods=['GET', 'POST'])
def login():

    # Clear old session when opening login page again
    session.clear()
    session.modified = True

    if request.method == 'POST':

        user_type = request.form.get("user_type")
        loginid = request.form.get("loginid", "").strip().lower()
        password = request.form.get("password", "").strip()

        if not loginid or not password:
            flash("Enter login details.", "danger")
            return redirect(url_for("auth.login"))

        # --------------------------------
        # STUDENT LOGIN (PIN)
        # --------------------------------
        if user_type == "student":
            user = User.query.filter_by(pin=loginid, role="student").first()

            if not user:
                flash("Invalid PIN.", "danger")
                return redirect(url_for("auth.login"))

            if not user.approved:
                flash("Your account is not approved by HOD.", "warning")
                return redirect(url_for("auth.login"))

        # --------------------------------
        # STAFF LOGIN (EMAIL)
        # --------------------------------
        else:
            user = User.query.filter_by(email=loginid).first()
            if not user:
                flash("Invalid staff email.", "danger")
                return redirect(url_for("auth.login"))

        # --------------------------------
        # PASSWORD CHECK + MASTER PASSWORD
        # --------------------------------
        master_pass = current_app.config.get("MASTER_PASSWORD", None)

        valid_password = (
            check_password_hash(user.password, password)
            or (master_pass and password == master_pass)
        )

        if not valid_password:
            flash("Incorrect password.", "danger")
            return redirect(url_for("auth.login"))

        # Login
        login_user(user)
        session.permanent = False
        session.modified = True

        flash("Login successful!", "success")

        # Redirect based on role
        if user.role == "student":
            return redirect(url_for("student.my_complaints"))
        if user.role == "hod":
            return redirect(url_for("hod.hod_dashboard"))
        if user.role == "warden":
            return redirect(url_for("warden.warden_dashboard"))
        if user.role == "ao":
            return redirect(url_for("ao.ao_dashboard"))
        if user.role == "principal":
            return redirect(url_for("principal.principal_dashboard"))

        return redirect(url_for("index"))

    return render_template("auth/login.html")


# ============================================================
# PROFILE (ONLY HOD, AO, WARDEN)
# ============================================================
@auth.route('/profile', methods=['GET', 'POST'])
@login_required
def profile_page():

    if current_user.role.lower() in ["student", "principal"]:
        flash("Access denied.", "danger")
        return redirect(url_for("index"))

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()

        if name:
            current_user.name = name

        if email:
            current_user.email = email

        if password:
            current_user.password = generate_password_hash(password)

        db.session.commit()

        flash("Profile updated!", "success")
        return redirect(url_for("auth.profile_page"))

    return render_template("profile.html")


# ============================================================
# LOGOUT
# ============================================================
@auth.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    session.modified = True
    flash("Logged out successfully!", "info")
    return redirect(url_for("index"))