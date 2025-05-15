import os
import pandas as pd
import logging
import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, current_app
from werkzeug.utils import secure_filename
from models import db, Student, UploadedFile, ChatLog
from functools import wraps

# Initialize logging
logger = logging.getLogger(__name__)

# Create blueprint
admin_bp = Blueprint('admin', __name__)

# Admin required decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_type' not in session or session['user_type'] != 'admin':
            flash('You need to be logged in as an admin to access this page', 'danger')
            return redirect(url_for('login.login_page'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/admin/dashboard')
@admin_required
def dashboard():
    # Get statistics for the dashboard
    total_students = db.session.query(Student).count()
    total_uploads = db.session.query(UploadedFile).count()
    total_chats = db.session.query(ChatLog).count()
    
    # Get chat logs for the last 7 days
    seven_days_ago = datetime.datetime.utcnow() - datetime.timedelta(days=7)
    recent_chats = db.session.query(ChatLog).filter(ChatLog.timestamp >= seven_days_ago).order_by(ChatLog.timestamp.desc()).all()
    
    # Group by day
    chat_data = {}
    for chat in recent_chats:
        day = chat.timestamp.strftime('%Y-%m-%d')
        chat_data[day] = chat_data.get(day, 0) + 1
    
    # Format for chart
    chart_labels = list(chat_data.keys())
    chart_data = list(chat_data.values())
    
    return render_template('admin.html', 
                           total_students=total_students,
                           total_uploads=total_uploads,
                           total_chats=total_chats,
                           chart_labels=chart_labels,
                           chart_data=chart_data)

@admin_bp.route('/admin/upload', methods=['GET', 'POST'])
@admin_required
def upload():
    if request.method == 'POST':
        # Check if file is part of the request
        if 'file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
            
        file = request.files['file']
        
        # Check if a file is selected
        if file.filename == '':
            flash('No file selected', 'danger')
            return redirect(request.url)
            
        # Check file type
        allowed_extensions = current_app.config['ALLOWED_EXTENSIONS']
        if not allowed_file(file.filename, allowed_extensions):
            flash(f'File type not allowed. Allowed types: {", ".join(allowed_extensions)}', 'danger')
            return redirect(request.url)
            
        # Save the file
        try:
            filename = secure_filename(file.filename)
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # Determine file type
            file_extension = filename.rsplit('.', 1)[1].lower()
            
            # Create record in database
            uploaded_file = UploadedFile(
                filename=filename,
                file_path=file_path,
                file_type=file_extension,
                uploaded_by=session['user_id']
            )
            db.session.add(uploaded_file)
            
            # If it's a CSV, check if it has student data and import
            if file_extension == 'csv':
                try:
                    import_student_data(file_path)
                except Exception as e:
                    logger.error(f"Error importing student data: {str(e)}")
                    flash(f'File uploaded but there was an error importing student data: {str(e)}', 'warning')
            
            db.session.commit()
            flash('File uploaded successfully', 'success')
            return redirect(url_for('admin.upload'))
            
        except Exception as e:
            logger.error(f"File upload error: {str(e)}")
            flash(f'Error uploading file: {str(e)}', 'danger')
            return redirect(request.url)
    
    # GET request - show upload form
    files = UploadedFile.query.order_by(UploadedFile.uploaded_at.desc()).all()
    return render_template('upload.html', files=files)

@admin_bp.route('/admin/students', methods=['GET'])
@admin_required
def list_students():
    students = db.session.query(Student).all()
    return jsonify([{
        'id': student.id,
        'serial_no': student.serial_no,
        'roll_no': student.roll_no,
        'name': student.name,
        'major': student.major,
        'current_gpa': student.current_gpa,
        'attendance': f"{student.days_present}/{student.total_days}",
        'attendance_percentage': round((student.days_present / student.total_days) * 100, 2) if student.total_days > 0 else 0
    } for student in students])

@admin_bp.route('/admin/students/<int:student_id>', methods=['DELETE'])
@admin_required
def delete_student(student_id):
    student = db.session.query(Student).filter(Student.id == student_id).first()
    if not student:
        return jsonify({'success': False, 'message': 'Student not found'}), 404
        
    try:
        db.session.delete(student)
        db.session.commit()
        return jsonify({'success': True, 'message': f'Student {student.name} deleted successfully'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting student: {str(e)}")
        return jsonify({'success': False, 'message': f'Error deleting student: {str(e)}'}), 500

@admin_bp.route('/admin/chatlogs', methods=['GET'])
@admin_required
def get_chat_logs():
    logs = db.session.query(ChatLog).order_by(ChatLog.timestamp.desc()).all()
    return jsonify([log.to_dict() for log in logs])

def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def import_student_data(file_path):
    """Import student data from CSV file"""
    try:
        df = pd.read_csv(file_path)
        
        # Check if it has required columns
        required_columns = ['serial_no', 'roll_no', 'name']
        if not all(col in df.columns for col in required_columns):
            logger.warning(f"CSV missing required columns: {required_columns}")
            return
        
        # Import students
        for _, row in df.iterrows():
            # Check if student already exists
            existing_student = Student.query.filter_by(
                serial_no=row['serial_no'], 
                roll_no=row['roll_no']
            ).first()
            
            if existing_student:
                # Update existing student
                for column in df.columns:
                    if hasattr(existing_student, column) and column in row:
                        setattr(existing_student, column, row[column])
            else:
                # Create new student
                student_data = {}
                for column in df.columns:
                    # Handle semester columns which have spaces in names
                    if column.startswith('Semester'):
                        semester_num = column.split(' ')[1]
                        student_data[f'sem{semester_num}'] = row[column]
                    elif hasattr(Student, column):
                        student_data[column] = row[column]
                
                # Create the student
                student = Student(**student_data)
                db.session.add(student)
        
        db.session.commit()
        logger.info(f"Imported {len(df)} students from CSV")
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error importing student data: {str(e)}")
        raise
