from flask import Flask, render_template, redirect, request, flash, url_for, session
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime
from dotenv import load_dotenv
from PIL import Image
from functools import wraps

# Import extensions and models
from extensions import db, login_manager
from models import User, Experience, Education, Skill, Job, Responsibility, Requirement, Tag, Application

# Load environment variables (Vercel provides these directly)
load_dotenv()

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-12345')

# Vercel filesystem is read-only except for /tmp
if os.environ.get('VERCEL'):
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/database.db'
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI', 'sqlite:///database.db')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = '/tmp' if os.environ.get('VERCEL') else os.getenv('UPLOAD_FOLDER', 'static/uploads')
app.config['TEMPLATES_AUTO_RELOAD'] = True
DB_SECRET = os.getenv('DB_SECRET', 'admin123')

# Initialize Extensions
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = "login"

def format_indian(number):
    s = str(int(number or 0))
    if len(s) <= 3: return s
    last_three = s[-3:]
    remaining = s[:-3]
    remaining_rev = remaining[::-1]
    groups = [remaining_rev[i:i+2] for i in range(0, len(remaining_rev), 2)]
    formatted_remaining = ",".join(groups)[::-1]
    return f"{formatted_remaining},{last_three}"

app.jinja_env.filters['indian_format'] = format_indian

# Initialize database tables safely
try:
    with app.app_context():
        db.create_all()
except Exception as e:
    print(f"Database initialization error: {e}")

# -----------------------
# HELPERS & MIDDLEWARE
# -----------------------

@login_manager.user_loader
def load_user(user_id):
    try:
        return User.query.get(int(user_id))
    except:
        return None

def admin_token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_verified'):
            return redirect(url_for('admin_verify'))
        if not current_user.is_authenticated or current_user.role != "admin":
            admin_user = User.query.filter_by(role='admin').first()
            if admin_user:
                login_user(admin_user)
            else:
                return redirect(url_for("admin_verify"))
        return f(*args, **kwargs)
    return decorated

# -----------------------
# ROUTES
# -----------------------

@app.route("/")
def index():
    try:
        query = Job.query.filter_by(status="active")
        if current_user.is_authenticated and current_user.role == "seeker":
            query = query.filter(~Job.applications.any(user_id=current_user.id))
        jobs = query.order_by(Job.posted_at.desc()).limit(6).all()
        return render_template("index.html", jobs=jobs)
    except Exception as e:
        return f"App Error: {e}" if os.environ.get('FLASK_DEBUG') else "Server Error", 500

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        if User.query.filter_by(email=request.form["email"]).first():
            flash("Email already exists!")
            return redirect(url_for("register"))
        user = User(
            username=request.form["username"], email=request.form["email"],
            password=generate_password_hash(request.form["password"]),
            role=request.form["role"], full_name=request.form["username"]
        )
        db.session.add(user)
        db.session.commit()
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(email=request.form["email"]).first()
        if user and check_password_hash(user.password, request.form["password"]):
            login_user(user)
            if user.role == "admin":
                session['admin_verified'] = True
                return redirect(url_for("admin"))
            return redirect(url_for("dashboard"))
        flash("Invalid credentials")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    session.pop('admin_verified', None)
    return redirect(url_for("index"))

@app.route("/dashboard")
@login_required
def dashboard():
    posted_jobs = Job.query.filter_by(poster_id=current_user.id).all() if current_user.role == "employer" else []
    apps = Application.query.filter_by(user_id=current_user.id).all()
    return render_template("dashboard.html", jobs=posted_jobs, applications=apps)

@app.route("/job/<int:job_id>")
def job_detail(job_id):
    job = Job.query.get_or_404(job_id)
    return render_template("job_detail.html", job=job)

@app.route("/jobs")
def jobs():
    from sqlalchemy import or_
    search_query = request.args.get("q", "")
    query = Job.query.filter_by(status="active")
    if current_user.is_authenticated and current_user.role == "seeker":
        query = query.filter(~Job.applications.any(user_id=current_user.id))
    if search_query:
        query = query.filter(or_(Job.title.contains(search_query), Job.company_name.contains(search_query)))
    return render_template("jobs.html", jobs=query.all(), search_query=search_query)

# -----------------------
# ADMIN ROUTES
# -----------------------

@app.route("/admin")
@admin_token_required
def admin():
    users = User.query.all()
    jobs = Job.query.all()
    return render_template("admin_secure_dashboard.html", users=users, jobs=jobs)

@app.route("/admin/verify", methods=["GET", "POST"])
def admin_verify():
    if request.method == "POST":
        if request.form.get("secret_key") == DB_SECRET:
            session['admin_verified'] = True
            admin_user = User.query.filter_by(role='admin').first()
            if not admin_user:
                admin_user = User(
                    username="admin", email="admin@portal.com",
                    password=generate_password_hash("admin123"),
                    role="admin", full_name="System Admin"
                )
                db.session.add(admin_user)
                db.session.commit()
            login_user(admin_user)
            return redirect(url_for("admin"))
        flash("Invalid Secret Key")
    return render_template("admin_token_portal.html")

@app.route("/admin/api/generate_token", methods=["POST"])
def generate_admin_token():
    secret = request.json.get("secret_key") if request.is_json else request.form.get("secret_key")
    if secret == DB_SECRET:
        session['admin_verified'] = True
        admin_user = User.query.filter_by(role='admin').first()
        if not admin_user:
            admin_user = User(username="admin", email="admin@portal.com", password=generate_password_hash("admin123"), role="admin", full_name="System Admin")
            db.session.add(admin_user)
            db.session.commit()
        login_user(admin_user)
        if request.is_json: return {"success": True}
        return redirect(url_for("admin"))
    return {"error": "Invalid Key"}, 401

@app.route("/admin/logout_session")
def admin_logout_session():
    session.pop('admin_verified', None)
    return redirect(url_for("index"))

@app.route("/delete_job/<int:job_id>")
@login_required
def delete_job(job_id):
    job = Job.query.get_or_404(job_id)
    if current_user.role == "admin" or job.poster_id == current_user.id:
        db.session.delete(job)
        db.session.commit()
    return redirect(url_for("admin" if current_user.role == "admin" else "dashboard"))

@app.route("/seed")
def seed():
    try:
        db.create_all()
        if not User.query.filter_by(email="admin@portal.com").first():
            admin = User(username="admin", email="admin@portal.com", password=generate_password_hash("admin123"), role="admin", full_name="System Admin")
            db.session.add(admin)
            db.session.commit()
        return "Database Seeded Successfully"
    except Exception as e:
        return f"Seed Error: {e}", 500

@app.errorhandler(404)
def not_found(e): return redirect(url_for("login"))

@app.errorhandler(Exception)
def handle_exception(e):
    return render_template("server_error.html", error=str(e)), 500

# Vercel needs 'app' variable at top level
if __name__ == "__main__":
    app.run(port=5001, debug=True)
