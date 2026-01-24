# student.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_from_directory
from flask_login import login_required, current_user
from extensions import db
from models import Complaint, User, Notification
import os, uuid

student = Blueprint('student', __name__, template_folder='templates/student')


# ===================================================================
# CATEGORY → ASSIGNED STAFF MAPPING
# ===================================================================
CATEGORIES = {
    # WARDEN
    "hostel_problem": "warden",
    "mess_food": "warden",
    "electricity_issues": "warden",
    "water_issues": "warden",
    "hostel_cleanliness": "warden",
    "hostel_security": "warden",
    "room_maintenance": "warden",
    "bathroom_plumbing": "warden",
    "noisy_environment": "warden",

    # HOD
    "academic_issue": "hod",
    "faculty_misbehavior": "hod",
    "lab_issue": "hod",
    "department_infrastructure": "hod",
    "syllabus_not_covered": "hod",
    "teaching_quality_issue": "hod",

    # AO
    "certificate_issue": "ao",
    "scholarship_issue": "ao",
    "fee_receipt_issue": "ao",
    "bonafide_request_delay": "ao",
    "hostel_bill_issue": "ao",
    "mess_bill_issue": "ao",

    # DEFAULT
    "other": "hod"
}


# ===================================================================
# FILE NEW COMPLAINT
# ===================================================================
@student.route('/complaint/new', methods=['GET', 'POST'])
@login_required
def new_complaint():

    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        category = request.form.get('category')

        if not title or not description or not category:
            flash("Please fill all fields.", "danger")
            return redirect(url_for('student.new_complaint'))

        upload_dir = current_app.config.get("UPLOAD_FOLDER", "uploads")
        os.makedirs(upload_dir, exist_ok=True)

        file_list = []
        for f in request.files.getlist("attachments"):
            if f and f.filename:
                ext = os.path.splitext(f.filename)[1]
                fname = f"{uuid.uuid4().hex}{ext}"
                f.save(os.path.join(upload_dir, fname))
                file_list.append(fname)

        attachments = ",".join(file_list) if file_list else None

        assigned_role = CATEGORIES.get(category, "hod")

        complaint = Complaint(
            title=title,
            description=description,
            category=category,
            attachment=attachments,
            student_id=current_user.id,
            status="Pending",
            assigned_to=assigned_role,
            department=current_user.department
        )

        db.session.add(complaint)
        db.session.commit()

        # Notify staff
        staff = None
        if assigned_role == "hod":
            staff = User.query.filter_by(role="hod", department=current_user.department).first()
        else:
            staff = User.query.filter_by(role=assigned_role).first()

        if staff:
            db.session.add(Notification(
                user_id=staff.id,
                message=f"New complaint submitted: {complaint.title}"
            ))
            db.session.commit()

        flash("Complaint submitted successfully!", "success")
        return redirect(url_for("student.my_complaints"))

    return render_template("student/complaint_form.html",
                           categories=sorted(CATEGORIES.keys()))


# ===================================================================
# MY COMPLAINTS LIST
# ===================================================================
@student.route('/my_complaints')
@login_required
def my_complaints():
    complaints = Complaint.query.filter_by(student_id=current_user.id)\
                                .order_by(Complaint.created_at.desc()).all()
    return render_template("student/my_complaints.html", complaints=complaints)


# ===================================================================
# VIEW FULL COMPLAINT DETAILS
# ===================================================================
@student.route('/complaint/<int:cid>')
@login_required
def complaint_view(cid):

    complaint = Complaint.query.get_or_404(cid)

    # Security: student can view only their own complaint
    if complaint.student_id != current_user.id:
        flash("You are not allowed to view this complaint.", "danger")
        return redirect(url_for("student.my_complaints"))

    # Split attachments into list
    files = complaint.attachment.split(",") if complaint.attachment else []

    return render_template("student/complaint_view.html",
                       complaint=complaint,
                       files=files)



# ===================================================================
# VIEW FILES
# ===================================================================
@student.route('/view_file/<path:filename>')
@login_required
def view_file(filename):
    folder = current_app.config['UPLOAD_FOLDER']
    return send_from_directory(folder, filename)


# ===================================================================
# PROFILE
# ===================================================================
@student.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():

    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        pwd = request.form.get("password")

        if name:
            current_user.name = name
        if email:
            current_user.email = email
        if pwd:
            current_user.password = generate_password_hash(pwd)

        db.session.commit()
        flash("Profile updated successfully!", "success")
        return redirect(url_for("student.profile"))

    return render_template("student/profile.html")