from extensions import db
from models import User
from werkzeug.security import generate_password_hash
from app import app

with app.app_context():
    db.create_all()
    admins = [
        dict(name='CSE HOD', email='csehod@example.com', pin=None, password=generate_password_hash('csehod123'), department='CSE', role='hod', approved=True),
        dict(name='ECE HOD', email='ecehod@example.com', pin=None, password=generate_password_hash('ecehod123'), department='ECE', role='hod', approved=True),
        dict(name='Principal', email='principal@example.com', pin=None, password=generate_password_hash('principal123'), department=None, role='principal', approved=True),
        dict(name='Hostel Warden', email='warden@example.com', pin=None, password=generate_password_hash('warden123'), department=None, role='warden', approved=True),
        dict(name='Accounts Officer', email='ao@example.com', pin=None, password=generate_password_hash('ao123'), department=None, role='ao', approved=True),
    ]
    for a in admins:
        if not User.query.filter_by(email=a['email']).first():
            u = User(
                name=a['name'],
                email=a['email'],
                pin=a['pin'],
                password=a['password'],
                department=a['department'],
                role=a['role'],
                approved=a['approved']
            )
            db.session.add(u)

    db.session.commit()
    print('Admins created / existed.')
