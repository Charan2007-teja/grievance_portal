import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:rdbms@localhost/grievance_portal"
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret")

SQLALCHEMY_TRACK_MODIFICATIONS = False

UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")

# Use this ONLY for emergency login.
MASTER_PASSWORD = os.environ.get("MASTER_PASSWORD", "SDPT@123")
