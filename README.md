# 🎓 Student Data Organizer
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

Step 1:  📦 Install Dependencies
```bash
pip install flask flask-sqlalchemy flask-session flask-login flask-wtf google-generativeai pandas pdfplumber python-dotenv werkzeug email-validator nltk
```
Step 2: ▶️ Run the App
Navigate into the project folder and run the main application:
```bash
cd StudentDataOrganizer
python main.py
```

Step 3: 🌐 Access in Browser
Once running, you’ll see output like this:

```bash
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
 * Running on http://10.16.198.150:5000
```

Open your browser and visit:

http://127.0.0.1:5000

---
## 📸 SnapShot 
<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/47651b7c-21df-4ae5-bb3d-95a97a9f9f8b" />
<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/79f1b4ad-9c99-4e72-96f1-6dec572a58d3" />
<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/02df1b1d-e271-4b2b-abc8-f89f8f4f2991" />
<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/9d26b9ef-0c26-443a-83ae-d972564e85ee" />
<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/14c77d4d-08aa-4406-b08b-41431b7acdf9" />
<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/e11e3b2d-aceb-443f-a5f6-f466b8748ad7" />
<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/a6939f41-c0db-40c2-8fdc-fec46c58d15a" />








