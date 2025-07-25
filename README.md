# Online Task & Productivity Tracker – Web Application

A user-friendly and professional web application built with Flask to help individuals manage tasks, monitor productivity, track time spent, and visualize progress through real-time analytics. This project was developed as part of a structured 45-day milestone.

## 🚀 Features

- 🔐 Google OAuth & Email/Password-based login system  
- ✅ Task creation, editing, and deletion with priorities and due dates  
- ⏱️ Start, pause, and log time spent on each task  
- 📊 Analytics dashboard with charts (daily, monthly, status, priority)  
- 🔍 Search and filter tasks by name, status, or priority  
- 📤 Export reports in **PDF** and **CSV** formats  
- 📱 Responsive design for desktop and mobile browsers

## 🛠️ Tech Stack

| Layer        | Technologies Used                          |
|--------------|---------------------------------------------|
| Backend      | Python, Flask, SQLAlchemy, Flask-Login      |
| Frontend     | HTML5, CSS3, JavaScript, Chart.js           |
| Authentication | Google OAuth 2.0 (Authlib), Flask-Login |
| Database     | SQLite                                      |
| Data Export  | jsPDF, pandas                               |


## 📁 Project Structure
productivity_tracker_demo/
├── app.py
├── config.py
├── init_db.py
├── models.py
├── requirements.txt
├── .gitignore
├── README.md
├── static/
│ ├── css/
│ ├── js/
│ └── images/
├── templates/
│ ├── base.html
│ ├── home.html
│ ├── login.html
│ ├── signup.html
│ ├── dashboard.html
│ └── about.html

## 🧪 Setup Guide
### 1. Clone the Repository : git clone https://github.com/pokalapavan2004/Online-Task-Productivity-Tracker-Web-Application.git
                              cd Online-Task-Productivity-Tracker-Web-Application

### 2. Create and Activate Virtual Environment (Windows): python -m venv venv
                                                          venv\Scripts\activate

### 3. Install Dependencies : pip install -r requirements.txt
### 4. Add Google OAuth Credentials : Download client_secret.json from Google Cloud Console and place it in the root of your project:
                                      productivity_tracker_demo/
                                      ├── app.py
                                      ├── client_secret.json  ✅ Place here
                                      ⚠️ Note: This file is excluded from GitHub for security via .gitignore
                                      
### 5. Initialize the Database  : python init_db.py
### 6. Run the Application : python app.py
### Visit in your browser: 🔗 http://localhost:5001

## 🔒 Security & .gitignore
To protect sensitive and local-only files, the following are excluded from GitHub:
client_secret.json
users.db
venv/
__pycache__/
*.pyc

## ✅ Deliverables
1. Google OAuth & Email-based authentication  
2. Per-task time tracking  
3. Real-time analytics and insights  
4. Exportable task reports (PDF, CSV)  
5. Clean and responsive user interface  
6. Secure and maintainable codebase

## 👤 Author
Developer: POKALA PAVAN NAGA MANIKANTA
GitHub: @pokalapavan2004
Email: pavanpokala2004@gmail.com

## 📄 License
This project is intended for educational and demonstration purposes only. Commercial use is not allowed without prior approval.




