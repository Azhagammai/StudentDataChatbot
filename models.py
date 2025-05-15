from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    serial_no = db.Column(db.Integer, nullable=False)
    roll_no = db.Column(db.String(10), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    street = db.Column(db.String(200))
    city = db.Column(db.String(100))
    state = db.Column(db.String(50))
    pin_code = db.Column(db.String(10))
    father_name = db.Column(db.String(100))
    mother_name = db.Column(db.String(100))
    phone_number = db.Column(db.String(20))
    total_days = db.Column(db.Integer)
    days_present = db.Column(db.Integer)
    days_absent = db.Column(db.Integer)
    major = db.Column(db.String(100))
    current_gpa = db.Column(db.Float)
    courses = db.Column(db.String(500))
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(10))
    hobbies = db.Column(db.String(200))
    sem1 = db.Column(db.Float)
    sem2 = db.Column(db.Float)
    sem3 = db.Column(db.Float)
    sem4 = db.Column(db.Float)
    sem5 = db.Column(db.Float)
    sem6 = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('serial_no', 'roll_no', name='unique_student'),
    )

class UploadedFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_type = db.Column(db.String(10), nullable=False)  # 'csv' or 'pdf'
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

class ChatLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_type = db.Column(db.String(10))  # 'student' or 'admin'
    user_id = db.Column(db.Integer)  # student serial_no or admin id
    query = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_type': self.user_type,
            'user_id': self.user_id,
            'query': self.query,
            'response': self.response,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        }
