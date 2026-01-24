# ao.py (FINAL FIXED VERSION — SAME LOGIC AS WARDEN & HOD)
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from extensions import db
from models import Complaint, ComplaintHistory
import os, uuid

ao = Blueprint('ao', __name__, template_folder='templates/ao')


# ========================================================
# AO DASHBOARD
# ========================================================
@ao.route('/dashboard')
@login_required
def ao_dashboard():

    if current_user.role != 'ao':
        flash('Access denied', 'danger')
        return redirect('/')

    complaints = Complaint.query.filter_by(
        assigned_to='ao'
    ).order_by(Complaint.created_at.desc()).all()

    return render_template('ao/dashboard.html', complaints=complaints)



# ========================================================
# RESPOND (Stage 1 — BEFORE WORK)
# ========================================================
@ao.route('/respond/<int:complaint_id>', methods=['GET', 'POST'])
@login_required
def respond(complaint_id):

    if current_user.role != 'ao':
        flash("Access denied", "danger")
        return redirect('/')

    c = Complaint.query.get_or_404(complaint_id)

    # 🔒 Already resolved — no more responding
    if c.status == "Resolved":
        flash("This complaint is already resolved.", "info")
        return redirect(url_for('ao.ao_dashboard'))

    # If already responded, go to resolve page
    if c.status == "In Progress":
        return redirect(url_for('ao.resolve_complaint', complaint_id=c.id))

    if request.method == "POST":

        response_text = request.form.get("response")
        before_uploads = request.files.getlist("before_attachments")
        after_uploads = request.files.getlist("after_attachments")

        if not response_text:
            flash("Response cannot be empty.", "danger")
            return redirect(url_for('ao.respond', complaint_id=c.id))

        upload_dir = current_app.config.get("UPLOAD_FOLDER", "uploads")
        os.makedirs(upload_dir, exist_ok=True)

        # -----------------------------
        # SAVE BEFORE FILES
        # -----------------------------
        before_list = []
        for f in before_uploads:
            if f and f.filename:
                ext = os.path.splitext(f.filename)[1]
                new_name = f"BEFORE_{uuid.uuid4().hex}{ext}"
                f.save(os.path.join(upload_dir, new_name))
                before_list.append(new_name)

        if before_list:
            existing = c.before_files.split(",") if c.before_files else []
            c.before_files = ",".join(existing + before_list)

        # -----------------------------
        # SAVE AFTER FILES (Stage 1)
        # -----------------------------
        after_list = []
        for f in after_uploads:
            if f and f.filename:
                ext = os.path.splitext(f.filename)[1]
                new_name = f"AFTER_{uuid.uuid4().hex}{ext}"
                f.save(os.path.join(upload_dir, new_name))
                after_list.append(new_name)

        if after_list:
            existing = c.after_files.split(",") if c.after_files else []
            c.after_files = ",".join(existing + after_list)

        # -----------------------------
        # SET STATUS
        # -----------------------------
        c.status = "In Progress"
        c.response = response_text
        c.response_by = current_user.name

        # History record
        history = ComplaintHistory(
            complaint_id=c.id,
            action="Responded by AO (Before Work)",
            message=response_text,
            performed_by=current_user.name
        )

        db.session.add(history)
        db.session.add(c)
        db.session.commit()

        flash("Response submitted! Work now In Progress.", "success")
        return redirect(url_for('ao.ao_dashboard'))

    return render_template("ao/respond.html", complaint=c)



# ========================================================
# RESOLVE (Stage 2 — AFTER WORK)
# ========================================================
@ao.route('/resolve/<int:complaint_id>', methods=['GET', 'POST'])
@login_required
def resolve_complaint(complaint_id):

    if current_user.role != 'ao':
        flash("Access denied", "danger")
        return redirect('/')

    c = Complaint.query.get_or_404(complaint_id)

    if c.status == "Resolved":
        flash("Already resolved!", "info")
        return redirect(url_for('ao.ao_dashboard'))

    if request.method == "POST":

        upload_dir = current_app.config.get("UPLOAD_FOLDER", "uploads")
        os.makedirs(upload_dir, exist_ok=True)

        uploaded_files = request.files.getlist("final_files")
        after_list = []

        # SAVE FINAL AFTER FILES
        for f in uploaded_files:
            if f and f.filename:
                ext = os.path.splitext(f.filename)[1]
                fname = f"AFTER_{uuid.uuid4().hex}{ext}"
                f.save(os.path.join(upload_dir, fname))
                after_list.append(fname)

        if after_list:
            existing = c.after_files.split(",") if c.after_files else []
            c.after_files = ",".join(existing + after_list)

        c.status = "Resolved"

        history = ComplaintHistory(
            complaint_id=c.id,
            action="Resolved by AO",
            message="Final AFTER files submitted",
            performed_by=current_user.name
        )

        db.session.add(history)
        db.session.add(c)
        db.session.commit()

        flash("Complaint marked as RESOLVED!", "success")
        return redirect(url_for('ao.ao_dashboard'))

    return render_template("ao/resolve.html", complaint=c)
