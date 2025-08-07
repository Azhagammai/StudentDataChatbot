# 🎓 AI-Powered Student Data Chatbot

EduBot is a smart assistant that helps manage student information using a chatbot interface. Built using Python and Flask, it allows admins to interact with student data easily using conversational commands. The goal is to bring automation and convenience into educational data management.

---

## 🔥 Key Features

- 🔐 Secure **Admin Login**
- 💬 Chatbot-based interface for student queries
- 📄 View, Add, Update, Delete student records
- 📁 Extract student data from PDFs using OCR
- 🧠 Natural Language Processing with **NLTK**
- 📊 Store data with **SQLAlchemy**
- ☁️ Runs on **Flask server** (local or cloud)

---

## 🚀 Tech Stack

| Area            | Technology                         |
|-----------------|-------------------------------------|
| Backend         | Python 3.13, Flask                 |
| Database        | SQLite (via SQLAlchemy)           |
| Session Mgmt    | Flask-Login, Flask-Session        |
| Forms & Auth    | Flask-WTF, Werkzeug, Email Validator |
| AI & Chatbot    | Google Generative AI (Gemini), NLTK |
| PDF Parsing     | pdfplumber                         |
| Deployment      | Replit or localhost                |

---

## 🗂️ Project Structure

```bash
StudentDataChatbot/
│
├── .env # Environment variables
├── admin.py # Admin panel logic
├── app.py # Flask app configuration
├── chatbot.py # Chatbot logic using Gemini AI
├── login.py # Login system using Flask-Login
├── main.py # App launcher
├── models.py # Data model (SQLAlchemy)
├── pyproject.toml # Project dependencies
├── static/ # Static files (CSS, JS)
├── templates/ # HTML templates (Jinja2)
├── uploads/ # Uploaded PDF files
└── README.md # Project description

```
---

## 🛠️ Setup Instructions

### Step 1: 📦 Install Dependencies

Open your terminal and run the following command inside your project directory:

step 1: 
pip install flask flask-sqlalchemy flask-session flask-login flask-wtf google-generativeai pandas pdfplumber python-dotenv werkzeug email-validator nltk

Step 2: ▶️ Run the App
Navigate into the project folder and run the main application:


cd StudentDataChatbot
python main.py

Step 3: 🌐 Access in Browser
Once running, you’ll see output like this:


 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
 * Running on http://10.16.198.150:5000

Open your browser and visit:

http://127.0.0.1:5000

