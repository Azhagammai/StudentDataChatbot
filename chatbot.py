import os
import pandas as pd
import pdfplumber
import logging
import google.generativeai as genai
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from flask import Blueprint, render_template, request, session, jsonify, current_app, flash, redirect, url_for
from models import db, Student, ChatLog, UploadedFile
from functools import wraps

# Initialize NLTK components
try:
    nltk.download('punkt')
    nltk.download('stopwords')
except Exception as e:
    print(f"Error downloading NLTK data: {str(e)}")

# Initialize logging
logger = logging.getLogger(__name__)

# Set up Gemini API
api_key = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=api_key)

# Initialize model with generation config
try:
    generation_config = {
        "temperature": 0.2,
        "top_p": 0.8,
        "top_k": 40,
        "max_output_tokens": 1024,
    }
    
    safety_settings = [
        {
            "category": "HARM_CATEGORY_HARASSMENT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        },
        {
            "category": "HARM_CATEGORY_HATE_SPEECH",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        },
        {
            "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        },
        {
            "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        },
    ]
    
    model = genai.GenerativeModel(
        model_name="gemini-pro",
        generation_config=generation_config,
        safety_settings=safety_settings
    )
    logger.info("Gemini AI model initialized successfully")
except Exception as e:
    logger.error(f"Error initializing Gemini AI model: {str(e)}")
    model = None

# Create blueprint
chatbot_bp = Blueprint('chatbot', __name__)

# Login required decorator
def login_required(user_type):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_type' not in session or session['user_type'] != user_type:
                if user_type == 'student':
                    flash('You need to be logged in as a student to access this page', 'danger')
                else:
                    flash('You need to be logged in as an admin to access this page', 'danger')
                return redirect(url_for('login.login_page'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@chatbot_bp.route('/chat', methods=['GET'])
@login_required('student')
def chat():
    student_name = session.get('student_name', 'Student')
    return render_template('chat.html', student_name=student_name)

@chatbot_bp.route('/admin/chat', methods=['GET'])
@login_required('admin')
def admin_chat():
    return render_template('admin_chat.html')

@chatbot_bp.route('/api/chat', methods=['POST'])
def process_chat():
    if 'user_type' not in session:
        return jsonify({'error': 'You must be logged in to use the chatbot'}), 401
        
    data = request.json
    query = data.get('query', '')
    
    if not query:
        return jsonify({'error': 'Empty query'}), 400
    
    user_type = session['user_type']
    user_id = session['user_id']
    
    try:
        # Process the query and get response
        if user_type == 'student':
            response = process_student_query(query, user_id)
        else:  # admin
            response = process_admin_query(query)
            
        # Log the chat
        chat_log = ChatLog()
        chat_log.user_type = user_type
        chat_log.user_id = user_id
        chat_log.query = query
        chat_log.response = response
        db.session.add(chat_log)
        db.session.commit()
        
        return jsonify({'response': response})
    
    except Exception as e:
        logger.error(f"Error processing chat: {str(e)}")
        return jsonify({'error': 'An error occurred while processing your query. Please try a different question.'}), 500

def process_student_query(query, student_id):
    # Get student data
    student = db.session.query(Student).filter(Student.id == student_id).first()
    if not student:
        return "Sorry, I couldn't find your student record."
    
    # Create safe tokenization with simple split for fallback
    try:
        # Try NLTK tokenization first
        tokens = word_tokenize(query.lower())
        stop_words = set(stopwords.words('english'))
        filtered_tokens = [word for word in tokens if word.isalnum() and word not in stop_words]
    except Exception as e:
        # Fallback to simple tokenization if NLTK fails
        logger.error(f"NLTK tokenization failed: {str(e)}")
        tokens = query.lower().split()
        filtered_tokens = [word for word in tokens if len(word) > 2]
    
    # Identify entities and keywords
    keywords = set(filtered_tokens)
    
    # Create student info dictionary manually instead of using __dict__
    student_info = {
        'id': student.id,
        'serial_no': student.serial_no,
        'roll_no': student.roll_no,
        'name': student.name,
        'major': student.major,
        'current_gpa': student.current_gpa,
        'days_present': student.days_present,
        'total_days': student.total_days,
        'days_absent': student.days_absent,
        'courses': student.courses,
        'date_of_birth': str(student.date_of_birth) if student.date_of_birth else None,
        'gender': student.gender,
        'father_name': student.father_name,
        'mother_name': student.mother_name,
        'hobbies': student.hobbies
    }
    
    # Prepare context
    context = {
        "student_info": student_info,
        "query": query,
        "keywords": list(keywords)
    }
    
    # Add code of conduct information if relevant
    if any(word in keywords for word in ['code', 'conduct', 'rule', 'policy', 'attendance']):
        context["code_of_conduct"] = extract_code_of_conduct()
    
    # Add data from uploaded files if relevant
    if any(word in keywords for word in ['report', 'performance', 'grade', 'score']):
        context["uploaded_files_data"] = get_data_from_uploaded_files(student)
    
    # Generate response using Gemini
    prompt = f"""
    You are an educational assistant for Dr. Mahalingam College of Engineering and Technology.
    You need to answer a student's query based on their academic information.
    
    Student Information:
    Name: {student.name}
    Roll Number: {student.roll_no}
    Serial Number: {student.serial_no}
    Major: {student.major}
    Current GPA: {student.current_gpa}
    Attendance: {student.days_present} days present out of {student.total_days} total days
    Courses: {student.courses}
    
    Semester Results:
    Semester 1: {student.sem1}
    Semester 2: {student.sem2}
    Semester 3: {student.sem3}
    Semester 4: {student.sem4}
    Semester 5: {student.sem5}
    Semester 6: {student.sem6}
    
    Personal Information:
    Date of Birth: {student.date_of_birth}
    Gender: {student.gender}
    Father's Name: {student.father_name}
    Mother's Name: {student.mother_name}
    Phone: {student.phone_number}
    Address: {student.street}, {student.city}, {student.state}, {student.pin_code}
    Hobbies: {student.hobbies}
    
    Other Context:
    {context.get('code_of_conduct', '')}
    {context.get('uploaded_files_data', '')}
    
    The student's query is: "{query}"
    
    Please provide a helpful, accurate, and friendly response based ONLY on the information provided.
    Be concise but thorough. If you don't have enough information to answer the query, 
    politely state that you don't have that information.
    """
    
    try:
        if model is None:
            logger.error("Gemini model not initialized")
            return "I'm sorry, I'm having trouble accessing my knowledge base right now. Please try again later."
        
        # Generate response safely
        generation_response = model.generate_content(prompt)
        
        if generation_response and hasattr(generation_response, 'text'):
            return generation_response.text
        else:
            logger.error(f"Invalid response format: {generation_response}")
            return "I'm sorry, I couldn't generate a proper response. Please try a different question."
    except Exception as e:
        logger.error(f"Gemini API error: {str(e)}")
        return "I'm sorry, I'm having trouble processing your request right now. Please try again later."

def process_admin_query(query):
    # Create safe tokenization with simple split for fallback
    try:
        # Try NLTK tokenization first
        tokens = word_tokenize(query.lower())
        stop_words = set(stopwords.words('english'))
        filtered_tokens = [word for word in tokens if word.isalnum() and word not in stop_words]
    except Exception as e:
        # Fallback to simple tokenization if NLTK fails
        logger.error(f"NLTK tokenization failed: {str(e)}")
        tokens = query.lower().split()
        filtered_tokens = [word for word in tokens if len(word) > 2]
    
    # Extract relevant keywords
    keywords = set(filtered_tokens)
    
    # Check if query is about student listings
    students_data = []
    if any(word in keywords for word in ['list', 'show', 'students', 'student']):
        # Get all students
        students = db.session.query(Student).all()
        students_data = [
            {
                'name': student.name,
                'roll_no': student.roll_no,
                'serial_no': student.serial_no,
                'major': student.major,
                'current_gpa': student.current_gpa,
                'attendance': f"{student.days_present}/{student.total_days}",
                'attendance_percentage': round((student.days_present / student.total_days) * 100, 2) if student.total_days > 0 else 0
            } for student in students
        ]
    
    # Generate admin-specific prompt
    prompt = f"""
    You are an administrative assistant for Dr. Mahalingam College of Engineering and Technology.
    An administrator has asked: "{query}"
    
    Based on the available data, here is what I know:
    
    Student data summary:
    - Total students: {Student.query.count()}
    - Students with attendance below 70%: {sum(1 for s in Student.query.all() if s.total_days > 0 and (s.days_present / s.total_days) < 0.7)}
    - Students with GPA above 7: {Student.query.filter(Student.current_gpa > 7).count()}
    
    Uploaded files:
    - Total files: {UploadedFile.query.count()}
    - CSV files: {UploadedFile.query.filter_by(file_type='csv').count()}
    - PDF files: {UploadedFile.query.filter_by(file_type='pdf').count()}
    
    Chat logs:
    - Total queries: {ChatLog.query.count()}
    - Student queries: {ChatLog.query.filter_by(user_type='student').count()}
    - Admin queries: {ChatLog.query.filter_by(user_type='admin').count()}
    
    Student Information (if requested):
    {students_data if students_data else "No specific student data requested."}
    
    Please provide a helpful, accurate, and professional response based ONLY on the information provided.
    Format data as needed to make it readable, and if you're displaying a list of students, 
    organize it in a clear tabular format using markdown.
    
    If you don't have enough information to answer the query, politely state that you don't have that information.
    """
    
    try:
        if model is None:
            logger.error("Gemini model not initialized")
            return "I'm sorry, I'm having trouble accessing my knowledge base right now. Please try again later."
        
        # Generate response safely
        generation_response = model.generate_content(prompt)
        
        if generation_response and hasattr(generation_response, 'text'):
            return generation_response.text
        else:
            logger.error(f"Invalid response format: {generation_response}")
            return "I'm sorry, I couldn't generate a proper response. Please try a different question."
    except Exception as e:
        logger.error(f"Gemini API error: {str(e)}")
        return "I'm sorry, I'm having trouble processing your request right now. Please try again later."

def extract_code_of_conduct():
    try:
        # Read the code of conduct file from PDF
        pdf_path = os.path.join(os.getcwd(), "data", "code_of_conduct.pdf")
        if os.path.exists(pdf_path):
            with pdfplumber.open(pdf_path) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() + "\n"
                return text
        else:
            # If PDF not found, return a generic message about code of conduct
            return """
            Students are expected to follow the college code of conduct which includes:
            - Regular attendance in classes
            - Maintaining proper dress code
            - No use of mobile phones in classrooms
            - Academic honesty
            - Respectful behavior towards faculty and peers
            For more details, please refer to the full Code of Conduct document.
            """
    except Exception as e:
        logger.error(f"Error reading code of conduct PDF: {str(e)}")
        return "Unable to read the code of conduct document due to a technical error. Please refer to the physical copy or ask an administrator."

def get_data_from_uploaded_files(student):
    """Extract relevant data about a student from uploaded files"""
    result = ""
    
    try:
        # Get all uploaded files
        files = UploadedFile.query.all()
        
        for file in files:
            file_path = file.file_path
            
            if file.file_type == 'csv':
                # Extract data from CSV
                try:
                    df = pd.read_csv(file_path)
                    # Check if student info exists in the CSV
                    student_row = df[(df['serial_no'] == student.serial_no) | 
                                    (df['roll_no'] == student.roll_no)]
                    
                    if not student_row.empty:
                        result += f"\nData from {file.filename}:\n"
                        result += str(student_row.to_dict(orient='records')[0])
                except Exception as e:
                    logger.error(f"Error reading CSV file {file.filename}: {str(e)}")
            
            elif file.file_type == 'pdf':
                # Extract data from PDF
                try:
                    with pdfplumber.open(file_path) as pdf:
                        text = ""
                        for page in pdf.pages:
                            text += page.extract_text() + "\n"
                        
                        # Simple check for student name in PDF
                        if student.name.lower() in text.lower() or student.roll_no in text:
                            result += f"\nThe student is mentioned in {file.filename}."
                except Exception as e:
                    logger.error(f"Error reading PDF file {file.filename}: {str(e)}")
    
    except Exception as e:
        logger.error(f"Error accessing uploaded files: {str(e)}")
        
    return result if result else "No additional data found in uploaded files."
