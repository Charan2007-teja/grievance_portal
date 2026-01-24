# hod.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from extensions import db
from models import User, Complaint, ComplaintHistory
import os, uuid

hod = Blueprint('hod', __name__, template_folder='templates/hod')


# ---------------------------------------------------------
# HOD DASHBOARD
# ---------------------------------------------------------
@hod.route('/dashboard')
@login_required
def hod_dashboard():

    if current_user.role != "hod":
        flash("Access denied", "danger")
        return redirect('/')

    complaints = Complaint.query.filter_by(
        assigned_to='hod',
        department=current_user.department
    ).order_by(Complaint.created_at.desc()).all()

    pending_students = User.query.filter_by(
        role='student',
        department=current_user.department,
        approved=False
    ).all()

    approved_students = User.query.filter_by(
        role='student',
        department=current_user.department,
        approved=True
    ).all()

    return render_template(
        "hod/dashboard.html",
        complaints=complaints,
        pending_students=pending_students,
        approved_students=approved_students
    )


# ---------------------------------------------------------
# VIEW COMPLAINT (HOD) ✅ NEW
# ---------------------------------------------------------
@hod.route('/complaint/<int:cid>')
@login_required
def view_complaint(cid):

    if current_user.role != 'hod':
        flash("Access denied", "danger")
        return redirect('/')

    complaint = Complaint.query.get_or_404(cid)

    if complaint.department != current_user.department:
        flash("Unauthorized access", "danger")
        return redirect(url_for('hod.hod_dashboard'))

    return render_template(
        "hod/view_complaint.html",
        complaint=complaint
    )


# ---------------------------------------------------------
# RESPOND (STAGE 1)
# ---------------------------------------------------------
@hod.route('/respond/<int:complaint_id>', methods=['GET', 'POST'])
@login_required
def respond(complaint_id):

    if current_user.role != 'hod':
        flash("Access denied", "danger")
        return redirect('/')

    c = Complaint.query.get_or_404(complaint_id)

    if c.response:
        return redirect(url_for('hod.resolve_complaint', complaint_id=c.id))

    if request.method == "POST":

        response_text = request.form.get("response")
        before_files = request.files.getlist("before_files")
        after_files = request.files.getlist("after_files")

        if not response_text:
            flash("Response cannot be empty!", "danger")
            return redirect(url_for('hod.respond', complaint_id=c.id))

        upload_dir = current_app.config["UPLOAD_FOLDER"]
        os.makedirs(upload_dir, exist_ok=True)

        # BEFORE FILES
        for f in before_files:
            if f.filename:
                ext = os.path.splitext(f.filename)[1]
                new_name = f"BEFORE_{uuid.uuid4().hex}{ext}"
                f.save(os.path.join(upload_dir, new_name))
                c.before_files = ",".join(
                    filter(None, [c.before_files, new_name])
                )

        # AFTER FILES
        for f in after_files:
            if f.filename:
                ext = os.path.splitext(f.filename)[1]
                new_name = f"AFTER_{uuid.uuid4().hex}{ext}"
                f.save(os.path.join(upload_dir, new_name))
                c.after_files = ",".join(
                    filter(None, [c.after_files, new_name])
                )

        c.status = "Resolved" if any(f.filename for f in after_files) else "In Progress"
        c.response = response_text
        c.response_by = current_user.name

        db.session.add(
            ComplaintHistory(
                complaint_id=c.id,
                action="Responded by HOD",
                message=response_text,
                performed_by=current_user.name
            )
        )

        db.session.commit()
        flash("Response submitted!", "success")
        return redirect(url_for('hod.hod_dashboard'))

    return render_template("hod/respond.html", complaint=c)


# ---------------------------------------------------------
# RESOLVE (STAGE 2)
# ---------------------------------------------------------
@hod.route('/resolve/<int:complaint_id>', methods=['GET', 'POST'])
@login_required
def resolve_complaint(complaint_id):

    if current_user.role != 'hod':
        flash("Access denied", "danger")
        return redirect('/')

    c = Complaint.query.get_or_404(complaint_id)

    if c.status == "Resolved":
        flash("Complaint already resolved.", "info")
        return redirect(url_for('hod.hod_dashboard'))

    if request.method == "POST":

        upload_dir = current_app.config["UPLOAD_FOLDER"]
        os.makedirs(upload_dir, exist_ok=True)

        after_files = request.files.getlist("final_files")

        for f in after_files:
            if f.filename:
                ext = os.path.splitext(f.filename)[1]
                new_name = f"AFTER_{uuid.uuid4().hex}{ext}"
                f.save(os.path.join(upload_dir, new_name))
                c.after_files = ",".join(
                    filter(None, [c.after_files, new_name])
                )

        c.status = "Resolved"

        db.session.add(
            ComplaintHistory(
                complaint_id=c.id,
                action="Marked Resolved by HOD",
                message="Final AFTER photos submitted",
                performed_by=current_user.name
            )
        )

        db.session.commit()
        flash("Complaint marked as Resolved!", "success")
        return redirect(url_for('hod.hod_dashboard'))

    return render_template("hod/resolve.html", complaint=c)


# ---------------------------------------------------------
# APPROVE STUDENT
# ---------------------------------------------------------
@hod.route('/approve_student/<int:student_id>')
@login_required
def approve_student(student_id):

    if current_user.role != "hod":
        flash("Access denied", "danger")
        return redirect('/')

    student = User.query.get_or_404(student_id)

    if student.department != current_user.department:
        flash("Unauthorized action!", "danger")
        return redirect(url_for('hod.hod_dashboard'))

    student.approved = True
    db.session.commit()

    flash(f"{student.name} approved successfully!", "success")
    return redirect(url_for('hod.hod_dashboard'))


# ---------------------------------------------------------
# DECLINE STUDENT
# ---------------------------------------------------------
@hod.route('/decline_student/<int:student_id>')
@login_required
def decline_student(student_id):

    if current_user.role != "hod":
        flash("Access denied", "danger")
        return redirect('/')

    student = User.query.get_or_404(student_id)

    if student.department != current_user.department:
        flash("Unauthorized action!", "danger")
        return redirect(url_for('hod.hod_dashboard'))

    db.session.delete(student)
    db.session.commit()

    flash("Student declined and removed!", "info")
    return redirect(url_for('hod.hod_dashboard'))