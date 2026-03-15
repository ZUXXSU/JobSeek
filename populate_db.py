import os
import random
from app import app, db, User, Job, Tag, Requirement, Responsibility, Skill, Experience, Education
from werkzeug.security import generate_password_hash

# --- Data ---
USER_NAMES = ["Alex", "Ben", "Charlie", "David", "Eva", "Frank", "Grace", "Henry", "Ivy", "Jack"]
COMPANY_NAMES = ["Innovate Inc", "TechCorp", "Solutions Ltd", "DataWave", "CloudPioneer", "QuantumLeap", "NextGen", "Synergy", "Apex", "Zenith"]
JOB_TITLES = ["Software Engineer", "Frontend Developer", "Backend Developer", "Full Stack Engineer", "DevOps Engineer", "Data Scientist", "Product Manager", "UI/UX Designer", "QA Tester", "Project Manager"]
LOCATIONS = ["Mumbai", "Bangalore", "Pune", "Hyderabad", "Chennai", "Delhi", "Kolkata"]
DEGREES = ["B.Tech in CS", "M.S. in Data Science", "B.A. in Design", "MBA", "B.E. in IT"]
INSTITUTIONS = ["IIT Bombay", "BITS Pilani", "NIT Warangal", "MIT", "Stanford"]
SKILLS = ["Python", "JavaScript", "React", "Node.js", "SQL", "AWS", "Docker", "Kubernetes", "Figma", "Jira"]

def create_detailed_users():
    print("Creating specific detailed users...")
    # Darshan - Seeker
    darshan = User.query.filter_by(email="darshan@gmail.com").first()
    if not darshan:
        darshan = User(
            username="darshan", email="darshan@gmail.com", password=generate_password_hash("password123"), role="seeker",
            full_name="Darshan Solanki", phone="9876543210", city="Mumbai", state="Maharashtra", country="India",
            professional_summary="Enthusiastic full-stack developer with 3 years of experience building web applications with Python and JavaScript.",
            expected_salary_min=1200000,
            profile_picture=f"https://ui-avatars.com/api/?name=Darshan+Solanki"
        )
        db.session.add(darshan)
        db.session.flush()
        db.session.add(Skill(user_id=darshan.id, name="Python"))
        db.session.add(Skill(user_id=darshan.id, name="Flask"))
        db.session.add(Skill(user_id=darshan.id, name="JavaScript"))
        db.session.add(Experience(user_id=darshan.id, company="Old Company", role="Junior Dev", start_date="2021-01", end_date="2023-01", description="Worked on legacy systems."))
        db.session.add(Education(user_id=darshan.id, institution="Mumbai University", degree="B.E. in Computer Science", year_of_passing=2021))
        print("User 'darshan@gmail.com' created.")

    # Employer - Recruiter
    employer = User.query.filter_by(email="employer@gmail.com").first()
    if not employer:
        employer = User(
            username="mainrecruiter", email="employer@gmail.com", password=generate_password_hash("password123"), role="employer",
            full_name="Global Tech Recruiters", phone="1234567890", city="Bangalore", state="Karnataka", country="India",
            company_logo=f"https://ui-avatars.com/api/?name=Global+Tech"
        )
        db.session.add(employer)
        db.session.flush()
        
        # Add jobs for this employer
        job1 = Job(poster_id=employer.id, title="Senior Python Developer", company_name="Global Tech Recruiters", description="Seeking an expert Python dev.", location="Bangalore", salary_min=2000000, salary_max=3000000)
        job2 = Job(poster_id=employer.id, title="Lead React Engineer", company_name="Global Tech Recruiters", description="Lead our frontend team.", location="Remote", salary_min=2500000, salary_max=3500000)
        db.session.add_all([job1, job2])
        print("User 'employer@gmail.com' created with 2 job postings.")

    db.session.commit()

def create_users():
    print("Creating 10 new seeker users...")
    for i in range(10):
        name = USER_NAMES[i]
        username = f"{name.lower()}{i}"
        email = f"{username}@example.com"
        
        user = User(
            username=username, email=email, password=generate_password_hash("password123"), role="seeker", full_name=name,
            phone=f"9{random.randint(100,999)}{random.randint(100,999)}{random.randint(1000,9999)}",
            city=random.choice(LOCATIONS), country="India", professional_summary=f"A dedicated professional with a passion for {random.choice(SKILLS)}.",
            profile_picture=f"https://ui-avatars.com/api/?name={name.replace(' ', '+')}"
        )
        db.session.add(user)
    db.session.commit()
    print("Seeker users created.")

def create_companies_and_jobs():
    print("Creating 10 new companies, each with multiple jobs...")
    for i in range(10):
        company_name = COMPANY_NAMES[i]
        
        employer = User(
            username=company_name.lower().replace(" ", "").replace(".", ""), email=f"contact@{company_name.lower().replace(' ', '')}.com",
            password=generate_password_hash("password123"), role="employer", full_name=company_name,
            company_logo=f"https://ui-avatars.com/api/?name={company_name.replace(' ', '+')}"
        )
        db.session.add(employer)
        db.session.flush()

        for _ in range(random.randint(2, 5)):
            job_title = random.choice(JOB_TITLES)
            job = Job(
                poster_id=employer.id, title=job_title, company_name=company_name,
                description=f"We are hiring a skilled {job_title} to join our dynamic team. You will be responsible for...",
                location=random.choice(LOCATIONS), job_type="Full-time", experience_level="Mid-Senior",
                salary_min=random.randint(8, 20) * 100000, salary_max=random.randint(20, 40) * 100000
            )
            db.session.add(job)
    db.session.commit()
    print("Companies and jobs created.")

if __name__ == "__main__":
    with app.app_context():
        print("Resetting database...")
        db.drop_all()
        db.create_all()
        print("Database reset complete.")
        
        create_users()
        create_companies_and_jobs()
        create_detailed_users()
        
    print("Database population complete!")
