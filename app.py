from flask import Flask, render_template, redirect, url_for, session, request, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from authlib.integrations.flask_client import OAuth, OAuthError
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from config import Config
from models import db, User, Task
import json, os
import csv
from flask import Response
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io
from collections import defaultdict
from datetime import datetime, timedelta


# App Initialization 
app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

# Login Manager 
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login_page'

# Google OAuth code
oauth = OAuth(app)
with open('client_secret.json', 'r') as f:
    credentials = json.load(f)['web']

google = oauth.register(
    name='google',
    client_id=credentials['client_id'],
    client_secret=credentials['client_secret'],
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

# User Loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ROUTS

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        print(f"\n[LOGIN DEBUG] Email entered: {email}")

        # Show all users with that email
        users = User.query.filter_by(email=email).all()
        print("[LOGIN DEBUG] Matching users in DB:")
        for u in users:
            print(f" - {u.email} | provider={u.provider} | password_exists={'Yes' if u.password else 'No'}")

        # Actual login logic
        user = User.query.filter_by(email=email, provider='local').first()

        if user and user.password:
            if check_password_hash(user.password, password):
                print("[LOGIN DEBUG]  Password matched, logging in.")
                login_user(user)
                return redirect(url_for('dashboard'))
            else:
                print("[LOGIN DEBUG]  Incorrect password.")
                flash("Incorrect password", "danger")
        else:
            print("[LOGIN DEBUG]  User not found or provider mismatch.")
            flash("User not found or registered with Google", "danger")

    return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email is already registered. Please log in.', 'warning')
            return redirect(url_for('login_page'))

        hashed_password = generate_password_hash(password)
        user = User(name=name, email=email, password=hashed_password, provider='local')
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for('dashboard'))

    return render_template('signup.html')

@app.route('/login/google')
def login_with_google():
    session.pop('_google_authlib_state_', None)  # Clear CSRF token if present
    redirect_uri = url_for('authorize', _external=True)
    return google.authorize_redirect(redirect_uri, prompt='select_account')

@app.route('/authorize')
def authorize():
    try:
        token = google.authorize_access_token()
        resp = google.get('https://www.googleapis.com/oauth2/v1/userinfo')
        user_info = resp.json()

        user = User.query.filter_by(email=user_info['email']).first()
        if not user:
            user = User(
                name=user_info['name'],
                email=user_info['email'],
                password=None,
                provider='google'
            )
            db.session.add(user)
            db.session.commit()

        login_user(user)

        # Store minimal info in session if needed
        session['user_name'] = user.name
        session['user_id'] = user.id

        return redirect(url_for('dashboard'))

    except OAuthError as e:
        return f"OAuth error: {str(e)}", 400
    except Exception as e:
        return f"Unexpected error: {str(e)}", 500


@app.route('/dashboard')
@login_required
def dashboard():
    tasks = Task.query.filter_by(user_id=current_user.id).all()

    total_tasks = len(tasks)
    completed_tasks = sum(1 for task in tasks if task.completed)
    pending_tasks = total_tasks - completed_tasks
    total_time = sum(task.time_spent for task in tasks)

    #  Daily analytics  7 days max
    today = datetime.today()
    daily_data = []
    daily_labels = []
    
    for i in range(6, -1, -1):  # Last 7 days
        date = today - timedelta(days=i)
        day_tasks = [task for task in tasks if task.created_at.date() == date.date()]
        daily_data.append(len(day_tasks))
        daily_labels.append(date.strftime('%m/%d'))

    #  Monthly analytics  6 months max
    monthly_data = []
    monthly_labels = []
    
    for i in range(5, -1, -1):  # Last 6 months
        date = today - timedelta(days=30*i)
        month_start = date.replace(day=1)
        next_month = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1)
        
        month_tasks = [task for task in tasks if month_start <= task.created_at < next_month]
        monthly_data.append(len(month_tasks))
        monthly_labels.append(date.strftime('%b %Y'))

    # Priority distribution
    priority_data = {
        'High': len([task for task in tasks if task.priority == 'High']),
        'Medium': len([task for task in tasks if task.priority == 'Medium']),
        'Low': len([task for task in tasks if task.priority == 'Low'])
    }

    # Completion rate data
    completion_data = {
        'completed': completed_tasks,
        'pending': pending_tasks
    }

    #  Time analysis (estimated vs actual for completed tasks)
    completed_with_actual = [task for task in tasks if task.completed and task.actual_time_spent]
    time_labels = [task.title[:15] + '...' if len(task.title) > 15 else task.title for task in completed_with_actual[:2]]
    estimated_times = [task.time_spent for task in completed_with_actual[:2]]
    actual_times = [task.actual_time_spent for task in completed_with_actual[:2]]

    return render_template(
        'dashboard.html',
        tasks=tasks,
        current_user=current_user,
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        pending_tasks=pending_tasks,
        total_time=total_time,
        daily_labels=daily_labels,
        daily_data=daily_data,
        monthly_labels=monthly_labels,
        monthly_data=monthly_data,
        priority_data=priority_data,
        completion_data=completion_data,
        time_labels=time_labels,
        estimated_times=estimated_times,
        actual_times=actual_times
    )

from flask_login import login_required, current_user
from flask import jsonify

@app.route('/api/analytics-data')
@login_required
def analytics_data():
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    
    # Process data for charts
    # Example: tasks by day
    from collections import defaultdict
    from datetime import datetime

    tasks_by_day = defaultdict(int)
    for task in tasks:
        day = task.created_at.strftime('%Y-%m-%d')
        tasks_by_day[day] += 1
    
    data = {
        "taskCreation": {
            "labels": list(tasks_by_day.keys()),
            "data": list(tasks_by_day.values())
        },
        # Add other analytics similarly
    }

    return jsonify(data)

@app.route('/add-task', methods=['POST'])
@login_required
def add_task():
    title = request.form['title']
    description = request.form.get('description')
    priority = request.form.get('priority')
    due_date = request.form.get('due_date')
    time_spent = request.form.get('time_spent')
    completed = True if request.form.get('completed') == 'True' else False

    new_task = Task(
        title=title,
        description=description,
        priority=priority,
        due_date=datetime.strptime(due_date, '%Y-%m-%d'),
        time_spent=float(time_spent),
        completed=completed,
        user_id=current_user.id
    )

    db.session.add(new_task)
    db.session.commit()

    return redirect(url_for('dashboard'))
@app.route('/edit-task/<int:task_id>', methods=['POST'])
@login_required
def edit_task(task_id):
    # Get the task from database
    task = Task.query.get_or_404(task_id)
    
    # Check if the current user owns this task
    if task.user_id != current_user.id:
        flash('Unauthorized to edit this task.', 'error')
        return redirect(url_for('dashboard'))
    
    # Update task with form data
    task.title = request.form['title']
    task.description = request.form.get('description')
    task.priority = request.form.get('priority')
    task.due_date = datetime.strptime(request.form.get('due_date'), '%Y-%m-%d') if request.form.get('due_date') else None
    task.time_spent = float(request.form.get('time_spent'))
    task.completed = True if request.form.get('completed') == 'True' else False
    
    # Save changes to database
    try:
        db.session.commit()
        flash('Task updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error updating task. Please try again.', 'error')
    
    return redirect(url_for('dashboard'))

@app.route('/log-time/<int:task_id>', methods=['POST'])
@login_required
def log_time(task_id):
    data = request.get_json()
    actual_time_spent = float(data.get('actual_time_spent', 0))

    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    task.actual_time_spent = actual_time_spent
    db.session.commit()

    return jsonify({'message': 'Time logged successfully'})

@app.route('/logout')
def logout():
    logout_user()
    session.pop('_google_authlib_state_', None)
    session.pop('user', None)
    session.pop('user_id', None)
    session.pop('user_name', None)
    return redirect(url_for('login_page'))

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store'
    return response

@app.route('/debug-users')
def debug_users():
    users = User.query.all()
    return "<br>".join([f"{u.email} — {u.provider}" for u in users])



@app.route('/download/csv')
@login_required
def download_csv():
    tasks = Task.query.filter_by(user_id=current_user.id).all()

    # Create in-memory file-like object
    si = io.StringIO()
    writer = csv.writer(si)

    # Write CSV header
    writer.writerow([
        'Title', 'Description', 'Priority', 'Due Date',
        'Time Spent', 'Actual Time', 'Completed'
    ])

    # Write task data
    for task in tasks:
        writer.writerow([
            task.title,
            task.description,
            task.priority,
            task.due_date.strftime('%Y-%m-%d') if task.due_date else '',
            task.time_spent,
            task.actual_time_spent,
            'Yes' if task.completed else 'No'
        ])

    # Move to beginning
    si.seek(0)

    # Return as downloadable CSV
    return Response(
        si.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=task_report.csv"}
    )




@app.route('/download/pdf')
@login_required
def download_pdf():
    tasks = Task.query.filter_by(user_id=current_user.id).all()

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    p.setFont("Helvetica-Bold", 14)
    p.drawString(30, height - 40, "Task Report")

    y = height - 70
    p.setFont("Helvetica", 10)
    for task in tasks:
        task_line = f"{task.title} | {task.priority} | {task.due_date} | Spent: {task.time_spent} | Done: {'Yes' if task.completed else 'No'}"
        p.drawString(30, y, task_line)
        y -= 15
        if y < 40:
            p.showPage()
            y = height - 40

    p.save()
    buffer.seek(0)

    return Response(buffer, mimetype='application/pdf',
                    headers={"Content-Disposition": "attachment;filename=task_report.pdf"})

@app.route('/delete-task/<int:task_id>', methods=['POST'])
@login_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        flash('Unauthorized to delete this task.', 'error')
        return redirect(url_for('dashboard'))

    db.session.delete(task)
    db.session.commit()
    flash('Task deleted successfully.', 'success')
    return redirect(url_for('dashboard'))

# --- Main Entry ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    port = int(os.environ.get("PORT", 5001))
    app.run(debug=True, host="0.0.0.0", port=port)
