from flask import Flask, render_template, redirect, request, flash, url_for, session
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import uuid
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

# -----------------------
# USER PROFILE & DETAILS
# -----------------------

@app.route("/profile/update", methods=["POST"])
@login_required
def update_profile():
    current_user.full_name = request.form.get("full_name")
    current_user.phone = request.form.get("phone")
    current_user.city = request.form.get("city")
    current_user.state = request.form.get("state")
    current_user.country = request.form.get("country")
    if current_user.role == "seeker":
        current_user.expected_salary_min = int(request.form.get("expected_salary_min", 0))
    current_user.professional_summary = request.form.get("professional_summary")
    db.session.commit()
    flash("Profile updated successfully!")
    return redirect(url_for("dashboard"))

@app.route("/profile/picture", methods=["POST"])
@login_required
def update_profile_picture():
    if 'profile_picture' in request.files:
        file = request.files['profile_picture']
        if file.filename != '':
            ext = file.filename.rsplit('.', 1)[1].lower()
            filename = f"{current_user.username}_{uuid.uuid4().hex[:4]}.{ext}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            current_user.profile_picture = f"uploads/{filename}"
            db.session.commit()
    return redirect(url_for("dashboard"))

@app.route("/experience/add", methods=["POST"])
@login_required
def add_experience():
    exp = Experience(
        user_id=current_user.id,
        company=request.form.get("company"),
        role=request.form.get("role"),
        start_date=request.form.get("start_date"),
        end_date=request.form.get("end_date"),
        current_job='current_job' in request.form,
        description=request.form.get("description")
    )
    db.session.add(exp)
    db.session.commit()
    return redirect(url_for("dashboard"))

@app.route("/experience/update/<int:exp_id>", methods=["POST"])
@login_required
def update_experience(exp_id):
    exp = Experience.query.get_or_404(exp_id)
    if exp.user_id == current_user.id:
        exp.company = request.form.get("company")
        exp.role = request.form.get("role")
        exp.start_date = request.form.get("start_date")
        exp.end_date = request.form.get("end_date")
        exp.current_job = 'current_job' in request.form
        exp.description = request.form.get("description")
        db.session.commit()
    return redirect(url_for("dashboard"))

@app.route("/experience/delete/<int:exp_id>")
@login_required
def delete_experience(exp_id):
    exp = Experience.query.get_or_404(exp_id)
    if exp.user_id == current_user.id:
        db.session.delete(exp)
        db.session.commit()
    return redirect(url_for("dashboard"))

@app.route("/education/add", methods=["POST"])
@login_required
def add_education():
    edu = Education(
        user_id=current_user.id,
        institution=request.form.get("institution"),
        degree=request.form.get("degree"),
        year_of_passing=int(request.form.get("year_of_passing", 0))
    )
    db.session.add(edu)
    db.session.commit()
    return redirect(url_for("dashboard"))

@app.route("/education/update/<int:edu_id>", methods=["POST"])
@login_required
def update_education(edu_id):
    edu = Education.query.get_or_404(edu_id)
    if edu.user_id == current_user.id:
        edu.institution = request.form.get("institution")
        edu.degree = request.form.get("degree")
        edu.year_of_passing = int(request.form.get("year_of_passing", 0))
        db.session.commit()
    return redirect(url_for("dashboard"))

@app.route("/education/delete/<int:edu_id>")
@login_required
def delete_education(edu_id):
    edu = Education.query.get_or_404(edu_id)
    if edu.user_id == current_user.id:
        db.session.delete(edu)
        db.session.commit()
    return redirect(url_for("dashboard"))

@app.route("/skill/add", methods=["POST"])
@login_required
def add_skill():
    names = request.form.get("name", "").split(",")
    for name in names:
        if name.strip():
            skill = Skill(user_id=current_user.id, name=name.strip())
            db.session.add(skill)
    db.session.commit()
    return redirect(url_for("dashboard"))

@app.route("/skill/delete/<int:skill_id>")
@login_required
def delete_skill(skill_id):
    skill = Skill.query.get_or_404(skill_id)
    if skill.user_id == current_user.id:
        db.session.delete(skill)
        db.session.commit()
    return redirect(url_for("dashboard"))

@app.route("/post_job", methods=["GET", "POST"])
@login_required
def post_job():
    if current_user.role != "employer":
        flash("Only employers can post jobs.")
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        job = Job(
            poster_id=current_user.id,
            title=request.form.get("title"),
            company_name=request.form.get("company_name"),
            location=request.form.get("location"),
            experience_level=request.form.get("experience_level"),
            job_type=request.form.get("job_type"),
            salary_min=int(request.form.get("salary_min", 0)),
            salary_max=int(request.form.get("salary_max", 0)),
            is_remote='is_remote' in request.form,
            description=request.form.get("description")
        )
        db.session.add(job)
        db.session.flush() # Get job.id
        
        # Add responsibilities
        for res in request.form.get("responsibilities", "").split("\n"):
            if res.strip():
                db.session.add(Responsibility(job_id=job.id, text=res.strip()))
        
        # Add requirements
        for req in request.form.get("requirements", "").split("\n"):
            if req.strip():
                db.session.add(Requirement(job_id=job.id, text=req.strip()))
                
        # Add tags
        for tag in request.form.get("tags", "").split(","):
            if tag.strip():
                db.session.add(Tag(job_id=job.id, name=tag.strip()))
                
        db.session.commit()
        flash("Job posted successfully!")
        return redirect(url_for("dashboard"))
    return render_template("post_job.html")

@app.route("/apply/<int:job_id>", methods=["GET", "POST"])
@login_required
def apply(job_id):
    job = Job.query.get_or_404(job_id)
    if request.method == "POST":
        if 'resume' in request.files:
            file = request.files['resume']
            if file.filename != '':
                filename = secure_filename(f"{current_user.username}_{job.id}_{file.filename}")
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                app_entry = Application(user_id=current_user.id, job_id=job.id, resume=filename)
                db.session.add(app_entry)
                job.applicant_count += 1
                db.session.commit()
                flash("Application submitted successfully!")
                return redirect(url_for("dashboard"))
    return render_template("apply.html", job=job)

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
