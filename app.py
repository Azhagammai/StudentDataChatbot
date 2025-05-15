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
    from models import User, Student
    admin = db.session.query(User).filter(User.email == "admin@example.com").first()
    if not admin:
        admin = User()
        admin.email = "admin@example.com"
        admin.is_admin = True
        admin.set_password("admin123")
        db.session.add(admin)
        db.session.commit()
        logger.info("Admin user created.")
    
    # Import students from CSV if not exists
    if db.session.query(Student).count() == 0:
        try:
            import pandas as pd
            import os
            from datetime import datetime
            
            students_csv_path = os.path.join(os.getcwd(), "data", "students.csv")
            if os.path.exists(students_csv_path):
                df = pd.read_csv(students_csv_path)
                
                for _, row in df.iterrows():
                    student_data = {}
                    for column in df.columns:
                        # Handle semester columns which have spaces in names
                        if column.startswith('Semester'):
                            semester_num = column.split(' ')[1]
                            student_data[f'sem{semester_num}'] = row[column]
                        elif hasattr(Student, column.lower().replace(' ', '_')):
                            student_data[column.lower().replace(' ', '_')] = row[column]
                        elif column.lower().replace(' ', '_') in [c.key for c in Student.__table__.columns]:
                            student_data[column.lower().replace(' ', '_')] = row[column]
                        elif hasattr(Student, column):
                            student_data[column] = row[column]
                    
                    # Convert date_of_birth to datetime if it's a string
                    if 'date_of_birth' in student_data and isinstance(student_data['date_of_birth'], str):
                        try:
                            student_data['date_of_birth'] = datetime.strptime(student_data['date_of_birth'], '%Y-%m-%d').date()
                        except:
                            student_data['date_of_birth'] = None
                    
                    try:
                        student = Student(**student_data)
                        db.session.add(student)
                    except Exception as e:
                        logger.error(f"Error adding student {student_data.get('name')}: {str(e)}")
                
                db.session.commit()
                logger.info(f"Imported {len(df)} students from CSV")
        except Exception as e:
            logger.error(f"Error importing students from CSV: {str(e)}")

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
