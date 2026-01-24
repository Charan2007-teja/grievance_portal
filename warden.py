# warden.py (FINAL CLEAN VERSION)
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from extensions import db
from models import Complaint, ComplaintHistory
import os, uuid

warden = Blueprint('warden', __name__, template_folder='templates/warden')


# =============================================================
# WARDEN DASHBOARD
# =============================================================
@warden.route('/dashboard')
@login_required
def warden_dashboard():

    if current_user.role != 'warden':
        flash("Access denied", "danger")
        return redirect('/')

    complaints = Complaint.query.filter_by(
        assigned_to='warden'
    ).order_by(Complaint.created_at.desc()).all()

    return render_template("warden/dashboard.html", complaints=complaints)



# =============================================================
# RESPOND (Stage 1 — BEFORE WORK ONLY)
# =============================================================
@warden.route('/respond/<int:complaint_id>', methods=['GET', 'POST'])
@login_required
def respond(complaint_id):

    if current_user.role != 'warden':
        flash("Access denied", "danger")
        return redirect('/')

    c = Complaint.query.get_or_404(complaint_id)

    # Cannot respond again if already resolved
    if c.status == "Resolved":
        flash("This complaint is already resolved.", "info")
        return redirect(url_for("warden.warden_dashboard"))

    # If already in progress → go to final resolve page
    if c.status == "In Progress":
        return redirect(url_for("warden.resolve_complaint", complaint_id=c.id))

    if request.method == "POST":

        response_text = request.form.get("response")
        before_files = request.files.getlist("before_files")

        if not response_text:
            flash("Response cannot be empty!", "danger")
            return redirect(url_for('warden.respond', complaint_id=c.id))

        upload_dir = current_app.config.get("UPLOAD_FOLDER", "uploads")
        os.makedirs(upload_dir, exist_ok=True)

        saved_before = []

        # Save BEFORE files
        for f in before_files:
            if f and f.filename:
                ext = os.path.splitext(f.filename)[1]
                new_name = f"BEFORE_{uuid.uuid4().hex}{ext}"
                f.save(os.path.join(upload_dir, new_name))
                saved_before.append(new_name)

        # Merge into before_files column
        if saved_before:
            existing = c.before_files.split(",") if c.before_files else []
            c.before_files = ",".join(existing + saved_before)

        # Update complaint
        c.status = "In Progress"
        c.response = response_text
        c.response_by = current_user.name

        db.session.add(c)

        # History entry
        h = ComplaintHistory(
            complaint_id=c.id,
            action="Responded by Warden (Before Work)",
            message=response_text,
            performed_by=current_user.name
        )
        db.session.add(h)

        db.session.commit()

        flash("Response submitted! Work now In Progress.", "success")
        return redirect(url_for("warden.warden_dashboard"))

    return render_template("warden/respond.html", complaint=c)



# =============================================================
# RESOLVE (Stage 2 — AFTER WORK ONLY)
# =============================================================
@warden.route('/resolve/<int:complaint_id>', methods=['GET', 'POST'])
@login_required
def resolve_complaint(complaint_id):

    if current_user.role != 'warden':
        flash("Access denied", "danger")
        return redirect('/')

    c = Complaint.query.get_or_404(complaint_id)

    # If already resolved → stop
    if c.status == "Resolved":
        flash("Already resolved!", "info")
        return redirect(url_for("warden.warden_dashboard"))

    if request.method == "POST":

        upload_dir = current_app.config.get("UPLOAD_FOLDER", "uploads")
        os.makedirs(upload_dir, exist_ok=True)

        final_files = request.files.getlist("final_files")
        saved_after = []

        # Save AFTER files
        for f in final_files:
            if f and f.filename:
                ext = os.path.splitext(f.filename)[1]
                new_name = f"AFTER_{uuid.uuid4().hex}{ext}"
                f.save(os.path.join(upload_dir, new_name))
                saved_after.append(new_name)

        # Merge into after_files column
        if saved_after:
            existing = c.after_files.split(",") if c.after_files else []
            c.after_files = ",".join(existing + saved_after)

        # Mark resolved
        c.status = "Resolved"

        db.session.add(c)

        # History entry
        h = ComplaintHistory(
            complaint_id=c.id,
            action="Resolved by Warden",
            message="AFTER work proof submitted",
            performed_by=current_user.name
        )
        db.session.add(h)

        db.session.commit()

        flash("Complaint resolved successfully!", "success")
        return redirect(url_for("warden.warden_dashboard"))

    return render_template("warden/resolve.html", complaint=c)
