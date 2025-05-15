import os
import logging
from flask import Flask, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from datetime import timedelta

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create DB base class
class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy with our base
db = SQLAlchemy(model_class=Base)

# Create the Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
app.permanent_session_lifetime = timedelta(days=1)

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///database.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Configure file upload settings
app.config["UPLOAD_FOLDER"] = os.path.join(os.getcwd(), "data", "uploads")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB max file size
app.config["ALLOWED_EXTENSIONS"] = {'csv', 'pdf'}

# Ensure upload directory exists
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# Initialize the database
db.init_app(app)

# Import models and create tables
with app.app_context():
    import models
    db.create_all()
    
    # Create admin user if not exists
    from models import User
    admin = User.query.filter_by(email="admin@example.com").first()
    if not admin:
        admin = User(email="admin@example.com", is_admin=True)
        admin.set_password("admin123")
        db.session.add(admin)
        db.session.commit()
        logger.info("Admin user created.")

# Import blueprints
from login import login_bp
from chatbot import chatbot_bp
from admin import admin_bp

# Register blueprints
app.register_blueprint(login_bp)
app.register_blueprint(chatbot_bp)
app.register_blueprint(admin_bp)

# Root route
@app.route('/')
def index():
    return redirect(url_for('login.login_page'))

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    logger.error(f"404 error: {e}")
    return "Page not found", 404

@app.errorhandler(500)
def internal_server_error(e):
    logger.error(f"500 error: {e}")
    return "Internal server error", 500

# If this file is run directly, start the app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
