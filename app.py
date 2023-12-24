from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SECRET_KEY'] = 'your_secret_key'
db = SQLAlchemy(app)

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

@app.route('/')
def index():
    return render_template('index.html')

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
    # Here you can implement session logout logic
    return redirect(url_for('index'))

def analyze_user_behavior(user_id):
    activities = UserActivity.query.filter_by(user_id=user_id).all()
    # Example analysis: Detect if a user logs in multiple times in a short period
    recent_logins = [act for act in activities if act.activity == "User logged in" and datetime.utcnow() - act.timestamp < timedelta(minutes=5)]
    if len(recent_logins) > 3:
        generate_alert(f"User {user_id} logged in multiple times in a short period.")


def generate_alert(message):
    print(f"ALERT: {message}")
    # Here, you can extend this to send email notifications or log to an external system



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
