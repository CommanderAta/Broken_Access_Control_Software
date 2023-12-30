from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import os
from flask_mail import Mail, Message

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SECRET_KEY'] = 'your_secret_key'
db = SQLAlchemy(app)

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'adhdestinies@gmail.com'
app.config['MAIL_PASSWORD'] = 'ufcjvdlrhjdbhwco' 
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False

mail = Mail(app)

bank_access_attempts = {}
ALLOWED_USER_IDS = [1] 

class UserActivity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    activity = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)  # Now correctly using datetime

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    activities = db.relationship('UserActivity', backref='user', lazy=True)

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)  # Add an admin flag

@app.route('/')
def index():
    return render_template('index.html')

def generate_alert(message):
    try:
        msg = Message("Alert from Flask App", sender=app.config['MAIL_USERNAME'], recipients=["commanderata@gmail.com", "muhammedhur@gmail.com"])
        msg.body = message
        mail.send(msg)
        print(f"Email alert sent: {message}")
    except Exception as e:
        print(f"Failed to send email alert: {e}")

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        new_user = User(username=username, password=password)

        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('index'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['user_id'] = user.id
            log_activity(user.id, "User logged in")
            analyze_user_behavior(user.id)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials')
    return render_template('login.html')

def log_activity(user_id, activity):
    new_activity = UserActivity(user_id=user_id, activity=activity)
    db.session.add(new_activity)
    db.session.commit()

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')  # Render the dashboard template


@app.route('/logout')
def logout():
    session.pop('user_id', None)  # Remove user_id from session
    flash('You have been logged out.')
    return redirect(url_for('index'))


def analyze_user_behavior(user_id):
    activities = UserActivity.query.filter_by(user_id=user_id).all()
    recent_logins = [act for act in activities if act.activity == "User logged in" and datetime.utcnow() - act.timestamp < timedelta(minutes=5)]
    if len(recent_logins) > 3:
        print("Atta Ali")
        generate_alert(f"User {user_id} logged in multiple times in a short period.")

@app.route('/bank')
def bank():
    user_id = session.get('user_id')

    # Check if the user is logged in
    if not user_id:
        flash('You need to login first')
        return redirect(url_for('login'))

    # Get the user from the database
    user = User.query.get(user_id)

    # Check if the user is an admin
    if user and user.is_admin:
        # Increment access attempts for the user
        generate_alert(f"Admin user {user.username} accessed the bank page")

        # Additional logic for admin users (if needed) can go here

        return render_template('bank.html')
    else:
        flash('You do not have admin privileges to access this page')
        return redirect(url_for('dashboard'))  # Redirect to the dashboard

    return redirect(url_for('dashboard'))  # Redirect to a safe page




@app.route('/escalate_privileges')
def escalate_privileges():
    user_id = session.get('user_id')
    if user_id:
        user = User.query.get(user_id)
        if user:
            # Toggle admin status
            user.is_admin = not user.is_admin
            db.session.commit()
            flash('Privileges have been escalated. Admin status: ' + str(user.is_admin))

            # Send email notification about privilege escalation
            generate_alert(f"Admin privileges changed for user {user.username}. New status: {user.is_admin}")
        else:
            flash('User not found.')
    else:
        flash('You need to login first.')
    
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
