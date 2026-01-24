from flask import Flask, render_template
from flask_login import LoginManager
from extensions import db
from models import User
import os

# Import Blueprints
from auth import auth
from student import student
from hod import hod
from ao import ao
from principal import principal

import warden as warden_module
warden = warden_module.warden


# -----------------------------------------
# CREATE APP
# -----------------------------------------
app = Flask(__name__)
app.config.from_object("config")


# -----------------------------------------
# ENSURE UPLOAD FOLDER EXISTS
# -----------------------------------------
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


# -----------------------------------------
# INITIALIZE DATABASE
# -----------------------------------------
db.init_app(app)


# -----------------------------------------
# LOGIN MANAGER
# -----------------------------------------
login_manager = LoginManager()
login_manager.login_view = "auth.login"     # If not logged in → redirect to login
login_manager.init_app(app)


@login_manager.user_loader
def load_user(uid):
    return User.query.get(int(uid))


# -----------------------------------------
# REGISTER BLUEPRINTS
# -----------------------------------------
app.register_blueprint(auth, url_prefix="/auth")
app.register_blueprint(student, url_prefix="/student")
app.register_blueprint(hod, url_prefix="/hod")
app.register_blueprint(ao, url_prefix="/ao")
app.register_blueprint(principal, url_prefix="/principal")
app.register_blueprint(warden, url_prefix="/warden")


# -----------------------------------------
# HOME PAGE
# -----------------------------------------
@app.route("/")
def index():
    return render_template("index.html")


# -----------------------------------------
# RUN THE APP
# -----------------------------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
