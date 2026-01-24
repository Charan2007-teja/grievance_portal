from extensions import db
from flask_login import UserMixin
from datetime import datetime

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    pin = db.Column(db.String(32), unique=True, nullable=True, index=True)
    password = db.Column(db.String(255), nullable=False)
    department = db.Column(db.String(10), nullable=True, index=True)
    role = db.Column(db.String(20), nullable=False, default='student', index=True)
    approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())

    complaints = db.relationship(
        'Complaint', backref='student', lazy=True,
        cascade='all, delete-orphan', passive_deletes=True
    )

    notifications = db.relationship(
        'Notification', backref='user', lazy=True,
        cascade='all, delete-orphan', passive_deletes=True
    )


class Complaint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)

    # Student attachments
    attachment = db.Column(db.Text, nullable=True)

    # Staff attachments (NEW!)
    before_files = db.Column(db.Text, nullable=True)   # BEFORE work images
    after_files = db.Column(db.Text, nullable=True)    # AFTER work images

    response = db.Column(db.Text, nullable=True)
    response_by = db.Column(db.String(50), nullable=True)

    status = db.Column(db.String(50), default='Pending')
    assigned_to = db.Column(db.String(20), nullable=True)
    department = db.Column(db.String(10), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=db.func.now())
    resolved_at = db.Column(db.DateTime, nullable=True)

    student_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id', ondelete='CASCADE'),
        nullable=False, index=True
    )


class ComplaintHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    complaint_id = db.Column(
        db.Integer, 
        db.ForeignKey('complaint.id', ondelete='CASCADE'),
        nullable=False, index=True
    )

    action = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=True)
    performed_by = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    complaint = db.relationship(
        'Complaint',
        backref=db.backref('history', lazy='dynamic')
    )


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id', ondelete='CASCADE'),
        nullable=False, index=True
    )

    message = db.Column(db.String(255), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())
