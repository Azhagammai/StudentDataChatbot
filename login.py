import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import db, User, Student

login_bp = Blueprint('login', __name__)
logger = logging.getLogger(__name__)

@login_bp.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        login_type = request.form.get('login_type')
        
        if login_type == 'student':
            return handle_student_login()
        elif login_type == 'admin':
            return handle_admin_login()
        else:
            flash('Invalid login type', 'danger')
            
    return render_template('login.html')

def handle_student_login():
    serial_no = request.form.get('serial_no')
    roll_no = request.form.get('roll_no')
    
    if not serial_no or not roll_no:
        flash('Please provide both serial number and roll number', 'danger')
        return render_template('login.html')
    
    try:
        serial_no = int(serial_no)
    except ValueError:
        flash('Serial number must be a number', 'danger')
        return render_template('login.html')
        
    # Check if student exists
    student = db.session.query(Student).filter(Student.serial_no == serial_no, Student.roll_no == roll_no).first()
    
    if student:
        session.permanent = True
        session['user_type'] = 'student'
        session['user_id'] = student.id
        session['student_serial'] = student.serial_no
        session['student_roll'] = student.roll_no
        session['student_name'] = student.name
        
        logger.info(f"Student login successful: {student.name}")
        return redirect(url_for('chatbot.chat'))
    else:
        flash('Invalid credentials. Please try again.', 'danger')
        return render_template('login.html')

def handle_admin_login():
    email = request.form.get('email')
    password = request.form.get('password')
    
    if not email or not password:
        flash('Please provide both email and password', 'danger')
        return render_template('login.html')
        
    # Check if admin exists
    admin = db.session.query(User).filter(User.email == email).first()
    
    if admin and admin.check_password(password):
        if not admin.is_admin:
            flash('You do not have administrative privileges', 'danger')
            return render_template('login.html')
            
        session.permanent = True
        session['user_type'] = 'admin'
        session['user_id'] = admin.id
        session['admin_email'] = admin.email
        
        logger.info(f"Admin login successful: {admin.email}")
        return redirect(url_for('admin.dashboard'))
    else:
        flash('Invalid credentials. Please try again.', 'danger')
        return render_template('login.html')

@login_bp.route('/logout')
def logout():
    user_type = session.get('user_type')
    
    session.clear()
    flash('You have been logged out successfully', 'success')
    
    logger.info(f"{user_type} logged out")
    return redirect(url_for('login.login_page'))
