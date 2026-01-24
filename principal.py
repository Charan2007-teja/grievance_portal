# principal.py
from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from models import Complaint, User
from extensions import db

principal = Blueprint('principal', __name__, template_folder='templates/principal')




@principal.route('/dashboard')
@login_required
def principal_dashboard():
    if current_user.role != 'principal':
        flash('Access denied', 'danger')
        return redirect('/')

    # All complaints (for table)
    complaints = Complaint.query.order_by(Complaint.created_at.desc()).all()

    # Recent 5 complaints
    recent_complaints = Complaint.query.order_by(Complaint.created_at.desc()).limit(5).all()

    # Counter widgets
    total = Complaint.query.count()
    pending = Complaint.query.filter_by(status='Pending').count()
    in_progress = Complaint.query.filter_by(status='In Progress').count()
    resolved = Complaint.query.filter_by(status='Resolved').count()

    # Department counts
    cse_students = User.query.filter_by(department='CSE', role='student').count()
    ece_students = User.query.filter_by(department='ECE', role='student').count()

    # Complaints by department
    dept_counts = {
        'CSE': Complaint.query.filter_by(department='CSE').count(),
        'ECE': Complaint.query.filter_by(department='ECE').count(),
    }

    # Complaints by category
    from sqlalchemy import func
    category_counts = dict(
        Complaint.query.with_entities(Complaint.category, func.count(Complaint.id)).group_by(Complaint.category).all()
    )

    # Recent student registrations (last 5)
    recent_students = User.query.filter_by(role='student').order_by(User.created_at.desc()).limit(5).all()

    return render_template(
        'principal/dashboard.html',
        complaints=complaints,
        recent_complaints=recent_complaints,
        total=total,
        pending=pending,
        in_progress=in_progress,
        resolved=resolved,
        cse_students=cse_students,
        ece_students=ece_students,
        dept_counts=dept_counts,
        category_counts=category_counts,
        recent_students=recent_students,
        profile=current_user
    )



@principal.route('/all_complaints')
@login_required
def all_complaints():

    if current_user.role != 'principal':
        flash('Access denied', 'danger')
        return redirect('/')

    complaints = Complaint.query.order_by(Complaint.created_at.desc()).all()

    return render_template(
        'principal/all_complaints.html',
        complaints=complaints
    )
