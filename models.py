from datetime import datetime
from flask_login import UserMixin
from extensions import db

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default="seeker")
    full_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    city = db.Column(db.String(50))
    state = db.Column(db.String(50))
    country = db.Column(db.String(50))
    profile_picture = db.Column(db.String(200))
    company_logo = db.Column(db.String(200))
    professional_summary = db.Column(db.Text)
    expected_salary_min = db.Column(db.Integer, default=0)
    currency = db.Column(db.String(10), default="INR")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    experiences = db.relationship('Experience', backref='user', lazy=True, cascade="all, delete-orphan")
    educations = db.relationship('Education', backref='user', lazy=True, cascade="all, delete-orphan")
    skills = db.relationship('Skill', backref='user', lazy=True, cascade="all, delete-orphan")
    applications = db.relationship('Application', backref='user', lazy=True)
    jobs = db.relationship('Job', backref='poster', lazy=True, cascade="all, delete-orphan")

class Experience(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    company = db.Column(db.String(100))
    role = db.Column(db.String(100))
    start_date = db.Column(db.String(20))
    end_date = db.Column(db.String(20))
    current_job = db.Column(db.Boolean, default=False)
    description = db.Column(db.Text)

class Education(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    institution = db.Column(db.String(100))
    degree = db.Column(db.String(100))
    year_of_passing = db.Column(db.Integer)

class Skill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(50))

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    poster_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    company_name = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default="active")
    description = db.Column(db.Text)
    location = db.Column(db.String(100))
    job_type = db.Column(db.String(50))
    is_remote = db.Column(db.Boolean, default=False)
    experience_level = db.Column(db.String(50))
    salary_min = db.Column(db.Integer)
    salary_max = db.Column(db.Integer)
    posted_at = db.Column(db.DateTime, default=datetime.utcnow)
    applicant_count = db.Column(db.Integer, default=0)

    responsibilities = db.relationship('Responsibility', backref='job', lazy=True, cascade="all, delete-orphan")
    requirements = db.relationship('Requirement', backref='job', lazy=True, cascade="all, delete-orphan")
    tags = db.relationship('Tag', backref='job', lazy=True, cascade="all, delete-orphan")

class Responsibility(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=False)
    text = db.Column(db.Text)

class Requirement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=False)
    text = db.Column(db.Text)

class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=False)
    name = db.Column(db.String(50))

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'))
    resume = db.Column(db.String(200))
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)
    job = db.relationship('Job', backref='applications', lazy=True)
