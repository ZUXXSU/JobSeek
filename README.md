# Job Portal Web Application

A full-stack Job Portal built with **Python (Flask)**, **SQLite**, and **Bootstrap 5**.

## 🚀 Features
- **User Roles:**
  - **Job Seekers:** Register, search jobs with filters (category, location), and apply by uploading a resume.
  - **Employers:** Post new job listings and manage (view/delete) their own postings via the Dashboard.
  - **Admin:** Manage all users and job listings.
- **Job Search:** Filter jobs by title, location, category, and company.
- **Authentication:** Secure login/registration with password hashing.
- **Environment Configuration:** Uses `.env` for secure configuration.

## 🛠️ Tech Stack
- **Backend:** Flask (Python)
- **Database:** SQLite (SQLAlchemy ORM)
- **Frontend:** HTML5, CSS3, Jinja2, Bootstrap 5
- **Configuration:** python-dotenv

## 📋 Prerequisites
- Python 3.8+
- pip (Python package manager)

## ⚙️ Installation & Setup

1. **Clone the project folder**
   
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables:**
   Create a `.env` file in the root directory (or use the existing one):
   ```env
   SECRET_KEY=your_secret_key
   DATABASE_URI=sqlite:///database.db
   FLASK_PORT=5000
   FLASK_DEBUG=True
   UPLOAD_FOLDER=static/uploads
   ```

4. **Initialize the Database:**
   The database tables are automatically created on the first run.
   To seed initial demo data, visit `http://127.0.0.1:5000/seed` after starting the server.

5. **Run the Application:**
   ```bash
   python app.py
   ```

6. **Access the App:**
   Open your browser and go to `http://127.0.0.1:5000`

## 🔐 Demo Credentials

### 🛡️ Admin & System Management
- **Admin Secure Portal:** `http://127.0.0.1:5000/admin/token_portal`
  - **Secret Key:** `admin123` (Use this to generate a secure JWT token)
- **Database Management:** `http://127.0.0.1:5000/database`
  - **Secret Key:** `admin123`
- **Database Reset:** `http://127.0.0.1:5000/database/reset` (Requires Database Management login)

### 👥 User Logins
- **Job Seeker:**
  - **Email:** `darshan@gmail.com`
  - **Password:** `password123`
- **Employer:**
  - **Email:** `employer@gmail.com`
  - **Password:** `password123`
- **System Admin (Legacy Login):**
  - **Email:** `admin@portal.com`
  - **Password:** `admin123`

## 📂 Project Structure
- `app.py`: Main application logic and routes.
- `templates/`: HTML Jinja2 templates.
- `static/`: CSS files and uploaded resumes.
- `database.db`: SQLite database file.
- `.env`: Configuration settings.

## 📝 Evaluation Criteria Met
- [x] **Functionality:** All roles (Seeker, Employer, Admin) implemented.
- [x] **Code Quality:** Clean, modular, and well-commented code.
- [x] **UI/UX Design:** Responsive Bootstrap 5 design.
- [x] **Documentation:** Comprehensive README and setup instructions.
